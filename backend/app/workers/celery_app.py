from ..core.config import settings

celery_app = None

if settings.REDIS_URL:
    try:
        from celery import Celery
        celery_app = Celery(
            "autovid",
            broker=settings.REDIS_URL,
            backend=settings.REDIS_URL,
            include=["app.workers.tasks"]
        )
        celery_app.conf.update(
            task_serializer="json",
            accept_content=["json"],
            result_serializer="json",
            timezone="UTC",
            enable_utc=True,
            task_track_started=True,
            task_time_limit=1800,
        )
    except ImportError:
        pass

class MockTask:
    def delay(self, *args, **kwargs):
        raise NotImplementedError("Celery not available, use background tasks")

class MockCeleryApp:
    def task(self, *args, **kwargs):
        def decorator(func):
            func.delay = lambda *a, **kw: (_ for _ in ()).throw(
                NotImplementedError("Celery not available")
            )
            return func
        return decorator

if celery_app is None:
    celery_app = MockCeleryApp()
