"""
Cafe Management API Endpoints
Optimized for Cloud Run with Firestore
"""
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from typing import List, Dict, Any, Optional
import logging

from app.models.schemas import (
    CafeCreate, CafeUpdate, Cafe, ApiResponse
)
from app.database.firestore import get_cafe_repo
from app.core.config import get_storage_bucket
# TODO: Implement storage service
# from app.services.storage_service import upload_image_to_gcs

logger = logging.getLogger(__name__)
router = APIRouter()


# Simple auth dependency for testing (replace with proper auth later)
async def get_current_user():
    """Mock current user for testing"""
    return {
        "id": "test-user-123",
        "email": "test@example.com",
        "role": "admin"
    }


async def get_current_admin_user():
    """Mock admin user for testing"""
    return {
        "id": "admin-user-123", 
        "email": "admin@example.com",
        "role": "admin"
    }


async def verify_cafe_access(cafe_id: str, current_user: Dict[str, Any]):
    """Verify user has access to cafe"""
    try:
        cafe_repo = get_cafe_repo()
        cafe = await cafe_repo.get_by_id(cafe_id)
        
        if not cafe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cafe not found"
            )
        
        if cafe.get("owner_id") != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this cafe"
            )
        
        return cafe
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying cafe access: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify cafe access"
        )


