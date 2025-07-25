"""
Table Management API Endpoints
Updated for local development with mock authentication
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Dict, Any
import logging

from app.models.schemas import TableCreate, Table, ApiResponse
from app.database.firestore import get_table_repo, get_cafe_repo, get_order_repo
from app.services.qr_service import get_qr_service

logger = logging.getLogger(__name__)
router = APIRouter()


# Mock authentication for testing
async def get_current_admin_user():
    """Mock admin user for testing"""
    return {
        "id": "admin-user-123", 
        "email": "admin@example.com",
        "role": "admin"
    }


async def verify_cafe_access(cafe_id: str, current_user: Dict[str, Any]):
    """Mock cafe access verification for testing"""
    try:
        cafe = await get_cafe_repo().get_by_id(cafe_id)
        
        if not cafe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cafe not found"
            )
        
        # For testing, allow access if user is admin
        if current_user.get("role") == "admin":
            return cafe
        
        # Check ownership
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
async def create_table(
    table_data: TableCreate,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Create a new table with QR code"""
    try:
        # Verify cafe ownership
        await verify_cafe_access(table_data.cafe_id, current_user)
        
        # Check if table number already exists
        existing_table = await get_table_repo().get_by_table_number(
            table_data.cafe_id, table_data.table_number
        )
        if existing_table:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Table {table_data.table_number} already exists"
            )
        
        # Get cafe details for QR code generation
        cafe = await get_cafe_repo().get_by_id(table_data.cafe_id)
        cafe_name = cafe.get("name", "") if cafe else ""
        
        # Create table data
        table_dict = table_data.dict()
        table_dict["is_active"] = True
        
        # Create table in database first to get ID
        table_id = await get_table_repo().create(table_dict)
        
        # Generate QR code
        qr_service = get_qr_service()
        qr_data = await qr_service.generate_table_qr(
            table_data.cafe_id, 
            table_id, 
            cafe_name, 
            table_data.table_number
        )
        
        # Update table with QR code information
        await get_table_repo().update(table_id, {
            "qr_code_data": qr_data["qr_code_data"],
            "qr_code_url": qr_data["qr_code_url"],
            "blob_path": qr_data.get("blob_path", "")
        })
        
        # Get complete table data
        table = await get_table_repo().get_by_id(table_id)
        
        logger.info(f"✅ Created table {table_data.table_number} for cafe {table_data.cafe_id}")
        
        return ApiResponse(
            success=True,
            message="Table created successfully",
            data=table
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating table: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create table: {str(e)}"
        )


