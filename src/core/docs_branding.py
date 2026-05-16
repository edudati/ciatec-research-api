"""Swagger / ReDoc with CIATec favicon and static branding assets."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles

BRANDING_MOUNT_PATH = "/static/branding"
BRANDING_ICON_URL = f"{BRANDING_MOUNT_PATH}/icon-32x32.svg"

BRANDING_DIR = Path(__file__).resolve().parents[1] / "static" / "branding"

API_DESCRIPTION_MARKDOWN = (
    f"![CIATec]({BRANDING_MOUNT_PATH}/logo-horizontal-light-102x32.svg)\n\n"
    "Documentação interativa da **CIATec Research API**. "
    f"Logo para fundo escuro: `{BRANDING_MOUNT_PATH}/logo-horizontal-dark-102x32.svg`."
)


def register_branding_static_and_docs(app: FastAPI) -> None:
    """Serve `/static/branding/*` and `/docs` + `/redoc` with CIATec favicon."""
    app.mount(
        BRANDING_MOUNT_PATH,
        StaticFiles(directory=str(BRANDING_DIR)),
        name="static_branding",
    )

    @app.get("/docs", include_in_schema=False)
    async def swagger_ui_html(req: Request) -> HTMLResponse:
        root = req.scope.get("root_path", "").rstrip("/")
        openapi_path = app.openapi_url or "/openapi.json"
        openapi_url = root + openapi_path
        oauth2_redirect_url = app.swagger_ui_oauth2_redirect_url
        if oauth2_redirect_url:
            oauth2_redirect_url = root + oauth2_redirect_url
        return get_swagger_ui_html(
            openapi_url=openapi_url,
            title=f"{app.title} - Swagger UI",
            oauth2_redirect_url=oauth2_redirect_url,
            init_oauth=app.swagger_ui_init_oauth,
            swagger_ui_parameters=app.swagger_ui_parameters,
            swagger_favicon_url=root + BRANDING_ICON_URL,
        )

    if app.swagger_ui_oauth2_redirect_url:

        @app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
        async def swagger_ui_redirect(_req: Request) -> HTMLResponse:
            return get_swagger_ui_oauth2_redirect_html()

    @app.get("/redoc", include_in_schema=False)
    async def redoc_html(req: Request) -> HTMLResponse:
        root = req.scope.get("root_path", "").rstrip("/")
        openapi_path = app.openapi_url or "/openapi.json"
        openapi_url = root + openapi_path
        return get_redoc_html(
            openapi_url=openapi_url,
            title=f"{app.title} - ReDoc",
            redoc_favicon_url=root + BRANDING_ICON_URL,
        )
