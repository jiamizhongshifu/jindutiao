"""
Test script for Behavior Recognition Engine

Tests the complete behavior recognition pipeline:
- ActivityCollector
- AppClassifier
- DomainClassifier
- BehaviorAnalyzer

Usage:
    python test_behavior_recognition.py
"""

import logging
import time
from gaiya.core.activity_collector import ActivityCollector, ActivitySnapshot
from gaiya.core.app_classifier import AppClassifier
from gaiya.core.domain_classifier import DomainClassifier
from gaiya.core.behavior_analyzer import BehaviorAnalyzer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)

logger = logging.getLogger(__name__)


def test_classifiers():
    """Test App and Domain Classifiers"""
    logger.info("=" * 60)
    logger.info("1. Testing Classifiers")
    logger.info("=" * 60)

    # Test AppClassifier
    logger.info("\n[AppClassifier]")
    app_classifier = AppClassifier(logger=logger)

    test_apps = [
        "chrome.exe",
        "Cursor.exe",
        "WeChat.exe",
        "bilibili.exe",
        "WINWORD.EXE",
        "unknown.exe"
    ]

    for app in test_apps:
        app_type = app_classifier.classify(app)
        default_mode = app_classifier.get_default_mode(app_type)
        logger.info(f"  {app:20s} → {app_type:10s} (default mode: {default_mode})")

    # Test DomainClassifier
    logger.info("\n[DomainClassifier]")
    domain_classifier = DomainClassifier(logger=logger)

    test_urls = [
        "https://github.com/user/repo",
        "https://bilibili.com/video/BV123",
        "https://notion.so/workspace/page",
        "https://jd.com/product/123",
        "https://chat.openai.com",
        "https://unknown-domain.com"
    ]

    for url in test_urls:
        category, mode = domain_classifier.classify(url)
        domain = domain_classifier.extract_domain(url)
        logger.info(f"  {domain:25s} → {category:10s} / {mode}")

    logger.info("\n✓ Classifiers test completed\n")


def test_behavior_analyzer():
    """Test Behavior Analyzer with real data"""
    logger.info("=" * 60)
    logger.info("2. Testing Behavior Analyzer")
    logger.info("=" * 60)

    # Initialize components
    analyzer = BehaviorAnalyzer(logger=logger)
    collector = ActivityCollector(collection_interval=5, logger=logger)

    logger.info("\nCollecting and analyzing 5 activity snapshots...")
    logger.info("Please switch between different apps to test behavior detection\n")

    for i in range(5):
        logger.info(f"[Snapshot #{i+1}/5]")

        # Collect activity
        snapshot = collector.collect_once()

        if snapshot:
            # Analyze behavior
            behavior_info = analyzer.analyze(snapshot)

            # Display results
            logger.info(f"  App: {behavior_info.app}")
            logger.info(f"  App Type: {behavior_info.app_type}")
            logger.info(f"  Window Title: {snapshot.window_title[:50]}")

            if behavior_info.url:
                logger.info(f"  URL: {behavior_info.url}")
                logger.info(f"  Domain: {behavior_info.domain}")
                logger.info(f"  Domain Category: {behavior_info.domain_category}")

            logger.info(f"  Content Mode: {behavior_info.mode}")
            logger.info(f"  Duration: {behavior_info.active_duration_sec}s")
            logger.info(f"  Trend: {behavior_info.trend}")

            # Highlight interesting behaviors
            if behavior_info.mode == "production":
                logger.info("  ✓ Productive activity detected!")
            elif behavior_info.mode == "consumption":
                logger.info("  ⚠ Consumption activity detected!")

            logger.info("")
        else:
            logger.warning("  Failed to collect snapshot\n")

        if i < 4:
            time.sleep(5)

    # Show current state
    logger.info("\n[Current State]")
    state = analyzer.get_current_state()
    logger.info(f"  Current App: {state['current_app']}")
    logger.info(f"  Current Mode: {state['current_mode']}")
    logger.info(f"  Duration in State: {state['duration_sec']}s")

    logger.info("\n✓ Behavior Analyzer test completed\n")


