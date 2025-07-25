"""
Notification Management API Endpoints
Handles real-time notifications, WebSocket connections, and notification management
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from datetime import datetime

from app.models.schemas import (
    Notification, NotificationCreate, NotificationType, 
    ApiResponse, User
)
from app.services.notification_service import get_notification_service
from app.core.security import get_current_user, get_current_admin_user

router = APIRouter()


@router.websocket("/ws/{connection_type}/{connection_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    connection_type: str, 
    connection_id: str
):
    """WebSocket endpoint for real-time notifications"""
    notification_service = get_notification_service()
    
    try:
        # Validate connection type
        if connection_type not in ["users", "cafes", "admins"]:
            await websocket.close(code=1008, reason="Invalid connection type")
            return
        
        # Accept connection
        await notification_service.connect_websocket(websocket, connection_type, connection_id)
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                
                # Parse and handle message
                import json
                try:
                    message = json.loads(data)
                    await notification_service.handle_websocket_message(websocket, message)
                except json.JSONDecodeError:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }))
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"WebSocket error: {e}")
                break
                
    except Exception as e:
        print(f"WebSocket connection error: {e}")
    finally:
        # Clean up connection
        notification_service.disconnect_websocket(connection_type, connection_id)


@router.post("/", response_model=Notification, status_code=status.HTTP_201_CREATED)
async def create_notification(
    notification_data: NotificationCreate,
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new notification (admin only)"""
    try:
        notification_service = get_notification_service()
        notification = await notification_service.create_notification(notification_data)
        
        return notification
        
    except Exception as e:
        print(f"Error creating notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create notification"
        )


@router.get("/", response_model=List[Notification])
async def get_user_notifications(
    unread_only: bool = Query(False, description="Get only unread notifications"),
    limit: int = Query(50, le=100, description="Maximum number of notifications to return"),
    current_user: User = Depends(get_current_user)
):
    """Get notifications for the current user"""
    try:
        notification_service = get_notification_service()
        notifications = await notification_service.get_user_notifications(
            current_user.id, unread_only, limit
        )
        
        return notifications
        
    except Exception as e:
        print(f"Error getting user notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notifications"
        )


@router.get("/unread-count", response_model=Dict[str, int])
async def get_unread_count(
    current_user: User = Depends(get_current_user)
):
    """Get count of unread notifications for the current user"""
    try:
        notification_service = get_notification_service()
        unread_count = await notification_service.get_unread_count(current_user.id)
        
        return {"unread_count": unread_count}
        
    except Exception as e:
        print(f"Error getting unread count: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get unread count"
        )


