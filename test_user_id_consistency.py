#!/usr/bin/env python3
"""
Test script to verify user ID consistency across different creation methods
"""

import requests
import json
import sys
import re
import uuid

def is_valid_uuid(test_string):
    """Check if string is a valid UUID format"""
    try:
        uuid.UUID(test_string)
        return True
    except ValueError:
        return False

def test_register_endpoint():
    """Test user creation via register endpoint"""
    print("\n🔍 Testing Register Endpoint (/users/register)")
    print("-" * 50)
    
    url = "http://localhost:8000/api/v1/users/register"
    
    # Generate unique email for testing
    test_email = f"test_register_{uuid.uuid4().hex[:8]}@example.com"
    
    data = {
        "email": test_email,
        "phone": f"98765{uuid.uuid4().hex[:5]}",
        "first_name": "Register",
        "last_name": "Test",
        "password": "testpassword123"
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 201:
            result = response.json()
            user_data = result.get("user", {})
            user_id = user_data.get("id")
            
            print(f"✅ Register successful!")
            print(f"   User ID: {user_id}")
            print(f"   Email: {user_data.get('email')}")
            print(f"   UUID format: {'✅ Valid' if is_valid_uuid(user_id) else '❌ Invalid'}")
            
            return {
                "success": True,
                "user_id": user_id,
                "email": user_data.get("email"),
                "is_uuid": is_valid_uuid(user_id),
                "token": result.get("access_token")
            }
        else:
            print(f"❌ Register failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return {"success": False, "error": response.text}
            
    except Exception as e:
        print(f"❌ Register request failed: {e}")
        return {"success": False, "error": str(e)}

def test_create_user_endpoint(auth_token):
    """Test user creation via POST /users endpoint"""
    print("\n🔍 Testing Create User Endpoint (POST /users)")
    print("-" * 50)
    
    url = "http://localhost:8000/api/v1/users"
    
    # Generate unique email for testing
    test_email = f"test_create_{uuid.uuid4().hex[:8]}@example.com"
    
    data = {
        "email": test_email,
        "phone": f"87654{uuid.uuid4().hex[:5]}",
        "first_name": "Create",
        "last_name": "Test",
        "password": "testpassword123",
        "role_id": "default_role_id",  # You might need to adjust this
        "venue_ids": []
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 201:
            result = response.json()
            user_data = result.get("data", {})
            user_id = user_data.get("id")
            
            print(f"✅ Create user successful!")
            print(f"   User ID: {user_id}")
            print(f"   Email: {user_data.get('email')}")
            print(f"   UUID format: {'✅ Valid' if is_valid_uuid(user_id) else '❌ Invalid'}")
            
            return {
                "success": True,
                "user_id": user_id,
                "email": user_data.get("email"),
                "is_uuid": is_valid_uuid(user_id)
            }
        else:
            print(f"❌ Create user failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return {"success": False, "error": response.text}
            
    except Exception as e:
        print(f"❌ Create user request failed: {e}")
        return {"success": False, "error": str(e)}

def test_without_auth():
    """Test create user endpoint without authentication"""
    print("\n🔍 Testing Create User Without Auth")
    print("-" * 50)
    
    url = "http://localhost:8000/api/v1/users"
    
    # Generate unique email for testing
    test_email = f"test_noauth_{uuid.uuid4().hex[:8]}@example.com"
    
    data = {
        "email": test_email,
        "phone": f"76543{uuid.uuid4().hex[:5]}",
        "first_name": "NoAuth",
        "last_name": "Test",
        "password": "testpassword123",
        "role_id": "default_role_id",
        "venue_ids": []
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 201:
            result = response.json()
            user_data = result.get("data", {})
            user_id = user_data.get("id")
            
            print(f"✅ Create user without auth successful!")
            print(f"   User ID: {user_id}")
            print(f"   Email: {user_data.get('email')}")
            print(f"   UUID format: {'✅ Valid' if is_valid_uuid(user_id) else '❌ Invalid'}")
            
            return {
                "success": True,
                "user_id": user_id,
                "email": user_data.get("email"),
                "is_uuid": is_valid_uuid(user_id)
            }
        elif response.status_code == 401:
            print("❌ Authentication required (expected if auth is enforced)")
            return {"success": False, "error": "Auth required"}
        else:
            print(f"❌ Create user failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return {"success": False, "error": response.text}
            
    except Exception as e:
        print(f"❌ Create user request failed: {e}")
        return {"success": False, "error": str(e)}

def main():
    print("🚀 USER ID CONSISTENCY TEST")
    print("=" * 60)
    print("Testing that all user creation methods use consistent UUID format")
    
    results = []
    
    # Test 1: Register endpoint
    register_result = test_register_endpoint()
    results.append(("Register", register_result))
    
    # Test 2: Create user with auth (if we have a token from register)
    if register_result.get("success") and register_result.get("token"):
        create_result = test_create_user_endpoint(register_result["token"])
        results.append(("Create with Auth", create_result))
    elif len(sys.argv) > 1:
        # Use provided auth token
        auth_token = sys.argv[1]
        create_result = test_create_user_endpoint(auth_token)
        results.append(("Create with Auth", create_result))
    else:
        print("\n⚠️  Skipping authenticated create test (no token available)")
    
    # Test 3: Create user without auth
    no_auth_result = test_without_auth()
    results.append(("Create without Auth", no_auth_result))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 CONSISTENCY TEST RESULTS")
    print("=" * 60)
    
    all_uuid_format = True
    successful_tests = 0
    
    for test_name, result in results:
        if result.get("success"):
            successful_tests += 1
            user_id = result.get("user_id", "N/A")
            is_uuid = result.get("is_uuid", False)
            
            status = "✅" if is_uuid else "❌"
            print(f"{status} {test_name}:")
            print(f"   User ID: {user_id}")
            print(f"   UUID Format: {'Valid' if is_uuid else 'Invalid'}")
            print(f"   Email: {result.get('email', 'N/A')}")
            
            if not is_uuid:
                all_uuid_format = False
        else:
            print(f"❌ {test_name}: Failed - {result.get('error', 'Unknown error')}")
    
    print(f"\n📈 Summary:")
    print(f"   Successful tests: {successful_tests}/{len(results)}")
    print(f"   All UUIDs consistent: {'✅ Yes' if all_uuid_format and successful_tests > 0 else '❌ No'}")
    
    if all_uuid_format and successful_tests > 0:
        print("\n🎉 SUCCESS: All user creation methods now use consistent UUID format!")
        return True
    else:
        print("\n💥 ISSUE: User ID formats are not consistent across creation methods")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(f"Using provided auth token: {sys.argv[1][:20]}...")
    else:
        print("No auth token provided - will use token from register test if available")
    
    success = main()
    sys.exit(0 if success else 1)