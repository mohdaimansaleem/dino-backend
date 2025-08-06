#!/usr/bin/env python3
"""
Test the users API endpoint
"""

import requests
import json
import sys
from typing import Optional

def test_users_endpoint(base_url: str = "http://localhost:8000", auth_token: Optional[str] = None):
    """Test the GET /users endpoint"""
    
    url = f"{base_url}/api/v1/users/"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    params = {
        "page": 1,
        "page_size": 10
    }
    
    print("🔍 TESTING USERS ENDPOINT")
    print("=" * 40)
    print(f"URL: {url}")
    print(f"Params: {params}")
    print(f"Auth: {'Yes' if auth_token else 'No'}")
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        print(f"\n📊 RESPONSE")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS!")
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Analyze response
            success = data.get("success", False)
            total = data.get("total", 0)
            users = data.get("data", [])
            page = data.get("page", 1)
            page_size = data.get("page_size", 10)
            total_pages = data.get("total_pages", 0)
            has_next = data.get("has_next", False)
            has_prev = data.get("has_prev", False)
            
            print(f"\n📈 ANALYSIS")
            print(f"Success: {success}")
            print(f"Total users: {total}")
            print(f"Users in this page: {len(users)}")
            print(f"Page: {page}")
            print(f"Page size: {page_size}")
            print(f"Total pages: {total_pages}")
            print(f"Has next: {has_next}")
            print(f"Has previous: {has_prev}")
            
            if users:
                print(f"\n👥 SAMPLE USERS")
                for i, user in enumerate(users[:3]):
                    print(f"   {i+1}. {user.get('first_name', '')} {user.get('last_name', '')} ({user.get('email', 'No email')})")
                    print(f"      ID: {user.get('id', 'No ID')}")
                    print(f"      Phone: {user.get('phone', 'No phone')}")
                    print(f"      Role: {user.get('role_id', 'No role')}")
                    print(f"      Active: {user.get('is_active', 'Unknown')}")
                if len(users) > 3:
                    print(f"   ... and {len(users) - 3} more users")
            else:
                print(f"\n⚠️  NO USERS FOUND")
                print("   The database might be empty.")
                print("   Run: python3 populate_test_users.py")
            
            return True
            
        elif response.status_code == 401:
            print("❌ UNAUTHORIZED (401)")
            print("   Authentication required")
            try:
                error_data = response.json()
                print(f"   Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   Response: {response.text}")
            return False
            
        elif response.status_code == 403:
            print("❌ FORBIDDEN (403)")
            print("   Access denied")
            try:
                error_data = response.json()
                print(f"   Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   Response: {response.text}")
            return False
            
        elif response.status_code == 404:
            print("❌ NOT FOUND (404)")
            print("   Endpoint not found")
            print(f"   Response: {response.text}")
            return False
            
        else:
            print(f"❌ UNEXPECTED STATUS: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR")
        print("   Server is not running or not accessible")
        print("   Start server: uvicorn app.main:app --reload")
        return False
        
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT ERROR")
        print("   Request timed out")
        return False
        
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

def test_user_registration():
    """Test user registration endpoint"""
    
    url = "http://localhost:8000/api/v1/users/register"
    
    user_data = {
        "email": f"testuser_{int(__import__('time').time())}@example.com",
        "phone": f"+155500{int(__import__('time').time()) % 10000:04d}",
        "first_name": "Test",
        "last_name": "User",
        "password": "testpassword123"
    }
    
    headers = {"Content-Type": "application/json"}
    
    print(f"\n🔍 TESTING USER REGISTRATION")
    print("=" * 40)
    print(f"URL: {url}")
    print(f"Data: {json.dumps({k: v if k != 'password' else '***' for k, v in user_data.items()}, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=user_data, timeout=10)
        
        print(f"\n📊 RESPONSE")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print("✅ REGISTRATION SUCCESS!")
            print(f"Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ REGISTRATION FAILED")
            try:
                error_data = response.json()
                print(f"   Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ REGISTRATION ERROR: {e}")
        return False

def main():
    """Main function"""
    print("🚀 DINO BACKEND - USERS API TEST")
    print("=" * 60)
    
    # Test 1: Users endpoint without auth
    print("\n1️⃣  Testing GET /users (no auth)")
    success_no_auth = test_users_endpoint()
    
    # Test 2: User registration
    print("\n2️⃣  Testing user registration")
    reg_success = test_user_registration()
    
    # Test 3: Users endpoint again (should have more users now)
    if reg_success:
        print("\n3️⃣  Testing GET /users again (after registration)")
        success_after_reg = test_users_endpoint()
    else:
        success_after_reg = False
    
    # Test 4: With auth token if provided
    auth_token = None
    if len(sys.argv) > 1:
        auth_token = sys.argv[1]
        print(f"\n4️⃣  Testing GET /users (with auth)")
        success_with_auth = test_users_endpoint(auth_token=auth_token)
    else:
        print(f"\n💡 To test with auth token:")
        print("   python3 test_users_api.py YOUR_AUTH_TOKEN")
        success_with_auth = None
    
    # Summary
    print(f"\n📊 TEST SUMMARY")
    print("=" * 30)
    print(f"GET /users (no auth): {'✅' if success_no_auth else '❌'}")
    print(f"User registration: {'✅' if reg_success else '❌'}")
    print(f"GET /users (after reg): {'✅' if success_after_reg else '❌'}")
    if success_with_auth is not None:
        print(f"GET /users (with auth): {'✅' if success_with_auth else '❌'}")
    
    overall_success = success_no_auth or success_after_reg
    
    if overall_success:
        print(f"\n🎉 USERS ENDPOINT IS WORKING!")
    else:
        print(f"\n💥 USERS ENDPOINT HAS ISSUES")
        print(f"\n🔧 TROUBLESHOOTING:")
        print("   1. Make sure server is running: uvicorn app.main:app --reload")
        print("   2. Populate test data: python3 populate_test_users.py")
        print("   3. Check server logs for errors")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)