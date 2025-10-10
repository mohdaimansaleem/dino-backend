"""
Firestore ID Generator Utility
Provides centralized ID generation using Firestore's native format
"""
from typing import Optional
from google.cloud import firestore
from app.core.config import get_firestore_client
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class FirestoreIDGenerator:
    """
    Centralized ID generator using Firestore's native document ID format.
    Generates IDs in the format: SOWLTGf5VydgACM4pJUq (20 characters, alphanumeric)
    """
    
    def __init__(self):
        self._db = None
    
    def _get_db(self):
        """Get Firestore client instance"""
        if not self._db:
            self._db = get_firestore_client()
        return self._db
    
    def generate_id(self, collection_name: Optional[str] = None) -> str:
        """
        Generate a Firestore-style document ID.
        
        Args:
            collection_name: Optional collection name for context (not used in generation)
            
        Returns:
            str: Firestore-style ID (e.g., 'SOWLTGf5VydgACM4pJUq')
        """
        try:
            db = self._get_db()
            # Use a temporary collection to generate ID, then return just the ID
            temp_collection = db.collection('_temp_id_generation')
            doc_ref = temp_collection.document()
            generated_id = doc_ref.id
            
            logger.debug(f"Generated Firestore ID: {generated_id}" + 
                        (f" for collection: {collection_name}" if collection_name else ""))
            
            return generated_id
            
        except Exception as e:
            logger.error(f"Failed to generate Firestore ID: {e}")
            # Fallback to a simple alphanumeric ID if Firestore is unavailable
            import secrets
            import string
            fallback_id = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(20))
            logger.warning(f"Using fallback ID generation: {fallback_id}")
            return fallback_id
    
    def generate_workspace_id(self) -> str:
        """Generate ID for workspace"""
        return self.generate_id('workspaces')
    
    def generate_venue_id(self) -> str:
        """Generate ID for venue"""
        return self.generate_id('venues')
    
    def generate_user_id(self) -> str:
        """Generate ID for user"""
        return self.generate_id('users')
    
    def generate_role_id(self) -> str:
        """Generate ID for role"""
        return self.generate_id('roles')
    
    def generate_permission_id(self) -> str:
        """Generate ID for permission"""
        return self.generate_id('permissions')
    
    def generate_menu_category_id(self) -> str:
        """Generate ID for menu category"""
        return self.generate_id('menu_categories')
    
    def generate_menu_item_id(self) -> str:
        """Generate ID for menu item"""
        return self.generate_id('menu_items')
    
    def generate_table_id(self) -> str:
        """Generate ID for table"""
        return self.generate_id('tables')
    
    def generate_table_area_id(self) -> str:
        """Generate ID for table area"""
        return self.generate_id('table_areas')
    
    def generate_order_id(self) -> str:
        """Generate ID for order"""
        return self.generate_id('orders')
    
    def generate_customer_id(self) -> str:
        """Generate ID for customer"""
        return self.generate_id('customers')
    
    def generate_transaction_id(self) -> str:
        """Generate ID for transaction"""
        return self.generate_id('transactions')
    
    def generate_notification_id(self) -> str:
        """Generate ID for notification"""
        return self.generate_id('notifications')
    
    def generate_review_id(self) -> str:
        """Generate ID for review"""
        return self.generate_id('reviews')
    
    def validate_firestore_id(self, doc_id: str) -> bool:
        """
        Validate if an ID follows Firestore's format.
        
        Args:
            doc_id: Document ID to validate
            
        Returns:
            bool: True if valid Firestore ID format
        """
        if not doc_id or not isinstance(doc_id, str):
            return False
        
        # Firestore auto-generated IDs are 20 characters long
        # and contain only alphanumeric characters
        if len(doc_id) != 20:
            return False
        
        # Check if all characters are alphanumeric
        return doc_id.isalnum()
    
    def is_uuid_format(self, doc_id: str) -> bool:
        """
        Check if an ID is in UUID format (old format).
        
        Args:
            doc_id: Document ID to check
            
        Returns:
            bool: True if UUID format
        """
        if not doc_id or not isinstance(doc_id, str):
            return False
        
        # UUID format: 8-4-4-4-12 characters separated by hyphens
        import re
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return bool(re.match(uuid_pattern, doc_id, re.IGNORECASE))


# Global instance
_id_generator = FirestoreIDGenerator()


def generate_firestore_id(collection_name: Optional[str] = None) -> str:
    """
    Generate a Firestore-style document ID.
    
    Args:
        collection_name: Optional collection name for context
        
    Returns:
        str: Firestore-style ID
    """
    return _id_generator.generate_id(collection_name)


def generate_workspace_id() -> str:
    """Generate ID for workspace"""
    return _id_generator.generate_workspace_id()


def generate_venue_id() -> str:
    """Generate ID for venue"""
    return _id_generator.generate_venue_id()


def generate_user_id() -> str:
    """Generate ID for user"""
    return _id_generator.generate_user_id()


def generate_role_id() -> str:
    """Generate ID for role"""
    return _id_generator.generate_role_id()


def generate_permission_id() -> str:
    """Generate ID for permission"""
    return _id_generator.generate_permission_id()


def generate_menu_category_id() -> str:
    """Generate ID for menu category"""
    return _id_generator.generate_menu_category_id()


def generate_menu_item_id() -> str:
    """Generate ID for menu item"""
    return _id_generator.generate_menu_item_id()


def generate_table_id() -> str:
    """Generate ID for table"""
    return _id_generator.generate_table_id()


def generate_table_area_id() -> str:
    """Generate ID for table area"""
    return _id_generator.generate_table_area_id()


def generate_order_id() -> str:
    """Generate ID for order"""
    return _id_generator.generate_order_id()


def generate_customer_id() -> str:
    """Generate ID for customer"""
    return _id_generator.generate_customer_id()


def generate_transaction_id() -> str:
    """Generate ID for transaction"""
    return _id_generator.generate_transaction_id()


def generate_notification_id() -> str:
    """Generate ID for notification"""
    return _id_generator.generate_notification_id()


def generate_review_id() -> str:
    """Generate ID for review"""
    return _id_generator.generate_review_id()


def validate_firestore_id(doc_id: str) -> bool:
    """Validate if an ID follows Firestore's format"""
    return _id_generator.validate_firestore_id(doc_id)


def is_uuid_format(doc_id: str) -> bool:
    """Check if an ID is in UUID format (old format)"""
    return _id_generator.is_uuid_format(doc_id)


# Backward compatibility - replace UUID generation
def generate_unique_id() -> str:
    """
    Generate a unique ID using Firestore format.
    This replaces the old UUID-based generation.
    """
    return generate_firestore_id()


def generate_short_id(length: int = 8) -> str:
    """
    Generate a short unique ID.
    Note: This maintains the original behavior for specific use cases.
    """
    import secrets
    import string
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))


# Export the generator instance for advanced usage
get_id_generator = lambda: _id_generator