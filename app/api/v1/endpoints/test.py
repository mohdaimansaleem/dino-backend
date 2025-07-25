"""
Test API Endpoints for Database and Cloud Services
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import logging
from datetime import datetime

from app.database.firestore import (
    get_cafe_repo, get_user_repo, get_menu_item_repo
)
from app.core.config import get_firestore_client
from app.core.config import cloud_manager, settings
from app.models.schemas import ApiResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=Dict[str, Any])
async def test_health():
    """Test overall system health"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "environment": settings.ENVIRONMENT,
            "project_id": settings.GCP_PROJECT_ID,
            "services": {}
        }
        
        # Test Firestore
        try:
            db = get_firestore_client()
            collections = list(db.collections(page_size=1))
            health_status["services"]["firestore"] = {
                "status": "Connected",
                "collections_found": len(collections)
            }
        except Exception as e:
            health_status["services"]["firestore"] = {
                "status": f"Error: {str(e)}"
            }
        
        # Test Cloud Storage
        try:
            cloud_health = cloud_manager.health_check()
            if cloud_health["storage"]:
                health_status["services"]["storage"] = {
                    "status": "✅ Connected",
                    "bucket": settings.GCS_BUCKET_NAME
                }
            else:
                health_status["services"]["storage"] = {
                    "status": "❌ Not available"
                }
        except Exception as e:
            health_status["services"]["storage"] = {
                "status": f"❌ Error: {str(e)}"
            }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/firestore", response_model=Dict[str, Any])
async def test_firestore():
    """Test Firestore connection and operations"""
    try:
        db = get_firestore_client()
        
        # Test basic operations
        test_results = {
            "connection": "Connected",
            "project_id": settings.GCP_PROJECT_ID,
            "database_id": settings.FIRESTORE_DATABASE_ID,
            "operations": {}
        }
        
        # Test collection listing
        try:
            collections = list(db.collections(page_size=10))
            test_results["operations"]["list_collections"] = {
                "status": "Success",
                "count": len(collections),
                "collections": [col.id for col in collections]
            }
        except Exception as e:
            test_results["operations"]["list_collections"] = {
                "status": f"Error: {str(e)}"
            }
        
        # Test document creation and retrieval
        try:
            test_collection = db.collection("test_connection")
            test_doc = {
                "message": "Test document",
                "timestamp": datetime.utcnow(),
                "test_id": "connection_test"
            }
            
            # Create document
            doc_ref = test_collection.add(test_doc)[1]
            
            # Read document
            doc = doc_ref.get()
            if doc.exists:
                test_results["operations"]["create_read_document"] = {
                    "status": "Success",
                    "document_id": doc.id,
                    "data": doc.to_dict()
                }
                
                # Clean up - delete test document
                doc_ref.delete()
            else:
                test_results["operations"]["create_read_document"] = {
                    "status": "Document not found after creation"
                }
                
        except Exception as e:
            test_results["operations"]["create_read_document"] = {
                "status": f"Error: {str(e)}"
            }
        
        return test_results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Firestore test failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Firestore test failed: {str(e)}"
        )


@router.get("/storage", response_model=Dict[str, Any])
async def test_storage():
    """Test Cloud Storage connection"""
    try:
        storage_client = cloud_manager.get_storage_client()
        bucket = cloud_manager.get_storage_bucket()
        
        test_results = {
            "connection": "Connected",
            "bucket_name": settings.GCS_BUCKET_NAME,
            "project_id": settings.GCP_PROJECT_ID,
            "operations": {}
        }
        
        # Test bucket access
        try:
            bucket_exists = bucket.exists()
            test_results["operations"]["bucket_access"] = {
                "status": "Success" if bucket_exists else "Bucket not found",
                "exists": bucket_exists
            }
        except Exception as e:
            test_results["operations"]["bucket_access"] = {
                "status": f"Error: {str(e)}"
            }
        
        # Test listing objects (first 5)
        try:
            blobs = list(bucket.list_blobs(max_results=5))
            test_results["operations"]["list_objects"] = {
                "status": "Success",
                "count": len(blobs),
                "objects": [blob.name for blob in blobs]
            }
        except Exception as e:
            test_results["operations"]["list_objects"] = {
                "status": f"Error: {str(e)}"
            }
        
        return test_results
        
    except Exception as e:
        logger.error(f"Storage test failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Storage test failed: {str(e)}"
        )


@router.post("/cafe/sample", response_model=ApiResponse)
async def create_sample_cafe():
    """Create a sample cafe for testing"""
    try:
        cafe_repo = get_cafe_repo()
        
        sample_cafe = {
            "name": "Dino Test Cafe",
            "description": "A sample cafe created for testing the API",
            "address": "123 Test Street, Sample City, SC 12345",
            "phone": "+1-555-0123",
            "email": "contact@dinotestcafe.com",
            "owner_id": "test-owner-123",
            "is_active": True,
            "cuisine_type": "International",
            "opening_hours": {
                "monday": "8:00-22:00",
                "tuesday": "8:00-22:00", 
                "wednesday": "8:00-22:00",
                "thursday": "8:00-22:00",
                "friday": "8:00-23:00",
                "saturday": "9:00-23:00",
                "sunday": "9:00-21:00"
            },
            "features": ["wifi", "outdoor_seating", "takeaway", "delivery"],
            "rating": 4.5,
            "price_range": "$$"
        }
        
        cafe_id = await cafe_repo.create(sample_cafe)
        created_cafe = await cafe_repo.get_by_id(cafe_id)
        
        logger.info(f"Created sample cafe: {cafe_id}")
        
        return ApiResponse(
            success=True,
            message="Sample cafe created successfully",
            data={
                "cafe_id": cafe_id,
                "cafe": created_cafe
            }
        )
        
    except Exception as e:
        logger.error(f"Error creating sample cafe: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create sample cafe: {str(e)}"
        )


@router.post("/user/sample", response_model=ApiResponse)
async def create_sample_user():
    """Create a sample user for testing"""
    try:
        user_repo = get_user_repo()
        
        sample_user = {
            "email": "test@dinoapi.com",
            "name": "Test User",
            "phone": "+1-555-0199",
            "role": "customer",
            "is_active": True,
            "preferences": {
                "notifications": True,
                "newsletter": False,
                "dietary_restrictions": ["vegetarian"]
            }
        }
        
        user_id = await user_repo.create(sample_user)
        created_user = await user_repo.get_by_id(user_id)
        
        logger.info(f"Created sample user: {user_id}")
        
        return ApiResponse(
            success=True,
            message="Sample user created successfully",
            data={
                "user_id": user_id,
                "user": created_user
            }
        )
        
    except Exception as e:
        logger.error(f"Error creating sample user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create sample user: {str(e)}"
        )


@router.get("/collections", response_model=Dict[str, Any])
async def list_collections():
    """List all Firestore collections"""
    try:
        db = get_firestore_client()
        collections = list(db.collections())
        
        collection_info = {}
        for collection in collections:
            try:
                # Get document count (first 10 for performance)
                docs = list(collection.limit(10).stream())
                collection_info[collection.id] = {
                    "sample_count": len(docs),
                    "sample_docs": [doc.id for doc in docs[:5]]  # First 5 doc IDs
                }
            except Exception as e:
                collection_info[collection.id] = {
                    "error": str(e)
                }
        
        return {
            "total_collections": len(collections),
            "collections": collection_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing collections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list collections: {str(e)}"
        )