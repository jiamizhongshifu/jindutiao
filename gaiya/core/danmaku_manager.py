"""
Danmaku Manager - 弹幕管理器
管理弹幕的生成、更新和渲染
"""

import json
import os
import random
import time
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

    def get_task_category(self, tasks: List[Dict], current_time_percentage: float) -> str:
        """根据当前时间获取任务类型"""
        if not tasks:
            return "default"

        # Find current task based on time percentage
        current_minute = int(current_time_percentage * 24 * 60)

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
        """判断是否应该生成新弹幕"""
        if not self.enabled:
            if self.logger:
                self.logger.debug(f"弹幕未启用")
            return False

        if len(self.danmakus) >= self.max_count:
            if self.logger:
                self.logger.debug(f"弹幕数量已达上限: {len(self.danmakus)}/{self.max_count}")
            return False

        time_since_last = current_time - self.last_spawn_time
        if time_since_last >= self.frequency:
            if self.logger:
                self.logger.info(f"准备生成新弹幕 (距上次: {time_since_last:.1f}s, 频率: {self.frequency}s)")
            return True

        return False

    def spawn_danmaku(self, screen_width: int, window_height: int,
                     tasks: List[Dict], current_time_percentage: float):
        """生成新弹幕"""
        # Get task category
        category = self.get_task_category(tasks, current_time_percentage)

        # Fallback to default if category not found or has no content
        if category not in self.presets or not self.presets[category]:
            category = "default"

        # Random select content
        content = random.choice(self.presets[category])

        # Calculate position
        # X: start from right edge + some buffer
        x = screen_width + 50

        # Y: 在窗口内从底部向上计算（window_height - y_offset）
        # 根据已有弹幕数量错开Y轴位置,避免重叠
        # window_height包含进度条区域和弹幕区域
        base_y = window_height - self.y_offset  # 从窗口底部向上偏移
        y_variation = len(self.danmakus) * 30  # 每条弹幕错开30px
        y = base_y - y_variation

        # Calculate speed (pixels per second for delta_time approach)
        # Base speed: traverse screen in 10 seconds = screen_width / 10
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
