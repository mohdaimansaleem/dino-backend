"""
Enhanced Order Management API Endpoints
Comprehensive order handling with real-time notifications and transaction integration
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import datetime, timedelta
import uuid

from app.models.schemas import (
    Order, OrderCreate, OrderUpdate, OrderStatus, PaymentStatus,
    ApiResponse, User, OrderType, PaymentMethod, DashboardStats,
    Transaction, PaymentGateway
)
from app.database.firestore import (
    get_order_repo, get_cafe_repo, get_menu_item_repo, get_table_repo
)
# Services will be implemented later
# from app.services.notification_service import get_notification_service
# from app.services.transaction_service import get_transaction_service
from app.core.security import get_current_user, get_current_admin_user, verify_cafe_access

router = APIRouter()


def generate_order_number() -> str:
    """Generate a human-readable order number"""
    timestamp = datetime.utcnow().strftime("%y%m%d")
    random_part = str(uuid.uuid4().int)[:4]
    return f"ORD{timestamp}{random_part}"


async def calculate_order_totals(items: List[Dict[str, Any]], cafe_id: str) -> Dict[str, float]:
    """Calculate order totals including tax and delivery fees"""
    menu_repo = get_menu_repo()
    cafe_repo = get_cafe_repo()
    
    subtotal = 0.0
    
    # Calculate subtotal
    for item in items:
        menu_item = await menu_repo.get_by_id(item["menu_item_id"])
        if menu_item and menu_item.get("is_available", True):
            item_price = menu_item["base_price"]
            
            # Add variant price if applicable
            if item.get("variant_id"):
                variants = menu_item.get("variants", [])
                for variant in variants:
                    if variant.get("id") == item["variant_id"]:
                        item_price += variant.get("price_modifier", 0)
                        break
            
            subtotal += item_price * item["quantity"]
    
    # Get cafe settings for fees
    cafe = await cafe_repo.get_by_id(cafe_id)
    cafe_settings = cafe.get("settings", {}) if cafe else {}
    
    # Calculate tax (assuming 5% GST)
    tax_rate = 0.05
    tax_amount = subtotal * tax_rate
    
    # Calculate delivery fee if applicable
    delivery_fee = cafe_settings.get("delivery_fee", 0.0)
    
    # Total amount
    total_amount = subtotal + tax_amount + delivery_fee
    
    return {
        "subtotal": round(subtotal, 2),
        "tax_amount": round(tax_amount, 2),
        "delivery_fee": round(delivery_fee, 2),
        "total_amount": round(total_amount, 2)
    }


async def estimate_preparation_time(items: List[Dict[str, Any]]) -> int:
    """Estimate total preparation time for order"""
    menu_repo = get_menu_repo()
    max_time = 0
    
    for item in items:
        menu_item = await menu_repo.get_by_id(item["menu_item_id"])
        if menu_item:
            item_time = menu_item.get("preparation_time_minutes", 15)
            max_time = max(max_time, item_time)
    
    # Add base processing time
    return max_time + 10


@router.post("/", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_order(order_data: OrderCreate):
    """Create a new order"""
    try:
        order_repo = get_order_repo()
        menu_repo = get_menu_repo()
        cafe_repo = get_cafe_repo()
        # TODO: Add notification service
        # notification_service = get_notification_service()
        
        # Validate cafe exists and is active
        cafe = await cafe_repo.get_by_id(order_data.cafe_id)
        if not cafe or not cafe.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cafe is not available"
            )
        
        # Validate menu items and build order items
        order_items = []
        for item_data in order_data.items:
            menu_item = await menu_repo.get_by_id(item_data.menu_item_id)
            if not menu_item:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Menu item not found"
                )
            
            if not menu_item.get("is_available", True):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Menu item '{menu_item['name']}' is not available"
                )
            
            if menu_item["cafe_id"] != order_data.cafe_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Menu item does not belong to this cafe"
                )
            
            # Calculate item price with variant
            item_price = menu_item["base_price"]
            variant_name = None
            
            if item_data.variant_id:
                variants = menu_item.get("variants", [])
                for variant in variants:
                    if variant.get("id") == item_data.variant_id:
                        item_price += variant.get("price_modifier", 0)
                        variant_name = variant.get("name")
                        break
            
            order_items.append({
                "menu_item_id": item_data.menu_item_id,
                "menu_item_name": menu_item["name"],
                "variant_id": item_data.variant_id,
                "variant_name": variant_name,
                "quantity": item_data.quantity,
                "unit_price": item_price,
                "total_price": item_price * item_data.quantity,
                "special_instructions": item_data.special_instructions
            })
        
        # Calculate totals
        totals = await calculate_order_totals(order_data.items, order_data.cafe_id)
        
        # Estimate preparation time
        estimated_time = await estimate_preparation_time(order_data.items)
        estimated_ready_time = datetime.utcnow() + timedelta(minutes=estimated_time)
        
        # Create order data
        order_dict = order_data.dict()
        order_dict.update({
            "order_number": generate_order_number(),
            "items": order_items,
            "subtotal": totals["subtotal"],
            "tax_amount": totals["tax_amount"],
            "delivery_fee": totals["delivery_fee"],
            "discount_amount": 0.0,
            "total_amount": totals["total_amount"],
            "status": OrderStatus.PENDING,
            "payment_status": PaymentStatus.PENDING,
            "estimated_ready_time": estimated_ready_time
        })
        
        # Create order
        order_id = await order_repo.create(order_dict)
        
        # Get created order
        created_order = await order_repo.get_by_id(order_id)
        order = Order(**created_order)
        
        # TODO: Send notification
        # await notification_service.notify_order_placed(order)
        
        # TODO: Update menu item order counts
        # for item in order_data.items:
        #     await menu_repo.increment_order_count(item.menu_item_id, item.quantity)
        
        # TODO: Update cafe order count
        # await cafe_repo.increment_order_count(order_data.cafe_id)
        
        return ApiResponse(
            success=True,
            message="Order created successfully",
            data=created_order
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order"
        )


@router.get("/{order_id}", response_model=Order)
async def get_order(order_id: str):
    """Get order by ID"""
    try:
        order_repo = get_order_repo()
        order_data = await order_repo.get_by_id(order_id)
        
        if not order_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        return Order(**order_data)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get order"
        )


@router.get("/cafe/{cafe_id}", response_model=List[Order])
async def get_cafe_orders(
    cafe_id: str,
    status_filter: Optional[OrderStatus] = None,
    order_type: Optional[OrderType] = None,
    limit: Optional[int] = 50,
    current_user: User = Depends(get_current_admin_user)
):
    """Get orders for a cafe (admin only)"""
    try:
        # Verify cafe access
        await verify_cafe_access(cafe_id, current_user.dict())
        
        order_repo = get_order_repo()
        
        if status_filter:
            orders_data = await order_repo.get_by_status(cafe_id, status_filter)
        else:
            orders_data = await order_repo.get_by_cafe(cafe_id, limit=limit)
        
        # Filter by order type if specified
        if order_type:
            orders_data = [order for order in orders_data if order.get("order_type") == order_type]
        
        return [Order(**order) for order in orders_data]
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting cafe orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cafe orders"
        )


@router.get("/cafe/{cafe_id}/active", response_model=List[Order])
async def get_active_cafe_orders(
    cafe_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Get active orders for a cafe"""
    try:
        # Verify cafe access
        await verify_cafe_access(cafe_id, current_user.dict())
        
        order_repo = get_order_repo()
        orders_data = await order_repo.get_active_orders(cafe_id)
        
        return [Order(**order) for order in orders_data]
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting active orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get active orders"
        )


