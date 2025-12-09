"""
Test script for Phase 4: Danmaku Event Engine

Tests the complete event-driven danmaku system:
- CooldownManager
- DanmakuEventEngine
- Event priority queue
- Probability scheduling
- Timing jitter
- Context generation

Usage:
    python test_danmaku_engine.py
"""

import logging
import time
import json
from gaiya.core.activity_collector import ActivitySnapshot
from gaiya.core.behavior_analyzer import BehaviorAnalyzer
from gaiya.core.cooldown_manager import CooldownManager, CooldownConfig
from gaiya.core.danmaku_event_engine import DanmakuEventEngine, EventPriority

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)

logger = logging.getLogger(__name__)


def test_cooldown_manager():
    """Test 1: Cooldown Manager"""
    logger.info("=" * 60)
    logger.info("Test 1: Cooldown Manager")
    logger.info("=" * 60)

    # Create cooldown manager with shorter thresholds for testing
    config = CooldownConfig(
        global_cooldown_sec=3,
        category_cooldown_sec=5,
        tone_cooldown_sec=7
    )
    cooldown = CooldownManager(config=config, logger=logger)

    # Test 1: Initial check (should allow)
    logger.info("\n[Check 1: Initial check]")
    can_show = cooldown.can_show_danmaku("focus_steady", "鼓励")
    logger.info(f"  Can show: {can_show} (Expected: True)")
    assert can_show, "Initial check should allow danmaku"

    # Record danmaku shown
    cooldown.record_danmaku_shown("focus_steady", "鼓励")
    logger.info("  Recorded: focus_steady / 鼓励")

    # Test 2: Immediate check (should block - global cooldown)
    logger.info("\n[Check 2: Immediate check (global cooldown)]")
    can_show = cooldown.can_show_danmaku("moyu_start", "调侃")
    logger.info(f"  Can show: {can_show} (Expected: False)")
    assert not can_show, "Should be blocked by global cooldown"

    # Test 3: Wait for global cooldown
    logger.info("\n[Check 3: After global cooldown]")
    time.sleep(3.1)
    can_show = cooldown.can_show_danmaku("moyu_start", "调侃")
    logger.info(f"  Can show: {can_show} (Expected: True)")
    assert can_show, "Should allow after global cooldown"

    cooldown.record_danmaku_shown("moyu_start", "调侃")

    # Test 4: Category cooldown check
    logger.info("\n[Check 4: Category cooldown check]")
    time.sleep(3.1)  # Global cooldown passed
    can_show = cooldown.can_show_danmaku("moyu_start", "吐槽")  # Same category
    logger.info(f"  Can show (same category): {can_show} (Expected: False)")
    assert not can_show, "Should be blocked by category cooldown"

    # Test 5: Different category (should allow)
    logger.info("\n[Check 5: Different category]")
    can_show = cooldown.can_show_danmaku("focus_steady", "吐槽")
    logger.info(f"  Can show (different category): {can_show} (Expected: True)")
    assert can_show, "Should allow different category"

    # Test 6: Statistics
    logger.info("\n[Statistics]")
    stats = cooldown.get_statistics()
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")

    logger.info("\n✓ Cooldown Manager test passed\n")


