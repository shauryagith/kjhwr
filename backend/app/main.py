from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
from app.core.config import settings
from app.core.logging import logger
from app.api.routes import router as api_router
from app.repositories.data_store import data_store
from app.services.ingestion import ingestion_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}...")
    if not data_store.has_data():
        logger.warning("Cache is empty at startup. Attempting initial January 2026 data load...")
        try:
            await ingestion_service.fetch_month_data(year=2026, month=1, force_refresh=False)
        except Exception as e:
            logger.error(f"Initial ingestion failed during startup: {e}")
    else:
        stats = data_store.get_stats()
        logger.info(
            f"DataStore initialized from cache: {stats['actualsCount']} actuals, {stats['forecastsCount']} forecasts."
        )
    yield
    logger.info("Application shutdown completed.")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="UK Wind Forecast & Day-Ahead Procurement Intelligence Platform for Gridbricks",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected server error occurred."}
    )


# Mount API routes
app.include_router(api_router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/v1/health",
        "metadata": "/api/v1/metadata",
        "summary": "/api/v1/analysis/summary"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
