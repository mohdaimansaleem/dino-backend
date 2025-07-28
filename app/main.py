"""
Dino E-Menu Backend API
Production-ready FastAPI application for Google Cloud Run
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.core.config import settings, initialize_cloud_services, validate_configuration
from app.core.logging_config import setup_logging, get_logger
from app.api.v1.api import api_router

# Setup logging first
setup_logging(settings.LOG_LEVEL)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management for Cloud Run deployment"""
    # Startup
    logger.info("Starting Dino E-Menu API", extra={
        "environment": settings.ENVIRONMENT,
        "project_id": settings.GCP_PROJECT_ID,
        "database_id": settings.DATABASE_NAME,
        "debug_mode": settings.DEBUG
    })
    
    # Validate configuration
    config_validation = validate_configuration()
    if not config_validation["valid"]:
        logger.error("Configuration validation failed")
        for error in config_validation["errors"]:
            logger.error(f"Config error: {error}")
        if settings.is_production:
            raise RuntimeError("Critical: Configuration validation failed")
    
    for warning in config_validation["warnings"]:
        logger.warning(f"Config warning: {warning}")
    
    # Initialize cloud services
    try:
        success = initialize_cloud_services()
        if success:
            logger.info("Cloud services initialized successfully")
        else:
            logger.error("Failed to initialize cloud services")
            # In production, we might want to exit here
            if settings.is_production:
                raise RuntimeError("Critical: Cloud services initialization failed")
            
    except Exception as e:
        logger.error("Error during cloud services initialization", exc_info=True)
        if settings.is_production:
            raise
    
    logger.info("Dino E-Menu API startup completed successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Dino E-Menu API")


# Create FastAPI application
app = FastAPI(
    title="Dino E-Menu API",
    description="A comprehensive e-menu solution for restaurants and cafes",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Include API routes with enhanced documentation
app.include_router(api_router, prefix="/api/v1")

# Setup enhanced API documentation
from app.core.api_docs import setup_api_documentation
setup_api_documentation(app)


# =============================================================================
# HEALTH CHECK ENDPOINTS (Required for Cloud Run)
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Dino E-Menu API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run"""
    from app.core.config import cloud_manager
    
    # Basic health check
    health_status = {
        "status": "healthy",
        "service": "dino-api",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "project_id": settings.GCP_PROJECT_ID,
        "database_id": settings.DATABASE_NAME
    }
    
    # Add detailed health check for non-production environments
    if not settings.is_production:
        try:
            cloud_health = cloud_manager.health_check()
            health_status["services"] = {
                "firestore": "connected" if cloud_health["firestore"] else "failed",
                "storage": "connected" if cloud_health["storage"] else "failed"
            }
            if cloud_health["errors"]:
                health_status["errors"] = cloud_health["errors"]
        except Exception as e:
            health_status["services"] = {"error": str(e)}
    
    return health_status


@app.get("/readiness")
async def readiness_check():
    """Readiness check for Kubernetes/Cloud Run"""
    return {
        "status": "ready",
        "service": "dino-api",
        "timestamp": os.environ.get("STARTUP_TIME", "unknown")
    }


@app.get("/liveness")
async def liveness_check():
    """Liveness check for Cloud Run"""
    return {"status": "alive", "service": "dino-api"}


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.exception_handler(500)
async def internal_server_error(request, exc):
    """Handle internal server errors"""
    logger.error("Internal server error occurred", exc_info=True, extra={
        "request_url": str(request.url),
        "request_method": request.method
    })
    return {
        "error": "Internal server error",
        "message": "An unexpected error occurred",
        "status_code": 500
    }


# =============================================================================
# STARTUP FOR LOCAL DEVELOPMENT
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8080))
    
    logger.info(f"Starting server on port {port}")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
        log_level=settings.LOG_LEVEL.lower() if hasattr(settings, 'LOG_LEVEL') else "info",
        access_log=True,
        workers=1  # Single worker for Cloud Run
    )