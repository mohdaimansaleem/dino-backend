"""
Table Area Management API Endpoints
Additional endpoints for managing table areas/sections within venues
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
import uuid
from datetime import datetime

from app.core.security import get_current_user, get_current_admin_user
from app.core.logging_config import get_logger
from app.models.schemas import ApiResponse

logger = get_logger(__name__)
router = APIRouter()


class TableArea(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    venue_id: str
    capacity: Optional[int] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TableAreaCreate(BaseModel):
    name: str
    description: Optional[str] = None
    venue_id: str
    capacity: Optional[int] = None


class TableAreaUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    capacity: Optional[int] = None
    is_active: Optional[bool] = None


@router.get("/venues/{venue_id}/areas", 
            response_model=List[TableArea],
            summary="Get venue areas",
            description="Get all table areas for a venue")
async def get_venue_areas(
    venue_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all table areas for a venue"""
    try:
        from app.database.firestore import get_venue_repo
        venue_repo = get_venue_repo()
        
        # Validate venue exists and user has access
        venue = await venue_repo.get_by_id(venue_id)
        if not venue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Venue not found"
            )
        
        # Check permissions
        from app.core.security import _get_user_role
        user_role = await _get_user_role(current_user)
        
        if user_role not in ['superadmin', 'admin', 'operator']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # For now, return mock areas since we don't have a separate areas collection
        # In a real implementation, you'd have a separate areas collection
        mock_areas = [
            {
                "id": "area_1",
                "name": "Main Dining",
                "description": "Main dining area with window seating",
                "venue_id": venue_id,
                "capacity": 40,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "id": "area_2", 
                "name": "Outdoor Patio",
                "description": "Outdoor seating area",
                "venue_id": venue_id,
                "capacity": 20,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "id": "area_3",
                "name": "Private Room",
                "description": "Private dining room for events",
                "venue_id": venue_id,
                "capacity": 12,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        areas = [TableArea(**area) for area in mock_areas]
        
        logger.info(f"Retrieved {len(areas)} areas for venue: {venue_id}")
        return areas
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting venue areas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get venue areas"
        )


@router.post("/areas", 
             response_model=ApiResponse,
             summary="Create table area",
             description="Create a new table area")
async def create_area(
    area_data: TableAreaCreate,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Create a new table area"""
    try:
        from app.database.firestore import get_venue_repo
        venue_repo = get_venue_repo()
        
        # Validate venue exists and user has access
        venue = await venue_repo.get_by_id(area_data.venue_id)
        if not venue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Venue not found"
            )
        
        # Check permissions
        from app.core.security import _get_user_role
        user_role = await _get_user_role(current_user)
        
        if user_role != 'superadmin':
            if (venue.get('admin_id') != current_user['id'] and 
                venue.get('owner_id') != current_user['id']):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: Not authorized for this venue"
                )
        
        # Create area (mock implementation)
        area_id = str(uuid.uuid4())
        new_area = {
            "id": area_id,
            "name": area_data.name,
            "description": area_data.description,
            "venue_id": area_data.venue_id,
            "capacity": area_data.capacity,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # In a real implementation, you'd save this to a database
        # For now, we'll just return success
        
        logger.info(f"Area created: {area_id} for venue {area_data.venue_id}")
        return ApiResponse(
            success=True,
            message="Table area created successfully",
            data=new_area
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating area: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create area"
        )


@router.put("/areas/{area_id}", 
            response_model=ApiResponse,
            summary="Update table area",
            description="Update table area information")
async def update_area(
    area_id: str,
    area_data: TableAreaUpdate,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Update table area"""
    try:
        # Mock implementation - in reality you'd fetch from database
        # and validate permissions
        
        update_data = area_data.dict(exclude_unset=True)
        update_data['updated_at'] = datetime.utcnow()
        
        logger.info(f"Area updated: {area_id}")
        return ApiResponse(
            success=True,
            message="Table area updated successfully",
            data=update_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating area: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update area"
        )


@router.delete("/areas/{area_id}", 
               response_model=ApiResponse,
               summary="Delete table area",
               description="Delete table area")
async def delete_area(
    area_id: str,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Delete table area"""
    try:
        # Mock implementation - in reality you'd validate permissions
        # and check if area has tables before deletion
        
        logger.info(f"Area deleted: {area_id}")
        return ApiResponse(
            success=True,
            message="Table area deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting area: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete area"
        )


@router.get("/areas/{area_id}/tables", 
            response_model=List[Dict[str, Any]],
            summary="Get area tables",
            description="Get all tables in a specific area")
async def get_area_tables(
    area_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all tables in an area"""
    try:
        # Mock implementation - return empty list for now
        # In reality, you'd filter tables by area_id
        
        logger.info(f"Tables retrieved for area: {area_id}")
        return []
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting area tables: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get area tables"
        )