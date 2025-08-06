#!/usr/bin/env python3
"""
Test script for the new permission endpoints
"""
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_USER_ID = "test_user_123"
TEST_ROLE_ID = "test_role_456"

def test_endpoints():
    """Test the new permission endpoints"""
    
    print("🧪 Testing Permission Endpoints")
    print("=" * 50)
    
    # Test 1: Get user permissions
    print("\n1. Testing GET /permissions/users/{user_id}/permissions")
    try:
        response = requests.get(f"{BASE_URL}/permissions/users/{TEST_USER_ID}/permissions")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Permissions found: {len(data)}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 2: Get role permissions
    print("\n2. Testing GET /permissions/roles/{role_id}/permissions")
    try:
        response = requests.get(f"{BASE_URL}/permissions/roles/{TEST_ROLE_ID}/permissions")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Permissions found: {len(data)}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 3: Get current user permissions
    print("\n3. Testing GET /permissions/me/permissions")
    try:
        response = requests.get(f"{BASE_URL}/permissions/me/permissions")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Permissions found: {len(data)}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 4: Get detailed user permissions
    print("\n4. Testing GET /permissions/users/{user_id}/permissions/detailed")
    try:
        response = requests.get(f"{BASE_URL}/permissions/users/{TEST_USER_ID}/permissions/detailed")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   User ID: {data.get('user_id')}")
            print(f"   Role: {data.get('role', {}).get('name', 'N/A')}")
            print(f"   Total permissions: {data.get('total_permissions', 0)}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 5: Check specific permissions
    print("\n5. Testing POST /permissions/users/{user_id}/permissions/check")
    try:
        check_data = ["venue.read", "menu.create", "order.manage"]
        response = requests.post(
            f"{BASE_URL}/permissions/users/{TEST_USER_ID}/permissions/check",
            json=check_data
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   User ID: {data.get('user_id')}")
            print(f"   Has all permissions: {data.get('has_all')}")
            print(f"   Has any permissions: {data.get('has_any')}")
            print(f"   Permission details: {data.get('permissions')}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")
    print("\nNote: These tests will fail without authentication.")
    print("Use these endpoints with proper JWT tokens in production.")

if __name__ == "__main__":
    test_endpoints()