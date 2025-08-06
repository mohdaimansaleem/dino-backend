#!/usr/bin/env python3
"""
Test script to verify the user search endpoint fix
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.database.firestore import get_user_repo
from app.core.logging_config import get_logger

logger = get_logger(__name__)

async def test_user_search():
    """Test the user search functionality"""
    try:
        # Get user repository
        user_repo = get_user_repo()
        
        # Test 1: Get all users to see what's available
        print("=== Test 1: Getting all users ===")
        all_users = await user_repo.get_all()
        print(f"Total users in database: {len(all_users)}")
        
        for user in all_users:
            print(f"- {user.get('first_name', '')} {user.get('last_name', '')} ({user.get('email', '')})")
        
        # Test 2: Test search_text method directly
        print("\n=== Test 2: Testing search_text method ===")
        search_fields = ['first_name', 'last_name', 'email', 'phone']
        search_term = "john"
        
        print(f"Searching for '{search_term}' in fields: {search_fields}")
        search_results = await user_repo.search_text(
            search_fields=search_fields,
            search_term=search_term,
            limit=50
        )
        
        print(f"Search results: {len(search_results)} users found")
        for user in search_results:
            print(f"- {user.get('first_name', '')} {user.get('last_name', '')} ({user.get('email', '')})")
        
        # Test 3: Test with different search terms
        print("\n=== Test 3: Testing different search terms ===")
        test_terms = ["dev", "example", "user", "development"]
        
        for term in test_terms:
            results = await user_repo.search_text(
                search_fields=search_fields,
                search_term=term,
                limit=10
            )
            print(f"Search '{term}': {len(results)} results")
        
        print("\n=== User search test completed successfully ===")
        return True
        
    except Exception as e:
        print(f"Error during user search test: {e}")
        logger.error(f"User search test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_user_search())
    sys.exit(0 if success else 1)