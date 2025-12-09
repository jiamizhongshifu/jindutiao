"""
Danmaku Event Engine - Event-driven danmaku triggering system

Integrates behavior recognition with danmaku display:
- Event-driven architecture with priority queue
- Behavior trend detection and mapping to danmaku categories
- Probability-based scheduling (30-50% trigger rate)
- Timing jitter (±5s randomness)
- Cooldown management integration
- Context-aware template variable substitution

Author: GaiYa Team
Date: 2025-12-08
"""

import time
import random
import logging
import queue
import threading
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from .behavior_analyzer import BehaviorInfo, BehaviorTrend
from .cooldown_manager import CooldownManager, CooldownConfig


class EventPriority(Enum):
    """Event priority levels"""
    HIGH = 1        # 摸鱼开始, 专注崩溃
    MEDIUM = 2      # 专注稳定, 任务切换
    LOW = 3         # 模式切换, 其他


@dataclass
class DanmakuEvent:
    """
    Danmaku event data structure

    Attributes:
        category: Event category (matches BehaviorTrend)
        priority: Event priority
        behavior_info: Associated BehaviorInfo
        timestamp: Event creation timestamp
        context: Additional context variables for template
    """
    category: str
    priority: EventPriority
    behavior_info: BehaviorInfo
    timestamp: float
    context: Dict = None

    def __lt__(self, other):
        """Comparison for priority queue (lower value = higher priority)"""
        return self.priority.value < other.priority.value


