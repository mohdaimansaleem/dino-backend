#!/usr/bin/env python3
"""
Script to migrate venue rating data from old structure to new structure.
Converts 'rating' and 'total_reviews' to 'rating_total' and 'rating_count'.
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.firestore import venue_repo


async def migrate_venue_ratings():
    """Migrate venue rating data to new structure"""
    
    print("🔄 Starting venue rating migration...")
    print("=" * 60)
    
    try:
        # Get all venues
        venues = await venue_repo.get_all()
        
        if not venues:
            print("ℹ️  No venues found in the database")
            return
        
        print(f"📊 Found {len(venues)} venues to process")
        
        migrated_count = 0
        skipped_count = 0
        
        for venue in venues:
            venue_id = venue.get('id')
            venue_name = venue.get('name', 'Unknown')
            
            # Check if venue already has new rating structure
            if 'rating_total' in venue and 'rating_count' in venue:
                print(f"   ✓ {venue_name} - Already migrated")
                skipped_count += 1
                continue
            
            # Get old rating data
            old_rating = venue.get('rating', 0.0)
            old_total_reviews = venue.get('total_reviews', 0)
            
            # Calculate new rating structure
            if old_total_reviews > 0 and old_rating > 0:
                # If we have an average rating and review count, calculate total
                rating_total = old_rating * old_total_reviews
                rating_count = old_total_reviews
            else:
                # Default values for venues with no ratings
                rating_total = 0.0
                rating_count = 0
            
            # Prepare update data
            update_data = {
                'rating_total': rating_total,
                'rating_count': rating_count
            }
            
            # Remove old fields if they exist
            if 'rating' in venue:
                update_data['rating'] = None  # This will be removed by Firestore
            if 'total_reviews' in venue:
                update_data['total_reviews'] = None  # This will be removed by Firestore
            
            try:
                # Update the venue
                await venue_repo.update(venue_id, update_data)
                
                # Calculate average for display
                avg_rating = rating_total / rating_count if rating_count > 0 else 0.0
                
                print(f"   ✅ {venue_name} - Migrated (Total: {rating_total:.1f}, Count: {rating_count}, Avg: {avg_rating:.2f})")
                migrated_count += 1
                
            except Exception as e:
                print(f"   ❌ {venue_name} - Error: {e}")
                continue
        
        print("=" * 60)
        print(f"🎉 Migration completed!")
        print(f"   ✅ Migrated: {migrated_count} venues")
        print(f"   ⏭️  Skipped: {skipped_count} venues (already migrated)")
        print(f"   📊 Total processed: {len(venues)} venues")
        
        if migrated_count > 0:
            print("\n📝 Migration Summary:")
            print("   - Old 'rating' field → removed")
            print("   - Old 'total_reviews' field → removed") 
            print("   - New 'rating_total' field → sum of all ratings")
            print("   - New 'rating_count' field → number of ratings")
            print("   - Average rating can now be calculated as: rating_total / rating_count")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return


async def verify_migration():
    """Verify the migration was successful"""
    
    print("\n🔍 Verifying migration...")
    print("-" * 40)
    
    try:
        venues = await venue_repo.get_all()
        
        success_count = 0
        issue_count = 0
        
        for venue in venues:
            venue_name = venue.get('name', 'Unknown')
            
            # Check if venue has new structure
            has_rating_total = 'rating_total' in venue
            has_rating_count = 'rating_count' in venue
            has_old_rating = 'rating' in venue and venue.get('rating') is not None
            has_old_reviews = 'total_reviews' in venue and venue.get('total_reviews') is not None
            
            if has_rating_total and has_rating_count and not has_old_rating and not has_old_reviews:
                rating_total = venue.get('rating_total', 0)
                rating_count = venue.get('rating_count', 0)
                avg_rating = rating_total / rating_count if rating_count > 0 else 0.0
                
                print(f"   ✅ {venue_name} - OK (Total: {rating_total:.1f}, Count: {rating_count}, Avg: {avg_rating:.2f})")
                success_count += 1
            else:
                issues = []
                if not has_rating_total:
                    issues.append("missing rating_total")
                if not has_rating_count:
                    issues.append("missing rating_count")
                if has_old_rating:
                    issues.append("still has old rating field")
                if has_old_reviews:
                    issues.append("still has old total_reviews field")
                
                print(f"   ⚠️  {venue_name} - Issues: {', '.join(issues)}")
                issue_count += 1
        
        print("-" * 40)
        print(f"✅ Verification completed!")
        print(f"   ✅ Success: {success_count} venues")
        print(f"   ⚠️  Issues: {issue_count} venues")
        
        if issue_count == 0:
            print("🎉 All venues successfully migrated!")
        else:
            print("⚠️  Some venues may need manual attention")
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")


def main():
    """Main function"""
    
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        asyncio.run(verify_migration())
    else:
        asyncio.run(migrate_venue_ratings())
        asyncio.run(verify_migration())


if __name__ == "__main__":
    main()