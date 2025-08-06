#!/usr/bin/env python3
"""
Simple test script for open permission endpoints
Tests that any authenticated user can access permission endpoints
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:8000/api/v1"

def test_open_permission_endpoints(auth_token):
    """Test that permission endpoints are now open to any authenticated user"""
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }
    
    print("🚀 Testing Open Permission Endpoints")
    print("="*50)
    
    # Test 1: Get current user profile to get user ID
    print("\n1. Getting current user profile...")
    response = requests.get(f"{BASE_URL}/users/profile", headers=headers)
    
    if response.status_code == 200:
        user_data = response.json()
        user_id = user_data.get("id")
        role_id = user_data.get("role_id")
        print(f"✅ Current user: {user_data.get('first_name', '')} {user_data.get('last_name', '')} (ID: {user_id})")
        print(f"   Role ID: {role_id}")
    else:
        print(f"❌ Failed to get user profile: {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    
    # Test 2: Get user permissions (should work now)
    print(f"\n2. Getting permissions for user {user_id}...")
    response = requests.get(f"{BASE_URL}/permissions/users/{user_id}/permissions", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            perm_data = data.get("data", {})
            print(f"✅ Successfully retrieved permissions!")
            print(f"   User: {perm_data.get('user_name', 'Unknown')}")
            print(f"   Role: {perm_data.get('role', {}).get('name', 'Unknown')}")
            print(f"   Total permissions: {perm_data.get('total_permissions', 0)}")
        else:
            print(f"❌ API returned success=false: {data}")
            return False
    else:
        print(f"❌ Failed to get user permissions: {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    
    # Test 3: Get role permissions (if role exists)
    if role_id:
        print(f"\n3. Getting permissions for role {role_id}...")
        response = requests.get(f"{BASE_URL}/permissions/roles/{role_id}/permissions", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                role_data = data.get("data", {})
                print(f"✅ Successfully retrieved role permissions!")
                print(f"   Role: {role_data.get('role_name', 'Unknown')}")
                print(f"   Total permissions: {role_data.get('total_permissions', 0)}")
                print(f"   Users with role: {role_data.get('users_with_role', 0)}")
            else:
                print(f"❌ API returned success=false: {data}")
                return False
        else:
            print(f"❌ Failed to get role permissions: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    else:
        print("\n3. Skipping role permissions test (no role assigned)")
    
    # Test 4: Check specific permissions
    print(f"\n4. Checking specific permissions for user {user_id}...")
    test_permissions = ["venue.read", "order.create", "user.update"]
    
    response = requests.post(
        f"{BASE_URL}/permissions/users/{user_id}/permissions/check",
        headers=headers,
        json=test_permissions
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            check_data = data.get("data", {})
            print(f"✅ Successfully checked permissions!")
            print(f"   Has all permissions: {check_data.get('has_all_permissions', False)}")
            print(f"   Has any permissions: {check_data.get('has_any_permissions', False)}")
            
            results = check_data.get('permission_results', {})
            for perm, has_perm in results.items():
                status = "✅" if has_perm else "❌"
                print(f"   {status} {perm}")
        else:
            print(f"❌ API returned success=false: {data}")
            return False
    else:
        print(f"❌ Failed to check permissions: {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    
    # Test 5: Get permissions summary
    print(f"\n5. Getting permissions summary for user {user_id}...")
    response = requests.get(f"{BASE_URL}/permissions/users/{user_id}/permissions/summary", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            summary_data = data.get("data", {})
            print(f"✅ Successfully retrieved permissions summary!")
            print(f"   Resources count: {summary_data.get('resources_count', 0)}")
            
            resources = summary_data.get('permissions_by_resource', [])
            for resource in resources[:3]:  # Show first 3 resources
                actions = resource.get('actions', [])
                print(f"   - {resource.get('resource', 'Unknown')}: {len(actions)} actions")
        else:
            print(f"❌ API returned success=false: {data}")
            return False
    else:
        print(f"❌ Failed to get permissions summary: {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    
    # Test 6: Validate access
    print(f"\n6. Validating access for user {user_id}...")
    access_data = {
        "user_id": user_id,
        "resource": "venue",
        "action": "read"
    }
    
    response = requests.post(
        f"{BASE_URL}/permissions/validate-access",
        headers=headers,
        json=access_data
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            access_result = data.get("data", {})
            has_access = access_result.get('has_access', False)
            access_type = access_result.get('access_type', 'none')
            
            status = "✅" if has_access else "❌"
            print(f"{status} Access validation completed!")
            print(f"   Has access: {has_access} (Type: {access_type})")
            print(f"   Permission: {access_result.get('permission_name', 'Unknown')}")
        else:
            print(f"❌ API returned success=false: {data}")
            return False
    else:
        print(f"❌ Failed to validate access: {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    
    print("\n" + "="*50)
    print("🎉 All permission endpoints are now OPEN and working!")
    print("✅ Any authenticated user can access permission data")
    return True

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python test_open_permission_endpoints.py <auth_token>")
        print("Example: python test_open_permission_endpoints.py eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
        sys.exit(1)
    
    auth_token = sys.argv[1]
    
    try:
        success = test_open_permission_endpoints(auth_token)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()