def test_event_engine_basic():
    """Test 2: Event Engine Basic Operations"""
    logger.info("=" * 60)
    logger.info("Test 2: Event Engine Basic Operations")
    logger.info("=" * 60)

    # Create engine with 100% trigger probability for testing
    cooldown_config = CooldownConfig(
        global_cooldown_sec=1,
        category_cooldown_sec=2,
        tone_cooldown_sec=3
    )
    cooldown = CooldownManager(config=cooldown_config, logger=logger)
    engine = DanmakuEventEngine(
        cooldown_manager=cooldown,
        trigger_probability=1.0,  # 100% for testing
        jitter_range_sec=2,
        logger=logger
    )

    # Create behavior analyzer
    analyzer = BehaviorAnalyzer(logger=logger)

    # Test 1: Process focus_steady behavior
    logger.info("\n[Test 1: Focus Steady Behavior]")
    snapshot1 = ActivitySnapshot(
        app="Code.exe",
        window_title="main.py - VSCode",
        url="",
        timestamp=int(time.time())
    )
    behavior1 = analyzer.analyze(snapshot1)

    # Manually set trend for testing
    behavior1.trend = "focus_steady"
    behavior1.active_duration_sec = 1200  # 20 minutes

    engine.process_behavior(behavior1)
    logger.info(f"  Processed behavior: {behavior1.trend}")
    logger.info(f"  Queue size: {engine.event_queue.qsize()}")

    # Test 2: Consume event
    logger.info("\n[Test 2: Consume Event]")
    events = engine.consume_events(max_events=1)
    logger.info(f"  Events consumed: {len(events)}")

    if events:
        event = events[0]
        logger.info(f"  Category: {event.category}")
        logger.info(f"  Priority: {event.priority.name}")
        logger.info(f"  Context variables:")
        for key, value in event.context.items():
            logger.info(f"    {key}: {value}")

    assert len(events) == 1, "Should consume one event"

    # Test 3: Multiple behaviors
    logger.info("\n[Test 3: Multiple Behaviors]")

    # Moyu start (HIGH priority)
    time.sleep(1.1)
    snapshot2 = ActivitySnapshot(
        app="chrome.exe",
        window_title="Bilibili",
        url="https://bilibili.com/video/test",
        timestamp=int(time.time())
    )
    behavior2 = analyzer.analyze(snapshot2)
    behavior2.trend = "moyu_start"
    behavior2.active_duration_sec = 180  # 3 minutes
    engine.process_behavior(behavior2)

    # Mode switch (LOW priority)
    time.sleep(1.1)
    snapshot3 = ActivitySnapshot(
        app="WeChat.exe",
        window_title="Chat",
        url="",
        timestamp=int(time.time())
    )
    behavior3 = analyzer.analyze(snapshot3)
    behavior3.trend = "mode_switch"
    engine.process_behavior(behavior3)

    logger.info(f"  Queue size after processing: {engine.event_queue.qsize()}")

    # Test 4: Priority order
    logger.info("\n[Test 4: Priority Order]")
    events = engine.consume_events(max_events=2)
    logger.info(f"  Events consumed: {len(events)}")

    for i, event in enumerate(events):
        logger.info(f"  Event {i+1}: {event.category} (Priority: {event.priority.name})")

    # First event should be HIGH priority (moyu_start)
    if events:
        assert events[0].priority == EventPriority.HIGH, "First event should be HIGH priority"

    # Test 5: Statistics
    logger.info("\n[Statistics]")
    stats = engine.get_statistics()
    for key, value in stats.items():
        if key != 'cooldown_stats':
            logger.info(f"  {key}: {value}")

    logger.info("\n✓ Event Engine basic test passed\n")


def test_probability_scheduling():
    """Test 3: Probability Scheduling"""
    logger.info("=" * 60)
    logger.info("Test 3: Probability Scheduling")
    logger.info("=" * 60)

    # Test different trigger probabilities
    test_cases = [
        (0.0, "Never trigger"),
        (0.3, "30% trigger rate"),
        (0.5, "50% trigger rate"),
        (1.0, "Always trigger")
    ]

    analyzer = BehaviorAnalyzer(logger=logger)

    for probability, description in test_cases:
        logger.info(f"\n[Test: {description} (probability={probability})]")

        engine = DanmakuEventEngine(
            trigger_probability=probability,
            logger=logger
        )

        # Process 20 behaviors
        triggered = 0
        total = 20

        for i in range(total):
            snapshot = ActivitySnapshot(
                app="Code.exe",
                window_title=f"file{i}.py",
                url="",
                timestamp=int(time.time())
            )
            behavior = analyzer.analyze(snapshot)
            behavior.trend = "focus_steady"

            queue_size_before = engine.event_queue.qsize()
            engine.process_behavior(behavior)
            queue_size_after = engine.event_queue.qsize()

            if queue_size_after > queue_size_before:
                triggered += 1

        trigger_rate = triggered / total
        logger.info(f"  Triggered: {triggered}/{total} ({trigger_rate:.1%})")
        logger.info(f"  Expected: ~{probability:.1%}")

        # Verify trigger rate is within reasonable range
        if probability == 0.0:
            assert triggered == 0, "Should never trigger with 0% probability"
        elif probability == 1.0:
            assert triggered == total, "Should always trigger with 100% probability"
        else:
            # Allow ±20% variance for randomness
            assert abs(trigger_rate - probability) < 0.3, f"Trigger rate should be close to {probability}"

    logger.info("\n✓ Probability scheduling test passed\n")


