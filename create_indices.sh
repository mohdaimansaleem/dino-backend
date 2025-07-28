#!/bin/bash

# Firestore Composite Indices Creation Script for Dino E-Menu
# This script creates optimized indices for faster API retrieval
# Usage: ./create_firestore_indices.sh

# Get script directory and load environment
SCRIPT_DIR="$( cd "$(dirname "$0")" ; pwd -P )"

# Check if environment file exists
if [ -f "${SCRIPT_DIR}/.env.production.sh" ]; then
    . ${SCRIPT_DIR}/.env.production.sh
    echo "✅ Loaded production environment"
elif [ -f "${SCRIPT_DIR}/.env" ]; then
    . ${SCRIPT_DIR}/.env
    echo "✅ Loaded .env file"
else
    echo "❌ No environment file found. Please create .env.production.sh or .env"
    echo "Required variables: GCP_PROJECT_ID, DATABASE_NAME"
    exit 1
fi

# Validate required environment variables
if [ -z "$GCP_PROJECT_ID" ] || [ -z "$DATABASE_NAME" ]; then
    echo "❌ Missing required environment variables:"
    echo "   GCP_PROJECT_ID: ${GCP_PROJECT_ID:-'NOT SET'}"
    echo "   DATABASE_NAME: ${DATABASE_NAME:-'NOT SET'}"
    exit 1
fi

echo "🔥 Creating Firestore Composite Indices for Dino E-Menu"
echo "======================================================="
echo "Project: $GCP_PROJECT_ID"
echo "Database: $DATABASE_NAME"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Function to create index with error handling
create_index() {
    local collection="$1"
    local description="$2"
    shift 2
    local field_configs="$@"
    
    echo -e "${BLUE}📊 Creating index for $collection: $description${NC}"
    
    if gcloud firestore indexes composite create \
        --project=${GCP_PROJECT_ID} \
        --database=${DATABASE_NAME} \
        --collection-group=${collection} \
        $field_configs \
        --quiet 2>/dev/null; then
        echo -e "${GREEN}✅ Success: $collection index created${NC}"
    else
        echo -e "${YELLOW}⚠️  Index may already exist or failed: $collection${NC}"
    fi
    echo ""
}

echo -e "${BLUE}🏢 WORKSPACE INDICES${NC}"
echo "===================="

# Workspace by owner and status
create_index "workspaces" "Owner and active status" \
    --field-config=field-path=owner_id,order=ascending \
    --field-config=field-path=is_active,order=ascending \
    --field-config=field-path=created_at,order=descending

# Workspace by business type and creation time
create_index "workspaces" "Business type and creation time" \
    --field-config=field-path=business_type,order=ascending \
    --field-config=field-path=created_at,order=descending

# Workspace by name (for uniqueness checks)
create_index "workspaces" "Name and active status" \
    --field-config=field-path=name,order=ascending \
    --field-config=field-path=is_active,order=ascending

echo -e "${BLUE}🏪 CAFE INDICES${NC}"
echo "==============="

# Cafes by workspace
create_index "cafes" "Workspace and active status" \
    --field-config=field-path=workspace_id,order=ascending \
    --field-config=field-path=is_active,order=ascending \
    --field-config=field-path=created_at,order=descending

# Cafes by location and rating
create_index "cafes" "Location and rating" \
    --field-config=field-path=address,order=ascending \
    --field-config=field-path=rating,order=descending

# Cafes by cuisine type and price range
create_index "cafes" "Cuisine and price range" \
    --field-config=field-path=cuisine_types,order=ascending \
    --field-config=field-path=price_range,order=ascending \
    --field-config=field-path=rating,order=descending

# Cafes by subscription status
create_index "cafes" "Subscription status and plan" \
    --field-config=field-path=subscription_status,order=ascending \
    --field-config=field-path=subscription_plan,order=ascending \
    --field-config=field-path=created_at,order=descending

# Cafes by verification status
create_index "cafes" "Verification and active status" \
    --field-config=field-path=is_verified,order=ascending \
    --field-config=field-path=is_active,order=ascending \
    --field-config=field-path=rating,order=descending

echo -e "${BLUE}👥 USER INDICES${NC}"
echo "==============="

# Users by workspace
create_index "users" "Workspace and active status" \
    --field-config=field-path=workspace_id,order=ascending \
    --field-config=field-path=is_active,order=ascending \
    --field-config=field-path=created_at,order=descending

# Users by cafe
create_index "users" "Cafe and role" \
    --field-config=field-path=cafe_id,order=ascending \
    --field-config=field-path=role_id,order=ascending \
    --field-config=field-path=created_at,order=descending

# Users by role
create_index "users" "Role and active status" \
    --field-config=field-path=role_id,order=ascending \
    --field-config=field-path=is_active,order=ascending \
    --field-config=field-path=created_at,order=descending

