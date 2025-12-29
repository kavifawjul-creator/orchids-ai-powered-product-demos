from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .core.config import settings
from .core.events import event_bus
from .api.routes import router
from .api.websocket import websocket_endpoint

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await event_bus.connect()
    except Exception:
        pass
    
    yield
    
    try:
        await event_bus.disconnect()
    except Exception:
        pass

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
