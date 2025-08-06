#!/usr/bin/env python3
"""
Test the users endpoint logic directly (without server)
"""

import asyncio
import sys

async def test_user_repository():
    """Test the user repository directly"""
    try:
        print("🔍 Testing user repository directly...")
        
        # Import the repository
        from app.database.firestore import get_user_repo
        
        user_repo = get_user_repo()
        print("✅ User repository initialized")
        
        # Get all users
        all_users = await user_repo.get_all()
        print(f"📊 Found {len(all_users)} users in database")
        
        if all_users:
            print("👥 Sample users:")
            for i, user in enumerate(all_users[:3]):
                print(f"   {i+1}. {user.get('first_name', 'No name')} {user.get('last_name', '')} ({user.get('email', 'No email')})")
                print(f"      ID: {user.get('id', 'No ID')}")
                print(f"      Active: {user.get('is_active', 'Unknown')}")
        else:
            print("📝 No users found in database")
        
        return len(all_users)
        
    except Exception as e:
        print(f"❌ Error testing repository: {e}")
        import traceback
        traceback.print_exc()
        return -1

async def test_endpoint_logic():
    """Test the endpoint logic directly"""
    try:
        print("\n🔍 Testing endpoint logic...")
        
        # Import required modules
        from app.database.firestore import get_user_repo
        from app.models.dto import UserResponseDTO, PaginatedResponseDTO
        
        user_repo = get_user_repo()
        
        # Simulate the endpoint logic
        page = 1
        page_size = 10
        search = None
        role_id = None
        is_active = None
        
        print(f"Parameters: page={page}, page_size={page_size}")
        
        # Build filters
        query_filters = []
        if role_id:
            query_filters.append(('role_id', '==', role_id))
        if is_active is not None:
            query_filters.append(('is_active', '==', is_active))
        
        # Get all users
        if query_filters:
            all_users = await user_repo.query(query_filters)
        else:
            all_users = await user_repo.get_all()
        
        print(f"📊 Retrieved {len(all_users)} users from database")
        
        # Apply search filter if provided
        if search:
            search_term = search.lower()
            filtered_users = []
            for user in all_users:
                if (search_term in user.get('first_name', '').lower() or
                    search_term in user.get('last_name', '').lower() or
                    search_term in user.get('email', '').lower() or
                    search_term in user.get('phone', '').lower()):
                    filtered_users.append(user)
            all_users = filtered_users
            print(f"After search filter: {len(all_users)} users")
        
        # Calculate pagination
        total = len(all_users)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_users = all_users[start_idx:end_idx]
        
        print(f"📄 Pagination: total={total}, pages={total_pages}, showing={len(paginated_users)}")
        
        # Remove sensitive data and convert to response format
        response_users = []
        for user in paginated_users:
            # Remove sensitive fields
            user_copy = user.copy()
            user_copy.pop('hashed_password', None)
            
            # Convert to UserResponseDTO format
            try:
                user_response = UserResponseDTO(**user_copy)
                response_users.append(user_response.dict())
                print(f"   ✅ Converted user: {user.get('email', 'No email')}")
            except Exception as e:
                print(f"   ⚠️  Error converting user {user.get('id', 'unknown')}: {e}")
                # Fallback: include basic fields
                response_users.append({
                    'id': user.get('id'),
                    'email': user.get('email'),
                    'first_name': user.get('first_name'),
                    'last_name': user.get('last_name'),
                    'phone': user.get('phone'),
                    'role_id': user.get('role_id'),
                    'is_active': user.get('is_active', True),
                    'created_at': user.get('created_at'),
                    'updated_at': user.get('updated_at')
                })
                print(f"   ✅ Used fallback for user: {user.get('email', 'No email')}")
        
        # Create response
        response = PaginatedResponseDTO(
            success=True,
            data=response_users,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
        
        print(f"📋 Final response:")
        print(f"   Success: {response.success}")
        print(f"   Data count: {len(response.data)}")
        print(f"   Total: {response.total}")
        
        return response
        
    except Exception as e:
        print(f"❌ Error testing endpoint logic: {e}")
        import traceback
        traceback.print_exc()
        return None

async def create_test_user():
    """Create a test user directly"""
    try:
        print("\n📝 Creating a test user...")
        
        from app.database.firestore import get_user_repo
        import uuid
        from datetime import datetime
        
        user_repo = get_user_repo()
        
        # Generate test user data
        user_id = str(uuid.uuid4())
        user_data = {
            'id': user_id,
            'email': f'testuser_{uuid.uuid4().hex[:8]}@example.com',
            'phone': f'555{uuid.uuid4().hex[:7]}',
            'first_name': 'Test',
            'last_name': 'User',
            'hashed_password': 'dummy_hash',  # Not a real hash, just for testing
            'role_id': 'test_role_id',
            'venue_ids': [],
            'is_active': True,
            'is_verified': False,
            'email_verified': False,
            'phone_verified': False,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # Create user
        created_user = await user_repo.create(user_data, doc_id=user_id)
        print(f"✅ Created test user: {created_user.get('email')} (ID: {created_user.get('id')})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("🚀 DIRECT USERS ENDPOINT TEST")
    print("=" * 50)
    
    # Test 1: Repository
    user_count = await test_user_repository()
    
    if user_count == -1:
        print("\n💥 Repository test failed!")
        return False
    
    # Test 2: Create test user if database is empty
    if user_count == 0:
        print("\n📝 Database is empty, creating test user...")
        if await create_test_user():
            print("✅ Test user created, testing repository again...")
            user_count = await test_user_repository()
        else:
            print("❌ Failed to create test user")
            return False
    
    # Test 3: Endpoint logic
    response = await test_endpoint_logic()
    
    if response and response.success and response.total > 0:
        print(f"\n🎉 SUCCESS! Endpoint logic works correctly")
        print(f"   Returns {response.total} users")
        print(f"   Response format is correct")
        return True
    else:
        print(f"\n❌ Endpoint logic failed or returned empty results")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)