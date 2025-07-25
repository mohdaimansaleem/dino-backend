"""
Menu Management API Endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from typing import List, Dict, Any, Optional
import os
import uuid

from app.models.schemas import (
    MenuItemCreate, MenuItemUpdate, MenuItem, 
    MenuCategoryCreate, MenuCategoryUpdate, MenuCategory,
    ApiResponse
)
from app.database.firestore import get_menu_item_repo, get_menu_category_repo, get_cafe_repo
from app.core.security import get_current_user, get_current_admin_user, verify_cafe_access
from app.core.config import settings


router = APIRouter()


async def save_menu_item_image(file: UploadFile) -> str:
    """Save uploaded menu item image (mock implementation)"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # TODO: Implement actual file upload to Cloud Storage
    # For now, return a mock URL
    filename = f"{uuid.uuid4()}.jpg"
    return f"https://example.com/menu_items/{filename}"


# Menu Categories Endpoints
@router.post("/categories", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_menu_category(
    category_data: MenuCategoryCreate,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Create a new menu category"""
    try:
        # Verify cafe ownership
        await verify_cafe_access(category_data.cafe_id, current_user)
        
        # Create category
        category_dict = category_data.dict()
        category_id = await get_menu_category_repo().create(category_dict)
        
        # Get created category
        category = await get_menu_category_repo().get_by_id(category_id)
        
        return ApiResponse(
            success=True,
            message="Menu category created successfully",
            data=category
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create menu category: {str(e)}"
        )


@router.get("/categories/{cafe_id}", response_model=List[MenuCategory])
async def get_menu_categories(cafe_id: str):
    """Get menu categories for a cafe (public endpoint)"""
    try:
        categories = await get_menu_category_repo().get_by_cafe(cafe_id)
        return [MenuCategory(**category) for category in categories]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get menu categories: {str(e)}"
        )


@router.put("/categories/{category_id}", response_model=ApiResponse)
async def update_menu_category(
    category_id: str,
    category_update: MenuCategoryUpdate,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Update menu category"""
    try:
        # Get category to verify ownership
        category = await get_menu_category_repo().get_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Menu category not found"
            )
        
        # Verify cafe ownership
        await verify_cafe_access(category["cafe_id"], current_user)
        
        # Update category
        update_data = category_update.dict(exclude_unset=True)
        await get_menu_category_repo().update(category_id, update_data)
        
        # Get updated category
        updated_category = await get_menu_category_repo().get_by_id(category_id)
        
        return ApiResponse(
            success=True,
            message="Menu category updated successfully",
            data=updated_category
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update menu category: {str(e)}"
        )


@router.delete("/categories/{category_id}", response_model=ApiResponse)
async def delete_menu_category(
    category_id: str,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Delete menu category"""
    try:
        # Get category to verify ownership
        category = await get_menu_category_repo().get_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Menu category not found"
            )
        
        # Verify cafe ownership
        await verify_cafe_access(category["cafe_id"], current_user)
        
        # Check if category has menu items
        items = await get_menu_item_repo().get_by_category(category["cafe_id"], category["name"])
        if items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete category with existing menu items"
            )
        
        # Delete category
        await get_menu_category_repo().delete(category_id)
        
        return ApiResponse(
            success=True,
            message="Menu category deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete menu category: {str(e)}"
        )


# Menu Items Endpoints
@router.post("/items", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_menu_item(
    item_data: MenuItemCreate,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Create a new menu item"""
    try:
        # Verify cafe ownership
        await verify_cafe_access(item_data.cafe_id, current_user)
        
        # Create menu item
        item_dict = item_data.dict()
        item_id = await get_menu_item_repo().create(item_dict)
        
        # Get created item
        item = await get_menu_item_repo().get_by_id(item_id)
        
        return ApiResponse(
            success=True,
            message="Menu item created successfully",
            data=item
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create menu item: {str(e)}"
        )


@router.get("/items/{cafe_id}", response_model=List[MenuItem])
async def get_menu_items(
    cafe_id: str,
    category: Optional[str] = None,
    is_veg: Optional[bool] = None,
    available_only: bool = True
):
    """Get menu items for a cafe (public endpoint)"""
    try:
        if category:
            items = await get_menu_item_repo().get_by_category(cafe_id, category)
        else:
            items = await get_menu_item_repo().get_by_cafe(cafe_id)
        
        # Apply filters
        if is_veg is not None:
            items = [item for item in items if item.get("is_vegetarian") == is_veg]
        
        if available_only:
            items = [item for item in items if item.get("is_available", True)]
        
        return [MenuItem(**item) for item in items]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get menu items: {str(e)}"
        )


@router.get("/items/detail/{item_id}", response_model=MenuItem)
async def get_menu_item(item_id: str):
    """Get menu item by ID (public endpoint)"""
    try:
        item = await get_menu_item_repo().get_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Menu item not found"
            )
        
        return MenuItem(**item)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get menu item: {str(e)}"
        )


@router.put("/items/{item_id}", response_model=ApiResponse)
async def update_menu_item(
    item_id: str,
    item_update: MenuItemUpdate,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Update menu item"""
    try:
        # Get item to verify ownership
        item = await get_menu_item_repo().get_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Menu item not found"
            )
        
        # Verify cafe ownership
        await verify_cafe_access(item["cafe_id"], current_user)
        
        # Update item
        update_data = item_update.dict(exclude_unset=True)
        await get_menu_item_repo().update(item_id, update_data)
        
        # Get updated item
        updated_item = await get_menu_item_repo().get_by_id(item_id)
        
        return ApiResponse(
            success=True,
            message="Menu item updated successfully",
            data=updated_item
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update menu item: {str(e)}"
        )


@router.post("/items/{item_id}/image", response_model=ApiResponse)
async def upload_menu_item_image(
    item_id: str,
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Upload menu item image"""
    try:
        # Get item to verify ownership
        item = await get_menu_item_repo().get_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Menu item not found"
            )
        
        # Verify cafe ownership
        await verify_cafe_access(item["cafe_id"], current_user)
        
        # Save uploaded image
        image_url = await save_menu_item_image(file)
        
        # Update item with image URL
        await get_menu_item_repo().update(item_id, {"image_urls": [image_url]})
        
        return ApiResponse(
            success=True,
            message="Image uploaded successfully",
            data={"image_url": image_url}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {str(e)}"
        )


@router.delete("/items/{item_id}", response_model=ApiResponse)
async def delete_menu_item(
    item_id: str,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Delete menu item"""
    try:
        # Get item to verify ownership
        item = await get_menu_item_repo().get_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Menu item not found"
            )
        
        # Verify cafe ownership
        await verify_cafe_access(item["cafe_id"], current_user)
        
        # Delete item
        await get_menu_item_repo().delete(item_id)
        
        return ApiResponse(
            success=True,
            message="Menu item deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete menu item: {str(e)}"
        )


@router.post("/items/reorder", response_model=ApiResponse)
async def reorder_menu_items(
    cafe_id: str,
    item_orders: List[Dict[str, Any]],  # [{"id": "item_id", "order": 1}, ...]
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Reorder menu items (for drag-and-drop functionality)"""
    try:
        # Verify cafe ownership
        await verify_cafe_access(cafe_id, current_user)
        
        # Update order for each item
        for item_order in item_orders:
            item_id = item_order.get("id")
            order = item_order.get("order")
            
            if item_id and order is not None:
                await get_menu_item_repo().update(item_id, {"display_order": order})
        
        return ApiResponse(
            success=True,
            message="Menu items reordered successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reorder menu items: {str(e)}"
        )