"""
AstraX AI — FastAPI Application Factory
Main entry point for the backend server.
"""

import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.config import settings
from app.db.models import init_db
from app.api.v1 import datasets, processing, detection, candidates, assistant, export, tasks, app_settings

logger = logging.getLogger("astrax")

# Track startup time
_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown."""
    # Startup
    logger.info("🚀 AstraX AI starting up...")
    settings.setup_dirs()
    await init_db()
    logger.info(f"📂 Data directory: {settings.data_dir.resolve()}")
    logger.info(f"💾 Database: {settings.database_url}")
    logger.info(f"🎯 GPU enabled: {settings.gpu_enabled}")
    logger.info("✅ AstraX AI ready")

    yield

    # Shutdown
    logger.info("🛑 AstraX AI shutting down...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Research-grade asteroid detection & astronomical image analysis platform. "
            "Ingest FITS datasets, perform advanced image processing, detect moving "
            "celestial candidates, and generate observation reports."
        ),
        lifespan=lifespan,
        default_response_class=ORJSONResponse,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # ── CORS ──
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request timing middleware ──
    @app.middleware("http")
    async def add_timing_header(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{elapsed:.4f}"
        return response

    # ── Health check ──
    @app.get("/api/v1/health", tags=["System"])
    async def health_check():
        """System health check endpoint."""
        gpu_available = False
        try:
            import cupy  # noqa: F401
            gpu_available = True
        except ImportError:
            pass

        return {
            "status": "healthy",
            "version": settings.app_version,
            "uptime_seconds": round(time.time() - _start_time, 2),
            "gpu_available": gpu_available,
            "app_name": settings.app_name,
        }

    from app.api.v1 import ws
    
    # ── Register routers ──
    api_prefix = "/api/v1"
    app.include_router(datasets.router, prefix=f"{api_prefix}/datasets", tags=["Datasets"])
    app.include_router(processing.router, prefix=f"{api_prefix}/processing", tags=["Processing"])
    app.include_router(detection.router, prefix=f"{api_prefix}/detection", tags=["Detection"])
    app.include_router(candidates.router, prefix=f"{api_prefix}/candidates", tags=["Candidates"])
    app.include_router(assistant.router, prefix=f"{api_prefix}/assistant", tags=["AI Assistant"])
    app.include_router(export.router, prefix=f"{api_prefix}/export", tags=["Export"])
    app.include_router(tasks.router, prefix=f"{api_prefix}/tasks", tags=["Tasks"])
    app.include_router(app_settings.router, prefix=f"{api_prefix}/settings", tags=["Settings"])
    
    # WebSocket
    app.include_router(ws.router, tags=["WebSockets"])

    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
