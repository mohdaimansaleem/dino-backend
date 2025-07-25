"""
Analytics API Endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict

from app.models.schemas import SalesAnalytics, PopularItem, RevenueData, StatusData, ApiResponse
from app.database.firestore import order_repo, menu_item_repo
from app.core.security import get_current_admin_user, verify_cafe_access


router = APIRouter()


async def calculate_sales_analytics(cafe_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Calculate comprehensive sales analytics for a cafe"""
    # Get orders in date range
    orders = await order_repo.query([
        ("cafe_id", "==", cafe_id),
        ("created_at", ">=", start_date),
        ("created_at", "<=", end_date)
    ])
    
    # Filter completed orders (served)
    completed_orders = [order for order in orders if order.get("status") == "served"]
    
    # Calculate basic metrics
    total_orders = len(completed_orders)
    total_revenue = sum(order.get("total_amount", 0) for order in completed_orders)
    average_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Calculate popular items
    item_stats = defaultdict(lambda: {"count": 0, "revenue": 0, "name": ""})
    
    for order in completed_orders:
        for item in order.get("items", []):
            item_id = item.get("menu_item_id")
            quantity = item.get("quantity", 0)
            price = item.get("price", 0)
            name = item.get("menu_item_name", "")
            
            item_stats[item_id]["count"] += quantity
            item_stats[item_id]["revenue"] += price * quantity
            item_stats[item_id]["name"] = name
    
    # Sort popular items by order count
    popular_items = []
    for item_id, stats in sorted(item_stats.items(), key=lambda x: x[1]["count"], reverse=True)[:10]:
        popular_items.append(PopularItem(
            menu_item_id=item_id,
            menu_item_name=stats["name"],
            order_count=stats["count"],
            revenue=stats["revenue"]
        ))
    
    # Calculate revenue by day
    daily_revenue = defaultdict(lambda: {"revenue": 0, "orders": 0})
    
    for order in completed_orders:
        order_date = order.get("created_at")
        if isinstance(order_date, datetime):
            date_str = order_date.strftime("%Y-%m-%d")
            daily_revenue[date_str]["revenue"] += order.get("total_amount", 0)
            daily_revenue[date_str]["orders"] += 1
    
    revenue_by_day = []
    for date_str, data in sorted(daily_revenue.items()):
        revenue_by_day.append(RevenueData(
            date=date_str,
            revenue=data["revenue"],
            orders=data["orders"]
        ))
    
    # Calculate orders by status
    status_counts = defaultdict(int)
    for order in orders:
        status = order.get("status", "unknown")
        status_counts[status] += 1
    
    orders_by_status = []
    for status, count in status_counts.items():
        orders_by_status.append(StatusData(
            status=status,
            count=count
        ))
    
    return {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "average_order_value": average_order_value,
        "popular_items": popular_items,
        "revenue_by_day": revenue_by_day,
        "orders_by_status": orders_by_status
    }


@router.get("/{cafe_id}", response_model=SalesAnalytics)
async def get_cafe_analytics(
    cafe_id: str,
    days: int = 30,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Get comprehensive analytics for a cafe"""
    try:
        # Verify cafe ownership
        await verify_cafe_access(cafe_id, current_user)
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Calculate analytics
        analytics_data = await calculate_sales_analytics(cafe_id, start_date, end_date)
        
        return SalesAnalytics(**analytics_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}"
        )


@router.get("/{cafe_id}/revenue", response_model=List[RevenueData])
async def get_revenue_analytics(
    cafe_id: str,
    days: int = 30,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Get revenue analytics for a cafe"""
    try:
        # Verify cafe ownership
        await verify_cafe_access(cafe_id, current_user)
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get analytics
        analytics_data = await calculate_sales_analytics(cafe_id, start_date, end_date)
        
        return analytics_data["revenue_by_day"]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get revenue analytics: {str(e)}"
        )


@router.get("/{cafe_id}/popular-items", response_model=List[PopularItem])
async def get_popular_items(
    cafe_id: str,
    days: int = 30,
    limit: int = 10,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Get popular items analytics for a cafe"""
    try:
        # Verify cafe ownership
        await verify_cafe_access(cafe_id, current_user)
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get analytics
        analytics_data = await calculate_sales_analytics(cafe_id, start_date, end_date)
        
        return analytics_data["popular_items"][:limit]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get popular items: {str(e)}"
        )


@router.get("/{cafe_id}/order-status", response_model=List[StatusData])
async def get_order_status_analytics(
    cafe_id: str,
    days: int = 30,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Get order status distribution analytics"""
    try:
        # Verify cafe ownership
        await verify_cafe_access(cafe_id, current_user)
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get analytics
        analytics_data = await calculate_sales_analytics(cafe_id, start_date, end_date)
        
        return analytics_data["orders_by_status"]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get order status analytics: {str(e)}"
        )


@router.get("/{cafe_id}/summary", response_model=ApiResponse)
async def get_analytics_summary(
    cafe_id: str,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Get analytics summary with key metrics"""
    try:
        # Verify cafe ownership
        await verify_cafe_access(cafe_id, current_user)
        
        # Get today's analytics
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        
        today_analytics = await calculate_sales_analytics(cafe_id, today, tomorrow)
        
        # Get this week's analytics
        week_start = today - timedelta(days=today.weekday())
        week_analytics = await calculate_sales_analytics(cafe_id, week_start, tomorrow)
        
        # Get this month's analytics
        month_start = today.replace(day=1)
        month_analytics = await calculate_sales_analytics(cafe_id, month_start, tomorrow)
        
        # Get active orders count
        active_orders = await order_repo.query([
            ("cafe_id", "==", cafe_id),
            ("status", "in", ["pending", "confirmed", "preparing", "ready"])
        ])
        
        summary = {
            "today": {
                "revenue": today_analytics["total_revenue"],
                "orders": today_analytics["total_orders"]
            },
            "this_week": {
                "revenue": week_analytics["total_revenue"],
                "orders": week_analytics["total_orders"]
            },
            "this_month": {
                "revenue": month_analytics["total_revenue"],
                "orders": month_analytics["total_orders"]
            },
            "active_orders": len(active_orders),
            "average_order_value": month_analytics["average_order_value"]
        }
        
        return ApiResponse(
            success=True,
            message="Analytics summary retrieved successfully",
            data=summary
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics summary: {str(e)}"
        )