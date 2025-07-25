"""
Authentication API Endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any

from app.models.schemas import (
    UserCreate, UserLogin, User, UserUpdate, AuthToken, ApiResponse
)
from app.services.auth_service import auth_service
from app.core.security import get_current_user, get_current_user_id


router = APIRouter()


@router.post("/register", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    try:
        user = await auth_service.register_user(user_data)
        return ApiResponse(
            success=True,
            message="User registered successfully",
            data=user
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=AuthToken)
async def login_user(login_data: UserLogin):
    """Login user and return JWT token"""
    try:
        token = await auth_service.login_user(login_data)
        return token
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information"""
    return User(**current_user)


@router.put("/me", response_model=ApiResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Update current user information"""
    try:
        # Convert to dict and remove None values
        update_data = user_update.dict(exclude_unset=True)
        
        user = await auth_service.update_user(current_user_id, update_data)
        return ApiResponse(
            success=True,
            message="User updated successfully",
            data=user
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update failed: {str(e)}"
        )


@router.post("/change-password", response_model=ApiResponse)
async def change_password(
    current_password: str,
    new_password: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Change user password"""
    try:
        await auth_service.change_password(current_user_id, current_password, new_password)
        return ApiResponse(
            success=True,
            message="Password changed successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password change failed: {str(e)}"
        )


@router.post("/logout", response_model=ApiResponse)
async def logout_user():
    """Logout user (client-side token removal)"""
    return ApiResponse(
        success=True,
        message="Logged out successfully. Please remove the token from client storage."
    )


@router.delete("/deactivate", response_model=ApiResponse)
async def deactivate_account(current_user_id: str = Depends(get_current_user_id)):
    """Deactivate user account"""
    try:
        await auth_service.deactivate_user(current_user_id)
        return ApiResponse(
            success=True,
            message="Account deactivated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Account deactivation failed: {str(e)}"
        )