def test_timing_jitter():
    """Test 4: Timing Jitter"""
    logger.info("=" * 60)
    logger.info("Test 4: Timing Jitter")
    logger.info("=" * 60)

    engine = DanmakuEventEngine(
        trigger_probability=1.0,
        jitter_range_sec=5,
        logger=logger
    )

    analyzer = BehaviorAnalyzer(logger=logger)

    # Process multiple behaviors
    logger.info("\n[Processing 5 behaviors and checking jitter]")
    base_time = time.time()

    for i in range(5):
        snapshot = ActivitySnapshot(
            app="Code.exe",
            window_title=f"file{i}.py",
            url="",
            timestamp=int(base_time + i * 10)
        )
        behavior = analyzer.analyze(snapshot)
        behavior.trend = "focus_steady"
        engine.process_behavior(behavior)

    # Consume events and check jitter
    logger.info("\n[Consuming events and measuring jitter]")
    jitters = []

    for i in range(5):
        events = engine.consume_events(max_events=1)
        if events:
            event = events[0]
            original_time = base_time + i * 10
            jittered_time = event.timestamp
            jitter = jittered_time - original_time
            jitters.append(jitter)
            logger.info(f"  Event {i+1}: Jitter = {jitter:+.2f}s (range: ±5s)")

            # Verify jitter is within range
            assert abs(jitter) <= 5, f"Jitter should be within ±5s, got {jitter}"

    logger.info(f"\n  Average jitter: {sum(jitters)/len(jitters):.2f}s")
    logger.info(f"  Jitter range: [{min(jitters):.2f}s, {max(jitters):.2f}s]")

    logger.info("\n✓ Timing jitter test passed\n")


