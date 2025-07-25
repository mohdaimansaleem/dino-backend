"""
Authentication Service
Production-ready user authentication and management
"""
from typing import Optional, Dict, Any
from datetime import timedelta
from fastapi import HTTPException, status

from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.core.logging_config import LoggerMixin
from app.database.firestore import get_user_repo
from app.models.schemas import UserCreate, UserLogin, User, Token, AuthToken


class AuthService(LoggerMixin):
    """Authentication service for user management"""
    
    async def register_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """Register a new user"""
        user_repo = get_user_repo()
        
        try:
            # Check if user already exists
            existing_user = await user_repo.get_by_email(user_data.email)
            if existing_user:
                self.logger.warning("Registration attempt with existing email", extra={
                    "email": user_data.email
                })
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            
            # Hash password
            hashed_password = get_password_hash(user_data.password)
            
            # Create user data
            user_dict = {
                "email": user_data.email,
                "phone": user_data.phone,
                "first_name": user_data.first_name,
                "last_name": user_data.last_name,
                "role": user_data.role.value,
                "hashed_password": hashed_password,
                "is_active": True,
                "is_verified": False,
                "login_count": 0,
                "total_orders": 0,
                "total_spent": 0.0,
                "addresses": [],
                "preferences": {}
            }
            
            # Save to database
            user_id = await user_repo.create(user_dict)
            
            # Get created user (without password)
            user = await user_repo.get_by_id(user_id)
            if user:
                user.pop("hashed_password", None)
            
            self.log_operation("user_registration", user_id=user_id, email=user_data.email)
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            self.log_error(e, "user_registration", email=user_data.email)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed"
            )
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password"""
        user_repo = get_user_repo()
        
        try:
            user = await user_repo.get_by_email(email)
            if not user:
                self.logger.warning("Authentication attempt with non-existent email", extra={
                    "email": email
                })
                return None
            
            if not verify_password(password, user["hashed_password"]):
                self.logger.warning("Authentication attempt with invalid password", extra={
                    "email": email,
                    "user_id": user.get("id")
                })
                return None
            
            # Remove password from user data
            user.pop("hashed_password", None)
            
            self.log_operation("user_authentication", user_id=user.get("id"), email=email)
            return user
            
        except Exception as e:
            self.log_error(e, "user_authentication", email=email)
            return None
    
    async def login_user(self, login_data: UserLogin) -> AuthToken:
        """Login user and return JWT token"""
        try:
            user = await self.authenticate_user(login_data.email, login_data.password)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            if not user.get("is_active", True):
                self.logger.warning("Login attempt by inactive user", extra={
                    "user_id": user.get("id"),
                    "email": login_data.email
                })
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Inactive user"
                )
            
            # Create access token
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user["id"], "email": user["email"], "role": user["role"]},
                expires_delta=access_token_expires
            )
            
            # Update login count
            user_repo = get_user_repo()
            await user_repo.update(user["id"], {
                "login_count": user.get("login_count", 0) + 1,
                "last_login": user.get("updated_at")
            })
            
            self.log_operation("user_login", user_id=user["id"], email=login_data.email)
            
            return AuthToken(
                access_token=access_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user=User(**user)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            self.log_error(e, "user_login", email=login_data.email)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Login failed"
            )
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        user_repo = get_user_repo()
        
        try:
            user = await user_repo.get_by_id(user_id)
            if user:
                user.pop("hashed_password", None)
            
            self.log_operation("get_user_by_id", user_id=user_id, found=user is not None)
            return user
            
        except Exception as e:
            self.log_error(e, "get_user_by_id", user_id=user_id)
            return None
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user information"""
        user_repo = get_user_repo()
        
        try:
            # Remove sensitive fields that shouldn't be updated directly
            update_data.pop("hashed_password", None)
            update_data.pop("id", None)
            update_data.pop("created_at", None)
            
            # Update user
            await user_repo.update(user_id, update_data)
            
            # Return updated user
            user = await user_repo.get_by_id(user_id)
            if user:
                user.pop("hashed_password", None)
            
            self.log_operation("update_user", user_id=user_id, fields=list(update_data.keys()))
            return user
            
        except Exception as e:
            self.log_error(e, "update_user", user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Update failed"
            )
    
    async def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """Change user password"""
        user_repo = get_user_repo()
        
        try:
            user = await user_repo.get_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Verify current password
            if not verify_password(current_password, user["hashed_password"]):
                self.logger.warning("Password change attempt with invalid current password", extra={
                    "user_id": user_id
                })
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Incorrect current password"
                )
            
            # Hash new password
            new_hashed_password = get_password_hash(new_password)
            
            # Update password
            await user_repo.update(user_id, {"hashed_password": new_hashed_password})
            
            self.log_operation("change_password", user_id=user_id)
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            self.log_error(e, "change_password", user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Password change failed"
            )
    
    async def deactivate_user(self, user_id: str) -> bool:
        """Deactivate user account"""
        user_repo = get_user_repo()
        
        try:
            await user_repo.update(user_id, {"is_active": False})
            self.log_operation("deactivate_user", user_id=user_id)
            return True
            
        except Exception as e:
            self.log_error(e, "deactivate_user", user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Account deactivation failed"
            )


# Service instance
auth_service = AuthService()