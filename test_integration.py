"""
Integration Test for Behavior Danmaku System

Tests the complete integration:
- BehaviorDanmakuManager initialization
- DanmakuManager integration
- Config loading
- Behavior danmaku generation

Usage:
    python test_integration.py
"""

import json
import logging
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)

logger = logging.getLogger(__name__)


def test_behavior_danmaku_manager():
    """Test 1: Behavior Danmaku Manager Initialization"""
    logger.info("=" * 60)
    logger.info("Test 1: Behavior Danmaku Manager Initialization")
    logger.info("=" * 60)

    # Load config
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info("✓ Config loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise

    # Check behavior_recognition config
    if 'behavior_recognition' in config:
        logger.info("✓ behavior_recognition config found")
        br_config = config['behavior_recognition']
        logger.info(f"  - enabled: {br_config.get('enabled')}")
        logger.info(f"  - collection_interval: {br_config.get('collection_interval')}s")
        logger.info(f"  - trigger_probability: {br_config.get('trigger_probability')}")
    else:
        logger.warning("behavior_recognition config not found in config.json")

    # Initialize BehaviorDanmakuManager
    logger.info("\nInitializing BehaviorDanmakuManager...")
    try:
        from gaiya.core.behavior_danmaku_manager import BehaviorDanmakuManager
        behavior_manager = BehaviorDanmakuManager(config, logger)

        stats = behavior_manager.get_statistics()
        logger.info("✓ BehaviorDanmakuManager initialized successfully")
        logger.info(f"  Statistics: {stats}")

    except Exception as e:
        logger.error(f"Failed to initialize BehaviorDanmakuManager: {e}", exc_info=True)
        raise

    logger.info("\n✓ Test 1 passed\n")
    return behavior_manager


def test_danmaku_manager_integration():
    """Test 2: DanmakuManager Integration"""
    logger.info("=" * 60)
    logger.info("Test 2: DanmakuManager Integration")
    logger.info("=" * 60)

    # Load config
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Initialize DanmakuManager
    logger.info("\nInitializing DanmakuManager...")
    try:
        from gaiya.core.danmaku_manager import DanmakuManager
        app_dir = "."
        danmaku_manager = DanmakuManager(app_dir, config, logger)

        logger.info("✓ DanmakuManager initialized successfully")

        # Check if behavior_danmaku_manager is integrated
        if hasattr(danmaku_manager, 'behavior_danmaku_manager'):
            if danmaku_manager.behavior_danmaku_manager:
                logger.info("✓ BehaviorDanmakuManager is integrated")
                stats = danmaku_manager.behavior_danmaku_manager.get_statistics()
                logger.info(f"  Statistics: {stats}")
            else:
                logger.warning("BehaviorDanmakuManager failed to initialize")
        else:
            logger.error("behavior_danmaku_manager attribute not found")
            raise AssertionError("BehaviorDanmakuManager not integrated")

    except Exception as e:
        logger.error(f"Failed to test DanmakuManager integration: {e}", exc_info=True)
        raise

    logger.info("\n✓ Test 2 passed\n")


def test_behavior_templates():
    """Test 3: Behavior Templates Loading"""
    logger.info("=" * 60)
    logger.info("Test 3: Behavior Templates Loading")
    logger.info("=" * 60)

    try:
        with open('gaiya/data/behavior_danmaku.json', 'r', encoding='utf-8') as f:
            templates = json.load(f)

        logger.info(f"✓ Loaded {len(templates)} behavior categories")

        total_templates = 0
        for category, tones in templates.items():
            category_count = sum(len(tone_templates) for tone_templates in tones.values())
            total_templates += category_count
            logger.info(f"  - {category}: {category_count} templates")

        logger.info(f"\n  Total: {total_templates} behavior templates")

        # Verify structure
        expected_categories = ['focus_steady', 'moyu_start', 'moyu_steady', 'mode_switch', 'task_switch']
        expected_tones = ['吐槽', '调侃', '鼓励', '观察', '吃瓜', '建议']

        for category in expected_categories:
            assert category in templates, f"Missing category: {category}"
            for tone in expected_tones:
                assert tone in templates[category], f"Missing tone {tone} in {category}"

        logger.info("\n✓ Template structure validated")

    except FileNotFoundError:
        logger.error("behavior_danmaku.json not found!")
        raise
    except Exception as e:
        logger.error(f"Failed to load behavior templates: {e}", exc_info=True)
        raise

    logger.info("\n✓ Test 3 passed\n")


def test_config_reload():
    """Test 4: Config Reload"""
    logger.info("=" * 60)
    logger.info("Test 4: Config Reload")
    logger.info("=" * 60)

    # Load config
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Initialize managers
    from gaiya.core.danmaku_manager import DanmakuManager
    danmaku_manager = DanmakuManager(".", config, logger)

    logger.info("✓ DanmakuManager initialized")

    # Modify config
    test_config = config.copy()
    test_config['behavior_recognition'] = test_config.get('behavior_recognition', {}).copy()
    test_config['behavior_recognition']['trigger_probability'] = 0.5

    logger.info("\nReloading config with modified trigger_probability=0.5...")

    try:
        danmaku_manager.reload_config(test_config)
        logger.info("✓ Config reloaded successfully")

        if danmaku_manager.behavior_danmaku_manager:
            new_prob = danmaku_manager.behavior_danmaku_manager.trigger_probability
            logger.info(f"  New trigger_probability: {new_prob}")
            assert new_prob == 0.5, f"Expected 0.5, got {new_prob}"
            logger.info("✓ Config change applied correctly")

    except Exception as e:
        logger.error(f"Failed to reload config: {e}", exc_info=True)
        raise

    logger.info("\n✓ Test 4 passed\n")


def main():
    """Run all integration tests"""
    logger.info("\n" + "=" * 60)
    logger.info("Behavior Danmaku System - Integration Test")
    logger.info("=" * 60 + "\n")

    try:
        # Test 1: Behavior Danmaku Manager
        behavior_manager = test_behavior_danmaku_manager()

        # Test 2: DanmakuManager Integration
        test_danmaku_manager_integration()

        # Test 3: Behavior Templates
        test_behavior_templates()

        # Test 4: Config Reload
        test_config_reload()

        logger.info("=" * 60)
        logger.info("✓ All Integration Tests Passed!")
        logger.info("=" * 60)

    except AssertionError as e:
        logger.error(f"\n✗ Test Failed: {e}")
        raise
    except Exception as e:
        logger.error(f"\n✗ Unexpected Error: {e}")
        raise


if __name__ == "__main__":
    main()
