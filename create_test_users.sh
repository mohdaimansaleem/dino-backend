#!/bin/bash

# Create Test Users via API
# This script creates test users using the registration endpoint

echo "🚀 Creating Test Users via API"
echo "================================"

BASE_URL="http://localhost:8000"
REGISTER_URL="$BASE_URL/api/v1/users/register"
USERS_URL="$BASE_URL/api/v1/users/?page=1&page_size=10"

# Function to create a user
create_user() {
    local email=$1
    local phone=$2
    local first_name=$3
    local last_name=$4
    local password=$5
    
    echo "📝 Creating user: $email"
    
    response=$(curl -s -w "\n%{http_code}" -X POST "$REGISTER_URL" \
        -H "Content-Type: application/json" \
        -d "{
            \"email\": \"$email\",
            \"phone\": \"$phone\",
            \"first_name\": \"$first_name\",
            \"last_name\": \"$last_name\",
            \"password\": \"$password\"
        }")
    
    # Extract status code (last line)
    status_code=$(echo "$response" | tail -n1)
    # Extract response body (all but last line)
    body=$(echo "$response" | head -n -1)
    
    if [ "$status_code" = "201" ]; then
        echo "   ✅ Success: $email created"
        return 0
    else
        echo "   ❌ Failed: $email (Status: $status_code)"
        echo "   Response: $body"
        return 1
    fi
}

# Function to test users endpoint
test_users_endpoint() {
    echo ""
    echo "🔍 Testing GET /users endpoint..."
    
    response=$(curl -s -w "\n%{http_code}" "$USERS_URL")
    
    # Extract status code (last line)
    status_code=$(echo "$response" | tail -n1)
    # Extract response body (all but last line)
    body=$(echo "$response" | head -n -1)
    
    if [ "$status_code" = "200" ]; then
        echo "✅ Endpoint working! Status: $status_code"
        
        # Parse JSON to get total count (basic parsing)
        total=$(echo "$body" | grep -o '"total":[0-9]*' | cut -d':' -f2)
        success=$(echo "$body" | grep -o '"success":[a-z]*' | cut -d':' -f2)
        
        echo "   Success: $success"
        echo "   Total users: $total"
        
        # Pretty print the response
        echo ""
        echo "📊 Response:"
        echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
        
        return 0
    else
        echo "❌ Endpoint failed! Status: $status_code"
        echo "   Response: $body"
        return 1
    fi
}

# Check if server is running
echo "🔍 Checking if server is running..."
if curl -s "$BASE_URL/api/v1/health" > /dev/null 2>&1; then
    echo "✅ Server is running"
else
    echo "❌ Server is not running!"
    echo "   Start server with: uvicorn app.main:app --reload"
    exit 1
fi

# Test endpoint first
echo ""
echo "1️⃣  Testing current state..."
test_users_endpoint
initial_test=$?

# Create test users
echo ""
echo "2️⃣  Creating test users..."

users_created=0

# Create admin user
if create_user "admin@dino.com" "+1234567890" "Admin" "User" "admin123"; then
    ((users_created++))
fi

# Create manager user  
if create_user "manager@dino.com" "+1234567891" "Manager" "User" "manager123"; then
    ((users_created++))
fi

# Create operator user
if create_user "operator@dino.com" "+1234567892" "Operator" "User" "operator123"; then
    ((users_created++))
fi

# Create test users
if create_user "john.doe@example.com" "+1555000001" "John" "Doe" "password123"; then
    ((users_created++))
fi

if create_user "jane.smith@example.com" "+1555000002" "Jane" "Smith" "password123"; then
    ((users_created++))
fi

echo ""
echo "📊 Created $users_created users"

# Test endpoint again
echo ""
echo "3️⃣  Testing endpoint after user creation..."
test_users_endpoint
final_test=$?

# Summary
echo ""
echo "📋 SUMMARY"
echo "=========="
echo "Users created: $users_created"
echo "Initial test: $([ $initial_test -eq 0 ] && echo "✅ Passed" || echo "❌ Failed")"
echo "Final test: $([ $final_test -eq 0 ] && echo "✅ Passed" || echo "❌ Failed")"

if [ $final_test -eq 0 ] && [ $users_created -gt 0 ]; then
    echo ""
    echo "🎉 SUCCESS! Users endpoint is now working with data."
    echo ""
    echo "💡 You can now test with:"
    echo "   curl \"$USERS_URL\""
    echo "   curl \"$USERS_URL&search=admin\""
    echo "   curl \"$USERS_URL&is_active=true\""
    exit 0
else
    echo ""
    echo "⚠️  There may still be issues. Check the responses above."
    exit 1
fi