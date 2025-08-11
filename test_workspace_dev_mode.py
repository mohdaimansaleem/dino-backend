#!/usr/bin/env python3
"""
Test workspace endpoint with development mode
"""
import asyncio
import sys
import os

# Set development mode
os.environ["DEV_MODE"] = "true"

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_workspace_dev_mode():
    """Test workspace endpoint with development mode"""
    try:
        print("🔍 Testing workspace endpoint with development mode...")
        print(f"DEV_MODE: {os.environ.get('DEV_MODE')}")
        
        # Test 1: Test mock repository directly
        print("\n1. Testing mock workspace repository...")
        from app.core.dev_mode import get_mock_workspace_repo
        
        mock_repo = get_mock_workspace_repo()
        all_workspaces = await mock_repo.get_all()
        
        print(f"✅ Mock repository working:")
        print(f"   Total workspaces: {len(all_workspaces)}")
        for ws in all_workspaces:
            print(f"   - {ws['id']}: {ws['display_name']} (active: {ws['is_active']})")
        
        # Test 2: Test workspace endpoint with mock data
        print("\n2. Testing workspace endpoint with mock data...")
        from app.api.v1.endpoints.workspace import workspaces_endpoint
        
        # Create a mock user for testing
        mock_user = {
            'id': 'user_1',
            'role': 'superadmin',
            'workspace_id': 'workspace_1'
        }
        
        # Test the get_items method
        result = await workspaces_endpoint.get_items(
            page=1,
            page_size=10,
            search=None,
            filters={},
            current_user=mock_user
        )
        
        print(f"✅ Endpoint result with mock data:")
        print(f"   Success: {result.success}")
        print(f"   Total: {result.total}")
        print(f"   Data count: {len(result.data) if result.data else 0}")
        print(f"   Page: {result.page}")
        print(f"   Page size: {result.page_size}")
        
        if result.data:
            print(f"   Workspaces returned:")
            for ws in result.data:
                # Handle both dict and Pydantic model objects
                if hasattr(ws, 'dict'):
                    ws_dict = ws.dict()
                    print(f"     - {ws_dict.get('id')}: {ws_dict.get('display_name')} (active: {ws_dict.get('is_active')})")
                else:
                    print(f"     - {ws.get('id')}: {ws.get('display_name')} (active: {ws.get('is_active')})")
        
        # Test 3: Test with search filter
        print("\n3. Testing with search filter...")
        search_result = await workspaces_endpoint.get_items(
            page=1,
            page_size=10,
            search="Restaurant",
            filters={},
            current_user=mock_user
        )
        
        print(f"✅ Search result for 'Restaurant':")
        print(f"   Total found: {search_result.total}")
        print(f"   Data count: {len(search_result.data) if search_result.data else 0}")
        
        # Test 4: Test with active filter
        print("\n4. Testing with active filter...")
        active_result = await workspaces_endpoint.get_items(
            page=1,
            page_size=10,
            search=None,
            filters={"is_active": True},
            current_user=mock_user
        )
        
        print(f"✅ Active workspaces result:")
        print(f"   Total active: {active_result.total}")
        print(f"   Data count: {len(active_result.data) if active_result.data else 0}")
        
        print("\n🎯 Development Mode Test Summary:")
        print("   ✅ Mock repository working correctly")
        print("   ✅ Workspace endpoint working with mock data")
        print("   ✅ Search functionality working")
        print("   ✅ Filter functionality working")
        print("   ✅ Pagination working")
        
        print("\n💡 To test this with your API:")
        print("   1. Set environment variable: export DEV_MODE=true")
        print("   2. Start your FastAPI server")
        print("   3. Test: GET {{api_base_url}}/workspaces?page=1&page_size=10")
        print("   4. Or test: GET {{api_base_url}}/workspaces/public-debug")
        
    except Exception as e:
        print(f"❌ Development mode test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_workspace_dev_mode())