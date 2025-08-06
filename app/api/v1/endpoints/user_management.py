"""
User Management API with New Database Hierarchy
- Users have venue_ids list (not workspace_id)
- Venues have workspace_id
- Phone numbers are required and unique
- No profile images in user collection
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import datetime

from app.core.security import (
    get_current_user, 
    get_current_admin_user,
    get_current_superadmin_user,
    get_password_hash,
    verify_password
)
from app.core.logging_config import get_logger
from app.database.firestore import (
    get_user_repo, 
    get_venue_repo, 
    get_workspace_repo
)

logger = get_logger(__name__)
router = APIRouter()


class UserManagementService:
    """User management service with new hierarchy"""
    
    @staticmethod
    async def create_user(user_data: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user with venue assignments"""
        try:
            user_repo = get_user_repo()
            
            # Validate required fields
            required_fields = ['email', 'phone', 'first_name', 'last_name', 'password']
            for field in required_fields:
                if not user_data.get(field):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"{field} is required"
                    )
            
            # Check email uniqueness
            existing_email = await user_repo.get_by_email(user_data['email'])
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )
            
            # Check phone uniqueness
            existing_phone = await user_repo.get_by_phone(user_data['phone'])
            if existing_phone:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Phone number already exists"
                )
            
            # Validate venue assignments
            venue_ids = user_data.get('venue_ids', [])
            if venue_ids:
                venue_repo = get_venue_repo()
                for venue_id in venue_ids:
                    venue = await venue_repo.get_by_id(venue_id)
                    if not venue:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Venue {venue_id} not found"
                        )
            
            # Hash password
            hashed_password = get_password_hash(user_data['password'])
            
            # Prepare user data
            new_user = {
                'email': user_data['email'],
                'phone': user_data['phone'],
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'hashed_password': hashed_password,
                'role': user_data.get('role', 'operator'),
                'venue_ids': venue_ids,
                'is_active': True,
                'is_verified': False,
                'email_verified': False,
                'phone_verified': False,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            # Create user
            user_id = await user_repo.create(new_user)
            new_user['id'] = user_id
            
            # Remove password from response
            new_user.pop('hashed_password', None)
            
            logger.info(f"User created successfully: {user_data['email']}")
            return new_user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
    
    @staticmethod
    async def update_user(user_id: str, update_data: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
        """Update user with venue assignments"""
        try:
            user_repo = get_user_repo()
            
            # Get existing user
            existing_user = await user_repo.get_by_id(user_id)
            if not existing_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Check email uniqueness if being updated
            if 'email' in update_data and update_data['email'] != existing_user.get('email'):
                existing_email = await user_repo.get_by_email(update_data['email'])
                if existing_email:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already exists"
                    )
            
            # Check phone uniqueness if being updated
            if 'phone' in update_data and update_data['phone'] != existing_user.get('phone'):
                existing_phone = await user_repo.get_by_phone(update_data['phone'])
                if existing_phone:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Phone number already exists"
                    )
            
            # Validate venue assignments if being updated
            if 'venue_ids' in update_data:
                venue_ids = update_data['venue_ids']
                if venue_ids:
                    venue_repo = get_venue_repo()
                    for venue_id in venue_ids:
                        venue = await venue_repo.get_by_id(venue_id)
                        if not venue:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Venue {venue_id} not found"
                            )
            
            # Handle password update
            if 'password' in update_data:
                update_data['hashed_password'] = get_password_hash(update_data['password'])
                update_data.pop('password')
            
            # Add updated timestamp
            update_data['updated_at'] = datetime.utcnow()
            
            # Update user
            await user_repo.update(user_id, update_data)
            
            # Get updated user
            updated_user = await user_repo.get_by_id(user_id)
            updated_user.pop('hashed_password', None)
            
            logger.info(f"User updated successfully: {user_id}")
            return updated_user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user"
            )
    
    @staticmethod
    async def assign_venues_to_user(user_id: str, venue_ids: List[str], current_user: Dict[str, Any]) -> Dict[str, Any]:
        """Assign venues to a user"""
        try:
            user_repo = get_user_repo()
            venue_repo = get_venue_repo()
            
            # Get user
            user = await user_repo.get_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Validate all venues exist
            for venue_id in venue_ids:
                venue = await venue_repo.get_by_id(venue_id)
                if not venue:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Venue {venue_id} not found"
                    )
            
            # Update user's venue assignments
            await user_repo.update(user_id, {
                'venue_ids': venue_ids,
                'updated_at': datetime.utcnow()
            })
            
            # Get updated user
            updated_user = await user_repo.get_by_id(user_id)
            updated_user.pop('hashed_password', None)
            
            logger.info(f"Venues assigned to user {user_id}: {venue_ids}")
            return updated_user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error assigning venues to user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to assign venues"
            )
    
    @staticmethod
    async def get_users_by_venue(venue_id: str, current_user: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get all users assigned to a specific venue"""
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
            logger.error(f"Error getting users by venue: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get venue users"
            )


# =============================================================================
# USER MANAGEMENT ENDPOINTS
# =============================================================================

@router.post("/users", summary="Create user")
async def create_user(
    user_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Create a new user with venue assignments"""
    user = await UserManagementService.create_user(user_data, current_user)
    return {
        "success": True,
        "message": "User created successfully",
        "data": user
    }


@router.get("/users", summary="Get all users")
async def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    venue_id: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Get users with filtering and pagination"""
    try:
        user_repo = get_user_repo()
        
        # Build filters
        filters = []
        if role:
            filters.append(('role', '==', role))
        
        # Get users
        if venue_id:
            users = await UserManagementService.get_users_by_venue(venue_id, current_user)
        else:
            users = await user_repo.get_all()
        
        # Remove passwords
        for user in users:
            user.pop('hashed_password', None)
        
        # Apply search filter
        if search:
            search_lower = search.lower()
            users = [
                user for user in users
                if (search_lower in user.get('first_name', '').lower() or
                    search_lower in user.get('last_name', '').lower() or
                    search_lower in user.get('email', '').lower() or
                    search_lower in user.get('phone', '').lower())
            ]
        
        # Apply role filter
        if role:
            users = [user for user in users if user.get('role') == role]
        
        # Pagination
        total = len(users)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_users = users[start:end]
        
        return {
            "success": True,
            "data": {
                "users": paginated_users,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "pages": (total + page_size - 1) // page_size
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get users"
        )


@router.get("/users/{user_id}", summary="Get user by ID")
async def get_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get user by ID"""
    try:
        user_repo = get_user_repo()
        user = await user_repo.get_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Remove password
        user.pop('hashed_password', None)
        
        return {
            "success": True,
            "data": user
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user"
        )


@router.put("/users/{user_id}", summary="Update user")
async def update_user(
    user_id: str,
    update_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update user"""
    # Check permissions
    if user_id != current_user['id'] and current_user.get('role') not in ['admin', 'superadmin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )
    
    user = await UserManagementService.update_user(user_id, update_data, current_user)
    return {
        "success": True,
        "message": "User updated successfully",
        "data": user
    }


@router.post("/users/{user_id}/assign-venues", summary="Assign venues to user")
async def assign_venues_to_user(
    user_id: str,
    venue_ids: List[str],
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Assign venues to a user"""
    user = await UserManagementService.assign_venues_to_user(user_id, venue_ids, current_user)
    return {
        "success": True,
        "message": "Venues assigned successfully",
        "data": user
    }


@router.get("/venues/{venue_id}/users", summary="Get users by venue")
async def get_users_by_venue(
    venue_id: str,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Get all users assigned to a venue"""
    users = await UserManagementService.get_users_by_venue(venue_id, current_user)
    return {
        "success": True,
        "data": users
    }


@router.put("/users/{user_id}/deactivate", summary="Deactivate user")
async def deactivate_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Deactivate user (set is_active to False)"""
    try:
        user_repo = get_user_repo()
        
        # Check if user exists
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Deactivate user
        await user_repo.update(user_id, {
            'is_active': False,
            'updated_at': datetime.utcnow()
        })
        
        logger.info(f"User deactivated: {user_id}")
        return {
            "success": True,
            "message": "User deactivated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )


@router.put("/users/{user_id}/activate", summary="Activate user")
async def activate_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Activate user"""
    try:
        user_repo = get_user_repo()
        
        # Check if user exists
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Activate user
        await user_repo.update(user_id, {
            'is_active': True,
            'updated_at': datetime.utcnow()
        })
        
        logger.info(f"User activated: {user_id}")
        return {
            "success": True,
            "message": "User activated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate user"
        )