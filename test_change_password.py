#!/usr/bin/env python3
"""
Test script for the change-password endpoint
"""

import requests
import json
import sys

def test_change_password(auth_token, current_password, new_password):
    """Test the change password endpoint"""
    
    url = "http://localhost:8000/api/v1/users/change-password"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }
    
    # Request body - FastAPI will extract these parameters
    data = {
        "current_password": current_password,
        "new_password": new_password
    }
    
    print("🔐 Testing Change Password Endpoint")
    print("="*40)
    print(f"URL: {url}")
    print(f"Request Body: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("success"):
                print("✅ Password changed successfully!")
                return True
            else:
                print("❌ Password change failed (API returned success=false)")
                return False
        else:
            print(f"❌ Password change failed with status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {e}")
        return False

def main():
    if len(sys.argv) < 4:
        print("Usage: python test_change_password.py <auth_token> <current_password> <new_password>")
        print("Example: python test_change_password.py eyJhbGciOiJIUzI1... oldpass123 newpass456")
        sys.exit(1)
    
    auth_token = sys.argv[1]
    current_password = sys.argv[2]
    new_password = sys.argv[3]
    
    success = test_change_password(auth_token, current_password, new_password)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()