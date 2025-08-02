"""
Dino Multi-Venue Platform - Main API Router
Simplified router with core endpoints and roles/permissions
"""
from fastapi import APIRouter
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Import core endpoints
from app.api.v1.endpoints import (
    user,
    venue, 
    workspace,
    menu,
    table,
    order,
    auth,
    health,
    roles,
    permissions
)

api_router = APIRouter()

# =============================================================================
# CORE MANAGEMENT ENDPOINTS
# =============================================================================

# User Management
api_router.include_router(
    user.router, 
    prefix="/users", 
    tags=["users"],
    responses={
        404: {"description": "User not found"},
        403: {"description": "Access denied"},
        401: {"description": "Authentication required"}
    }
)

# Venue Management
api_router.include_router(
    venue.router, 
    prefix="/venues", 
    tags=["venues"],
    responses={
        404: {"description": "Venue not found"},
        403: {"description": "Access denied"},
        401: {"description": "Authentication required"}
    }
)

# Workspace Management
api_router.include_router(
    workspace.router, 
    prefix="/workspaces", 
    tags=["workspaces"],
    responses={
        404: {"description": "Workspace not found"},
        403: {"description": "Access denied"},
        401: {"description": "Authentication required"}
    }
)

# Menu Management
api_router.include_router(
    menu.router, 
    prefix="/menu", 
    tags=["menu"],
    responses={
        404: {"description": "Menu item/category not found"},
        403: {"description": "Access denied"},
        401: {"description": "Authentication required"}
    }
)

# Table Management
api_router.include_router(
    table.router, 
    prefix="/tables", 
    tags=["tables"],
    responses={
        404: {"description": "Table not found"},
        403: {"description": "Access denied"},
        401: {"description": "Authentication required"}
    }
)

# Order Management
api_router.include_router(
    order.router, 
    prefix="/orders", 
    tags=["orders"],
    responses={
        404: {"description": "Order not found"},
        403: {"description": "Access denied"},
        401: {"description": "Authentication required"}
    }
)

# =============================================================================
# AUTHENTICATION ENDPOINTS
# =============================================================================

# Authentication & Registration
api_router.include_router(
    auth.router, 
    prefix="/auth", 
    tags=["authentication"],
    responses={
        401: {"description": "Authentication failed"},
        400: {"description": "Invalid credentials"},
        409: {"description": "User already exists"}
    }
)

# Health Check Endpoints
api_router.include_router(
    health.router, 
    prefix="/health", 
    tags=["health"],
    responses={
        200: {"description": "Health check successful"},
        503: {"description": "Service unavailable"}
    }
)

# =============================================================================
# ROLE AND PERMISSION MANAGEMENT ENDPOINTS
# =============================================================================

# Roles Management
api_router.include_router(
    roles.router, 
    prefix="/roles", 
    tags=["roles"],
    responses={
        404: {"description": "Role not found"},
        403: {"description": "Access denied"},
        401: {"description": "Authentication required"},
        400: {"description": "Invalid role data"}
    }
)

# Permissions Management
api_router.include_router(
    permissions.router, 
    prefix="/permissions", 
    tags=["permissions"],
    responses={
        404: {"description": "Permission not found"},
        403: {"description": "Access denied"},
        401: {"description": "Authentication required"},
        400: {"description": "Invalid permission data"}
    }
)

# =============================================================================
# API HEALTH CHECK
# =============================================================================

@api_router.get(
    "/health",
    summary="API Health Check",
    description="Check if the API is healthy and responsive",
    tags=["health"]
)
async def api_health_check():
    """API health check endpoint"""
    
    return {
        "status": "healthy", 
        "service": "dino-multi-venue-platform",
        "version": "2.0.0",
        "endpoints": {
            "core_management": [
                "users", "venues", "workspaces", 
                "menu", "tables", "orders", "auth"
            ],
            "role_management": ["roles", "permissions"]
        },
        "architecture": {
            "multi_tenancy": "Workspace-based isolation",
            "role_based_access": "Three-tier hierarchy with permissions",
            "authentication": "JWT-based authentication"
        }
    }

# =============================================================================
# API STATISTICS ENDPOINT
# =============================================================================

@api_router.get(
    "/stats",
    summary="API Statistics",
    description="Get API usage statistics and endpoint information",
    tags=["statistics"]
)
async def get_api_statistics():
    """Get API statistics"""
    return {
        "total_endpoints": len([
            route for route in api_router.routes 
            if hasattr(route, 'methods')
        ]),
        "endpoint_groups": {
            "core_management": 6,
            "authentication": 1,
            "role_management": 2,
            "utility": 2
        },
        "features": {
            "authentication": "JWT-based with role hierarchy",
            "authorization": "Role-based access control (SuperAdmin/Admin/Operator)",
            "multi_tenancy": "Workspace-based isolation",
            "role_management": "Comprehensive role and permission system"
        },
        "data_models": {
            "workspaces": "Multi-tenant isolation",
            "users": "Role-based permissions",
            "venues": "Business management",
            "menu": "Categories and items",
            "tables": "QR code integration",
            "orders": "Complete lifecycle management",
            "roles": "Permission-based access control",
            "permissions": "Granular access management"
        }
    }