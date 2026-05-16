"""Postgres + Alembic for integration tests under this package."""

from collections.abc import AsyncGenerator
from pathlib import Path
import json
import time

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy import text

_ROOT = Path(__file__).resolve().parents[2]

# #region agent log
def _debug_log(message: str, data: dict, hypothesis_id: str):
    try:
        log_entry = {
            "sessionId": "25bd74",
            "id": f"log_{int(time.time() * 1000)}_{hypothesis_id}",
            "timestamp": int(time.time() * 1000),
            "location": "tests/integration/conftest.py",
            "message": message,
            "data": data,
            "runId": "initial",
            "hypothesisId": hypothesis_id
        }
        Path("debug-25bd74.log").open("a").write(json.dumps(log_entry) + "\n")
    except:
        pass
# #endregion

_DISABLE_FK_AND_TRUNCATE_SQL = [
    # Disable FK constraints temporarily
    "SET session_replication_role = replica",
    # Now truncate with restart identity (more aggressive)
    "TRUNCATE TABLE intervention_records, match_result_details, match_results, matches, sessions, user_level_progress, user_games, question_answers, self_report_tokens, questionnaire_responses, assessment_records, timeline_events, project_export_jobs, participant_enrollments, participant_conditions, groups, participant_profiles, projects, refresh_tokens, auth_users, users RESTART IDENTITY",
    # Re-enable FK constraints
    "SET session_replication_role = DEFAULT"
]
# vocabulary_terms / vocabulary_schemes are NOT truncated here: data comes
# from Alembic seed and must survive so participant_conditions severity checks work.


@pytest.fixture(scope="session", autouse=True)
def _apply_migrations() -> None:
    # #region agent log
    _debug_log("Migration fixture started", {"root_path": str(_ROOT)}, "B")
    # #endregion
    
    try:
        cfg = Config(str(_ROOT / "alembic.ini"))
        # #region agent log
        _debug_log("Alembic config created", {"config_file": str(_ROOT / "alembic.ini")}, "B")
        # #endregion
        
        # #region agent log
        _debug_log("Starting alembic upgrade", {}, "B")
        # #endregion
        
        command.upgrade(cfg, "head")
        
        # #region agent log
        _debug_log("Alembic upgrade completed", {}, "B")
        # #endregion
        
    except Exception as e:
        # #region agent log
        _debug_log("Migration fixture failed", {
            "error": str(e),
            "error_type": type(e).__name__
        }, "B")
        # #endregion
        raise


@pytest_asyncio.fixture(autouse=True)
async def _truncate_auth_tables(
    _apply_migrations: None,
) -> AsyncGenerator[None]:
    """Aggressive engine management to avoid AsyncPG operation conflicts."""
    import asyncio
    
    # #region agent log
    _debug_log("Starting aggressive engine management", {}, "K")
    # #endregion
    
    try:
        from src.core.database import engine
        
        # #region agent log
        _debug_log("Engine imported, aggressive dispose", {"engine_id": id(engine)}, "K")
        # #endregion
        
        await engine.dispose()
        await asyncio.sleep(0.1)  # Give asyncpg time to clean up
        
        # #region agent log
        _debug_log("Engine disposed, yielding to test", {}, "K")
        # #endregion
        
        yield
        
        # #region agent log
        _debug_log("Test completed, aggressive cleanup", {}, "K")
        # #endregion
        
        await engine.dispose()
        await asyncio.sleep(0.1)  # Give asyncpg time to clean up
        
        # #region agent log
        _debug_log("Final cleanup completed", {}, "K")
        # #endregion
        
    except Exception as e:
        # #region agent log
        _debug_log("Aggressive fixture failed", {
            "error": str(e),
            "error_type": type(e).__name__
        }, "K")
        # #endregion
        raise
