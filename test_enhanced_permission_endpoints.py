#!/usr/bin/env python3
"""
Enhanced Permission Endpoints Test Script
Tests the improved permission endpoints with proper authorization
"""

import requests
import json
import sys
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json"}

class PermissionEndpointTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.headers = HEADERS.copy()
        self.auth_token = None
        self.test_user_id = None
        self.test_role_id = None
        
    def set_auth_token(self, token: str):
        """Set authentication token"""
        self.auth_token = token
        self.headers["Authorization"] = f"Bearer {token}"
        
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            return {
                "status_code": response.status_code,
                "data": response.json() if response.content else {},
                "success": 200 <= response.status_code < 300
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "status_code": 0,
                "data": {"error": str(e)},
                "success": False
            }
        except json.JSONDecodeError:
            return {
                "status_code": response.status_code,
                "data": {"error": "Invalid JSON response"},
                "success": False
            }
    
    def test_get_user_permissions(self, user_id: str) -> Dict[str, Any]:
        """Test GET /permissions/users/{user_id}/permissions"""
        print(f"\n🔍 Testing GET /permissions/users/{user_id}/permissions")
        
        result = self.make_request("GET", f"/permissions/users/{user_id}/permissions")
        
        if result["success"]:
            data = result["data"].get("data", {})
            print(f"✅ Success: Retrieved permissions for user {data.get('user_name', user_id)}")
            print(f"   Role: {data.get('role', {}).get('name', 'Unknown')}")
            print(f"   Total permissions: {data.get('total_permissions', 0)}")
            
            # Show first few permissions
            permissions = data.get('permissions', [])
            if permissions:
                print("   Sample permissions:")
                for perm in permissions[:3]:
                    print(f"     - {perm.get('name', 'Unknown')}: {perm.get('description', 'No description')}")
                if len(permissions) > 3:
                    print(f"     ... and {len(permissions) - 3} more")
        else:
            print(f"❌ Failed: {result['data'].get('detail', 'Unknown error')}")
            
        return result
    
    def test_get_role_permissions(self, role_id: str) -> Dict[str, Any]:
        """Test GET /permissions/roles/{role_id}/permissions"""
        print(f"\n🔍 Testing GET /permissions/roles/{role_id}/permissions")
        
        result = self.make_request("GET", f"/permissions/roles/{role_id}/permissions")
        
        if result["success"]:
            data = result["data"].get("data", {})
            print(f"✅ Success: Retrieved permissions for role {data.get('role_name', role_id)}")
            print(f"   Description: {data.get('role_description', 'No description')}")
            print(f"   Total permissions: {data.get('total_permissions', 0)}")
            print(f"   Users with this role: {data.get('users_with_role', 0)}")
            
            # Show first few permissions
            permissions = data.get('permissions', [])
            if permissions:
                print("   Sample permissions:")
                for perm in permissions[:3]:
                    print(f"     - {perm.get('name', 'Unknown')}: {perm.get('description', 'No description')}")
                if len(permissions) > 3:
                    print(f"     ... and {len(permissions) - 3} more")
        else:
            print(f"❌ Failed: {result['data'].get('detail', 'Unknown error')}")
            
        return result
    
    def test_check_user_permissions(self, user_id: str, permission_names: list) -> Dict[str, Any]:
        """Test POST /permissions/users/{user_id}/permissions/check"""
        print(f"\n🔍 Testing POST /permissions/users/{user_id}/permissions/check")
        print(f"   Checking permissions: {permission_names}")
        
        result = self.make_request("POST", f"/permissions/users/{user_id}/permissions/check", permission_names)
        
        if result["success"]:
            data = result["data"].get("data", {})
            print(f"✅ Success: Permission check completed for {data.get('user_name', user_id)}")
            print(f"   Has all permissions: {data.get('has_all_permissions', False)}")
            print(f"   Has any permissions: {data.get('has_any_permissions', False)}")
            
            perm_results = data.get('permission_results', {})
            for perm, has_perm in perm_results.items():
                status = "✅" if has_perm else "❌"
                print(f"   {status} {perm}")
                
            missing = data.get('missing_permissions', [])
            if missing:
                print(f"   Missing: {', '.join(missing)}")
        else:
            print(f"❌ Failed: {result['data'].get('detail', 'Unknown error')}")
            
        return result
    
    def test_get_user_permissions_summary(self, user_id: str) -> Dict[str, Any]:
        """Test GET /permissions/users/{user_id}/permissions/summary"""
        print(f"\n🔍 Testing GET /permissions/users/{user_id}/permissions/summary")
        
        result = self.make_request("GET", f"/permissions/users/{user_id}/permissions/summary")
        
        if result["success"]:
            data = result["data"].get("data", {})
            print(f"✅ Success: Retrieved permissions summary for {data.get('user_name', user_id)}")
            print(f"   Total permissions: {data.get('total_permissions', 0)}")
            print(f"   Resources count: {data.get('resources_count', 0)}")
            
            resources = data.get('permissions_by_resource', [])
            if resources:
                print("   Resources:")
                for resource in resources[:3]:
                    actions = resource.get('actions', [])
                    print(f"     - {resource.get('resource', 'Unknown')}: {len(actions)} actions ({', '.join(actions[:3])}{'...' if len(actions) > 3 else ''})")
                if len(resources) > 3:
                    print(f"     ... and {len(resources) - 3} more resources")
        else:
            print(f"❌ Failed: {result['data'].get('detail', 'Unknown error')}")
            
        return result
    
    def test_get_role_permissions_summary(self, role_id: str) -> Dict[str, Any]:
        """Test GET /permissions/roles/{role_id}/permissions/summary"""
        print(f"\n🔍 Testing GET /permissions/roles/{role_id}/permissions/summary")
        
        result = self.make_request("GET", f"/permissions/roles/{role_id}/permissions/summary")
        
        if result["success"]:
            data = result["data"].get("data", {})
            print(f"✅ Success: Retrieved permissions summary for role {data.get('role_name', role_id)}")
            print(f"   Total permissions: {data.get('total_permissions', 0)}")
            print(f"   Resources count: {data.get('resources_count', 0)}")
            print(f"   Users with this role: {data.get('users_with_role', 0)}")
            
            resources = data.get('permissions_by_resource', [])
            if resources:
                print("   Resources:")
                for resource in resources[:3]:
                    actions = resource.get('actions', [])
                    print(f"     - {resource.get('resource', 'Unknown')}: {len(actions)} actions ({', '.join(actions[:3])}{'...' if len(actions) > 3 else ''})")
                if len(resources) > 3:
                    print(f"     ... and {len(resources) - 3} more resources")
        else:
            print(f"❌ Failed: {result['data'].get('detail', 'Unknown error')}")
            
        return result
    
    def test_validate_user_access(self, user_id: str, resource: str, action: str) -> Dict[str, Any]:
        """Test POST /permissions/validate-access"""
        print(f"\n🔍 Testing POST /permissions/validate-access")
        print(f"   User: {user_id}, Resource: {resource}, Action: {action}")
        
        data = {
            "user_id": user_id,
            "resource": resource,
            "action": action
        }
        
        result = self.make_request("POST", "/permissions/validate-access", data)
        
        if result["success"]:
            response_data = result["data"].get("data", {})
            has_access = response_data.get('has_access', False)
            access_type = response_data.get('access_type', 'none')
            
            status = "✅" if has_access else "❌"
            print(f"{status} Access: {has_access} (Type: {access_type})")
            print(f"   User: {response_data.get('user_name', user_id)}")
            print(f"   Permission: {response_data.get('permission_name', 'Unknown')}")
            
            matching = response_data.get('matching_permissions', [])
            if matching:
                print(f"   Matching permissions: {len(matching)}")
                for perm in matching[:2]:
                    print(f"     - {perm.get('name', 'Unknown')}")
        else:
            print(f"❌ Failed: {result['data'].get('detail', 'Unknown error')}")
            
        return result
    
    def test_authorization_scenarios(self):
        """Test various authorization scenarios"""
        print("\n" + "="*60)
        print("🔐 TESTING AUTHORIZATION SCENARIOS")
        print("="*60)
        
        # Test unauthorized access (no token)
        print("\n🔍 Testing unauthorized access (no token)")
        original_headers = self.headers.copy()
        self.headers = {"Content-Type": "application/json"}  # Remove auth header
        
        result = self.make_request("GET", "/permissions/users/test-user/permissions")
        if result["status_code"] == 401:
            print("✅ Correctly rejected unauthorized request")
        else:
            print(f"❌ Expected 401, got {result['status_code']}")
        
        # Restore headers
        self.headers = original_headers
        
        # Test accessing other user's permissions (should fail for non-admin)
        print("\n🔍 Testing access to other user's permissions")
        result = self.make_request("GET", "/permissions/users/different-user-id/permissions")
        if result["status_code"] == 403:
            print("✅ Correctly rejected access to other user's permissions")
        elif result["status_code"] == 404:
            print("✅ User not found (expected for test)")
        else:
            print(f"❌ Unexpected response: {result['status_code']}")
    
    def get_test_data(self):
        """Get test user and role IDs from the system"""
        print("\n🔍 Getting test data...")
        
        # Try to get current user info
        result = self.make_request("GET", "/users/profile")
        if result["success"]:
            user_data = result["data"]
            self.test_user_id = user_data.get("id")
            print(f"✅ Found current user: {user_data.get('first_name', '')} {user_data.get('last_name', '')} (ID: {self.test_user_id})")
            
            # Get role ID
            role_id = user_data.get("role_id")
            if role_id:
                self.test_role_id = role_id
                print(f"✅ Found user role ID: {role_id}")
            else:
                print("⚠️  User has no role assigned")
        else:
            print("❌ Could not get current user info")
            
        # Try to get roles list
        result = self.make_request("GET", "/roles?page_size=5")
        if result["success"]:
            roles = result["data"].get("data", [])
            if roles and not self.test_role_id:
                self.test_role_id = roles[0].get("id")
                print(f"✅ Found test role: {roles[0].get('name', 'Unknown')} (ID: {self.test_role_id})")
        
        return self.test_user_id, self.test_role_id
    
    def run_comprehensive_test(self):
        """Run comprehensive test suite"""
        print("🚀 ENHANCED PERMISSION ENDPOINTS TEST SUITE")
        print("="*60)
        
        # Get test data
        user_id, role_id = self.get_test_data()
        
        if not user_id:
            print("❌ Cannot run tests without user ID")
            return False
        
        success_count = 0
        total_tests = 0
        
        # Test 1: Get user permissions
        total_tests += 1
        result = self.test_get_user_permissions(user_id)
        if result["success"]:
            success_count += 1
        
        # Test 2: Get role permissions (if role available)
        if role_id:
            total_tests += 1
            result = self.test_get_role_permissions(role_id)
            if result["success"]:
                success_count += 1
        
        # Test 3: Check specific permissions
        total_tests += 1
        test_permissions = ["venue.read", "order.create", "user.update", "nonexistent.permission"]
        result = self.test_check_user_permissions(user_id, test_permissions)
        if result["success"]:
            success_count += 1
        
        # Test 4: Get user permissions summary
        total_tests += 1
        result = self.test_get_user_permissions_summary(user_id)
        if result["success"]:
            success_count += 1
        
        # Test 5: Get role permissions summary (if role available)
        if role_id:
            total_tests += 1
            result = self.test_get_role_permissions_summary(role_id)
            if result["success"]:
                success_count += 1
        
        # Test 6: Validate user access
        total_tests += 1
        result = self.test_validate_user_access(user_id, "venue", "read")
        if result["success"]:
            success_count += 1
        
        # Test 7: Authorization scenarios
        self.test_authorization_scenarios()
        
        # Summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        print(f"✅ Successful tests: {success_count}/{total_tests}")
        print(f"📈 Success rate: {(success_count/total_tests)*100:.1f}%")
        
        if success_count == total_tests:
            print("🎉 All tests passed!")
            return True
        else:
            print("⚠️  Some tests failed. Check the output above for details.")
            return False

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python test_enhanced_permission_endpoints.py <auth_token>")
        print("Example: python test_enhanced_permission_endpoints.py eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
        sys.exit(1)
    
    auth_token = sys.argv[1]
    
    # Initialize tester
    tester = PermissionEndpointTester()
    tester.set_auth_token(auth_token)
    
    # Run tests
    success = tester.run_comprehensive_test()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()