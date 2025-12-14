"""
Danmaku Manager - 弹幕管理器
管理弹幕的生成、更新和渲染
"""

import json
import os
import random
import time
from datetime import datetime
from typing import List, Dict, Optional
from PySide6.QtCore import QTimer
from PySide6.QtGui import QPainter, QFont, QColor, QPen, QPainterPath
from PySide6.QtCore import Qt, QRectF
from gaiya.utils import time_utils, path_utils


class Danmaku:
    """单条弹幕对象"""

    def __init__(self, content: str, x: float, y: float, speed: float,
                 color: str = "#FFFFFF", font_size: int = 14, opacity: float = 1.0):
        self.id = f"danmaku_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        self.content = content
        self.x = x
        self.y = y
        self.speed = speed
        self.color = color
        self.font_size = font_size
        self.opacity = opacity
        self.create_time = time.time()
        self.source = "preset"
        self.width = 0  # Will be calculated after rendering

    def update(self, delta_time: float = 1.0):
        """更新弹幕位置"""
        self.x -= self.speed * delta_time

    def is_out_of_screen(self) -> bool:
        """判断弹幕是否已完全移出屏幕"""
        return self.x + self.width < 0


class DanmakuManager:
    """弹幕管理器"""

    def __init__(self, app_dir: str, config: Dict, logger=None):
        self.app_dir = app_dir
        self.config = config
        self.logger = logger
        self.danmakus: List[Danmaku] = []
        self.presets: Dict[str, List[str]] = {}
        self.last_spawn_time = 0
        self.enabled = False

        # 防重复机制: 记录最近20条弹幕历史
        self.recent_history: List[str] = []
        self.max_history = 20

        # 当前任务信息缓存(用于模板替换)
        self.current_task_name = ""
        self.current_task_start_time = 0
        self.current_task_end_time = 0

        # 行为识别弹幕管理器
        self.behavior_danmaku_manager = None
        try:
            from gaiya.core.behavior_danmaku_manager import BehaviorDanmakuManager
            self.behavior_danmaku_manager = BehaviorDanmakuManager(config, logger)
            self.behavior_danmaku_manager.start()
        except Exception as e:
            if logger:
                logger.warning(f"Failed to initialize behavior danmaku manager: {e}")

        # Load preset danmaku content
        self._load_presets()

        # Load config
        self._load_config()

    def _load_presets(self):
        """加载预设弹幕内容"""
        # 使用 path_utils 获取正确的资源路径（支持PyInstaller打包）
        preset_path = path_utils.get_resource_path("gaiya/data/danmaku_presets.json")
        try:
            with open(preset_path, "r", encoding="utf-8") as f:
                self.presets = json.load(f)
            if self.logger:
                self.logger.info(f"Loaded {len(self.presets)} danmaku preset categories")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to load danmaku presets: {e}")
            # Fallback to default presets
            self.presets = {
                "default": [
                    "时间一去不复返",
                    "珍惜每一分钟",
                    "你今天又进步了!",
                    "坚持就是胜利"
                ]
            }

    def _load_config(self):
        """加载弹幕配置"""
        danmaku_config = self.config.get("danmaku", {})
        self.enabled = danmaku_config.get("enabled", False)
        self.frequency = danmaku_config.get("frequency", 30)  # 默认30秒一条
        self.speed_multiplier = danmaku_config.get("speed", 1.0)  # 速度倍率
        self.font_size = danmaku_config.get("font_size", 14)
        self.opacity = danmaku_config.get("opacity", 1.0)
        self.max_count = danmaku_config.get("max_count", 3)  # 同屏最大弹幕数
        self.y_offset = danmaku_config.get("y_offset", 80)  # 距离进度条的Y轴偏移
        self.color_mode = danmaku_config.get("color_mode", "auto")

    def reload_config(self, config: Dict):
        """重新加载配置"""
        self.config = config
        self._load_config()

        # 重新加载行为识别配置
        if self.behavior_danmaku_manager:
            self.behavior_danmaku_manager.reload_config(config)

    def get_task_category(self, tasks: List[Dict], current_time_percentage: float) -> str:
        """根据当前时间获取任务类型"""
        if not tasks:
            return "default"

        # Use actual current time instead of percentage (percentage is for compact mode display, not real time)
        now = datetime.now()
        current_minute = now.hour * 60 + now.minute

        for task in tasks:
            # Parse time strings using time_utils
            task_start = task.get('start', '')
            task_end = task.get('end', '')

            start_seconds = time_utils.time_str_to_seconds(task_start)
            end_seconds = time_utils.time_str_to_seconds(task_end)

            start_minute = start_seconds // 60
            end_minute = end_seconds // 60

            # Handle cross-day tasks
            if end_minute < start_minute:
                if current_minute >= start_minute or current_minute < end_minute:
                    return self._map_task_name_to_category(task.get('task', ''), current_minute)
            else:
                if start_minute <= current_minute < end_minute:
                    return self._map_task_name_to_category(task.get('task', ''), current_minute)

        return "default"

    def _map_task_name_to_category(self, task_name: str, current_minute: int = None) -> str:
        """将任务名称映射到弹幕类别

        Args:
            task_name: 任务名称
            current_minute: 当前时间(分钟数,从0到1440),用于区分早晚通勤
        """
        task_name_lower = task_name.lower()

        # Mapping rules
        if any(keyword in task_name_lower for keyword in ['工作', 'work', '办公', '项目']):
            return "work"
        elif any(keyword in task_name_lower for keyword in ['学习', 'study', '阅读', '课程']):
            return "study"
        elif any(keyword in task_name_lower for keyword in ['休息', 'rest', '放松', '休闲']):
            return "rest"
        elif any(keyword in task_name_lower for keyword in ['运动', 'exercise', '健身', '锻炼']):
            return "exercise"
        elif any(keyword in task_name_lower for keyword in ['会议', 'meeting', '讨论']):
            return "meeting"
        elif any(keyword in task_name_lower for keyword in ['吃饭', 'meal', '午餐', '晚餐', '早餐']):
            return "meal"
        elif any(keyword in task_name_lower for keyword in ['通勤', 'commute', '上班', '下班']):
            # 根据时间区分早晚通勤
            # 早上通勤: 6:00-12:00 (360-720分钟)
            # 晚上通勤: 17:00-21:00 (1020-1260分钟)
            if current_minute is not None:
                if 360 <= current_minute < 720:  # 6:00-12:00
                    return "commute_morning"
                elif 1020 <= current_minute < 1260:  # 17:00-21:00
                    return "commute_evening"
            return "commute"
        elif any(keyword in task_name_lower for keyword in ['娱乐', 'entertainment', '游戏', '看剧']):
            return "entertainment"
        elif any(keyword in task_name_lower for keyword in ['睡觉', 'sleep', '休眠']):
            return "sleep"
        else:
            return "default"

    def should_spawn_danmaku(self, current_time: float) -> bool:
        """判断是否应该生成新弹幕 (添加随机性)"""
        if not self.enabled:
            if self.logger:
                self.logger.debug(f"弹幕未启用")
            return False

        if len(self.danmakus) >= self.max_count:
            if self.logger:
                self.logger.debug(f"弹幕数量已达上限: {len(self.danmakus)}/{self.max_count}")
            return False

        time_since_last = current_time - self.last_spawn_time

        # 添加随机性: 基准频率 ± 30%浮动
        # 例如30秒 → 21-39秒随机
        random_offset = self.frequency * 0.3 * (random.random() * 2 - 1)  # -30% ~ +30%
        threshold = self.frequency + random_offset

        if time_since_last >= threshold:
            if self.logger:
                self.logger.info(f"准备生成新弹幕 (距上次: {time_since_last:.1f}s, 阈值: {threshold:.1f}s)")
            return True

        return False

    def spawn_danmaku(self, screen_width: int, window_height: int,
                     tasks: List[Dict], current_time_percentage: float):
        """生成新弹幕 (支持模板替换和防重复)"""
        # 优先检查行为识别弹幕
        if self.behavior_danmaku_manager and self.behavior_danmaku_manager.has_pending_danmaku():
            content = self.behavior_danmaku_manager.get_pending_danmaku()
            if content:
                self._create_and_add_danmaku(content, screen_width, window_height, "behavior")
                return

        # 回退到时间任务弹幕
        # Get task category and update task info cache
        category = self.get_task_category(tasks, current_time_percentage)
        self._update_current_task_info(tasks, current_time_percentage)

        # Fallback to default if category not found or has no content
        if category not in self.presets or not self.presets[category]:
            category = "default"

        # 防重复机制: 选择不在历史中的内容
        content = self._select_non_repeat_content(category)

        # 模板替换: 处理动态变量
        content = self._apply_template(content, current_time_percentage)

        # 添加到历史记录
        self._add_to_history(content)

        # Create and add danmaku
        self._create_and_add_danmaku(content, screen_width, window_height, category)

    def _create_and_add_danmaku(self, content: str, screen_width: int,
                                window_height: int, category: str):
        """创建并添加弹幕"""
        # Calculate position
        # X: start from right edge + some buffer
        x = screen_width + 50

        # Y: 添加随机偏移,避免每次都在完全相同的高度
        base_y = window_height - self.y_offset
        y_variation = len(self.danmakus) * 30  # 基础错开
        random_offset = random.randint(-15, 15)  # 添加 ±15px 随机偏移
        y = base_y - y_variation + random_offset

        # Calculate speed (pixels per second for delta_time approach)
        base_speed = screen_width / 10
        speed = base_speed * self.speed_multiplier

        # Create danmaku
        color = self._get_danmaku_color(category)
        danmaku = Danmaku(content, x, y, speed, color, self.font_size, self.opacity)

        self.danmakus.append(danmaku)
        self.last_spawn_time = time.time()

        if self.logger:
            self.logger.info(f"✨ 生成弹幕: \"{content}\" | 类别:{category} | 位置:({x:.0f}, {y:.0f}) | 颜色:{color}")

    def _get_danmaku_color(self, category: str) -> str:
        """根据类别获取弹幕颜色"""
        if self.color_mode == "auto":
            color_map = {
                "work": "#4CAF50",      # Green - 工作
                "study": "#2196F3",     # Blue - 学习
                "rest": "#FFC107",      # Amber - 休息
                "exercise": "#F44336",  # Red - 运动
                "meeting": "#9C27B0",   # Purple - 会议
                "meal": "#FF9800",      # Orange - 用餐
                "commute": "#00BCD4",   # Cyan - 通勤
                "commute_morning": "#4DD0E1",  # Light Cyan - 早晨通勤
                "commute_evening": "#0097A7",  # Dark Cyan - 晚间通勤
                "entertainment": "#E91E63",  # Pink - 娱乐
                "sleep": "#3F51B5",     # Indigo - 睡眠
                "motivational": "#FFEB3B",  # Yellow - 励志
                # 行为识别弹幕颜色
                "behavior": "#00E676",  # Bright Green - 行为感知
                "focus_steady": "#00E676",  # Bright Green - 专注稳定
                "moyu_start": "#FF6D00",    # Deep Orange - 摸鱼开始
                "moyu_steady": "#FF1744",   # Red - 持续摸鱼
                "mode_switch": "#00B0FF",   # Light Blue - 模式切换
                "task_switch": "#76FF03",   # Light Green - 任务切换
                "default": "#FFFFFF"    # White - 默认
            }
            return color_map.get(category, "#FFFFFF")
        else:
            return "#FFFFFF"  # Fixed white color

    def update(self, delta_time: float = 1.0):
        """更新所有弹幕"""
        if not self.enabled:
            return

        # Update all danmakus
        for danmaku in self.danmakus:
            danmaku.update(delta_time)

        # Remove out-of-screen danmakus
        self.danmakus = [d for d in self.danmakus if not d.is_out_of_screen()]

    def render(self, painter: QPainter, screen_width: int, screen_height: int):
        """渲染所有弹幕"""
        if not self.enabled or not self.danmakus:
            return

        if self.logger:
            self.logger.debug(f"[弹幕渲染] 开始渲染 {len(self.danmakus)} 条弹幕, screen_width={screen_width}, screen_height={screen_height}")

        # Save painter state
        painter.save()

        try:
            for i, danmaku in enumerate(self.danmakus):
                if self.logger:
                    self.logger.debug(f"[弹幕渲染] #{i+1}: \"{danmaku.content}\" at ({danmaku.x:.0f}, {danmaku.y:.0f})")
                self._render_danmaku(painter, danmaku)
        finally:
            # Restore painter state
            painter.restore()

    def _render_danmaku(self, painter: QPainter, danmaku: Danmaku):
        """渲染单条弹幕"""
        # Set font
        font = QFont("Microsoft YaHei UI", danmaku.font_size, QFont.Bold)
        painter.setFont(font)

        # Calculate text width if not calculated yet
        if danmaku.width == 0:
            metrics = painter.fontMetrics()
            danmaku.width = metrics.horizontalAdvance(danmaku.content)

        # Set opacity
        color = QColor(danmaku.color)
        color.setAlphaF(danmaku.opacity)

        # Draw text with stroke (outline) for better visibility
        # 1. Draw black outline
        painter.setPen(QPen(QColor(0, 0, 0, int(255 * danmaku.opacity)), 2))
        path = QPainterPath()
        path.addText(danmaku.x, danmaku.y, font, danmaku.content)
        painter.drawPath(path)

        # 2. Draw white text on top
        painter.setPen(QPen(color))
        painter.drawText(int(danmaku.x), int(danmaku.y), danmaku.content)

    def clear(self):
        """清空所有弹幕"""
        self.danmakus.clear()

    def set_enabled(self, enabled: bool):
        """启用/禁用弹幕"""
        self.enabled = enabled
        if not enabled:
            self.clear()

    def _update_current_task_info(self, tasks: List[Dict], current_time_percentage: float):
        """更新当前任务信息缓存"""
        if not tasks:
            return

        # Use actual current time instead of percentage
        now = datetime.now()
        current_minute = now.hour * 60 + now.minute

        for task in tasks:
            task_start = task.get('start', '')
            task_end = task.get('end', '')

            start_seconds = time_utils.time_str_to_seconds(task_start)
            end_seconds = time_utils.time_str_to_seconds(task_end)

            start_minute = start_seconds // 60
            end_minute = end_seconds // 60

            # Handle cross-day tasks
            if end_minute < start_minute:
                if current_minute >= start_minute or current_minute < end_minute:
                    self.current_task_name = task.get('task', '')
                    self.current_task_start_time = start_minute
                    self.current_task_end_time = end_minute if end_minute > 0 else 1440 + end_minute
                    return
            else:
                if start_minute <= current_minute < end_minute:
                    self.current_task_name = task.get('task', '')
                    self.current_task_start_time = start_minute
                    self.current_task_end_time = end_minute
                    return

    def _select_non_repeat_content(self, category: str) -> str:
        """选择不在历史记录中的内容"""
        available_contents = self.presets.get(category, [])

        if not available_contents:
            return "时间在流逝..."

        # 过滤掉历史中的内容
        non_repeat_contents = [c for c in available_contents if c not in self.recent_history]

        # 如果可选内容太少(< 5条),清空部分历史
        if len(non_repeat_contents) < 5 and len(self.recent_history) > 10:
            # 保留最近的10条,清除更早的
            self.recent_history = self.recent_history[-10:]
            non_repeat_contents = [c for c in available_contents if c not in self.recent_history]

        # 如果还是没有可用内容,直接从所有内容中选择
        if not non_repeat_contents:
            non_repeat_contents = available_contents

        return random.choice(non_repeat_contents)

    def _add_to_history(self, content: str):
        """添加内容到历史记录"""
        self.recent_history.append(content)

        # 保持历史记录在最大限制内
        if len(self.recent_history) > self.max_history:
            self.recent_history.pop(0)

    def _apply_template(self, content: str, current_time_percentage: float) -> str:
        """应用模板替换动态变量

        支持的变量:
        - {task_name}: 当前任务名称
        - {elapsed}: 已用时间(分钟)
        - {remaining}: 剩余时间(分钟)
        - {progress}: 完成百分比
        - {time_period}: 时间段(早晨/上午/下午/晚上)
        """
        # 检查是否包含模板变量
        if '{' not in content:
            return content

        # Use actual current time instead of percentage
        now = datetime.now()
        current_minute = now.hour * 60 + now.minute

        # 替换任务名称
        if '{task_name}' in content:
            content = content.replace('{task_name}', self.current_task_name or '当前任务')

        # 计算已用时间和剩余时间
        if self.current_task_start_time and self.current_task_end_time:
            elapsed = current_minute - self.current_task_start_time
            if elapsed < 0:  # 跨天任务
                elapsed = current_minute + 1440 - self.current_task_start_time

            remaining = self.current_task_end_time - current_minute
            if remaining < 0:  # 跨天任务
                remaining = self.current_task_end_time + 1440 - current_minute

            if '{elapsed}' in content:
                content = content.replace('{elapsed}', str(max(0, elapsed)))

            if '{remaining}' in content:
                content = content.replace('{remaining}', str(max(0, remaining)))

            # 计算进度百分比
            total_duration = self.current_task_end_time - self.current_task_start_time
            if total_duration < 0:  # 跨天任务
                total_duration = self.current_task_end_time + 1440 - self.current_task_start_time

            if total_duration > 0:
                progress = int((elapsed / total_duration) * 100)
                progress = max(0, min(100, progress))  # 限制在0-100

                if '{progress}' in content:
                    content = content.replace('{progress}', str(progress))

        # 替换时间段
        if '{time_period}' in content:
            if 0 <= current_minute < 360:  # 0:00-6:00
                time_period = '深夜'
            elif 360 <= current_minute < 540:  # 6:00-9:00
                time_period = '早晨'
            elif 540 <= current_minute < 720:  # 9:00-12:00
                time_period = '上午'
            elif 720 <= current_minute < 780:  # 12:00-13:00
                time_period = '中午'
            elif 780 <= current_minute < 1080:  # 13:00-18:00
                time_period = '下午'
            elif 1080 <= current_minute < 1320:  # 18:00-22:00
                time_period = '晚上'
            else:  # 22:00-24:00
                time_period = '深夜'

            content = content.replace('{time_period}', time_period)

        return content
