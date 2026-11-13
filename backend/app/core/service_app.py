"""Builds one FastAPI app per microservice from the shared Lab 1 code.

Each entrypoint in app/entrypoints/ passes only the routers that service owns.
Every service gets the same CORS policy, error handlers, and two health
endpoints:

- GET /health/live  -> 200 while the process is serving requests.
- GET /health       -> 200 when required dependencies (MySQL, MongoDB, Kafka)
                       are reachable, 503 otherwise. Docker's HEALTHCHECK and
                       compose `depends_on: service_healthy` use this one.
"""

import logging
from collections.abc import Iterable
from types import ModuleType

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.health import run_checks


def create_service_app(
    service: str,
    routers: Iterable[ModuleType],
    *,
    description: str,
    serve_profile_pictures: bool = False,
    check_platform: bool = False,
    check_ollama: bool = False,
) -> FastAPI:
    app = FastAPI(title=f"Handshake {service} service (Pair {settings.pair})", description=description)

    # Kafka publish results ("p17.events") go to stdout next to uvicorn's access log.
    p17_logger = logging.getLogger("p17")
    if not p17_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(f"%(asctime)s %(levelname)s [{service}] %(message)s"))
        p17_logger.addHandler(handler)
        p17_logger.setLevel(logging.INFO)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)

    for router_module in routers:
        app.include_router(router_module.router)

    if serve_profile_pictures:
        from fastapi.staticfiles import StaticFiles

        from app.services.file_service import PICTURE_DIR, ensure_upload_dirs

        ensure_upload_dirs()
        app.mount("/uploads/profile_pictures", StaticFiles(directory=PICTURE_DIR), name="profile_pictures")

    @app.get("/health/live", tags=["health"], summary="Liveness probe")
    def live() -> dict[str, str]:
        return {"status": "ok", "service": service}

    @app.get("/health", tags=["health"], summary="Readiness probe with dependency checks")
    def health() -> JSONResponse:
        healthy, checks = run_checks(include_platform=check_platform, include_ollama=check_ollama)
        return JSONResponse(
            status_code=200 if healthy else 503,
            content={"status": "ok" if healthy else "degraded", "service": service, "checks": checks},
        )

    return app
