#!/usr/bin/env python3
"""
Script to migrate all rating data from old structure to new structure.
Handles both venues and menu items in one go.
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.firestore import venue_repo, menu_item_repo


async def migrate_venue_ratings():
    """Migrate venue rating data"""
    print("🏢 Migrating venue ratings...")
    
    venues = await venue_repo.get_all()
    if not venues:
        print("   ℹ️  No venues found")
        return 0, 0
    
    migrated_count = 0
    skipped_count = 0
    
    for venue in venues:
        venue_id = venue.get('id')
        venue_name = venue.get('name', 'Unknown')
        
        # Check if venue already has new rating structure
        if 'rating_total' in venue and 'rating_count' in venue:
            skipped_count += 1
            continue
        
        # Get old rating data
        old_rating = venue.get('rating', 0.0)
        old_total_reviews = venue.get('total_reviews', 0)
        
        # Calculate new rating structure
        if old_total_reviews > 0 and old_rating > 0:
            rating_total = old_rating * old_total_reviews
            rating_count = old_total_reviews
        else:
            rating_total = 0.0
            rating_count = 0
        
        # Update venue
        update_data = {
            'rating_total': rating_total,
            'rating_count': rating_count
        }
        
        # Remove old fields
        if 'rating' in venue:
            update_data['rating'] = None
        if 'total_reviews' in venue:
            update_data['total_reviews'] = None
        
        try:
            await venue_repo.update(venue_id, update_data)
            avg_rating = rating_total / rating_count if rating_count > 0 else 0.0
            print(f"   ✅ {venue_name} - Migrated (Total: {rating_total:.1f}, Count: {rating_count}, Avg: {avg_rating:.2f})")
            migrated_count += 1
        except Exception as e:
            print(f"   ❌ {venue_name} - Error: {e}")
    
    return migrated_count, skipped_count


async def migrate_menu_item_ratings():
    """Migrate menu item rating data"""
    print("\n🍽️  Migrating menu item ratings...")
    
    menu_items = await menu_item_repo.get_all()
    if not menu_items:
        print("   ℹ️  No menu items found")
        return 0, 0
    
    migrated_count = 0
    skipped_count = 0
    
    for menu_item in menu_items:
        item_id = menu_item.get('id')
        item_name = menu_item.get('name', 'Unknown')
        
        # Check if menu item already has new rating structure
        if 'rating_total' in menu_item and 'rating_count' in menu_item:
            skipped_count += 1
            continue
        
        # Get old rating data
        old_rating = menu_item.get('rating', 0.0)
        
        # For menu items, assume 1 review if rating > 0
        if old_rating > 0:
            rating_total = old_rating
            rating_count = 1
        else:
            rating_total = 0.0
            rating_count = 0
        
        # Update menu item
        update_data = {
            'rating_total': rating_total,
            'rating_count': rating_count
        }
        
        # Remove old field
        if 'rating' in menu_item:
            update_data['rating'] = None
        
        try:
            await menu_item_repo.update(item_id, update_data)
            avg_rating = rating_total / rating_count if rating_count > 0 else 0.0
            print(f"   ✅ {item_name} - Migrated (Total: {rating_total:.1f}, Count: {rating_count}, Avg: {avg_rating:.2f})")
            migrated_count += 1
        except Exception as e:
            print(f"   ❌ {item_name} - Error: {e}")
    
    return migrated_count, skipped_count


async def verify_all_migrations():
    """Verify all migrations"""
    print("\n🔍 Verifying all migrations...")
    print("-" * 50)
    
    # Verify venues
    print("🏢 Checking venues...")
    venues = await venue_repo.get_all()
    venue_success = 0
    venue_issues = 0
    
    for venue in venues:
        venue_name = venue.get('name', 'Unknown')
        has_rating_total = 'rating_total' in venue
        has_rating_count = 'rating_count' in venue
        has_old_fields = 'rating' in venue or 'total_reviews' in venue
        
        if has_rating_total and has_rating_count and not has_old_fields:
            venue_success += 1
        else:
            venue_issues += 1
            print(f"   ⚠️  {venue_name} - Has issues")
    
    # Verify menu items
    print("\n🍽️  Checking menu items...")
    menu_items = await menu_item_repo.get_all()
    item_success = 0
    item_issues = 0
    
    for menu_item in menu_items:
        item_name = menu_item.get('name', 'Unknown')
        has_rating_total = 'rating_total' in menu_item
        has_rating_count = 'rating_count' in menu_item
        has_old_rating = 'rating' in menu_item and menu_item.get('rating') is not None
        
        if has_rating_total and has_rating_count and not has_old_rating:
            item_success += 1
        else:
            item_issues += 1
            print(f"   ⚠️  {item_name} - Has issues")
    
    print("-" * 50)
    print(f"✅ Verification Summary:")
    print(f"   🏢 Venues: {venue_success} success, {venue_issues} issues")
    print(f"   🍽️  Menu Items: {item_success} success, {item_issues} issues")
    
    total_success = venue_success + item_success
    total_issues = venue_issues + item_issues
    
    if total_issues == 0:
        print("🎉 All entities successfully migrated!")
    else:
        print(f"⚠️  {total_issues} entities may need manual attention")
    
    return total_success, total_issues


async def migrate_all_ratings():
    """Migrate all rating data"""
    
    print("🔄 Starting comprehensive rating migration...")
    print("=" * 70)
    
    try:
        # Migrate venues
        venue_migrated, venue_skipped = await migrate_venue_ratings()
        
        # Migrate menu items
        item_migrated, item_skipped = await migrate_menu_item_ratings()
        
        # Summary
        total_migrated = venue_migrated + item_migrated
        total_skipped = venue_skipped + item_skipped
        
        print("\n" + "=" * 70)
        print(f"🎉 Migration completed!")
        print(f"   ✅ Total migrated: {total_migrated} entities")
        print(f"   ⏭️  Total skipped: {total_skipped} entities (already migrated)")
        print(f"   🏢 Venues: {venue_migrated} migrated, {venue_skipped} skipped")
        print(f"   🍽️  Menu Items: {item_migrated} migrated, {item_skipped} skipped")
        
        if total_migrated > 0:
            print("\n📝 Migration Summary:")
            print("   - Old rating fields → removed")
            print("   - New 'rating_total' field → sum of all ratings")
            print("   - New 'rating_count' field → number of ratings")
            print("   - Average rating = rating_total / rating_count")
            print("\n⚠️  Note: Menu items with existing ratings assumed 1 review")
        
        return total_migrated, total_skipped
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return 0, 0


def main():
    """Main function"""
    
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        asyncio.run(verify_all_migrations())
    else:
        asyncio.run(migrate_all_ratings())
        asyncio.run(verify_all_migrations())


if __name__ == "__main__":
    main()