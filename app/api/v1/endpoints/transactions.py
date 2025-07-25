"""
Transaction Management API Endpoints
Handles payment processing, transaction tracking, and financial operations
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import datetime, timedelta

from app.models.schemas import (
    Transaction, TransactionCreate, TransactionType, PaymentMethod, 
    PaymentStatus, ApiResponse, User, PaymentGateway
)
from app.services.transaction_service import get_transaction_service
from app.database.firestore import get_order_repo
from app.core.security import get_current_user, get_current_admin_user, verify_cafe_access

router = APIRouter()


@router.post("/", response_model=Transaction, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_data: TransactionCreate,
    cafe_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new transaction (admin only)"""
    try:
        # Verify cafe access
        await verify_cafe_access(cafe_id, current_user.dict())
        
        transaction_service = get_transaction_service()
        transaction = await transaction_service.create_transaction(transaction_data, cafe_id)
        
        return transaction
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating transaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create transaction"
        )


@router.get("/{transaction_id}", response_model=Transaction)
async def get_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get transaction by ID"""
    try:
        transaction_service = get_transaction_service()
        transaction = await transaction_service.get_transaction_by_id(transaction_id)
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Check if user has access to this transaction
        if current_user.role == "customer":
            # Customer can only see their own order transactions
            order_repo = get_enhanced_order_repo()
            order_data = await order_repo.get_by_id(transaction.order_id)
            
            if not order_data or order_data.get("customer_id") != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
        elif current_user.role in ["admin", "cafe_owner"]:
            # Admin/cafe owner can see transactions for their cafes
            order_repo = get_enhanced_order_repo()
            order_data = await order_repo.get_by_id(transaction.order_id)
            
            if order_data:
                await verify_cafe_access(order_data["cafe_id"], current_user.dict())
        
        return transaction
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting transaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get transaction"
        )


@router.get("/order/{order_id}", response_model=List[Transaction])
async def get_order_transactions(
    order_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all transactions for an order"""
    try:
        # Verify access to order
        order_repo = get_enhanced_order_repo()
        order_data = await order_repo.get_by_id(order_id)
        
        if not order_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Check access permissions
        if current_user.role == "customer":
            if order_data.get("customer_id") != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
        elif current_user.role in ["admin", "cafe_owner"]:
            await verify_cafe_access(order_data["cafe_id"], current_user.dict())
        
        transaction_service = get_transaction_service()
        transactions = await transaction_service.get_order_transactions(order_id)
        
        return transactions
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting order transactions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get order transactions"
        )


@router.post("/{transaction_id}/confirm", response_model=ApiResponse)
async def confirm_transaction(
    transaction_id: str,
    payment_confirmation: Dict[str, Any],
    current_user: User = Depends(get_current_admin_user)
):
    """Confirm a payment transaction"""
    try:
        transaction_service = get_transaction_service()
        
        # Get transaction to verify access
        transaction = await transaction_service.get_transaction_by_id(transaction_id)
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Verify cafe access
        order_repo = get_enhanced_order_repo()
        order_data = await order_repo.get_by_id(transaction.order_id)
        if order_data:
            await verify_cafe_access(order_data["cafe_id"], current_user.dict())
        
        # Confirm payment
        success = await transaction_service.confirm_payment(transaction_id, payment_confirmation)
        
        if success:
            return ApiResponse(
                success=True,
                message="Payment confirmed successfully"
            )
        else:
            return ApiResponse(
                success=False,
                message="Payment confirmation failed"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error confirming transaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm transaction"
        )


@router.post("/{transaction_id}/refund", response_model=ApiResponse)
async def create_refund(
    transaction_id: str,
    refund_amount: Optional[float] = None,
    reason: str = "requested_by_customer",
    current_user: User = Depends(get_current_admin_user)
):
    """Create a refund for a transaction"""
    try:
        transaction_service = get_transaction_service()
        
        # Get transaction to verify access
        transaction = await transaction_service.get_transaction_by_id(transaction_id)
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Verify cafe access
        order_repo = get_enhanced_order_repo()
        order_data = await order_repo.get_by_id(transaction.order_id)
        if order_data:
            await verify_cafe_access(order_data["cafe_id"], current_user.dict())
        
        # Create refund
        refund_result = await transaction_service.create_refund(
            transaction_id, refund_amount, reason
        )
        
        if refund_result["success"]:
            return ApiResponse(
                success=True,
                message="Refund processed successfully",
                data=refund_result
            )
        else:
            return ApiResponse(
                success=False,
                message=refund_result.get("error", "Refund failed")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating refund: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create refund"
        )


