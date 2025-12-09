"""
Behavior Danmaku Manager - 行为识别弹幕管理器

整合行为识别系统与弹幕显示系统:
- 后台采集用户活动
- 分析行为模式
- 触发行为感知弹幕
- 与现有时间弹幕并行工作

Author: GaiYa Team
Date: 2025-12-08
"""

import json
import random
import logging
import threading
import time
from typing import Dict, List, Optional
from pathlib import Path

from gaiya.core.activity_collector import ActivityCollector, ActivitySnapshot
from gaiya.core.behavior_analyzer import BehaviorAnalyzer, BehaviorInfo
from gaiya.core.danmaku_event_engine import DanmakuEventEngine, DanmakuEvent
from gaiya.core.cooldown_manager import CooldownManager, CooldownConfig
from gaiya.utils import path_utils


class BehaviorDanmakuManager:
    """
    行为识别弹幕管理器

    Features:
    - 后台活动采集(独立线程)
    - 行为分析与趋势检测
    - 事件驱动的弹幕触发
    - 与现有DanmakuManager协同工作
    - 配置化控制
    """

    def __init__(self, config: Dict, logger: Optional[logging.Logger] = None):
        """
        Initialize Behavior Danmaku Manager

        Args:
            config: Application configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

        # 行为识别配置
        behavior_config = config.get("behavior_recognition", {})
        self.enabled = behavior_config.get("enabled", False)
        self.collection_interval = behavior_config.get("collection_interval", 5)
        self.trigger_probability = behavior_config.get("trigger_probability", 0.4)

        # 冷却配置
        cooldown_config = CooldownConfig(
            global_cooldown_sec=behavior_config.get("global_cooldown", 30),
            category_cooldown_sec=behavior_config.get("category_cooldown", 60),
            tone_cooldown_sec=behavior_config.get("tone_cooldown", 120)
        )

        # 初始化组件
        self.activity_collector = ActivityCollector(
            collection_interval=self.collection_interval,
            logger=logger
        )

        self.behavior_analyzer = BehaviorAnalyzer(logger=logger)

        self.cooldown_manager = CooldownManager(
            config=cooldown_config,
            logger=logger
        )

        self.event_engine = DanmakuEventEngine(
            cooldown_manager=self.cooldown_manager,
            trigger_probability=self.trigger_probability,
            jitter_range_sec=5,
            logger=logger
        )

        # 弹幕模板库
        self.behavior_templates: Dict = {}
        self._load_behavior_templates()

        # 待显示的弹幕队列 (传递给 DanmakuManager)
        self.pending_danmakus: List[str] = []
        self.pending_lock = threading.Lock()

        # 后台线程控制
        self.running = False
        self.collection_thread: Optional[threading.Thread] = None

        self.logger.info(f"BehaviorDanmakuManager initialized: enabled={self.enabled}")

    def _load_behavior_templates(self):
        """加载行为弹幕模板库"""
        template_path = path_utils.get_resource_path("gaiya/data/behavior_danmaku.json")
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                self.behavior_templates = json.load(f)

            total = sum(
                len(tones)
                for category in self.behavior_templates.values()
                for tones in category.values()
            )
            self.logger.info(f"Loaded {total} behavior danmaku templates from {len(self.behavior_templates)} categories")

        except FileNotFoundError:
            self.logger.error(f"Behavior template file not found: {template_path}")
            self.behavior_templates = {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse behavior templates JSON: {e}")
            self.behavior_templates = {}
        except Exception as e:
            self.logger.error(f"Failed to load behavior templates: {e}")
            self.behavior_templates = {}

    def start(self):
        """启动后台活动采集"""
        if not self.enabled:
            self.logger.info("Behavior recognition is disabled")
            return

        if self.running:
            self.logger.warning("Behavior collection already running")
            return

        self.running = True
        self.collection_thread = threading.Thread(
            target=self._collection_loop,
            daemon=True,
            name="BehaviorCollectionThread"
        )
        self.collection_thread.start()
        self.logger.info("Behavior collection thread started")

    def stop(self):
        """停止后台活动采集"""
        if not self.running:
            return

        self.running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        self.logger.info("Behavior collection thread stopped")

    def _collection_loop(self):
        """后台活动采集循环"""
        self.logger.info("Behavior collection loop started")

        while self.running:
            loop_start = time.time()
            try:
                # 采集活动快照
                snapshot = self.activity_collector.collect_once()

                if snapshot:
                    # 分析行为
                    behavior_info = self.behavior_analyzer.analyze(snapshot)

                    # 处理行为信息
                    self._process_behavior(behavior_info)

                # Performance monitoring
                loop_elapsed = (time.time() - loop_start) * 1000  # Convert to ms
                self.logger.debug(f"⏱️ Collection loop cycle: {loop_elapsed:.1f}ms")

                # 等待下一次采集
                time.sleep(self.collection_interval)

            except Exception as e:
                loop_elapsed = (time.time() - loop_start) * 1000
                self.logger.error(f"Error in collection loop: {e} (cycle_time={loop_elapsed:.1f}ms)", exc_info=True)
                time.sleep(self.collection_interval)

        self.logger.info("Behavior collection loop ended")

    def _process_behavior(self, behavior_info: BehaviorInfo):
        """处理行为信息,生成弹幕事件"""
        # 传递给事件引擎
        self.event_engine.process_behavior(behavior_info)

        # 尝试消费事件
        events = self.event_engine.consume_events(max_events=1)

        for event in events:
            # 生成弹幕内容
            danmaku_text = self._generate_danmaku_from_event(event)

            if danmaku_text:
                # 添加到待显示队列
                with self.pending_lock:
                    self.pending_danmakus.append(danmaku_text)

                self.logger.info(f"🎯 Generated behavior danmaku: {danmaku_text[:50]}...")

    def _generate_danmaku_from_event(self, event: DanmakuEvent) -> Optional[str]:
        """从事件生成弹幕内容"""
        category = event.category
        context = event.context

        # 检查模板库
        if category not in self.behavior_templates:
            self.logger.warning(f"Category not found in templates: {category}")
            return None

        category_templates = self.behavior_templates[category]

        # 获取推荐语调
        tone = self._get_tone_for_category(category)

        if tone not in category_templates:
            self.logger.warning(f"Tone {tone} not found in category {category}")
            # 随机选择一个可用语调
            available_tones = list(category_templates.keys())
            if not available_tones:
                return None
            tone = random.choice(available_tones)

        # 随机选择模板
        templates = category_templates[tone]
        if not templates:
            return None

        template = random.choice(templates)

        # 替换上下文变量
        danmaku_text = self._apply_context_variables(template, context)

        return danmaku_text

    def _get_tone_for_category(self, category: str) -> str:
        """获取分类对应的推荐语调"""
        tone_map = {
            'focus_steady': '鼓励',
            'moyu_start': '调侃',
            'moyu_steady': '吐槽',
            'mode_switch': '观察',
            'task_switch': '建议',
        }
        return tone_map.get(category, '观察')

    def _apply_context_variables(self, template: str, context: Dict) -> str:
        """应用上下文变量替换"""
        result = template

        # 替换所有上下文变量
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))

        return result

    def get_pending_danmaku(self) -> Optional[str]:
        """获取一条待显示的弹幕"""
        with self.pending_lock:
            if self.pending_danmakus:
                return self.pending_danmakus.pop(0)
        return None

    def has_pending_danmaku(self) -> bool:
        """检查是否有待显示的弹幕"""
        with self.pending_lock:
            return len(self.pending_danmakus) > 0

    def reload_config(self, config: Dict):
        """重新加载配置"""
        self.config = config

        behavior_config = config.get("behavior_recognition", {})
        old_enabled = self.enabled
        self.enabled = behavior_config.get("enabled", False)

        # 更新配置
        self.collection_interval = behavior_config.get("collection_interval", 5)
        self.trigger_probability = behavior_config.get("trigger_probability", 0.4)

        # 更新事件引擎
        self.event_engine.update_trigger_probability(self.trigger_probability)

        # 更新冷却管理器
        self.cooldown_manager.update_config(
            global_cooldown_sec=behavior_config.get("global_cooldown", 30),
            category_cooldown_sec=behavior_config.get("category_cooldown", 60),
            tone_cooldown_sec=behavior_config.get("tone_cooldown", 120)
        )

        # 启动/停止采集线程
        if self.enabled and not old_enabled:
            self.start()
        elif not self.enabled and old_enabled:
            self.stop()

        self.logger.info(f"Config reloaded: enabled={self.enabled}")

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            'enabled': self.enabled,
            'running': self.running,
            'pending_danmakus': len(self.pending_danmakus),
            'collection_interval': self.collection_interval,
            'trigger_probability': self.trigger_probability,
            'engine_stats': self.event_engine.get_statistics(),
            'cooldown_stats': self.cooldown_manager.get_statistics(),
            'template_categories': len(self.behavior_templates)
        }
