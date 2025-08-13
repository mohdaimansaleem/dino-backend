"""
Enhanced Menu Management API Endpoints
Complete CRUD for menu categories and items with venue isolation and advanced features
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Query

from app.models.schemas import MenuCategory, MenuItem, SpiceLevel
from app.models.dto import (
    MenuCategoryCreateDTO, MenuCategoryUpdateDTO, MenuCategoryResponseDTO,
    MenuItemCreateDTO, MenuItemUpdateDTO, MenuItemResponseDTO,
    ApiResponseDTO, PaginatedResponseDTO
)
# Removed base endpoint dependency
from app.core.base_endpoint import WorkspaceIsolatedEndpoint
from app.core.dependency_injection import get_repository_manager
from app.core.security import get_current_user, get_current_admin_user, require_venue_access
from app.core.logging_config import get_logger
from app.utils.menu_item_utils import ensure_menu_item_fields, process_menu_items_for_response

logger = get_logger(__name__)
router = APIRouter()


class MenuCategoriesEndpoint(WorkspaceIsolatedEndpoint[MenuCategory, MenuCategoryCreateDTO, MenuCategoryUpdateDTO]):
    """Enhanced Menu Categories endpoint with venue isolation"""
    
    def __init__(self):
        super().__init__(
            model_class=MenuCategory,
            create_schema=MenuCategoryCreateDTO,
            update_schema=MenuCategoryUpdateDTO,
            collection_name="menu_categories",
            require_auth=True,
            require_admin=True
        )
    
    def get_repository(self):
        return get_repository_manager().get_repository('menu_category')
    
    async def _prepare_create_data(self, 
                                  data: Dict[str, Any], 
                                  current_user: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare category data before creation"""
        # Set default values
        data['is_active'] = True
        data['image_url'] = None
        
        return data
    
    async def _validate_create_permissions(self, 
                                         data: Dict[str, Any], 
                                         current_user: Optional[Dict[str, Any]]):
        """Validate category creation permissions"""
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Validate venue access
        venue_id = data.get('venue_id')
        if venue_id:
            await self._validate_venue_access(venue_id, current_user)
    
    async def _validate_venue_access(self, venue_id: str, current_user: Dict[str, Any]):
        """Validate user has access to the venue"""
        await require_venue_access(venue_id, current_user)


