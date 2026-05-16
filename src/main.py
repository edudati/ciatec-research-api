from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from src.core.config import get_settings
from src.core.database import engine
from src.core.docs_branding import (
    API_DESCRIPTION_MARKDOWN,
    register_branding_static_and_docs,
)
from src.core.middleware import register_cors, register_exception_handlers
from src.modules.auth.router import router as auth_router
from src.modules.catalog.router_admin import (
    catalog_node_mirror_router,
)
from src.modules.catalog.router_admin import (
    router as admin_catalog_router,
)
from src.modules.catalog.router_public import router as catalog_router
from src.modules.health.router import router as health_router
from src.modules.health_conditions.router import router as health_conditions_router
from src.modules.instruments.router import router as instruments_router
from src.modules.matches.router import router as matches_router
from src.modules.participant_conditions.router import (
    router as participant_conditions_router,
)
from src.modules.participants.router import router as participants_router
from src.modules.progress.router import router as progress_router
from src.modules.project_assessments.router import router as project_assessments_router
from src.modules.project_enrollments.router import router as project_enrollments_router
from src.modules.project_exports.router import router as project_exports_router
from src.modules.project_groups.router import router as project_groups_router
from src.modules.project_interventions.router import (
    router as project_interventions_router,
)
from src.modules.project_members.router import router as project_members_router
from src.modules.project_questionnaires.router import (
    router as project_questionnaires_router,
)
from src.modules.projects.router import router as projects_router
from src.modules.self_report.router import router as self_report_router
from src.modules.sessions.router import router as sessions_router
from src.modules.telemetry.bestbeat.router import router as bestbeat_router
from src.modules.telemetry.bubbles.router import router as bubbles_router
from src.modules.telemetry.trunktilt.router import router as trunktilt_router
from src.modules.timeline.router import router as timeline_router
from src.modules.timeline.runtime import (
    init_timeline_runtime,
    shutdown_timeline_runtime,
)
from src.modules.users.router import router as users_router
from src.modules.vocabulary.router import router as vocabulary_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    await init_timeline_runtime(settings)
    yield
    await shutdown_timeline_runtime()
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="CIATec Research API",
        version="1.0.0",
        lifespan=lifespan,
        description=API_DESCRIPTION_MARKDOWN,
        docs_url=None,
        redoc_url=None,
    )
    register_cors(app, settings)
    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(health_conditions_router)
    app.include_router(instruments_router)
    app.include_router(vocabulary_router)
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(participants_router)
    app.include_router(participant_conditions_router)
    app.include_router(projects_router)
    app.include_router(project_exports_router)
    app.include_router(project_groups_router)
    app.include_router(project_members_router)
    app.include_router(project_enrollments_router)
    app.include_router(project_assessments_router)
    app.include_router(project_interventions_router)
    app.include_router(project_questionnaires_router)
    app.include_router(self_report_router)
    app.include_router(timeline_router)
    app.include_router(catalog_router)
    app.include_router(catalog_node_mirror_router)
    app.include_router(admin_catalog_router)
    app.include_router(sessions_router)
    app.include_router(matches_router)
    app.include_router(progress_router)
    app.include_router(trunktilt_router)
    app.include_router(bubbles_router)
    app.include_router(bestbeat_router)
    register_branding_static_and_docs(app)

    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            routes=app.routes,
        )
        openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})[
            "bearerAuth"
        ] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Access token from login, register, or refresh.",
        }
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi  # type: ignore[method-assign]
    return app


app = create_app()
