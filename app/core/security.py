"""
Security utilities for authentication and authorization with venue-based data isolation
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Import unified password security
from app.core.unified_password_security import (
    verify_password as secure_verify_password,
    get_password_hash as secure_get_password_hash,
    login_tracker,
    sanitize_error_message,
    password_handler
)

# JWT token security
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash with enhanced security"""
    return secure_verify_password(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate secure password hash with validation"""
    return secure_get_password_hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token with enhanced security"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add security claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),  # Issued at
        "nbf": datetime.utcnow(),  # Not before
        "iss": "dino-api",         # Issuer
        "aud": "dino-client"       # Audience
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode JWT token with enhanced security"""
    try:
        # Verify token with audience and issuer validation
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM],
            audience="dino-client",
            issuer="dino-api"
        )
        
        # Additional security checks
        if not payload.get("sub"):
            raise JWTError("Missing subject claim")
        
        return payload
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=sanitize_error_message("Could not validate credentials"),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Get current user ID from JWT token"""
    # Check if JWT auth is disabled (development mode)
    if not settings.is_jwt_auth_enabled:
        logger.info("JWT authentication disabled - using development user")
        return settings.DEV_USER_ID
    
    token = credentials.credentials
    payload = verify_token(token)
    user_id: str = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Get current authenticated user with enhanced validation
    Supports both JWT authentication and development mode
    """
    try:
        # Check if JWT auth is disabled (development mode)
        if not settings.is_jwt_auth_enabled:
            logger.info("JWT authentication disabled - using development user")
            return await get_development_user()
        
        token = credentials.credentials
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        from app.database.firestore import get_user_repo
        user_repo = get_user_repo()
        user = await user_repo.get_by_id(user_id)
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not user.get('is_active', True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is deactivated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Role is now directly stored in user document
        if 'role' not in user:
            user['role'] = 'operator'
        
        # Remove sensitive information
        user.pop('hashed_password', None)
        
        return user
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current user with admin privileges"""
    user_role = current_user.get('role', 'operator')
    
    if user_role not in ['admin', 'superadmin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user


async def get_current_superadmin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current user with superadmin privileges"""
    user_role = current_user.get('role', 'operator')
    
    if user_role != 'superadmin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin privileges required"
        )
    
    return current_user


async def validate_venue_access(user: Dict[str, Any], venue_id: str) -> bool:
    """
    Validate if user has access to specific venue
    Implements strict venue-based data isolation
    """
    try:
        user_role = user.get('role', 'operator')
        
        # SuperAdmin has access to all venues (for system management only)
        if user_role == 'superadmin':
            return True
        
        # Get user's assigned venues from venue_ids list
        user_venue_ids = user.get('venue_ids', [])
        
        # Check if user has access to this venue
        if venue_id in user_venue_ids:
            return True
        
        # No workspace-level access in new hierarchy
        # Users must be explicitly assigned to venues
        
        return False
        
    except Exception as e:
        logger.error(f"Error validating venue access: {e}")
        return False


async def require_venue_access(venue_id: str, current_user: Dict[str, Any]) -> None:
    """
    Require venue access for the current user
    Raises HTTPException if access is denied
    """
    has_access = await validate_venue_access(current_user, venue_id)
    
    if not has_access:
        logger.warning(f"Venue access denied for user {current_user.get('id')} to venue {venue_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You don't have permission to access this venue"
        )


async def get_user_accessible_venues(user: Dict[str, Any]) -> List[str]:
    """Get list of venue IDs user has access to"""
    try:
        user_role = user.get('role', 'operator')
        
        # SuperAdmin gets all venues (for system management)
        if user_role == 'superadmin':
            from app.database.firestore import get_venue_repo
            venue_repo = get_venue_repo()
            all_venues = await venue_repo.get_all()
            return [venue['id'] for venue in all_venues if venue.get('is_active', True)]
        
        # Get user's assigned venues from venue_ids list
        user_venue_ids = user.get('venue_ids', [])
        return user_venue_ids
        
    except Exception as e:
        logger.error(f"Error getting accessible venues: {e}")
        return []


