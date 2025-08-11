"""
Venue Management API with New Database Hierarchy
- Venues have workspace_id (required)
- Venues can be assigned to multiple users via user.venue_ids
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import datetime

from app.core.security import (
    get_current_user, 
    get_current_admin_user,
    get_current_superadmin_user
)
from app.core.logging_config import get_logger
from app.database.firestore import (
    get_venue_repo, 
    get_workspace_repo,
    get_user_repo
)

logger = get_logger(__name__)
router = APIRouter()


class VenueManagementService:
    """Venue management service with new hierarchy"""
    
    @staticmethod
    async def create_venue(venue_data: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new venue with workspace assignment"""
        try:
            venue_repo = get_venue_repo()
            workspace_repo = get_workspace_repo()
            
            # Validate required fields
            required_fields = ['name', 'description', 'workspace_id', 'location', 'phone']
            for field in required_fields:
                if not venue_data.get(field):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"{field} is required"
                    )
            
            # Validate workspace exists
            workspace = await workspace_repo.get_by_id(venue_data['workspace_id'])
            if not workspace:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Workspace not found"
                )
            
            # Validate location structure
            location = venue_data['location']
            required_location_fields = ['address', 'city', 'state', 'country', 'postal_code']
            for field in required_location_fields:
                if not location.get(field):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"location.{field} is required"
                    )
            
            # Prepare venue data
            new_venue = {
                'name': venue_data['name'],
                'description': venue_data['description'],
                'workspace_id': venue_data['workspace_id'],
                'location': location,
                'phone': venue_data['phone'],
                'email': venue_data.get('email', ''),
                'website': venue_data.get('website', ''),
                'price_range': venue_data.get('price_range', 'mid_range'),
                'subscription_plan': venue_data.get('subscription_plan', 'basic'),
                'subscription_status': venue_data.get('subscription_status', 'active'),
                'status': venue_data.get('status', 'active'),
                'is_active': True,
                'is_open': venue_data.get('is_open', True),
                'rating_total': 0.0,
                'rating_count': 0,
                'admin_id': venue_data.get('admin_id'),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            # Create venue
            venue_id = await venue_repo.create(new_venue)
            new_venue['id'] = venue_id
            
            logger.info(f"Venue created successfully: {venue_data['name']}")
            return new_venue
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating venue: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create venue"
            )
    
    @staticmethod
    async def update_venue(venue_id: str, update_data: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
        """Update venue"""
        try:
            venue_repo = get_venue_repo()
            workspace_repo = get_workspace_repo()
            
            # Get existing venue
            existing_venue = await venue_repo.get_by_id(venue_id)
            if not existing_venue:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Venue not found"
                )
            
            # Validate workspace if being updated
            if 'workspace_id' in update_data:
                workspace = await workspace_repo.get_by_id(update_data['workspace_id'])
                if not workspace:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Workspace not found"
                    )
            
            # Add updated timestamp
            update_data['updated_at'] = datetime.utcnow()
            
            # Update venue
            await venue_repo.update(venue_id, update_data)
            
            # Get updated venue
            updated_venue = await venue_repo.get_by_id(venue_id)
            
            logger.info(f"Venue updated successfully: {venue_id}")
            return updated_venue
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating venue: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update venue"
            )
    
    @staticmethod
    async def get_venues_by_workspace(workspace_id: str, current_user: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get all venues in a workspace"""
        try:
            venue_repo = get_venue_repo()
            
            # Get all venues
            all_venues = await venue_repo.get_all()
            
            # Filter venues by workspace
            workspace_venues = [
                venue for venue in all_venues 
                if venue.get('workspace_id') == workspace_id
            ]
            
            return workspace_venues
            
        except Exception as e:
            logger.error(f"Error getting venues by workspace: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get workspace venues"
            )
    
    @staticmethod
    async def get_venue_users(venue_id: str, current_user: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get all users assigned to a venue"""
        try:
            user_repo = get_user_repo()
            
            # Get all users
            all_users = await user_repo.get_all()
            
            # Filter users who have this venue in their venue_ids
            venue_users = []
            for user in all_users:
                user_venue_ids = user.get('venue_ids', [])
                if venue_id in user_venue_ids:
                    user.pop('hashed_password', None)
                    venue_users.append(user)
            
            return venue_users
            
        except Exception as e:
            logger.error(f"Error getting venue users: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get venue users"
            )


# =============================================================================
# VENUE MANAGEMENT ENDPOINTS
# =============================================================================

@router.post("/venues", summary="Create venue")
async def create_venue(
    venue_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Create a new venue"""
    venue = await VenueManagementService.create_venue(venue_data, current_user)
    return {
        "success": True,
        "message": "Venue created successfully",
        "data": venue
    }


@router.get("/venues", summary="Get all venues")
async def get_venues(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    workspace_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get venues with filtering and pagination"""
    try:
        venue_repo = get_venue_repo()
        
        # Get venues
        if workspace_id:
            venues = await VenueManagementService.get_venues_by_workspace(workspace_id, current_user)
        else:
            venues = await venue_repo.get_all()
        
        # Apply search filter
        if search:
            search_lower = search.lower()
            venues = [
                venue for venue in venues
                if (search_lower in venue.get('name', '').lower() or
                    search_lower in venue.get('description', '').lower() or
                    search_lower in venue.get('location', {}).get('city', '').lower())
            ]
        
        # Apply active filter
        if is_active is not None:
            venues = [venue for venue in venues if venue.get('is_active') == is_active]
        
        # Pagination
        total = len(venues)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_venues = venues[start:end]
        
        return {
            "success": True,
            "data": {
                "venues": paginated_venues,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "pages": (total + page_size - 1) // page_size
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting venues: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get venues"
        )


@router.get("/venues/{venue_id}", summary="Get venue by ID")
async def get_venue(
    venue_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get venue by ID"""
    try:
        venue_repo = get_venue_repo()
        venue = await venue_repo.get_by_id(venue_id)
        
        if not venue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Venue not found"
            )
        
        return {
            "success": True,
            "data": venue
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting venue: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get venue"
        )


@router.put("/venues/{venue_id}", summary="Update venue")
async def update_venue(
    venue_id: str,
    update_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Update venue"""
    venue = await VenueManagementService.update_venue(venue_id, update_data, current_user)
    return {
        "success": True,
        "message": "Venue updated successfully",
        "data": venue
    }


@router.get("/venues/{venue_id}/users", summary="Get venue users")
async def get_venue_users(
    venue_id: str,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Get all users assigned to a venue"""
    users = await VenueManagementService.get_venue_users(venue_id, current_user)
    return {
        "success": True,
        "data": users
    }


@router.get("/workspaces/{workspace_id}/venues", summary="Get venues by workspace")
async def get_venues_by_workspace(
    workspace_id: str,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Get all venues in a workspace"""
    venues = await VenueManagementService.get_venues_by_workspace(workspace_id, current_user)
    return {
        "success": True,
        "data": venues
    }


@router.delete("/venues/{venue_id}", summary="Deactivate venue")
async def deactivate_venue(
    venue_id: str,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Deactivate venue (soft delete)"""
    try:
        venue_repo = get_venue_repo()
        
        # Check if venue exists
        venue = await venue_repo.get_by_id(venue_id)
        if not venue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Venue not found"
            )
        
        # Deactivate venue
        await venue_repo.update(venue_id, {
            'is_active': False,
            'updated_at': datetime.utcnow()
        })
        
        logger.info(f"Venue deactivated: {venue_id}")
        return {
            "success": True,
            "message": "Venue deactivated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating venue: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate venue"
        )


@router.post("/venues/{venue_id}/activate", summary="Activate venue")
async def activate_venue(
    venue_id: str,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Activate venue"""
    try:
        venue_repo = get_venue_repo()
        
        # Check if venue exists
        venue = await venue_repo.get_by_id(venue_id)
        if not venue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Venue not found"
            )
        
        # Activate venue
        await venue_repo.update(venue_id, {
            'is_active': True,
            'updated_at': datetime.utcnow()
        })
        
        logger.info(f"Venue activated: {venue_id}")
        return {
            "success": True,
            "message": "Venue activated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating venue: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate venue"
        )