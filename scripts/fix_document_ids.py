#!/usr/bin/env python3
"""
Script to ensure all documents in all collections have their 'id' field matching the Firestore document ID.
This script should be run after implementing the document ID consistency changes.
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.firestore import (
    workspace_repo, role_repo, permission_repo, user_repo, venue_repo,
    menu_item_repo, menu_category_repo, table_repo, table_area_repo,
    order_repo, customer_repo, review_repo, notification_repo,
    transaction_repo, analytics_repo
)


async def fix_all_collections():
    """Fix document IDs across all collections"""
    
    repositories = [
        ("workspaces", workspace_repo),
        ("roles", role_repo),
        ("permissions", permission_repo),
        ("users", user_repo),
        ("venues", venue_repo),
        ("menu_items", menu_item_repo),
        ("menu_categories", menu_category_repo),
        ("tables", table_repo),
        ("table_areas", table_area_repo),
        ("orders", order_repo),
        ("customers", customer_repo),
        ("reviews", review_repo),
        ("notifications", notification_repo),
        ("transactions", transaction_repo),
        ("analytics", analytics_repo),
    ]
    
    total_checked = 0
    total_fixed = 0
    
    print("🔧 Starting document ID consistency check across all collections...")
    print("=" * 70)
    
    for collection_name, repo in repositories:
        print(f"📋 Checking collection: {collection_name}")
        
        try:
            result = await repo.ensure_document_ids_consistency()
            
            checked = result["checked"]
            fixed = result["fixed"]
            
            total_checked += checked
            total_fixed += fixed
            
            if fixed > 0:
                print(f"   ✅ Fixed {fixed} documents out of {checked} checked")
            else:
                print(f"   ✓ All {checked} documents already consistent")
                
        except Exception as e:
            print(f"   ❌ Error processing {collection_name}: {e}")
            continue
    
    print("=" * 70)
    print(f"🎉 Completed! Total documents checked: {total_checked}")
    print(f"🔧 Total documents fixed: {total_fixed}")
    
    if total_fixed > 0:
        print(f"✅ Successfully ensured all document IDs are consistent with Firestore document IDs")
    else:
        print(f"✓ All documents were already consistent")


async def check_single_collection(collection_name: str):
    """Check a single collection"""
    
    repo_map = {
        "workspaces": workspace_repo,
        "roles": role_repo,
        "permissions": permission_repo,
        "users": user_repo,
        "venues": venue_repo,
        "menu_items": menu_item_repo,
        "menu_categories": menu_category_repo,
        "tables": table_repo,
        "table_areas": table_area_repo,
        "orders": order_repo,
        "customers": customer_repo,
        "reviews": review_repo,
        "notifications": notification_repo,
        "transactions": transaction_repo,
        "analytics": analytics_repo,
    }
    
    if collection_name not in repo_map:
        print(f"❌ Unknown collection: {collection_name}")
        print(f"Available collections: {', '.join(repo_map.keys())}")
        return
    
    repo = repo_map[collection_name]
    
    print(f"🔧 Checking collection: {collection_name}")
    
    try:
        result = await repo.ensure_document_ids_consistency()
        
        checked = result["checked"]
        fixed = result["fixed"]
        
        print(f"📊 Results:")
        print(f"   - Documents checked: {checked}")
        print(f"   - Documents fixed: {fixed}")
        
        if fixed > 0:
            print(f"✅ Successfully fixed {fixed} documents")
        else:
            print(f"✓ All documents were already consistent")
            
    except Exception as e:
        print(f"❌ Error processing {collection_name}: {e}")


def main():
    """Main function"""
    
    if len(sys.argv) > 1:
        collection_name = sys.argv[1]
        asyncio.run(check_single_collection(collection_name))
    else:
        asyncio.run(fix_all_collections())


if __name__ == "__main__":
    main()