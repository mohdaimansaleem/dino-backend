"""
Authentication API Endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any

from app.models.schemas import (
    UserCreate, UserLogin, User, UserUpdate, AuthToken, ApiResponse, WorkspaceRegistration
)
from app.services.validation_service import get_validation_service
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
        
        # Log successful login for monitoring
        from app.core.logging_config import get_logger
        logger = get_logger(__name__)
        logger.info("User login successful", extra={
            "user_email": login_data.email,
            "user_id": token.user.id,
            "token_expires_in": token.expires_in
        })
        
        return token
    except HTTPException:
        raise
    except Exception as e:
        from app.core.logging_config import get_logger
        logger = get_logger(__name__)
        logger.error("Login failed", extra={
            "user_email": login_data.email,
            "error": str(e)
        })
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


@router.post("/refresh", response_model=AuthToken)
async def refresh_token(refresh_token: str):
    """Refresh JWT token"""
    try:
        token = await auth_service.refresh_token(refresh_token)
        return token
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
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


# =============================================================================
# WORKSPACE REGISTRATION ENDPOINTS (Consolidated from registration.py)
# =============================================================================

@router.post("/register-workspace", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def register_workspace(registration_data: WorkspaceRegistration):
    """Register a new workspace with venue and superadmin user with comprehensive validation"""
    try:
        from app.services.workspace_service import workspace_service
        from app.core.logging_config import LoggerMixin
        
        # Get validation service
        validation_service = get_validation_service()
        
        # Convert Pydantic model to dict for validation
        registration_dict = registration_data.dict()
        
        # Validate workspace data
        workspace_data = {
            "display_name": registration_dict["workspace_display_name"],
            "description": registration_dict.get("workspace_description"),
            "business_type": registration_dict["business_type"]
        }
        workspace_errors = await validation_service.validate_workspace_data(workspace_data, is_update=False)
        
        # Validate venue data
        venue_data = {
            "name": registration_dict["venue_name"],
            "description": registration_dict["venue_description"],
            "location": registration_dict["venue_location"],
            "phone": registration_dict["venue_phone"],
            "email": registration_dict["venue_email"],
            "website": registration_dict.get("venue_website"),
            "cuisine_types": registration_dict.get("cuisine_types", []),
            "price_range": registration_dict["price_range"]
        }
        venue_errors = await validation_service.validate_venue_data(venue_data, is_update=False)
        
        # Validate user data
        user_data = {
            "email": registration_dict["owner_email"],
            "phone": registration_dict["owner_phone"],
            "first_name": registration_dict["owner_first_name"],
            "last_name": registration_dict["owner_last_name"],
            "password": registration_dict["owner_password"]
        }
        user_errors = await validation_service.validate_user_data(user_data, is_update=False)
        
        # Combine all validation errors
        all_errors = workspace_errors + venue_errors + user_errors
        if all_errors:
            validation_service.raise_validation_exception(all_errors)
        
        class RegistrationHandler(LoggerMixin):
            pass
        
        handler = RegistrationHandler()
        result = await workspace_service.register_workspace(registration_data)
        
        handler.log_operation("workspace_registration", 
                            workspace_id=result["workspace"]["id"],
                            user_id=result["user"]["id"],
                            venue_id=result["venue"]["id"])
        
        return ApiResponse(
            success=True,
            message="Workspace registered successfully. You can now login with your credentials.",
            data={
                "workspace_name": result["workspace"]["name"],
                "workspace_id": result["workspace"]["id"],
                "venue_name": result["venue"]["name"],
                "venue_id": result["venue"]["id"],
                "owner_email": result["user"]["email"]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Workspace registration failed"
        )


@router.post("/workspace-login", response_model=AuthToken)
async def workspace_login(login_data: UserLogin):
    """Login after workspace registration"""
    try:
        from app.core.logging_config import LoggerMixin
        
        class RegistrationHandler(LoggerMixin):
            pass
        
        handler = RegistrationHandler()
        
        # Use existing auth service for login
        token = await auth_service.login_user(login_data)
        
        handler.log_operation("workspace_login", 
                            user_id=token.user.id,
                            email=login_data.email)
        
        return token
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )