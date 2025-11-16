"""
GaiYa场景编辑器 - 可视化场景设计工具

功能：
- 拖拽式场景元素摆放
- 实时预览场景效果
- 场景配置导出（JSON）
- 素材库管理

创建日期：2025-11-13
版本：v1.0.0
"""

import sys
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QListWidget, QListWidgetItem, QPushButton, QLabel,
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsItem,
    QGroupBox, QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox,
    QFileDialog, QMessageBox, QComboBox, QCheckBox, QToolBar, QDialog,
    QTextEdit, QDialogButtonBox, QSlider, QTabWidget
)
from PySide6.QtCore import Qt, QPointF, QRectF, QLineF, QSize, Signal, QTimer, QEvent
from PySide6.QtGui import (
    QPixmap, QIcon, QPainter, QColor, QPen, QBrush, QAction, QKeySequence,
    QUndoStack, QUndoCommand
)


# ============================================================================
# 事件配置数据类
# ============================================================================

@dataclass
class EventAction:
    """事件动作"""
    type: str  # show_tooltip, show_dialog, open_url
    params: Dict[str, str]  # 动作参数

@dataclass
class EventConfig:
    """事件配置"""
    trigger: str  # on_hover, on_click, on_time_reach
    action: EventAction

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "trigger": self.trigger,
            "action": {
                "type": self.action.type,
                "params": self.action.params
            }
        }


# ============================================================================
# 撤销/重做命令类
# ============================================================================

class AddItemCommand(QUndoCommand):
    """添加元素命令"""

    def __init__(self, canvas, item: 'SceneItemGraphics'):
        super().__init__("添加元素")
        self.canvas = canvas
        self.item = item

    def redo(self):
        """重做：添加元素"""
        if self.item not in self.canvas.scene_items:
            self.canvas.scene.addItem(self.item)
            self.canvas.scene_items.append(self.item)
            # 发出场景变化信号，通知刷新图层列表
            self.canvas.scene_changed.emit()

    def undo(self):
        """撤销：移除元素"""
        self.canvas.scene.removeItem(self.item)
        if self.item in self.canvas.scene_items:
            self.canvas.scene_items.remove(self.item)
            # 发出场景变化信号，通知刷新图层列表
            self.canvas.scene_changed.emit()


class MoveItemCommand(QUndoCommand):
    """移动元素命令"""

    def __init__(self, item: 'SceneItemGraphics', old_pos: QPointF, new_pos: QPointF):
        super().__init__("移动元素")
        self.item = item
        self.old_pos = old_pos
        self.new_pos = new_pos

    def redo(self):
        """重做：移动到新位置"""
        self.item._programmatic_move = True
        self.item.setPos(self.new_pos)
        self.item._programmatic_move = False

    def undo(self):
        """撤销：恢复到旧位置"""
        self.item._programmatic_move = True
        self.item.setPos(self.old_pos)
        self.item._programmatic_move = False


class MoveMultipleItemsCommand(QUndoCommand):
    """多选移动命令"""

    def __init__(self, items_moves: list):
        """
        初始化多选移动命令

        Args:
            items_moves: 列表，每个元素是(item, old_pos, new_pos)的元组
        """
        super().__init__(f"移动 {len(items_moves)} 个元素")
        self.items_moves = items_moves

    def redo(self):
        """重做：移动所有元素到新位置"""
        for item, old_pos, new_pos in self.items_moves:
            item._programmatic_move = True
            item.setPos(new_pos)
            item._programmatic_move = False

    def undo(self):
        """撤销：恢复所有元素到旧位置"""
        for item, old_pos, new_pos in self.items_moves:
            item._programmatic_move = True
            item.setPos(old_pos)
            item._programmatic_move = False


class ScaleItemCommand(QUndoCommand):
    """缩放元素命令"""

    def __init__(self, item: 'SceneItemGraphics', old_scale: float, new_scale: float):
        super().__init__("缩放元素")
        self.item = item
        self.old_scale = old_scale
        self.new_scale = new_scale

    def redo(self):
        """重做：缩放到新比例"""
        self.item.setScale(self.new_scale)
        self.item.scale_factor = self.new_scale

    def undo(self):
        """撤销：恢复到旧比例"""
        self.item.setScale(self.old_scale)
        self.item.scale_factor = self.old_scale


# ============================================================================
# 事件配置对话框
# ============================================================================

class EventConfigDialog(QDialog):
    """事件配置对话框"""

    def __init__(self, parent=None, event_config: Optional[EventConfig] = None):
        super().__init__(parent)

        self.setWindowTitle("配置事件")
        self.setModal(True)
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # 触发器选择
        trigger_group = QGroupBox("触发器")
        trigger_layout = QFormLayout(trigger_group)

        self.trigger_combo = QComboBox()
        self.trigger_combo.addItems([
            "on_hover - 鼠标悬停",
            "on_click - 鼠标点击",
            "on_time_reach - 时间到达",
            "on_progress_range - 进度范围",
            "on_task_start - 任务开始",
            "on_task_end - 任务结束"
        ])
        trigger_layout.addRow("触发类型:", self.trigger_combo)

        layout.addWidget(trigger_group)

        # 动作配置
        action_group = QGroupBox("动作")
        action_layout = QFormLayout(action_group)

        self.action_type_combo = QComboBox()
        self.action_type_combo.addItems([
            "show_tooltip - 显示提示",
            "show_dialog - 显示对话框",
            "open_url - 打开链接"
        ])
        self.action_type_combo.currentIndexChanged.connect(self._on_action_type_changed)
        action_layout.addRow("动作类型:", self.action_type_combo)

        # 参数编辑（根据动作类型动态变化）
        self.params_group = QGroupBox("参数")
        self.params_layout = QFormLayout(self.params_group)

        # 提示文本（用于show_tooltip和show_dialog）
        self.text_input = QTextEdit()
        self.text_input.setMaximumHeight(100)
        self.params_layout.addRow("文本内容:", self.text_input)

        # URL（用于open_url）
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com")
        self.params_layout.addRow("URL地址:", self.url_input)
        self.url_input.setVisible(False)

        # 时间参数（用于on_time_reach）
        self.time_input = QLineEdit()
        self.time_input.setPlaceholderText("例如: 09:00 或 50%")
        self.params_layout.addRow("时间:", self.time_input)
        self.time_input.setVisible(False)

        # 进度范围参数（用于on_progress_range）
        self.range_start_input = QLineEdit()
        self.range_start_input.setPlaceholderText("例如: 0 (表示0%)")
        self.params_layout.addRow("起始百分比:", self.range_start_input)
        self.range_start_input.setVisible(False)

        self.range_end_input = QLineEdit()
        self.range_end_input.setPlaceholderText("例如: 50 (表示50%)")
        self.params_layout.addRow("结束百分比:", self.range_end_input)
        self.range_end_input.setVisible(False)

        # 任务索引参数（用于on_task_start和on_task_end）
        self.task_index_input = QLineEdit()
        self.task_index_input.setPlaceholderText("例如: 0 (表示第一个任务)")
        self.params_layout.addRow("任务索引:", self.task_index_input)
        self.task_index_input.setVisible(False)

        action_layout.addRow(self.params_group)
        layout.addWidget(action_group)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # 如果提供了已有配置，加载它
        if event_config:
            self._load_config(event_config)

        # 初始化UI状态
        self._on_action_type_changed()
        self._on_trigger_changed()

        self.trigger_combo.currentIndexChanged.connect(self._on_trigger_changed)

    def _on_action_type_changed(self):
        """动作类型改变"""
        action_type = self.action_type_combo.currentText().split(" - ")[0]

        # 根据动作类型显示/隐藏参数
        if action_type == "open_url":
            self.text_input.setVisible(False)
            self.url_input.setVisible(True)
        else:
            self.text_input.setVisible(True)
            self.url_input.setVisible(False)

    def _on_trigger_changed(self):
        """触发器类型改变"""
        trigger = self.trigger_combo.currentText().split(" - ")[0]

        # 根据触发器类型显示/隐藏参数
        self.time_input.setVisible(trigger == "on_time_reach")
        self.range_start_input.setVisible(trigger == "on_progress_range")
        self.range_end_input.setVisible(trigger == "on_progress_range")
        self.task_index_input.setVisible(trigger in ["on_task_start", "on_task_end"])

    def _load_config(self, config: EventConfig):
        """加载已有配置"""
        # 设置触发器
        for i in range(self.trigger_combo.count()):
            if self.trigger_combo.itemText(i).startswith(config.trigger):
                self.trigger_combo.setCurrentIndex(i)
                break

        # 设置动作类型
        for i in range(self.action_type_combo.count()):
            if self.action_type_combo.itemText(i).startswith(config.action.type):
                self.action_type_combo.setCurrentIndex(i)
                break

        # 设置动作参数
        if "text" in config.action.params:
            self.text_input.setPlainText(config.action.params["text"])
        if "url" in config.action.params:
            self.url_input.setText(config.action.params["url"])
        if "time" in config.action.params:
            self.time_input.setText(config.action.params["time"])

        # 设置触发器参数
        if hasattr(config, 'trigger_params') and config.trigger_params:
            if "start_percent" in config.trigger_params:
                self.range_start_input.setText(str(config.trigger_params["start_percent"]))
            if "end_percent" in config.trigger_params:
                self.range_end_input.setText(str(config.trigger_params["end_percent"]))
            if "task_index" in config.trigger_params:
                self.task_index_input.setText(str(config.trigger_params["task_index"]))

    def get_event_config(self) -> EventConfig:
        """获取配置的事件"""
        trigger = self.trigger_combo.currentText().split(" - ")[0]
        action_type = self.action_type_combo.currentText().split(" - ")[0]

        # 构建动作参数字典
        params = {}

        if action_type == "open_url":
            params["url"] = self.url_input.text()
        else:
            params["text"] = self.text_input.toPlainText()

        if trigger == "on_time_reach":
            params["time"] = self.time_input.text()

        # 构建触发器参数字典
        trigger_params = {}

        if trigger == "on_progress_range":
            try:
                trigger_params["start_percent"] = float(self.range_start_input.text() or "0")
                trigger_params["end_percent"] = float(self.range_end_input.text() or "100")
            except ValueError:
                trigger_params["start_percent"] = 0.0
                trigger_params["end_percent"] = 100.0

        elif trigger in ["on_task_start", "on_task_end"]:
            try:
                trigger_params["task_index"] = int(self.task_index_input.text() or "0")
            except ValueError:
                trigger_params["task_index"] = 0

        action = EventAction(type=action_type, params=params)
        return EventConfig(trigger=trigger, action=action, trigger_params=trigger_params)


# ============================================================================
# 场景元素图形类
# ============================================================================

