#!/bin/bash

# Dummy User Registration Script for Dino E-Menu Portal (With Authentication)
# This script demonstrates how a new user can register their workspace and venue
# Usage: ./register_dummy_user_with_auth.sh

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# API Configuration
API_BASE_URL="https://dino-backend-api-1018711634531.us-central1.run.app/api/v1"
REGISTER_URL="$API_BASE_URL/register/workspace"
LOGIN_URL="$API_BASE_URL/register/workspace-login"

echo -e "${PURPLE}🦕 Dino E-Menu Portal - User Registration Demo (With Auth)${NC}"
echo "============================================================="
echo ""

# Function to get Google Cloud identity token
get_auth_token() {
    echo -e "${BLUE}🔐 Getting Google Cloud identity token...${NC}" >&2
    local token=$(gcloud auth print-identity-token 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$token" ]; then
        echo -e "${GREEN}✅ Authentication token obtained${NC}" >&2
        echo "$token"
        return 0
    else
        echo -e "${RED}❌ Failed to get authentication token${NC}" >&2
        echo "Please ensure you are logged in to Google Cloud:" >&2
        echo "  gcloud auth login" >&2
        return 1
    fi
}

# Function to generate random data
generate_random_email() {
    local prefix="demo$(date +%s)$(jot -r 1 100 999 2>/dev/null || echo $((RANDOM % 900 + 100)))"
    echo "${prefix}@dinovenue.com"
}

generate_random_phone() {
    local random_num=$(jot -r 1 7000000000 9999999999 2>/dev/null || echo $((7000000000 + RANDOM % 3000000000)))
    echo "+91${random_num}"
}

# Function to create registration payload
create_registration_payload() {
    local owner_email="$1"
    local owner_phone="$2"
    local venue_email="$3"
    local venue_phone="$4"
    
    cat << EOF
{
  "workspace_display_name": "Dino Demo Workspace",
  "workspace_description": "A demo workspace for testing the Dino E-Menu system",
  "business_type": "venue",
  "venue_name": "The Dino Venue",
  "venue_description": "A cozy venue serving delicious food and beverages with a prehistoric theme. We offer a wide variety of dishes from appetizers to desserts, perfect for families and friends.",
  "venue_address": "123 Jurassic Park Avenue, Dino City, DC 12345, India",
  "venue_phone": "$venue_phone",
  "venue_email": "$venue_email",
  "venue_website": "https://www.dinovenue.com",
  "cuisine_types": ["Continental", "Indian", "Italian", "Beverages"],
  "price_range": "mid_range",
  "owner_email": "$owner_email",
  "owner_phone": "$owner_phone",
  "owner_first_name": "John",
  "owner_last_name": "Doe",
  "owner_password": "DinoPass123!",
  "confirm_password": "DinoPass123!"
}
EOF
}

# Function to create login payload
create_login_payload() {
    local email="$1"
    local password="$2"
    
    cat << EOF
{
  "email": "$email",
  "password": "$password",
  "remember_me": false
}
EOF
}

# Get authentication token
AUTH_TOKEN=$(get_auth_token)
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Cannot proceed without authentication token${NC}"
    exit 1
fi

echo -e "${GREEN}🔑 Authentication token: ${AUTH_TOKEN:0:20}...${NC}"

echo ""

# Generate dummy data
echo -e "${BLUE}📊 Generating dummy user data...${NC}"
OWNER_EMAIL=$(generate_random_email)
OWNER_PHONE=$(generate_random_phone)
CAFE_EMAIL="venue.$(generate_random_email)"
CAFE_PHONE=$(generate_random_phone)

echo -e "${CYAN}Generated Data:${NC}"
echo "  👤 Owner Email: $OWNER_EMAIL"
echo "  📱 Owner Phone: $OWNER_PHONE"
echo "  🏪 Cafe Email: $CAFE_EMAIL"
echo "  📞 Cafe Phone: $CAFE_PHONE"
echo "  🔐 Password: DinoPass123!"
echo ""

# Create registration payload
echo -e "${BLUE}📝 Creating registration payload...${NC}"
REGISTRATION_PAYLOAD=$(create_registration_payload "$OWNER_EMAIL" "$OWNER_PHONE" "$CAFE_EMAIL" "$CAFE_PHONE")

echo -e "${CYAN}Registration Payload:${NC}"
echo "$REGISTRATION_PAYLOAD" | jq . 2>/dev/null || echo "$REGISTRATION_PAYLOAD"
echo ""

# Step 1: Register the workspace
echo -e "${BLUE}🚀 Step 1: Registering workspace and venue...${NC}"
echo "Endpoint: $REGISTER_URL"
echo ""

REGISTRATION_RESPONSE=$(curl -s -X POST "$REGISTER_URL" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d "$REGISTRATION_PAYLOAD" 2>/dev/null)

echo -e "${CYAN}Registration Response:${NC}"
echo "$REGISTRATION_RESPONSE" | jq . 2>/dev/null || echo "$REGISTRATION_RESPONSE"
echo ""

# Check if registration was successful
if echo "$REGISTRATION_RESPONSE" | grep -q '"success": *true'; then
    echo -e "${GREEN}✅ Registration successful!${NC}"
    
    # Extract registration details
    WORKSPACE_NAME=$(echo "$REGISTRATION_RESPONSE" | jq -r '.data.workspace_name // "N/A"')
    WORKSPACE_ID=$(echo "$REGISTRATION_RESPONSE" | jq -r '.data.workspace_id // "N/A"')
    CAFE_NAME=$(echo "$REGISTRATION_RESPONSE" | jq -r '.data.venue_name // "N/A"')
    CAFE_ID=$(echo "$REGISTRATION_RESPONSE" | jq -r '.data.venue_id // "N/A"')
    
    echo -e "${GREEN}📋 Registration Details:${NC}"
    echo "  🏢 Workspace: $WORKSPACE_NAME (ID: $WORKSPACE_ID)"
    echo "  🏪 Cafe: $CAFE_NAME (ID: $CAFE_ID)"
    echo "  👤 Owner: $OWNER_EMAIL"
    echo ""
    
    # Step 2: Login with the registered user
    echo -e "${BLUE}🔐 Step 2: Logging in with registered credentials...${NC}"
    echo "Endpoint: $LOGIN_URL"
    echo ""
    
    LOGIN_PAYLOAD=$(create_login_payload "$OWNER_EMAIL" "DinoPass123!")
    
    echo -e "${CYAN}Login Payload:${NC}"
    echo "$LOGIN_PAYLOAD" | jq . 2>/dev/null || echo "$LOGIN_PAYLOAD"
    echo ""
    
    LOGIN_RESPONSE=$(curl -s -X POST "$LOGIN_URL" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $AUTH_TOKEN" \
      -d "$LOGIN_PAYLOAD" 2>/dev/null)
    
    echo -e "${CYAN}Login Response:${NC}"
    echo "$LOGIN_RESPONSE" | jq . 2>/dev/null || echo "$LOGIN_RESPONSE"
    echo ""
    
    # Check if login was successful
    if echo "$LOGIN_RESPONSE" | grep -q '"access_token"'; then
        echo -e "${GREEN}✅ Login successful!${NC}"
        
        # Extract login details
        ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token // "N/A"')
        TOKEN_TYPE=$(echo "$LOGIN_RESPONSE" | jq -r '.token_type // "bearer"')
        EXPIRES_IN=$(echo "$LOGIN_RESPONSE" | jq -r '.expires_in // "N/A"')
        USER_ID=$(echo "$LOGIN_RESPONSE" | jq -r '.user.id // "N/A"')
        USER_ROLE=$(echo "$LOGIN_RESPONSE" | jq -r '.user.role_id // "N/A"')
        
        echo -e "${GREEN}🎫 Authentication Details:${NC}"
        echo "  🔑 Access Token: ${ACCESS_TOKEN:0:20}..."
        echo "  📝 Token Type: $TOKEN_TYPE"
        echo "  ⏰ Expires In: $EXPIRES_IN seconds"
        echo "  👤 User ID: $USER_ID"
        echo "  🎭 Role ID: $USER_ROLE"
        echo ""
        
        # Save credentials for future use
        echo -e "${BLUE}💾 Saving credentials to file...${NC}"
        cat > "demo_user_credentials.json" << EOF
{
  "registration_date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "owner": {
    "email": "$OWNER_EMAIL",
    "phone": "$OWNER_PHONE",
    "password": "DinoPass123!",
    "first_name": "John",
    "last_name": "Doe",
    "user_id": "$USER_ID"
  },
  "workspace": {
    "name": "$WORKSPACE_NAME",
    "id": "$WORKSPACE_ID",
    "display_name": "Dino Demo Workspace"
  },
  "venue": {
    "name": "$CAFE_NAME",
    "id": "$CAFE_ID",
    "email": "$CAFE_EMAIL",
    "phone": "$CAFE_PHONE"
  },
  "authentication": {
    "access_token": "$ACCESS_TOKEN",
    "token_type": "$TOKEN_TYPE",
    "expires_in": $EXPIRES_IN,
    "login_time": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  }
}
EOF
        
        echo -e "${GREEN}✅ Credentials saved to: demo_user_credentials.json${NC}"
        echo ""
        
        # Step 3: Test API access with the token
        echo -e "${BLUE}🧪 Step 3: Testing API access with authentication token...${NC}"
        
        # Test getting user profile
        echo "Testing user profile endpoint..."
        PROFILE_RESPONSE=$(curl -s -X GET "$API_BASE_URL/users/$USER_ID" \
          -H "Authorization: Bearer $ACCESS_TOKEN")
        
        if echo "$PROFILE_RESPONSE" | grep -q '"id"'; then
            echo -e "${GREEN}✅ User profile access successful${NC}"
        else
            echo -e "${YELLOW}⚠️  User profile access failed or requires different permissions${NC}"
        fi
        
        # Test getting workspace info
        echo "Testing workspace endpoint..."
        WORKSPACE_RESPONSE=$(curl -s -X GET "$API_BASE_URL/workspaces/$WORKSPACE_ID" \
          -H "Authorization: Bearer $ACCESS_TOKEN")
        
        if echo "$WORKSPACE_RESPONSE" | grep -q '"id"'; then
            echo -e "${GREEN}✅ Workspace access successful${NC}"
        else
            echo -e "${YELLOW}⚠️  Workspace access failed or requires different permissions${NC}"
        fi
        
        echo ""
        echo -e "${GREEN}🎉 Demo Registration and Login Completed Successfully!${NC}"
        echo ""
        echo -e "${BLUE}📋 Summary:${NC}"
        echo "  ✅ Workspace and venue registered in Firestore"
        echo "  ✅ Superadmin user created and authenticated"
        echo "  ✅ Access token obtained for API calls"
        echo "  ✅ Credentials saved for future testing"
        echo ""
        echo -e "${CYAN}🔧 Next Steps:${NC}"
        echo "  1. Use the access token to make authenticated API calls"
        echo "  2. Add menu items to your venue"
        echo "  3. Create tables for your venue"
        echo "  4. Set up operating hours"
        echo "  5. Invite staff members"
        echo ""
        echo -e "${YELLOW}💡 Usage Examples:${NC}"
        echo "  # Get user profile"
        echo "  curl -H \"Authorization: Bearer $ACCESS_TOKEN\" \"$API_BASE_URL/users/$USER_ID\""
        echo ""
        echo "  # Get workspace details"
        echo "  curl -H \"Authorization: Bearer $ACCESS_TOKEN\" \"$API_BASE_URL/workspaces/$WORKSPACE_ID\""
        echo ""
        echo "  # Get venue details"
        echo "  curl -H \"Authorization: Bearer $ACCESS_TOKEN\" \"$API_BASE_URL/venues/$CAFE_ID\""
        
    else
        echo -e "${RED}❌ Login failed!${NC}"
        echo "Please check the login response above for error details."
        
        # Check for specific error messages
        if echo "$LOGIN_RESPONSE" | grep -q "Invalid credentials"; then
            echo -e "${YELLOW}💡 Possible issue: Invalid email or password${NC}"
        elif echo "$LOGIN_RESPONSE" | grep -q "User not found"; then
            echo -e "${YELLOW}💡 Possible issue: User registration may have failed${NC}"
        fi
    fi
    
else
    echo -e "${RED}❌ Registration failed!${NC}"
    echo "Please check the registration response above for error details."
    
    # Check for specific error messages
    if echo "$REGISTRATION_RESPONSE" | grep -q "already exists"; then
        echo -e "${YELLOW}💡 Possible issue: Email or workspace name already exists${NC}"
        echo "Try running the script again to generate new random data."
    elif echo "$REGISTRATION_RESPONSE" | grep -q "validation"; then
        echo -e "${YELLOW}💡 Possible issue: Data validation failed${NC}"
        echo "Check the payload format and required field constraints."
    elif echo "$REGISTRATION_RESPONSE" | grep -q "403"; then
        echo -e "${YELLOW}💡 Possible issue: API access forbidden${NC}"
        echo "The API might require different authentication or permissions."
    fi
fi

echo ""
echo -e "${PURPLE}🦕 Demo completed. Thank you for testing Dino E-Menu!${NC}"