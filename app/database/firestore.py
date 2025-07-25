"""
Firestore Database Connection and Repository Classes
Production-ready implementation for Google Cloud Run
"""
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from app.core.config import get_firestore_client
from app.core.logging_config import LoggerMixin

logger = logging.getLogger(__name__)


class FirestoreRepository(LoggerMixin):
    """Base repository class for Firestore operations"""
    
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self.db = None
        self.collection = None
        self._initialize_collection()
    
    def _initialize_collection(self):
        """Initialize collection reference"""
        try:
            self.db = get_firestore_client()
            self.collection = self.db.collection(self.collection_name)
            self.logger.info(f"Initialized Firestore collection: {self.collection_name}")
        except Exception as e:
            self.log_error(e, "initialize_collection", collection=self.collection_name)
            raise
    
    def _ensure_collection(self):
        """Ensure collection is available"""
        if not self.collection:
            self._initialize_collection()
        
        if not self.collection:
            raise RuntimeError(f"Firestore collection '{self.collection_name}' not available")
    
    async def create(self, data: Dict[str, Any], doc_id: Optional[str] = None) -> str:
        """Create a new document"""
        self._ensure_collection()
        
        try:
            # Add timestamps
            data['created_at'] = datetime.utcnow()
            data['updated_at'] = datetime.utcnow()
            
            if doc_id:
                doc_ref = self.collection.document(doc_id)
                doc_ref.set(data)
                self.log_operation("create_document", 
                                 collection=self.collection_name, 
                                 doc_id=doc_id)
                return doc_id
            else:
                doc_ref = self.collection.add(data)[1]
                self.log_operation("create_document", 
                                 collection=self.collection_name, 
                                 doc_id=doc_ref.id)
                return doc_ref.id
        except Exception as e:
            self.log_error(e, "create_document", 
                          collection=self.collection_name, 
                          doc_id=doc_id)
            raise
    
    async def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        self._ensure_collection()
        
        try:
            doc = self.collection.document(doc_id).get()
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                self.log_operation("get_document", 
                                 collection=self.collection_name, 
                                 doc_id=doc_id, 
                                 found=True)
                return data
            
            self.log_operation("get_document", 
                             collection=self.collection_name, 
                             doc_id=doc_id, 
                             found=False)
            return None
        except Exception as e:
            self.log_error(e, "get_document", 
                          collection=self.collection_name, 
                          doc_id=doc_id)
            raise
    
    async def update(self, doc_id: str, data: Dict[str, Any]) -> bool:
        """Update document by ID"""
        self._ensure_collection()
        
        try:
            # Add update timestamp
            data['updated_at'] = datetime.utcnow()
            
            doc_ref = self.collection.document(doc_id)
            doc_ref.update(data)
            self.log_operation("update_document", 
                             collection=self.collection_name, 
                             doc_id=doc_id)
            return True
        except Exception as e:
            self.log_error(e, "update_document", 
                          collection=self.collection_name, 
                          doc_id=doc_id)
            raise
    
    async def delete(self, doc_id: str) -> bool:
        """Delete document by ID"""
        self._ensure_collection()
        
        try:
            self.collection.document(doc_id).delete()
            self.log_operation("delete_document", 
                             collection=self.collection_name, 
                             doc_id=doc_id)
            return True
        except Exception as e:
            self.log_error(e, "delete_document", 
                          collection=self.collection_name, 
                          doc_id=doc_id)
            raise
    
    async def get_all(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all documents in collection"""
        self._ensure_collection()
        
        try:
            query = self.collection
            if limit:
                query = query.limit(limit)
            
            docs = query.stream()
            results = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                results.append(data)
            
            self.log_operation("get_all_documents", 
                             collection=self.collection_name, 
                             count=len(results), 
                             limit=limit)
            return results
        except Exception as e:
            self.log_error(e, "get_all_documents", 
                          collection=self.collection_name, 
                          limit=limit)
            raise
    
    async def query(self, filters: List[tuple], order_by: Optional[str] = None, 
                   limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Query documents with filters"""
        self._ensure_collection()
        
        try:
            query = self.collection
            
            # Apply filters
            for field, operator, value in filters:
                query = query.where(filter=FieldFilter(field, operator, value))
            
            # Apply ordering
            if order_by:
                query = query.order_by(order_by)
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            docs = query.stream()
            results = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                results.append(data)
            
            self.log_operation("query_documents", 
                             collection=self.collection_name, 
                             filters=len(filters), 
                             count=len(results), 
                             order_by=order_by, 
                             limit=limit)
            return results
        except Exception as e:
            self.log_error(e, "query_documents", 
                          collection=self.collection_name, 
                          filters=filters, 
                          order_by=order_by, 
                          limit=limit)
            raise
    
    async def exists(self, doc_id: str) -> bool:
        """Check if document exists"""
        self._ensure_collection()
        
        try:
            doc = self.collection.document(doc_id).get()
            exists = doc.exists
            self.log_operation("check_document_exists", 
                             collection=self.collection_name, 
                             doc_id=doc_id, 
                             exists=exists)
            return exists
        except Exception as e:
            self.log_error(e, "check_document_exists", 
                          collection=self.collection_name, 
                          doc_id=doc_id)
            raise


# Repository classes for each collection
class UserRepository(FirestoreRepository):
    def __init__(self):
        super().__init__("users")
    
    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        results = await self.query([("email", "==", email)])
        return results[0] if results else None
    
    async def get_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Get user by phone number"""
        results = await self.query([("phone", "==", phone)])
        return results[0] if results else None


class CafeRepository(FirestoreRepository):
    def __init__(self):
        super().__init__("cafes")
    
    async def get_by_owner(self, owner_id: str) -> List[Dict[str, Any]]:
        """Get cafes by owner ID"""
        return await self.query([("owner_id", "==", owner_id)])
    
    async def get_active_cafes(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all active cafes"""
        return await self.query([("is_active", "==", True)], limit=limit)


class MenuItemRepository(FirestoreRepository):
    def __init__(self):
        super().__init__("menu_items")
    
    async def get_by_cafe(self, cafe_id: str) -> List[Dict[str, Any]]:
        """Get menu items by cafe ID"""
        return await self.query([("cafe_id", "==", cafe_id)], order_by="order")
    
    async def get_by_category(self, cafe_id: str, category: str) -> List[Dict[str, Any]]:
        """Get menu items by cafe and category"""
        return await self.query([
            ("cafe_id", "==", cafe_id),
            ("category", "==", category)
        ], order_by="order")


class MenuCategoryRepository(FirestoreRepository):
    def __init__(self):
        super().__init__("menu_categories")
    
    async def get_by_cafe(self, cafe_id: str) -> List[Dict[str, Any]]:
        """Get menu categories by cafe ID"""
        return await self.query([("cafe_id", "==", cafe_id)], order_by="order")


class TableRepository(FirestoreRepository):
    def __init__(self):
        super().__init__("tables")
    
    async def get_by_cafe(self, cafe_id: str) -> List[Dict[str, Any]]:
        """Get tables by cafe ID"""
        return await self.query([("cafe_id", "==", cafe_id)], order_by="table_number")
    
    async def get_by_table_number(self, cafe_id: str, table_number: int) -> Optional[Dict[str, Any]]:
        """Get table by cafe and table number"""
        results = await self.query([
            ("cafe_id", "==", cafe_id),
            ("table_number", "==", table_number)
        ])
        return results[0] if results else None


class OrderRepository(FirestoreRepository):
    def __init__(self):
        super().__init__("orders")
    
    async def get_by_cafe(self, cafe_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get orders by cafe ID"""
        return await self.query([("cafe_id", "==", cafe_id)], order_by="created_at", limit=limit)
    
    async def get_by_status(self, cafe_id: str, status: str) -> List[Dict[str, Any]]:
        """Get orders by cafe and status"""
        return await self.query([
            ("cafe_id", "==", cafe_id),
            ("status", "==", status)
        ], order_by="created_at")


class AnalyticsRepository(FirestoreRepository):
    def __init__(self):
        super().__init__("analytics")
    
    async def get_by_cafe_and_date_range(self, cafe_id: str, start_date: datetime, 
                                       end_date: datetime) -> List[Dict[str, Any]]:
        """Get analytics by cafe and date range"""
        return await self.query([
            ("cafe_id", "==", cafe_id),
            ("date", ">=", start_date),
            ("date", "<=", end_date)
        ], order_by="date")


# Repository instances
user_repo = UserRepository()
cafe_repo = CafeRepository()
menu_item_repo = MenuItemRepository()
menu_category_repo = MenuCategoryRepository()
table_repo = TableRepository()
order_repo = OrderRepository()
analytics_repo = AnalyticsRepository()


def get_user_repo() -> UserRepository:
    """Get user repository instance"""
    return user_repo


def get_cafe_repo() -> CafeRepository:
    """Get cafe repository instance"""
    return cafe_repo


def get_menu_item_repo() -> MenuItemRepository:
    """Get menu item repository instance"""
    return menu_item_repo


def get_menu_category_repo() -> MenuCategoryRepository:
    """Get menu category repository instance"""
    return menu_category_repo


def get_table_repo() -> TableRepository:
    """Get table repository instance"""
    return table_repo


def get_order_repo() -> OrderRepository:
    """Get order repository instance"""
    return order_repo


def get_analytics_repo() -> AnalyticsRepository:
    """Get analytics repository instance"""
    return analytics_repo