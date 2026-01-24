#!/usr/bin/env python3
"""
Elite 8 - Database & Scheduler Test Script

This script tests the database and scheduler functionality
for the Elite 8 AI Video Generation System.
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, "/workspace/waifugen_system")

from src.database import get_db, init_sample_data, JobStatus, PostStatus, Platform
from src.scheduler import get_scheduler, get_content_scheduler, JobScheduler


async def test_database():
    """Test database operations"""
    print("\n" + "="*50)
    print("TESTING DATABASE")
    print("="*50)
    
    # Get database instance
    db = get_db()
    
    # Initialize sample data
    print("\n1. Initializing sample data...")
    init_sample_data(db)
    print("   ✓ Sample data initialized")
    
    # Test characters
    print("\n2. Testing character operations...")
    characters = db.get_all_characters()
    print(f"   ✓ Found {len(characters)} characters")
    for char in characters[:3]:
        print(f"   - {char['name']} (ID: {char['id']})")
    
    # Test job creation
    print("\n3. Testing job creation...")
    job_id = db.create_job(
        character_id=characters[0]['id'],
        prompt="Test video generation",
        duration_seconds=15,
        platform="tiktok",
        scheduled_time=datetime.now() + timedelta(hours=1)
    )
    print(f"   ✓ Created job: {job_id}")
    
    # Test job status update
    print("\n4. Testing job status update...")
    db.update_job_status(job_id, JobStatus.QUEUED)
    print(f"   ✓ Job status updated to: {JobStatus.QUEUED.value}")
    
    # Test job retrieval
    job = db.get_job(job_id)
    print(f"   ✓ Retrieved job: {job['prompt']}")
    
    # Test job statistics
    print("\n5. Testing job statistics...")
    stats = db.get_job_stats()
    print(f"   ✓ Total jobs: {stats['total_jobs']}")
    print(f"   ✓ Today jobs: {stats['today_jobs']}")
    
    # Test credit usage
    print("\n6. Testing credit usage...")
    credit_usage = db.get_credit_usage(days=7)
    print(f"   ✓ Total credits used: {credit_usage['total_credits']}")
    print(f"   ✓ Cost: ${credit_usage['total_cost_usd']:.2f}")
    
    # Close database
    db.close()
    print("\n✓ Database tests completed successfully")
    
    return True


async def test_scheduler():
    """Test scheduler operations"""
    print("\n" + "="*50)
    print("TESTING SCHEDULER")
    print("="*50)
    
    # Get scheduler instance
    scheduler = get_scheduler()
    
    # Check scheduler status
    print("\n1. Checking scheduler status...")
    status = scheduler.get_scheduler_status()
    print(f"   ✓ Running: {status['running']}")
    print(f"   ✓ Tasks: {status['tasks_count']}")
    print(f"   ✓ Posting slots: {status['posting_slots']}")
    
    # Get upcoming tasks
    print("\n2. Getting upcoming tasks...")
    upcoming = scheduler.get_upcoming_tasks(hours=24)
    print(f"   ✓ Found {len(upcoming)} upcoming tasks")
    
    # Test content scheduler
    print("\n3. Testing content scheduler...")
    content_scheduler = get_content_scheduler(scheduler)
    
    # Get optimal posting times
    print("   - Optimal TikTok times:")
    times = content_scheduler.get_optimal_posting_times("tiktok")
    for t in times:
        print(f"     {t.strftime('%Y-%m-%d %H:%M')}")
    
    # Test character rotation
    print("\n4. Testing character rotation...")
    char = content_scheduler.get_character_for_slot(1)
    print(f"   ✓ Character for slot 1: {char}")
    
    # Close scheduler
    await scheduler.close()
    print("\n✓ Scheduler tests completed successfully")
    
    return True


async def test_full_schedule():
    """Test creating a full daily schedule"""
    print("\n" + "="*50)
    print("TESTING FULL SCHEDULE")
    print("="*50)
    
    scheduler = get_scheduler()
    content_scheduler = get_content_scheduler(scheduler)
    
    print("\n1. Creating daily schedule...")
    schedule = await content_scheduler.create_daily_schedule(
        date=datetime.now() + timedelta(days=1),
        platforms=["tiktok", "instagram"]
    )
    
    print(f"   ✓ Date: {schedule['date']}")
    print(f"   ✓ Jobs created: {schedule['jobs_created']}")
    print(f"   ✓ Posts created: {schedule['posts_created']}")
    
    print("\n2. Schedule details:")
    for slot in schedule['slots']:
        print(f"   Slot {slot['slot']} ({slot['time']}):")
        print(f"     - Character: {slot['character']['name'] if slot['character'] else 'None'}")
        print(f"     - Jobs: {len(slot['jobs'])}")
    
    await scheduler.close()
    print("\n✓ Full schedule test completed")
    
    return True


async def main():
    """Main test function"""
    print("\n" + "="*60)
    print("ELITE 8 - DATABASE & SCHEDULER INTEGRATION TEST")
    print("="*60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    try:
        # Run tests
        await test_database()
        await test_scheduler()
        await test_full_schedule()
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED ✓")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
