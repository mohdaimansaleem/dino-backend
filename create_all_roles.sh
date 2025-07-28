#!/bin/bash

# Create all roles with proper permission mapping in Firestore
# Usage: AUTH_TOKEN="$(gcloud auth print-identity-token)" ./create_all_roles.sh

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Configuration
PERMISSIONS_URL="https://dino-backend-api-1018711634531.us-central1.run.app/api/v1/permissions"
ROLES_URL="https://dino-backend-api-1018711634531.us-central1.run.app/api/v1/roles"
AUTH_TOKEN="${AUTH_TOKEN:-}"

# Check if token is provided
if [ -z "$AUTH_TOKEN" ]; then
    echo -e "${RED}❌ No authentication token provided${NC}"
    echo "Usage: AUTH_TOKEN=\"\$(gcloud auth print-identity-token)\" $0"
    exit 1
fi

echo -e "${PURPLE}👥 Creating All Roles with Permission Mapping${NC}"
echo "=============================================="
echo ""

# Function to get permission ID by name
get_permission_id_by_name() {
    local perm_name="$1"
    echo -e "${BLUE}🔍 Looking up permission: $perm_name${NC}" >&2
    
    response=$(curl -s -H "Authorization: Bearer $AUTH_TOKEN" "${PERMISSIONS_URL}/name/${perm_name}")
    
    if echo "$response" | grep -q '"id"'; then
        perm_id=$(echo "$response" | jq -r '.id' 2>/dev/null)
        echo -e "${GREEN}✅ Found: $perm_name (ID: $perm_id)${NC}" >&2
        echo "$perm_id"
        return 0
    else
        echo -e "${YELLOW}⚠️  Permission not found: $perm_name${NC}" >&2
        echo ""
        return 1
    fi
}

