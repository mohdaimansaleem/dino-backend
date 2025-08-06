"""
Generic Utilities for API Endpoints
Provides reusable functions to eliminate code duplication
"""
from typing import Dict, Any, Optional, List, Callable, TypeVar, Generic
from fastapi import HTTPException, status
from app.core.security import _get_user_role
from app.core.logging_config import get_logger
from app.models.dto import ApiResponseDTO

logger = get_logger(__name__)

T = TypeVar('T')

# =============================================================================
# PERMISSION VALIDATION UTILITIES
# =============================================================================

async def validate_user_role(
    current_user: Dict[str, Any], 
    required_roles: List[str],
    error_message: str = "Insufficient permissions"
) -> str:
    """
    Generic role validation utility
    
    Args:
        current_user: Current user data
        required_roles: List of roles that are allowed
        error_message: Custom error message
        
    Returns:
        str: User's role
        
    Raises:
        HTTPException: If user doesn't have required role
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    user_role = await _get_user_role(current_user)
    
    if user_role not in required_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_message
        )
    
    return user_role


async def validate_superadmin_only(current_user: Dict[str, Any]) -> str:
    """Validate that user is superadmin"""
    return await validate_user_role(
        current_user, 
        ["superadmin"], 
        "Only superadmin can perform this action"
    )


async def validate_admin_or_superadmin(current_user: Dict[str, Any]) -> str:
    """Validate that user is admin or superadmin"""
    return await validate_user_role(
        current_user, 
        ["admin", "superadmin"], 
        "Admin or superadmin role required"
    )


async def validate_resource_ownership(
    current_user: Dict[str, Any],
    resource: Dict[str, Any],
    owner_field: str = "admin_id",
    allow_superadmin: bool = True
) -> bool:
    """
    Validate that user owns the resource or is superadmin
    
    Args:
        current_user: Current user data
        resource: Resource to check ownership
        owner_field: Field name that contains owner ID
        allow_superadmin: Whether superadmin can access any resource
        
    Returns:
        bool: True if user has access
        
    Raises:
        HTTPException: If user doesn't have access
    """
    user_role = await _get_user_role(current_user)
    
    # Superadmin can access everything
    if allow_superadmin and user_role == "superadmin":
        return True
    
    # Check ownership
    if resource.get(owner_field) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You don't own this resource"
        )
    
    return True


# =============================================================================
# ERROR HANDLING UTILITIES
# =============================================================================

def handle_endpoint_errors(operation_name: str):
    """
    Decorator for consistent error handling in endpoints
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error in {operation_name}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"{operation_name} failed"
                )
        return wrapper
    return decorator


async def safe_get_resource(
    repo: Any,
    resource_id: str,
    resource_name: str = "Resource"
) -> Dict[str, Any]:
    """
    Safely get a resource by ID with consistent error handling
    
    Args:
        repo: Repository instance
        resource_id: ID of resource to get
        resource_name: Name of resource for error messages
        
    Returns:
        Dict[str, Any]: Resource data
        
    Raises:
        HTTPException: If resource not found
    """
    resource = await repo.get_by_id(resource_id)
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_name} not found"
        )
    return resource


# =============================================================================
# ACTIVATION/DEACTIVATION UTILITIES
# =============================================================================

async def generic_activate_resource(
    repo: Any,
    resource_id: str,
    current_user: Dict[str, Any],
    resource_name: str = "Resource",
    validation_func: Optional[Callable] = None
) -> ApiResponseDTO:
    """
    Generic activation utility for any resource
    
    Args:
        repo: Repository instance
        resource_id: ID of resource to activate
        current_user: Current user data
        resource_name: Name of resource for messages
        validation_func: Optional validation function
        
    Returns:
        ApiResponseDTO: Success response
    """
    # Get resource
    resource = await safe_get_resource(repo, resource_id, resource_name)
    
    # Validate permissions if function provided
    if validation_func:
        await validation_func(resource, current_user)
    
    # Activate resource
    await repo.update(resource_id, {"is_active": True})
    
    logger.info(f"{resource_name} activated: {resource_id}")
    return ApiResponseDTO(
        success=True,
        message=f"{resource_name} activated successfully"
    )


