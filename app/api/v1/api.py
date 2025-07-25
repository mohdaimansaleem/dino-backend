"""
Main API Router
Includes all endpoint routers
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, cafes, menu, tables, orders, analytics, users, transactions, notifications, uploads

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(cafes.router, prefix="/cafes", tags=["cafes"])
api_router.include_router(menu.router, prefix="/menu", tags=["menu"])
api_router.include_router(tables.router, prefix="/tables", tags=["tables"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
# Test endpoints removed for production
# api_router.include_router(test.router, prefix="/test", tags=["testing"])

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "dino-api-v1"}