class SceneItemGraphics(QGraphicsPixmapItem):
    """场景元素图形对象"""

    def __init__(self, image_path: str, item_id: str, canvas=None):
        super().__init__()

        self.item_id = item_id
        self.image_path = image_path
        self.x_percent = 0.0  # 相对X位置（百分比）
        self.y_pixel = 0  # 绝对Y位置（像素）
        self.scale_factor = 1.0  # 缩放比例
        self.canvas = canvas  # 引用画布对象（用于网格吸附）
        self.events: List[EventConfig] = []  # 事件列表

        # 拖动撤销记录
        self._drag_start_pos = None  # 记录拖动开始时的位置
        self._programmatic_move = False  # 标记是否是程序化移动（用于撤销/重做）

        # 加载图片
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            self.setPixmap(pixmap)

        # 设置为可交互
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

        # 设置初始层级（默认为51，确保在道路层上方）
        # 道路层的z-index是50
        self.setZValue(51)

    def itemChange(self, change, value):
        """元素变化时的回调"""
        if change == QGraphicsItem.ItemPositionChange and self.canvas:
            new_pos = value

            # 程序化移动（撤销/重做）时跳过网格吸附和对齐
            if self._programmatic_move:
                return value

            # 检查是否是多选移动（如果选中了多个元素，禁用网格吸附和对齐辅助线以保持相对位置）
            selected_count = len([item for item in self.canvas.scene.selectedItems() if isinstance(item, SceneItemGraphics)])
            is_multi_select = selected_count > 1

            # 多选时禁用吸附和对齐，直接返回新位置
            if is_multi_select:
                return value

            # 对齐辅助线检测（优先级高于网格吸附）
            if self.canvas.enable_alignment_guides:
                aligned_pos, alignment_lines = self.canvas.check_alignment(self, new_pos)

                # 更新画布的辅助线
                self.canvas.alignment_lines = alignment_lines

                # 触发画布重绘以显示辅助线
                self.canvas.viewport().update()

                # 如果检测到对齐，使用对齐后的位置
                if aligned_pos:
                    return aligned_pos

            # 网格吸附（如果没有对齐检测）
            if self.canvas.snap_to_grid:
                grid = self.canvas.grid_size
                snapped_x = round(new_pos.x() / grid) * grid
                snapped_y = round(new_pos.y() / grid) * grid
                return QPointF(snapped_x, snapped_y)

        elif change == QGraphicsItem.ItemPositionHasChanged:
            # 位置改变完成后，同步更新坐标属性并清除辅助线
            if self.canvas:
                # 同步更新x_percent和y_pixel（基于新位置）
                current_pos = self.pos()
                self.x_percent = current_pos.x() / self.canvas.canvas_width
                self.y_pixel = int(current_pos.y())

                # 清除辅助线
                self.canvas.alignment_lines = []
                self.canvas.viewport().update()

        return super().itemChange(change, value)

    def paint(self, painter, option, widget):
        """自定义绘制（添加选中边框）"""
        super().paint(painter, option, widget)

        # 如果被选中，绘制边框
        if self.isSelected():
            painter.setPen(QPen(QColor(0, 120, 215), 2, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.boundingRect())

    def mousePressEvent(self, event):
        """鼠标按下事件 - 记录拖动开始位置（包括多选）"""
        # 记录当前item的起始位置
        self._drag_start_pos = self.pos()

        # 如果是多选，记录所有选中items的起始位置
        if self.canvas:
            selected_items = [item for item in self.canvas.scene.selectedItems()
                              if isinstance(item, SceneItemGraphics)]
            if len(selected_items) > 1:
                # 存储所有选中items的起始位置
                self._multi_drag_start_positions = {item: item.pos() for item in selected_items}
            else:
                self._multi_drag_start_positions = None

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 创建撤销命令（支持多选）"""
        super().mouseReleaseEvent(event)

        if not self.canvas or not self.canvas.undo_stack:
            return

        # 检查是否是多选移动
        if hasattr(self, '_multi_drag_start_positions') and self._multi_drag_start_positions:
            # 多选移动：收集所有移动的items
            items_moves = []
            for item, old_pos in self._multi_drag_start_positions.items():
                new_pos = item.pos()
                if new_pos != old_pos:
                    items_moves.append((item, old_pos, new_pos))

            # 如果有items移动了，创建多选移动命令
            if items_moves:
                command = MoveMultipleItemsCommand(items_moves)
                self.canvas.undo_stack.push(command)

            self._multi_drag_start_positions = None

        # 单选移动：只处理当前item
        elif self._drag_start_pos is not None:
            new_pos = self.pos()
            if new_pos != self._drag_start_pos:
                command = MoveItemCommand(self, self._drag_start_pos, new_pos)
                self.canvas.undo_stack.push(command)

        self._drag_start_pos = None

    def to_config_dict(self) -> dict:
        """导出为配置字典"""
        return {
            "id": self.item_id,
            "image": os.path.basename(self.image_path),
            "position": {
                "x_percent": self.x_percent * 100,  # 转换为0-100范围（内部是0-1）
                "y_pixel": self.y_pixel
            },
            "scale": self.scale_factor,
            "z_index": int(self.zValue()),
            "events": [event.to_dict() for event in self.events]
        }


class SceneCanvas(QGraphicsView):
    """场景画布视图"""

    item_selected = Signal(SceneItemGraphics)  # 元素选中信号
    road_layer_selected = Signal()  # 道路层选中信号
    scene_changed = Signal()  # 场景变化信号（元素添加/删除/修改）

    def __init__(self, parent=None, undo_stack=None):
        super().__init__(parent)

        # 创建场景
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # 设置画布尺寸（默认1800x150）
        self.canvas_width = 1800
        self.canvas_height = 150
        self.scene.setSceneRect(0, 0, self.canvas_width, self.canvas_height)

        # 道路层设置
        self.road_image_path: Optional[str] = None  # 道路图片路径
        self.road_pixmap: Optional[QPixmap] = None  # 道路图片
        self.road_offset_x = 0  # 道路层X轴偏移（像素）
        self.road_offset_y = 0  # 道路层Y轴偏移（像素）
        self.road_scale = 1.0  # 道路层缩放比例（默认100%）
        self.road_item: Optional[QGraphicsPixmapItem] = None  # 道路层图形对象

        # 网格设置
        self.grid_size = 10  # 网格大小（像素）
        self.show_grid = True  # 是否显示网格
        self.snap_to_grid = True  # 是否吸附到网格

        # 绘制背景网格
        self.setBackgroundBrush(QBrush(QColor(250, 250, 250)))

        # 场景元素列表
        self.scene_items: List[SceneItemGraphics] = []

        # 对齐辅助线
        self.alignment_lines = []  # 存储辅助线
        self.enable_alignment_guides = True  # 是否启用对齐辅助线

        # 撤销栈
        self.undo_stack = undo_stack

        # 启用拖拽接受
        self.setAcceptDrops(True)

        # 视图设置 - 显示完整场景
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # 禁用交互式缩放
        self.setTransformationAnchor(QGraphicsView.AnchorViewCenter)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)

        # 启用框选模式（橡皮筋选择）
        self.setDragMode(QGraphicsView.RubberBandDrag)

        # 剪贴板数据（用于复制/粘贴）
        self.clipboard_items = []  # 存储复制的元素数据

        # 安全区域蒙版设置
        self.show_safe_area_mask = True  # 是否显示安全区域蒙版
        self.safe_area_margin_left = 100  # 左边距
        self.safe_area_margin_right = 100  # 右边距
        self.safe_area_margin_top = 10  # 上边距
        self.safe_area_margin_bottom = 20  # 下边距
        self.safe_mask_items = []  # 存储蒙版图形对象

        # 预览播放控制
        self.current_progress = 0.0  # 当前进度(0.0-1.0)
        self.is_playing = False  # 是否正在播放
        self.play_timer = None  # 播放定时器
        self.play_speed = 1.0  # 播放速度倍率

        # 连接场景选中信号
        self.scene.selectionChanged.connect(self._on_selection_changed)

    def _on_selection_changed(self):
        """场景选中项改变时触发"""
        selected_items = self.scene.selectedItems()
        if selected_items:
            for item in selected_items:
                # 检查是否选中了道路层
                if item is self.road_item:
                    self.road_layer_selected.emit()
                    break
                # 处理SceneItemGraphics类型的元素
                elif isinstance(item, SceneItemGraphics):
                    self.item_selected.emit(item)
                    break

    def set_road_image(self, image_path: str):
        """设置道路层图片"""
        self.road_image_path = image_path
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            return

        self.road_pixmap = pixmap

        # 移除旧的道路层图形对象
        if self.road_item:
            self.scene.removeItem(self.road_item)
            self.road_item = None

        # 创建平铺的道路图片
        tiled_pixmap = self._create_tiled_road_pixmap()

        # 创建道路层图形对象
        self.road_item = QGraphicsPixmapItem(tiled_pixmap)
        self.road_item.setPos(self.road_offset_x, self.road_offset_y)

        # 设置道路层的 z-index 为 50（中间值）
        # 场景元素 z-index < 50 会显示在道路下方
        # 场景元素 z-index > 50 会显示在道路上方
        self.road_item.setZValue(50)

        # 设置道路层可选中、可移动
        self.road_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.road_item.setFlag(QGraphicsItem.ItemIsMovable, True)

        # 添加到场景
        self.scene.addItem(self.road_item)

    def _create_tiled_road_pixmap(self) -> QPixmap:
        """创建平铺的道路图片"""
        if not self.road_pixmap:
            return QPixmap()

        # 应用缩放
        scaled_pixmap = self.road_pixmap
        if self.road_scale != 1.0:
            scaled_width = int(self.road_pixmap.width() * self.road_scale)
            scaled_height = int(self.road_pixmap.height() * self.road_scale)
            scaled_pixmap = self.road_pixmap.scaled(
                scaled_width, scaled_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

        road_width = scaled_pixmap.width()
        road_height = scaled_pixmap.height()

        # 创建一个足够宽的画布来平铺道路
        tiled_width = self.canvas_width
        tiled_pixmap = QPixmap(tiled_width, road_height)
        tiled_pixmap.fill(Qt.transparent)

        # 在画布上平铺绘制道路
        painter = QPainter(tiled_pixmap)
        x = 0
        while x < tiled_width:
            painter.drawPixmap(x, 0, scaled_pixmap)
            x += road_width
        painter.end()

        return tiled_pixmap

    def update_road_layer(self):
        """更新道路层（偏移或缩放改变时调用）"""
        if not self.road_item or not self.road_pixmap:
            return

        # 重新创建平铺图片
        tiled_pixmap = self._create_tiled_road_pixmap()
        self.road_item.setPixmap(tiled_pixmap)
        self.road_item.setPos(self.road_offset_x, self.road_offset_y)

    def drawBackground(self, painter: QPainter, rect: QRectF):
        """绘制背景网格"""
        super().drawBackground(painter, rect)

        # 绘制网格
        if self.show_grid:
            # 设置网格线样式
            painter.setPen(QPen(QColor(230, 230, 230), 1, Qt.DotLine))

            # 绘制垂直网格线
            left = int(rect.left()) - (int(rect.left()) % self.grid_size)
            top = int(rect.top()) - (int(rect.top()) % self.grid_size)

            for x in range(left, int(rect.right()), self.grid_size):
                painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))

            # 绘制水平网格线
            for y in range(top, int(rect.bottom()), self.grid_size):
                painter.drawLine(int(rect.left()), y, int(rect.right()), y)

        # 3. 绘制画布边界
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.drawRect(0, 0, self.canvas_width, self.canvas_height)

        # 4. 绘制对齐辅助线
        if self.alignment_lines:
            painter.setPen(QPen(QColor(255, 0, 0), 1, Qt.DashLine))  # 红色虚线
            for line in self.alignment_lines:
                painter.drawLine(line)

    def drawForeground(self, painter: QPainter, rect: QRectF):
        """绘制前景（包括安全区域蒙版）"""
        super().drawForeground(painter, rect)

        # 绘制安全区域蒙版
        if self.show_safe_area_mask:
            # 设置半透明灰色
            mask_color = QColor(100, 100, 100, 120)  # 灰色，透明度120/255
            painter.setBrush(QBrush(mask_color))
            painter.setPen(Qt.NoPen)

            # 计算安全区域
            safe_x = self.safe_area_margin_left
            safe_y = self.safe_area_margin_top
            safe_width = self.canvas_width - self.safe_area_margin_left - self.safe_area_margin_right
            safe_height = self.canvas_height - self.safe_area_margin_top - self.safe_area_margin_bottom

            # 绘制四个蒙版矩形（上、下、左、右）
            # 左侧蒙版
            if self.safe_area_margin_left > 0:
                painter.drawRect(0, 0, self.safe_area_margin_left, self.canvas_height)

            # 右侧蒙版
            if self.safe_area_margin_right > 0:
                painter.drawRect(
                    self.canvas_width - self.safe_area_margin_right,
                    0,
                    self.safe_area_margin_right,
                    self.canvas_height
                )

            # 上侧蒙版
            if self.safe_area_margin_top > 0:
                painter.drawRect(
                    self.safe_area_margin_left,
                    0,
                    safe_width,
                    self.safe_area_margin_top
                )

            # 下侧蒙版
            if self.safe_area_margin_bottom > 0:
                painter.drawRect(
                    self.safe_area_margin_left,
                    self.canvas_height - self.safe_area_margin_bottom,
                    safe_width,
                    self.safe_area_margin_bottom
                )

            # 绘制安全区域边框（绿色虚线）
            painter.setPen(QPen(QColor(0, 255, 0, 150), 2, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(safe_x, safe_y, safe_width, safe_height)

        # 绘制进度标记（底部刻度）
        # 进度应该在安全区域范围内显示
        if self.current_progress >= 0:
            # 计算安全区域范围
            safe_x = self.safe_area_margin_left
            safe_width = self.canvas_width - self.safe_area_margin_left - self.safe_area_margin_right

            # 进度标记在安全区域内的位置
            progress_x = safe_x + (self.current_progress * safe_width)

            # 绘制底部的小三角形刻度
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(255, 0, 0, 200)))  # 红色填充

            # 三角形顶点（向上的小三角）
            from PySide6.QtCore import QPointF
            triangle_height = 15  # 三角形高度
            triangle_width = 10   # 三角形底边宽度

            triangle = [
                QPointF(progress_x, self.canvas_height),  # 底部中心点
                QPointF(progress_x - triangle_width/2, self.canvas_height - triangle_height),  # 左上
                QPointF(progress_x + triangle_width/2, self.canvas_height - triangle_height),  # 右上
            ]

            painter.drawPolygon(triangle)

    def toggle_safe_area_mask(self, enabled: bool):
        """切换安全区域蒙版显示"""
        self.show_safe_area_mask = enabled
        self.viewport().update()  # 触发重绘

    def check_alignment(self, moving_item, new_pos):
        """检测元素对齐关系并返回吸附后的位置和辅助线

        Args:
            moving_item: 正在移动的元素
            new_pos: 新位置

        Returns:
            (aligned_pos, alignment_lines): 对齐后的位置和辅助线列表
        """
        SNAP_THRESHOLD = 10  # 吸附阈值（像素）

        aligned_x = None
        aligned_y = None
        alignment_lines = []

        # 获取移动元素的边界框
        moving_rect = moving_item.boundingRect()
        moving_left = new_pos.x()
        moving_right = new_pos.x() + moving_rect.width()
        moving_center_x = new_pos.x() + moving_rect.width() / 2
        moving_top = new_pos.y()
        moving_bottom = new_pos.y() + moving_rect.height()
        moving_center_y = new_pos.y() + moving_rect.height() / 2

        # 遍历所有场景元素（除了正在移动的元素）
        for item in self.scene.items():
            if not isinstance(item, SceneItemGraphics) or item == moving_item:
                continue

            # 获取目标元素的边界框
            target_rect = item.boundingRect()
            target_pos = item.pos()
            target_left = target_pos.x()
            target_right = target_pos.x() + target_rect.width()
            target_center_x = target_pos.x() + target_rect.width() / 2
            target_top = target_pos.y()
            target_bottom = target_pos.y() + target_rect.height()
            target_center_y = target_pos.y() + target_rect.height() / 2

            # 检测水平对齐（X轴）
            # 左边缘对齐
            if abs(moving_left - target_left) < SNAP_THRESHOLD:
                aligned_x = target_left
                alignment_lines.append(
                    QLineF(target_left, 0, target_left, self.canvas_height)
                )
            # 右边缘对齐
            elif abs(moving_right - target_right) < SNAP_THRESHOLD:
                aligned_x = target_right - moving_rect.width()
                alignment_lines.append(
                    QLineF(target_right, 0, target_right, self.canvas_height)
                )
            # 中心对齐
            elif abs(moving_center_x - target_center_x) < SNAP_THRESHOLD:
                aligned_x = target_center_x - moving_rect.width() / 2
                alignment_lines.append(
                    QLineF(target_center_x, 0, target_center_x, self.canvas_height)
                )
            # 左边缘对齐目标右边缘
            elif abs(moving_left - target_right) < SNAP_THRESHOLD:
                aligned_x = target_right
                alignment_lines.append(
                    QLineF(target_right, 0, target_right, self.canvas_height)
                )
            # 右边缘对齐目标左边缘
            elif abs(moving_right - target_left) < SNAP_THRESHOLD:
                aligned_x = target_left - moving_rect.width()
                alignment_lines.append(
                    QLineF(target_left, 0, target_left, self.canvas_height)
                )

            # 检测垂直对齐（Y轴）
            # 上边缘对齐
            if abs(moving_top - target_top) < SNAP_THRESHOLD:
                aligned_y = target_top
                alignment_lines.append(
                    QLineF(0, target_top, self.canvas_width, target_top)
                )
            # 下边缘对齐
            elif abs(moving_bottom - target_bottom) < SNAP_THRESHOLD:
                aligned_y = target_bottom - moving_rect.height()
                alignment_lines.append(
                    QLineF(0, target_bottom, self.canvas_width, target_bottom)
                )
            # 中心对齐
            elif abs(moving_center_y - target_center_y) < SNAP_THRESHOLD:
                aligned_y = target_center_y - moving_rect.height() / 2
                alignment_lines.append(
                    QLineF(0, target_center_y, self.canvas_width, target_center_y)
                )
            # 上边缘对齐目标下边缘
            elif abs(moving_top - target_bottom) < SNAP_THRESHOLD:
                aligned_y = target_bottom
                alignment_lines.append(
                    QLineF(0, target_bottom, self.canvas_width, target_bottom)
                )
            # 下边缘对齐目标上边缘
            elif abs(moving_bottom - target_top) < SNAP_THRESHOLD:
                aligned_y = target_top - moving_rect.height()
                alignment_lines.append(
                    QLineF(0, target_top, self.canvas_width, target_top)
                )

        # 构造对齐后的位置
        if aligned_x is not None or aligned_y is not None:
            final_x = aligned_x if aligned_x is not None else new_pos.x()
            final_y = aligned_y if aligned_y is not None else new_pos.y()
            return QPointF(final_x, final_y), alignment_lines

        return None, []

    def add_scene_item(self, image_path: str, x: float, y: float, use_undo=True) -> SceneItemGraphics:
        """添加场景元素到画布"""
        # 生成唯一ID
        item_id = f"item_{len(self.scene_items) + 1}"

        # 创建图形对象，传递canvas引用
        item = SceneItemGraphics(image_path, item_id, canvas=self)

        # 如果启用了网格吸附，调整位置
        if self.snap_to_grid:
            x = round(x / self.grid_size) * self.grid_size
            y = round(y / self.grid_size) * self.grid_size

        item.setPos(x, y)

        # 设置层级（后添加的元素层级更高）
        # 道路层的z-index是50（固定）
        # 场景元素默认在道路上方，z-index从51开始递增
        # 用户可以手动调整到0-100的任意值，< 50会显示在道路下方
        item.setZValue(51 + len(self.scene_items))

        # 使用撤销命令添加元素
        if use_undo and self.undo_stack:
            command = AddItemCommand(self, item)
            self.undo_stack.push(command)
        else:
            # 直接添加（不记录到撤销栈）
            self.scene.addItem(item)
            self.scene_items.append(item)

        return item

    def copy_selected_items(self):
        """复制选中的元素到剪贴板"""
        selected_items = [item for item in self.scene.selectedItems() if isinstance(item, SceneItemGraphics)]

        if not selected_items:
            return

        # 清空剪贴板
        self.clipboard_items = []

        # 复制每个元素的数据
        for item in selected_items:
            item_data = {
                'image_path': item.image_path,
                'x_percent': item.x_percent,
                'y_pixel': item.y_pixel,
                'scale': item.scale_factor,
                'z_index': item.zValue(),
                'pos_x': item.pos().x(),
                'pos_y': item.pos().y(),
                'events': [event.to_dict() for event in item.events]
            }
            self.clipboard_items.append(item_data)


    def paste_items(self):
        """粘贴剪贴板中的元素"""
        if not self.clipboard_items:
            return

        # 清除当前选中
        self.scene.clearSelection()

        # 粘贴偏移量（避免完全重叠）
        offset_x = 20
        offset_y = 20

        # 粘贴每个元素
        for item_data in self.clipboard_items:
            # 计算新位置
            new_x = item_data['pos_x'] + offset_x
            new_y = item_data['pos_y'] + offset_y

            # 创建新元素
            new_item = self.add_scene_item(
                item_data['image_path'],
                new_x,
                new_y,
                use_undo=True
            )

            # 设置其他属性
            new_item.scale_factor = item_data['scale']
            new_item.setScale(item_data['scale'])
            new_item.setZValue(item_data['z_index'])

            # 恢复事件配置
            new_item.events = [
                EventConfig.from_dict(event_dict)
                for event_dict in item_data['events']
            ]

            # 选中新元素
            new_item.setSelected(True)


    def delete_selected_items(self):
        """删除选中的元素"""
        selected_items = [item for item in self.scene.selectedItems() if isinstance(item, SceneItemGraphics)]

        if not selected_items:
            return

        # 删除每个选中的元素
        for item in selected_items:
            # 从场景中移除
            self.scene.removeItem(item)
            # 从列表中移除
            if item in self.scene_items:
                self.scene_items.remove(item)

        # 发出场景变化信号,触发图层列表刷新
        self.scene_changed.emit()


    def dragEnterEvent(self, event):
        """接受拖拽"""
        # 接受从素材库的拖拽或文件管理器的拖拽
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        """拖拽移动"""
        event.acceptProposedAction()

    def dropEvent(self, event):
        """处理拖拽放下"""
        file_path = None
        is_road_layer = False  # 是否来自道路层列表

        # 优先检查是否从QListWidget拖拽
        source_widget = event.source()

        if isinstance(source_widget, QListWidget):
            # 从素材库拖拽
            current_item = source_widget.currentItem()
            if current_item:
                file_path = current_item.data(Qt.UserRole)
                # 检查是否来自道路层列表
                parent = source_widget.parent()
                if parent and isinstance(parent, QGroupBox):
                    is_road_layer = parent.title() == "道路层"

        # 如果不是从QListWidget，检查是否从文件管理器拖拽
        elif event.mimeData().hasUrls():
            file_path = event.mimeData().urls()[0].toLocalFile()

        # 如果获取到了有效的文件路径
        if file_path and file_path.lower().endswith('.png'):
            if is_road_layer:
                # 设置为道路背景
                self.set_road_image(file_path)
            else:
                # 在放下位置添加场景元素
                pos = self.mapToScene(event.position().toPoint())
                self.add_scene_item(file_path, pos.x(), pos.y())
            event.acceptProposedAction()
        else:
            event.ignore()

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        super().mousePressEvent(event)

        # 获取点击位置的元素
        item = self.itemAt(event.position().toPoint())
        if isinstance(item, SceneItemGraphics):
            self.item_selected.emit(item)
        elif item == self.road_item:
            # 点击道路层时发出信号
            self.road_layer_selected.emit()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件（拖动结束）"""
        super().mouseReleaseEvent(event)

        # 如果拖动的是道路层，同步更新offset值并刷新属性面板
        if self.road_item and self.road_item.isSelected():
            actual_pos = self.road_item.pos()
            self.road_offset_x = int(actual_pos.x())
            self.road_offset_y = int(actual_pos.y())

            # 发出信号，通知属性面板刷新显示
            self.road_layer_selected.emit()

    def resizeEvent(self, event):
        """窗口大小改变时，适配视图以显示完整场景"""
        super().resizeEvent(event)
        self.fit_scene_in_view()

    def showEvent(self, event):
        """首次显示时，适配视图"""
        super().showEvent(event)
        self.fit_scene_in_view()

    def fit_scene_in_view(self):
        """适配场景到视图中，确保完整显示"""
        if self.scene:
            # 获取场景矩形
            scene_rect = self.scene.sceneRect()
            # 适配整个场景到视图，保持宽高比
            self.fitInView(scene_rect, Qt.KeepAspectRatio)

    # ==================== 播放控制方法 ====================

    def set_progress(self, progress: float):
        """设置当前进度(0.0-1.0)"""
        self.current_progress = max(0.0, min(1.0, progress))
        self.viewport().update()  # 触发重绘，显示进度条位置

    def play_preview(self):
        """开始播放预览"""
        self.is_playing = True

        # 创建定时器
        if not self.play_timer:
            self.play_timer = QTimer(self)
            self.play_timer.timeout.connect(self._advance_progress)

        # 根据速度设置间隔
        interval = int(100 / self.play_speed)  # 基础100ms
        self.play_timer.setInterval(interval)
        self.play_timer.start()

    def pause_preview(self):
        """暂停播放预览"""
        self.is_playing = False
        if self.play_timer:
            self.play_timer.stop()

    def reset_preview(self):
        """重置预览到起点"""
        self.pause_preview()
        self.set_progress(0.0)

    def set_play_speed(self, speed: float):
        """设置播放速度"""
        self.play_speed = speed
        # 如果正在播放，更新定时器间隔
        if self.is_playing and self.play_timer:
            interval = int(100 / self.play_speed)
            self.play_timer.setInterval(interval)

    def _advance_progress(self):
        """前进进度（播放时调用）"""
        # 每次前进1%
        new_progress = self.current_progress + 0.01

        if new_progress > 1.0:
            # 循环播放
            new_progress = 0.0

        self.set_progress(new_progress)


class AssetLibraryPanel(QWidget):
    """素材库面板"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # 布局
        layout = QVBoxLayout(self)

        # 标题
        title = QLabel("素材库")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)

        # 道路层分组
        road_group = QGroupBox("道路层")
        road_layout = QVBoxLayout(road_group)
        self.road_list = QListWidget()
        self.road_list.setIconSize(QSize(48, 48))  # 缩小缩略图尺寸，节省空间
        road_layout.addWidget(self.road_list)
        # 道路层上传按钮
        road_upload_btn = QPushButton("+ 上传道路图片")
        road_upload_btn.clicked.connect(self.import_road_asset)
        road_layout.addWidget(road_upload_btn)
        # 道路层加载按钮
        road_load_btn = QPushButton("设为道路")
        road_load_btn.clicked.connect(self.load_selected_road)
        road_layout.addWidget(road_load_btn)
        layout.addWidget(road_group)

        # 场景层分组
        scene_group = QGroupBox("场景层")
        scene_layout = QVBoxLayout(scene_group)
        self.scene_list = QListWidget()
        self.scene_list.setIconSize(QSize(48, 48))  # 缩小缩略图尺寸，节省空间
        scene_layout.addWidget(self.scene_list)
        # 场景层上传按钮
        scene_upload_btn = QPushButton("+ 上传场景图片")
        scene_upload_btn.clicked.connect(self.import_scene_asset)
        scene_layout.addWidget(scene_upload_btn)
        # 场景层加载按钮
        scene_load_btn = QPushButton("加载到画布")
        scene_load_btn.clicked.connect(self.load_selected_scene)
        scene_layout.addWidget(scene_load_btn)
        layout.addWidget(scene_group)

        # 启用拖拽
        self.road_list.setDragEnabled(True)
        self.scene_list.setDragEnabled(True)

        # 连接点击事件 - 点击道路层图片时显示道路层调整面板
        self.road_list.itemClicked.connect(self.on_road_item_clicked)

        # 设置拖拽模式
        self.road_list.setDragDropMode(QListWidget.DragOnly)
        self.scene_list.setDragDropMode(QListWidget.DragOnly)

        # 加载默认素材
        self.load_default_assets()

    def load_default_assets(self):
        """加载默认素材库（scenes/default/assets/目录）"""
        import os
        from pathlib import Path

        # 默认素材路径
        default_assets_dir = Path("scenes/default/assets")

        if not default_assets_dir.exists():
            print(f"默认素材目录不存在: {default_assets_dir}")
            return

        # 加载所有PNG图片
        for asset_file in default_assets_dir.glob("*.png"):
            file_path = str(asset_file)

            # 根据文件名判断是道路层还是场景层
            # 道路层通常包含 "road" 关键词
            if "road" in asset_file.name.lower():
                self.add_road_asset(file_path)
            else:
                self.add_scene_asset(file_path)

    def import_road_asset(self):
        """导入道路层素材"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择道路图片",
            "",
            "PNG图片 (*.png)"
        )

        for file_path in file_paths:
            self.add_road_asset(file_path)

    def import_scene_asset(self):
        """导入场景层素材"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择场景图片",
            "",
            "PNG图片 (*.png)"
        )

        for file_path in file_paths:
            self.add_scene_asset(file_path)

    def add_road_asset(self, file_path: str):
        """添加道路层素材"""
        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            return

        # 创建列表项
        item = QListWidgetItem(QIcon(pixmap), os.path.basename(file_path))
        item.setData(Qt.UserRole, file_path)
        self.road_list.addItem(item)

    def add_scene_asset(self, file_path: str):
        """添加场景层素材"""
        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            return

        # 创建列表项
        item = QListWidgetItem(QIcon(pixmap), os.path.basename(file_path))
        item.setData(Qt.UserRole, file_path)
        self.scene_list.addItem(item)

    def load_selected_road(self):
        """将选中的道路图片设为道路层背景"""
        current_item = self.road_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请先选择一个道路图片")
            return

        file_path = current_item.data(Qt.UserRole)
        # 调用父窗口的方法设置道路
        parent_window = self.window()
        if hasattr(parent_window, 'canvas'):
            parent_window.canvas.set_road_image(file_path)

    def load_selected_scene(self):
        """将选中的场景图片加载到画布中央"""
        current_item = self.scene_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请先选择一个场景图片")
            return

        file_path = current_item.data(Qt.UserRole)
        # 调用父窗口的方法添加场景元素到画布中央
        parent_window = self.window()
        if hasattr(parent_window, 'canvas'):
            # 在画布中央添加元素
            canvas = parent_window.canvas
            center_x = canvas.canvas_width / 2
            center_y = canvas.canvas_height / 2
            canvas.add_scene_item(file_path, center_x, center_y)

    def on_road_item_clicked(self, item):
        """道路层图片被点击时，显示道路层调整面板"""
        parent_window = self.window()
        if hasattr(parent_window, 'property_panel'):
            parent_window.property_panel.show_road_panel()


class PropertyPanel(QWidget):
    """属性面板"""

    def __init__(self, parent=None, canvas=None):
        super().__init__(parent)

        self.canvas = canvas  # 保存canvas引用

        layout = QVBoxLayout(self)

        # 标题
        title = QLabel("属性面板")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)

        # 基本信息分组
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout(basic_group)

        self.scene_name_input = QLineEdit()
        self.scene_name_input.setPlaceholderText("例如: 像素森林")
        basic_layout.addRow("场景名称:", self.scene_name_input)

        self.canvas_height_input = QSpinBox()
        self.canvas_height_input.setRange(100, 300)
        self.canvas_height_input.setValue(150)
        self.canvas_height_input.setSuffix(" px")
        basic_layout.addRow("画布高度:", self.canvas_height_input)

        layout.addWidget(basic_group)

        # 道路层分组
        self.road_group = QGroupBox("道路层")
        self.road_group.setVisible(False)  # 默认隐藏
        road_layout = QVBoxLayout(self.road_group)

        # 道路图片预览
        self.road_preview = QLabel("未选择道路图片")
        self.road_preview.setAlignment(Qt.AlignCenter)
        self.road_preview.setStyleSheet("border: 1px solid #ccc; padding: 10px; background: white;")
        self.road_preview.setMinimumHeight(80)
        road_layout.addWidget(self.road_preview)

        # 道路文件名显示
        self.road_filename_label = QLabel("文件: 无")
        self.road_filename_label.setStyleSheet("font-size: 11px; color: #666;")
        road_layout.addWidget(self.road_filename_label)

        # 道路位置调整
        road_position_layout = QFormLayout()

        self.road_x_input = QSpinBox()
        self.road_x_input.setRange(-1000, 1000)
        self.road_x_input.setValue(0)
        self.road_x_input.setSuffix(" px")
        self.road_x_input.valueChanged.connect(self._on_road_x_changed)
        self.road_x_input.setEnabled(False)
        road_position_layout.addRow("X偏移:", self.road_x_input)

        self.road_y_input = QSpinBox()
        self.road_y_input.setRange(-300, 300)
        self.road_y_input.setValue(0)
        self.road_y_input.setSuffix(" px")
        self.road_y_input.valueChanged.connect(self._on_road_y_changed)
        self.road_y_input.setEnabled(False)
        road_position_layout.addRow("Y偏移:", self.road_y_input)

        # 道路缩放控制（滑块 + 数值输入框）
        road_scale_container = QWidget()
        road_scale_layout = QHBoxLayout(road_scale_container)
        road_scale_layout.setContentsMargins(0, 0, 0, 0)

        self.road_scale_slider = QSlider(Qt.Horizontal)
        self.road_scale_slider.setRange(10, 300)  # 10% 到 300%
        self.road_scale_slider.setValue(100)  # 默认100%
        self.road_scale_slider.setEnabled(False)
        self.road_scale_slider.valueChanged.connect(self._on_road_scale_slider_changed)

        # 新增：道路缩放数值输入框（支持精确控制）
        self.road_scale_spinbox = QDoubleSpinBox()
        self.road_scale_spinbox.setRange(0.1, 3.0)  # 0.1x 到 3.0x
        self.road_scale_spinbox.setValue(1.0)
        self.road_scale_spinbox.setSuffix("x")
        self.road_scale_spinbox.setSingleStep(0.1)
        self.road_scale_spinbox.setDecimals(1)
        self.road_scale_spinbox.setMinimumWidth(70)
        self.road_scale_spinbox.setEnabled(False)
        self.road_scale_spinbox.valueChanged.connect(self._on_road_scale_spinbox_changed)

        road_scale_layout.addWidget(self.road_scale_slider)
        road_scale_layout.addWidget(self.road_scale_spinbox)

        road_position_layout.addRow("缩放:", road_scale_container)

        # 道路层级控制
        self.road_z_input = QSpinBox()
        self.road_z_input.setRange(0, 100)
        self.road_z_input.setValue(50)
        self.road_z_input.setEnabled(False)
        self.road_z_input.valueChanged.connect(self._on_road_z_changed)
        road_position_layout.addRow("层级:", self.road_z_input)

        road_layout.addLayout(road_position_layout)

        # 道路操作按钮
        road_button_layout = QHBoxLayout()
        self.select_road_button = QPushButton("选择道路图片")
        self.select_road_button.clicked.connect(self._on_select_road)
        road_button_layout.addWidget(self.select_road_button)

        self.clear_road_button = QPushButton("清除道路")
        self.clear_road_button.clicked.connect(self._on_clear_road)
        self.clear_road_button.setEnabled(False)
        road_button_layout.addWidget(self.clear_road_button)

        road_layout.addLayout(road_button_layout)
        layout.addWidget(self.road_group)

        # 选中元素分组
        self.element_group = QGroupBox("选中元素")
        self.element_group.setVisible(False)  # 默认隐藏
        element_layout = QFormLayout(self.element_group)

        self.element_id_label = QLabel("未选中")
        element_layout.addRow("ID:", self.element_id_label)

        self.element_x_input = QSpinBox()
        self.element_x_input.setRange(-1000, 2000)  # 像素范围，支持超出画布
        self.element_x_input.setSuffix(" px")
        self.element_x_input.valueChanged.connect(self._on_x_changed)
        element_layout.addRow("X位置:", self.element_x_input)

        self.element_y_input = QSpinBox()
        self.element_y_input.setRange(-1000, 1000)  # 支持负值
        self.element_y_input.setSuffix(" px")
        self.element_y_input.valueChanged.connect(self._on_y_changed)
        element_layout.addRow("Y位置:", self.element_y_input)

        # 场景元素缩放控制（滑块 + 数值输入框）
        element_scale_container = QWidget()
        element_scale_layout = QHBoxLayout(element_scale_container)
        element_scale_layout.setContentsMargins(0, 0, 0, 0)

        self.element_scale_slider = QSlider(Qt.Horizontal)
        self.element_scale_slider.setRange(1, 500)  # 1 到 500（内部值，代表 0.01x 到 5.0x）
        self.element_scale_slider.setValue(100)  # 默认100（1.0x）
        self.element_scale_slider.valueChanged.connect(self._on_scale_slider_changed)

        # 新增：缩放数值输入框（支持精确控制，使用倍数显示）
        self.element_scale_spinbox = QDoubleSpinBox()
        self.element_scale_spinbox.setRange(0.01, 5.0)  # 0.01x 到 5.0x
        self.element_scale_spinbox.setValue(1.0)
        self.element_scale_spinbox.setSuffix("x")
        self.element_scale_spinbox.setSingleStep(0.1)
        self.element_scale_spinbox.setDecimals(2)
        self.element_scale_spinbox.setMinimumWidth(70)
        self.element_scale_spinbox.valueChanged.connect(self._on_scale_spinbox_changed)

        element_scale_layout.addWidget(self.element_scale_slider)
        element_scale_layout.addWidget(self.element_scale_spinbox)

        element_layout.addRow("缩放:", element_scale_container)

        self.element_z_input = QSpinBox()
        self.element_z_input.setRange(0, 100)
        self.element_z_input.valueChanged.connect(self._on_z_changed)
        element_layout.addRow("层级:", self.element_z_input)

        # 事件配置部分
        events_label = QLabel("事件配置")
        events_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        element_layout.addRow(events_label)

        # 事件列表
        self.events_list = QListWidget()
        self.events_list.setMaximumHeight(120)
        element_layout.addRow(self.events_list)

        # 事件操作按钮
        events_button_layout = QHBoxLayout()

        self.add_event_button = QPushButton("添加事件")
        self.add_event_button.clicked.connect(self._on_add_event)
        events_button_layout.addWidget(self.add_event_button)

        self.edit_event_button = QPushButton("编辑")
        self.edit_event_button.clicked.connect(self._on_edit_event)
        self.edit_event_button.setEnabled(False)
        events_button_layout.addWidget(self.edit_event_button)

        self.delete_event_button = QPushButton("删除")
        self.delete_event_button.clicked.connect(self._on_delete_event)
        self.delete_event_button.setEnabled(False)
        events_button_layout.addWidget(self.delete_event_button)

        element_layout.addRow(events_button_layout)

        # 事件列表选中变化时启用/禁用编辑和删除按钮
        self.events_list.itemSelectionChanged.connect(self._on_event_selection_changed)

        layout.addWidget(self.element_group)

        # 添加弹性空间
        layout.addStretch()

        # 当前选中的元素
        self.current_item: Optional[SceneItemGraphics] = None
        self._updating = False  # 防止循环更新的标志

    def set_selected_item(self, item: SceneItemGraphics):
        """设置当前选中的元素"""
        self.current_item = item

        # 显示场景元素面板，隐藏道路层面板
        self.element_group.setVisible(True)
        self.road_group.setVisible(False)

        # 阻止信号触发，避免循环更新
        self._updating = True

        # 更新UI显示
        import os
        filename = os.path.basename(item.image_path)
        self.element_id_label.setText(filename)
        # X位置：将百分比转为像素值显示
        x_pixel = int(item.x_percent * self.canvas.canvas_width)
        self.element_x_input.setValue(x_pixel)
        self.element_y_input.setValue(item.y_pixel)

        # 更新缩放滑块和数值输入框
        scale_value = int(item.scale_factor * 100)  # 滑块内部值（100 = 1.0x）
        self.element_scale_slider.setValue(scale_value)
        self.element_scale_spinbox.setValue(item.scale_factor)  # 直接设置倍数（如 1.5）

        self.element_z_input.setValue(int(item.zValue()))

        # 加载事件列表
        self._load_events_list()

        self._updating = False

    def show_road_panel(self):
        """显示道路层调整面板"""
        # 显示道路层面板，隐藏场景元素面板
        self.road_group.setVisible(True)
        self.element_group.setVisible(False)

        # 阻止信号触发
        self._updating = True

        # 更新道路层属性显示
        if self.canvas.road_image_path:
            self.road_x_input.setValue(self.canvas.road_offset_x)
            self.road_y_input.setValue(self.canvas.road_offset_y)

            # 更新缩放滑块和数值输入框
            scale_value = int(self.canvas.road_scale * 100)
            self.road_scale_slider.setValue(scale_value)
            self.road_scale_spinbox.setValue(self.canvas.road_scale)

            # 更新层级（从道路层item读取）
            if self.canvas.road_item:
                self.road_z_input.setValue(int(self.canvas.road_item.zValue()))

            self.road_x_input.setEnabled(True)
            self.road_y_input.setEnabled(True)
            self.road_scale_slider.setEnabled(True)
            self.road_scale_spinbox.setEnabled(True)
            self.road_z_input.setEnabled(True)
            self.clear_road_button.setEnabled(True)
        else:
            self.road_x_input.setEnabled(False)
            self.road_y_input.setEnabled(False)
            self.road_scale_slider.setEnabled(False)
            self.road_scale_spinbox.setEnabled(False)
            self.road_z_input.setEnabled(False)
            self.clear_road_button.setEnabled(False)

        self._updating = False

    def _on_x_changed(self, value):
        """X位置改变（value 是像素值）"""
        if self._updating or not self.current_item:
            return

        # 将像素值转为百分比存储
        self.current_item.x_percent = value / self.canvas.canvas_width

        # 更新元素的实际位置（保持Y不变）
        current_pos = self.current_item.pos()
        self.current_item.setPos(value, current_pos.y())

    def _on_y_changed(self, value):
        """Y位置改变"""
        if self._updating or not self.current_item:
            return

        # 更新像素值
        self.current_item.y_pixel = value

        # 更新元素的实际位置（保持X不变）
        current_pos = self.current_item.pos()
        self.current_item.setPos(current_pos.x(), value)

    def _on_scale_slider_changed(self, value):
        """缩放滑块改变"""
        if self._updating or not self.current_item:
            return

        # 计算倍数（滑块值/100）
        scale = value / 100.0

        # 同步更新数值输入框（阻止循环触发）
        self._updating = True
        self.element_scale_spinbox.setValue(scale)
        self._updating = False

        # 应用缩放
        self.current_item.scale_factor = scale
        self.current_item.setScale(scale)

    def _on_scale_spinbox_changed(self, value):
        """缩放数值框改变（value 已经是倍数，如 1.5）"""
        if self._updating or not self.current_item:
            return

        # 同步更新滑块（阻止循环触发）
        self._updating = True
        slider_value = int(value * 100)  # 倍数转为滑块内部值
        self.element_scale_slider.setValue(slider_value)
        self._updating = False

        # 应用缩放（value 已经是倍数）
        self.current_item.scale_factor = value
        self.current_item.setScale(value)

    def _on_z_changed(self, value):
        """层级改变"""
        if self._updating or not self.current_item:
            return

        self.current_item.setZValue(value)
        # 强制刷新视图以显示层级变化
        self.current_item.update()
        if self.canvas:
            self.canvas.viewport().update()

    # ========== 道路层管理方法 ==========

    def _on_select_road(self):
        """选择道路图片"""
        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择道路图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg)"
        )

        if file_path and self.canvas:
            # 设置道路图片到画布
            self.canvas.set_road_image(file_path)

            # 更新预览
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                # 缩放预览图片
                scaled_pixmap = pixmap.scaledToHeight(60, Qt.SmoothTransformation)
                self.road_preview.setPixmap(scaled_pixmap)

                # 更新文件名显示
                import os
                filename = os.path.basename(file_path)
                self.road_filename_label.setText(f"文件: {filename}")

                # 启用清除按钮和位置调整控件
                self.clear_road_button.setEnabled(True)
                self.road_x_input.setEnabled(True)
                self.road_y_input.setEnabled(True)
                self.road_scale_slider.setEnabled(True)
                self.road_scale_spinbox.setEnabled(True)

    def _on_clear_road(self):
        """清除道路"""
        if self.canvas:
            # 从场景中移除道路图形对象
            if self.canvas.road_item:
                self.canvas.scene.removeItem(self.canvas.road_item)
                self.canvas.road_item = None

            self.canvas.road_image_path = None
            self.canvas.road_pixmap = None
            self.canvas.road_offset_x = 0
            self.canvas.road_offset_y = 0
            self.canvas.road_scale = 1.0
            self.canvas.viewport().update()

            # 重置预览
            self.road_preview.clear()
            self.road_preview.setText("未选择道路图片")
            self.road_filename_label.setText("文件: 无")

            # 禁用控件并重置数值
            self.clear_road_button.setEnabled(False)
            self.road_x_input.setValue(0)
            self.road_x_input.setEnabled(False)
            self.road_y_input.setValue(0)
            self.road_y_input.setEnabled(False)
            self.road_scale_slider.setValue(100)
            self.road_scale_slider.setEnabled(False)
            self.road_scale_spinbox.setValue(1.0)
            self.road_scale_spinbox.setEnabled(False)

    def _on_road_x_changed(self, value):
        """X偏移改变"""
        if self._updating:
            return
        if self.canvas:
            self.canvas.road_offset_x = value
            self.canvas.update_road_layer()

    def _on_road_y_changed(self, value):
        """Y偏移改变"""
        if self._updating:
            return
        if self.canvas:
            self.canvas.road_offset_y = value
            self.canvas.update_road_layer()

    def _on_road_scale_slider_changed(self, value):
        """道路缩放滑块改变"""
        if self._updating:
            return

        # 计算实际缩放值（滑块值/100）
        scale = value / 100.0

        # 同步更新数值输入框（阻止循环触发）
        self._updating = True
        self.road_scale_spinbox.setValue(scale)
        self._updating = False

        # 应用缩放
        if self.canvas:
            self.canvas.road_scale = scale
            self.canvas.update_road_layer()

    def _on_road_scale_spinbox_changed(self, value):
        """道路缩放数值框改变"""
        if self._updating:
            return

        # 同步更新滑块（阻止循环触发）
        self._updating = True
        slider_value = int(value * 100)
        self.road_scale_slider.setValue(slider_value)
        self._updating = False

        # 应用缩放
        if self.canvas:
            self.canvas.road_scale = value
            self.canvas.update_road_layer()

    def _on_road_z_changed(self, value):
        """道路层级改变"""
        if self._updating:
            return

        # 更新道路层的z-index
        if self.canvas and self.canvas.road_item:
            self.canvas.road_item.setZValue(value)

    # ========== 事件管理方法 ==========

    def _load_events_list(self):
        """加载事件列表"""
        self.events_list.clear()

        if not self.current_item:
            return

        for event in self.current_item.events:
            # 格式化显示事件
            trigger_text = {
                "on_hover": "悬停",
                "on_click": "点击",
                "on_time_reach": "时间到达",
                "on_progress_range": "进度范围",
                "on_task_start": "任务开始",
                "on_task_end": "任务结束"
            }.get(event.trigger, event.trigger)

            action_text = {
                "show_tooltip": "显示提示",
                "show_dialog": "显示对话框",
                "open_url": "打开链接"
            }.get(event.action.type, event.action.type)

            item_text = f"{trigger_text} → {action_text}"
            self.events_list.addItem(item_text)

    def _on_event_selection_changed(self):
        """事件列表选中变化"""
        has_selection = bool(self.events_list.selectedItems())
        self.edit_event_button.setEnabled(has_selection)
        self.delete_event_button.setEnabled(has_selection)

    def _on_add_event(self):
        """添加事件"""
        if not self.current_item:
            return

        # 打开事件配置对话框
        dialog = EventConfigDialog(self)

        if dialog.exec() == QDialog.Accepted:
            # 获取配置的事件
            event_config = dialog.get_event_config()

            # 添加到当前元素
            self.current_item.events.append(event_config)

            # 刷新事件列表
            self._load_events_list()

    def _on_edit_event(self):
        """编辑事件"""
        if not self.current_item:
            return

        # 获取选中的事件索引
        selected_items = self.events_list.selectedItems()
        if not selected_items:
            return

        selected_index = self.events_list.row(selected_items[0])

        if 0 <= selected_index < len(self.current_item.events):
            # 获取要编辑的事件
            event_config = self.current_item.events[selected_index]

            # 打开事件配置对话框（传入已有配置）
            dialog = EventConfigDialog(self, event_config)

            if dialog.exec() == QDialog.Accepted:
                # 更新事件配置
                new_config = dialog.get_event_config()
                self.current_item.events[selected_index] = new_config

                # 刷新事件列表
                self._load_events_list()

                # 保持选中状态
                self.events_list.setCurrentRow(selected_index)

    def _on_delete_event(self):
        """删除事件"""
        if not self.current_item:
            return

        # 获取选中的事件索引
        selected_items = self.events_list.selectedItems()
        if not selected_items:
            return

        selected_index = self.events_list.row(selected_items[0])

        if 0 <= selected_index < len(self.current_item.events):
            # 删除事件
            del self.current_item.events[selected_index]

            # 刷新事件列表
            self._load_events_list()


# ============================================================================
# 图层管理面板
# ============================================================================

class LayerPanel(QWidget):
    """图层管理面板 - 显示/隐藏/锁定图层"""

    def __init__(self, canvas=None, parent=None):
        super().__init__(parent)
        self.canvas = canvas  # 引用主画布
        self.layer_items = {}  # 存储图层项 {layer_id: widget}

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # 标题
        title_layout = QHBoxLayout()
        title_label = QLabel("图层管理")
        title_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        title_layout.addWidget(title_label)

        # 刷新按钮
        refresh_btn = QPushButton("🔄")
        refresh_btn.setMaximumWidth(30)
        refresh_btn.setToolTip("刷新图层列表")
        refresh_btn.clicked.connect(self.refresh_layers)
        title_layout.addWidget(refresh_btn)

        layout.addLayout(title_layout)

        # 图层列表
        self.layers_list = QListWidget()
        self.layers_list.setMinimumHeight(200)
        self.layers_list.setDragDropMode(QListWidget.InternalMove)  # 支持拖拽排序
        self.layers_list.model().rowsMoved.connect(self._on_layer_reordered)
        layout.addWidget(self.layers_list)

        # 说明文字
        help_label = QLabel("💡 提示: 拖拽调整图层顺序 (上方优先显示)")
        help_label.setStyleSheet("color: #666; font-size: 9pt;")
        layout.addWidget(help_label)

    def refresh_layers(self):
        """刷新图层列表"""
        if not self.canvas:
            return

        # 清空列表
        self.layers_list.clear()
        self.layer_items.clear()

        # 收集所有图层
        layers = []

        # 1. 道路层（如果存在）
        if hasattr(self.canvas, 'road_item') and self.canvas.road_item:
            road_item = self.canvas.road_item
            layers.append({
                'id': 'road_layer',
                'name': '🛣 道路层',
                'z_index': road_item.zValue(),
                'visible': road_item.isVisible(),
                'locked': not (road_item.flags() & QGraphicsItem.ItemIsMovable),
                'item': road_item
            })

        # 2. 场景元素
        for item in self.canvas.scene.items():
            if isinstance(item, SceneItemGraphics):
                # 从路径中提取文件名
                import os
                filename = os.path.basename(item.image_path)

                layers.append({
                    'id': item.item_id,  # 用于内部标识
                    'name': f'🖼 {filename}',  # 显示原始文件名
                    'z_index': item.zValue(),
                    'visible': item.isVisible(),
                    'locked': not (item.flags() & QGraphicsItem.ItemIsMovable),
                    'item': item
                })

        # 按z-index排序（从高到低，高的在上方）
        layers.sort(key=lambda x: x['z_index'], reverse=True)

        # 添加到列表
        for layer_data in layers:
            self._add_layer_item(layer_data)

    def _add_layer_item(self, layer_data):
        """添加图层项到列表"""
        # 创建列表项
        list_item = QListWidgetItem(self.layers_list)

        # 创建自定义widget
        layer_widget = QWidget()
        layer_layout = QHBoxLayout(layer_widget)
        layer_layout.setContentsMargins(5, 2, 5, 2)

        # 可见性复选框
        visibility_cb = QCheckBox()
        visibility_cb.setChecked(layer_data['visible'])
        visibility_cb.setToolTip("切换可见性")
        visibility_cb.toggled.connect(
            lambda checked, lid=layer_data['id']: self._on_visibility_changed(lid, checked)
        )
        layer_layout.addWidget(visibility_cb)

        # 锁定复选框
        lock_cb = QCheckBox()
        lock_cb.setText("🔒" if layer_data['locked'] else "🔓")
        lock_cb.setChecked(layer_data['locked'])
        lock_cb.setToolTip("切换锁定状态")
        lock_cb.toggled.connect(
            lambda checked, lid=layer_data['id']: self._on_lock_changed(lid, checked)
        )
        layer_layout.addWidget(lock_cb)

        # 图层名称
        name_label = QLabel(layer_data['name'])
        layer_layout.addWidget(name_label)

        layer_layout.addStretch()

        # Z-Index显示
        z_label = QLabel(f"Z: {int(layer_data['z_index'])}")
        z_label.setStyleSheet("color: #888; font-size: 9pt;")
        layer_layout.addWidget(z_label)

        # 设置widget到列表项
        list_item.setSizeHint(layer_widget.sizeHint())
        self.layers_list.addItem(list_item)
        self.layers_list.setItemWidget(list_item, layer_widget)

        # 保存引用
        self.layer_items[layer_data['id']] = {
            'list_item': list_item,
            'widget': layer_widget,
            'graphics_item': layer_data['item']
        }

    def _on_visibility_changed(self, layer_id, visible):
        """切换图层可见性"""
        if layer_id in self.layer_items:
            graphics_item = self.layer_items[layer_id]['graphics_item']
            graphics_item.setVisible(visible)

            # 刷新画布
            if self.canvas:
                self.canvas.update()

    def _on_lock_changed(self, layer_id, locked):
        """切换图层锁定状态"""
        if layer_id in self.layer_items:
            graphics_item = self.layer_items[layer_id]['graphics_item']

            # 设置可移动性
            if locked:
                graphics_item.setFlag(graphics_item.ItemIsMovable, False)
                graphics_item.setFlag(graphics_item.ItemIsSelectable, False)
            else:
                graphics_item.setFlag(graphics_item.ItemIsMovable, True)
                graphics_item.setFlag(graphics_item.ItemIsSelectable, True)

            # 更新锁定标记文本
            for widget in self.layer_items[layer_id]['widget'].findChildren(QCheckBox):
                if "锁定" in widget.toolTip():
                    widget.setText("🔒" if locked else "🔓")
                    break

    def _on_layer_reordered(self):
        """图层顺序改变时更新z-index"""
        if not self.canvas:
            return

        # 从上到下遍历列表，分配z-index
        item_count = self.layers_list.count()

        for i in range(item_count):
            list_item = self.layers_list.item(i)
            layer_widget = self.layers_list.itemWidget(list_item)

            # 找到对应的layer_id
            for layer_id, layer_info in self.layer_items.items():
                if layer_info['list_item'] == list_item:
                    # 计算新的z-index（上方=高z-index）
                    new_z = 100 - i  # 从100开始递减

                    # 更新graphics item的z-index
                    graphics_item = layer_info['graphics_item']
                    graphics_item.setZValue(new_z)

                    # 更新UI显示
                    for label in layer_widget.findChildren(QLabel):
                        if label.text().startswith("Z:"):
                            label.setText(f"Z: {new_z}")
                            break

                    break

        # 刷新画布
        self.canvas.update()


# ============================================================================
# 场景编辑器主窗口
# ============================================================================

class SceneEditorWindow(QMainWindow):
    """场景编辑器主窗口"""

    # 窗口关闭信号（用于通知父窗口刷新场景列表）
    editor_closed = Signal()

    def __init__(self):
        super().__init__()

        # 初始化日志记录器
        self.logger = logging.getLogger(__name__)

        self.setWindowTitle("GaiYa 场景编辑器 v2.0.0")
        self.setGeometry(100, 100, 1400, 800)

        # 确定场景保存目录（与 gaiya/scene/loader.py 保持一致）
        if getattr(sys, 'frozen', False):
            # PyInstaller 打包环境：exe 所在目录下的 scenes/（与exe同级）
            # 这样可以确保场景编辑器导出的场景，主窗口能够扫描到
            base_dir = Path(sys.executable).parent
            self.logger.info(f"[场景编辑器] 打包环境, exe目录: {base_dir}")
        else:
            # 开发环境：项目根目录（__file__ 是 scene_editor.py）
            base_dir = Path(__file__).parent
            self.logger.info(f"[场景编辑器] 开发环境, 项目根目录: {base_dir}")

        self.scenes_dir = base_dir / "scenes"
        self.scenes_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"[场景编辑器] 场景目录: {self.scenes_dir}")

        # 创建撤销栈
        self.undo_stack = QUndoStack(self)

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)

        # 创建三栏分割器
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：素材库
        self.asset_panel = AssetLibraryPanel()
        splitter.addWidget(self.asset_panel)

        # 中间：画布容器（画布 + 进度控制）
        canvas_container = QWidget()
        canvas_layout = QVBoxLayout(canvas_container)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.setSpacing(0)

        # 画布（传递撤销栈）
        self.canvas = SceneCanvas(undo_stack=self.undo_stack)
        self.canvas.item_selected.connect(self.on_item_selected)
        self.canvas.road_layer_selected.connect(self.on_road_layer_selected)
        canvas_layout.addWidget(self.canvas)

        # 进度控制工具栏（紧贴画布底部）
        progress_toolbar = QWidget()
        progress_toolbar.setMaximumHeight(50)
        progress_layout = QHBoxLayout(progress_toolbar)
        progress_layout.setContentsMargins(5, 5, 5, 5)

        # 播放/暂停按钮
        self.play_button = QPushButton("▶ 播放")
        self.play_button.clicked.connect(self.toggle_play)
        self.play_button.setMaximumWidth(70)
        progress_layout.addWidget(self.play_button)

        # 重置按钮
        reset_button = QPushButton("⏮ 重置")
        reset_button.clicked.connect(self.reset_progress)
        reset_button.setMaximumWidth(70)
        progress_layout.addWidget(reset_button)

        # 进度滑块
        progress_layout.addWidget(QLabel("进度:"))
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 100)
        self.progress_slider.setValue(0)
        self.progress_slider.valueChanged.connect(self.on_progress_changed)
        progress_layout.addWidget(self.progress_slider)

        self.progress_label = QLabel("0%")
        self.progress_label.setMinimumWidth(40)
        progress_layout.addWidget(self.progress_label)

        # 播放速度
        progress_layout.addWidget(QLabel("速度:"))
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.5x", "1x", "2x", "5x"])
        self.speed_combo.setCurrentIndex(1)  # 默认1x
        self.speed_combo.currentTextChanged.connect(self.on_speed_changed)
        self.speed_combo.setMaximumWidth(70)
        progress_layout.addWidget(self.speed_combo)

        canvas_layout.addWidget(progress_toolbar)

        splitter.addWidget(canvas_container)

        # 右侧：使用TabWidget组织属性面板和图层面板
        right_panel_tabs = QTabWidget()

        # Tab 1: 属性面板（传递canvas引用）
        self.property_panel = PropertyPanel(canvas=self.canvas)
        right_panel_tabs.addTab(self.property_panel, "⚙ 属性编辑")

        # Tab 2: 图层管理面板
        self.layer_panel = LayerPanel(canvas=self.canvas)
        right_panel_tabs.addTab(self.layer_panel, "📚 图层管理")

        splitter.addWidget(right_panel_tabs)

        # 设置分割比例（1:3:1）
        splitter.setSizes([250, 800, 350])

        main_layout.addWidget(splitter)

        # 创建工具栏（在canvas创建之后）
        self.create_toolbar()

        # 底部状态栏
        status_layout = QHBoxLayout()

        # 网格控制
        self.grid_checkbox = QCheckBox("显示网格")
        self.grid_checkbox.setChecked(True)
        self.grid_checkbox.toggled.connect(self.toggle_grid)
        status_layout.addWidget(self.grid_checkbox)

        self.snap_checkbox = QCheckBox("吸附网格")
        self.snap_checkbox.setChecked(True)
        self.snap_checkbox.toggled.connect(self.toggle_snap)
        status_layout.addWidget(self.snap_checkbox)

        # 对齐辅助线控制
        self.alignment_checkbox = QCheckBox("对齐辅助线")
        self.alignment_checkbox.setChecked(True)
        self.alignment_checkbox.toggled.connect(self.toggle_alignment_guides)
        status_layout.addWidget(self.alignment_checkbox)

        # 安全区域蒙版控制
        self.safe_mask_checkbox = QCheckBox("安全区域蒙版")
        self.safe_mask_checkbox.setChecked(True)
        self.safe_mask_checkbox.toggled.connect(self.toggle_safe_mask)
        status_layout.addWidget(self.safe_mask_checkbox)

        status_layout.addStretch()

        # 画布宽度选择
        status_layout.addWidget(QLabel("画布宽度:"))
        self.canvas_width_combo = QComboBox()
        self.canvas_width_combo.addItems(["1200px", "1600px", "1800px (推荐)", "2400px"])
        # 根据当前画布宽度设置默认值
        if self.canvas.canvas_width == 1200:
            self.canvas_width_combo.setCurrentIndex(0)
        elif self.canvas.canvas_width == 1600:
            self.canvas_width_combo.setCurrentIndex(1)
        elif self.canvas.canvas_width == 1800:
            self.canvas_width_combo.setCurrentIndex(2)
        elif self.canvas.canvas_width == 2400:
            self.canvas_width_combo.setCurrentIndex(3)
        else:
            self.canvas_width_combo.setCurrentIndex(2)  # 默认1800px
        self.canvas_width_combo.currentTextChanged.connect(self.on_canvas_width_changed)
        self.canvas_width_combo.setMaximumWidth(150)
        status_layout.addWidget(self.canvas_width_combo)

        # 导入场景按钮
        import_btn = QPushButton("📂 导入场景")
        import_btn.clicked.connect(self.import_config)
        import_btn.setToolTip("从config.json导入场景进行编辑")
        status_layout.addWidget(import_btn)

        # 导出场景按钮
        export_btn = QPushButton("💾 导出场景配置")
        export_btn.clicked.connect(self.export_config)
        export_btn.setToolTip("导出当前场景为config.json文件")
        status_layout.addWidget(export_btn)

        main_layout.addLayout(status_layout)

        # 初始化图层列表
        self.layer_panel.refresh_layers()

        # 连接场景变化信号到图层列表刷新
        self.canvas.scene_changed.connect(self.layer_panel.refresh_layers)

        # 创建快捷键
        self.create_shortcuts()

    def create_shortcuts(self):
        """创建快捷键"""
        from PySide6.QtGui import QShortcut, QKeySequence
        from PySide6.QtCore import Qt

        # Ctrl+C - 复制
        self.copy_shortcut = QShortcut(QKeySequence.Copy, self)
        self.copy_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.copy_shortcut.activated.connect(self._handle_copy)

        # Ctrl+V - 粘贴
        self.paste_shortcut = QShortcut(QKeySequence.Paste, self)
        self.paste_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.paste_shortcut.activated.connect(self._handle_paste)

        # Delete - 删除
        self.delete_shortcut = QShortcut(QKeySequence.Delete, self)
        self.delete_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.delete_shortcut.activated.connect(self._handle_delete)

        # Ctrl+A - 全选
        self.select_all_shortcut = QShortcut(QKeySequence.SelectAll, self)
        self.select_all_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.select_all_shortcut.activated.connect(self.select_all_items)

    def _handle_copy(self):
        """处理复制快捷键"""
        print("[DEBUG] Copy shortcut activated!")  # 调试日志
        self.canvas.copy_selected_items()

    def _handle_paste(self):
        """处理粘贴快捷键"""
        print("[DEBUG] Paste shortcut activated!")  # 调试日志
        self.canvas.paste_items()

    def _handle_delete(self):
        """处理删除快捷键"""
        print("[DEBUG] Delete shortcut activated!")  # 调试日志
        self.canvas.delete_selected_items()

    def select_all_items(self):
        """全选所有元素（场景层和道路层）"""
        for item in self.canvas.scene.items():
            # 选中场景元素和道路层
            if isinstance(item, SceneItemGraphics) or item == self.canvas.road_item:
                item.setSelected(True)

    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # 撤销动作
        undo_action = self.undo_stack.createUndoAction(self, "撤销")
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.setIcon(QIcon())  # 可以添加图标
        toolbar.addAction(undo_action)

        # 重做动作
        redo_action = self.undo_stack.createRedoAction(self, "重做")
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.setIcon(QIcon())  # 可以添加图标
        toolbar.addAction(redo_action)

        toolbar.addSeparator()

        # 复制动作（快捷键通过QShortcut单独设置，避免冲突）
        copy_action = QAction("复制 (Ctrl+C)", self)
        copy_action.triggered.connect(self._handle_copy)
        toolbar.addAction(copy_action)

        # 粘贴动作
        paste_action = QAction("粘贴 (Ctrl+V)", self)
        paste_action.triggered.connect(self._handle_paste)
        toolbar.addAction(paste_action)

        # 删除动作
        delete_action = QAction("删除 (Del)", self)
        delete_action.triggered.connect(self._handle_delete)
        toolbar.addAction(delete_action)

        toolbar.addSeparator()

        # 全选动作
        select_all_action = QAction("全选 (Ctrl+A)", self)
        select_all_action.triggered.connect(self.select_all_items)
        toolbar.addAction(select_all_action)

    def toggle_grid(self, checked):
        """切换网格显示"""
        self.canvas.show_grid = checked
        self.canvas.viewport().update()

    def toggle_snap(self, checked):
        """切换网格吸附"""
        self.canvas.snap_to_grid = checked

    def toggle_alignment_guides(self, checked):
        """切换对齐辅助线"""
        self.canvas.enable_alignment_guides = checked
        # 如果关闭，清除现有的辅助线
        if not checked:
            self.canvas.alignment_lines = []
            self.canvas.viewport().update()

    def toggle_safe_mask(self, checked):
        """切换安全区域蒙版显示"""
        self.canvas.toggle_safe_area_mask(checked)

    def on_canvas_width_changed(self, text):
        """处理画布宽度切换"""
        # 从文本中提取宽度值（"1800px (推荐)" -> 1800）
        width_str = text.split("px")[0]
        try:
            new_width = int(width_str)
        except ValueError:
            return

        # 保存当前画布宽度（用于计算比例）
        old_width = self.canvas.canvas_width

        # 更新画布宽度
        self.canvas.canvas_width = new_width
        self.canvas.scene.setSceneRect(0, 0, new_width, self.canvas.canvas_height)

        # 重新定位所有场景元素（基于x_percent，保持y_pixel不变）
        for item in self.canvas.scene_items:
            # 根据x_percent重新计算X位置
            new_x = item.x_percent * new_width
            item.setPos(new_x, item.y_pixel)

        # 重新渲染道路层（如果存在）
        if self.canvas.road_pixmap:
            self.canvas.update_road_layer()

        # 刷新视图
        self.canvas.viewport().update()

        # 刷新属性面板（如果有选中的元素）
        if self.property_panel.current_item:
            # 更新X位置显示（基于新宽度）
            x_pixel = int(self.property_panel.current_item.x_percent * new_width)
            self.property_panel.element_x_input.setValue(x_pixel)

    # ==================== 进度控制方法 ====================

    def toggle_play(self):
        """切换播放/暂停"""
        if self.canvas.is_playing:
            self.canvas.pause_preview()
            self.play_button.setText("▶ 播放")
        else:
            self.canvas.play_preview()
            self.play_button.setText("⏸ 暂停")

    def reset_progress(self):
        """重置进度到0"""
        self.canvas.reset_preview()
        self.play_button.setText("▶ 播放")
        self.progress_slider.setValue(0)

    def on_progress_changed(self, value):
        """进度滑块改变"""
        progress = value / 100.0
        self.canvas.set_progress(progress)
        self.progress_label.setText(f"{value}%")

    def on_speed_changed(self, text):
        """播放速度改变"""
        speed = float(text.replace('x', ''))
        self.canvas.set_play_speed(speed)

    def delete_selected(self):
        """删除选中的元素（已废弃，使用canvas.delete_selected_items）"""
        self.canvas.delete_selected_items()

    def on_item_selected(self, item: SceneItemGraphics):
        """处理元素选中事件"""
        self.property_panel.set_selected_item(item)

    def on_road_layer_selected(self):
        """处理道路层选中事件"""
        self.property_panel.show_road_panel()

    def export_config(self):
        """导出场景配置（自动复制所有图片到标准目录结构）"""
        import os
        import shutil
        from pathlib import Path

        # 配置日志文件（保存到用户可访问的位置）
        log_file = Path.home() / "scene_editor_export.log"

        # 创建专用的logger和handler（避免basicConfig配置冲突）
        logger = logging.getLogger('scene_export')
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()  # 清除已有的handlers

        # 创建文件handler
        file_handler = logging.FileHandler(str(log_file), mode='w', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        logger.info("=" * 50)
        logger.info("开始导出场景配置")
        logger.info(f"日志文件位置: {log_file}")
        logger.info("=" * 50)

        # 获取场景名称
        scene_name = self.property_panel.scene_name_input.text()
        logger.debug(f"场景名称: '{scene_name}'")
        if not scene_name:
            logger.error("场景名称为空！")
            QMessageBox.warning(self, "导出失败", "请先设置场景名称！")
            return

        # 规范化场景名称（去除非法字符）
        scene_name = "".join(c for c in scene_name if c.isalnum() or c in ('_', '-'))
        logger.debug(f"规范化后的场景名称: '{scene_name}'")
        if not scene_name:
            logger.error("场景名称格式不正确！")
            QMessageBox.warning(self, "导出失败", "场景名称格式不正确！请使用字母、数字、下划线或横线。")
            return

        # 检查目录冲突（使用实例的 scenes_dir）
        scene_dir = self.scenes_dir / scene_name
        logger.debug(f"导出目标目录: {scene_dir}")
        logger.debug(f"self.scenes_dir = {self.scenes_dir}")
        logger.debug(f"scene_dir.exists() = {scene_dir.exists()}")

        # 初始化备份路径（确保在所有代码路径中都能访问）
        road_backup_path = None
        scene_items_backup = {}  # 场景元素备份: {原始路径: 临时备份路径}

        if scene_dir.exists():
            logger.info(f"场景目录已存在，询问用户是否覆盖")
            reply = QMessageBox.question(
                self,
                "场景已存在",
                f"场景 '{scene_name}' 已存在，是否覆盖？\n\n路径: {scene_dir}",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                logger.info("用户选择不覆盖，取消导出")
                return

            # 在删除旧场景前，先备份道路层文件（如果存在）
            if self.canvas.road_image_path:
                old_road_path = Path(self.canvas.road_image_path)
                if old_road_path.exists():
                    import tempfile
                    # 创建临时文件备份道路层
                    with tempfile.NamedTemporaryFile(delete=False, suffix=old_road_path.suffix) as tmp:
                        shutil.copy2(old_road_path, tmp.name)
                        road_backup_path = tmp.name
                        logger.info(f"道路层已备份到: {road_backup_path}")

            # 在删除旧场景前，先备份所有场景元素的图片文件
            import tempfile
            for item in self.canvas.scene_items:
                if item.image_path:
                    old_item_path = Path(item.image_path)
                    if old_item_path.exists():
                        # 为每个元素创建临时备份
                        with tempfile.NamedTemporaryFile(delete=False, suffix=old_item_path.suffix) as tmp:
                            shutil.copy2(old_item_path, tmp.name)
                            scene_items_backup[item.image_path] = tmp.name
                            logger.debug(f"场景元素已备份: {old_item_path.name} -> {tmp.name}")

            if scene_items_backup:
                logger.info(f"已备份 {len(scene_items_backup)} 个场景元素")

            # 删除旧场景
            logger.info("删除旧场景目录...")
            try:
                shutil.rmtree(scene_dir)
                logger.info("旧场景删除成功")
            except Exception as e:
                logger.error(f"删除旧场景失败: {e}", exc_info=True)
                # 清理临时备份文件
                cleanup_count = 0
                if road_backup_path and Path(road_backup_path).exists():
                    try:
                        os.unlink(road_backup_path)
                        cleanup_count += 1
                    except Exception as cleanup_error:
                        logger.warning(f"清理道路层临时文件失败: {cleanup_error}")

                for original_path, backup_path in scene_items_backup.items():
                    if Path(backup_path).exists():
                        try:
                            os.unlink(backup_path)
                            cleanup_count += 1
                        except Exception as cleanup_error:
                            logger.warning(f"清理场景元素临时文件失败: {cleanup_error}")

                if cleanup_count > 0:
                    logger.info(f"已清理 {cleanup_count} 个临时备份文件")

                QMessageBox.critical(self, "删除失败", f"无法删除旧场景:\n{e}")
                return

        # 创建目录结构
        logger.info("创建场景目录结构...")
        try:
            logger.debug(f"创建主目录: {scene_dir}")
            scene_dir.mkdir(parents=True, exist_ok=True)

            logger.debug(f"创建 assets 子目录")
            assets_dir = scene_dir / "assets"
            assets_dir.mkdir(exist_ok=True)

            logger.info(f"目录创建成功: {scene_dir}")
        except Exception as e:
            logger.error(f"创建目录失败: {e}", exc_info=True)

            # 清理临时备份文件
            cleanup_count = 0
            if road_backup_path and Path(road_backup_path).exists():
                try:
                    os.unlink(road_backup_path)
                    cleanup_count += 1
                except Exception as cleanup_error:
                    logger.warning(f"清理道路层临时文件失败: {cleanup_error}")

            for original_path, backup_path in scene_items_backup.items():
                if Path(backup_path).exists():
                    try:
                        os.unlink(backup_path)
                        cleanup_count += 1
                    except Exception as cleanup_error:
                        logger.warning(f"清理场景元素临时文件失败: {cleanup_error}")

            if cleanup_count > 0:
                logger.info(f"已清理 {cleanup_count} 个临时备份文件")

            QMessageBox.critical(self, "创建目录失败", f"无法创建场景目录:\n{e}")
            return

        # 统计复制的文件
        copied_files = []

        # 生成配置字典
        config = {
            "scene_id": scene_name,
            "name": self.property_panel.scene_name_input.text(),
            "version": "1.0.0",
            "canvas": {
                "width": self.canvas.canvas_width,
                "height": self.canvas.canvas_height
            },
            "layers": {}
        }

        # 添加道路层（如果有）
        logger.info(f"检查道路层: road_image_path = {self.canvas.road_image_path}")
        if self.canvas.road_image_path:
            logger.info("开始处理道路层...")

            # 从道路层item的实际位置读取offset（用户可能拖动了道路层）
            if self.canvas.road_item:
                actual_pos = self.canvas.road_item.pos()
                self.canvas.road_offset_x = int(actual_pos.x())
                self.canvas.road_offset_y = int(actual_pos.y())
                logger.debug(f"道路层位置: x={self.canvas.road_offset_x}, y={self.canvas.road_offset_y}")

            # 复制道路层图片到 assets/ 目录
            road_dest_name = "road.png"  # 默认文件名
            try:
                # 优先使用备份文件，如果没有备份则使用当前路径
                if road_backup_path and Path(road_backup_path).exists():
                    road_src = Path(road_backup_path)
                    logger.info(f"使用备份的道路层文件: {road_src}")
                else:
                    road_src = Path(self.canvas.road_image_path)
                    logger.debug(f"道路层源文件: {road_src}")

                # 检查源文件是否存在
                if road_src.exists():
                    # 源文件存在，正常复制
                    road_dest_name = self._copy_file_with_rename(road_src, assets_dir, "road.png")
                    logger.info(f"道路层复制成功: {road_dest_name}")
                    copied_files.append(f"道路层: {road_dest_name}")

                    # 清理临时备份文件
                    if road_backup_path and Path(road_backup_path).exists():
                        try:
                            os.unlink(road_backup_path)
                            logger.debug(f"临时备份文件已清理: {road_backup_path}")
                        except:
                            pass
                else:
                    # 源文件不存在
                    logger.warning(f"道路层源文件不存在: {road_src}")
                    QMessageBox.warning(
                        self,
                        "警告",
                        f"道路层源文件不存在:\n{road_src}\n\n将跳过道路层导出。"
                    )
            except Exception as e:
                logger.error(f"复制道路层失败: {e}", exc_info=True)
                QMessageBox.warning(self, "警告", f"道路层复制失败，将继续导出其他内容:\n{e}")
                # 清理临时备份文件
                if road_backup_path and Path(road_backup_path).exists():
                    try:
                        os.unlink(road_backup_path)
                    except:
                        pass

            config["layers"]["road"] = {
                "type": "tiled",
                "image": f"assets/{road_dest_name}",  # 添加 assets/ 前缀
                "offset_x": self.canvas.road_offset_x,  # 修正字段名: x_offset → offset_x
                "offset_y": self.canvas.road_offset_y,  # 修正字段名: y_offset → offset_y
                "scale": self.canvas.road_scale,
                "z_index": int(self.canvas.road_item.zValue()) if self.canvas.road_item else 50
            }

        # 添加场景层并复制图片
        scene_items_config = []

        # 关键诊断信息
        logger.info(f"场景元素列表长度: {len(self.canvas.scene_items)}")
        logger.info(f"场景中的所有图形项: {len(self.canvas.scene.items())}")
        logger.info(f"scene_items 是否为空: {len(self.canvas.scene_items) == 0}")

        if len(self.canvas.scene_items) == 0:
            logger.warning("警告：scene_items 列表为空！")
            logger.debug("尝试从 scene.items() 中查找场景元素...")
            for item in self.canvas.scene.items():
                logger.debug(f"  - 图形项类型: {type(item).__name__}")

        for i, item in enumerate(self.canvas.scene_items):
            logger.info(f"处理第 {i+1}/{len(self.canvas.scene_items)} 个元素: {item.image_path}")
            try:
                # 复制场景元素图片到 assets/
                # 优先使用备份文件，如果没有备份则使用当前路径
                if item.image_path in scene_items_backup:
                    item_src = Path(scene_items_backup[item.image_path])
                    logger.info(f"  使用备份的场景元素文件: {item_src}")
                else:
                    item_src = Path(item.image_path)
                    logger.debug(f"  场景元素源文件: {item_src}")

                original_name = os.path.basename(item.image_path)
                logger.debug(f"  原始文件名: {original_name}")

                item_dest_name = self._copy_file_with_rename(item_src, assets_dir, original_name)
                logger.debug(f"  复制后文件名: {item_dest_name}")
                copied_files.append(f"场景元素: {item_dest_name}")

                # 获取配置（路径已经是 basename）
                item_config = item.to_config_dict()
                # 确保使用复制后的文件名，并添加 assets/ 前缀（因为图片在 assets/ 目录下）
                item_config["image"] = f"assets/{item_dest_name}"
                scene_items_config.append(item_config)
                logger.debug(f"  配置项添加成功: {item_config['id']}")
            except Exception as e:
                logger.error(f"处理元素 {i+1} 时出错: {e}", exc_info=True)

        config["layers"]["scene"] = {
            "items": scene_items_config
        }

        logger.info(f"场景配置项数量: {len(scene_items_config)}")
        logger.debug(f"完整配置（前500字符）: {json.dumps(config, indent=2, ensure_ascii=False)[:500]}")

        # 保存配置文件
        config_path = scene_dir / "config.json"
        logger.info(f"准备写入配置文件: {config_path}")
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info("配置文件写入成功！")
            logger.debug(f"配置文件大小: {config_path.stat().st_size} 字节")
        except Exception as e:
            logger.error(f"配置文件写入失败: {e}", exc_info=True)

            # 清理临时备份文件
            cleanup_count = 0
            if road_backup_path and Path(road_backup_path).exists():
                try:
                    os.unlink(road_backup_path)
                    cleanup_count += 1
                except Exception as cleanup_error:
                    logger.warning(f"清理道路层临时文件失败: {cleanup_error}")

            for original_path, backup_path in scene_items_backup.items():
                if Path(backup_path).exists():
                    try:
                        os.unlink(backup_path)
                        cleanup_count += 1
                    except Exception as cleanup_error:
                        logger.warning(f"清理场景元素临时文件失败: {cleanup_error}")

            if cleanup_count > 0:
                logger.info(f"已清理 {cleanup_count} 个临时备份文件")

            QMessageBox.critical(self, "保存失败", f"无法保存配置文件:\n{e}")
            return

        # 成功提示
        file_count = len(copied_files)
        logger.info(f"导出完成！共复制 {file_count} 个文件")
        logger.info("=" * 50)

        message = f"场景已成功导出到:\n{scene_dir.absolute()}\n\n"
        message += f"包含:\n- config.json\n- {file_count} 个图片文件\n\n"
        message += f"调试日志已保存到:\n{log_file}\n\n"
        message += "⚠️ 重要提示:\n"
        message += "新导出的场景需要【重启主程序】后才能在场景列表中显示。\n"
        message += "或者在主程序的场景设置中点击【刷新场景】按钮。"

        # 询问是否打开文件夹
        reply = QMessageBox.question(
            self,
            "导出成功",
            message + "\n\n是否打开文件夹？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            import subprocess
            import platform

            try:
                if platform.system() == "Windows":
                    os.startfile(scene_dir)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", str(scene_dir)])
                else:  # Linux
                    subprocess.run(["xdg-open", str(scene_dir)])
            except Exception as e:
                QMessageBox.warning(self, "打开失败", f"无法打开文件夹:\n{e}")

        # 清理临时备份文件
        cleanup_count = 0
        if road_backup_path and Path(road_backup_path).exists():
            try:
                os.unlink(road_backup_path)
                cleanup_count += 1
                logger.debug(f"已删除道路层临时备份: {road_backup_path}")
            except Exception as e:
                logger.warning(f"清理道路层临时文件失败: {e}")

        for original_path, backup_path in scene_items_backup.items():
            if Path(backup_path).exists():
                try:
                    os.unlink(backup_path)
                    cleanup_count += 1
                    logger.debug(f"已删除场景元素临时备份: {backup_path}")
                except Exception as e:
                    logger.warning(f"清理场景元素临时文件失败: {e}")

        if cleanup_count > 0:
            logger.info(f"已清理 {cleanup_count} 个临时备份文件")

    def _copy_file_with_rename(self, src_path: Path, dest_dir: Path, preferred_name: str) -> str:
        """
        复制文件到目标目录，如果文件名冲突则自动重命名

        Args:
            src_path: 源文件路径
            dest_dir: 目标目录
            preferred_name: 期望的文件名

        Returns:
            实际使用的文件名（可能被重命名）
        """
        import shutil

        # 分离文件名和扩展名
        name_part, ext_part = os.path.splitext(preferred_name)

        # 检查冲突并自动重命名
        dest_path = dest_dir / preferred_name
        counter = 1
        while dest_path.exists():
            # 生成新文件名：name_1.png, name_2.png, ...
            new_name = f"{name_part}_{counter}{ext_part}"
            dest_path = dest_dir / new_name
            counter += 1

        # 复制文件
        shutil.copy2(src_path, dest_path)

        return dest_path.name

    def import_config(self):
        """导入场景配置"""
        # 选择文件
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "导入场景配置",
            "",
            "JSON文件 (*.json)"
        )

        if not file_path:
            return

        try:
            # 读取配置文件
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 清空当前场景
            self._clear_scene()

            # 加载场景名称
            scene_name = config.get("name", "未命名场景")
            self.property_panel.scene_name_input.setText(scene_name)

            # 加载画布配置
            canvas_config = config.get("canvas", {})
            canvas_width = canvas_config.get("width", 1800)  # 读取画布宽度
            canvas_height = canvas_config.get("height", 150)

            # 更新画布宽度（通过宽度选择控件）
            width_index = self.canvas_width_combo.findText(f"{canvas_width}px")
            if width_index >= 0:
                self.canvas_width_combo.setCurrentIndex(width_index)
            else:
                # 如果找不到对应的宽度选项，手动设置
                self.canvas.canvas_width = canvas_width
                self.canvas.scene.setSceneRect(0, 0, canvas_width, canvas_height)

            # 更新画布高度
            self.property_panel.canvas_height_input.setValue(canvas_height)
            self.canvas.canvas_height = canvas_height
            self.canvas.scene.setSceneRect(0, 0, self.canvas.canvas_width, canvas_height)

            # 加载道路层
            layers = config.get("layers", {})
            road_config = layers.get("road")
            if road_config:
                self._load_road_layer(road_config, file_path)

            # 加载场景元素
            scene_layer = layers.get("scene", {})
            items = scene_layer.get("items", [])
            self._load_scene_items(items, file_path)

            # 刷新图层列表
            self.layer_panel.refresh_layers()

            # 刷新画布
            self.canvas.viewport().update()

            QMessageBox.information(
                self,
                "导入成功",
                f"场景配置已导入:\n{scene_name}\n\n包含 {len(items)} 个场景元素"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "导入失败",
                f"导入场景配置时出错:\n{str(e)}"
            )

    def _clear_scene(self):
        """清空当前场景"""
        # 清空所有场景元素
        for item in self.canvas.scene_items[:]:  # 使用切片避免修改列表时出错
            self.canvas.scene.removeItem(item)
        self.canvas.scene_items.clear()

        # 清空道路层
        if self.canvas.road_item:
            self.canvas.scene.removeItem(self.canvas.road_item)
            self.canvas.road_item = None
        self.canvas.road_image_path = None
        self.canvas.road_pixmap = None
        self.canvas.road_offset_x = 0
        self.canvas.road_offset_y = 0
        self.canvas.road_scale = 1.0

        # 清空撤销栈
        self.undo_stack.clear()

    def _load_road_layer(self, road_config: dict, config_file_path: str):
        """加载道路层"""
        import os
        from pathlib import Path

        # 获取配置文件所在目录
        config_dir = Path(config_file_path).parent

        # 获取道路图片文件名
        road_image_file = road_config.get("image", "")
        if not road_image_file:
            return

        # 构造完整路径（优先同目录下的assets文件夹）
        possible_paths = [
            config_dir / "assets" / road_image_file,  # scenes/xxx/assets/road.png
            config_dir / road_image_file,  # scenes/xxx/road.png
        ]

        road_image_path = None
        for path in possible_paths:
            if path.exists():
                road_image_path = str(path)
                break

        if not road_image_path:
            QMessageBox.warning(
                self,
                "道路图片未找到",
                f"无法找到道路图片:\n{road_image_file}\n\n请确保图片在config.json同目录或assets子目录中"
            )
            return

        # 先设置道路层配置参数（必须在set_road_image之前）
        # 注意：config.json中使用的键名是 offset_x/offset_y（不是 x_offset/y_offset）
        self.canvas.road_offset_x = road_config.get("offset_x", 0)
        self.canvas.road_offset_y = road_config.get("offset_y", 0)
        self.canvas.road_scale = road_config.get("scale", 1.0)

        # 设置道路图片（会使用上面设置的offset和scale）
        self.canvas.set_road_image(road_image_path)

        # 设置z-index
        if self.canvas.road_item:
            z_index = road_config.get("z_index", 50)
            self.canvas.road_item.setZValue(z_index)

    def _load_scene_items(self, items: list, config_file_path: str):
        """加载场景元素"""
        import os
        from pathlib import Path

        # 获取配置文件所在目录
        config_dir = Path(config_file_path).parent
        logging.info(f"[导入] 开始加载 {len(items)} 个场景元素")
        logging.debug(f"[导入] 配置文件目录: {config_dir}")

        for item_data in items:
            # 获取图片文件名
            image_file = item_data.get("image", "")
            if not image_file:
                logging.warning(f"[导入] 跳过空图片路径的元素")
                continue

            # 构造完整路径（优先同目录下的assets文件夹）
            possible_paths = [
                config_dir / "assets" / image_file,  # scenes/xxx/assets/item.png
                config_dir / image_file,  # scenes/xxx/item.png
            ]

            image_path = None
            for path in possible_paths:
                if path.exists():
                    image_path = str(path)
                    break

            if not image_path:
                logging.warning(f"[导入] 无法找到场景元素图片: {image_file}")
                logging.debug(f"[导入] 尝试的路径: {[str(p) for p in possible_paths]}")
                continue

            # 创建场景元素
            item_id = item_data.get("id", f"item_{len(self.canvas.scene_items) + 1}")
            logging.info(f"[导入] 成功加载图片: {image_path}, ID: {item_id}")
            scene_item = SceneItemGraphics(image_path, item_id, self.canvas)

            # 设置位置
            position = item_data.get("position", {})
            # 注意：config中保存的是0-100范围，需要转换为0-1范围
            scene_item.x_percent = position.get("x_percent", 0.0) / 100.0
            scene_item.y_pixel = position.get("y_pixel", 0)

            # 计算实际X位置（基于画布宽度）
            x_pos = scene_item.x_percent * self.canvas.canvas_width
            scene_item.setPos(x_pos, scene_item.y_pixel)

            # 设置缩放
            scale = item_data.get("scale", 1.0)
            scene_item.scale_factor = scale
            scene_item.setScale(scale)

            # 设置层级
            z_index = item_data.get("z_index", 51)
            scene_item.setZValue(z_index)

            # 加载事件配置
            events = item_data.get("events", [])
            for event_data in events:
                trigger = event_data.get("trigger", "")
                action_data = event_data.get("action", {})

                action = EventAction(
                    type=action_data.get("type", ""),
                    params=action_data.get("params", {})
                )

                event_config = EventConfig(trigger=trigger, action=action)

                # 加载触发器参数（如果有）
                trigger_params = event_data.get("trigger_params", {})
                if trigger_params:
                    event_config.trigger_params = trigger_params

                scene_item.events.append(event_config)

            # 添加到场景
            self.canvas.scene.addItem(scene_item)
            self.canvas.scene_items.append(scene_item)
            logging.debug(f"[导入] 元素已添加到scene_items, 当前总数: {len(self.canvas.scene_items)}")

    def closeEvent(self, event):
        """窗口关闭事件 - 发出信号通知父窗口"""
        self.editor_closed.emit()
        super().closeEvent(event)


def main():
    """主函数"""
    app = QApplication(sys.argv)

    window = SceneEditorWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
