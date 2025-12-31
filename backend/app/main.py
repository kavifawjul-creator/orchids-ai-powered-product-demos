import os
import time
import signal
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
from collections import defaultdict
from fastapi import FastAPI, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from .core.config import settings
from .core.events import event_bus
from .api.routes import router
from .api.websocket import websocket_endpoint

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("autovid")

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

class MetricsCollector:
    def __init__(self):
        self.request_count: Dict[str, int] = defaultdict(int)
        self.request_latencies: Dict[str, list] = defaultdict(list)
        self.error_count: Dict[str, int] = defaultdict(int)
        self.start_time = datetime.utcnow()
    
    def record_request(self, path: str, method: str, latency: float, status_code: int):
        key = f"{method}:{path}"
        self.request_count[key] += 1
        self.request_latencies[key].append(latency)
        if len(self.request_latencies[key]) > 1000:
            self.request_latencies[key] = self.request_latencies[key][-1000:]
        if status_code >= 400:
            self.error_count[key] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        total_requests = sum(self.request_count.values())
        total_errors = sum(self.error_count.values())
        
        avg_latencies = {}
        for key, latencies in self.request_latencies.items():
            if latencies:
                avg_latencies[key] = {
                    "avg_ms": round(sum(latencies) / len(latencies) * 1000, 2),
                    "min_ms": round(min(latencies) * 1000, 2),
                    "max_ms": round(max(latencies) * 1000, 2),
                    "count": len(latencies)
                }
        
        return {
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": round(total_errors / total_requests * 100, 2) if total_requests > 0 else 0,
            "endpoints": {
                key: {
                    "count": self.request_count[key],
                    "errors": self.error_count.get(key, 0),
                    "latency": avg_latencies.get(key, {})
                }
                for key in self.request_count
            }
        }

metrics = MetricsCollector()

shutdown_event = asyncio.Event()

async def graceful_shutdown():
    logger.info("Initiating graceful shutdown...")
    shutdown_event.set()
    
    try:
        from .services.sandbox.service import sandbox_service
        cleaned = await sandbox_service.cleanup_all_sandboxes()
        logger.info(f"Cleaned up {cleaned} sandboxes during shutdown")
    except Exception as e:
        logger.error(f"Error during sandbox cleanup: {e}")
    
    logger.info("Graceful shutdown complete")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME}...")
    
    try:
        await event_bus.connect()
        logger.info("Event bus connected")
    except Exception as e:
        logger.warning(f"Event bus connection failed: {e}")
    
    try:
        from .services.sandbox.service import sandbox_service
        await sandbox_service.startup_recovery()
    except Exception as e:
        logger.warning(f"Sandbox recovery failed: {e}")
    
    yield
    
    await graceful_shutdown()
    
    try:
        await event_bus.disconnect()
        logger.info("Event bus disconnected")
    except Exception:
        pass

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan
)

app.state.limiter = limiter
app.state.metrics = metrics
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

allowed_origins = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://localhost:3000",
]

if settings.DEBUG:
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def logging_and_metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    client_ip = get_remote_address(request)
    method = request.method
    path = request.url.path
    
    logger.info(f"→ {method} {path} from {client_ip}")
    
    try:
        response = await call_next(request)
        latency = time.time() - start_time
        
        metrics.record_request(path, method, latency, response.status_code)
        
        log_level = logging.WARNING if response.status_code >= 400 else logging.INFO
        logger.log(log_level, f"← {method} {path} - {response.status_code} ({latency*1000:.2f}ms)")
        
        response.headers["X-Request-Time"] = f"{latency*1000:.2f}ms"
        return response
        
    except Exception as e:
        latency = time.time() - start_time
        metrics.record_request(path, method, latency, 500)
        logger.error(f"✕ {method} {path} - Error: {str(e)} ({latency*1000:.2f}ms)")
        raise

app.include_router(router, prefix=settings.API_V1_PREFIX)

@app.websocket("/ws/{channel}")
async def ws_endpoint(websocket: WebSocket, channel: str):
    await websocket_endpoint(websocket, channel)

@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    from .core.database import get_supabase
    
    health_status = {
        "status": "healthy",
        "service": settings.APP_NAME,
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": (datetime.utcnow() - metrics.start_time).total_seconds(),
        "dependencies": {}
    }
    
    try:
        supabase = get_supabase()
        supabase.table("projects").select("id").limit(1).execute()
        health_status["dependencies"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["dependencies"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
    
    try:
        if settings.REDIS_URL:
            import redis
            r = redis.from_url(settings.REDIS_URL)
            r.ping()
            health_status["dependencies"]["redis"] = {"status": "healthy"}
        else:
            health_status["dependencies"]["redis"] = {"status": "not_configured"}
    except Exception as e:
        health_status["dependencies"]["redis"] = {"status": "unhealthy", "error": str(e)}
    
    try:
        if settings.OPENAI_API_KEY:
            health_status["dependencies"]["openai"] = {"status": "configured"}
        else:
            health_status["dependencies"]["openai"] = {"status": "not_configured"}
    except Exception:
        health_status["dependencies"]["openai"] = {"status": "unknown"}
    
    return health_status

@app.get("/metrics")
async def get_metrics():
    return metrics.get_metrics()