@router.put("/{notification_id}/read", response_model=ApiResponse)
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark a notification as read"""
    try:
        notification_service = get_notification_service()
        
        # Get notification to verify ownership
        notifications = await notification_service.get_user_notifications(current_user.id)
        notification = next((n for n in notifications if n.id == notification_id), None)
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        success = await notification_service.mark_notification_read(notification_id)
        
        if success:
            return ApiResponse(
                success=True,
                message="Notification marked as read"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to mark notification as read"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error marking notification as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read"
        )


@router.put("/mark-all-read", response_model=ApiResponse)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user)
):
    """Mark all notifications as read for the current user"""
    try:
        notification_service = get_notification_service()
        success = await notification_service.mark_all_notifications_read(current_user.id)
        
        if success:
            return ApiResponse(
                success=True,
                message="All notifications marked as read"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to mark all notifications as read"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error marking all notifications as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark all notifications as read"
        )


@router.post("/send-system-alert", response_model=ApiResponse)
async def send_system_alert(
    message: str,
    recipient_type: str = "admin",
    priority: str = "normal",
    current_user: User = Depends(get_current_admin_user)
):
    """Send system alert (admin only)"""
    try:
        # Validate inputs
        if recipient_type not in ["admin", "cafe", "user"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid recipient type"
            )
        
        if priority not in ["low", "normal", "high", "urgent"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid priority level"
            )
        
        notification_service = get_notification_service()
        await notification_service.send_system_alert(message, recipient_type, priority)
        
        return ApiResponse(
            success=True,
            message="System alert sent successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error sending system alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send system alert"
        )


@router.get("/types", response_model=List[Dict[str, Any]])
async def get_notification_types():
    """Get available notification types"""
    try:
        notification_types = [
            {
                "id": NotificationType.ORDER_PLACED,
                "name": "Order Placed",
                "description": "New order has been placed",
                "icon": "🛒",
                "color": "#4CAF50"
            },
            {
                "id": NotificationType.ORDER_CONFIRMED,
                "name": "Order Confirmed",
                "description": "Order has been confirmed",
                "icon": "✅",
                "color": "#2196F3"
            },
            {
                "id": NotificationType.ORDER_READY,
                "name": "Order Ready",
                "description": "Order is ready for pickup/delivery",
                "icon": "🍽️",
                "color": "#FF9800"
            },
            {
                "id": NotificationType.ORDER_DELIVERED,
                "name": "Order Delivered",
                "description": "Order has been delivered",
                "icon": "🚚",
                "color": "#4CAF50"
            },
            {
                "id": NotificationType.PAYMENT_RECEIVED,
                "name": "Payment Received",
                "description": "Payment has been received",
                "icon": "💰",
                "color": "#4CAF50"
            },
            {
                "id": NotificationType.SYSTEM_ALERT,
                "name": "System Alert",
                "description": "System notification or alert",
                "icon": "⚠️",
                "color": "#F44336"
            }
        ]
        
        return notification_types
        
    except Exception as e:
        print(f"Error getting notification types: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification types"
        )


@router.get("/connection-stats", response_model=Dict[str, Any])
async def get_connection_stats(
    current_user: User = Depends(get_current_admin_user)
):
    """Get WebSocket connection statistics (admin only)"""
    try:
        notification_service = get_notification_service()
        stats = notification_service.get_connection_stats()
        
        return stats
        
    except Exception as e:
        print(f"Error getting connection stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get connection statistics"
        )


@router.post("/test-notification", response_model=ApiResponse)
async def send_test_notification(
    recipient_id: str,
    recipient_type: str = "user",
    current_user: User = Depends(get_current_admin_user)
):
    """Send a test notification (admin only)"""
    try:
        notification_service = get_notification_service()
        
        test_notification = NotificationCreate(
            recipient_id=recipient_id,
            recipient_type=recipient_type,
            notification_type=NotificationType.SYSTEM_ALERT,
            title="Test Notification",
            message=f"This is a test notification sent at {datetime.utcnow().isoformat()}",
            data={
                "test": True,
                "sent_by": current_user.id,
                "timestamp": datetime.utcnow().isoformat()
            },
            priority="normal"
        )
        
        notification = await notification_service.create_notification(test_notification)
        
        return ApiResponse(
            success=True,
            message="Test notification sent successfully",
            data={"notification_id": notification.id}
        )
        
    except Exception as e:
        print(f"Error sending test notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test notification"
        )


@router.delete("/cleanup", response_model=ApiResponse)
async def cleanup_old_notifications(
    days_old: int = Query(30, ge=1, le=365, description="Delete notifications older than this many days"),
    current_user: User = Depends(get_current_admin_user)
):
    """Clean up old notifications (admin only)"""
    try:
        notification_service = get_notification_service()
        deleted_count = await notification_service.cleanup_old_notifications(days_old)
        
        return ApiResponse(
            success=True,
            message=f"Cleaned up {deleted_count} old notifications",
            data={"deleted_count": deleted_count}
        )
        
    except Exception as e:
        print(f"Error cleaning up notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clean up notifications"
        )


@router.get("/preferences", response_model=Dict[str, Any])
async def get_notification_preferences(
    current_user: User = Depends(get_current_user)
):
    """Get notification preferences for the current user"""
    try:
        # Get user preferences from user profile
        preferences = current_user.preferences
        
        notification_preferences = {
            "email_notifications": preferences.email_notifications if preferences else True,
            "sms_notifications": preferences.sms_notifications if preferences else False,
            "push_notifications": True,  # Always enabled for web
            "notification_types": {
                "order_updates": True,
                "payment_confirmations": True,
                "promotional_offers": preferences.notifications_enabled if preferences else True,
                "system_alerts": True
            }
        }
        
        return notification_preferences
        
    except Exception as e:
        print(f"Error getting notification preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification preferences"
        )


@router.put("/preferences", response_model=ApiResponse)
async def update_notification_preferences(
    preferences: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Update notification preferences for the current user"""
    try:
        # Update user preferences
        from app.database.firestore import get_user_repo, get_cafe_repo
        user_repo = get_enhanced_user_repo()
        
        # Get current user preferences
        current_preferences = current_user.preferences.dict() if current_user.preferences else {}
        
        # Update notification-related preferences
        if "email_notifications" in preferences:
            current_preferences["email_notifications"] = preferences["email_notifications"]
        if "sms_notifications" in preferences:
            current_preferences["sms_notifications"] = preferences["sms_notifications"]
        if "notifications_enabled" in preferences:
            current_preferences["notifications_enabled"] = preferences["notifications_enabled"]
        
        # Save updated preferences
        success = await user_repo.update_preferences(current_user.id, current_preferences)
        
        if success:
            return ApiResponse(
                success=True,
                message="Notification preferences updated successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update notification preferences"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating notification preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification preferences"
        )