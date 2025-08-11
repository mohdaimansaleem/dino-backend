#!/usr/bin/env python3
"""
Test script for menu endpoint
"""
import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_menu_endpoint():
    """Test the menu endpoint that's failing"""
    try:
        from app.database.repository_manager import get_repository_manager
        from app.models.dto import MenuItemResponseDTO
        
        # Test venue ID from the error
        venue_id = "9ec66a25-3fa3-4d0a-9c1b-f9ed3c8ab993"
        
        print(f"Testing menu items for venue: {venue_id}")
        
        # Get repository
        repo = get_repository_manager().get_repository('menu_item')
        
        # Get items by venue
        items_data = await repo.get_by_venue(venue_id)
        print(f"Found {len(items_data)} items in database")
        
        if items_data:
            print("Sample item data:")
            sample_item = items_data[0]
            print(f"Keys: {list(sample_item.keys())}")
            print(f"Sample: {sample_item}")
            
            # Test creating MenuItemResponseDTO
            try:
                # Add calculated average_rating field
                rating_count = sample_item.get('rating_count', 0)
                rating_total = sample_item.get('rating_total', 0.0)
                sample_item['average_rating'] = round(rating_total / rating_count, 2) if rating_count > 0 else 0.0
                
                dto = MenuItemResponseDTO(**sample_item)
                print("✅ Successfully created MenuItemResponseDTO")
                print(f"DTO: {dto}")
            except Exception as e:
                print(f"❌ Error creating MenuItemResponseDTO: {e}")
                print(f"Missing fields or validation errors")
        else:
            print("No items found for this venue")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_menu_endpoint())