def test_mode_detection_logic():
    """Test content mode detection with simulated scenarios"""
    logger.info("=" * 60)
    logger.info("3. Testing Mode Detection Logic")
    logger.info("=" * 60)

    analyzer = BehaviorAnalyzer(logger=logger)

    # Scenario 1: IDE with code editing
    logger.info("\n[Scenario 1: VSCode editing Python code]")
    snapshot1 = ActivitySnapshot(
        app="Code.exe",
        window_title="main.py - Visual Studio Code",
        url="",
        timestamp=int(time.time())
    )
    behavior1 = analyzer.analyze(snapshot1)
    logger.info(f"  Detected Mode: {behavior1.mode} (Expected: production)")
    assert behavior1.mode == "production", "VSCode should be production mode"

    # Scenario 2: Browser on GitHub
    logger.info("\n[Scenario 2: Chrome browsing GitHub]")
    snapshot2 = ActivitySnapshot(
        app="chrome.exe",
        window_title="Pull Request #123 - GitHub",
        url="https://github.com/user/repo/pull/123",
        timestamp=int(time.time())
    )
    behavior2 = analyzer.analyze(snapshot2)
    logger.info(f"  Detected Mode: {behavior2.mode} (Expected: production)")
    logger.info(f"  Domain Category: {behavior2.domain_category} (Expected: code)")
    assert behavior2.mode == "production", "GitHub should be production mode"

    # Scenario 3: Browser on Bilibili
    logger.info("\n[Scenario 3: Chrome watching Bilibili]")
    snapshot3 = ActivitySnapshot(
        app="chrome.exe",
        window_title="Awesome Video - Bilibili",
        url="https://www.bilibili.com/video/BV1234567890",
        timestamp=int(time.time()) + 10
    )
    behavior3 = analyzer.analyze(snapshot3)
    logger.info(f"  Detected Mode: {behavior3.mode} (Expected: consumption)")
    logger.info(f"  Domain Category: {behavior3.domain_category} (Expected: video)")
    assert behavior3.mode == "consumption", "Bilibili should be consumption mode"

    # Scenario 4: WeChat chatting
    logger.info("\n[Scenario 4: WeChat chatting]")
    snapshot4 = ActivitySnapshot(
        app="WeChat.exe",
        window_title="Chat with Friend",
        url="",
        timestamp=int(time.time()) + 20
    )
    behavior4 = analyzer.analyze(snapshot4)
    logger.info(f"  Detected Mode: {behavior4.mode} (Expected: neutral)")
    assert behavior4.mode == "neutral", "WeChat should be neutral mode"

    logger.info("\n✓ Mode detection logic test completed\n")


def test_trend_detection():
    """Test behavior trend detection"""
    logger.info("=" * 60)
    logger.info("4. Testing Trend Detection")
    logger.info("=" * 60)

    analyzer = BehaviorAnalyzer(logger=logger)
    base_time = int(time.time())

    # Simulate sustained production activity
    logger.info("\n[Scenario: Sustained production activity]")
    for i in range(3):
        snapshot = ActivitySnapshot(
            app="Code.exe",
            window_title="main.py - VSCode",
            url="",
            timestamp=base_time + i * 60  # 1 minute intervals
        )
        behavior = analyzer.analyze(snapshot)
        logger.info(f"  After {behavior.active_duration_sec}s: trend={behavior.trend}")

    # Simulate focus_steady (20+ minutes)
    logger.info("\n[Scenario: Extended focus (20+ minutes)]")
    snapshot_focus = ActivitySnapshot(
        app="Code.exe",
        window_title="main.py - VSCode",
        url="",
        timestamp=base_time + 21 * 60  # 21 minutes
    )
    behavior_focus = analyzer.analyze(snapshot_focus)
    logger.info(f"  After {behavior_focus.active_duration_sec}s: trend={behavior_focus.trend}")
    logger.info(f"  Expected: focus_steady")

    # Simulate mode switch
    logger.info("\n[Scenario: Mode switch (work → Bilibili)]")
    analyzer.reset_state()  # Reset to simulate new session

    snapshot_work = ActivitySnapshot(
        app="Code.exe",
        window_title="Working on project",
        url="",
        timestamp=base_time + 100
    )
    analyzer.analyze(snapshot_work)

    time.sleep(0.1)

    snapshot_moyu = ActivitySnapshot(
        app="chrome.exe",
        window_title="Funny video - Bilibili",
        url="https://bilibili.com/video/test",
        timestamp=base_time + 110
    )
    behavior_moyu = analyzer.analyze(snapshot_moyu)
    logger.info(f"  Switched from production to consumption")
    logger.info(f"  Trend: {behavior_moyu.trend}")

    logger.info("\n✓ Trend detection test completed\n")


def main():
    """Run all tests"""
    logger.info("\n" + "=" * 60)
    logger.info("Behavior Recognition Engine - Comprehensive Test")
    logger.info("=" * 60 + "\n")

    try:
        # Test 1: Classifiers
        test_classifiers()

        # Test 2: Live behavior analysis
        test_behavior_analyzer()

        # Test 3: Mode detection logic
        test_mode_detection_logic()

        # Test 4: Trend detection
        test_trend_detection()

        logger.info("=" * 60)
        logger.info("✓ All Tests Passed Successfully!")
        logger.info("=" * 60)

    except AssertionError as e:
        logger.error(f"\n✗ Test Failed: {e}")
        raise
    except Exception as e:
        logger.error(f"\n✗ Unexpected Error: {e}")
        raise


if __name__ == "__main__":
    main()
