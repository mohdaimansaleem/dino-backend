#!/usr/bin/env python3
"""
Debug script to check workspace endpoint and database
"""
import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_workspace_debug():
    """Test workspace endpoint and database"""
    try:
        print("🔍 Testing workspace endpoint and database...")
        
        # Test 1: Check if we can import and initialize the workspace repository
        print("\n1. Testing workspace repository...")
        from app.database.firestore import get_workspace_repo
        
        workspace_repo = get_workspace_repo()
        print(f"✅ Workspace repository initialized: {workspace_repo.collection_name}")
        
        # Test 2: Check if we can get all workspaces
        print("\n2. Getting all workspaces from database...")
        all_workspaces = await workspace_repo.get_all()
        print(f"📊 Total workspaces in database: {len(all_workspaces)}")
        
        if all_workspaces:
            print("📋 Workspace details:")
            for i, workspace in enumerate(all_workspaces[:3]):  # Show first 3
                print(f"  {i+1}. ID: {workspace.get('id')}")
                print(f"     Name: {workspace.get('name', 'N/A')}")
                print(f"     Display Name: {workspace.get('display_name', 'N/A')}")
                print(f"     Active: {workspace.get('is_active', 'N/A')}")
                print(f"     Created: {workspace.get('created_at', 'N/A')}")
                print()
        else:
            print("❌ No workspaces found in database")
            
        # Test 3: Test workspace endpoint directly
        print("\n3. Testing workspace endpoint logic...")
        from app.api.v1.endpoints.workspace import workspaces_endpoint
        
        # Create a mock user for testing
        mock_user = {
            'id': 'test_user_id',
            'role': 'superadmin',
            'workspace_id': None
        }
        
        # Test the get_items method
        try:
            result = await workspaces_endpoint.get_items(
                page=1,
                page_size=10,
                search=None,
                filters={},
                current_user=mock_user
            )
            
            print(f"✅ Endpoint result:")
            print(f"   Success: {result.success}")
            print(f"   Total: {result.total}")
            print(f"   Data count: {len(result.data) if result.data else 0}")
            print(f"   Page: {result.page}")
            print(f"   Page size: {result.page_size}")
            
        except Exception as e:
            print(f"❌ Endpoint test failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 4: Check user role function
        print("\n4. Testing user role function...")
        try:
            from app.core.security import _get_user_role
            user_role = await _get_user_role(mock_user)
            print(f"✅ User role: {user_role}")
        except Exception as e:
            print(f"❌ User role test failed: {e}")
            
        # Test 5: Check if there are any users in the database
        print("\n5. Checking users in database...")
        try:
            from app.database.firestore import get_user_repo
            user_repo = get_user_repo()
            all_users = await user_repo.get_all(limit=5)
            print(f"📊 Total users in database (first 5): {len(all_users)}")
            
            if all_users:
                print("👥 User details:")
                for i, user in enumerate(all_users):
                    print(f"  {i+1}. ID: {user.get('id')}")
                    print(f"     Email: {user.get('email', 'N/A')}")
                    print(f"     Role ID: {user.get('role_id', 'N/A')}")
                    print(f"     Workspace ID: {user.get('workspace_id', 'N/A')}")
                    print()
            else:
                print("❌ No users found in database")
                
        except Exception as e:
            print(f"❌ User check failed: {e}")
            
        print("\n🎯 Debug Summary:")
        print(f"   - Workspaces in DB: {len(all_workspaces)}")
        print(f"   - Repository working: ✅")
        print("   - Endpoint logic: Check above results")
        
    except Exception as e:
        print(f"❌ Debug script failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_workspace_debug())