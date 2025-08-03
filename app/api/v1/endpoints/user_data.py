"""
User Data API Endpoint
Provides comprehensive user data including venue, workspace, and related information
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends

from app.models.schemas import ApiResponse
from app.core.security import get_current_user
from app.database.firestore import (
    get_user_repo, get_venue_repo, get_workspace_repo, 
    get_menu_item_repo, get_table_repo, get_order_repo
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/user-data", 
            response_model=ApiResponse,
            summary="Get comprehensive user data",
            description="Get all data related to the current user including venue, workspace, and related information")
async def get_user_data(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get comprehensive user data for UI population"""
    try:
        logger.info(f"Getting user data for user: {current_user.get('id')}")
        
        # Get user role
        from app.core.security import _get_user_role
        user_role = await _get_user_role(current_user)
        
        # Initialize repositories
        user_repo = get_user_repo()
        venue_repo = get_venue_repo()
        workspace_repo = get_workspace_repo()
        menu_repo = get_menu_item_repo()
        table_repo = get_table_repo()
        order_repo = get_order_repo()
        
        # Get user's venue
        venue_id = current_user.get('venue_id')
        venue_data = None
        
        if venue_id:
            venue_data = await venue_repo.get_by_id(venue_id)
        elif user_role == 'superadmin':
            # For superadmin, get the first available venue
            all_venues = await venue_repo.get_all()
            if all_venues:
                venue_data = all_venues[0]
                venue_id = venue_data['id']
                logger.info(f"SuperAdmin assigned to first venue: {venue_id}")
        
        if not venue_data:
            logger.warning(f"No venue found for user: {current_user.get('id')}")
            return ApiResponse(
                success=False,
                message="No venue assigned to user",
                data=None
            )
        
        # Get workspace data
        workspace_id = venue_data.get('workspace_id') or current_user.get('workspace_id')
        workspace_data = None
        if workspace_id:
            workspace_data = await workspace_repo.get_by_id(workspace_id)
        
        # Get venue-specific data with error handling for index issues
        try:
            venue_menu_items = await menu_repo.get_by_venue(venue_id)
        except Exception as e:
            logger.warning(f"Failed to get menu items, using fallback: {e}")
            venue_menu_items = []
            
        try:
            venue_tables = await table_repo.get_by_venue(venue_id)
        except Exception as e:
            logger.warning(f"Failed to get tables, using fallback: {e}")
            venue_tables = []
            
        try:
            venue_orders = await order_repo.get_by_venue(venue_id, limit=100)
        except Exception as e:
            logger.warning(f"Failed to get orders, using fallback: {e}")
            venue_orders = []
        
        # Sort data client-side to avoid Firestore index requirements
        venue_menu_items.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        venue_tables.sort(key=lambda x: x.get('table_number', 0))
        venue_orders.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Get venue users (for user management)
        venue_users = []
        if user_role in ['admin', 'superadmin']:
            try:
                venue_users = await user_repo.get_by_venue(venue_id)
            except Exception as e:
                logger.warning(f"Failed to get venue users, using fallback: {e}")
                venue_users = []
        
        # Calculate venue statistics
        total_orders = len(venue_orders)
        total_revenue = sum(order.get('total_amount', 0) for order in venue_orders if order.get('payment_status') == 'paid')
        active_tables = len([table for table in venue_tables if table.get('is_active', False)])
        total_menu_items = len(venue_menu_items)
        
        # Prepare response data
        response_data = {
            "user": {
                "id": current_user['id'],
                "email": current_user['email'],
                "first_name": current_user.get('first_name', ''),
                "last_name": current_user.get('last_name', ''),
                "phone": current_user.get('phone', ''),
                "role": user_role,
                "is_active": current_user.get('is_active', True),
                "venue_id": venue_id,
                "workspace_id": workspace_id,
                "created_at": current_user.get('created_at'),
                "updated_at": current_user.get('updated_at')
            },
            "venue": {
                "id": venue_data['id'],
                "name": venue_data['name'],
                "description": venue_data.get('description', ''),
                "location": venue_data.get('location', {}),
                "phone": venue_data.get('phone', ''),
                "email": venue_data.get('email', ''),
                "is_active": venue_data.get('is_active', False),
                "is_open": venue_data.get('is_open', False),
                "workspace_id": venue_data.get('workspace_id'),
                "created_at": venue_data.get('created_at'),
                "updated_at": venue_data.get('updated_at')
            },
            "workspace": workspace_data if workspace_data else None,
            "statistics": {
                "total_orders": total_orders,
                "total_revenue": total_revenue,
                "active_tables": active_tables,
                "total_tables": len(venue_tables),
                "total_menu_items": total_menu_items,
                "total_users": len(venue_users)
            },
            "menu_items": venue_menu_items[:20],  # Recent menu items
            "tables": venue_tables,
            "recent_orders": venue_orders[:10],  # Recent orders
            "users": venue_users if user_role in ['admin', 'superadmin'] else [],
            "permissions": {
                "can_manage_menu": user_role in ['admin', 'superadmin'],
                "can_manage_tables": user_role in ['admin', 'superadmin'],
                "can_manage_orders": True,  # All roles can manage orders
                "can_manage_users": user_role in ['admin', 'superadmin'],
                "can_view_analytics": user_role in ['admin', 'superadmin'],
                "can_manage_venue": user_role == 'superadmin'
            }
        }
        
        logger.info(f"User data retrieved successfully for venue: {venue_id}")
        return ApiResponse(
            success=True,
            message="User data retrieved successfully",
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"Error getting user data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user data: {str(e)}"
        )