class MenuItemsEndpoint(WorkspaceIsolatedEndpoint[MenuItem, MenuItemCreateDTO, MenuItemUpdateDTO]):
    """Enhanced Menu Items endpoint with venue isolation"""
    
    def __init__(self):
        super().__init__(
            model_class=MenuItem,
            create_schema=MenuItemCreateDTO,
            update_schema=MenuItemUpdateDTO,
            collection_name="menu_items",
            require_auth=True,
            require_admin=True
        )
    
    def get_repository(self):
        return get_repository_manager().get_repository('menu_item')
    
    async def _prepare_create_data(self, 
                                  data: Dict[str, Any], 
                                  current_user: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare menu item data before creation"""
        # Set default values
        data['image_urls'] = []
        data['is_available'] = True
        data['rating_total'] = 0.0
        data['rating_count'] = 0
        data['average_rating'] = 0.0
        
        return data
    
    async def _validate_create_permissions(self, 
                                         data: Dict[str, Any], 
                                         current_user: Optional[Dict[str, Any]]):
        """Validate menu item creation permissions"""
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Validate venue access
        venue_id = data.get('venue_id')
        if venue_id:
            await self._validate_venue_access(venue_id, current_user)
        
        # Validate category exists and belongs to the same venue
        category_id = data.get('category_id')
        if category_id:
            await self._validate_category_access(category_id, venue_id)
    
    async def _validate_venue_access(self, venue_id: str, current_user: Dict[str, Any]):
        """Validate user has access to the venue"""
        await require_venue_access(venue_id, current_user)
    
    async def _validate_category_access(self, category_id: str, venue_id: str):
        """Validate category belongs to the venue"""
        category_repo = get_repository_manager().get_repository('menu_category')
        
        category = await category_repo.get_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Menu category not found"
            )
        
        if category.get('venue_id') != venue_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category does not belong to the specified venue"
            )
    
    async def search_menu_items(self, 
                              venue_id: str,
                              search_term: str,
                              current_user: Dict[str, Any]) -> List[MenuItem]:
        """Search menu items within a venue"""
        # Validate venue access
        await self._validate_venue_access(venue_id, current_user)
        
        repo = self.get_repository()
        
        # Get all menu items for the venue
        venue_items = await repo.get_by_venue(venue_id)
        
        # Filter by search term
        search_lower = search_term.lower()
        matching_items = []
        
        for item in venue_items:
            if (search_lower in item.get('name', '').lower() or
                search_lower in item.get('description', '').lower()):
                matching_items.append(item)
        
        # Process items to ensure all required fields are present
        processed_items = process_menu_items_for_response(matching_items)
        
        return [MenuItemResponseDTO(**item) for item in processed_items]
    
    async def get_items_by_category(self, 
                                  venue_id: str,
                                  category_id: str,
                                  current_user: Dict[str, Any]) -> List[MenuItem]:
        """Get menu items by category"""
        # Validate venue access
        await self._validate_venue_access(venue_id, current_user)
        
        # Validate category
        await self._validate_category_access(category_id, venue_id)
        
        repo = self.get_repository()
        items_data = await repo.get_by_category(venue_id, category_id)
        
        # Process items to ensure all required fields are present
        processed_items = process_menu_items_for_response(items_data)
        
        return [MenuItemResponseDTO(**item) for item in processed_items]


# Initialize endpoints
categories_endpoint = MenuCategoriesEndpoint()
items_endpoint = MenuItemsEndpoint()


# =============================================================================
# MENU CATEGORIES ENDPOINTS
# =============================================================================

@router.get("/categories", 
            response_model=PaginatedResponseDTO,
            summary="Get menu categories",
            description="Get paginated list of menu categories")
async def get_menu_categories(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    venue_id: Optional[str] = Query(None, description="Filter by venue ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Get menu categories with pagination and filtering"""
    filters = {}
    if venue_id:
        filters['venue_id'] = venue_id
    if is_active is not None:
        filters['is_active'] = is_active
    
    return await categories_endpoint.get_items(
        page=page,
        page_size=page_size,
        filters=filters,
        current_user=current_user
    )


@router.post("/categories", 
             response_model=ApiResponseDTO,
             status_code=status.HTTP_201_CREATED,
             summary="Create menu category",
             description="Create a new menu category")
async def create_menu_category(
    category_data: MenuCategoryCreateDTO,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Create a new menu category"""
    return await categories_endpoint.create_item(category_data, current_user)


@router.get("/categories/{category_id}", 
            response_model=MenuCategoryResponseDTO,
            summary="Get menu category by ID",
            description="Get specific menu category by ID")
async def get_menu_category(
    category_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get menu category by ID"""
    return await categories_endpoint.get_item(category_id, current_user)


@router.put("/categories/{category_id}", 
            response_model=ApiResponseDTO,
            summary="Update menu category",
            description="Update menu category information")
async def update_menu_category(
    category_id: str,
    category_update: MenuCategoryUpdateDTO,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Update menu category information"""
    return await categories_endpoint.update_item(category_id, category_update, current_user)


@router.delete("/categories/{category_id}", 
               response_model=ApiResponseDTO,
               summary="Delete menu category",
               description="Delete menu category permanently")
async def delete_menu_category(
    category_id: str,
    force: bool = Query(False, description="Force delete even if category has menu items"),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Delete menu category permanently"""
    try:
        # Get repositories
        category_repo = get_repository_manager().get_repository('menu_category')
        menu_item_repo = get_repository_manager().get_repository('menu_item')
        
        # Check if category exists
        category = await category_repo.get_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Menu category not found"
            )
        
        # Validate permissions
        await categories_endpoint._validate_access_permissions(category, current_user)
        
        # Check if category has menu items
        items_in_category = await menu_item_repo.query([('category_id', '==', category_id)])
        if items_in_category and not force:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete category: {len(items_in_category)} menu items are assigned to this category. Use force=true to delete anyway or reassign items first."
            )
        
        # If force delete, remove all items in the category first
        if force and items_in_category:
            for item in items_in_category:
                await menu_item_repo.delete(item['id'])
            logger.info(f"Force deleted {len(items_in_category)} menu items in category: {category_id}")
        
        # Delete category from database
        await category_repo.delete(category_id)
        
        logger.info(f"Menu category deleted: {category_id}")
        return ApiResponseDTO(
            success=True,
            message="Menu category deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting menu category: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete menu category"
        )


@router.post("/categories/{category_id}/image", 
             response_model=ApiResponseDTO,
             summary="Upload category image",
             description="Upload image for menu category")
async def upload_category_image(
    category_id: str,
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Upload category image"""
    try:
        # Validate category access
        category = await categories_endpoint.get_item(category_id, current_user)
        
        # TODO: Implement storage service
        # storage_service = get_storage_service()
        # image_url = await storage_service.upload_image(...)
        
        # Mock implementation for now
        image_url = f"https://example.com/categories/{category_id}/image.jpg"
        
        # Update category with image URL
        repo = get_repository_manager().get_repository('menu_category')
        await repo.update(category_id, {"image_url": image_url})
        
        logger.info(f"Image uploaded for category: {category_id}")
        return ApiResponseDTO(
            success=True,
            message="Category image uploaded successfully",
            data={"image_url": image_url}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading category image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image"
        )


# =============================================================================
# MENU ITEMS ENDPOINTS
# =============================================================================

@router.get("/items", 
            response_model=PaginatedResponseDTO,
            summary="Get menu items",
            description="Get paginated list of menu items")
async def get_menu_items(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    venue_id: Optional[str] = Query(None, description="Filter by venue ID"),
    category_id: Optional[str] = Query(None, description="Filter by category ID"),
    is_available: Optional[bool] = Query(None, description="Filter by availability"),
    is_vegetarian: Optional[bool] = Query(None, description="Filter by vegetarian"),
    spice_level: Optional[SpiceLevel] = Query(None, description="Filter by spice level"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get menu items with pagination and filtering"""
    filters = {}
    if venue_id:
        filters['venue_id'] = venue_id
    if category_id:
        filters['category_id'] = category_id
    if is_available is not None:
        filters['is_available'] = is_available
    if is_vegetarian is not None:
        filters['is_vegetarian'] = is_vegetarian
    if spice_level:
        filters['spice_level'] = spice_level.value
    
    return await items_endpoint.get_items(
        page=page,
        page_size=page_size,
        filters=filters,
        current_user=current_user
    )


@router.post("/items", 
             response_model=ApiResponseDTO,
             status_code=status.HTTP_201_CREATED,
             summary="Create menu item",
             description="Create a new menu item")
async def create_menu_item(
    item_data: MenuItemCreateDTO,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Create a new menu item"""
    return await items_endpoint.create_item(item_data, current_user)


@router.get("/items/{item_id}", 
            response_model=MenuItemResponseDTO,
            summary="Get menu item by ID",
            description="Get specific menu item by ID")
async def get_menu_item(
    item_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get menu item by ID"""
    return await items_endpoint.get_item(item_id, current_user)


@router.put("/items/{item_id}", 
            response_model=ApiResponseDTO,
            summary="Update menu item",
            description="Update menu item information")
async def update_menu_item(
    item_id: str,
    item_update: MenuItemUpdateDTO,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Update menu item information"""
    return await items_endpoint.update_item(item_id, item_update, current_user)


@router.delete("/items/{item_id}", 
               response_model=ApiResponseDTO,
               summary="Delete menu item",
               description="Delete menu item permanently from database")
async def delete_menu_item(
    item_id: str,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Delete menu item permanently from database"""
    try:
        # Get repositories
        repo = get_repository_manager().get_repository('menu_item')
        order_repo = get_repository_manager().get_repository('order')
        
        # Check if item exists
        item = await repo.get_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Menu item not found"
            )
        
        # Validate permissions
        await items_endpoint._validate_access_permissions(item, current_user)
        
        # Check if item is used in any orders (safety check)
        orders_with_item = await order_repo.query([('items', 'array-contains-any', [{'menu_item_id': item_id}])])
        if orders_with_item:
            logger.warning(f"Menu item {item_id} is referenced in {len(orders_with_item)} orders but will be deleted")
        
        # Delete item from database
        await repo.delete(item_id)
        
        logger.info(f"Menu item permanently deleted: {item_id}")
        return ApiResponseDTO(
            success=True,
            message="Menu item deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting menu item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete menu item"
        )


@router.post("/items/{item_id}/images", 
             response_model=ApiResponseDTO,
             summary="Upload item images",
             description="Upload images for menu item")
async def upload_item_images(
    item_id: str,
    files: List[UploadFile] = File(...),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Upload menu item images"""
    try:
        # Validate item access
        item = await items_endpoint.get_item(item_id, current_user)
        
        # TODO: Implement storage service
        # storage_service = get_storage_service()
        # uploaded_urls = []
        # for file in files:
        #     image_url = await storage_service.upload_image(...)
        #     uploaded_urls.append(image_url)
        
        # Mock implementation for now
        uploaded_urls = [
            f"https://example.com/items/{item_id}/image_{i}.jpg" 
            for i in range(len(files))
        ]
        
        # Update item with image URLs
        repo = get_repository_manager().get_repository('menu_item')
        current_images = item.image_urls or []
        all_images = current_images + uploaded_urls
        
        await repo.update(item_id, {"image_urls": all_images})
        
        logger.info(f"Images uploaded for menu item: {item_id}")
        return ApiResponseDTO(
            success=True,
            message="Images uploaded successfully",
            data={"image_urls": uploaded_urls}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading item images: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload images"
        )


# =============================================================================
# PUBLIC ENDPOINTS (No Authentication Required)
# =============================================================================

@router.get("/public/validate-qr-access", 
             response_model=Dict[str, Any],
             summary="Validate QR code access",
             description="Validate QR code and return venue/table info if valid for menu access")
async def validate_qr_code_access(qr_code: str = Query(..., description="QR code to validate")):
    """Validate QR code and return venue/table information if valid"""
    try:
        # Import validation service
        from app.services.venue_validation_service import venue_validation_service
        
        # Validate QR code access
        is_valid, validation_data = await venue_validation_service.validate_qr_code_access(qr_code)
        
        if not is_valid:
            # Return specific error for venue not accepting orders
            error_data = validation_data
            if error_data.get('error_type') in ['venue_inactive', 'venue_not_operational']:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={
                        "error": "venue_not_accepting_orders",
                        "message": error_data.get('message', 'Venue is not accepting orders'),
                        "venue_name": error_data.get('venue_name'),
                        "show_error_page": True
                    }
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": error_data.get('error_type', 'validation_failed'),
                        "message": error_data.get('message', 'QR code validation failed')
                    }
                )
        
        logger.info(f"QR code access validated successfully for venue: {validation_data['venue']['id']}")
        return {
            "success": True,
            "message": "QR code access validated successfully",
            "data": validation_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating QR code access: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate QR code access"
        )


@router.get("/public/venues/{venue_id}/menu-with-validation", 
            response_model=Dict[str, Any],
            summary="Get complete menu with validation",
            description="Get venue menu with categories and items after validation")
async def get_public_venue_menu_with_validation(
    venue_id: str,
    table_id: Optional[str] = Query(None, description="Table ID for validation")
):
    """Get complete venue menu (categories and items) after validation"""
    try:
        # Import validation service
        from app.services.venue_validation_service import venue_validation_service
        
        # Validate venue and table before showing menu
        is_valid, validation_data = await venue_validation_service.validate_venue_and_table_for_menu(
            venue_id, table_id
        )
        
        if not is_valid:
            # Return specific error for venue not accepting orders
            error_data = validation_data
            if error_data.get('error_type') in ['venue_inactive', 'venue_not_operational']:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={
                        "error": "venue_not_accepting_orders",
                        "message": error_data.get('message', 'Venue is not accepting orders'),
                        "venue_name": error_data.get('venue_name'),
                        "show_error_page": True
                    }
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error": error_data.get('error_type', 'validation_failed'),
                        "message": error_data.get('message', 'Access validation failed')
                    }
                )
        
        # Get categories
        category_repo = get_repository_manager().get_repository('menu_category')
        categories_data = await category_repo.get_by_venue(venue_id)
        active_categories = [cat for cat in categories_data if cat.get('is_active', False)]
        categories = [MenuCategoryResponseDTO(**cat) for cat in active_categories]
        
        # Get menu items
        item_repo = get_repository_manager().get_repository('menu_item')
        items_data = await item_repo.get_by_venue(venue_id)
        available_items = [item for item in items_data if item.get('is_available', False)]
        
        # Process items to ensure all required fields are present
        processed_items = process_menu_items_for_response(available_items)
        items = []
        for item in processed_items:
            try:
                dto_item = MenuItemResponseDTO(**item)
                items.append(dto_item)
            except Exception as dto_error:
                logger.error(f"Error creating DTO for item {item.get('id', 'unknown')}: {dto_error}")
                continue
        
        # Organize items by category
        items_by_category = {}
        for item in items:
            category_id = item.category_id
            if category_id not in items_by_category:
                items_by_category[category_id] = []
            items_by_category[category_id].append(item)
        
        logger.info(f"Retrieved complete menu for venue: {venue_id} - {len(categories)} categories, {len(items)} items")
        
        return {
            "success": True,
            "venue": validation_data['venue'],
            "table": validation_data['table'],
            "categories": categories,
            "items": items,
            "items_by_category": items_by_category,
            "validation_timestamp": validation_data['validation_timestamp']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting venue menu with validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get menu"
        )

@router.get("/public/venues/{venue_id}/categories", 
            response_model=List[MenuCategoryResponseDTO],
            summary="Get venue categories (public)",
            description="Get all active categories for a specific venue (public endpoint)")
async def get_public_venue_categories(
    venue_id: str,
    table_id: Optional[str] = Query(None, description="Table ID for validation")
):
    """Get all active categories for a venue (public endpoint)"""
    try:
        # Import validation service
        from app.services.venue_validation_service import venue_validation_service
        
        # Validate venue and table before showing menu
        is_valid, validation_data = await venue_validation_service.validate_venue_and_table_for_menu(
            venue_id, table_id
        )
        
        if not is_valid:
            # Return specific error for venue not accepting orders
            error_data = validation_data
            if error_data.get('error_type') in ['venue_inactive', 'venue_not_operational']:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={
                        "error": "venue_not_accepting_orders",
                        "message": error_data.get('message', 'Venue is not accepting orders'),
                        "venue_name": error_data.get('venue_name'),
                        "show_error_page": True
                    }
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error": error_data.get('error_type', 'validation_failed'),
                        "message": error_data.get('message', 'Access validation failed')
                    }
                )
        
        repo = get_repository_manager().get_repository('menu_category')
        categories_data = await repo.get_by_venue(venue_id)
        
        # Filter only active categories for public access
        active_categories = [cat for cat in categories_data if cat.get('is_active', False)]
        
        categories = [MenuCategoryResponseDTO(**cat) for cat in active_categories]
        
        logger.info(f"Retrieved {len(categories)} public categories for venue: {venue_id}")
        return categories
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting public venue categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get categories"
        )


@router.get("/public/venues/{venue_id}/items", 
            response_model=List[MenuItemResponseDTO],
            summary="Get venue menu items (public)",
            description="Get all available menu items for a specific venue (public endpoint)")
async def get_public_venue_menu_items(
    venue_id: str,
    category_id: Optional[str] = None,
    table_id: Optional[str] = Query(None, description="Table ID for validation")
):
    """Get all available menu items for a venue (public endpoint)"""
    try:
        logger.info(f"Getting public menu items for venue: {venue_id}, category: {category_id}, table: {table_id}")
        
        # Import validation service
        from app.services.venue_validation_service import venue_validation_service
        
        # Validate venue and table before showing menu
        is_valid, validation_data = await venue_validation_service.validate_venue_and_table_for_menu(
            venue_id, table_id
        )
        
        if not is_valid:
            # Return specific error for venue not accepting orders
            error_data = validation_data
            if error_data.get('error_type') in ['venue_inactive', 'venue_not_operational']:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={
                        "error": "venue_not_accepting_orders",
                        "message": error_data.get('message', 'Venue is not accepting orders'),
                        "venue_name": error_data.get('venue_name'),
                        "show_error_page": True
                    }
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error": error_data.get('error_type', 'validation_failed'),
                        "message": error_data.get('message', 'Access validation failed')
                    }
                )
        
        repo = get_repository_manager().get_repository('menu_item')
        
        if category_id and category_id != "None":
            # Get items by category
            logger.debug(f"Getting items by category: {category_id}")
            items_data = await repo.get_by_category(venue_id, category_id)
        else:
            # Get all items for venue
            logger.debug(f"Getting all items for venue: {venue_id}")
            items_data = await repo.get_by_venue(venue_id)
        
        logger.debug(f"Retrieved {len(items_data)} raw items from database")
        
        # Filter only available items for public access
        available_items = [item for item in items_data if item.get('is_available', False)]
        logger.debug(f"Filtered to {len(available_items)} available items")
        
        # Process items to ensure all required fields are present
        try:
            processed_items = process_menu_items_for_response(available_items)
            logger.debug(f"Successfully processed {len(processed_items)} items")
        except Exception as process_error:
            logger.error(f"Error processing menu items: {process_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing menu items: {str(process_error)}"
            )
        
        # Create DTO objects
        try:
            items = []
            for i, item in enumerate(processed_items):
                try:
                    dto_item = MenuItemResponseDTO(**item)
                    items.append(dto_item)
                except Exception as dto_error:
                    logger.error(f"Error creating DTO for item {i} (id: {item.get('id', 'unknown')}): {dto_error}")
                    logger.error(f"Item data: {item}")
                    # Skip this item and continue with others
                    continue
            
            logger.info(f"Successfully created {len(items)} DTO objects from {len(processed_items)} processed items")
        except Exception as dto_error:
            logger.error(f"Error creating MenuItemResponseDTO objects: {dto_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating response objects: {str(dto_error)}"
            )
        
        logger.info(f"Retrieved {len(items)} public menu items for venue: {venue_id}")
        return items
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting public venue menu items: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get menu items: {str(e)}"
        )


# =============================================================================
# SEARCH AND FILTER ENDPOINTS
# =============================================================================

@router.get("/venues/{venue_id}/categories", 
            response_model=List[MenuCategoryResponseDTO],
            summary="Get venue categories",
            description="Get all categories for a specific venue")
async def get_venue_categories(
    venue_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all categories for a venue"""
    try:
        # Validate venue access
        await categories_endpoint._validate_venue_access(venue_id, current_user)
        
        repo = get_repository_manager().get_repository('menu_category')
        categories_data = await repo.get_by_venue(venue_id)
        
        # Filter active categories for non-admin users
        if current_user.get('role') != 'admin':
            categories_data = [cat for cat in categories_data if cat.get('is_active', False)]
        
        categories = [MenuCategoryResponseDTO(**cat) for cat in categories_data]
        
        logger.info(f"Retrieved {len(categories)} categories for venue: {venue_id}")
        return categories
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting venue categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get categories"
        )


@router.get("/venues/{venue_id}/items", 
            response_model=List[MenuItemResponseDTO],
            summary="Get venue menu items",
            description="Get all menu items for a specific venue")
async def get_venue_menu_items(
    venue_id: str,
    category_id: Optional[str] = Query(None, description="Filter by category"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all menu items for a venue"""
    try:
        if category_id:
            # Get items by category
            items = await items_endpoint.get_items_by_category(venue_id, category_id, current_user)
        else:
            # Validate venue access
            await items_endpoint._validate_venue_access(venue_id, current_user)
            
            repo = get_repository_manager().get_repository('menu_item')
            items_data = await repo.get_by_venue(venue_id)
            
            # Filter available items for non-admin users
            if current_user.get('role') != 'admin':
                items_data = [item for item in items_data if item.get('is_available', False)]
            
            # Process items to ensure all required fields are present
            processed_items = process_menu_items_for_response(items_data)
            
            items = [MenuItemResponseDTO(**item) for item in processed_items]
        
        logger.info(f"Retrieved {len(items)} menu items for venue: {venue_id}")
        return items
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting venue menu items: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get menu items"
        )


@router.get("/venues/{venue_id}/search", 
            response_model=List[MenuItemResponseDTO],
            summary="Search menu items",
            description="Search menu items within a venue")
async def search_venue_menu_items(
    venue_id: str,
    q: str = Query(..., min_length=2, description="Search query"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Search menu items within a venue"""
    try:
        items = await items_endpoint.search_menu_items(venue_id, q, current_user)
        
        logger.info(f"Menu search performed in venue {venue_id}: '{q}' - {len(items)} results")
        return items
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching menu items: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )


# =============================================================================
# BULK OPERATIONS ENDPOINTS
# =============================================================================

@router.post("/items/bulk-update-availability", 
             response_model=ApiResponseDTO,
             summary="Bulk update item availability",
             description="Update availability for multiple menu items")
async def bulk_update_item_availability(
    item_ids: List[str],
    is_available: bool,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Bulk update menu item availability"""
    try:
        repo = get_repository_manager().get_repository('menu_item')
        
        # Validate all items exist and user has access
        for item_id in item_ids:
            item = await repo.get_by_id(item_id)
            if not item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Menu item {item_id} not found"
                )
            
            await items_endpoint._validate_access_permissions(item, current_user)
        
        # Bulk update
        updates = [(item_id, {"is_available": is_available}) for item_id in item_ids]
        await repo.update_batch(updates)
        
        logger.info(f"Bulk updated availability for {len(item_ids)} items")
        return ApiResponseDTO(
            success=True,
            message=f"Updated availability for {len(item_ids)} items"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error bulk updating item availability: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update items"
        )


@router.post("/categories/{category_id}/items/toggle-availability", 
             response_model=ApiResponseDTO,
             summary="Toggle category items availability",
             description="Toggle availability for all items in a category")
async def toggle_category_items_availability(
    category_id: str,
    is_available: bool,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Toggle availability for all items in a category"""
    try:
        # Validate category access
        category = await categories_endpoint.get_item(category_id, current_user)
        
        # Get all items in category
        repo = get_repository_manager().get_repository('menu_item')
        items_data = await repo.query([('category_id', '==', category_id)])
        
        # Bulk update
        updates = [(item['id'], {"is_available": is_available}) for item in items_data]
        await repo.update_batch(updates)
        
        logger.info(f"Toggled availability for {len(items_data)} items in category: {category_id}")
        return ApiResponseDTO(
            success=True,
            message=f"Updated availability for {len(items_data)} items in category"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling category items availability: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update category items"
        )