"""
场景事件管理器 - SceneEventManager

负责处理场景元素的交互事件,包括鼠标悬停、点击和时间触发
"""

import logging
import webbrowser
from typing import Optional, Set, Tuple, List, Dict, Any
from PySide6.QtCore import QPointF, QRectF, QObject, Signal
from PySide6.QtWidgets import QToolTip, QMessageBox

from .models import SceneConfig, SceneItem, EventConfig, EventTriggerType, EventActionType


class SceneEventManager(QObject):
    """场景事件管理器

    职责:
    - 检测鼠标hover/click事件
    - 检测进度时间触发事件
    - 执行事件动作(tooltip、dialog、url)
    """

    # 信号定义
    tooltip_requested = Signal(str, QPointF)  # (文本, 位置)

    def __init__(self, scene: Optional[SceneConfig] = None, canvas_rect: Optional[QRectF] = None, parent=None):
        """初始化事件管理器

        Args:
            scene: 场景配置对象
            canvas_rect: 画布矩形区域
            parent: 父对象
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.scene = scene
        self.canvas_rect = canvas_rect or QRectF(0, 0, 1000, 150)

        # 已触发的时间事件集合(避免重复触发)
        self._triggered_time_events: Set[Tuple[str, str]] = set()  # (item_id, event_trigger)

        # 当前悬停的元素ID
        self._hovered_item_id: Optional[str] = None

        # 当前活动的任务索引(用于检测任务开始/结束)
        self._current_task_index: Optional[int] = None

        self.logger.debug("SceneEventManager initialized")

    def set_scene(self, scene: SceneConfig):
        """设置场景配置

        Args:
            scene: 场景配置对象
        """
        self.scene = scene
        self._triggered_time_events.clear()
        self._hovered_item_id = None
        self._current_task_index = None
        self.logger.info(f"Scene set: {scene.metadata.name if hasattr(scene, 'metadata') else scene.name}")

    def set_canvas_rect(self, canvas_rect: QRectF):
        """设置画布矩形区域

        Args:
            canvas_rect: 画布矩形区域
        """
        self.canvas_rect = canvas_rect

    def check_hover_events(self, mouse_pos: QPointF, progress: float = 0.0):
        """检查鼠标悬停事件

        Args:
            mouse_pos: 鼠标位置（屏幕坐标）
            progress: 当前进度 (0.0 - 1.0)
        """
        if not self.scene:
            return

        # 查找鼠标下的场景元素
        hovered_item = self._find_item_at_position(mouse_pos)

        if hovered_item:
            # 如果是新的悬停元素,触发hover事件
            if self._hovered_item_id != hovered_item.id:
                self._hovered_item_id = hovered_item.id
                self._process_hover_events(hovered_item, mouse_pos)
        else:
            # 鼠标不在任何元素上,清除悬停状态
            if self._hovered_item_id is not None:
                self._hovered_item_id = None
                # 可选: 隐藏tooltip
                QToolTip.hideText()

    def check_click_events(self, mouse_pos: QPointF, progress: float = 0.0):
        """检查鼠标点击事件

        Args:
            mouse_pos: 鼠标位置（屏幕坐标）
            progress: 当前进度 (0.0 - 1.0)
        """
        if not self.scene:
            return

        # 查找点击位置的场景元素
        clicked_item = self._find_item_at_position(mouse_pos)

        if clicked_item:
            self._process_click_events(clicked_item, mouse_pos)

    def check_time_events(self, progress: float, tasks: Optional[List[Dict[str, Any]]] = None):
        """检查进度时间触发事件

        Args:
            progress: 当前进度 (0.0 - 1.0)
            tasks: 任务列表(可选),用于检测任务开始/结束事件
        """
        if not self.scene:
            return

        # 如果提供了任务列表,计算当前活动任务
        current_task_idx = None
        if tasks:
            current_task_idx = self._get_current_task_index(progress, tasks)

        # 遍历所有场景元素
        for item in self.scene.scene_layer.items:
            # 检查该元素的时间触发事件
            for event in item.events:
                # 处理精确时间点触发(on_time_reach)
                if event.trigger == EventTriggerType.ON_TIME_REACH.value:
                    # 获取触发时间点
                    trigger_progress = event.action.params.get('progress', 0.0)

                    # 检查是否已达到触发点且未触发过
                    event_key = (item.id, event.trigger, trigger_progress)
                    if progress >= trigger_progress and event_key not in self._triggered_time_events:
                        # 触发事件
                        self._execute_action(event.action, item)
                        # 标记为已触发
                        self._triggered_time_events.add(event_key)

                # 处理进度范围触发(on_progress_range)
                elif event.trigger == EventTriggerType.ON_PROGRESS_RANGE.value:
                    # 获取范围参数
                    start_percent = event.trigger_params.get('start_percent', 0.0)
                    end_percent = event.trigger_params.get('end_percent', 100.0)

                    # 转换为0-1范围
                    start_progress = start_percent / 100.0
                    end_progress = end_percent / 100.0

                    # 检查进度是否在范围内
                    if start_progress <= progress <= end_progress:
                        # 使用范围作为key,确保在范围内只触发一次
                        event_key = (item.id, event.trigger, start_percent, end_percent)
                        if event_key not in self._triggered_time_events:
                            # 触发事件
                            self._execute_action(event.action, item)
                            # 标记为已触发
                            self._triggered_time_events.add(event_key)
                    else:
                        # 如果进度离开范围,重置该事件(允许再次进入时触发)
                        event_key = (item.id, event.trigger, start_percent, end_percent)
                        if event_key in self._triggered_time_events:
                            self._triggered_time_events.discard(event_key)

                # 处理任务开始触发(on_task_start)
                elif event.trigger == EventTriggerType.ON_TASK_START.value:
                    if tasks is None:
                        continue

                    # 获取要监控的任务索引
                    target_task_idx = event.trigger_params.get('task_index', -1)
                    if target_task_idx < 0 or target_task_idx >= len(tasks):
                        continue

                    # 检测是否刚进入该任务
                    if current_task_idx == target_task_idx and self._current_task_index != target_task_idx:
                        # 触发任务开始事件
                        self._execute_action(event.action, item)
                        self.logger.debug(f"Task {target_task_idx} started")

                # 处理任务结束触发(on_task_end)
                elif event.trigger == EventTriggerType.ON_TASK_END.value:
                    if tasks is None:
                        continue

                    # 获取要监控的任务索引
                    target_task_idx = event.trigger_params.get('task_index', -1)
                    if target_task_idx < 0 or target_task_idx >= len(tasks):
                        continue

                    # 检测是否刚离开该任务
                    if self._current_task_index == target_task_idx and current_task_idx != target_task_idx:
                        # 触发任务结束事件
                        self._execute_action(event.action, item)
                        self.logger.debug(f"Task {target_task_idx} ended")

        # 更新当前任务索引
        if tasks is not None:
            self._current_task_index = current_task_idx

    def reset_time_events(self):
        """重置时间事件触发记录

        在进度重置到0时调用,允许时间事件重新触发
        """
        self._triggered_time_events.clear()
        self._current_task_index = None
        self.logger.debug("Time events reset")

    def _get_current_task_index(self, progress: float, tasks: List[Dict[str, Any]]) -> Optional[int]:
        """根据当前进度计算活动任务索引

        Args:
            progress: 当前进度 (0.0 - 1.0)
            tasks: 任务列表,每个任务应包含 'duration' 字段(分钟数)

        Returns:
            当前活动任务的索引,如果没有活动任务则返回None
        """
        if not tasks:
            return None

        # 计算总时长
        total_duration = sum(task.get('duration', 0) for task in tasks)
        if total_duration <= 0:
            return None

        # 遍历任务,找出当前进度对应的任务
        cumulative_progress = 0.0
        for idx, task in enumerate(tasks):
            task_duration = task.get('duration', 0)
            if task_duration <= 0:
                continue

            # 计算该任务在总进度中的占比
            task_progress_span = task_duration / total_duration
            task_start = cumulative_progress
            task_end = cumulative_progress + task_progress_span

            # 检查当前进度是否在该任务范围内
            if task_start <= progress < task_end:
                return idx

            cumulative_progress = task_end

        # 如果进度>=1.0,返回最后一个任务
        if progress >= 1.0 and tasks:
            return len(tasks) - 1

        return None

    def _find_item_at_position(self, mouse_pos: QPointF) -> Optional[SceneItem]:
        """查找鼠标位置下的场景元素

        Args:
            mouse_pos: 鼠标位置（屏幕坐标）

        Returns:
            场景元素对象,如果没有则返回None
        """
        # 按z-index从大到小检查(高层级优先)
        items_sorted = sorted(
            self.scene.scene_layer.items,
            key=lambda item: item.z_index,
            reverse=True
        )

        for item in items_sorted:
            if self._is_point_in_item(mouse_pos, item):
                return item

        return None

    def _is_point_in_item(self, point: QPointF, item: SceneItem) -> bool:
        """检查点是否在场景元素的矩形区域内

        Args:
            point: 点坐标
            item: 场景元素

        Returns:
            True表示点在元素内
        """
        # 计算元素的实际矩形区域
        item_rect = self._get_item_rect(item)

        # 检查点是否在矩形内
        return item_rect.contains(point)

    def _get_item_rect(self, item: SceneItem) -> QRectF:
        """获取场景元素的实际矩形区域

        Args:
            item: 场景元素

        Returns:
            元素的矩形区域
        """
        # 这里需要与renderer中的计算逻辑保持一致
        # 暂时使用估算值,实际应从renderer获取或共享计算逻辑

        # X位置: 根据百分比计算
        item_x = self.canvas_rect.x() + self.canvas_rect.width() * (item.position.x_percent / 100.0)
        # Y位置: 从canvas顶部的像素偏移
        item_y = self.canvas_rect.y() + item.position.y_pixel

        # 尺寸: 需要知道原始图片尺寸 * 缩放比例
        # 这里暂时使用估算值（后续可优化为从renderer获取）
        estimated_width = 50 * item.scale  # 假设元素宽度约50px
        estimated_height = 50 * item.scale  # 假设元素高度约50px

        return QRectF(item_x, item_y, estimated_width, estimated_height)

    def _process_hover_events(self, item: SceneItem, mouse_pos: QPointF):
        """处理hover事件

        Args:
            item: 场景元素
            mouse_pos: 鼠标位置
        """
        for event in item.events:
            if event.trigger == EventTriggerType.ON_HOVER.value:
                self._execute_action(event.action, item, mouse_pos)

    def _process_click_events(self, item: SceneItem, mouse_pos: QPointF):
        """处理click事件

        Args:
            item: 场景元素
            mouse_pos: 鼠标位置
        """
        for event in item.events:
            if event.trigger == EventTriggerType.ON_CLICK.value:
                self._execute_action(event.action, item, mouse_pos)

    def _execute_action(self, action: 'EventAction', item: SceneItem, mouse_pos: Optional[QPointF] = None):
        """执行事件动作

        Args:
            action: 事件动作配置
            item: 触发事件的场景元素
            mouse_pos: 鼠标位置（可选）
        """
        try:
            if action.type == EventActionType.SHOW_TOOLTIP.value:
                self._show_tooltip(action.params, mouse_pos)

            elif action.type == EventActionType.SHOW_DIALOG.value:
                self._show_dialog(action.params)

            elif action.type == EventActionType.OPEN_URL.value:
                self._open_url(action.params)

            else:
                self.logger.warning(f"Unknown action type: {action.type}")

        except Exception as e:
            self.logger.error(f"Failed to execute action {action.type}: {e}", exc_info=True)

    def _show_tooltip(self, params: dict, mouse_pos: Optional[QPointF] = None):
        """显示工具提示

        Args:
            params: 动作参数，包含 'text' 字段
            mouse_pos: 鼠标位置
        """
        text = params.get('text', '')
        if not text:
            return

        if mouse_pos:
            # 在鼠标位置显示tooltip
            QToolTip.showText(mouse_pos.toPoint(), text)
            self.logger.debug(f"Tooltip shown: {text}")
        else:
            self.logger.warning("Cannot show tooltip: mouse_pos is None")

    def _show_dialog(self, params: dict):
        """显示对话框

        Args:
            params: 动作参数，包含 'text' 字段
        """
        text = params.get('text', '')
        if not text:
            return

        # 使用QMessageBox显示对话框
        msg_box = QMessageBox()
        msg_box.setWindowTitle("场景提示")
        msg_box.setText(text)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.exec()

        self.logger.info(f"Dialog shown: {text}")

    def _open_url(self, params: dict):
        """打开URL

        Args:
            params: 动作参数，包含 'url' 字段
        """
        url = params.get('url', '')
        if not url:
            return

        try:
            webbrowser.open(url)
            self.logger.info(f"Opened URL: {url}")
        except Exception as e:
            self.logger.error(f"Failed to open URL {url}: {e}")
