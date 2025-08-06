#!/usr/bin/env python3
"""
Populate test users directly in Firestore database
This script creates test users without requiring the server to be running
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime
from typing import Dict, Any

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def create_test_users():
    """Create test users directly in Firestore"""
    try:
        # Import after adding to path
        from app.database.firestore import get_user_repo
        from app.core.unified_password_security import password_handler
        
        print("🚀 POPULATING TEST USERS")
        print("=" * 50)
        
        user_repo = get_user_repo()
        
        # Check if users already exist
        existing_users = await user_repo.get_all()
        print(f"📊 Current users in database: {len(existing_users)}")
        
        if len(existing_users) >= 5:
            print("✅ Database already has sufficient users")
            return True
        
        # Test users data
        test_users = [
            {
                "email": "admin@dino.com",
                "phone": "+1234567890",
                "first_name": "Admin",
                "last_name": "User",
                "password": "admin123",
                "role_id": "admin_role",
                "venue_ids": []
            },
            {
                "email": "manager@dino.com", 
                "phone": "+1234567891",
                "first_name": "Manager",
                "last_name": "User",
                "password": "manager123",
                "role_id": "manager_role",
                "venue_ids": []
            },
            {
                "email": "operator@dino.com",
                "phone": "+1234567892", 
                "first_name": "Operator",
                "last_name": "User",
                "password": "operator123",
                "role_id": "operator_role",
                "venue_ids": []
            },
            {
                "email": "john.doe@example.com",
                "phone": "+1555000001",
                "first_name": "John",
                "last_name": "Doe", 
                "password": "password123",
                "role_id": "operator_role",
                "venue_ids": []
            },
            {
                "email": "jane.smith@example.com",
                "phone": "+1555000002",
                "first_name": "Jane",
                "last_name": "Smith",
                "password": "password123", 
                "role_id": "operator_role",
                "venue_ids": []
            }
        ]
        
        created_count = 0
        
        for i, user_data in enumerate(test_users, 1):
            try:
                print(f"\n📝 Creating user {i}: {user_data['email']}")
                
                # Check if user already exists
                existing_user = await user_repo.get_by_email(user_data['email'])
                if existing_user:
                    print(f"   ⚠️  User already exists: {user_data['email']}")
                    continue
                
                # Hash password
                hashed_password = password_handler.hash_password(user_data['password'])
                
                # Generate UUID for user
                user_id = str(uuid.uuid4())
                
                # Prepare user data for database
                db_user_data = {
                    'id': user_id,
                    'email': user_data['email'],
                    'phone': user_data['phone'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'hashed_password': hashed_password,
                    'role_id': user_data['role_id'],
                    'venue_ids': user_data['venue_ids'],
                    'is_active': True,
                    'is_verified': False,
                    'email_verified': False,
                    'phone_verified': False,
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
                
                # Create user in database
                created_user = await user_repo.create(db_user_data, doc_id=user_id)
                
                print(f"   ✅ Created: {user_data['email']} (ID: {user_id})")
                created_count += 1
                
            except Exception as e:
                print(f"   ❌ Error creating user {user_data['email']}: {e}")
                continue
        
        print(f"\n📊 SUMMARY")
        print(f"   Created: {created_count} new users")
        
        # Verify final count
        final_users = await user_repo.get_all()
        print(f"   Total users in database: {len(final_users)}")
        
        if len(final_users) > 0:
            print(f"\n👥 Sample users:")
            for i, user in enumerate(final_users[:3]):
                print(f"   {i+1}. {user.get('first_name')} {user.get('last_name')} ({user.get('email')})")
            if len(final_users) > 3:
                print(f"   ... and {len(final_users) - 3} more users")
        
        return True
        
    except Exception as e:
        print(f"❌ Error populating users: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_user_queries():
    """Test various user queries"""
    try:
        from app.database.firestore import get_user_repo
        
        print(f"\n🔍 TESTING USER QUERIES")
        print("=" * 30)
        
        user_repo = get_user_repo()
        
        # Test get_all
        all_users = await user_repo.get_all()
        print(f"✅ get_all(): {len(all_users)} users")
        
        # Test pagination simulation
        page_size = 10
        page = 1
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_users = all_users[start_idx:end_idx]
        
        total = len(all_users)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        print(f"✅ Pagination test:")
        print(f"   Total: {total}")
        print(f"   Page {page} of {total_pages}")
        print(f"   Users in page: {len(paginated_users)}")
        
        # Test specific queries
        if all_users:
            first_user = all_users[0]
            
            # Test get_by_id
            user_by_id = await user_repo.get_by_id(first_user['id'])
            print(f"✅ get_by_id(): {'Found' if user_by_id else 'Not found'}")
            
            # Test get_by_email
            user_by_email = await user_repo.get_by_email(first_user['email'])
            print(f"✅ get_by_email(): {'Found' if user_by_email else 'Not found'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing queries: {e}")
        return False

def main():
    """Main function"""
    print("🚀 DINO BACKEND - USER DATABASE SETUP")
    print("=" * 60)
    
    try:
        # Run async functions
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Create test users
        success = loop.run_until_complete(create_test_users())
        
        if success:
            # Test queries
            loop.run_until_complete(test_user_queries())
            
            print(f"\n🎉 SUCCESS!")
            print("   Test users have been created in the database.")
            print("   The GET /users endpoint should now return data.")
            print(f"\n💡 Next steps:")
            print("   1. Start the server: uvicorn app.main:app --reload")
            print("   2. Test the endpoint: GET {{api_base_url}}/users/?page=1&page_size=10")
            
            return True
        else:
            print(f"\n💥 FAILED!")
            print("   Could not create test users.")
            return False
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'loop' in locals():
            loop.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)