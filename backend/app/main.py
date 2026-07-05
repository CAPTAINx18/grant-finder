import logging
import time
from typing import Dict, Any
import redis.asyncio as aioredis
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import check_db_connection
from app.api.v1.api import api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

async def seed_crawler_sources() -> None:
    import sys
    if "pytest" in sys.modules:
        logger.info("Running in pytest environment. Skipping database seeding.")
        return

    from app.core.database import SessionLocal
    from app.models.grant_source_registry import GrantSourceRegistry
    from sqlalchemy import select

    sources_to_seed = [
        {
            "name": "Startup India schemes portal",
            "url": "https://www.startupindia.gov.in/content/sih/en/government-schemes.html",
            "update_method": "startup_india",
            "cron_schedule": "0 0 * * *",
            "is_active": True
        },
        {
            "name": "BIRAC Call for Proposals (CFP)",
            "url": "https://www.birac.nic.in/cfp.php",
            "update_method": "birac",
            "cron_schedule": "0 2 * * *",
            "is_active": True
        },
        {
            "name": "World Bank India Projects API",
            "url": "http://search.worldbank.org/api/v2/projects",
            "update_method": "world_bank",
            "cron_schedule": "0 4 * * *",
            "is_active": True
        },
        {
            "name": "Horizon Europe (India Eligible)",
            "url": "https://api.tech.ec.europa.eu/search-api/prod/rest/search",
            "update_method": "horizon_europe_india",
            "cron_schedule": "0 6 * * *",
            "is_active": True
        }
    ]

    from app.core.config import settings
    if settings.ENABLE_MOCK_DATA:
        sources_to_seed.append({
            "name": "Mock Ingestion Source",
            "url": "https://mocksite.gov/api",
            "update_method": "mock",
            "cron_schedule": "*/5 * * * *",
            "is_active": True
        })

    async with SessionLocal() as db:
        # Cleanup mock grants and US-only grants from database
        from app.models.grant import Grant
        from sqlalchemy import delete
        
        await db.execute(delete(Grant).where(
            (Grant.official_source_link.like("https://mocksite.gov%")) | 
            (Grant.official_source_link.like("https://mocksite.org%"))
        ))
        
        await db.execute(delete(Grant).where(
            (Grant.country_eligibility == "US") | 
            (Grant.country_eligibility == "United States") |
            (Grant.country_eligibility == "USA")
        ))

        # Seed active sources
        for src_data in sources_to_seed:
            stmt = select(GrantSourceRegistry).where(GrantSourceRegistry.update_method == src_data["update_method"])
            res = await db.execute(stmt)
            exists = res.scalars().first()
            if not exists:
                logger.info(f"Seeding active crawler source: '{src_data['name']}'")
                source = GrantSourceRegistry(**src_data)
                db.add(source)
            else:
                exists.is_active = src_data["is_active"]

        from sqlalchemy import update
        active_methods = [s["update_method"] for s in sources_to_seed]
        stmt_deactivate = (
            update(GrantSourceRegistry)
            .where(GrantSourceRegistry.update_method.notin_(active_methods))
            .values(is_active=False)
        )
        await db.execute(stmt_deactivate)
        
        if not settings.ENABLE_MOCK_DATA:
            await db.execute(delete(GrantSourceRegistry).where(GrantSourceRegistry.update_method == "mock"))
            
        await db.commit()


@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up: Seeding crawler registries.")
    try:
        await seed_crawler_sources()
    except Exception as e:
        logger.error(f"Failed to seed crawler sources: {e}")

# Register routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# CORS configuration
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Basic middleware to log request execution times
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(f"Request {request.method} {request.url.path} completed in {process_time:.4f}s")
    return response


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception encountered: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred.",
            "error_code": "INTERNAL_SERVER_ERROR",
            "status_code": 500
        }
    )


@app.get("/")
async def root() -> Dict[str, str]:
    return {
        "message": "Welcome to the GrantFinder API. Discover and match global grant opportunities.",
        "version": "1.0.0",
        "docs": f"{settings.API_V1_STR}/docs"
    }


@app.get(f"{settings.API_V1_STR}/health")
async def health_check() -> JSONResponse:
    # 1. Check PostgreSQL connection
    db_healthy = await check_db_connection()

    # 2. Check Redis connection
    redis_healthy = False
    redis_latency_ms = -1.0
    try:
        start_time = time.time()
        client = aioredis.from_url(settings.REDIS_URL, socket_timeout=2.0)
        pong = await client.ping()
        redis_latency_ms = (time.time() - start_time) * 1000
        if pong:
            redis_healthy = True
        await client.close()
    except Exception as e:
        logger.error(f"Redis connection check failed: {e}")

    # Determine overall status
    is_healthy = db_healthy and redis_healthy
    status_code = status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": f"{time.time()}",
            "version": "1.0.0",
            "services": {
                "database": {
                    "status": "healthy" if db_healthy else "unhealthy"
                },
                "redis": {
                    "status": "healthy" if redis_healthy else "unhealthy",
                    "latency_ms": round(redis_latency_ms, 2) if redis_healthy else None
                }
            }
        }
    )