async def generic_deactivate_resource(
    repo: Any,
    resource_id: str,
    current_user: Dict[str, Any],
    resource_name: str = "Resource",
    validation_func: Optional[Callable] = None
) -> ApiResponseDTO:
    """
    Generic deactivation utility for any resource
    
    Args:
        repo: Repository instance
        resource_id: ID of resource to deactivate
        current_user: Current user data
        resource_name: Name of resource for messages
        validation_func: Optional validation function
        
    Returns:
        ApiResponseDTO: Success response
    """
    # Get resource
    resource = await safe_get_resource(repo, resource_id, resource_name)
    
    # Validate permissions if function provided
    if validation_func:
        await validation_func(resource, current_user)
    
    # Deactivate resource
    await repo.update(resource_id, {"is_active": False})
    
    logger.info(f"{resource_name} deactivated: {resource_id}")
    return ApiResponseDTO(
        success=True,
        message=f"{resource_name} deactivated successfully"
    )


# =============================================================================
# SEARCH AND FILTERING UTILITIES
# =============================================================================

def build_filters_from_params(
    filters_dict: Optional[Dict[str, Any]] = None,
    **additional_filters
) -> List[tuple]:
    """
    Build query filters from parameters
    
    Args:
        filters_dict: Dictionary of filters
        **additional_filters: Additional filters as keyword arguments
        
    Returns:
        List[tuple]: List of filter tuples for repository queries
    """
    query_filters = []
    
    # Add filters from dict
    if filters_dict:
        for field, value in filters_dict.items():
            if value is not None:
                query_filters.append((field, '==', value))
    
    # Add additional filters
    for field, value in additional_filters.items():
        if value is not None:
            query_filters.append((field, '==', value))
    
    return query_filters


async def generic_search_by_text(
    repo: Any,
    search_fields: List[str],
    search_term: str,
    additional_filters: Optional[List[tuple]] = None,
    limit: int = 50,
    dto_class: Optional[type] = None
) -> List[Any]:
    """
    Generic text search utility
    
    Args:
        repo: Repository instance
        search_fields: Fields to search in
        search_term: Search term
        additional_filters: Additional query filters
        limit: Maximum results
        dto_class: DTO class to convert results to
        
    Returns:
        List[Any]: Search results
    """
    matching_items = await repo.search_text(
        search_fields=search_fields,
        search_term=search_term,
        additional_filters=additional_filters or [],
        limit=limit
    )
    
    if dto_class:
        return [dto_class(**item) for item in matching_items]
    
    return matching_items


# =============================================================================
# VALIDATION UTILITIES
# =============================================================================

async def validate_unique_field(
    repo: Any,
    field_name: str,
    field_value: str,
    exclude_id: Optional[str] = None,
    error_message: Optional[str] = None
) -> None:
    """
    Validate that a field value is unique
    
    Args:
        repo: Repository instance
        field_name: Name of field to check
        field_value: Value to check for uniqueness
        exclude_id: ID to exclude from check (for updates)
        error_message: Custom error message
        
    Raises:
        HTTPException: If field value is not unique
    """
    # Get method name dynamically
    get_method = getattr(repo, f"get_by_{field_name}", None)
    if not get_method:
        return  # Skip validation if method doesn't exist
    
    existing_item = await get_method(field_value)
    
    if existing_item and (not exclude_id or existing_item.get('id') != exclude_id):
        error_msg = error_message or f"{field_name.replace('_', ' ').title()} already exists"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )


# =============================================================================
# RESPONSE UTILITIES
# =============================================================================

def create_success_response(
    message: str,
    data: Optional[Any] = None
) -> ApiResponseDTO:
    """Create a standardized success response"""
    return ApiResponseDTO(
        success=True,
        message=message,
        data=data
    )


