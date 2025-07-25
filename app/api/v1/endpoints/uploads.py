"""
File Upload API Endpoints
Handles image and document uploads to Google Cloud Storage
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import RedirectResponse

from app.models.schemas import (
    ImageUploadResponse, BulkImageUploadResponse, ApiResponse, User
)
from app.services.storage_service import get_storage_service
from app.core.security import get_current_user, get_current_admin_user
from app.core.config import get_settings

router = APIRouter()


@router.post("/image", response_model=ImageUploadResponse)
async def upload_single_image(
    file: UploadFile = File(...),
    folder: Optional[str] = Form(None),
    optimize: bool = Form(True),
    generate_thumbnails: bool = Form(False),
    current_user: User = Depends(get_current_user)
):
    """Upload a single image"""
    try:
        storage_service = get_storage_service()
        
        # Set default folder based on user role
        if not folder:
            if current_user.role in ["admin", "cafe_owner"]:
                folder = "cafe-images"
            else:
                folder = f"user-uploads/{current_user.id}"
        
        # Upload image
        result = await storage_service.upload_image(
            file=file,
            folder=folder,
            optimize=optimize,
            generate_thumbnails=generate_thumbnails
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image"
        )


@router.post("/images", response_model=BulkImageUploadResponse)
async def upload_multiple_images(
    files: List[UploadFile] = File(...),
    folder: Optional[str] = Form(None),
    optimize: bool = Form(True),
    current_user: User = Depends(get_current_user)
):
    """Upload multiple images"""
    try:
        # Validate number of files
        if len(files) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 files allowed per upload"
            )
        
        storage_service = get_storage_service()
        
        # Set default folder based on user role
        if not folder:
            if current_user.role in ["admin", "cafe_owner"]:
                folder = "cafe-images"
            else:
                folder = f"user-uploads/{current_user.id}"
        
        # Upload images
        result = await storage_service.upload_multiple_images(
            files=files,
            folder=folder,
            optimize=optimize
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading images: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload images"
        )


@router.post("/document", response_model=ImageUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    folder: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """Upload a document file"""
    try:
        storage_service = get_storage_service()
        
        # Set default folder
        if not folder:
            folder = f"documents/{current_user.id}"
        
        # Upload document
        result = await storage_service.upload_document(
            file=file,
            folder=folder
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document"
        )


@router.post("/menu-item-image", response_model=ImageUploadResponse)
async def upload_menu_item_image(
    file: UploadFile = File(...),
    menu_item_id: str = Form(...),
    current_user: User = Depends(get_current_admin_user)
):
    """Upload image for a menu item (admin/cafe owner only)"""
    try:
        storage_service = get_storage_service()
        
        # Upload to menu items folder
        folder = f"menu-items/{menu_item_id}"
        
        result = await storage_service.upload_image(
            file=file,
            folder=folder,
            optimize=True,
            generate_thumbnails=True
        )
        
        # Update menu item with image URL
        from app.database.firestore import get_menu_item_repo, get_cafe_repo
        menu_repo = get_enhanced_menu_repo()
        
        # Get current menu item
        menu_item = await menu_repo.get_by_id(menu_item_id)
        if menu_item:
            # Add image URL to existing image URLs
            image_urls = menu_item.get("image_urls", [])
            image_urls.append(result.file_url)
            
            await menu_repo.update(menu_item_id, {
                "image_urls": image_urls
            })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading menu item image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload menu item image"
        )


@router.post("/cafe-logo", response_model=ImageUploadResponse)
async def upload_cafe_logo(
    file: UploadFile = File(...),
    cafe_id: str = Form(...),
    current_user: User = Depends(get_current_admin_user)
):
    """Upload logo for a cafe (admin/cafe owner only)"""
    try:
        # Verify cafe access
        from app.core.security import verify_cafe_access
        await verify_cafe_access(cafe_id, current_user.dict())
        
        storage_service = get_storage_service()
        
        # Upload to cafe logos folder
        folder = f"cafe-logos/{cafe_id}"
        
        result = await storage_service.upload_image(
            file=file,
            folder=folder,
            optimize=True
        )
        
        # Update cafe with logo URL
        from app.database.firestore import get_menu_item_repo, get_cafe_repo
        cafe_repo = get_enhanced_cafe_repo()
        
        await cafe_repo.update(cafe_id, {
            "logo_url": result.file_url
        })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading cafe logo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload cafe logo"
        )


@router.post("/cafe-cover", response_model=ImageUploadResponse)
async def upload_cafe_cover_image(
    file: UploadFile = File(...),
    cafe_id: str = Form(...),
    current_user: User = Depends(get_current_admin_user)
):
    """Upload cover image for a cafe (admin/cafe owner only)"""
    try:
        # Verify cafe access
        from app.core.security import verify_cafe_access
        await verify_cafe_access(cafe_id, current_user.dict())
        
        storage_service = get_storage_service()
        
        # Upload to cafe covers folder
        folder = f"cafe-covers/{cafe_id}"
        
        result = await storage_service.upload_image(
            file=file,
            folder=folder,
            optimize=True
        )
        
        # Update cafe with cover image URL
        from app.database.firestore import get_menu_item_repo, get_cafe_repo
        cafe_repo = get_enhanced_cafe_repo()
        
        await cafe_repo.update(cafe_id, {
            "cover_image_url": result.file_url
        })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading cafe cover image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload cafe cover image"
        )


@router.delete("/file/{file_path:path}", response_model=ApiResponse)
async def delete_file(
    file_path: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a file from storage"""
    try:
        storage_service = get_storage_service()
        
        # Check if user has permission to delete this file
        # Users can only delete files in their own folders (unless admin)
        if current_user.role not in ["admin", "cafe_owner"]:
            if not file_path.startswith(f"user-uploads/{current_user.id}/"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permission denied"
                )
        
        success = await storage_service.delete_file(file_path)
        
        if success:
            return ApiResponse(
                success=True,
                message="File deleted successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file"
        )


