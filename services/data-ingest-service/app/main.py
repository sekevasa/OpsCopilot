"""Main application factory."""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from shared.config import get_settings
from shared.database import db
from shared.logger import setup_logging
from .api.routes import router as ingest_router


def create_app() -> FastAPI:
    """Create FastAPI application."""
    settings = get_settings()
    settings.service_name = "data-ingest-service"

    # Setup logging
    logger = setup_logging(settings.service_name)

    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        docs_url=settings.api_docs_url,
        redoc_url=settings.api_redoc_url,
    )

    # Include routers
    app.include_router(ingest_router)

    # Error handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        """Handle validation errors."""
        return JSONResponse(
            status_code=422,
            content={
                "detail": exc.errors(),
                "body": exc.body,
            },
        )

    # Lifecycle events
    @app.on_event("startup")
    async def startup():
        """Initialize on startup."""
        logger.info(f"Starting {settings.service_name}")
        await db.initialize()
        try:
            await db.create_tables()
        except Exception as e:
            logger.warning(
                f"Database initialization failed: {type(e).__name__}: {e}")
            logger.warning("Continuing without database (mock mode)")

    @app.on_event("shutdown")
    async def shutdown():
        """Cleanup on shutdown."""
        logger.info(f"Shutting down {settings.service_name}")
        try:
            await db.close()
        except Exception:
            pass  # Ignore close errors

    return app


app = create_app()
