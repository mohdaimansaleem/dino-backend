"""
Dashboard endpoints for different user roles
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random

from app.core.security import get_current_user
from app.core.logging_config import get_logger
from app.models.schemas import User, ApiResponse

logger = get_logger(__name__)

router = APIRouter()

def generate_mock_dashboard_data(user: User, dashboard_type: str = "admin") -> Dict[str, Any]:
    """Generate mock dashboard data based on user role and venue"""
    
    # Base data that varies by venue
    base_multiplier = 1.0
    if user.venue_id:
        # Use venue_id to create consistent but varied data
        venue_hash = hash(user.venue_id) % 100
        base_multiplier = 0.5 + (venue_hash / 100)
    
    if dashboard_type == "superadmin":
        return {
            "summary": {
                "total_workspaces": random.randint(3, 8),
                "total_venues": random.randint(8, 25),
                "total_users": random.randint(30, 100),
                "total_orders": random.randint(500, 2000),
                "total_revenue": random.randint(50000, 200000),
                "active_venues": random.randint(6, 20),
            },
            "workspaces": [
                {
                    "id": f"ws_{i}",
                    "name": f"Restaurant Group {i}",
                    "venue_count": random.randint(1, 5),
                    "user_count": random.randint(5, 20),
                    "is_active": random.choice([True, True, True, False]),  # 75% active
                    "created_at": (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat(),
                }
                for i in range(1, random.randint(4, 7))
            ],
        }
    
    elif dashboard_type == "admin":
        return {
            "summary": {
                "today_orders": int(random.randint(8, 25) * base_multiplier),
                "today_revenue": int(random.randint(5000, 15000) * base_multiplier),
                "total_tables": random.randint(10, 30),
                "occupied_tables": random.randint(3, 15),
                "total_menu_items": random.randint(25, 60),
                "active_menu_items": random.randint(20, 55),
                "total_staff": random.randint(4, 12),
            },
            "recent_orders": [
                {
                    "id": f"order_{i}",
                    "order_number": f"ORD-{1000 + i:03d}",
                    "table_number": random.randint(1, 20),
                    "total_amount": random.randint(300, 1500),
                    "status": random.choice(["pending", "confirmed", "preparing", "ready", "served"]),
                    "created_at": (datetime.now() - timedelta(minutes=random.randint(5, 120))).isoformat(),
                }
                for i in range(1, random.randint(4, 8))
            ],
        }
    
    elif dashboard_type == "operator":
        active_orders_count = int(random.randint(3, 12) * base_multiplier)
        return {
            "summary": {
                "active_orders": active_orders_count,
                "pending_orders": random.randint(1, 4),
                "preparing_orders": random.randint(2, 6),
                "ready_orders": random.randint(0, 3),
                "occupied_tables": random.randint(5, 15),
                "total_tables": random.randint(15, 25),
            },
            "active_orders": [
                {
                    "id": f"active_order_{i}",
                    "order_number": f"ORD-{2000 + i:03d}",
                    "table_number": random.randint(1, 20),
                    "total_amount": random.randint(400, 1200),
                    "status": random.choice(["pending", "confirmed", "preparing", "ready"]),
                    "created_at": (datetime.now() - timedelta(minutes=random.randint(5, 60))).isoformat(),
                    "estimated_ready_time": (datetime.now() + timedelta(minutes=random.randint(5, 30))).isoformat(),
                    "items_count": random.randint(1, 6),
                }
                for i in range(1, min(active_orders_count + 1, 8))
            ],
        }
    
    return {}

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
        # Create a user-like object for the mock data generator
        user_obj = type('User', (), {
            'id': current_user.get('id'),
            'venue_id': current_user.get('venue_id'),
            'role': user_role
        })()
        
        dashboard_data = generate_mock_dashboard_data(user_obj, "superadmin")
        logger.info(f"Super admin dashboard data generated for user: {current_user.get('id')}")
        
        return ApiResponse(
            success=True,
            message="Super admin dashboard data retrieved successfully",
            data=dashboard_data
        )
    except Exception as e:
        logger.error(f"Error generating super admin dashboard data: {str(e)}")
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
        # Create a user-like object for the mock data generator
        user_obj = type('User', (), {
            'id': current_user.get('id'),
            'venue_id': venue_id,
            'role': user_role
        })()
        
        dashboard_data = generate_mock_dashboard_data(user_obj, "admin")
        logger.info(f"Admin dashboard data generated for user: {current_user.get('id')}, venue: {venue_id}")
        
        return ApiResponse(
            success=True,
            message="Admin dashboard data retrieved successfully",
            data=dashboard_data
        )
    except Exception as e:
        logger.error(f"Error generating admin dashboard data: {str(e)}")
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
        # Create a user-like object for the mock data generator
        user_obj = type('User', (), {
            'id': current_user.get('id'),
            'venue_id': venue_id,
            'role': user_role
        })()
        
        dashboard_data = generate_mock_dashboard_data(user_obj, "operator")
        logger.info(f"Operator dashboard data generated for user: {current_user.get('id')}, venue: {venue_id}")
        
        return ApiResponse(
            success=True,
            message="Operator dashboard data retrieved successfully",
            data=dashboard_data
        )
    except Exception as e:
        logger.error(f"Error generating operator dashboard data: {str(e)}")
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
        
        # Create a user-like object for the mock data generator
        user_obj = type('User', (), {
            'id': current_user.get('id'),
            'venue_id': venue_id,
            'role': user_role
        })()
        
        # Route to appropriate dashboard based on role
        if user_role == "superadmin":
            dashboard_data = generate_mock_dashboard_data(user_obj, "superadmin")
        elif user_role == "admin":
            # Check if user has venue assigned
            if not venue_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No venue assigned. Please contact your administrator to assign you to a venue."
                )
            dashboard_data = generate_mock_dashboard_data(user_obj, "admin")
        elif user_role == "operator":
            # Check if user has venue assigned
            if not venue_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No venue assigned. Please contact your administrator to assign you to a venue."
                )
            dashboard_data = generate_mock_dashboard_data(user_obj, "operator")
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
        logger.error(f"Error generating dashboard data: {str(e)}")
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
            "last_updated": datetime.now().isoformat(),
        }
        
        # Add role-specific stats
        if venue_id:
            # Create a user-like object for the mock data generator
            user_obj = type('User', (), {
                'id': current_user.get('id'),
                'venue_id': venue_id,
                'role': user_role
            })()
            
            venue_data = generate_mock_dashboard_data(user_obj, "admin")
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
        logger.error(f"Error generating dashboard stats: {str(e)}")
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
        # Generate mock live order data
        pending_orders = random.randint(1, 5)
        preparing_orders = random.randint(2, 6)
        ready_orders = random.randint(0, 3)
        
        live_data = {
            "summary": {
                "total_active_orders": pending_orders + preparing_orders + ready_orders,
                "pending_orders": pending_orders,
                "preparing_orders": preparing_orders,
                "ready_orders": ready_orders,
            },
            "orders_by_status": {
                "pending": [
                    {
                        "id": f"pending_{i}",
                        "order_number": f"ORD-P{i:03d}",
                        "table_number": random.randint(1, 20),
                        "total_amount": random.randint(300, 1000),
                        "status": "pending",
                        "created_at": (datetime.now() - timedelta(minutes=random.randint(1, 15))).isoformat(),
                    }
                    for i in range(1, pending_orders + 1)
                ],
                "preparing": [
                    {
                        "id": f"preparing_{i}",
                        "order_number": f"ORD-R{i:03d}",
                        "table_number": random.randint(1, 20),
                        "total_amount": random.randint(400, 1200),
                        "status": "preparing",
                        "created_at": (datetime.now() - timedelta(minutes=random.randint(5, 30))).isoformat(),
                    }
                    for i in range(1, preparing_orders + 1)
                ],
                "ready": [
                    {
                        "id": f"ready_{i}",
                        "order_number": f"ORD-Y{i:03d}",
                        "table_number": random.randint(1, 20),
                        "total_amount": random.randint(500, 1500),
                        "status": "ready",
                        "created_at": (datetime.now() - timedelta(minutes=random.randint(10, 45))).isoformat(),
                    }
                    for i in range(1, ready_orders + 1)
                ],
            }
        }
        
        return ApiResponse(
            success=True,
            message="Live order status retrieved successfully",
            data=live_data
        )
    except Exception as e:
        logger.error(f"Error generating live order status: {str(e)}")
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
        # Generate mock table data
        total_tables = random.randint(15, 25)
        tables = []
        available = 0
        occupied = 0
        reserved = 0
        maintenance = 0
        
        for i in range(1, total_tables + 1):
            status = random.choice(["available", "occupied", "reserved", "maintenance"])
            if status == "available":
                available += 1
            elif status == "occupied":
                occupied += 1
            elif status == "reserved":
                reserved += 1
            else:
                maintenance += 1
                
            tables.append({
                "id": f"table_{i}",
                "table_number": i,
                "capacity": random.choice([2, 4, 6, 8]),
                "status": status,
            })
        
        live_data = {
            "tables": tables,
            "summary": {
                "total_tables": total_tables,
                "available": available,
                "occupied": occupied,
                "reserved": reserved,
                "maintenance": maintenance,
            }
        }
        
        return ApiResponse(
            success=True,
            message="Live order status retrieved successfully",
            data=live_data
        )
    except Exception as e:
        logger.error(f"Error generating live table status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load live table status"
        )