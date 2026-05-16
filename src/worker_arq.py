"""arq worker process. Run: python -m arq src.worker_arq.WorkerSettings"""

from arq.connections import RedisSettings

from src.core.config import get_settings
from src.modules.project_exports.arq_tasks import generate_project_export
from src.modules.timeline.arq_tasks import persist_timeline_event

_settings = get_settings()


def _redis_url_or_fail(url: str | None) -> str:
    if not url:
        msg = "redis_url / REDIS_URL must be set to run the timeline arq worker"
        raise RuntimeError(msg)
    return url


_REDIS_URL: str = _redis_url_or_fail(_settings.redis_url)


class WorkerSettings:
    functions = [persist_timeline_event, generate_project_export]
    redis_settings = RedisSettings.from_dsn(_REDIS_URL)
