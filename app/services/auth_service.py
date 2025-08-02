"""
Authentication Service
Production-ready user authentication and management
"""
from typing import Optional, Dict, Any, List
from datetime import timedelta, datetime
from fastapi import HTTPException, status

from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.core.logging_config import EnhancedLoggerMixin, log_function_call
from app.core.logging_middleware import business_logger
import time
from app.database.firestore import get_user_repo
from app.models.schemas import UserCreate, UserLogin, User, Token, AuthToken


class AuthService(EnhancedLoggerMixin):
    """Authentication service for user management"""
    
    def _convert_date_to_datetime(self, date_obj):
        """Convert date object to datetime for Firestore compatibility"""
        if date_obj is None:
            return None
        
        from datetime import datetime, date
        if isinstance(date_obj, date) and not isinstance(date_obj, datetime):
            # Convert date to datetime at midnight
            return datetime.combine(date_obj, datetime.min.time())
        elif isinstance(date_obj, datetime):
            return date_obj
        else:
            return date_obj
    
    def _convert_datetime_to_date(self, datetime_obj):
        """Convert datetime object back to date for schema compatibility"""
        if datetime_obj is None:
            return None
        
        from datetime import datetime, date
        if isinstance(datetime_obj, datetime):
            # Convert datetime to date
            return datetime_obj.date()
        elif isinstance(datetime_obj, date):
            return datetime_obj
        else:
            return datetime_obj
    
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
            
            # Set default role_id if not provided
            role_id = user_data.role_id
            if not role_id:
                # Get or create default operator role
                from app.database.firestore import get_role_repo
                role_repo = get_role_repo()
                
                # Try to find existing operator role
                operator_role = await role_repo.get_by_name("operator")
                if operator_role:
                    role_id = operator_role["id"]
                else:
                    # Create default operator role if it doesn't exist
                    role_data = {
                        "name": "operator",
                        "description": "Default operator role",
                        "permission_ids": []
                    }
                    role_id = await role_repo.create(role_data)
            
            # Hash password
            hashed_password = get_password_hash(user_data.password)
            
            # Create user data
            user_dict = {
                "email": user_data.email,
                "mobile_number": user_data.mobile_number,
                "first_name": user_data.first_name,
                "last_name": user_data.last_name,
                "role_id": role_id,
                "date_of_birth": self._convert_date_to_datetime(user_data.date_of_birth),
                "gender": user_data.gender,
                "hashed_password": hashed_password,
                "is_active": True,
                "is_verified": False,
                "email_verified": False,
                "mobile_verified": False,
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
    
    @log_function_call(include_args=False, include_result=False)
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password"""
        start_time = time.time()
        user_repo = get_user_repo()
        
        try:
            self.log_debug("Starting user authentication", email=email)
            
            # Log business operation
            business_logger.log_business_operation(
                operation="authenticate_user",
                entity_type="user",
                details={"email": email}
            )
            
            # Add timeout protection for database call
            import asyncio
            try:
                user = await asyncio.wait_for(user_repo.get_by_email(email), timeout=10.0)
            except asyncio.TimeoutError:
                self.log_error("Database timeout during user lookup", email=email)
                return None
            
            if not user:
                duration_ms = (time.time() - start_time) * 1000
                
                self.log_warning("Authentication failed - user not found", 
                               email=email, 
                               duration_ms=duration_ms,
                               failure_reason="user_not_found")
                
                business_logger.log_authorization_check(
                    operation="authenticate",
                    user_id="unknown",
                    resource="user_account",
                    allowed=False,
                    reason="user_not_found"
                )
                
                return None
            
            # Check if user is active
            if not user.get("is_active", True):
                duration_ms = (time.time() - start_time) * 1000
                self.log_warning("Authentication failed - user inactive", 
                               email=email,
                               user_id=user.get("id"),
                               duration_ms=duration_ms)
                return None
            
            if not verify_password(password, user["hashed_password"]):
                duration_ms = (time.time() - start_time) * 1000
                
                self.log_warning("Authentication failed - invalid password", 
                               email=email,
                               user_id=user.get("id"),
                               duration_ms=duration_ms,
                               failure_reason="invalid_password")
                
                business_logger.log_authorization_check(
                    operation="authenticate",
                    user_id=user.get("id"),
                    resource="user_account",
                    allowed=False,
                    reason="invalid_password"
                )
                
                return None
            
            # Remove password from user data
            user.pop("hashed_password", None)
            
            duration_ms = (time.time() - start_time) * 1000
            
            self.log_info("User authentication successful", 
                         user_id=user.get("id"), 
                         email=email,
                         duration_ms=duration_ms)
            
            business_logger.log_authorization_check(
                operation="authenticate",
                user_id=user.get("id"),
                resource="user_account",
                allowed=True,
                reason="valid_credentials"
            )
            
            return user
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            self.log_error(e, "user_authentication", 
                          email=email, 
                          duration_ms=duration_ms)
            
            business_logger.log_business_operation(
                operation="authenticate_user_error",
                entity_type="user",
                details={"email": email, "error": str(e)}
            )
            
            return None
    
    async def login_user(self, login_data: UserLogin) -> AuthToken:
        """Login user and return JWT token with permissions"""
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
            
            # Get user permissions and role information
            user_permissions = await self._get_user_permissions(user)
            
            # Create access token with role and permissions
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={
                    "sub": user["id"], 
                    "email": user["email"], 
                    "role_id": user["role_id"],
                    "permissions": [p["name"] for p in user_permissions["permissions"]]
                },
                expires_delta=access_token_expires
            )
            
            # Update login count (async, don't wait for completion)
            user_repo = get_user_repo()
            try:
                await user_repo.update(user["id"], {
                    "login_count": user.get("login_count", 0) + 1,
                    "last_login": datetime.utcnow()
                })
            except Exception as update_error:
                # Log but don't fail login for this
                self.log_warning("Failed to update login count", user_id=user["id"], error=str(update_error))
            
            self.log_operation("user_login", user_id=user["id"], email=login_data.email)
            
            # Ensure user data has all required fields for User schema
            user_for_token = {
                "id": user["id"],
                "email": user["email"],
                "mobile_number": user["mobile_number"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "role_id": user.get("role_id"),
                "date_of_birth": self._convert_datetime_to_date(user.get("date_of_birth")),
                "gender": user.get("gender"),
                "is_active": user.get("is_active", True),
                "is_verified": user.get("is_verified", False),
                "email_verified": user.get("email_verified", False),
                "mobile_verified": user.get("mobile_verified", False),
                "last_login": user.get("last_login"),
                "created_at": user.get("created_at"),
                "updated_at": user.get("updated_at"),
                # Add permissions and role info
                "role": user_permissions["role"]["name"],
                "permissions": user_permissions["permissions"],
                "workspace_id": user.get("workspace_id"),
                "venue_id": user.get("venue_id")
            }
            
            # Create refresh token
            refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            refresh_token = create_access_token(
                data={"sub": user["id"], "type": "refresh"},
                expires_delta=refresh_token_expires
            )
            
            return AuthToken(
                access_token=access_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                refresh_token=refresh_token,
                user=User(**user_for_token)
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
            
            # Convert date fields to datetime for Firestore compatibility
            if "date_of_birth" in update_data:
                update_data["date_of_birth"] = self._convert_date_to_datetime(update_data["date_of_birth"])
            
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
    
    async def refresh_token(self, refresh_token: str) -> AuthToken:
        """Refresh JWT token"""
        from app.core.security import verify_token, create_access_token
        
        try:
            # Verify refresh token
            payload = verify_token(refresh_token)
            user_id = payload.get("sub")
            token_type = payload.get("type")
            
            if not user_id or token_type != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            # Get user data
            user = await self.get_user_by_id(user_id)
            if not user or not user.get("is_active", True):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
            
            # Create new access token
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user["id"], "email": user["email"], "role_id": user["role_id"]},
                expires_delta=access_token_expires
            )
            
            # Create new refresh token
            refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            new_refresh_token = create_access_token(
                data={"sub": user["id"], "type": "refresh"},
                expires_delta=refresh_token_expires
            )
            
            # Prepare user data for response
            user_for_token = {
                "id": user["id"],
                "email": user["email"],
                "mobile_number": user["mobile_number"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "role_id": user.get("role_id"),
                "date_of_birth": self._convert_datetime_to_date(user.get("date_of_birth")),
                "gender": user.get("gender"),
                "is_active": user.get("is_active", True),
                "is_verified": user.get("is_verified", False),
                "email_verified": user.get("email_verified", False),
                "mobile_verified": user.get("mobile_verified", False),
                "last_login": user.get("last_login"),
                "created_at": user.get("created_at"),
                "updated_at": user.get("updated_at")
            }
            
            self.log_operation("token_refresh", user_id=user_id)
            
            return AuthToken(
                access_token=access_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                refresh_token=new_refresh_token,
                user=User(**user_for_token)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            self.log_error(e, "token_refresh")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token refresh failed"
            )
    
    async def _get_user_permissions(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Get user permissions and role information - optimized for login"""
        try:
            from app.database.firestore import get_role_repo
            
            role_repo = get_role_repo()
            user_role_id = user.get('role_id')
            
            if not user_role_id:
                # Return default empty permissions
                return {
                    'role': {'id': None, 'name': 'operator', 'display_name': 'Operator'},
                    'permissions': [],
                    'dashboard_permissions': self._get_default_dashboard_permissions('operator')
                }
            
            # Get role with permissions
            role = await role_repo.get_by_id(user_role_id)
            if not role:
                # Return default empty permissions
                return {
                    'role': {'id': user_role_id, 'name': 'operator', 'display_name': 'Operator'},
                    'permissions': [],
                    'dashboard_permissions': self._get_default_dashboard_permissions('operator')
                }
            
            role_name = role.get('name', 'operator')
            
            # Skip detailed permission loading during login for performance
            # Just return basic role info and default permissions
            basic_permissions = self._get_basic_role_permissions(role_name)
            dashboard_permissions = self._get_default_dashboard_permissions(role_name)
            
            return {
                'role': {
                    'id': role['id'],
                    'name': role_name,
                    'display_name': role.get('display_name', role_name.title()),
                    'description': role.get('description', '')
                },
                'permissions': basic_permissions,
                'dashboard_permissions': dashboard_permissions
            }
            
        except Exception as e:
            self.log_error(e, "get_user_permissions", user_id=user.get('id'))
            # Return default empty permissions on error
            return {
                'role': {'id': None, 'name': 'operator', 'display_name': 'Operator'},
                'permissions': [],
                'dashboard_permissions': self._get_default_dashboard_permissions('operator')
            }
    
    def _get_basic_role_permissions(self, role_name: str) -> List[Dict[str, Any]]:
        """Get basic permissions for role without database calls"""
        if role_name == 'superadmin':
            return [
                {'name': 'workspace:manage', 'resource': 'workspace', 'action': 'manage'},
                {'name': 'venue:manage', 'resource': 'venue', 'action': 'manage'},
                {'name': 'user:manage', 'resource': 'user', 'action': 'manage'},
                {'name': 'order:manage', 'resource': 'order', 'action': 'manage'},
                {'name': 'analytics:read', 'resource': 'analytics', 'action': 'read'}
            ]
        elif role_name == 'admin':
            return [
                {'name': 'venue:manage', 'resource': 'venue', 'action': 'manage'},
                {'name': 'order:manage', 'resource': 'order', 'action': 'manage'},
                {'name': 'menu:manage', 'resource': 'menu', 'action': 'manage'},
                {'name': 'analytics:read', 'resource': 'analytics', 'action': 'read'}
            ]
        else:  # operator
            return [
                {'name': 'order:read', 'resource': 'order', 'action': 'read'},
                {'name': 'order:update', 'resource': 'order', 'action': 'update'},
                {'name': 'table:read', 'resource': 'table', 'action': 'read'},
                {'name': 'table:update', 'resource': 'table', 'action': 'update'}
            ]
    
    def _get_default_dashboard_permissions(self, role_name: str) -> Dict[str, Any]:
        """Get default dashboard permissions without database calls"""
        if role_name == 'superadmin':
            return {
                "role": "superadmin",
                "components": {
                    "dashboard": True,
                    "orders": True,
                    "tables": True,
                    "menu": True,
                    "customers": True,
                    "analytics": True,
                    "settings": True,
                    "user_management": True,
                    "venue_management": True,
                    "workspace_settings": True
                },
                "actions": {
                    "create_venue": True,
                    "switch_venue": True,
                    "create_users": True,
                    "change_passwords": True,
                    "manage_menu": True,
                    "view_analytics": True,
                    "update_order_status": True,
                    "update_table_status": True
                }
            }
        elif role_name == 'admin':
            return {
                "role": "admin",
                "components": {
                    "dashboard": True,
                    "orders": True,
                    "tables": True,
                    "menu": True,
                    "customers": True,
                    "analytics": True,
                    "settings": True,
                    "user_management": False,
                    "venue_management": False,
                    "workspace_settings": False
                },
                "actions": {
                    "create_venue": False,
                    "switch_venue": False,
                    "create_users": True,
                    "change_passwords": True,
                    "manage_menu": True,
                    "view_analytics": True,
                    "update_order_status": True,
                    "update_table_status": True
                }
            }
        else:  # operator
            return {
                "role": "operator",
                "components": {
                    "dashboard": True,
                    "orders": True,
                    "tables": True,
                    "menu": False,
                    "customers": False,
                    "analytics": False,
                    "settings": False,
                    "user_management": False,
                    "venue_management": False,
                    "workspace_settings": False
                },
                "actions": {
                    "create_venue": False,
                    "switch_venue": False,
                    "create_users": False,
                    "change_passwords": False,
                    "manage_menu": False,
                    "view_analytics": False,
                    "update_order_status": True,
                    "update_table_status": True
                }
            }


# Service instance
auth_service = AuthService()