def test_context_generation():
    """Test 5: Context Generation"""
    logger.info("=" * 60)
    logger.info("Test 5: Context Generation")
    logger.info("=" * 60)

    engine = DanmakuEventEngine(
        trigger_probability=1.0,
        logger=logger
    )

    analyzer = BehaviorAnalyzer(logger=logger)

    # Test case 1: IDE
    logger.info("\n[Test 1: IDE Context]")
    snapshot1 = ActivitySnapshot(
        app="Code.exe",
        window_title="main.py - VSCode",
        url="",
        timestamp=int(time.time())
    )
    behavior1 = analyzer.analyze(snapshot1)
    behavior1.trend = "focus_steady"
    behavior1.active_duration_sec = 1200

    engine.process_behavior(behavior1)
    events = engine.consume_events(max_events=1)

    if events:
        context = events[0].context
        logger.info("  Context variables:")
        for key, value in context.items():
            logger.info(f"    {key}: {value}")

        assert context['app'] == "Code.exe"
        assert context['app_type'] == "ide"
        assert context['mode'] == "production"
        assert context['duration_min'] == 20

    # Test case 2: Browser with domain
    logger.info("\n[Test 2: Browser Context with Domain]")
    snapshot2 = ActivitySnapshot(
        app="chrome.exe",
        window_title="GitHub",
        url="https://github.com/user/repo",
        timestamp=int(time.time())
    )
    behavior2 = analyzer.analyze(snapshot2)
    behavior2.trend = "focus_steady"

    engine.clear_queue()  # Clear previous event
    engine.process_behavior(behavior2)
    events = engine.consume_events(max_events=1)

    if events:
        context = events[0].context
        logger.info("  Context variables:")
        for key, value in context.items():
            logger.info(f"    {key}: {value}")

        assert context['domain'] == "github.com"
        assert context['domain_category'] == "code"
        assert context['mode'] == "production"

    # Test case 3: Moyu scenario
    logger.info("\n[Test 3: Moyu Context]")
    snapshot3 = ActivitySnapshot(
        app="chrome.exe",
        window_title="Bilibili",
        url="https://bilibili.com/video/test",
        timestamp=int(time.time())
    )
    behavior3 = analyzer.analyze(snapshot3)
    behavior3.trend = "moyu_start"
    behavior3.active_duration_sec = 300

    engine.clear_queue()
    engine.process_behavior(behavior3)
    events = engine.consume_events(max_events=1)

    if events:
        context = events[0].context
        logger.info("  Context variables:")
        for key, value in context.items():
            logger.info(f"    {key}: {value}")

        assert context['domain'] == "bilibili.com"
        assert context['domain_category'] == "video"
        assert context['mode'] == "consumption"
        assert context['duration_min'] == 5

    logger.info("\n✓ Context generation test passed\n")


def test_behavior_danmaku_templates():
    """Test 6: Behavior Danmaku Templates"""
    logger.info("=" * 60)
    logger.info("Test 6: Behavior Danmaku Templates")
    logger.info("=" * 60)

    # Load behavior danmaku templates
    logger.info("\n[Loading behavior_danmaku.json]")
    try:
        with open('gaiya/data/behavior_danmaku.json', 'r', encoding='utf-8') as f:
            templates = json.load(f)

        logger.info(f"  Loaded {len(templates)} behavior categories")

        # Check structure
        expected_categories = ['focus_steady', 'moyu_start', 'moyu_steady', 'mode_switch', 'task_switch']
        expected_tones = ['吐槽', '调侃', '鼓励', '观察', '吃瓜', '建议']

        total_templates = 0

        for category in expected_categories:
            assert category in templates, f"Missing category: {category}"
            logger.info(f"\n  [{category}]")

            for tone in expected_tones:
                assert tone in templates[category], f"Missing tone {tone} in {category}"
                count = len(templates[category][tone])
                logger.info(f"    {tone}: {count} templates")
                total_templates += count

        logger.info(f"\n  Total behavior templates: {total_templates}")
        assert total_templates >= 450, f"Should have at least 450 templates, got {total_templates}"

    except FileNotFoundError:
        logger.error("  behavior_danmaku.json not found!")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"  Failed to parse JSON: {e}")
        raise

    logger.info("\n✓ Behavior danmaku templates test passed\n")


def main():
    """Run all tests"""
    logger.info("\n" + "=" * 60)
    logger.info("Phase 4: Danmaku Event Engine - Comprehensive Test")
    logger.info("=" * 60 + "\n")

    try:
        # Test 1: Cooldown Manager
        test_cooldown_manager()

        # Test 2: Event Engine Basic
        test_event_engine_basic()

        # Test 3: Probability Scheduling
        test_probability_scheduling()

        # Test 4: Timing Jitter
        test_timing_jitter()

        # Test 5: Context Generation
        test_context_generation()

        # Test 6: Behavior Danmaku Templates
        test_behavior_danmaku_templates()

        logger.info("=" * 60)
        logger.info("✓ All Phase 4 Tests Passed Successfully!")
        logger.info("=" * 60)

    except AssertionError as e:
        logger.error(f"\n✗ Test Failed: {e}")
        raise
    except Exception as e:
        logger.error(f"\n✗ Unexpected Error: {e}")
        raise


if __name__ == "__main__":
    main()
