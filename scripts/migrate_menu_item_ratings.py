#!/usr/bin/env python3
"""
Script to migrate menu item rating data from old structure to new structure.
Converts 'rating' to 'rating_total' and 'rating_count'.
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.firestore import menu_item_repo


async def migrate_menu_item_ratings():
    """Migrate menu item rating data to new structure"""
    
    print("🔄 Starting menu item rating migration...")
    print("=" * 60)
    
    try:
        # Get all menu items
        menu_items = await menu_item_repo.get_all()
        
        if not menu_items:
            print("ℹ️  No menu items found in the database")
            return
        
        print(f"📊 Found {len(menu_items)} menu items to process")
        
        migrated_count = 0
        skipped_count = 0
        
        for menu_item in menu_items:
            item_id = menu_item.get('id')
            item_name = menu_item.get('name', 'Unknown')
            
            # Check if menu item already has new rating structure
            if 'rating_total' in menu_item and 'rating_count' in menu_item:
                print(f"   ✓ {item_name} - Already migrated")
                skipped_count += 1
                continue
            
            # Get old rating data
            old_rating = menu_item.get('rating', 0.0)
            
            # For menu items, we don't have a review count, so we need to make assumptions
            # If rating is 0, assume no ratings
            # If rating > 0, assume at least 1 rating (we can't know the exact count)
            if old_rating > 0:
                # Assume this is an average rating with at least 1 review
                # We'll set count to 1 and total to the rating value
                # This is the best we can do without historical data
                rating_total = old_rating
                rating_count = 1
            else:
                # No rating data
                rating_total = 0.0
                rating_count = 0
            
            # Prepare update data
            update_data = {
                'rating_total': rating_total,
                'rating_count': rating_count
            }
            
            # Remove old field if it exists
            if 'rating' in menu_item:
                update_data['rating'] = None  # This will be removed by Firestore
            
            try:
                # Update the menu item
                await menu_item_repo.update(item_id, update_data)
                
                # Calculate average for display
                avg_rating = rating_total / rating_count if rating_count > 0 else 0.0
                
                print(f"   ✅ {item_name} - Migrated (Total: {rating_total:.1f}, Count: {rating_count}, Avg: {avg_rating:.2f})")
                migrated_count += 1
                
            except Exception as e:
                print(f"   ❌ {item_name} - Error: {e}")
                continue
        
        print("=" * 60)
        print(f"🎉 Migration completed!")
        print(f"   ✅ Migrated: {migrated_count} menu items")
        print(f"   ⏭️  Skipped: {skipped_count} menu items (already migrated)")
        print(f"   📊 Total processed: {len(menu_items)} menu items")
        
        if migrated_count > 0:
            print("\n📝 Migration Summary:")
            print("   - Old 'rating' field → removed")
            print("   - New 'rating_total' field → sum of all ratings")
            print("   - New 'rating_count' field → number of ratings")
            print("   - Average rating can now be calculated as: rating_total / rating_count")
            print("\n⚠️  Note: For existing menu items with ratings, we assumed 1 review")
            print("   This is because the old system didn't track review counts for menu items.")
            print("   Future ratings will be accurately tracked.")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return


async def verify_migration():
    """Verify the migration was successful"""
    
    print("\n🔍 Verifying migration...")
    print("-" * 40)
    
    try:
        menu_items = await menu_item_repo.get_all()
        
        success_count = 0
        issue_count = 0
        
        for menu_item in menu_items:
            item_name = menu_item.get('name', 'Unknown')
            
            # Check if menu item has new structure
            has_rating_total = 'rating_total' in menu_item
            has_rating_count = 'rating_count' in menu_item
            has_old_rating = 'rating' in menu_item and menu_item.get('rating') is not None
            
            if has_rating_total and has_rating_count and not has_old_rating:
                rating_total = menu_item.get('rating_total', 0)
                rating_count = menu_item.get('rating_count', 0)
                avg_rating = rating_total / rating_count if rating_count > 0 else 0.0
                
                print(f"   ✅ {item_name} - OK (Total: {rating_total:.1f}, Count: {rating_count}, Avg: {avg_rating:.2f})")
                success_count += 1
            else:
                issues = []
                if not has_rating_total:
                    issues.append("missing rating_total")
                if not has_rating_count:
                    issues.append("missing rating_count")
                if has_old_rating:
                    issues.append("still has old rating field")
                
                print(f"   ⚠️  {item_name} - Issues: {', '.join(issues)}")
                issue_count += 1
        
        print("-" * 40)
        print(f"✅ Verification completed!")
        print(f"   ✅ Success: {success_count} menu items")
        print(f"   ⚠️  Issues: {issue_count} menu items")
        
        if issue_count == 0:
            print("🎉 All menu items successfully migrated!")
        else:
            print("⚠️  Some menu items may need manual attention")
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")


def main():
    """Main function"""
    
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        asyncio.run(verify_migration())
    else:
        asyncio.run(migrate_menu_item_ratings())
        asyncio.run(verify_migration())


if __name__ == "__main__":
    main()