@router.get("/venue-data/{venue_id}",
            response_model=ApiResponse,
            summary="Get venue-specific data",
            description="Get all data for a specific venue (for superadmin switching venues)")
async def get_venue_data(
    venue_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get venue-specific data for venue switching"""
    try:
        # Get user role
        from app.core.security import _get_user_role
        user_role = await _get_user_role(current_user)
        
        # Only superadmin can switch venues
        if user_role != 'superadmin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superadmin can access different venues"
            )
        
        # Initialize repositories
        venue_repo = get_venue_repo()
        menu_repo = get_menu_item_repo()
        table_repo = get_table_repo()
        order_repo = get_order_repo()
        user_repo = get_user_repo()
        
        # Get venue data
        venue_data = await venue_repo.get_by_id(venue_id)
        if not venue_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Venue not found"
            )
        
        # Get venue-specific data with error handling
        try:
            venue_menu_items = await menu_repo.get_by_venue(venue_id)
        except Exception as e:
            logger.warning(f"Failed to get menu items: {e}")
            venue_menu_items = []
            
        try:
            venue_tables = await table_repo.get_by_venue(venue_id)
        except Exception as e:
            logger.warning(f"Failed to get tables: {e}")
            venue_tables = []
            
        try:
            venue_orders = await order_repo.get_by_venue(venue_id, limit=100)
        except Exception as e:
            logger.warning(f"Failed to get orders: {e}")
            venue_orders = []
            
        try:
            venue_users = await user_repo.get_by_venue(venue_id)
        except Exception as e:
            logger.warning(f"Failed to get users: {e}")
            venue_users = []
        
        # Sort data client-side to avoid Firestore index requirements
        venue_menu_items.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        venue_tables.sort(key=lambda x: x.get('table_number', 0))
        venue_orders.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Calculate statistics
        total_orders = len(venue_orders)
        total_revenue = sum(order.get('total_amount', 0) for order in venue_orders if order.get('payment_status') == 'paid')
        active_tables = len([table for table in venue_tables if table.get('is_active', False)])
        
        response_data = {
            "venue": venue_data,
            "statistics": {
                "total_orders": total_orders,
                "total_revenue": total_revenue,
                "active_tables": active_tables,
                "total_tables": len(venue_tables),
                "total_menu_items": len(venue_menu_items),
                "total_users": len(venue_users)
            },
            "menu_items": venue_menu_items[:20],
            "tables": venue_tables,
            "recent_orders": venue_orders[:10],
            "users": venue_users
        }
        
        return ApiResponse(
            success=True,
            message="Venue data retrieved successfully",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting venue data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get venue data: {str(e)}"
        )


@router.get("/available-venues",
            response_model=ApiResponse,
            summary="Get available venues for superadmin",
            description="Get list of venues that superadmin can switch to")
async def get_available_venues(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get available venues for superadmin venue switching"""
    try:
        # Get user role
        from app.core.security import _get_user_role
        user_role = await _get_user_role(current_user)
        
        # Only superadmin can see all venues
        if user_role != 'superadmin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superadmin can access venue list"
            )
        
        venue_repo = get_venue_repo()
        all_venues = await venue_repo.get_all()
        
        # Return simplified venue list
        venues = [
            {
                "id": venue['id'],
                "name": venue['name'],
                "description": venue.get('description', ''),
                "is_active": venue.get('is_active', False),
                "is_open": venue.get('is_open', False),
                "location": venue.get('location', {})
            }
            for venue in all_venues
        ]
        
        return ApiResponse(
            success=True,
            message="Available venues retrieved successfully",
            data={"venues": venues}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting available venues: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available venues: {str(e)}"
        )