@router.delete("/files", response_model=ApiResponse)
async def delete_multiple_files(
    file_paths: List[str],
    current_user: User = Depends(get_current_admin_user)
):
    """Delete multiple files from storage (admin only)"""
    try:
        if len(file_paths) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 50 files allowed per deletion"
            )
        
        storage_service = get_storage_service()
        results = await storage_service.delete_multiple_files(file_paths)
        
        successful_deletions = sum(1 for success in results.values() if success)
        failed_deletions = len(file_paths) - successful_deletions
        
        return ApiResponse(
            success=failed_deletions == 0,
            message=f"Deleted {successful_deletions} files, {failed_deletions} failed",
            data={
                "results": results,
                "successful": successful_deletions,
                "failed": failed_deletions
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete files"
        )


@router.get("/file-info/{file_path:path}", response_model=Dict[str, Any])
async def get_file_info(
    file_path: str,
    current_user: User = Depends(get_current_user)
):
    """Get information about a file"""
    try:
        storage_service = get_storage_service()
        
        # Check if user has permission to access this file info
        if current_user.role not in ["admin", "cafe_owner"]:
            if not file_path.startswith(f"user-uploads/{current_user.id}/"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permission denied"
                )
        
        file_info = storage_service.get_file_info(file_path)
        
        if file_info:
            return file_info
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting file info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get file information"
        )


@router.get("/files", response_model=List[Dict[str, Any]])
async def list_files(
    prefix: str = Query("", description="File path prefix to filter by"),
    max_results: int = Query(100, le=1000, description="Maximum number of files to return"),
    current_user: User = Depends(get_current_user)
):
    """List files in storage"""
    try:
        storage_service = get_storage_service()
        
        # Restrict access based on user role
        if current_user.role not in ["admin", "cafe_owner"]:
            # Regular users can only list their own files
            if not prefix.startswith(f"user-uploads/{current_user.id}/"):
                prefix = f"user-uploads/{current_user.id}/"
        
        files = storage_service.list_files(prefix, max_results)
        
        return files
        
    except Exception as e:
        print(f"Error listing files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list files"
        )


@router.get("/signed-url/{file_path:path}")
async def get_signed_url(
    file_path: str,
    expiration_hours: int = Query(1, ge=1, le=24, description="URL expiration in hours"),
    current_user: User = Depends(get_current_user)
):
    """Get a signed URL for private file access"""
    try:
        storage_service = get_storage_service()
        
        # Check if user has permission to access this file
        if current_user.role not in ["admin", "cafe_owner"]:
            if not file_path.startswith(f"user-uploads/{current_user.id}/"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permission denied"
                )
        
        from datetime import timedelta
        expiration = timedelta(hours=expiration_hours)
        
        signed_url = storage_service.get_signed_url(file_path, expiration)
        
        return RedirectResponse(url=signed_url)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating signed URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate signed URL"
        )


@router.post("/cleanup", response_model=ApiResponse)
async def cleanup_old_files(
    folder: str = Query(..., description="Folder to clean up"),
    days_old: int = Query(30, ge=1, le=365, description="Delete files older than this many days"),
    current_user: User = Depends(get_current_admin_user)
):
    """Clean up old files in a specific folder (admin only)"""
    try:
        storage_service = get_storage_service()
        deleted_count = storage_service.cleanup_old_files(folder, days_old)
        
        return ApiResponse(
            success=True,
            message=f"Cleaned up {deleted_count} old files from {folder}",
            data={"deleted_count": deleted_count, "folder": folder}
        )
        
    except Exception as e:
        print(f"Error cleaning up files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clean up files"
        )


@router.get("/storage-info", response_model=Dict[str, Any])
async def get_storage_info(
    current_user: User = Depends(get_current_admin_user)
):
    """Get storage configuration and limits (admin only)"""
    try:
        gcp_settings = get_settings()
        
        storage_info = {
            "bucket_name": gcp_settings.GCS_BUCKET_NAME,
            "bucket_region": gcp_settings.GCS_BUCKET_REGION,
            "max_image_size_mb": gcp_settings.MAX_IMAGE_SIZE_MB,
            "max_document_size_mb": gcp_settings.MAX_DOCUMENT_SIZE_MB,
            "allowed_image_types": gcp_settings.ALLOWED_IMAGE_TYPES,
            "images_folder": gcp_settings.GCS_IMAGES_FOLDER,
            "documents_folder": gcp_settings.GCS_DOCUMENTS_FOLDER,
            "qr_codes_folder": gcp_settings.GCS_QR_CODES_FOLDER,
            "cdn_base_url": f"https://storage.googleapis.com/{gcp_settings.GCS_BUCKET_NAME}"
        }
        
        return storage_info
        
    except Exception as e:
        print(f"Error getting storage info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get storage information"
        )