def log_operation_success(operation: str, resource_id: str, user_id: str) -> None:
    """Log successful operations consistently"""
    logger.info(f"{operation} successful: {resource_id} by user {user_id}")


# =============================================================================
# PAGINATION UTILITIES
# =============================================================================

def calculate_pagination_metadata(
    total: int,
    page: int,
    page_size: int
) -> Dict[str, Any]:
    """
    Calculate pagination metadata
    
    Args:
        total: Total number of items
        page: Current page number
        page_size: Items per page
        
    Returns:
        Dict[str, Any]: Pagination metadata
    """
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }


def apply_pagination(
    items: List[Any],
    page: int,
    page_size: int
) -> tuple[List[Any], Dict[str, Any]]:
    """
    Apply pagination to a list of items
    
    Args:
        items: List of items to paginate
        page: Current page number
        page_size: Items per page
        
    Returns:
        tuple: (paginated_items, pagination_metadata)
    """
    total = len(items)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    paginated_items = items[start_idx:end_idx]
    metadata = calculate_pagination_metadata(total, page, page_size)
    
    return paginated_items, metadata


# =============================================================================
# ENHANCED AUTHENTICATION AND AUTHORIZATION UTILITIES
# =============================================================================

async def get_user_role_cached(current_user: Dict[str, Any]) -> str:
    """Get user role with caching to avoid repeated database calls"""
    # Check if role is already cached in user object
    if 'role' in current_user:
        return current_user['role']
    
    # Get role from role_id
    role_id = current_user.get('role_id')
    if not role_id:
        return 'operator'
    
    try:
        from app.database.firestore import get_role_repo
        role_repo = get_role_repo()
        role = await role_repo.get_by_id(role_id)
        
        if role:
            role_name = role.get('name', 'operator')
            # Cache in user object for future use
            current_user['role'] = role_name
            return role_name
    except Exception as e:
        logger.warning(f"Failed to get user role: {e}")
    
    return 'operator'


async def validate_user_permissions(
    current_user: Dict[str, Any],
    required_permissions: List[str],
    resource_id: Optional[str] = None,
    resource_type: Optional[str] = None
) -> bool:
    """
    Comprehensive permission validation
    
    Args:
        current_user: Current user data
        required_permissions: List of required permissions
        resource_id: Optional resource ID for ownership checks
        resource_type: Optional resource type for specific validation
        
    Returns:
        bool: True if user has permissions
        
    Raises:
        HTTPException: If permissions are insufficient
    """
    user_role = await get_user_role_cached(current_user)
    
    # Superadmin has all permissions
    if user_role == 'superadmin':
        return True
    
    # Check specific permissions based on role
    role_permissions = {
        'admin': [
            'venue:manage', 'menu:manage', 'order:manage', 'table:manage',
            'user:read', 'user:create', 'analytics:read'
        ],
        'operator': [
            'order:read', 'order:update', 'table:read', 'table:update'
        ]
    }
    
    user_permissions = role_permissions.get(user_role, [])
    
    # Check if user has any of the required permissions
    has_permission = any(perm in user_permissions for perm in required_permissions)
    
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required: {', '.join(required_permissions)}"
        )
    
    return True


async def validate_resource_access(
    current_user: Dict[str, Any],
    resource: Dict[str, Any],
    access_type: str = "read"
) -> bool:
    """
    Validate user access to a specific resource
    
    Args:
        current_user: Current user data
        resource: Resource to check access for
        access_type: Type of access (read, write, delete)
        
    Returns:
        bool: True if access is allowed
        
    Raises:
        HTTPException: If access is denied
    """
    user_role = await get_user_role_cached(current_user)
    
    # Superadmin has access to everything
    if user_role == 'superadmin':
        return True
    
    # Check ownership for admin/operator roles
    if user_role in ['admin', 'operator']:
        # Check if user owns the resource
        owner_fields = ['admin_id', 'owner_id', 'user_id']
        for field in owner_fields:
            if resource.get(field) == current_user['id']:
                return True
        
        # Check venue access for venue-specific resources
        resource_venue_id = resource.get('venue_id')
        user_venue_ids = current_user.get('venue_ids', [])
        
        if resource_venue_id and resource_venue_id in user_venue_ids:
            return True
    
    # If no access found, deny
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied to this resource"
    )


