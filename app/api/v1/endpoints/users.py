"""
User Management API Endpoints
Handles user registration, profile management, and authentication
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer

from app.models.schemas import (
    UserCreate, User, UserUpdate, UserLogin, AuthToken,
    ApiResponse, UserAddress, UserPreferences, ImageUploadResponse
)
from app.services.auth_service import auth_service
# TODO: Implement storage service
# from app.services.storage_service import get_storage_service
from app.database.firestore import get_user_repo
from app.core.security import get_current_user
from app.core.config import settings

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=AuthToken)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    try:
        # Check if user already exists
        user_repo = get_enhanced_user_repo()
        existing_user = await user_repo.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check phone number
        existing_phone = await user_repo.get_by_phone(user_data.phone)
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered"
            )
        
        # Register user
        user = await auth_service.register_user(user_data)
        
        # Login user immediately after registration
        login_data = UserLogin(email=user_data.email, password=user_data.password)
        token = await auth_service.login_user(login_data)
        
        return token
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error registering user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=AuthToken)
async def login_user(login_data: UserLogin):
    """Login user"""
    try:
        token = await auth_service.login_user(login_data)
        
        # TODO: Update last login
        # user_repo = get_user_repo()
        # await user_repo.update_last_login(token.user.id)
        
        return token
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error logging in user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.get("/profile", response_model=User)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user


@router.put("/profile", response_model=User)
async def update_user_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update user profile"""
    try:
        user_repo = get_enhanced_user_repo()
        
        # Check if email is being updated and is unique
        if update_data.email and update_data.email != current_user.email:
            existing_user = await user_repo.get_by_email(update_data.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
        
        # Check if phone is being updated and is unique
        if update_data.phone and update_data.phone != current_user.phone:
            existing_phone = await user_repo.get_by_phone(update_data.phone)
            if existing_phone:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Phone number already in use"
                )
        
        # Update user
        updated_user = await auth_service.update_user(current_user.id, update_data.dict(exclude_unset=True))
        return User(**updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )


@router.post("/profile/image", response_model=ImageUploadResponse)
async def upload_profile_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload user profile image"""
    try:
        # TODO: Implement storage service
        # storage_service = get_storage_service()
        # image_url = await storage_service.upload_image(...)
        
        # Mock implementation for now
        mock_image_url = f"https://example.com/profiles/{current_user.id}/profile.jpg"
        
        # Update user profile with image URL
        user_repo = get_user_repo()
        await user_repo.update(current_user.id, {
            "profile_image_url": mock_image_url
        })
        
        return ImageUploadResponse(
            success=True,
            file_url=mock_image_url,
            file_name=file.filename,
            file_size=0,
            content_type=file.content_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading profile image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image upload failed"
        )


@router.post("/addresses", response_model=ApiResponse)
async def add_user_address(
    address: UserAddress,
    current_user: User = Depends(get_current_user)
):
    """Add a new address for the user"""
    try:
        user_repo = get_enhanced_user_repo()
        # TODO: Implement address management
        # success = await user_repo.add_address(current_user.id, address.dict())
        success = True  # Mock implementation
        
        if success:
            return ApiResponse(
                success=True,
                message="Address added successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add address"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error adding address: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add address"
        )


@router.get("/addresses", response_model=List[UserAddress])
async def get_user_addresses(current_user: User = Depends(get_current_user)):
    """Get all addresses for the user"""
    try:
        user_repo = get_enhanced_user_repo()
        user_data = await user_repo.get_by_id(current_user.id)
        
        if user_data and "addresses" in user_data:
            return [UserAddress(**addr) for addr in user_data["addresses"]]
        
        return []
        
    except Exception as e:
        print(f"Error getting addresses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get addresses"
        )


@router.put("/addresses/{address_id}", response_model=ApiResponse)
async def update_user_address(
    address_id: str,
    address_data: UserAddress,
    current_user: User = Depends(get_current_user)
):
    """Update a specific address"""
    try:
        user_repo = get_enhanced_user_repo()
        # TODO: Implement address update
        # success = await user_repo.update_address(...)
        success = True  # Mock implementation
        
        if success:
            return ApiResponse(
                success=True,
                message="Address updated successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating address: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update address"
        )


@router.delete("/addresses/{address_id}", response_model=ApiResponse)
async def delete_user_address(
    address_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a specific address"""
    try:
        user_repo = get_enhanced_user_repo()
        # TODO: Implement address deletion
        # success = await user_repo.delete_address(current_user.id, address_id)
        success = True  # Mock implementation
        
        if success:
            return ApiResponse(
                success=True,
                message="Address deleted successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting address: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete address"
        )


@router.put("/preferences", response_model=ApiResponse)
async def update_user_preferences(
    preferences: UserPreferences,
    current_user: User = Depends(get_current_user)
):
    """Update user preferences"""
    try:
        user_repo = get_enhanced_user_repo()
        # TODO: Implement preferences update
        # success = await user_repo.update_preferences(current_user.id, preferences.dict())
        success = True  # Mock implementation
        
        if success:
            return ApiResponse(
                success=True,
                message="Preferences updated successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update preferences"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences"
        )


@router.get("/preferences", response_model=UserPreferences)
async def get_user_preferences(current_user: User = Depends(get_current_user)):
    """Get user preferences"""
    try:
        user_repo = get_enhanced_user_repo()
        user_data = await user_repo.get_by_id(current_user.id)
        
        if user_data and "preferences" in user_data:
            return UserPreferences(**user_data["preferences"])
        
        return UserPreferences()
        
    except Exception as e:
        print(f"Error getting preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get preferences"
        )


@router.post("/change-password", response_model=ApiResponse)
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user)
):
    """Change user password"""
    try:
        success = await auth_service.change_password(
            current_user.id, 
            current_password, 
            new_password
        )
        
        if success:
            return ApiResponse(
                success=True,
                message="Password changed successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to change password"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error changing password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.post("/deactivate", response_model=ApiResponse)
async def deactivate_account(
    current_user: User = Depends(get_current_user)
):
    """Deactivate user account"""
    try:
        success = await auth_service.deactivate_user(current_user.id)
        
        if success:
            return ApiResponse(
                success=True,
                message="Account deactivated successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to deactivate account"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deactivating account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate account"
        )


@router.get("/search", response_model=List[User])
async def search_users(
    q: str,
    role: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Search users (admin only)"""
    try:
        # Check if user is admin
        if current_user.role not in ["admin", "cafe_owner"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to search users"
            )
        
        user_repo = get_enhanced_user_repo()
        # TODO: Implement user search
        # users_data = await user_repo.search_users(q, role)
        users_data = []  # Mock implementation
        
        return [User(**user) for user in users_data]
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error searching users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )