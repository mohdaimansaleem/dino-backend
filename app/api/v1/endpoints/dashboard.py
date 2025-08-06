"""
Dashboard endpoints for different user roles
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.core.security import get_current_user
from app.core.logging_config import get_logger
from app.models.dto import ApiResponse
# Dashboard service imported lazily to avoid circular imports

logger = get_logger(__name__)

router = APIRouter()


def _get_dashboard_service():
    """Lazy import of dashboard service to avoid circular imports"""
    from app.services.dashboard_service import dashboard_service
    return dashboard_service


@router.get("/dashboard/superadmin", response_model=ApiResponse)
async def get_superadmin_dashboard(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get super admin dashboard data"""
    logger.info(f"Super admin dashboard requested by user: {current_user.get('id')}")
    
    # Get user role from role_id
    from app.core.security import _get_user_role
    user_role = await _get_user_role(current_user)
    
    # Check if user has superadmin role
    if user_role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Super admin role required."
        )
    
    try:
        dashboard_data = await _get_dashboard_service().get_superadmin_dashboard_data(current_user)
        logger.info(f"Super admin dashboard data retrieved for user: {current_user.get('id')}")
        
        return ApiResponse(
            success=True,
            message="Super admin dashboard data retrieved successfully",
            data=dashboard_data
        )
    except Exception as e:
        logger.error(f"Error retrieving super admin dashboard data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load dashboard data"
        )


@router.get("/dashboard/admin", response_model=ApiResponse)
async def get_admin_dashboard(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get admin dashboard data for venue"""
    logger.info(f"Admin dashboard requested by user: {current_user.get('id')}")
    
    # Get user role from role_id
    from app.core.security import _get_user_role
    user_role = await _get_user_role(current_user)
    
    # Check if user has admin role
    if user_role not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin role required."
        )
    
    # Check if user has venue assigned (except for superadmin)
    venue_id = current_user.get('venue_id')
    if user_role != "superadmin" and not venue_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No venue assigned. Please contact your administrator to assign you to a venue."
        )
    
    try:
        dashboard_data = await _get_dashboard_service().get_admin_dashboard_data(venue_id, current_user)
        logger.info(f"Admin dashboard data retrieved for user: {current_user.get('id')}, venue: {venue_id}")
        
        return ApiResponse(
            success=True,
            message="Admin dashboard data retrieved successfully",
            data=dashboard_data
        )
    except Exception as e:
        logger.error(f"Error retrieving admin dashboard data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load dashboard data"
        )


@router.get("/dashboard/operator", response_model=ApiResponse)
async def get_operator_dashboard(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get operator dashboard data for venue"""
    logger.info(f"Operator dashboard requested by user: {current_user.get('id')}")
    
    # Get user role from role_id
    from app.core.security import _get_user_role
    user_role = await _get_user_role(current_user)
    
    # Check if user has operator role
    if user_role not in ["operator", "admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Operator role required."
        )
    
    # Check if user has venue assigned (except for superadmin)
    venue_id = current_user.get('venue_id')
    if user_role != "superadmin" and not venue_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No venue assigned. Please contact your administrator to assign you to a venue."
        )
    
    try:
        dashboard_data = await _get_dashboard_service().get_operator_dashboard_data(venue_id, current_user)
        logger.info(f"Operator dashboard data retrieved for user: {current_user.get('id')}, venue: {venue_id}")
        
        return ApiResponse(
            success=True,
            message="Operator dashboard data retrieved successfully",
            data=dashboard_data
        )
    except Exception as e:
        logger.error(f"Error retrieving operator dashboard data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load dashboard data"
        )