@router.get("/user/my-orders", response_model=List[Order])
async def get_user_orders(
    limit: Optional[int] = 20,
    current_user: User = Depends(get_current_user)
):
    """Get orders for the current user"""
    try:
        order_repo = get_order_repo()
        orders_data = await order_repo.get_by_customer(current_user.id, limit)
        
        return [Order(**order) for order in orders_data]
        
    except Exception as e:
        print(f"Error getting user orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user orders"
        )


@router.put("/{order_id}/status", response_model=ApiResponse)
async def update_order_status(
    order_id: str,
    new_status: OrderStatus,
    estimated_time: Optional[int] = None,
    current_user: User = Depends(get_current_admin_user)
):
    """Update order status"""
    try:
        order_repo = get_order_repo()
        # TODO: Add notification service
        # notification_service = get_notification_service()
        
        # Get order
        order_data = await order_repo.get_by_id(order_id)
        if not order_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Verify cafe access
        await verify_cafe_access(order_data["cafe_id"], current_user.dict())
        
        old_status = OrderStatus(order_data["status"])
        
        # Update order status
        update_data = {"status": new_status}
        
        if estimated_time:
            estimated_ready_time = datetime.utcnow() + timedelta(minutes=estimated_time)
            update_data["estimated_ready_time"] = estimated_ready_time
        
        await order_repo.update(order_id, update_data)
        
        # Get updated order
        updated_order_data = await order_repo.get_by_id(order_id)
        updated_order = Order(**updated_order_data)
        
        # TODO: Send notification
        # await notification_service.notify_order_status_change(updated_order, old_status)
        
        return ApiResponse(
            success=True,
            message=f"Order status updated to {new_status.value}",
            data=updated_order_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating order status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update order status"
        )


