#!/usr/bin/env python3
"""
Debug script to test menu endpoints locally
"""
import asyncio
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_menu_endpoints():
    """Test menu endpoints locally"""
    try:
        # Import the menu endpoint functions directly
        from app.api.v1.endpoints.menu import get_public_venue_categories, get_public_venue_menu_items
        from app.core.dependency_injection import initialize_di
        
        # Initialize dependency injection
        initialize_di()
        
        # Test venue ID
        venue_id = "9ec66a25-3fa3-4d0a-9c1b-f9ed3c8ab993"
        
        print(f"Testing menu endpoints for venue: {venue_id}")
        
        # Test categories endpoint
        print("\n1. Testing get_public_venue_categories...")
        try:
            categories = await get_public_venue_categories(venue_id)
            print(f"✅ Categories endpoint works: {len(categories)} categories found")
            for cat in categories[:3]:  # Show first 3
                print(f"   - {cat.name if hasattr(cat, 'name') else cat}")
        except Exception as e:
            print(f"❌ Categories endpoint failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test items endpoint
        print("\n2. Testing get_public_venue_menu_items...")
        try:
            items = await get_public_venue_menu_items(venue_id)
            print(f"✅ Items endpoint works: {len(items)} items found")
            for item in items[:3]:  # Show first 3
                print(f"   - {item.name if hasattr(item, 'name') else item}")
        except Exception as e:
            print(f"❌ Items endpoint failed: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_menu_endpoints())