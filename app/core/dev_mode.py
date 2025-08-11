"""
Development mode utilities for testing without external dependencies
"""
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.models.dto import PaginatedResponseDTO

class MockRepository:
    """Mock repository for development mode"""
    
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self._data = self._get_mock_data()
    
    def _get_mock_data(self) -> List[Dict[str, Any]]:
        """Get mock data based on collection name"""
        if self.collection_name == "workspaces":
            return [
                {
                    "id": "workspace_1",
                    "name": "demo_workspace_1",
                    "display_name": "Demo Restaurant Group",
                    "description": "A demo workspace for testing",
                    "is_active": True,
                    "owner_id": "user_1",
                    "venue_ids": ["venue_1", "venue_2"],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                {
                    "id": "workspace_2", 
                    "name": "demo_workspace_2",
                    "display_name": "Demo Cafe Chain",
                    "description": "Another demo workspace",
                    "is_active": True,
                    "owner_id": "user_2",
                    "venue_ids": ["venue_3"],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                {
                    "id": "workspace_3",
                    "name": "demo_workspace_3", 
                    "display_name": "Demo Food Court",
                    "description": "Food court workspace",
                    "is_active": False,
                    "owner_id": "user_3",
                    "venue_ids": [],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            ]
        elif self.collection_name == "users":
            return [
                {
                    "id": "user_1",
                    "email": "admin@demo.com",
                    "phone": "1234567890",
                    "first_name": "Demo",
                    "last_name": "Admin",
                    "role_id": "role_superadmin",
                    "workspace_id": "workspace_1",
                    "venue_ids": ["venue_1", "venue_2"],
                    "is_active": True,
                    "is_verified": True,
                    "email_verified": True,
                    "phone_verified": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                {
                    "id": "user_2",
                    "email": "manager@demo.com", 
                    "phone": "1234567891",
                    "first_name": "Demo",
                    "last_name": "Manager",
                    "role_id": "role_admin",
                    "workspace_id": "workspace_2",
                    "venue_ids": ["venue_3"],
                    "is_active": True,
                    "is_verified": True,
                    "email_verified": True,
                    "phone_verified": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            ]
        elif self.collection_name == "roles":
            return [
                {
                    "id": "role_superadmin",
                    "name": "superadmin",
                    "description": "Super Administrator with full access",
                    "permission_ids": ["perm_1", "perm_2", "perm_3"],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                {
                    "id": "role_admin",
                    "name": "admin", 
                    "description": "Administrator with venue access",
                    "permission_ids": ["perm_2", "perm_3"],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                {
                    "id": "role_operator",
                    "name": "operator",
                    "description": "Operator with limited access",
                    "permission_ids": ["perm_3"],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            ]
        else:
            return []
    
    async def get_all(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all mock data"""
        data = self._data.copy()
        if limit:
            data = data[:limit]
        return data
    
    async def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get mock data by ID"""
        for item in self._data:
            if item["id"] == doc_id:
                return item.copy()
        return None
    
    async def query(self, filters: List[tuple], order_by: Optional[str] = None, 
                   limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Query mock data with filters"""
        results = self._data.copy()
        
        # Apply filters
        for field, operator, value in filters:
            if operator == "==":
                results = [item for item in results if item.get(field) == value]
            elif operator == "!=":
                results = [item for item in results if item.get(field) != value]
            # Add more operators as needed
        
        # Apply limit
        if limit:
            results = results[:limit]
            
        return results
    
    async def create(self, data: Dict[str, Any], doc_id: Optional[str] = None) -> Dict[str, Any]:
        """Create mock data"""
        if not doc_id:
            doc_id = f"{self.collection_name}_{len(self._data) + 1}"
        
        data["id"] = doc_id
        data["created_at"] = datetime.utcnow()
        data["updated_at"] = datetime.utcnow()
        
        self._data.append(data.copy())
        return data
    
    async def update(self, doc_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update mock data"""
        for i, item in enumerate(self._data):
            if item["id"] == doc_id:
                self._data[i].update(data)
                self._data[i]["updated_at"] = datetime.utcnow()
                return self._data[i].copy()
        raise ValueError(f"Document {doc_id} not found")
    
    async def delete(self, doc_id: str) -> bool:
        """Delete mock data"""
        for i, item in enumerate(self._data):
            if item["id"] == doc_id:
                del self._data[i]
                return True
        return False


def is_dev_mode() -> bool:
    """Check if we're in development mode"""
    return os.environ.get("DEV_MODE", "false").lower() == "true"


def get_mock_workspace_repo():
    """Get mock workspace repository"""
    return MockRepository("workspaces")


def get_mock_user_repo():
    """Get mock user repository"""
    return MockRepository("users")


def get_mock_role_repo():
    """Get mock role repository"""
    return MockRepository("roles")


def create_mock_paginated_response(
    data: List[Dict[str, Any]], 
    page: int = 1, 
    page_size: int = 10,
    search: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None
) -> PaginatedResponseDTO:
    """Create a mock paginated response"""
    
    # Apply search filter if provided
    if search:
        search_lower = search.lower()
        data = [
            item for item in data 
            if search_lower in item.get("name", "").lower() or 
               search_lower in item.get("display_name", "").lower() or
               search_lower in item.get("description", "").lower()
        ]
    
    # Apply additional filters
    if filters:
        for key, value in filters.items():
            if value is not None:
                data = [item for item in data if item.get(key) == value]
    
    # Calculate pagination
    total = len(data)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_data = data[start_idx:end_idx]
    
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    has_next = page < total_pages
    has_prev = page > 1
    
    return PaginatedResponseDTO(
        success=True,
        data=paginated_data,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev
    )