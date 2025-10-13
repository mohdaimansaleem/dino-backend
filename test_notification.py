#!/usr/bin/env python3
"""
Test script to send a WebSocket notification
Run this to test if notifications are working
"""
import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

async def test_notification():
    """Test sending a WebSocket notification"""
    try:
        from app.core.websocket_manager import connection_manager
        from datetime import datetime
        
        # Sample order data
        test_order = {
            "id": "test-order-123",
            "order_number": "TEST-001",
            "venue_id": "test-venue-id",  # Replace with actual venue ID
            "total_amount": 25.50,
            "table_id": "test-table-1",
            "table_number": "T1",
            "status": "pending",
            "payment_status": "pending",
            "customer_name": "Test Customer",
            "items": [
                {"name": "Test Item", "quantity": 2, "price": 12.75}
            ],
            "created_at": datetime.utcnow().isoformat()
        }
        
        print(f"Sending test notification for venue: {test_order['venue_id']}")
        print(f"Order number: {test_order['order_number']}")
        
        # Send notification
        await connection_manager.send_order_notification(test_order, "order_created")
        
        print("✅ Test notification sent successfully!")
        
        # Also test system notification
        await connection_manager.send_system_notification(
            test_order['venue_id'],
            "test_notification",
            "Test Notification",
            "This is a test notification to verify WebSocket functionality",
            {"test": True}
        )
        
        print("✅ Test system notification sent successfully!")
        
    except Exception as e:
        print(f"❌ Error sending test notification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Testing WebSocket notifications...")
    asyncio.run(test_notification())