# =============================================================================
# CONSOLIDATED ERROR HANDLING
# =============================================================================

class StandardErrorHandler:
    """Centralized error handling for consistent responses"""
    
    @staticmethod
    def handle_not_found(resource_name: str, resource_id: str = None) -> HTTPException:
        """Standard not found error"""
        detail = f"{resource_name} not found"
        if resource_id:
            detail += f" (ID: {resource_id})"
        
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )
    
    @staticmethod
    def handle_validation_error(errors: List[str]) -> HTTPException:
        """Standard validation error"""
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation failed: {'; '.join(errors)}"
        )
    
    @staticmethod
    def handle_permission_error(action: str = None) -> HTTPException:
        """Standard permission error"""
        detail = "Insufficient permissions"
        if action:
            detail += f" for {action}"
        
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )
    
    @staticmethod
    def handle_server_error(operation: str, error: Exception = None) -> HTTPException:
        """Standard server error"""
        logger.error(f"Server error in {operation}: {error}")
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{operation} failed"
        )


# =============================================================================
# CONSOLIDATED CRUD OPERATIONS
# =============================================================================

async def generic_create_resource(
    repo: Any,
    data: Dict[str, Any],
    current_user: Dict[str, Any],
    resource_name: str,
    validation_func: Optional[Callable] = None,
    prepare_func: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    Generic resource creation with validation and preparation
    
    Args:
        repo: Repository instance
        data: Data to create
        current_user: Current user
        resource_name: Name of resource for logging
        validation_func: Optional validation function
        prepare_func: Optional data preparation function
        
    Returns:
        Dict[str, Any]: Created resource
    """
    try:
        # Validate permissions if function provided
        if validation_func:
            await validation_func(data, current_user)
        
        # Prepare data if function provided
        if prepare_func:
            data = await prepare_func(data, current_user)
        
        # Create resource
        created_resource = await repo.create(data)
        
        logger.info(f"{resource_name} created: {created_resource.get('id')} by user {current_user['id']}")
        return created_resource
        
    except HTTPException:
        raise
    except Exception as e:
        raise StandardErrorHandler.handle_server_error(f"{resource_name} creation", e)


async def generic_update_resource(
    repo: Any,
    resource_id: str,
    update_data: Dict[str, Any],
    current_user: Dict[str, Any],
    resource_name: str,
    validation_func: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    Generic resource update with validation
    
    Args:
        repo: Repository instance
        resource_id: ID of resource to update
        update_data: Data to update
        current_user: Current user
        resource_name: Name of resource for logging
        validation_func: Optional validation function
        
    Returns:
        Dict[str, Any]: Updated resource
    """
    try:
        # Get existing resource
        resource = await safe_get_resource(repo, resource_id, resource_name)
        
        # Validate access
        await validate_resource_access(current_user, resource, "write")
        
        # Additional validation if function provided
        if validation_func:
            await validation_func(resource, current_user)
        
        # Update resource
        updated_resource = await repo.update(resource_id, update_data)
        
        logger.info(f"{resource_name} updated: {resource_id} by user {current_user['id']}")
        return updated_resource
        
    except HTTPException:
        raise
    except Exception as e:
        raise StandardErrorHandler.handle_server_error(f"{resource_name} update", e)


def create_error_response(
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> ApiResponseDTO:
    """Create a standardized error response"""
    return ApiResponseDTO(
        success=False,
        message=message,
        data={
            "error_code": error_code,
            "details": details
        } if error_code or details else None
    )