async def get_user_primary_venue(current_user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get user's primary venue (first venue in their venue_ids list)"""
    try:
        # Get user's venue IDs
        user_venue_ids = current_user.get('venue_ids', [])
        
        if not user_venue_ids:
            return None
        
        # Get first venue as primary
        primary_venue_id = user_venue_ids[0]
        
        # Get venue details
        from app.database.firestore import get_venue_repo
        venue_repo = get_venue_repo()
        venue = await venue_repo.get_by_id(primary_venue_id)
        
        return venue
        
    except Exception as e:
        logger.error(f"Error getting user primary venue: {e}")
        return None


async def _get_user_role(user_data: Dict[str, Any]) -> str:
    """Get user role from role_id"""
    role_id = user_data.get("role_id")
    if not role_id:
        return "operator"  # Default role
    
    try:
        from app.database.firestore import get_role_repo
        role_repo = get_role_repo()
        role = await role_repo.get_by_id(role_id)
        
        if role:
            return role.get("name", "operator")
    except Exception as e:
        logger.warning(f"Failed to get user role: {e}")
    
    return "operator"


async def get_development_user() -> Dict[str, Any]:
    """
    Get development user when JWT authentication is disabled
    """
    try:
        # Try to get the development user from database first
        from app.database.firestore import get_user_repo
        user_repo = get_user_repo()
        user = await user_repo.get_by_id(settings.DEV_USER_ID)
        
        if user:
            logger.info(f"Using existing development user: {user.get('email')}")
            # Remove sensitive information
            user.pop('hashed_password', None)
            return user
        
        # If development user doesn't exist, create a mock user
        logger.info("Creating mock development user")
        mock_user = {
            "id": settings.DEV_USER_ID,
            "email": settings.DEV_USER_EMAIL,
            "first_name": "Development",
            "last_name": "User",
            "role": settings.DEV_USER_ROLE,
            "is_active": True,
            "venue_ids": [],  # SuperAdmin has access to all venues
            "workspace_id": "dev-workspace",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        return mock_user
        
    except Exception as e:
        logger.error(f"Error getting development user: {e}")
        # Return basic mock user as fallback
        return {
            "id": settings.DEV_USER_ID,
            "email": settings.DEV_USER_EMAIL,
            "first_name": "Development",
            "last_name": "User",
            "role": settings.DEV_USER_ROLE,
            "is_active": True,
            "venue_ids": [],
            "workspace_id": "dev-workspace",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }


async def get_optional_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """
    Get current user optionally (for public endpoints that can work with or without auth)
    """
    try:
        # Check if JWT auth is disabled
        if not settings.is_jwt_auth_enabled:
            return await get_development_user()
        
        # Try to get authorization header
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return None
        
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        # Get user from database
        from app.database.firestore import get_user_repo
        user_repo = get_user_repo()
        user = await user_repo.get_by_id(user_id)
        
        if user and user.get('is_active', True):
            user.pop('hashed_password', None)
            return user
        
        return None
        
    except Exception as e:
        logger.debug(f"Optional auth failed: {e}")
        return None


def verify_cafe_ownership(cafe_owner_id: str, current_user_id: str) -> bool:
    """Verify if current user owns the cafe"""
    return cafe_owner_id == current_user_id


async def verify_venue_access(venue_id: str, current_user: Dict[str, Any]) -> bool:
    """Verify if current user has access to venue (legacy function)"""
    return await validate_venue_access(current_user, venue_id)


async def verify_workspace_access(workspace_id: str, current_user: Dict[str, Any]) -> bool:
    """Verify if current user has access to workspace"""
    from app.database.firestore import get_workspace_repo
    
    workspace_repo = get_workspace_repo()
    workspace = await workspace_repo.get_by_id(workspace_id)
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    # Get user role
    user_role = await _get_user_role(current_user)
    
    # SuperAdmin can access all workspaces
    if user_role == "superadmin":
        return True
    
    # Admin and operator roles have limited workspace access
    if user_role in ["admin", "operator"]:
        return True
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not enough permissions to access this workspace"
    )