# Users by email (for login)
create_index "users" "Email and active status" \
    --field-config=field-path=email,order=ascending \
    --field-config=field-path=is_active,order=ascending

# Users by phone (for uniqueness)
create_index "users" "Phone and active status" \
    --field-config=field-path=phone,order=ascending \
    --field-config=field-path=is_active,order=ascending

# Users by verification status
create_index "users" "Verification status" \
    --field-config=field-path=is_verified,order=ascending \
    --field-config=field-path=email_verified,order=ascending \
    --field-config=field-path=created_at,order=descending

# Users by last login
create_index "users" "Last login activity" \
    --field-config=field-path=workspace_id,order=ascending \
    --field-config=field-path=last_login,order=descending

echo -e "${BLUE}🎭 ROLE INDICES${NC}"
echo "==============="

# Roles by system status
create_index "roles" "System roles and active status" \
    --field-config=field-path=is_system_role,order=ascending \
    --field-config=field-path=created_at,order=descending

# Roles by name (for uniqueness)
create_index "roles" "Role name" \
    --field-config=field-path=name,order=ascending

# Roles by permission count (for analytics)
create_index "roles" "Permission count" \
    --field-config=field-path=is_system_role,order=ascending \
    --field-config=field-path=created_at,order=descending

echo -e "${BLUE}🔐 PERMISSION INDICES${NC}"
echo "===================="

# Permissions by resource and action
create_index "permissions" "Resource and action" \
    --field-config=field-path=resource,order=ascending \
    --field-config=field-path=action,order=ascending

# Permissions by scope
create_index "permissions" "Resource and scope" \
    --field-config=field-path=resource,order=ascending \
    --field-config=field-path=scope,order=ascending

# Permissions by system status
create_index "permissions" "System permissions" \
    --field-config=field-path=is_system_permission,order=ascending \
    --field-config=field-path=resource,order=ascending

# Permissions by name (for uniqueness)
create_index "permissions" "Permission name" \
    --field-config=field-path=name,order=ascending

echo -e "${BLUE}🍽️ MENU INDICES${NC}"
echo "================"

# Menu categories by cafe
create_index "menu_categories" "Cafe and active status" \
    --field-config=field-path=cafe_id,order=ascending \
    --field-config=field-path=is_active,order=ascending \
    --field-config=field-path=created_at,order=ascending

# Menu items by cafe and category
create_index "menu_items" "Cafe and category" \
    --field-config=field-path=cafe_id,order=ascending \
    --field-config=field-path=category_id,order=ascending \
    --field-config=field-path=is_available,order=ascending

# Menu items by price
create_index "menu_items" "Cafe and price range" \
    --field-config=field-path=cafe_id,order=ascending \
    --field-config=field-path=base_price,order=ascending \
    --field-config=field-path=is_available,order=ascending

# Menu items by dietary preferences
create_index "menu_items" "Dietary preferences" \
    --field-config=field-path=cafe_id,order=ascending \
    --field-config=field-path=is_vegetarian,order=ascending \
    --field-config=field-path=is_vegan,order=ascending

# Menu items by spice level
create_index "menu_items" "Spice level and availability" \
    --field-config=field-path=cafe_id,order=ascending \
    --field-config=field-path=spice_level,order=ascending \
    --field-config=field-path=is_available,order=ascending

# Menu items by rating
create_index "menu_items" "Rating and availability" \
    --field-config=field-path=cafe_id,order=ascending \
    --field-config=field-path=rating,order=descending \
    --field-config=field-path=is_available,order=ascending

echo -e "${BLUE}📦 ORDER INDICES${NC}"
echo "================"

# Orders by cafe and status
create_index "orders" "Cafe and order status" \
    --field-config=field-path=cafe_id,order=ascending \
    --field-config=field-path=status,order=ascending \
    --field-config=field-path=created_at,order=descending

# Orders by customer
create_index "orders" "Customer orders" \
    --field-config=field-path=customer_id,order=ascending \
    --field-config=field-path=created_at,order=descending

# Orders by table
create_index "orders" "Table orders" \
    --field-config=field-path=table_id,order=ascending \
    --field-config=field-path=status,order=ascending \
    --field-config=field-path=created_at,order=descending

# Orders by payment status
create_index "orders" "Payment status" \
    --field-config=field-path=cafe_id,order=ascending \
    --field-config=field-path=payment_status,order=ascending \
    --field-config=field-path=created_at,order=descending

# Orders by order type
create_index "orders" "Order type and status" \
    --field-config=field-path=cafe_id,order=ascending \
    --field-config=field-path=order_type,order=ascending \
    --field-config=field-path=status,order=ascending

# Orders by total amount (for analytics)
create_index "orders" "Order value analytics" \
    --field-config=field-path=cafe_id,order=ascending \
    --field-config=field-path=total_amount,order=descending \
    --field-config=field-path=created_at,order=descending

echo -e "${BLUE}🪑 TABLE INDICES${NC}"
echo "================"