@router.get("/cafe/{cafe_id}/pending", response_model=List[Transaction])
async def get_pending_transactions(
    cafe_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Get pending transactions for a cafe"""
    try:
        # Verify cafe access
        await verify_cafe_access(cafe_id, current_user.dict())
        
        transaction_service = get_transaction_service()
        transactions = await transaction_service.get_pending_transactions(cafe_id)
        
        return transactions
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting pending transactions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get pending transactions"
        )


@router.get("/cafe/{cafe_id}/revenue", response_model=Dict[str, Any])
async def get_revenue_summary(
    cafe_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_admin_user)
):
    """Get revenue summary for a cafe"""
    try:
        # Verify cafe access
        await verify_cafe_access(cafe_id, current_user.dict())
        
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        transaction_service = get_transaction_service()
        revenue_summary = await transaction_service.get_cafe_revenue_summary(
            cafe_id, start_date, end_date
        )
        
        return revenue_summary
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting revenue summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get revenue summary"
        )


@router.get("/cafe/{cafe_id}/reconciliation", response_model=Dict[str, Any])
async def get_payment_reconciliation(
    cafe_id: str,
    date: datetime = Query(..., description="Date for reconciliation (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_admin_user)
):
    """Get payment reconciliation for a specific date"""
    try:
        # Verify cafe access
        await verify_cafe_access(cafe_id, current_user.dict())
        
        transaction_service = get_transaction_service()
        reconciliation = await transaction_service.reconcile_payments(cafe_id, date)
        
        return reconciliation
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting payment reconciliation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get payment reconciliation"
        )


@router.get("/cafe/{cafe_id}/financial-report", response_model=Dict[str, Any])
async def generate_financial_report(
    cafe_id: str,
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    current_user: User = Depends(get_current_admin_user)
):
    """Generate comprehensive financial report"""
    try:
        # Verify cafe access
        await verify_cafe_access(cafe_id, current_user.dict())
        
        # Validate date range
        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before end date"
            )
        
        # Limit report to maximum 1 year
        if (end_date - start_date).days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Report period cannot exceed 1 year"
            )
        
        transaction_service = get_transaction_service()
        financial_report = await transaction_service.generate_financial_report(
            cafe_id, start_date, end_date
        )
        
        return financial_report
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating financial report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate financial report"
        )


@router.get("/user/my-transactions", response_model=List[Transaction])
async def get_user_transactions(
    limit: Optional[int] = Query(20, le=100),
    current_user: User = Depends(get_current_user)
):
    """Get transactions for the current user"""
    try:
        # Get user's orders first
        order_repo = get_enhanced_order_repo()
        user_orders = await order_repo.get_by_customer(current_user.id)
        
        if not user_orders:
            return []
        
        # Get transactions for user's orders
        transaction_service = get_transaction_service()
        all_transactions = []
        
        for order in user_orders[:limit]:  # Limit orders to prevent too many queries
            order_transactions = await transaction_service.get_order_transactions(order["id"])
            all_transactions.extend(order_transactions)
        
        # Sort by creation date (newest first) and limit
        all_transactions.sort(key=lambda x: x.created_at, reverse=True)
        
        return all_transactions[:limit]
        
    except Exception as e:
        print(f"Error getting user transactions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user transactions"
        )


@router.get("/payment-methods", response_model=List[Dict[str, Any]])
async def get_payment_methods():
    """Get available payment methods"""
    try:
        payment_methods = [
            {
                "id": PaymentMethod.CASH,
                "name": "Cash",
                "description": "Pay with cash on delivery/pickup",
                "icon": "💵",
                "enabled": True
            },
            {
                "id": PaymentMethod.CARD,
                "name": "Credit/Debit Card",
                "description": "Pay with credit or debit card",
                "icon": "💳",
                "enabled": True
            },
            {
                "id": PaymentMethod.UPI,
                "name": "UPI",
                "description": "Pay using UPI apps like GPay, PhonePe",
                "icon": "📱",
                "enabled": True
            },
            {
                "id": PaymentMethod.WALLET,
                "name": "Digital Wallet",
                "description": "Pay using digital wallets",
                "icon": "👛",
                "enabled": True
            },
            {
                "id": PaymentMethod.NET_BANKING,
                "name": "Net Banking",
                "description": "Pay using internet banking",
                "icon": "🏦",
                "enabled": True
            }
        ]
        
        return payment_methods
        
    except Exception as e:
        print(f"Error getting payment methods: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get payment methods"
        )


@router.get("/payment-gateways", response_model=List[Dict[str, Any]])
async def get_payment_gateways():
    """Get available payment gateways"""
    try:
        payment_gateways = [
            {
                "id": PaymentGateway.RAZORPAY,
                "name": "Razorpay",
                "description": "Secure payment processing by Razorpay",
                "logo": "https://razorpay.com/logo.png",
                "enabled": True,
                "supported_methods": [
                    PaymentMethod.CARD, PaymentMethod.UPI, 
                    PaymentMethod.WALLET, PaymentMethod.NET_BANKING
                ]
            },
            {
                "id": PaymentGateway.STRIPE,
                "name": "Stripe",
                "description": "International payment processing by Stripe",
                "logo": "https://stripe.com/logo.png",
                "enabled": False,
                "supported_methods": [PaymentMethod.CARD]
            },
            {
                "id": PaymentGateway.PAYTM,
                "name": "Paytm",
                "description": "Pay using Paytm wallet and gateway",
                "logo": "https://paytm.com/logo.png",
                "enabled": True,
                "supported_methods": [
                    PaymentMethod.WALLET, PaymentMethod.UPI, PaymentMethod.CARD
                ]
            },
            {
                "id": PaymentGateway.CASH,
                "name": "Cash Payment",
                "description": "Pay with cash on delivery/pickup",
                "logo": None,
                "enabled": True,
                "supported_methods": [PaymentMethod.CASH]
            }
        ]
        
        return payment_gateways
        
    except Exception as e:
        print(f"Error getting payment gateways: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get payment gateways"
        )