@router.post("/{order_id}/payment", response_model=ApiResponse)
async def process_order_payment(
    order_id: str,
    payment_method: PaymentMethod,
    payment_gateway: PaymentGateway = PaymentGateway.RAZORPAY,
    payment_details: Optional[Dict[str, Any]] = None
):
    """Process payment for an order"""
    try:
        order_repo = get_order_repo()
        # TODO: Add transaction service
        # transaction_service = get_transaction_service()
        
        # Get order
        order_data = await order_repo.get_by_id(order_id)
        if not order_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        order = Order(**order_data)
        
        # Check if order can be paid
        if order.payment_status != PaymentStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order payment is not pending"
            )
        
        # TODO: Process payment
        # payment_result = await transaction_service.process_payment(
        #     order, payment_method, payment_gateway, payment_details or {}
        # )
        
        # For now, just update payment status to processing
        await order_repo.update(order_id, {
            "payment_status": PaymentStatus.PROCESSING
        })
        
        return ApiResponse(
            success=True,
            message="Payment initiated successfully (mock implementation)",
            data={"order_id": order_id, "status": "processing"}
        )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing payment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process payment"
        )


@router.get("/cafe/{cafe_id}/analytics", response_model=Dict[str, Any])
async def get_order_analytics(
    cafe_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_admin_user)
):
    """Get order analytics for a cafe"""
    try:
        # Verify cafe access
        await verify_cafe_access(cafe_id, current_user.dict())
        
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        order_repo = get_order_repo()
        # TODO: Implement analytics method
        # analytics = await order_repo.get_order_analytics(cafe_id, start_date, end_date)
        
        # Mock analytics data for now
        analytics = {
            "total_revenue": 0.0,
            "total_orders": 0,
            "average_order_value": 0.0,
            "popular_items": [],
            "revenue_by_day": [],
            "orders_by_status": []
        }
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting order analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get order analytics"
        )


@router.get("/cafe/{cafe_id}/dashboard", response_model=DashboardStats)
async def get_cafe_dashboard(
    cafe_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Get dashboard statistics for a cafe"""
    try:
        # Verify cafe access
        await verify_cafe_access(cafe_id, current_user.dict())
        
        order_repo = get_order_repo()
        menu_repo = get_menu_repo()
        
        # Get today's date range
        today = datetime.utcnow().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        
        # TODO: Implement date range queries
        # today_orders = await order_repo.get_orders_by_date_range(
        #     cafe_id, start_of_day, end_of_day
        # )
        today_orders = []
        
        # TODO: Implement active orders query
        # active_orders = await order_repo.get_active_orders(cafe_id)
        active_orders = []
        
        # TODO: Implement popular items query
        # popular_items = await menu_repo.get_popular_items(cafe_id, limit=5)
        popular_items = []
        
        # Calculate stats
        total_orders_today = len(today_orders)
        total_revenue_today = sum(
            order.get("total_amount", 0) for order in today_orders 
            if order.get("status") != OrderStatus.CANCELLED
        )
        pending_orders = len([
            order for order in active_orders 
            if order.get("status") == OrderStatus.PENDING
        ])
        
        # Get recent orders (last 10)
        recent_orders_data = await order_repo.get_by_cafe(cafe_id, limit=10)
        recent_orders = [Order(**order) for order in recent_orders_data]
        
        # Calculate average order value
        if total_orders_today > 0:
            average_order_value = total_revenue_today / total_orders_today
        else:
            average_order_value = 0.0
        
        return DashboardStats(
            total_orders_today=total_orders_today,
            total_revenue_today=total_revenue_today,
            pending_orders=pending_orders,
            active_customers=len(set(order.get("customer_id") for order in today_orders if order.get("customer_id"))),
            average_order_value=average_order_value,
            popular_items=[{
                "id": item["id"],
                "name": item["name"],
                "orders": item.get("total_orders", 0)
            } for item in popular_items],
            recent_orders=recent_orders
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting dashboard stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dashboard statistics"
        )