from __future__ import annotations

import os

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from vigia_api.core.settings import get_settings
from vigia_api.routers import (
    account,
    alerts,
    auth,
    avisos,
    health,
    invitations,
    normas,
    reportes,
    search,
    stats,
    workspaces,
)

# Sentry — no-op si falta SENTRY_DSN.
log = logging.getLogger("vigia_api")

_sentry_dsn = os.environ.get("SENTRY_DSN")
if _sentry_dsn:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        sentry_sdk.init(
            dsn=_sentry_dsn,
            integrations=[StarletteIntegration(), FastApiIntegration()],
            traces_sample_rate=0.1,
            environment=os.environ.get("VIGIA_ENV", "dev"),
        )
    except Exception as exc:  # pragma: no cover
        print(f"[sentry] init failed: {exc!r}")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Vigía API",
        version="0.1.0",
        description="Backend de Vigía — inteligencia legislativa y regulatoria argentina.",
    )

    # Errores no manejados → 500 JSON *dentro* del CORS. Sin esto el 500 lo arma
    # el ServerErrorMiddleware (afuera del CORSMiddleware), sale sin
    # Access-Control-Allow-Origin y el browser lo reporta como "NetworkError"
    # en vez de mostrar el error real.
    @app.middleware("http")
    async def _errores_json(request: Request, call_next):
        try:
            return await call_next(request)
        except Exception:
            log.exception("error no manejado en %s %s", request.method, request.url.path)
            return JSONResponse({"detail": "internal_error"}, status_code=500)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(workspaces.router)
    app.include_router(account.router)
    app.include_router(invitations.router)
    app.include_router(alerts.router)
    app.include_router(reportes.router)
    app.include_router(normas.router)
    app.include_router(search.router)
    app.include_router(stats.router)
    app.include_router(avisos.router)
    return app


app = create_app()
