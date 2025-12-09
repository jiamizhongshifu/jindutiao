"""
Cooldown Manager - Manage danmaku cooldown timing

Prevents danmaku spam by enforcing cooldown periods:
- Global cooldown: 30s minimum between any danmaku
- Category cooldown: 60s minimum between same-category danmaku
- Thread-safe with lock mechanism
- Supports cooldown reset for testing

Author: GaiYa Team
Date: 2025-12-08
"""

import time
import logging
import threading
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class CooldownConfig:
    """Cooldown configuration"""
    global_cooldown_sec: int = 30      # Global cooldown (30s)
    category_cooldown_sec: int = 60    # Category cooldown (60s)
    tone_cooldown_sec: int = 120       # Same tone cooldown (120s)


class CooldownManager:
    """
    Cooldown Manager - Prevent danmaku spam

    Features:
    - Global cooldown tracking (30s default)
    - Per-category cooldown tracking (60s default)
    - Per-tone cooldown tracking (120s default)
    - Thread-safe operations
    - Runtime cooldown adjustment
    - Statistics tracking
    """

    def __init__(self,
                 config: Optional[CooldownConfig] = None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize Cooldown Manager

        Args:
            config: Cooldown configuration
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.config = config or CooldownConfig()

        # Cooldown tracking
        self.last_danmaku_time: float = 0
        self.last_category_time: Dict[str, float] = {}
        self.last_tone_time: Dict[str, float] = {}

        # Thread safety
        self.lock = threading.Lock()

        # Statistics
        self.total_checks = 0
        self.blocked_by_global = 0
        self.blocked_by_category = 0
        self.blocked_by_tone = 0
        self.allowed_count = 0

        self.logger.info(f"CooldownManager initialized: "
                        f"global={self.config.global_cooldown_sec}s, "
                        f"category={self.config.category_cooldown_sec}s, "
                        f"tone={self.config.tone_cooldown_sec}s")

    def can_show_danmaku(self, category: str, tone: str) -> bool:
        """
        Check if danmaku can be shown based on cooldown rules

        Args:
            category: Danmaku category (e.g., "moyu_start", "focus_steady")
            tone: Danmaku tone (e.g., "吐槽", "鼓励")

        Returns:
            True if danmaku can be shown, False otherwise
        """
        with self.lock:
            self.total_checks += 1
            current_time = time.time()

            # Check 1: Global cooldown
            if current_time - self.last_danmaku_time < self.config.global_cooldown_sec:
                self.blocked_by_global += 1
                self.logger.debug(f"Blocked by global cooldown: "
                                f"{current_time - self.last_danmaku_time:.1f}s < "
                                f"{self.config.global_cooldown_sec}s")
                return False

            # Check 2: Category cooldown
            if category in self.last_category_time:
                time_since_category = current_time - self.last_category_time[category]
                if time_since_category < self.config.category_cooldown_sec:
                    self.blocked_by_category += 1
                    self.logger.debug(f"Blocked by category cooldown ({category}): "
                                    f"{time_since_category:.1f}s < "
                                    f"{self.config.category_cooldown_sec}s")
                    return False

            # Check 3: Tone cooldown
            if tone in self.last_tone_time:
                time_since_tone = current_time - self.last_tone_time[tone]
                if time_since_tone < self.config.tone_cooldown_sec:
                    self.blocked_by_tone += 1
                    self.logger.debug(f"Blocked by tone cooldown ({tone}): "
                                    f"{time_since_tone:.1f}s < "
                                    f"{self.config.tone_cooldown_sec}s")
                    return False

            # All checks passed
            self.allowed_count += 1
            return True

    def record_danmaku_shown(self, category: str, tone: str):
        """
        Record that a danmaku was shown (update cooldown timers)

        Args:
            category: Danmaku category
            tone: Danmaku tone
        """
        with self.lock:
            current_time = time.time()
            self.last_danmaku_time = current_time
            self.last_category_time[category] = current_time
            self.last_tone_time[tone] = current_time

            # Get remaining cooldowns for next event
            next_global = self.config.global_cooldown_sec
            next_category = self.config.category_cooldown_sec
            next_tone = self.config.tone_cooldown_sec

            self.logger.info(f"Danmaku recorded: category={category}, tone={tone}")
            self.logger.debug(f"❄️ Cooldown activated - global:{next_global}s, category:{next_category}s, tone:{next_tone}s")

    def get_remaining_cooldown(self, category: str = None, tone: str = None) -> Dict[str, float]:
        """
        Get remaining cooldown time for different types

        Args:
            category: Optional category to check
            tone: Optional tone to check

        Returns:
            Dictionary with remaining cooldown times (seconds)
        """
        with self.lock:
            current_time = time.time()
            result = {}

            # Global cooldown
            global_remaining = self.config.global_cooldown_sec - (current_time - self.last_danmaku_time)
            result['global'] = max(0, global_remaining)

            # Category cooldown
            if category and category in self.last_category_time:
                category_remaining = self.config.category_cooldown_sec - \
                                    (current_time - self.last_category_time[category])
                result['category'] = max(0, category_remaining)
            else:
                result['category'] = 0

            # Tone cooldown
            if tone and tone in self.last_tone_time:
                tone_remaining = self.config.tone_cooldown_sec - \
                                (current_time - self.last_tone_time[tone])
                result['tone'] = max(0, tone_remaining)
            else:
                result['tone'] = 0

            return result

    def reset_cooldown(self, reset_type: str = "all"):
        """
        Reset cooldown timers (for testing or manual control)

        Args:
            reset_type: "all", "global", "category", or "tone"
        """
        with self.lock:
            if reset_type == "all":
                self.last_danmaku_time = 0
                self.last_category_time.clear()
                self.last_tone_time.clear()
                self.logger.info("All cooldowns reset")
            elif reset_type == "global":
                self.last_danmaku_time = 0
                self.logger.info("Global cooldown reset")
            elif reset_type == "category":
                self.last_category_time.clear()
                self.logger.info("Category cooldowns reset")
            elif reset_type == "tone":
                self.last_tone_time.clear()
                self.logger.info("Tone cooldowns reset")

    def update_config(self,
                     global_cooldown_sec: int = None,
                     category_cooldown_sec: int = None,
                     tone_cooldown_sec: int = None):
        """
        Update cooldown configuration at runtime

        Args:
            global_cooldown_sec: New global cooldown (seconds)
            category_cooldown_sec: New category cooldown (seconds)
            tone_cooldown_sec: New tone cooldown (seconds)
        """
        with self.lock:
            if global_cooldown_sec is not None:
                self.config.global_cooldown_sec = global_cooldown_sec
                self.logger.info(f"Global cooldown updated to {global_cooldown_sec}s")

            if category_cooldown_sec is not None:
                self.config.category_cooldown_sec = category_cooldown_sec
                self.logger.info(f"Category cooldown updated to {category_cooldown_sec}s")

            if tone_cooldown_sec is not None:
                self.config.tone_cooldown_sec = tone_cooldown_sec
                self.logger.info(f"Tone cooldown updated to {tone_cooldown_sec}s")

    def get_statistics(self) -> Dict:
        """
        Get cooldown statistics

        Returns:
            Dictionary with statistics
        """
        with self.lock:
            return {
                'total_checks': self.total_checks,
                'allowed': self.allowed_count,
                'blocked_by_global': self.blocked_by_global,
                'blocked_by_category': self.blocked_by_category,
                'blocked_by_tone': self.blocked_by_tone,
                'allow_rate': f"{100 * self.allowed_count / max(1, self.total_checks):.1f}%",
                'active_categories': len(self.last_category_time),
                'active_tones': len(self.last_tone_time)
            }

    def cleanup_old_cooldowns(self, max_age_sec: int = 3600):
        """
        Clean up old cooldown entries (older than max_age_sec)

        Args:
            max_age_sec: Maximum age to keep (default: 1 hour)
        """
        with self.lock:
            current_time = time.time()

            # Cleanup categories
            categories_to_remove = [
                cat for cat, ts in self.last_category_time.items()
                if current_time - ts > max_age_sec
            ]
            for cat in categories_to_remove:
                del self.last_category_time[cat]

            # Cleanup tones
            tones_to_remove = [
                tone for tone, ts in self.last_tone_time.items()
                if current_time - ts > max_age_sec
            ]
            for tone in tones_to_remove:
                del self.last_tone_time[tone]

            if categories_to_remove or tones_to_remove:
                self.logger.debug(f"Cleaned up {len(categories_to_remove)} categories, "
                                f"{len(tones_to_remove)} tones")