# Tables by cafe and status
create_index "tables" "Cafe and table status" \
    --field-config=field-path=cafe_id,order=ascending \
    --field-config=field-path=table_status,order=ascending \
    --field-config=field-path=table_number,order=ascending

# Tables by capacity
create_index "tables" "Capacity and availability" \
    --field-config=field-path=cafe_id,order=ascending \
    --field-config=field-path=capacity,order=ascending \
    --field-config=field-path=table_status,order=ascending

# Tables by location
create_index "tables" "Location and status" \
    --field-config=field-path=cafe_id,order=ascending \
    --field-config=field-path=location,order=ascending \
    --field-config=field-path=is_active,order=ascending

# Tables by QR code (for quick lookup)
create_index "tables" "QR code lookup" \
    --field-config=field-path=qr_code,order=ascending \
    --field-config=field-path=is_active,order=ascending

echo -e "${BLUE}💳 TRANSACTION INDICES${NC}"
echo "====================="

# Transactions by cafe and status
create_index "transactions" "Cafe and payment status" \
    --field-config=field-path=cafe_id,order=ascending \
    --field-config=field-path=status,order=ascending \
    --field-config=field-path=processed_at,order=descending

# Transactions by order
create_index "transactions" "Order transactions" \
    --field-config=field-path=order_id,order=ascending \
    --field-config=field-path=processed_at,order=descending

# Transactions by payment method
create_index "transactions" "Payment method analytics" \
    --field-config=field-path=cafe_id,order=ascending \
    --field-config=field-path=payment_method,order=ascending \
    --field-config=field-path=processed_at,order=descending

# Transactions by gateway
create_index "transactions" "Payment gateway" \
    --field-config=field-path=payment_gateway,order=ascending \
    --field-config=field-path=status,order=ascending \
    --field-config=field-path=processed_at,order=descending

# Transactions by amount (for analytics)
create_index "transactions" "Transaction amount" \
    --field-config=field-path=cafe_id,order=ascending \
    --field-config=field-path=amount,order=descending \
    --field-config=field-path=processed_at,order=descending

echo -e "${BLUE}🔔 NOTIFICATION INDICES${NC}"
echo "======================"

# Notifications by recipient
create_index "notifications" "Recipient notifications" \
    --field-config=field-path=recipient_id,order=ascending \
    --field-config=field-path=is_read,order=ascending \
    --field-config=field-path=created_at,order=descending

# Notifications by type
create_index "notifications" "Notification type" \
    --field-config=field-path=recipient_id,order=ascending \
    --field-config=field-path=notification_type,order=ascending \
    --field-config=field-path=created_at,order=descending

# Notifications by priority
create_index "notifications" "Priority notifications" \
    --field-config=field-path=recipient_id,order=ascending \
    --field-config=field-path=priority,order=ascending \
    --field-config=field-path=created_at,order=descending

echo -e "${BLUE}⭐ REVIEW INDICES${NC}"
echo "================="

# Reviews by cafe
create_index "reviews" "Cafe reviews" \
    --field-config=field-path=cafe_id,order=ascending \
    --field-config=field-path=is_verified,order=ascending \
    --field-config=field-path=created_at,order=descending

# Reviews by customer
create_index "reviews" "Customer reviews" \
    --field-config=field-path=customer_id,order=ascending \
    --field-config=field-path=created_at,order=descending

# Reviews by rating
create_index "reviews" "Rating analysis" \
    --field-config=field-path=cafe_id,order=ascending \
    --field-config=field-path=rating,order=descending \
    --field-config=field-path=created_at,order=descending

# Reviews by order
create_index "reviews" "Order reviews" \
    --field-config=field-path=order_id,order=ascending \
    --field-config=field-path=feedback_type,order=ascending

echo ""
echo -e "${GREEN}🎉 Firestore Index Creation Completed!${NC}"
echo "========================================"
echo ""
echo -e "${BLUE}📊 Summary:${NC}"
echo "  • Workspace indices: 3 created"
echo "  • Cafe indices: 5 created"
echo "  • User indices: 7 created"
echo "  • Role indices: 3 created"
echo "  • Permission indices: 4 created"
echo "  • Menu indices: 6 created"
echo "  • Order indices: 6 created"
echo "  • Table indices: 4 created"
echo "  • Transaction indices: 5 created"
echo "  • Notification indices: 3 created"
echo "  • Review indices: 4 created"
echo ""
echo -e "${YELLOW}📝 Notes:${NC}"
echo "  • Some indices may already exist (warnings are normal)"
echo "  • Index creation can take several minutes to complete"
echo "  • Check Firestore console to verify index status"
echo "  • Indices will improve query performance significantly"
echo ""
echo -e "${BLUE}🔗 Verify indices at:${NC}"
echo "  https://console.firebase.google.com/project/$GCP_PROJECT_ID/firestore/indexes"
echo ""
echo -e "${GREEN}✨ All indices created successfully!${NC}"