@router.get("/dashboard", response_model=ApiResponse)
async def get_dashboard(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get dashboard data based on user role"""
    logger.info(f"Dashboard requested by user: {current_user.get('id')}")
    
    try:
        # Get user role from role_id
        from app.core.security import _get_user_role
        user_role = await _get_user_role(current_user)
        venue_id = current_user.get('venue_id')
        
        logger.info(f"Dashboard requested by user: {current_user.get('id')}, role: {user_role}")
        
        # Route to appropriate dashboard based on role
        if user_role == "superadmin":
            dashboard_data = await _get_dashboard_service().get_superadmin_dashboard_data(current_user)
        elif user_role == "admin":
            # Check if user has venue assigned
            if not venue_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No venue assigned. Please contact your administrator to assign you to a venue."
                )
            dashboard_data = await _get_dashboard_service().get_admin_dashboard_data(venue_id, current_user)
        elif user_role == "operator":
            # Check if user has venue assigned
            if not venue_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No venue assigned. Please contact your administrator to assign you to a venue."
                )
            dashboard_data = await _get_dashboard_service().get_operator_dashboard_data(venue_id, current_user)
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Dashboard access not available for your role."
            )
        
        return ApiResponse(
            success=True,
            message=f"{user_role.title()} dashboard data retrieved successfully",
            data=dashboard_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving dashboard data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load dashboard data"
        )


@router.get("/dashboard/stats", response_model=ApiResponse)
async def get_dashboard_stats(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get general dashboard statistics"""
    logger.info(f"Dashboard stats requested by user: {current_user.get('id')}")
    
    try:
        # Get user role from role_id
        from app.core.security import _get_user_role
        user_role = await _get_user_role(current_user)
        venue_id = current_user.get('venue_id')
        
        # Return basic stats that can be used across different dashboards
        stats = {
            "user_id": current_user.get('id'),
            "user_role": user_role,
            "venue_id": venue_id,
            "workspace_id": current_user.get('workspace_id'),
            "last_updated": datetime.utcnow().isoformat(),
        }
        
        # Add role-specific stats
        if venue_id:
            venue_data = await _get_dashboard_service().get_admin_dashboard_data(venue_id, current_user)
            stats.update({
                "today_orders": venue_data["summary"]["today_orders"],
                "today_revenue": venue_data["summary"]["today_revenue"],
                "occupied_tables": venue_data["summary"]["occupied_tables"],
                "total_tables": venue_data["summary"]["total_tables"],
            })
        
        return ApiResponse(
            success=True,
            message="Dashboard statistics retrieved successfully",
            data=stats
        )
    except Exception as e:
        logger.error(f"Error retrieving dashboard stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load dashboard statistics"
        )


@router.get("/dashboard/live-orders/{venue_id}", response_model=ApiResponse)
async def get_live_order_status(venue_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get live order status for a venue"""
    logger.info(f"Live order status requested for venue: {venue_id} by user: {current_user.get('id')}")
    
    # Get user role from role_id
    from app.core.security import _get_user_role
    user_role = await _get_user_role(current_user)
    
    # Check permissions
    if user_role not in ["admin", "operator", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin or operator role required."
        )
    
    # Check venue access (except for superadmin)
    if user_role != "superadmin" and current_user.get('venue_id') != venue_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You can only view data for your assigned venue."
        )
    
    try:
        live_data = await _get_dashboard_service().get_live_order_status(venue_id)
        
        return ApiResponse(
            success=True,
            message="Live order status retrieved successfully",
            data=live_data
        )
    except Exception as e:
        logger.error(f"Error retrieving live order status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load live order status"
        )


@router.get("/dashboard/live-tables/{venue_id}", response_model=ApiResponse)
async def get_live_table_status(venue_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get live table status for a venue"""
    logger.info(f"Live table status requested for venue: {venue_id} by user: {current_user.get('id')}")
    
    # Get user role from role_id
    from app.core.security import _get_user_role
    user_role = await _get_user_role(current_user)
    
    # Check permissions
    if user_role not in ["admin", "operator", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin or operator role required."
        )
    
    # Check venue access (except for superadmin)
    if user_role != "superadmin" and current_user.get('venue_id') != venue_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You can only view data for your assigned venue."
        )
    
    try:
        live_data = await _get_dashboard_service().get_live_table_status(venue_id)
        
        return ApiResponse(
            success=True,
            message="Live table status retrieved successfully",
            data=live_data
        )
    except Exception as e:
        logger.error(f"Error retrieving live table status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load live table status"
        )