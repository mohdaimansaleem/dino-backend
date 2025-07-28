#!/bin/bash

# Create all permissions in Firestore
# Usage: AUTH_TOKEN="$(gcloud auth print-identity-token)" ./create_all_permissions.sh

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
API_URL="https://dino-backend-api-1018711634531.us-central1.run.app/api/v1/permissions/"
AUTH_TOKEN="${AUTH_TOKEN:-}"

# Check if token is provided
if [ -z "$AUTH_TOKEN" ]; then
    echo -e "${RED}❌ No authentication token provided${NC}"
    echo "Usage: AUTH_TOKEN=\"\$(gcloud auth print-identity-token)\" $0"
    exit 1
fi

echo -e "${BLUE}🔐 Creating All Permissions in Firestore${NC}"
echo "=========================================="
echo ""

# Function to create permission
create_permission() {
    local name="$1"
    local description="$2"
    local resource="$3"
    local action="$4"
    local scope="$5"
    
    echo -e "${YELLOW}Creating: $name${NC}"
    
    response=$(curl -s -X POST "$API_URL" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $AUTH_TOKEN" \
      -d "{
        \"name\": \"$name\",
        \"description\": \"$description\",
        \"resource\": \"$resource\",
        \"action\": \"$action\",
        \"scope\": \"$scope\"
      }")
    
    if echo "$response" | grep -q '"id"'; then
        perm_id=$(echo "$response" | jq -r '.id' 2>/dev/null)
        echo -e "${GREEN}✅ Created: $name (ID: $perm_id)${NC}"
        return 0
    elif echo "$response" | grep -q "already exists"; then
        echo -e "${YELLOW}⚠️  Already exists: $name${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed: $name${NC}"
        echo "Response: $response"
        return 1
    fi
}

# Create all permissions
echo -e "${BLUE}📋 Workspace Permissions${NC}"
create_permission "workspace.create" "Create new workspaces" "workspace" "create" "all"
create_permission "workspace.read" "Read workspace information" "workspace" "read" "own"
create_permission "workspace.update" "Update workspace settings" "workspace" "update" "own"
create_permission "workspace.delete" "Delete workspaces" "workspace" "delete" "own"
create_permission "workspace.manage" "Full workspace management" "workspace" "manage" "all"

echo ""
echo -e "${BLUE}🏪 Venue Permissions${NC}"
create_permission "venue.create" "Create new venues" "venue" "create" "workspace"
create_permission "venue.read" "Read venue information" "venue" "read" "venue"
create_permission "venue.update" "Update venue settings" "venue" "update" "venue"
create_permission "venue.delete" "Delete venues" "venue" "delete" "workspace"
create_permission "venue.manage" "Full venue management" "venue" "manage" "workspace"

echo ""
echo -e "${BLUE}🍽️ Menu Permissions${NC}"
create_permission "menu.create" "Create menu items and categories" "menu" "create" "venue"
create_permission "menu.read" "Read menu items and categories" "menu" "read" "venue"
create_permission "menu.update" "Update menu items and categories" "menu" "update" "venue"
create_permission "menu.delete" "Delete menu items and categories" "menu" "delete" "venue"
create_permission "menu.manage" "Full menu management" "menu" "manage" "venue"

echo ""
echo -e "${BLUE}📦 Order Permissions${NC}"
create_permission "order.create" "Create new orders" "order" "create" "venue"
create_permission "order.read" "Read order information" "order" "read" "venue"
create_permission "order.update" "Update order status and details" "order" "update" "venue"
create_permission "order.delete" "Delete orders" "order" "delete" "venue"
create_permission "order.manage" "Full order management" "order" "manage" "venue"

echo ""
echo -e "${BLUE}👥 User Permissions${NC}"
create_permission "user.create" "Create new users" "user" "create" "workspace"
create_permission "user.read" "Read user information" "user" "read" "workspace"
create_permission "user.update" "Update user information" "user" "update" "workspace"
create_permission "user.delete" "Delete users" "user" "delete" "workspace"
create_permission "user.manage" "Full user management" "user" "manage" "all"

echo ""
echo -e "${BLUE}📊 Analytics Permissions${NC}"
create_permission "analytics.read" "Read analytics and reports" "analytics" "read" "venue"
create_permission "analytics.manage" "Full analytics management" "analytics" "manage" "workspace"

echo ""
echo -e "${BLUE}🪑 Table Permissions${NC}"
create_permission "table.create" "Create new tables" "table" "create" "venue"
create_permission "table.read" "Read table information" "table" "read" "venue"
create_permission "table.update" "Update table information" "table" "update" "venue"
create_permission "table.delete" "Delete tables" "table" "delete" "venue"
create_permission "table.manage" "Full table management" "table" "manage" "venue"

echo ""
echo -e "${GREEN}🎉 Permission creation completed!${NC}"
echo ""
echo "Verify permissions:"
echo "AUTH_TOKEN=\"\$(gcloud auth print-identity-token)\" curl -H \"Authorization: Bearer \$AUTH_TOKEN\" \"$API_URL\""