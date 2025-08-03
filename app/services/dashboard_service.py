
"""

Dashboard Service

Handles complex dashboard data aggregation and analytics

"""

from typing import Dict, Any, List, Optional

from datetime import datetime, timedelta

from collections import defaultdict



from app.core.logging_config import get_logger

# Import moved to avoid circular dependency

from app.models.schemas import OrderStatus, TableStatus, PaymentStatus



logger = get_logger(__name__)





class DashboardService:

  """Service for dashboard data aggregation and analytics"""

   

  def __init__(self):

    self.repo_manager = None

   

  def _get_repo_manager(self):

    """Lazy initialization of repository manager to avoid circular imports"""

    if self.repo_manager is None:

      from app.core.dependency_injection import get_repository_manager

      self.repo_manager = get_repository_manager()

    return self.repo_manager

   

  async def get_superadmin_dashboard_data(self, current_user: Dict[str, Any]) -> Dict[str, Any]:

    """Get comprehensive dashboard data for super admin"""

    try:

      # Get repositories

      workspace_repo = self._get_repo_manager().get_repository('workspace')

      venue_repo = self._get_repo_manager().get_repository('venue')

      user_repo = self._get_repo_manager().get_repository('user')

      order_repo = self._get_repo_manager().get_repository('order')

       

      # Get all workspaces

      workspaces = await workspace_repo.get_all()

       

      # Get all venues

      venues = await venue_repo.get_all()

      active_venues = [v for v in venues if v.get('is_active', False)]

       

      # Get all users

      users = await user_repo.get_all()

       

      # Get all orders for revenue calculation

      orders = await order_repo.get_all()

      paid_orders = [o for o in orders if o.get('payment_status') == PaymentStatus.PAID.value]

      total_revenue = sum(order.get('total_amount', 0) for order in paid_orders)

       

      # Prepare workspace details

      workspace_details = []

      for workspace in workspaces:

        workspace_id = workspace['id']

         

        # Count venues in this workspace

        workspace_venues = [v for v in venues if v.get('workspace_id') == workspace_id]

         

        # Count users in this workspace

        workspace_users = [u for u in users if u.get('workspace_id') == workspace_id]

         

        workspace_details.append({

          "id": workspace_id,

          "name": workspace.get('name', 'Unknown'),

          "venue_count": len(workspace_venues),

          "user_count": len(workspace_users),

          "is_active": workspace.get('is_active', False),

          "created_at": workspace.get('created_at', datetime.utcnow()).isoformat() if workspace.get('created_at') else datetime.utcnow().isoformat(),

        })

       

      return {

        "summary": {

          "total_workspaces": len(workspaces),

          "total_venues": len(venues),

          "total_users": len(users),

          "total_orders": len(orders),

          "total_revenue": total_revenue,

          "active_venues": len(active_venues),

        },

        "workspaces": workspace_details,

      }

       

    except Exception as e:

      logger.error(f"Error getting superadmin dashboard data: {e}")

      raise

   

  async def get_admin_dashboard_data(self, venue_id: str, current_user: Dict[str, Any]) -> Dict[str, Any]:

    """Get dashboard data for venue admin"""

    try:

      # Get repositories

      order_repo = self._get_repo_manager().get_repository('order')

      table_repo = self._get_repo_manager().get_repository('table')

      menu_item_repo = self._get_repo_manager().get_repository('menu_item')

      user_repo = self._get_repo_manager().get_repository('user')

       

      # Get today's date range

      today = datetime.utcnow().date()

      today_start = datetime.combine(today, datetime.min.time())

      today_end = datetime.combine(today, datetime.max.time())

       

      # Get all orders for this venue

      all_orders = await order_repo.get_by_venue_id(venue_id)

       

      # Filter today's orders

      today_orders = [

        order for order in all_orders

        if order.get('created_at') and today_start <= order['created_at'] <= today_end

      ]

       

      # Calculate today's revenue (only paid orders)

      today_revenue = sum(

        order.get('total_amount', 0) 

        for order in today_orders 

        if order.get('payment_status') == PaymentStatus.PAID.value

      )

       

      # Get tables for this venue

      tables = await table_repo.get_by_venue(venue_id)

      active_tables = [t for t in tables if t.get('is_active', False)]

      occupied_tables = [

        t for t in active_tables 

        if t.get('table_status') == TableStatus.OCCUPIED.value

      ]

       

      # Get menu items for this venue

      menu_items = await menu_item_repo.get_by_venue(venue_id)

      active_menu_items = [m for m in menu_items if m.get('is_available', False)]

       

      # Get staff for this venue

      staff = await user_repo.get_by_venue(venue_id)

       

      # Get recent orders (last 10)

      recent_orders = sorted(

        all_orders,

        key=lambda x: x.get('created_at', datetime.min),

        reverse=True

      )[:10]

       

      # Format recent orders

      formatted_recent_orders = []

      for order in recent_orders:

        # Get table number if available

        table_number = None

        if order.get('table_id'):

          table = await table_repo.get_by_id(order['table_id'])

          if table:

            table_number = table.get('table_number')

         

        formatted_recent_orders.append({

          "id": order['id'],

          "order_number": order.get('order_number', 'N/A'),

          "table_number": table_number,

          "total_amount": order.get('total_amount', 0),

          "status": order.get('status', 'unknown'),

          "created_at": order.get('created_at', datetime.utcnow()).isoformat() if order.get('created_at') else datetime.utcnow().isoformat(),

        })

       

      return {

        "summary": {

          "today_orders": len(today_orders),

          "today_revenue": today_revenue,

          "total_tables": len(active_tables),

          "occupied_tables": len(occupied_tables),

          "total_menu_items": len(menu_items),

          "active_menu_items": len(active_menu_items),

          "total_staff": len(staff),

        },

        "recent_orders": formatted_recent_orders,

      }

       

    except Exception as e:

      logger.error(f"Error getting admin dashboard data: {e}")

      raise

   

  async def get_operator_dashboard_data(self, venue_id: str, current_user: Dict[str, Any]) -> Dict[str, Any]:

    """Get dashboard data for venue operator"""

    try:

      # Get repositories

      order_repo = self._get_repo_manager().get_repository('order')

      table_repo = self._get_repo_manager().get_repository('table')

       

      # Get all orders for this venue

      all_orders = await order_repo.get_by_venue_id(venue_id)

       

      # Filter active orders (not completed/cancelled)

      active_statuses = [

        OrderStatus.PENDING.value,

        OrderStatus.CONFIRMED.value,

        OrderStatus.PREPARING.value,

        OrderStatus.READY.value,

        OrderStatus.OUT_FOR_DELIVERY.value

      ]

       

      active_orders = [

        order for order in all_orders

        if order.get('status') in active_statuses

      ]

       

      # Count orders by status

      pending_orders = len([o for o in active_orders if o.get('status') == OrderStatus.PENDING.value])

      preparing_orders = len([o for o in active_orders if o.get('status') == OrderStatus.PREPARING.value])

      ready_orders = len([o for o in active_orders if o.get('status') == OrderStatus.READY.value])

       

      # Get tables for this venue

      tables = await table_repo.get_by_venue(venue_id)

      active_tables = [t for t in tables if t.get('is_active', False)]

      occupied_tables = [

        t for t in active_tables 

        if t.get('table_status') == TableStatus.OCCUPIED.value

      ]

       

      # Format active orders with details

      formatted_active_orders = []

      for order in active_orders[:10]: # Limit to 10 most recent

        # Get table number if available

        table_number = None

        if order.get('table_id'):

          table = await table_repo.get_by_id(order['table_id'])

          if table:

            table_number = table.get('table_number')

         

        # Calculate estimated ready time if not set

        estimated_ready_time = order.get('estimated_ready_time')

        if not estimated_ready_time and order.get('created_at'):

          # Default 20 minutes from creation

          estimated_ready_time = order['created_at'] + timedelta(minutes=20)

         

        formatted_active_orders.append({

          "id": order['id'],

          "order_number": order.get('order_number', 'N/A'),

          "table_number": table_number,

          "total_amount": order.get('total_amount', 0),

          "status": order.get('status', 'unknown'),

          "created_at": order.get('created_at', datetime.utcnow()).isoformat() if order.get('created_at') else datetime.utcnow().isoformat(),

          "estimated_ready_time": estimated_ready_time.isoformat() if estimated_ready_time else None,

          "items_count": len(order.get('items', [])),

        })

       

      return {

        "summary": {

          "active_orders": len(active_orders),

          "pending_orders": pending_orders,

          "preparing_orders": preparing_orders,

          "ready_orders": ready_orders,

          "occupied_tables": len(occupied_tables),

          "total_tables": len(active_tables),

        },

        "active_orders": formatted_active_orders,

      }

       

    except Exception as e:

      logger.error(f"Error getting operator dashboard data: {e}")

      raise

   

  async def get_live_order_status(self, venue_id: str) -> Dict[str, Any]:

    """Get real-time order status for venue"""

    try:

      order_repo = self._get_repo_manager().get_repository('order')

      table_repo = self._get_repo_manager().get_repository('table')

       

      # Get all orders for this venue

      all_orders = await order_repo.get_by_venue_id(venue_id)

       

      # Filter active orders

      active_statuses = [

        OrderStatus.PENDING.value,

        OrderStatus.CONFIRMED.value,

        OrderStatus.PREPARING.value,

        OrderStatus.READY.value,

        OrderStatus.OUT_FOR_DELIVERY.value

      ]

       

      active_orders = [

        order for order in all_orders

        if order.get('status') in active_statuses

      ]

       

      # Group orders by status

      orders_by_status = defaultdict(list)

       

      for order in active_orders:

        status = order.get('status')

         

        # Get table number if available

        table_number = None

        if order.get('table_id'):

          table = await table_repo.get_by_id(order['table_id'])

          if table:

            table_number = table.get('table_number')

         

        order_data = {

          "id": order['id'],

          "order_number": order.get('order_number', 'N/A'),

          "table_number": table_number,

          "total_amount": order.get('total_amount', 0),

          "status": status,

          "created_at": order.get('created_at', datetime.utcnow()).isoformat() if order.get('created_at') else datetime.utcnow().isoformat(),

        }

         

        orders_by_status[status].append(order_data)

       

      # Calculate summary

      pending_count = len(orders_by_status.get(OrderStatus.PENDING.value, []))

      preparing_count = len(orders_by_status.get(OrderStatus.PREPARING.value, []))

      ready_count = len(orders_by_status.get(OrderStatus.READY.value, []))

       

      return {

        "summary": {

          "total_active_orders": len(active_orders),

          "pending_orders": pending_count,

          "preparing_orders": preparing_count,

          "ready_orders": ready_count,

        },

        "orders_by_status": dict(orders_by_status)

      }

       

    except Exception as e:

      logger.error(f"Error getting live order status: {e}")

      raise

   

  async def get_live_table_status(self, venue_id: str) -> Dict[str, Any]:

    """Get real-time table status for venue"""

    try:

      table_repo = self._get_repo_manager().get_repository('table')

       

      # Get all tables for this venue

      tables = await table_repo.get_by_venue(venue_id)

      active_tables = [t for t in tables if t.get('is_active', False)]

       

      # Count by status

      status_counts = {

        "available": 0,

        "occupied": 0,

        "reserved": 0,

        "maintenance": 0,

      }

       

      formatted_tables = []

      for table in active_tables:

        status = table.get('table_status', TableStatus.AVAILABLE.value)

         

        # Count status

        if status in status_counts:

          status_counts[status] += 1

         

        formatted_tables.append({

          "id": table['id'],

          "table_number": table.get('table_number'),

          "capacity": table.get('capacity', 4),

          "status": status,

        })

       

      return {

        "tables": formatted_tables,

        "summary": {

          "total_tables": len(active_tables),

          "available": status_counts["available"],

          "occupied": status_counts["occupied"],

          "reserved": status_counts["reserved"],

          "maintenance": status_counts["maintenance"],

        }

      }

       

    except Exception as e:

      logger.error(f"Error getting live table status: {e}")

      raise





# Global dashboard service instance

dashboard_service = DashboardService()