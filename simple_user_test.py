#!/usr/bin/env python3
"""
Simple test for users endpoint - works without database setup
"""

import requests
import json
import time

def test_endpoint(url, description):
    """Test an endpoint and return result"""
    print(f"🔍 {description}")
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, timeout=5)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            total = data.get('total', 0)
            users_count = len(data.get('data', []))
            print(f"   ✅ Success! Total: {total}, In page: {users_count}")
            return True, data
        else:
            print(f"   ❌ Failed: {response.status_code}")
            return False, None
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection failed - server not running")
        return False, None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, None

def create_user_via_api(email, phone, first_name, last_name, password):
    """Create user via registration API"""
    url = "http://localhost:8000/api/v1/users/register"
    
    user_data = {
        "email": email,
        "phone": phone,
        "first_name": first_name,
        "last_name": last_name,
        "password": password
    }
    
    print(f"📝 Creating user: {email}")
    
    try:
        response = requests.post(url, json=user_data, timeout=10)
        
        if response.status_code == 201:
            print(f"   ✅ Created: {email}")
            return True
        else:
            print(f"   ❌ Failed: {response.status_code}")
            try:
                error = response.json()
                print(f"   Error: {error.get('detail', 'Unknown error')}")
            except:
                print(f"   Response: {response.text[:100]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("🚀 SIMPLE USERS ENDPOINT TEST")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    users_url = f"{base_url}/api/v1/users/?page=1&page_size=10"
    
    # Test 1: Check current state
    print("\n1️⃣  Testing current endpoint state...")
    success, data = test_endpoint(users_url, "GET /users")
    
    if not success:
        print("\n💥 Server is not running or endpoint is broken!")
        print("   Start server: uvicorn app.main:app --reload")
        return False
    
    initial_total = data.get('total', 0) if data else 0
    print(f"   Current users in database: {initial_total}")
    
    # Test 2: Create users if database is empty
    if initial_total == 0:
        print(f"\n2️⃣  Database is empty. Creating test users...")
        
        test_users = [
            ("admin@dino.com", "+1234567890", "Admin", "User", "admin123"),
            ("test@example.com", "+1555000001", "Test", "User", "test123"),
        ]
        
        created_count = 0
        for email, phone, first_name, last_name, password in test_users:
            if create_user_via_api(email, phone, first_name, last_name, password):
                created_count += 1
                time.sleep(1)  # Small delay between requests
        
        print(f"\n   Created {created_count} users")
        
        # Test 3: Check endpoint again
        print(f"\n3️⃣  Testing endpoint after user creation...")
        success, data = test_endpoint(users_url, "GET /users (after creation)")
        
        if success and data:
            final_total = data.get('total', 0)
            print(f"   Final users in database: {final_total}")
            
            if final_total > 0:
                print(f"\n🎉 SUCCESS! Endpoint now returns {final_total} users")
                
                # Show sample data
                users = data.get('data', [])
                if users:
                    print(f"\n👥 Sample users:")
                    for i, user in enumerate(users[:2]):
                        print(f"   {i+1}. {user.get('first_name')} {user.get('last_name')} ({user.get('email')})")
                
                return True
            else:
                print(f"\n⚠️  Still no users returned. Check server logs.")
                return False
        else:
            print(f"\n💥 Endpoint still not working after user creation")
            return False
    
    else:
        print(f"\n✅ Database already has {initial_total} users!")
        
        # Show sample data
        users = data.get('data', [])
        if users:
            print(f"\n👥 Sample users:")
            for i, user in enumerate(users[:3]):
                print(f"   {i+1}. {user.get('first_name')} {user.get('last_name')} ({user.get('email')})")
        
        return True

if __name__ == "__main__":
    success = main()
    
    if success:
        print(f"\n✅ USERS ENDPOINT IS WORKING!")
        print(f"\n💡 Test commands:")
        print(f"   curl 'http://localhost:8000/api/v1/users/?page=1&page_size=10'")
        print(f"   curl 'http://localhost:8000/api/v1/users/?search