@router.get("/{cafe_id}", response_model=List[Table])
async def get_cafe_tables(
    cafe_id: str,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Get all tables for a cafe"""
    try:
        # Verify cafe ownership
        await verify_cafe_access(cafe_id, current_user)
        
        tables = await get_table_repo().get_by_cafe(cafe_id)
        
        logger.info(f"✅ Retrieved {len(tables)} tables for cafe {cafe_id}")
        
        return [Table(**table) for table in tables]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting tables for cafe {cafe_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tables: {str(e)}"
        )


@router.get("/public/{cafe_id}", response_model=List[Table])
async def get_public_cafe_tables(cafe_id: str):
    """Get active tables for a cafe (public endpoint for QR validation)"""
    try:
        tables = await get_table_repo().query([
            ("cafe_id", "==", cafe_id),
            ("is_active", "==", True)
        ])
        
        logger.info(f"✅ Retrieved {len(tables)} active tables for cafe {cafe_id}")
        
        return [Table(**table) for table in tables]
    except Exception as e:
        logger.error(f"❌ Error getting public tables for cafe {cafe_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tables: {str(e)}"
        )


@router.get("/detail/{table_id}", response_model=Table)
async def get_table(table_id: str):
    """Get table by ID (public endpoint for QR code access)"""
    try:
        table = await get_table_repo().get_by_id(table_id)
        if not table:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Table not found"
            )
        
        if not table.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Table is not active"
            )
        
        logger.info(f"✅ Retrieved table {table_id}")
        
        return Table(**table)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting table {table_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get table: {str(e)}"
        )


@router.post("/{table_id}/regenerate-qr", response_model=ApiResponse)
async def regenerate_table_qr(
    table_id: str,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Regenerate QR code for a table"""
    try:
        # Get table to verify ownership
        table = await get_table_repo().get_by_id(table_id)
        if not table:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Table not found"
            )
        
        # Verify cafe ownership
        await verify_cafe_access(table["cafe_id"], current_user)
        
        # Get cafe details
        cafe = await get_cafe_repo().get_by_id(table["cafe_id"])
        cafe_name = cafe.get("name", "") if cafe else ""
        
        # Extract old blob path for cleanup
        old_blob_path = table.get("blob_path", "")
        
        # Regenerate QR code
        qr_service = get_qr_service()
        qr_data = await qr_service.regenerate_table_qr(
            table["cafe_id"],
            table_id,
            old_blob_path,
            cafe_name,
            table["table_number"]
        )
        
        # Update table with new QR code information
        await get_table_repo().update(table_id, {
            "qr_code_data": qr_data["qr_code_data"],
            "qr_code_url": qr_data["qr_code_url"],
            "blob_path": qr_data.get("blob_path", "")
        })
        
        logger.info(f"✅ Regenerated QR code for table {table_id}")
        
        return ApiResponse(
            success=True,
            message="QR code regenerated successfully",
            data=qr_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error regenerating QR code for table {table_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate QR code: {str(e)}"
        )


@router.delete("/{table_id}", response_model=ApiResponse)
async def delete_table(
    table_id: str,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Delete table (with restriction: cannot delete first table)"""
    try:
        # Get table to verify ownership
        table = await get_table_repo().get_by_id(table_id)
        if not table:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Table not found"
            )
        
        # Verify cafe ownership
        await verify_cafe_access(table["cafe_id"], current_user)
        
        # Get all tables for the cafe to check if this is the first table
        all_tables = await get_table_repo().get_by_cafe(table["cafe_id"])
        
        # Sort by table number to find the first table
        all_tables.sort(key=lambda x: x.get("table_number", 0))
        
        if all_tables and all_tables[0]["id"] == table_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the first table. Delete tables in reverse order."
            )
        
        # Check if table has active orders
        active_orders = await get_order_repo().query([
            ("table_id", "==", table_id),
            ("status", "in", ["pending", "confirmed", "preparing", "ready"])
        ])
        
        if active_orders:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete table with active orders"
            )
        
        # Delete QR code file
        if table.get("blob_path"):
            qr_service = get_qr_service()
            await qr_service.delete_qr_file(table["blob_path"])
        
        # Delete table
        await get_table_repo().delete(table_id)
        
        logger.info(f"✅ Deleted table {table_id}")
        
        return ApiResponse(
            success=True,
            message="Table deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting table {table_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete table: {str(e)}"
        )


@router.post("/{table_id}/activate", response_model=ApiResponse)
async def activate_table(
    table_id: str,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Activate table"""
    try:
        # Get table to verify ownership
        table = await get_table_repo().get_by_id(table_id)
        if not table:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Table not found"
            )
        
        # Verify cafe ownership
        await verify_cafe_access(table["cafe_id"], current_user)
        
        # Activate table
        await get_table_repo().update(table_id, {"is_active": True})
        
        logger.info(f"✅ Activated table {table_id}")
        
        return ApiResponse(
            success=True,
            message="Table activated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error activating table {table_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate table: {str(e)}"
        )


@router.post("/{table_id}/deactivate", response_model=ApiResponse)
async def deactivate_table(
    table_id: str,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Deactivate table"""
    try:
        # Get table to verify ownership
        table = await get_table_repo().get_by_id(table_id)
        if not table:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Table not found"
            )
        
        # Verify cafe ownership
        await verify_cafe_access(table["cafe_id"], current_user)
        
        # Check if table has active orders
        active_orders = await get_order_repo().query([
            ("table_id", "==", table_id),
            ("status", "in", ["pending", "confirmed", "preparing", "ready"])
        ])
        
        if active_orders:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate table with active orders"
            )
        
        # Deactivate table
        await get_table_repo().update(table_id, {"is_active": False})
        
        logger.info(f"✅ Deactivated table {table_id}")
        
        return ApiResponse(
            success=True,
            message="Table deactivated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deactivating table {table_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate table: {str(e)}"
        )


# Test endpoint for creating sample table
@router.post("/test/create-sample", response_model=ApiResponse)
async def create_sample_table():
    """Create a sample table for testing"""
    try:
        # First, ensure we have a cafe to attach the table to
        cafe_repo = get_cafe_repo()
        cafes = await cafe_repo.get_all(limit=1)
        
        if not cafes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No cafes found. Create a cafe first using /api/v1/test/cafe/sample"
            )
        
        cafe = cafes[0]
        cafe_id = cafe["id"]
        
        # Create sample table
        table_data = {
            "cafe_id": cafe_id,
            "table_number": 1,
            "capacity": 4,
            "location": "Main dining area",
            "is_active": True
        }
        
        table_repo = get_table_repo()
        
        # Check if table already exists
        existing = await table_repo.get_by_table_number(cafe_id, 1)
        if existing:
            return ApiResponse(
                success=True,
                message="Sample table already exists",
                data=existing
            )
        
        # Create table
        table_id = await table_repo.create(table_data)
        
        # Generate QR code
        qr_service = get_qr_service()
        qr_data = await qr_service.generate_table_qr(
            cafe_id,
            table_id,
            cafe.get("name", "Sample Cafe"),
            1
        )
        
        # Update table with QR code
        await table_repo.update(table_id, {
            "qr_code_data": qr_data["qr_code_data"],
            "qr_code_url": qr_data["qr_code_url"],
            "blob_path": qr_data.get("blob_path", "")
        })
        
        # Get complete table
        table = await table_repo.get_by_id(table_id)
        
        logger.info(f"✅ Created sample table {table_id}")
        
        return ApiResponse(
            success=True,
            message="Sample table created successfully",
            data=table
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating sample table: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create sample table: {str(e)}"
        )