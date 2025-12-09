"""
Test script for Activity Collector

Usage:
    python test_activity_collector.py
"""

import logging
import time
from gaiya.core.activity_collector import ActivityCollector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)

logger = logging.getLogger(__name__)


def test_activity_collector():
    """Test Activity Collector functionality"""
    logger.info("=" * 60)
    logger.info("Activity Collector Test")
    logger.info("=" * 60)

    # Initialize collector
    collector = ActivityCollector(
        collection_interval=5,
        logger=logger
    )

    # Test single collection
    logger.info("\n1. Testing single data collection...")
    snapshot = collector.collect_once()

    if snapshot:
        logger.info(f"✓ Successfully collected activity snapshot:")
        logger.info(f"  - App: {snapshot.app}")
        logger.info(f"  - Window Title: {snapshot.window_title}")
        logger.info(f"  - URL: {snapshot.url or '(not a browser)'}")
        logger.info(f"  - Timestamp: {snapshot.timestamp}")
    else:
        logger.error("✗ Failed to collect activity snapshot")
        return

    # Test database stats
    logger.info("\n2. Testing database statistics...")
    stats = collector.get_database_stats()
    logger.info(f"✓ Database statistics:")
    logger.info(f"  - Total records: {stats.get('total_records', 0)}")
    logger.info(f"  - Oldest record: {stats.get('oldest_date', 'N/A')}")
    logger.info(f"  - Newest record: {stats.get('newest_date', 'N/A')}")

    # Test continuous collection (collect 5 times)
    logger.info("\n3. Testing continuous collection (5 snapshots, 5s interval)...")
    logger.info("Please switch between different applications to test...")

    for i in range(5):
        logger.info(f"\nCollecting snapshot #{i+1}/5...")
        snapshot = collector.collect_once()

        if snapshot:
            logger.info(f"  ✓ {snapshot.app}: {snapshot.window_title[:50]}")
            if snapshot.url:
                logger.info(f"    URL: {snapshot.url}")
        else:
            logger.warning(f"  ✗ Failed to collect snapshot #{i+1}")

        if i < 4:  # Don't sleep after last iteration
            time.sleep(collector.collection_interval)

    # Test recent snapshots retrieval
    logger.info("\n4. Testing recent snapshots retrieval...")
    recent = collector.get_recent_snapshots(limit=10)
    logger.info(f"✓ Retrieved {len(recent)} recent snapshots:")

    for idx, snap in enumerate(recent[:5], 1):
        logger.info(f"  {idx}. {snap.app}: {snap.window_title[:40]}")

    # Final stats
    logger.info("\n5. Final database statistics...")
    final_stats = collector.get_database_stats()
    logger.info(f"✓ Final statistics:")
    logger.info(f"  - Total records: {final_stats.get('total_records', 0)}")
    logger.info(f"  - Database path: {collector.db_path}")

    logger.info("\n" + "=" * 60)
    logger.info("Activity Collector Test Completed Successfully!")
    logger.info("=" * 60)


if __name__ == "__main__":
    test_activity_collector()