@router.post("/", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_cafe(
    cafe_data: CafeCreate,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Create a new cafe"""
    try:
        cafe_repo = get_cafe_repo()
        
        # Create cafe data with owner
        cafe_dict = cafe_data.dict()
        cafe_dict["owner_id"] = current_user["id"]
        cafe_dict["is_active"] = True
        
        # Save to database
        cafe_id = await cafe_repo.create(cafe_dict)
        
        # Get created cafe
        cafe = await cafe_repo.get_by_id(cafe_id)
        
        logger.info(f"✅ Created cafe {cafe_id} for user {current_user['id']}")
        
        return ApiResponse(
            success=True,
            message="Cafe created successfully",
            data=cafe
        )
    except Exception as e:
        logger.error(f"❌ Error creating cafe: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create cafe: {str(e)}"
        )


@router.get("/", response_model=List[Cafe])
async def get_cafes(
    limit: Optional[int] = 50,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get cafes (all active for public, owned for admin)"""
    try:
        cafe_repo = get_cafe_repo()
        
        if current_user.get("role") == "admin":
            # Admin users see their own cafes
            cafes = await cafe_repo.get_by_owner(current_user["id"])
            logger.info(f"✅ Retrieved {len(cafes)} cafes for admin {current_user['id']}")
        else:
            # Public users see all active cafes
            cafes = await cafe_repo.get_active_cafes(limit=limit)
            logger.info(f"✅ Retrieved {len(cafes)} active cafes")
        
        return [Cafe(**cafe) for cafe in cafes]
    except Exception as e:
        logger.error(f"❌ Error getting cafes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cafes: {str(e)}"
        )


@router.get("/my-cafes", response_model=List[Cafe])
async def get_my_cafes(current_user: Dict[str, Any] = Depends(get_current_admin_user)):
    """Get current user's cafes"""
    try:
        cafe_repo = get_cafe_repo()
        cafes = await cafe_repo.get_by_owner(current_user["id"])
        
        logger.info(f"✅ Retrieved {len(cafes)} cafes for user {current_user['id']}")
        
        return [Cafe(**cafe) for cafe in cafes]
    except Exception as e:
        logger.error(f"❌ Error getting user cafes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cafes: {str(e)}"
        )


@router.get("/{cafe_id}", response_model=Cafe)
async def get_cafe(cafe_id: str):
    """Get cafe by ID (public endpoint)"""
    try:
        cafe_repo = get_cafe_repo()
        cafe = await cafe_repo.get_by_id(cafe_id)
        
        if not cafe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cafe not found"
            )
        
        logger.info(f"✅ Retrieved cafe {cafe_id}")
        
        return Cafe(**cafe)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting cafe {cafe_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cafe: {str(e)}"
        )


@router.put("/{cafe_id}", response_model=ApiResponse)
async def update_cafe(
    cafe_id: str,
    cafe_update: CafeUpdate,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Update cafe information"""
    try:
        # Verify cafe ownership
        await verify_cafe_access(cafe_id, current_user)
        
        cafe_repo = get_cafe_repo()
        
        # Convert to dict and remove None values
        update_data = cafe_update.dict(exclude_unset=True)
        
        # Update cafe
        await cafe_repo.update(cafe_id, update_data)
        
        # Get updated cafe
        cafe = await cafe_repo.get_by_id(cafe_id)
        
        logger.info(f"✅ Updated cafe {cafe_id}")
        
        return ApiResponse(
            success=True,
            message="Cafe updated successfully",
            data=cafe
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating cafe {cafe_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update cafe: {str(e)}"
        )


@router.post("/{cafe_id}/logo", response_model=ApiResponse)
async def upload_cafe_logo(
    cafe_id: str,
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Upload cafe logo to Cloud Storage"""
    try:
        # Verify cafe ownership
        await verify_cafe_access(cafe_id, current_user)
        
        # TODO: Upload to Cloud Storage
        # logo_url = await upload_image_to_gcs(...)
        # Mock implementation for now
        logo_url = f"https://example.com/cafes/{cafe_id}/logo.jpg"
        
        # Update cafe with logo URL
        cafe_repo = get_cafe_repo()
        await cafe_repo.update(cafe_id, {"logo": logo_url})
        
        logger.info(f"✅ Uploaded logo for cafe {cafe_id}")
        
        return ApiResponse(
            success=True,
            message="Logo uploaded successfully",
            data={"logo_url": logo_url}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading logo for cafe {cafe_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload logo: {str(e)}"
        )


@router.delete("/{cafe_id}", response_model=ApiResponse)
async def delete_cafe(
    cafe_id: str,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Delete cafe (soft delete by deactivating)"""
    try:
        # Verify cafe ownership
        await verify_cafe_access(cafe_id, current_user)
        
        # Soft delete by deactivating
        cafe_repo = get_cafe_repo()
        await cafe_repo.update(cafe_id, {"is_active": False})
        
        logger.info(f"✅ Deactivated cafe {cafe_id}")
        
        return ApiResponse(
            success=True,
            message="Cafe deactivated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deactivating cafe {cafe_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete cafe: {str(e)}"
        )


@router.post("/{cafe_id}/activate", response_model=ApiResponse)
async def activate_cafe(
    cafe_id: str,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Activate cafe"""
    try:
        # Verify cafe ownership
        await verify_cafe_access(cafe_id, current_user)
        
        # Activate cafe
        cafe_repo = get_cafe_repo()
        await cafe_repo.update(cafe_id, {"is_active": True})
        
        logger.info(f"✅ Activated cafe {cafe_id}")
        
        return ApiResponse(
            success=True,
            message="Cafe activated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error activating cafe {cafe_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate cafe: {str(e)}"
        )


# Test endpoints for development
@router.post("/test/create-sample", response_model=ApiResponse)
async def create_sample_cafe():
    """Create a sample cafe for testing"""
    try:
        cafe_repo = get_cafe_repo()
        
        sample_cafe = {
            "name": "Test Cafe",
            "description": "A sample cafe for testing",
            "address": "123 Test Street, Test City",
            "phone": "+1234567890",
            "email": "test@testcafe.com",
            "owner_id": "test-user-123",
            "is_active": True,
            "cuisine_type": "International",
            "opening_hours": {
                "monday": "9:00-22:00",
                "tuesday": "9:00-22:00",
                "wednesday": "9:00-22:00",
                "thursday": "9:00-22:00",
                "friday": "9:00-23:00",
                "saturday": "9:00-23:00",
                "sunday": "10:00-21:00"
            }
        }
        
        cafe_id = await cafe_repo.create(sample_cafe)
        cafe = await cafe_repo.get_by_id(cafe_id)
        
        logger.info(f"✅ Created sample cafe {cafe_id}")
        
        return ApiResponse(
            success=True,
            message="Sample cafe created successfully",
            data=cafe
        )
    except Exception as e:
        logger.error(f"❌ Error creating sample cafe: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create sample cafe: {str(e)}"
        )