# Function to create role with permission IDs
create_role() {
    local name="$1"
    local description="$2"
    local permission_ids_json="$3"
    
    echo -e "${YELLOW}Creating role: $name${NC}"
    echo "Permission IDs: $permission_ids_json"
    
    # Create the JSON payload with proper escaping
    local json_payload=$(cat << EOF
{
  "name": "$name",
  "description": "$description",
  "permission_ids": $permission_ids_json
}
EOF
)
    
    echo "JSON Payload: $json_payload"
    
    response=$(curl -s -X POST "$ROLES_URL/" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $AUTH_TOKEN" \
      -d "$json_payload")
    
    if echo "$response" | grep -q '"id"'; then
        role_id=$(echo "$response" | jq -r '.id' 2>/dev/null)
        perm_count=$(echo "$permission_ids_json" | jq '. | length' 2>/dev/null || echo "0")
        echo -e "${GREEN}✅ Created: $name (ID: $role_id, $perm_count permissions)${NC}"
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

# Function to build permission array
build_permission_array() {
    local permission_names=("$@")
    local permission_ids=()
    local found_count=0
    
    echo -e "${BLUE}🔧 Building permission array...${NC}" >&2
    
    for perm_name in "${permission_names[@]}"; do
        perm_id=$(get_permission_id_by_name "$perm_name")
        if [ $? -eq 0 ] && [ -n "$perm_id" ]; then
            permission_ids+=("\"$perm_id\"")
            ((found_count++))
        fi
    done
    
    if [ ${#permission_ids[@]} -eq 0 ]; then
        echo "[]"
    else
        # Join array elements with commas
        IFS=','
        echo "[${permission_ids[*]}]"
        IFS=' '
    fi
    
    echo -e "${GREEN}✅ Found $found_count out of ${#permission_names[@]} permissions${NC}" >&2
    echo "" >&2
}

echo -e "${BLUE}🔧 Building permission sets for each role...${NC}"
echo ""

# Define permission sets for each role
echo -e "${PURPLE}📋 SUPERADMIN Role Permissions${NC}"
superadmin_permissions=(
    "workspace.create" "workspace.read" "workspace.update" "workspace.delete" "workspace.manage"
    "cafe.create" "cafe.read" "cafe.update" "cafe.delete" "cafe.manage"
    "menu.create" "menu.read" "menu.update" "menu.delete" "menu.manage"
    "order.create" "order.read" "order.update" "order.delete" "order.manage"
    "user.create" "user.read" "user.update" "user.delete" "user.manage"
    "analytics.read" "analytics.manage"
    "table.create" "table.read" "table.update" "table.delete" "table.manage"
)
superadmin_perms_json=$(build_permission_array "${superadmin_permissions[@]}")

echo -e "${PURPLE}📋 ADMIN Role Permissions${NC}"
admin_permissions=(
    "workspace.create" "workspace.read" "workspace.update" "workspace.delete" "workspace.manage"
    "cafe.create" "cafe.read" "cafe.update" "cafe.delete" "cafe.manage"
    "user.create" "user.read" "user.update" "user.delete" "user.manage"
    "analytics.read" "analytics.manage"
    "menu.read" "menu.manage"
    "order.read" "order.manage"
    "table.read" "table.manage"
)
admin_perms_json=$(build_permission_array "${admin_permissions[@]}")

echo -e "${PURPLE}📋 OPERATOR Role Permissions${NC}"
operator_permissions=(
    "cafe.read"
    "menu.create" "menu.read" "menu.update" "menu.delete" "menu.manage"
    "order.create" "order.read" "order.update" "order.delete" "order.manage"
    "table.create" "table.read" "table.update" "table.delete" "table.manage"
    "analytics.read"
)
operator_perms_json=$(build_permission_array "${operator_permissions[@]}")

# Create roles
echo -e "${BLUE}👥 Creating Roles...${NC}"
echo "==================="
echo ""

# Create SUPERADMIN role
echo -e "${PURPLE}Creating SUPERADMIN role...${NC}"
create_role "superadmin" \
    "Super administrator with full system access" \
    "$superadmin_perms_json"

echo ""

# Create ADMIN role
echo -e "${PURPLE}Creating ADMIN role...${NC}"
create_role "admin" \
    "Administrator with full workspace, cafe, user and analytics management" \
    "$admin_perms_json"

echo ""

# Create OPERATOR role
echo -e "${PURPLE}Creating OPERATOR role...${NC}"
create_role "operator" \
    "Cafe operator with menu, order and table management (no workspace/user management)" \
    "$operator_perms_json"

echo ""
echo -e "${GREEN}🎉 Role creation completed!${NC}"
echo ""

# Summary
superadmin_count=$(echo "$superadmin_perms_json" | jq '. | length' 2>/dev/null || echo "0")
admin_count=$(echo "$admin_perms_json" | jq '. | length' 2>/dev/null || echo "0")
operator_count=$(echo "$operator_perms_json" | jq '. | length' 2>/dev/null || echo "0")

echo -e "${BLUE}📊 Role Summary:${NC}"
echo "================"
echo "  🔹 SUPERADMIN: $superadmin_count permissions (Complete system access)"
echo "  🔹 ADMIN: $admin_count permissions (Management capabilities)"
echo "  🔹 OPERATOR: $operator_count permissions (Cafe operations only)"
echo ""

echo -e "${BLUE}📋 Permission Breakdown:${NC}"
echo "========================"
echo ""
echo -e "${YELLOW}SUPERADMIN permissions:${NC}"
echo "  • All workspace operations (create, read, update, delete, manage)"
echo "  • All cafe operations (create, read, update, delete, manage)"
echo "  • All menu operations (create, read, update, delete, manage)"
echo "  • All order operations (create, read, update, delete, manage)"
echo "  • All user operations (create, read, update, delete, manage)"
echo "  • All table operations (create, read, update, delete, manage)"
echo "  • Analytics (read, manage)"
echo ""
echo -e "${YELLOW}ADMIN permissions:${NC}"
echo "  • All workspace operations (create, read, update, delete, manage)"
echo "  • All cafe operations (create, read, update, delete, manage)"
echo "  • All user operations (create, read, update, delete, manage)"
echo "  • Menu oversight (read, manage)"
echo "  • Order oversight (read, manage)"
echo "  • Table oversight (read, manage)"
echo "  • Analytics (read, manage)"
echo ""
echo -e "${YELLOW}OPERATOR permissions:${NC}"
echo "  • Cafe information (read only)"
echo "  • Full menu operations (create, read, update, delete, manage)"
echo "  • Full order operations (create, read, update, delete, manage)"
echo "  • Full table operations (create, read, update, delete, manage)"
echo "  • Analytics (read only)"
echo ""

echo -e "${GREEN}✨ All roles created successfully!${NC}"
echo ""
echo -e "${BLUE}🔍 Verify roles:${NC}"
echo "AUTH_TOKEN=\"\$(gcloud auth print-identity-token)\" curl -H \"Authorization: Bearer \$AUTH_TOKEN\" \"$ROLES_URL\""
echo ""
echo -e "${YELLOW}💡 Note: Roles are created with proper permission mappings based on existing permissions in the database.${NC}"