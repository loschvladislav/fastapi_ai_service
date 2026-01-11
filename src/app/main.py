import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1 import api_keys, chat, summarize, translate, usage
from app.config import settings
from app.core.logging import setup_logging
from app.core.rate_limit import limiter
from app.services.cache_service import cache_service

# Setup logging
setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    await cache_service.connect()
    yield
    await cache_service.disconnect()


app = FastAPI(
    title="AI Service API",
    description="FastAPI microservice with OpenAI GPT integration",
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Routers
app.include_router(api_keys.router, prefix="/api/v1")
app.include_router(usage.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(summarize.router, prefix="/api/v1")
app.include_router(translate.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "cache": cache_service.is_connected}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.debug,
    )
