#!/usr/bin/env python3
"""
Test script for the GET /users endpoint
"""

import requests
import json
import sys

def test_users_endpoint(auth_token=None):
    """Test the GET /users endpoint"""
    
    url = "http://localhost:8000/api/v1/users"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    # Add auth token if provided
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    # Test parameters
    params = {
        "page": 1,
        "page_size": 10
    }
    
    print("🔍 Testing GET /users Endpoint")
    print("="*40)
    print(f"URL: {url}")
    print(f"Params: {params}")
    print(f"Headers: {headers}")
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success! Users endpoint is working")
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Show summary
            if data.get("success"):
                users = data.get("data", [])
                total = data.get("total", 0)
                print(f"\n📊 Summary:")
                print(f"   Total users: {total}")
                print(f"   Users in this page: {len(users)}")
                print(f"   Page: {data.get('page', 1)}")
                print(f"   Page size: {data.get('page_size', 10)}")
                
                if users:
                    print(f"\n👥 Sample users:")
                    for i, user in enumerate(users[:3]):  # Show first 3 users
                        print(f"   {i+1}. {user.get('first_name', '')} {user.get('last_name', '')} ({user.get('email', 'No email')})")
                    if len(users) > 3:
                        print(f"   ... and {len(users) - 3} more users")
            
            return True
            
        elif response.status_code == 404:
            print("❌ 404 Not Found - Endpoint might not be registered properly")
            print("   Check if the server is running and the endpoint is available")
            return False
            
        elif response.status_code == 401:
            print("❌ 401 Unauthorized - Authentication required")
            print("   Try providing a valid auth token")
            return False
            
        elif response.status_code == 403:
            print("❌ 403 Forbidden - Access denied")
            print("   User might not have sufficient privileges")
            return False
            
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Response text: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error - Is the server running on localhost:8000?")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {e}")
        print(f"Response text: {response.text}")
        return False

def main():
    print("🚀 Testing Users Endpoint")
    print("="*50)
    
    # Test without auth token first
    print("\n1. Testing without authentication...")
    success_no_auth = test_users_endpoint()
    
    # Test with auth token if provided
    if len(sys.argv) > 1:
        auth_token = sys.argv[1]
        print("\n2. Testing with authentication...")
        success_with_auth = test_users_endpoint(auth_token)
    else:
        print("\n💡 To test with authentication, provide token as argument:")
        print("   python test_users_endpoint.py YOUR_AUTH_TOKEN")
        success_with_auth = None
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    if success_no_auth:
        print("✅ Endpoint works without authentication")
    else:
        print("❌ Endpoint failed without authentication")
    
    if success_with_auth is not None:
        if success_with_auth:
            print("✅ Endpoint works with authentication")
        else:
            print("❌ Endpoint failed with authentication")
    
    # Overall result
    if success_no_auth or success_with_auth:
        print("\n🎉 Users endpoint is accessible!")
        return True
    else:
        print("\n💥 Users endpoint is not working")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)