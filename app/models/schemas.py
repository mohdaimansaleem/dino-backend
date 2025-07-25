"""
Consolidated Pydantic Schemas for Dino E-Menu Backend
Comprehensive data models for users, cafes, orders, and analytics
"""
from pydantic import BaseModel, EmailStr, Field, validator, HttpUrl
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
import re


# Enums
class UserRole(str, Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"
    CAFE_OWNER = "cafe_owner"
    STAFF = "staff"


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    SERVED = "served"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentMethod(str, Enum):
    CASH = "cash"
    CARD = "card"
    UPI = "upi"
    WALLET = "wallet"
    NET_BANKING = "net_banking"


class PaymentGateway(str, Enum):
    RAZORPAY = "razorpay"
    STRIPE = "stripe"
    PAYPAL = "paypal"
    CASH = "cash"


class OrderType(str, Enum):
    DINE_IN = "dine_in"
    TAKEAWAY = "takeaway"
    DELIVERY = "delivery"


class NotificationType(str, Enum):
    ORDER_PLACED = "order_placed"
    ORDER_CONFIRMED = "order_confirmed"
    ORDER_READY = "order_ready"
    ORDER_DELIVERED = "order_delivered"
    PAYMENT_RECEIVED = "payment_received"
    SYSTEM_ALERT = "system_alert"


class TransactionType(str, Enum):
    PAYMENT = "payment"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"


# Base Models
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TimestampMixin(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# User Schemas
class UserAddress(BaseSchema):
    id: Optional[str] = None
    label: str = Field(..., min_length=1, max_length=50)
    address_line_1: str = Field(..., min_length=5, max_length=200)
    address_line_2: Optional[str] = Field(None, max_length=200)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    postal_code: str = Field(..., min_length=5, max_length=10)
    country: str = Field(default="India", max_length=100)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    is_default: bool = Field(default=False)


class UserPreferences(BaseSchema):
    dietary_restrictions: List[str] = Field(default_factory=list)
    favorite_cuisines: List[str] = Field(default_factory=list)
    spice_level: Optional[str] = Field(None, pattern="^(mild|medium|hot|extra_hot)$")
    notifications_enabled: bool = Field(default=True)
    email_notifications: bool = Field(default=True)
    sms_notifications: bool = Field(default=False)


class UserBase(BaseSchema):
    email: EmailStr
    phone: str = Field(..., pattern="^[+]?[1-9]?[0-9]{7,15}$")
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    role: UserRole = UserRole.CUSTOMER


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    terms_accepted: bool = Field(..., description="User must accept terms and conditions")
    marketing_consent: bool = Field(default=False)

    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

    @validator('password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r"[A-Z]", v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r"[a-z]", v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r"\d", v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserLogin(BaseSchema):
    email: EmailStr
    password: str
    remember_me: bool = Field(default=False)


class UserUpdate(BaseSchema):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    phone: Optional[str] = Field(None, pattern="^[+]?[1-9]?[0-9]{7,15}$")
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = Field(None, pattern="^(male|female|other|prefer_not_to_say)$")
    profile_image_url: Optional[HttpUrl] = None
    preferences: Optional[UserPreferences] = None


class User(UserBase, TimestampMixin):
    id: str
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    profile_image_url: Optional[HttpUrl] = None
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    addresses: List[UserAddress] = Field(default_factory=list)
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    last_login: Optional[datetime] = None
    login_count: int = Field(default=0)
    total_orders: int = Field(default=0)
    total_spent: float = Field(default=0.0)


# Cafe Schemas
class CafeHours(BaseSchema):
    day: str = Field(..., pattern="^(monday|tuesday|wednesday|thursday|friday|saturday|sunday)$")
    open_time: str = Field(..., pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    close_time: str = Field(..., pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    is_closed: bool = Field(default=False)


class CafeSettings(BaseSchema):
    accepts_online_orders: bool = Field(default=True)
    delivery_available: bool = Field(default=False)
    takeaway_available: bool = Field(default=True)
    dine_in_available: bool = Field(default=True)
    minimum_order_amount: float = Field(default=0.0, ge=0)
    delivery_radius_km: float = Field(default=5.0, ge=0, le=50)
    delivery_fee: float = Field(default=0.0, ge=0)
    estimated_prep_time: int = Field(default=30, ge=5, le=120)
    auto_accept_orders: bool = Field(default=False)


class CafeBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., max_length=1000)
    address: str = Field(..., min_length=10, max_length=300)
    phone: str = Field(..., pattern="^[+]?[1-9]?[0-9]{7,15}$")
    email: EmailStr
    website: Optional[HttpUrl] = None
    cuisine_types: List[str] = Field(default_factory=list)
    price_range: str = Field(..., pattern="^(budget|mid_range|premium|luxury)$")


class CafeCreate(CafeBase):
    owner_id: str
    business_license: Optional[str] = None
    tax_id: Optional[str] = None


class CafeUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    address: Optional[str] = Field(None, min_length=10, max_length=300)
    phone: Optional[str] = Field(None, pattern="^[+]?[1-9]?[0-9]{7,15}$")
    email: Optional[EmailStr] = None
    website: Optional[HttpUrl] = None
    logo_url: Optional[HttpUrl] = None
    cover_image_url: Optional[HttpUrl] = None
    cuisine_types: Optional[List[str]] = None
    price_range: Optional[str] = Field(None, pattern="^(budget|mid_range|premium|luxury)$")
    operating_hours: Optional[List[CafeHours]] = None
    settings: Optional[CafeSettings] = None


class Cafe(CafeBase, TimestampMixin):
    id: str
    owner_id: str
    logo_url: Optional[HttpUrl] = None
    cover_image_url: Optional[HttpUrl] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    operating_hours: List[CafeHours] = Field(default_factory=list)
    settings: CafeSettings = Field(default_factory=CafeSettings)
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    rating: float = Field(default=0.0, ge=0, le=5)
    total_reviews: int = Field(default=0)
    total_orders: int = Field(default=0)


# Menu Schemas
class NutritionalInfo(BaseSchema):
    calories: Optional[int] = Field(None, ge=0)
    protein_g: Optional[float] = Field(None, ge=0)
    carbs_g: Optional[float] = Field(None, ge=0)
    fat_g: Optional[float] = Field(None, ge=0)
    fiber_g: Optional[float] = Field(None, ge=0)
    sugar_g: Optional[float] = Field(None, ge=0)
    sodium_mg: Optional[float] = Field(None, ge=0)


class MenuItemVariant(BaseSchema):
    id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=100)
    price_modifier: float = Field(default=0.0)
    is_available: bool = Field(default=True)


class MenuCategoryBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    display_order: int = Field(default=0, ge=0)


class MenuCategoryCreate(MenuCategoryBase):
    cafe_id: str


class MenuCategoryUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    display_order: Optional[int] = Field(None, ge=0)


class MenuCategory(MenuCategoryBase):
    id: str
    cafe_id: str


class MenuItemBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., max_length=1000)
    base_price: float = Field(..., gt=0)
    category_id: str
    is_vegetarian: bool = Field(default=True)
    is_vegan: bool = Field(default=False)
    is_gluten_free: bool = Field(default=False)
    spice_level: str = Field(default="mild", pattern="^(mild|medium|hot|extra_hot)$")
    is_available: bool = Field(default=True)
    preparation_time_minutes: int = Field(..., ge=5, le=120)
    ingredients: List[str] = Field(default_factory=list)
    allergens: List[str] = Field(default_factory=list)
    variants: List[MenuItemVariant] = Field(default_factory=list)
    nutritional_info: Optional[NutritionalInfo] = None
    tags: List[str] = Field(default_factory=list)
    display_order: int = Field(default=0, ge=0)


class MenuItemCreate(MenuItemBase):
    cafe_id: str


class MenuItemUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    base_price: Optional[float] = Field(None, gt=0)
    category_id: Optional[str] = None
    is_vegetarian: Optional[bool] = None
    is_vegan: Optional[bool] = None
    is_gluten_free: Optional[bool] = None
    spice_level: Optional[str] = Field(None, pattern="^(mild|medium|hot|extra_hot)$")
    image_urls: Optional[List[HttpUrl]] = None
    is_available: Optional[bool] = None
    preparation_time_minutes: Optional[int] = Field(None, ge=5, le=120)
    ingredients: Optional[List[str]] = None
    allergens: Optional[List[str]] = None
    variants: Optional[List[MenuItemVariant]] = None
    nutritional_info: Optional[NutritionalInfo] = None
    tags: Optional[List[str]] = None
    display_order: Optional[int] = Field(None, ge=0)


class MenuItem(MenuItemBase, TimestampMixin):
    id: str
    cafe_id: str
    image_urls: List[HttpUrl] = Field(default_factory=list)
    total_orders: int = Field(default=0)
    rating: float = Field(default=0.0, ge=0, le=5)
    review_count: int = Field(default=0)


# Table Schemas
class TableBase(BaseSchema):
    table_number: int = Field(..., ge=1)


class TableCreate(TableBase):
    cafe_id: str


class Table(TableBase, TimestampMixin):
    id: str
    cafe_id: str
    qr_code: str
    qr_code_url: str
    is_active: bool = True


# Order Schemas
class OrderItemBase(BaseSchema):
    menu_item_id: str
    menu_item_name: str
    variant_id: Optional[str] = None
    variant_name: Optional[str] = None
    quantity: int = Field(..., ge=1)
    unit_price: float = Field(..., gt=0)
    total_price: float = Field(..., gt=0)
    special_instructions: Optional[str] = Field(None, max_length=500)


class OrderItemCreate(BaseSchema):
    menu_item_id: str
    variant_id: Optional[str] = None
    quantity: int = Field(..., ge=1)
    special_instructions: Optional[str] = Field(None, max_length=500)


class OrderDeliveryInfo(BaseSchema):
    delivery_address: UserAddress
    delivery_phone: str = Field(..., pattern="^[+]?[1-9]?[0-9]{7,15}$")
    delivery_instructions: Optional[str] = Field(None, max_length=500)
    estimated_delivery_time: Optional[datetime] = None
    actual_delivery_time: Optional[datetime] = None
    delivery_person_name: Optional[str] = None
    delivery_person_phone: Optional[str] = None


class OrderBase(BaseSchema):
    cafe_id: str
    customer_id: Optional[str] = None
    customer_name: str = Field(..., min_length=1, max_length=100)
    customer_phone: str = Field(..., pattern="^[+]?[1-9]?[0-9]{7,15}$")
    customer_email: Optional[EmailStr] = None
    order_type: OrderType
    table_id: Optional[str] = None
    special_instructions: Optional[str] = Field(None, max_length=1000)
    delivery_info: Optional[OrderDeliveryInfo] = None


class OrderCreate(OrderBase):
    items: List[OrderItemCreate] = Field(..., min_items=1)


class OrderUpdate(BaseSchema):
    status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None
    estimated_ready_time: Optional[datetime] = None
    special_instructions: Optional[str] = Field(None, max_length=1000)


class Order(OrderBase, TimestampMixin):
    id: str
    order_number: str
    items: List[OrderItemBase]
    subtotal: float = Field(..., ge=0)
    tax_amount: float = Field(default=0.0, ge=0)
    delivery_fee: float = Field(default=0.0, ge=0)
    discount_amount: float = Field(default=0.0, ge=0)
    total_amount: float = Field(..., gt=0)
    status: OrderStatus = OrderStatus.PENDING
    payment_status: PaymentStatus = PaymentStatus.PENDING
    estimated_ready_time: Optional[datetime] = None
    actual_ready_time: Optional[datetime] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    review: Optional[str] = Field(None, max_length=1000)


# Transaction Schemas
class TransactionBase(BaseSchema):
    order_id: str
    amount: float = Field(..., gt=0)
    transaction_type: TransactionType
    payment_method: PaymentMethod
    payment_gateway: Optional[str] = None
    gateway_transaction_id: Optional[str] = None
    gateway_response: Optional[Dict[str, Any]] = None
    status: PaymentStatus
    description: Optional[str] = Field(None, max_length=500)


class TransactionCreate(TransactionBase):
    pass


class Transaction(TransactionBase, TimestampMixin):
    id: str
    processed_at: Optional[datetime] = None
    refunded_amount: float = Field(default=0.0, ge=0)


# Notification Schemas
class NotificationBase(BaseSchema):
    recipient_id: str
    recipient_type: str = Field(..., pattern="^(user|cafe|admin)$")
    notification_type: NotificationType
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=1000)
    data: Optional[Dict[str, Any]] = None
    is_read: bool = Field(default=False)
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")


class NotificationCreate(NotificationBase):
    pass


class Notification(NotificationBase, TimestampMixin):
    id: str
    read_at: Optional[datetime] = None


# Analytics Schemas
class PopularItem(BaseSchema):
    menu_item_id: str
    menu_item_name: str
    order_count: int
    revenue: float


class RevenueData(BaseSchema):
    date: str
    revenue: float
    orders: int


class StatusData(BaseSchema):
    status: OrderStatus
    count: int


class SalesAnalytics(BaseSchema):
    total_revenue: float
    total_orders: int
    average_order_value: float
    popular_items: List[PopularItem]
    revenue_by_day: List[RevenueData]
    orders_by_status: List[StatusData]


class DashboardStats(BaseSchema):
    total_orders_today: int = Field(default=0)
    total_revenue_today: float = Field(default=0.0)
    pending_orders: int = Field(default=0)
    active_customers: int = Field(default=0)
    average_order_value: float = Field(default=0.0)
    popular_items: List[Dict[str, Any]] = Field(default_factory=list)
    recent_orders: List[Order] = Field(default_factory=list)


# Response Schemas
class AuthToken(BaseSchema):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int
    user: User


class Token(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    user: User


class ApiResponse(BaseSchema):
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginatedResponse(BaseSchema):
    success: bool = True
    data: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class ErrorResponse(BaseSchema):
    success: bool = False
    error: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# File Upload Schemas
class ImageUploadResponse(BaseSchema):
    success: bool = True
    file_url: HttpUrl
    file_name: str
    file_size: int
    content_type: str
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)


class BulkImageUploadResponse(BaseSchema):
    success: bool = True
    uploaded_files: List[ImageUploadResponse]
    failed_files: List[Dict[str, str]] = Field(default_factory=list)
    total_uploaded: int
    total_failed: int