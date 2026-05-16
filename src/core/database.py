from collections.abc import AsyncGenerator
import json
import time
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import get_settings

_settings = get_settings()

# #region agent log
def _debug_log(message: str, data: dict, hypothesis_id: str):
    try:
        log_entry = {
            "sessionId": "25bd74",
            "id": f"log_{int(time.time() * 1000)}_{hypothesis_id}",
            "timestamp": int(time.time() * 1000),
            "location": "src/core/database.py",
            "message": message,
            "data": data,
            "runId": "initial",
            "hypothesisId": hypothesis_id
        }
        Path("debug-25bd74.log").open("a").write(json.dumps(log_entry) + "\n")
    except:
        pass
# #endregion

engine = create_async_engine(
    _settings.database_url_async,
    echo=_settings.database_echo,
    pool_pre_ping=True,
    pool_size=1,  # Force single connection to avoid concurrent operation conflicts
    max_overflow=0,  # No overflow connections
    pool_timeout=10,  # Shorter timeout to fail fast rather than hang
    pool_recycle=3600,  # Recycle connections every hour
    connect_args={
        "server_settings": {
            "jit": "off"  # Disable JIT to avoid potential asyncpg conflicts
        }
    }
)

# #region agent log
_debug_log("Engine created", {
    "url": _settings.database_url_async,
    "echo": _settings.database_echo,
    "pool_size": engine.pool.size() if hasattr(engine.pool, 'size') else "unknown",
    "pool_timeout": getattr(engine.pool, '_timeout', "unknown")
}, "A")
# #endregion

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# #region agent log
_debug_log("Session factory created", {
    "expire_on_commit": False,
    "autoflush": False
}, "E")
# #endregion

async def get_db() -> AsyncGenerator[AsyncSession]:
    # #region agent log
    _debug_log("get_db called - session start", {}, "A")
    # #endregion
    
    try:
        async with AsyncSessionLocal() as session:
            # #region agent log
            _debug_log("Session created successfully", {
                "session_id": id(session),
                "autocommit": getattr(session, 'autocommit', "unknown")
            }, "A")
            # #endregion
            yield session
            # #region agent log
            _debug_log("Session yielded - about to exit context", {"session_id": id(session)}, "A")
            # #endregion
    except Exception as e:
        # #region agent log
        _debug_log("Session creation failed", {
            "error": str(e),
            "error_type": type(e).__name__
        }, "A")
        # #endregion
        raise
