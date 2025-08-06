#!/usr/bin/env python3
"""
Diagnostic script to check the users endpoint availability
"""

import requests
import json
import sys

def test_endpoint(url, description, headers=None):
    """Test an endpoint and return results"""
    print(f"\n🔍 Testing: {description}")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=headers or {}, timeout=10)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS")
            try:
                data = response.json()
                if isinstance(data, dict):
                    print(f"Response keys: {list(data.keys())}")
                else:
                    print(f"Response type: {type(data)}")
            except:
                print("Response is not JSON")
        elif response.status_code == 404:
            print("❌ NOT FOUND - Endpoint not registered or server issue")
        elif response.status_code == 401:
            print("🔐 UNAUTHORIZED - Authentication required")
        elif response.status_code == 403:
            print("🚫 FORBIDDEN - Access denied")
        else:
            print(f"⚠️  UNEXPECTED STATUS: {response.status_code}")
        
        print(f"Response: {response.text[:200]}...")
        return response.status_code
        
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR - Server not running?")
        return 0
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT - Server not responding")
        return 0
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return 0

def main():
    base_url = "http://localhost:8000"
    
    print("🚀 USERS ENDPOINT DIAGNOSTIC")
    print("=" * 50)
    
    # Test 1: Health check
    health_status = test_endpoint(f"{base_url}/api/v1/health", "Health Check")
    
    if health_status == 0:
        print("\n💥 Server is not running or not accessible!")
        print("Please start the server with:")
        print("python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return False
    
    # Test 2: API docs
    docs_status = test_endpoint(f"{base_url}/docs", "API Documentation")
    
    # Test 3: Users profile (should work)
    profile_status = test_endpoint(f"{base_url}/api/v1/users/profile", "Users Profile (requires auth)")
    
    # Test 4: Users list without auth
    list_status = test_endpoint(f"{base_url}/api/v1/users", "Users List (no params)")
    
    # Test 5: Users list with params
    params_status = test_endpoint(f"{base_url}/api/v1/users?page=1&page_size=10", "Users List (with params)")
    
    # Test 6: Users register (should work)
    register_status = test_endpoint(f"{base_url}/api/v1/users/register", "Users Register")
    
    # Test 7: Check if it's a method issue
    print(f"\n🔍 Testing: POST to users endpoint")
    try:
        response = requests.post(f"{base_url}/api/v1/users", 
                               headers={"Content-Type": "application/json"},
                               json={"test": "data"},
                               timeout=10)
        print(f"POST Status: {response.status_code}")
        if response.status_code != 404:
            print("✅ POST endpoint exists (even if it fails validation)")
        else:
            print("❌ POST endpoint also returns 404")
    except Exception as e:
        print(f"POST Error: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    if health_status == 200:
        print("✅ Server is running")
    else:
        print("❌ Server health check failed")
    
    if list_status == 404 and params_status == 404:
        print("❌ Users GET endpoint not found")
        print("\n🔧 POSSIBLE SOLUTIONS:")
        print("1. Restart the server:")
        print("   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print("2. Check if the endpoint is registered in app/api/v1/api.py")
        print("3. Check for syntax errors in app/api/v1/endpoints/user.py")
        print("4. Check server logs for errors")
        return False
    elif list_status == 401 or params_status == 401:
        print("🔐 Users endpoint requires authentication")
        print("\n💡 Try with an auth token:")
        print("curl -H 'Authorization: Bearer YOUR_TOKEN' 'http://localhost:8000/api/v1/users?page=1&page_size=10'")
        return True
    elif list_status == 200 or params_status == 200:
        print("✅ Users endpoint is working!")
        return True
    else:
        print("⚠️  Users endpoint has issues but server is running")
        return False

if __name__ == "__main__":
    success = main()
    
    if not success:
        print("\n🔧 NEXT STEPS:")
        print("1. Check server logs for errors")
        print("2. Restart the server")
        print("3. Visit http://localhost:8000/docs to see available endpoints")
    
    sys.exit(0 if success else 1)