"""
Health Check API Endpoints
Simple endpoints to test API functionality
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
from datetime import datetime
import time

from app.models.dto import ApiResponse
from app.core.auth_dependencies import get_auth_status, get_conditional_current_user
from fastapi import Depends

router = APIRouter()


@router.get("/ping", response_model=ApiResponse)
async def ping():
    """Simple ping endpoint"""
    return ApiResponse(
        success=True,
        message="pong",
        data={
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy"
        }
    )


@router.get("/health", response_model=ApiResponse)
async def health_check():
    """Basic health check"""
    start_time = time.time()
    
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "response_time_ms": 0,
        "services": {
            "api": True,
            "database": False
        }
    }
    
    # Test database connection
    try:
        from app.database.firestore import get_user_repo
        user_repo = get_user_repo()
        
        # Simple database test - just check if we can connect
        await user_repo.exists("test-connection")
        health_data["services"]["database"] = True
        
    except Exception as e:
        health_data["services"]["database"] = False
        health_data["database_error"] = str(e)
    
    health_data["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
    
    return ApiResponse(
        success=True,
        message="Health check completed",
        data=health_data
    )


@router.get("/test-auth", response_model=ApiResponse)
async def test_auth():
    """Test authentication system without actual login"""
    try:
        from app.database.firestore import get_user_repo, get_role_repo
        
        user_repo = get_user_repo()
        role_repo = get_role_repo()
        
        # Test basic database operations
        test_results = {
            "user_repo_available": False,
            "role_repo_available": False,
            "can_query_users": False,
            "can_query_roles": False
        }
        
        # Test user repository
        try:
            test_results["user_repo_available"] = True
            # Try a simple query
            users = await user_repo.query([("is_active", "==", True)], limit=1)
            test_results["can_query_users"] = True
            test_results["sample_users_found"] = len(users)
        except Exception as e:
            test_results["user_query_error"] = str(e)
        
        # Test role repository
        try:
            test_results["role_repo_available"] = True
            # Try a simple query
            roles = await role_repo.get_all()
            test_results["can_query_roles"] = True
            test_results["roles_found"] = len(roles)
        except Exception as e:
            test_results["role_query_error"] = str(e)
        
        return ApiResponse(
            success=True,
            message="Auth system test completed",
            data=test_results
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Auth system test failed: {str(e)}",
            data={"error": str(e)}
        )


@router.get("/auth-status", response_model=ApiResponse)
async def auth_status():
    """Get current authentication configuration status"""
    try:
        auth_config = get_auth_status()
        
        return ApiResponse(
            success=True,
            message="Authentication status retrieved",
            data=auth_config
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Failed to get auth status: {str(e)}",
            data={"error": str(e)}
        )


@router.get("/test-conditional-auth", response_model=ApiResponse)
async def test_conditional_auth(current_user: Dict[str, Any] = Depends(get_conditional_current_user)):
    """Test conditional authentication (works with both JWT and development mode)"""
    try:
        user_info = {
            "user_id": current_user.get("id"),
            "email": current_user.get("email"),
            "role": current_user.get("role"),
            "first_name": current_user.get("first_name"),
            "last_name": current_user.get("last_name"),
            "is_active": current_user.get("is_active"),
            "workspace_id": current_user.get("workspace_id"),
            "venue_ids": current_user.get("venue_ids", [])
        }
        
        auth_config = get_auth_status()
        
        return ApiResponse(
            success=True,
            message="Conditional authentication test successful",
            data={
                "user": user_info,
                "auth_config": auth_config,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Conditional auth test failed: {str(e)}",
            data={"error": str(e)}
        )


@router.post("/test-login", response_model=ApiResponse)
async def test_login_process():
    """Test the login process without credentials"""
    try:
        from app.services.auth_service import auth_service
        
        # Test if auth service is available
        test_results = {
            "auth_service_available": True,
            "can_create_service": True,
            "service_methods": []
        }
        
        # Check available methods
        methods = [method for method in dir(auth_service) if not method.startswith('_')]
        test_results["service_methods"] = methods[:10]  # First 10 methods
        
        return ApiResponse(
            success=True,
            message="Login process test completed",
            data=test_results
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Login process test failed: {str(e)}",
            data={"error": str(e)}
        )


@router.get("/security-status", response_model=ApiResponse)
async def security_status():
    """Get security configuration status and recommendations"""
    try:
        from app.core.config import validate_configuration, settings
        from app.core.security_middleware import get_security_middleware_config
        
        # Validate configuration
        config_validation = validate_configuration()
        
        # Get security middleware status
        middleware_config = get_security_middleware_config()
        
        # Security recommendations
        recommendations = []
        warnings = []
        
        # Check critical security settings
        if hasattr(settings, 'SECRET_KEY') and "CHANGE-THIS" in settings.SECRET_KEY:
            warnings.append("Default SECRET_KEY detected - MUST be changed in production")
        
        if not settings.is_jwt_auth_enabled and settings.is_production:
            warnings.append("JWT authentication disabled in production environment")
        
        if "*" in settings.CORS_ORIGINS:
            warnings.append("CORS wildcard detected - not recommended for production")
        
        if settings.is_production and settings.DEBUG:
            warnings.append("DEBUG mode enabled in production")
        
        # Generate recommendations
        if not settings.is_production:
            recommendations.append("Enable JWT authentication for production deployment")
            recommendations.append("Configure specific CORS origins for production")
            recommendations.append("Set strong SECRET_KEY for production")
        
        security_status_data = {
            "environment": settings.ENVIRONMENT,
            "jwt_auth_enabled": settings.is_jwt_auth_enabled,
            "security_middleware": middleware_config,
            "configuration_valid": config_validation["valid"],
            "warnings": warnings + config_validation.get("warnings", []),
            "errors": config_validation.get("errors", []),
            "recommendations": recommendations,
            "security_features": {
                "password_hashing": "bcrypt with configurable rounds",
                "jwt_security": "Enhanced with audience/issuer validation",
                "rate_limiting": "IP-based with auth endpoint protection",
                "security_headers": "Comprehensive security headers",
                "request_validation": "Input sanitization and size limits",
                "development_mode_protection": "Warnings and logging"
            }
        }
        
        return ApiResponse(
            success=True,
            message="Security status retrieved",
            data=security_status_data
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Failed to get security status: {str(e)}",
            data={"error": str(e)}
        )


@router.get("/password-hash-info", response_model=ApiResponse)
async def get_password_hash_info():
    """Get information for implementing client-side password hashing"""
    try:
        from app.core.unified_password_security import get_client_hashing_info
        
        hash_info = get_client_hashing_info()
        
        return ApiResponse(
            success=True,
            message="Password hashing information retrieved",
            data=hash_info
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Failed to get password hash info: {str(e)}",
            data={"error": str(e)}
        )