class DanmakuEventEngine:
    """
    Danmaku Event Engine - Event-driven danmaku triggering

    Features:
    - Behavior trend → Danmaku event mapping
    - Priority queue for event management
    - Probability-based triggering (30-50%)
    - Timing jitter (±5s)
    - Cooldown management
    - Template context generation
    - Thread-safe operations
    """

    def __init__(self,
                 cooldown_manager: Optional[CooldownManager] = None,
                 trigger_probability: float = 0.4,
                 jitter_range_sec: int = 5,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize Danmaku Event Engine

        Args:
            cooldown_manager: CooldownManager instance
            trigger_probability: Base trigger probability (0.0-1.0)
            jitter_range_sec: Timing jitter range (±seconds)
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

        # Components
        self.cooldown_manager = cooldown_manager or CooldownManager(logger=logger)

        # Configuration
        self.trigger_probability = trigger_probability
        self.jitter_range_sec = jitter_range_sec

        # Event queue (priority queue)
        self.event_queue: queue.PriorityQueue = queue.PriorityQueue()

        # Event callbacks
        self.event_handlers: Dict[str, List[Callable]] = {}

        # Statistics
        self.total_events = 0
        self.triggered_events = 0
        self.suppressed_by_probability = 0
        self.suppressed_by_cooldown = 0

        # Thread safety
        self.lock = threading.Lock()

        # Behavior trend → Priority mapping
        self.priority_map = {
            BehaviorTrend.MOYU_START.value: EventPriority.HIGH,
            BehaviorTrend.FOCUS_STEADY.value: EventPriority.MEDIUM,
            BehaviorTrend.MOYU_STEADY.value: EventPriority.MEDIUM,
            BehaviorTrend.MODE_SWITCH.value: EventPriority.LOW,
            BehaviorTrend.TASK_SWITCH.value: EventPriority.LOW,
        }

        self.logger.info(f"DanmakuEventEngine initialized: "
                        f"probability={trigger_probability}, "
                        f"jitter=±{jitter_range_sec}s")

    def process_behavior(self, behavior_info: BehaviorInfo):
        """
        Process behavior info and potentially trigger danmaku event

        Args:
            behavior_info: BehaviorInfo from BehaviorAnalyzer
        """
        with self.lock:
            self.total_events += 1

            # Ignore NONE trends
            if not behavior_info.trend or behavior_info.trend == BehaviorTrend.NONE.value:
                return

            # Step 1: Probability filtering
            if not self._should_trigger():
                self.suppressed_by_probability += 1
                self.logger.debug(f"Event suppressed by probability: {behavior_info.trend}")
                return

            # Step 2: Determine event priority
            priority = self.priority_map.get(behavior_info.trend, EventPriority.LOW)

            # Step 3: Generate context variables
            context = self._generate_context(behavior_info)

            # Step 4: Create event
            event = DanmakuEvent(
                category=behavior_info.trend,
                priority=priority,
                behavior_info=behavior_info,
                timestamp=time.time(),
                context=context
            )

            # Step 5: Add to queue
            self.event_queue.put(event)
            self.logger.info(f"Event queued: {behavior_info.trend} (priority={priority.name})")

    def consume_events(self, max_events: int = 1) -> List[DanmakuEvent]:
        """
        Consume events from queue (respecting cooldown)

        Args:
            max_events: Maximum number of events to consume

        Returns:
            List of events to be displayed
        """
        events_to_show = []

        for _ in range(max_events):
            if self.event_queue.empty():
                break

            try:
                event = self.event_queue.get_nowait()

                # Get tone for cooldown check (use first available or default)
                tone = self._get_tone_for_category(event.category)

                # Check cooldown
                if not self.cooldown_manager.can_show_danmaku(event.category, tone):
                    self.suppressed_by_cooldown += 1
                    self.logger.debug(f"Event suppressed by cooldown: {event.category}")
                    continue

                # Apply timing jitter
                jittered_timestamp = self._apply_jitter(event.timestamp)
                event.timestamp = jittered_timestamp

                # Record cooldown
                self.cooldown_manager.record_danmaku_shown(event.category, tone)

                events_to_show.append(event)
                self.triggered_events += 1

            except queue.Empty:
                break

        return events_to_show

    def _should_trigger(self) -> bool:
        """
        Probability-based trigger decision

        Returns:
            True if should trigger, False otherwise
        """
        actual_prob = random.random()
        triggered = actual_prob < self.trigger_probability
        self.logger.debug(f"🎲 Probability check: {actual_prob:.3f} vs threshold:{self.trigger_probability:.3f} → {'triggered' if triggered else 'suppressed'}")
        return triggered

    def _apply_jitter(self, timestamp: float) -> float:
        """
        Apply timing jitter to timestamp

        Args:
            timestamp: Original timestamp

        Returns:
            Jittered timestamp
        """
        jitter = random.uniform(-self.jitter_range_sec, self.jitter_range_sec)
        return timestamp + jitter

    def _generate_context(self, behavior_info: BehaviorInfo) -> Dict:
        """
        Generate template context variables from behavior info

        Args:
            behavior_info: BehaviorInfo instance

        Returns:
            Dictionary with context variables
        """
        context = {
            'app': behavior_info.app,
            'app_type': behavior_info.app_type,
            'domain': behavior_info.domain or '未知网站',
            'domain_category': behavior_info.domain_category,
            'mode': behavior_info.mode,
            'trend': behavior_info.trend,
            'duration_min': behavior_info.active_duration_sec // 60,
            'duration_sec': behavior_info.active_duration_sec,
        }

        # Add human-readable descriptions
        mode_names = {
            'production': '生产模式',
            'consumption': '消费模式',
            'neutral': '中性模式',
            'unknown': '未知模式'
        }
        context['mode_name'] = mode_names.get(behavior_info.mode, '未知')

        app_type_names = {
            'browser': '浏览器',
            'ide': '代码编辑器',
            'office': '办公软件',
            'im': '聊天软件',
            'video': '视频软件',
            'player': '音乐播放器',
            'game': '游戏',
            'tool': '工具',
            'system': '系统',
            'other': '其他应用'
        }
        context['app_type_name'] = app_type_names.get(behavior_info.app_type, '未知应用')

        return context

    def _get_tone_for_category(self, category: str) -> str:
        """
        Get recommended tone for event category

        Args:
            category: Event category

        Returns:
            Tone string
        """
        # Map categories to default tones
        tone_map = {
            'moyu_start': '调侃',
            'moyu_steady': '吐槽',
            'focus_steady': '鼓励',
            'mode_switch': '观察',
            'task_switch': '建议',
        }
        return tone_map.get(category, '观察')

    def register_event_handler(self, category: str, handler: Callable):
        """
        Register event handler callback

        Args:
            category: Event category
            handler: Callback function(event: DanmakuEvent)
        """
        if category not in self.event_handlers:
            self.event_handlers[category] = []
        self.event_handlers[category].append(handler)
        self.logger.info(f"Registered handler for category: {category}")

    def unregister_event_handler(self, category: str, handler: Callable):
        """
        Unregister event handler callback

        Args:
            category: Event category
            handler: Callback function to remove
        """
        if category in self.event_handlers:
            self.event_handlers[category].remove(handler)

    def get_statistics(self) -> Dict:
        """
        Get engine statistics

        Returns:
            Dictionary with statistics
        """
        with self.lock:
            return {
                'total_events': self.total_events,
                'triggered_events': self.triggered_events,
                'suppressed_by_probability': self.suppressed_by_probability,
                'suppressed_by_cooldown': self.suppressed_by_cooldown,
                'trigger_rate': f"{100 * self.triggered_events / max(1, self.total_events):.1f}%",
                'queue_size': self.event_queue.qsize(),
                'cooldown_stats': self.cooldown_manager.get_statistics()
            }

    def clear_queue(self):
        """Clear event queue"""
        with self.lock:
            while not self.event_queue.empty():
                try:
                    self.event_queue.get_nowait()
                except queue.Empty:
                    break
            self.logger.info("Event queue cleared")

    def update_trigger_probability(self, probability: float):
        """
        Update trigger probability

        Args:
            probability: New probability (0.0-1.0)
        """
        if 0.0 <= probability <= 1.0:
            self.trigger_probability = probability
            self.logger.info(f"Trigger probability updated to {probability}")
        else:
            self.logger.warning(f"Invalid probability: {probability}, must be 0.0-1.0")

    def update_jitter_range(self, jitter_range_sec: int):
        """
        Update timing jitter range

        Args:
            jitter_range_sec: New jitter range (±seconds)
        """
        self.jitter_range_sec = jitter_range_sec
        self.logger.info(f"Jitter range updated to ±{jitter_range_sec}s")
