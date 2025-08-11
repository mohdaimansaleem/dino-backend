#!/usr/bin/env python3
"""
Debug Menu Public Endpoint
Test the specific endpoint that's failing with 500 error
"""
import asyncio
import traceback
from app.core.logging_config import setup_enhanced_logging, get_logger

# Setup logging
setup_enhanced_logging(log_level="DEBUG", enable_debug=True)
logger = get_logger(__name__)

async def test_menu_public_endpoint():
    """Test the public menu endpoint that's failing"""
    try:
        logger.info("🔍 Testing menu public endpoint...")
        
        # Import required modules
        from app.database.repository_manager import get_repository_manager
        from app.models.dto import MenuItemResponseDTO
        
        # Test venue ID from the error
        venue_id = "9ec66a25-3fa3-4d0a-9c1b-f9ed3c8ab993"
        
        logger.info(f"Testing venue ID: {venue_id}")
        
        # Get repository manager
        repo_manager = get_repository_manager()
        logger.info("✅ Repository manager obtained")
        
        # Get menu item repository
        repo = repo_manager.get_repository('menu_item')
        logger.info("✅ Menu item repository obtained")
        
        # Test get_by_venue method
        logger.info("Testing get_by_venue method...")
        items_data = await repo.get_by_venue(venue_id)
        logger.info(f"✅ Retrieved {len(items_data)} items from repository")
        
        # Filter only available items
        available_items = [item for item in items_data if item.get('is_available', False)]
        logger.info(f"✅ Filtered to {len(available_items)} available items")
        
        # Add calculated average_rating field for each item
        for item in available_items:
            rating_count = item.get('rating_count', 0)
            rating_total = item.get('rating_total', 0.0)
            item['average_rating'] = round(rating_total / rating_count, 2) if rating_count > 0 else 0.0
        
        logger.info("✅ Added average_rating calculations")
        
        # Try to create MenuItemResponseDTO objects
        logger.info("Testing MenuItemResponseDTO creation...")
        items = []
        for i, item in enumerate(available_items):
            try:
                dto_item = MenuItemResponseDTO(**item)
                items.append(dto_item)
                logger.debug(f"✅ Created DTO for item {i+1}: {item.get('name', 'Unknown')}")
            except Exception as e:
                logger.error(f"❌ Failed to create DTO for item {i+1}: {e}")
                logger.error(f"Item data: {item}")
                raise
        
        logger.info(f"✅ Successfully created {len(items)} MenuItemResponseDTO objects")
        
        # Test the actual endpoint logic
        logger.info("Testing endpoint logic simulation...")
        
        # Simulate the endpoint response
        result = {
            "status": "success",
            "items_count": len(items),
            "venue_id": venue_id,
            "available_items": len(available_items),
            "total_items": len(items_data)
        }
        
        logger.info(f"✅ Endpoint simulation successful: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error in menu public endpoint test: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

async def test_menu_category_endpoint():
    """Test the menu category endpoint as well"""
    try:
        logger.info("🔍 Testing menu category endpoint...")
        
        from app.database.repository_manager import get_repository_manager
        from app.models.dto import MenuCategoryResponseDTO
        
        venue_id = "9ec66a25-3fa3-4d0a-9c1b-f9ed3c8ab993"
        
        # Get repository manager
        repo_manager = get_repository_manager()
        repo = repo_manager.get_repository('menu_category')
        
        # Test get_by_venue method
        categories_data = await repo.get_by_venue(venue_id)
        logger.info(f"✅ Retrieved {len(categories_data)} categories from repository")
        
        # Filter only active categories
        active_categories = [cat for cat in categories_data if cat.get('is_active', False)]
        logger.info(f"✅ Filtered to {len(active_categories)} active categories")
        
        # Try to create MenuCategoryResponseDTO objects
        categories = []
        for i, cat in enumerate(active_categories):
            try:
                dto_cat = MenuCategoryResponseDTO(**cat)
                categories.append(dto_cat)
                logger.debug(f"✅ Created DTO for category {i+1}: {cat.get('name', 'Unknown')}")
            except Exception as e:
                logger.error(f"❌ Failed to create DTO for category {i+1}: {e}")
                logger.error(f"Category data: {cat}")
                raise
        
        logger.info(f"✅ Successfully created {len(categories)} MenuCategoryResponseDTO objects")
        
        result = {
            "status": "success",
            "categories_count": len(categories),
            "venue_id": venue_id,
            "active_categories": len(active_categories),
            "total_categories": len(categories_data)
        }
        
        logger.info(f"✅ Category endpoint simulation successful: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error in menu category endpoint test: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

async def main():
    """Main test function"""
    try:
        logger.info("🦕 Starting Menu Public Endpoint Debug Test")
        
        # Test menu items endpoint
        items_result = await test_menu_public_endpoint()
        logger.info(f"Menu items test result: {items_result}")
        
        # Test menu categories endpoint
        categories_result = await test_menu_category_endpoint()
        logger.info(f"Menu categories test result: {categories_result}")
        
        logger.info("✅ All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(main())