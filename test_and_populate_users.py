#!/usr/bin/env python3
"""
Test the users endpoint and populate with test data if empty
"""

import requests
import json
import sys
import uuid

def test_users_endpoint():
    """Test the GET /users endpoint"""
    print("🔍 Testing GET /users endpoint...")
    
    url = "http://localhost:8000/api/v1/users/?page=1&page_size=10"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Endpoint working! Status: {response.status_code}")
            print(f"   Success: {data.get('success', False)}")
            print(f"   Total users: {data.get('total', 0)}")
            print(f"   Users in response: {len(data.get('data', []))}")
            
            if data.get('total', 0) > 0:
                print("   Sample users:")
                for i, user in enumerate(data.get('data', [])[:3]):
                    print(f"     {i+1}. {user.get('first_name', '')} {user.get('last_name', '')} ({user.get('email', 'No email')})")
            
            return data.get('total', 0)
        else:
            print(f"❌ Endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return -1
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return -1

def create_test_user(index):
    """Create a test user"""
    print(f"📝 Creating test user {index}...")
    
    url = "http://localhost:8000/api/v1/users/register"
    
    # Generate unique data
    unique_id = uuid.uuid4().hex[:8]
    
    user_data = {
        "email": f"testuser{index}_{unique_id}@example.com",
        "phone": f"555000{index:04d}",
        "first_name": f"Test{index}",
        "last_name": f"User{index}",
        "password": "testpassword123"
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, headers=headers, json=user_data, timeout=10)
        
        if response.status_code == 201:
            result = response.json()
            user = result.get("user", {})
            print(f"✅ User {index} created: {user.get('email')} (ID: {user.get('id')})")
            return True
        else:
            print(f"❌ Failed to create user {index}: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating user {index}: {e}")
        return False

def create_test_user_via_post(index, auth_token=None):
    """Create a test user via POST /users endpoint"""
    print(f"📝 Creating test user {index} via POST /users...")
    
    url = "http://localhost:8000/api/v1/users/"
    
    # Generate unique data
    unique_id = uuid.uuid4().hex[:8]
    
    user_data = {
        "email": f"postuser{index}_{unique_id}@example.com",
        "phone": f"666000{index:04d}",
        "first_name": f"Post{index}",
        "last_name": f"User{index}",
        "password": "testpassword123",
        "role_id": "default_role_id",  # This might need to be a real role ID
        "venue_ids": []
    }
    
    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    try:
        response = requests.post(url, headers=headers, json=user_data, timeout=10)
        
        if response.status_code == 201:
            result = response.json()
            user = result.get("data", {})
            print(f"✅ User {index} created via POST: {user.get('email')} (ID: {user.get('id')})")
            return True
        else:
            print(f"❌ Failed to create user {index} via POST: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating user {index} via POST: {e}")
        return False

def get_available_role():
    """Get an available role ID"""
    print("🔍 Getting available roles...")
    
    url = "http://localhost:8000/api/v1/roles?page_size=5"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            roles = data.get('data', [])
            if roles:
                role = roles[0]
                print(f"✅ Found role: {role.get('name')} (ID: {role.get('id')})")
                return role.get('id')
        
        print("⚠️  No roles found, will use default")
        return "default_role_id"
        
    except Exception as e:
        print(f"⚠️  Error getting roles: {e}, will use default")
        return "default_role_id"

def main():
    print("🚀 USERS ENDPOINT TEST & POPULATION")
    print("=" * 50)
    
    # Test 1: Check current users
    user_count = test_users_endpoint()
    
    if user_count == -1:
        print("\n💥 Endpoint is not working! Please check server status.")
        return False
    
    if user_count == 0:
        print(f"\n📝 Database is empty. Creating test users...")
        
        # Get a valid role ID
        role_id = get_available_role()
        
        # Create test users via register endpoint
        created_count = 0
        for i in range(1, 4):  # Create 3 test users
            if create_test_user(i):
                created_count += 1
        
        print(f"\n✅ Created {created_count} users via register endpoint")
        
        # Test again
        print(f"\n🔍 Testing endpoint again after creating users...")
        user_count = test_users_endpoint()
        
        if user_count > 0:
            print(f"\n🎉 Success! Endpoint now returns {user_count} users")
            return True
        else:
            print(f"\n⚠️  Still no users returned. There might be an issue with the query.")
            return False
    
    else:
        print(f"\n✅ Database has {user_count} users. Endpoint is working correctly!")
        return True

if __name__ == "__main__":
    success = main()
    
    if not success:
        print("\n🔧 TROUBLESHOOTING TIPS:")
        print("1. Check if the server is running")
        print("2. Check server logs for errors")
        print("3. Verify database connection")
        print("4. Check if users collection exists in Firestore")
    
    sys.exit(0 if success else 1)