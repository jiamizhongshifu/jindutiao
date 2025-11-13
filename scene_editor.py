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
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QListWidget, QListWidgetItem, QPushButton, QLabel,
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsItem,
    QGroupBox, QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox,
    QFileDialog, QMessageBox, QComboBox, QCheckBox, QToolBar, QDialog,
    QTextEdit, QDialogButtonBox
)
from PySide6.QtCore import Qt, QPointF, QRectF, QSize, Signal
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

    def undo(self):
        """撤销：移除元素"""
        self.canvas.scene.removeItem(self.item)
        if self.item in self.canvas.scene_items:
            self.canvas.scene_items.remove(self.item)


class MoveItemCommand(QUndoCommand):
    """移动元素命令"""

    def __init__(self, item: 'SceneItemGraphics', old_pos: QPointF, new_pos: QPointF):
        super().__init__("移动元素")
        self.item = item
        self.old_pos = old_pos
        self.new_pos = new_pos

    def redo(self):
        """重做：移动到新位置"""
        self.item.setPos(self.new_pos)

    def undo(self):
        """撤销：恢复到旧位置"""
        self.item.setPos(self.old_pos)


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
            "on_time_reach - 时间到达"
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

        # 时间参数只对on_time_reach可见
        self.time_input.setVisible(trigger == "on_time_reach")

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

        # 设置参数
        if "text" in config.action.params:
            self.text_input.setPlainText(config.action.params["text"])
        if "url" in config.action.params:
            self.url_input.setText(config.action.params["url"])
        if "time" in config.action.params:
            self.time_input.setText(config.action.params["time"])

    def get_event_config(self) -> EventConfig:
        """获取配置的事件"""
        trigger = self.trigger_combo.currentText().split(" - ")[0]
        action_type = self.action_type_combo.currentText().split(" - ")[0]

        # 构建参数字典
        params = {}

        if action_type == "open_url":
            params["url"] = self.url_input.text()
        else:
            params["text"] = self.text_input.toPlainText()

        if trigger == "on_time_reach":
            params["time"] = self.time_input.text()

        action = EventAction(type=action_type, params=params)
        return EventConfig(trigger=trigger, action=action)


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

        # 加载图片
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            self.setPixmap(pixmap)

        # 设置为可交互
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

    def itemChange(self, change, value):
        """元素变化时的回调"""
        if change == QGraphicsItem.ItemPositionChange and self.canvas:
            # 网格吸附
            if self.canvas.snap_to_grid:
                new_pos = value
                grid = self.canvas.grid_size

                # 吸附到网格
                snapped_x = round(new_pos.x() / grid) * grid
                snapped_y = round(new_pos.y() / grid) * grid

                return QPointF(snapped_x, snapped_y)

        return super().itemChange(change, value)

    def paint(self, painter, option, widget):
        """自定义绘制（添加选中边框）"""
        super().paint(painter, option, widget)

        # 如果被选中，绘制边框
        if self.isSelected():
            painter.setPen(QPen(QColor(0, 120, 215), 2, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.boundingRect())

    def to_config_dict(self) -> dict:
        """导出为配置字典"""
        return {
            "id": self.item_id,
            "image": os.path.basename(self.image_path),
            "position": {
                "x_percent": self.x_percent,
                "y_pixel": self.y_pixel
            },
            "scale": self.scale_factor,
            "z_index": int(self.zValue()),
            "events": [event.to_dict() for event in self.events]
        }


class SceneCanvas(QGraphicsView):
    """场景画布视图"""

    item_selected = Signal(SceneItemGraphics)  # 元素选中信号

    def __init__(self, parent=None, undo_stack=None):
        super().__init__(parent)

        # 创建场景
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # 设置画布尺寸（默认1200x150）
        self.canvas_width = 1200
        self.canvas_height = 150
        self.scene.setSceneRect(0, 0, self.canvas_width, self.canvas_height)

        # 道路层设置
        self.road_image_path: Optional[str] = None  # 道路图片路径
        self.road_pixmap: Optional[QPixmap] = None  # 道路图片

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

        # 撤销栈
        self.undo_stack = undo_stack

        # 启用拖拽接受
        self.setAcceptDrops(True)

    def set_road_image(self, image_path: str):
        """设置道路层图片"""
        self.road_image_path = image_path
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            self.road_pixmap = pixmap
            self.viewport().update()  # 刷新显示

    def drawBackground(self, painter: QPainter, rect: QRectF):
        """绘制背景网格"""
        super().drawBackground(painter, rect)

        # 1. 绘制道路层（平铺）
        if self.road_pixmap and not self.road_pixmap.isNull():
            road_width = self.road_pixmap.width()
            road_height = self.road_pixmap.height()

            # 平铺绘制道路
            for x in range(0, int(self.canvas_width), road_width):
                # 道路只在画布高度范围内绘制
                painter.drawPixmap(x, 0, self.road_pixmap)

        # 2. 绘制网格
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

        # 使用撤销命令添加元素
        if use_undo and self.undo_stack:
            command = AddItemCommand(self, item)
            self.undo_stack.push(command)
        else:
            # 直接添加（不记录到撤销栈）
            self.scene.addItem(item)
            self.scene_items.append(item)

        return item

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

        # 处理从文件管理器拖拽的文件
        if event.mimeData().hasUrls():
            file_path = event.mimeData().urls()[0].toLocalFile()

        # 处理从素材库拖拽的项目
        elif event.mimeData().hasText():
            # QListWidget拖拽时会传递文本数据
            # 我们需要从源widget获取数据
            source_widget = event.source()
            if isinstance(source_widget, QListWidget):
                current_item = source_widget.currentItem()
                if current_item:
                    file_path = current_item.data(Qt.UserRole)

        # 如果获取到了有效的文件路径
        if file_path and file_path.lower().endswith('.png'):
            # 在放下位置添加元素
            pos = self.mapToScene(event.position().toPoint())
            self.add_scene_item(file_path, pos.x(), pos.y())
            event.acceptProposedAction()

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        super().mousePressEvent(event)

        # 获取点击位置的元素
        item = self.itemAt(event.position().toPoint())
        if isinstance(item, SceneItemGraphics):
            self.item_selected.emit(item)


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
        self.road_list.setIconSize(QSize(64, 64))
        road_layout.addWidget(self.road_list)
        layout.addWidget(road_group)

        # 场景层分组
        scene_group = QGroupBox("场景层")
        scene_layout = QVBoxLayout(scene_group)
        self.scene_list = QListWidget()
        self.scene_list.setIconSize(QSize(64, 64))
        scene_layout.addWidget(self.scene_list)
        layout.addWidget(scene_group)

        # 导入按钮
        import_btn = QPushButton("+ 导入素材")
        import_btn.clicked.connect(self.import_asset)
        layout.addWidget(import_btn)

        # 启用拖拽
        self.road_list.setDragEnabled(True)
        self.scene_list.setDragEnabled(True)

        # 设置拖拽模式
        self.road_list.setDragDropMode(QListWidget.DragOnly)
        self.scene_list.setDragDropMode(QListWidget.DragOnly)

    def import_asset(self):
        """导入素材文件"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择素材文件",
            "",
            "PNG图片 (*.png)"
        )

        for file_path in file_paths:
            self.add_asset(file_path)

    def add_asset(self, file_path: str):
        """添加素材到列表"""
        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            return

        # 创建列表项
        item = QListWidgetItem(QIcon(pixmap), os.path.basename(file_path))
        item.setData(Qt.UserRole, file_path)

        # 根据文件名判断添加到哪个列表
        filename = os.path.basename(file_path).lower()
        if 'road' in filename or 'path' in filename:
            self.road_list.addItem(item)
        else:
            self.scene_list.addItem(item)


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
        road_group = QGroupBox("道路层")
        road_layout = QVBoxLayout(road_group)

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
        layout.addWidget(road_group)

        # 选中元素分组
        self.element_group = QGroupBox("选中元素")
        self.element_group.setEnabled(False)  # 默认禁用，直到选中元素
        element_layout = QFormLayout(self.element_group)

        self.element_id_label = QLabel("未选中")
        element_layout.addRow("ID:", self.element_id_label)

        self.element_x_input = QDoubleSpinBox()
        self.element_x_input.setRange(0.0, 100.0)
        self.element_x_input.setSuffix(" %")
        self.element_x_input.setSingleStep(0.1)
        self.element_x_input.valueChanged.connect(self._on_x_changed)
        element_layout.addRow("X位置:", self.element_x_input)

        self.element_y_input = QSpinBox()
        self.element_y_input.setRange(0, 300)
        self.element_y_input.setSuffix(" px")
        self.element_y_input.valueChanged.connect(self._on_y_changed)
        element_layout.addRow("Y位置:", self.element_y_input)

        self.element_scale_input = QSpinBox()
        self.element_scale_input.setRange(10, 300)
        self.element_scale_input.setValue(100)
        self.element_scale_input.setSuffix(" %")
        self.element_scale_input.valueChanged.connect(self._on_scale_changed)
        element_layout.addRow("缩放:", self.element_scale_input)

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
        self.element_group.setEnabled(True)

        # 阻止信号触发，避免循环更新
        self._updating = True

        # 更新UI显示
        self.element_id_label.setText(item.item_id)
        self.element_x_input.setValue(item.x_percent * 100)
        self.element_y_input.setValue(item.y_pixel)
        self.element_scale_input.setValue(item.scale_factor * 100)
        self.element_z_input.setValue(int(item.zValue()))

        # 加载事件列表
        self._load_events_list()

        self._updating = False

    def _on_x_changed(self, value):
        """X位置改变"""
        if self._updating or not self.current_item:
            return

        self.current_item.x_percent = value / 100.0
        # TODO: 根据画布宽度更新实际像素位置

    def _on_y_changed(self, value):
        """Y位置改变"""
        if self._updating or not self.current_item:
            return

        self.current_item.y_pixel = value
        self.current_item.setY(value)

    def _on_scale_changed(self, value):
        """缩放改变"""
        if self._updating or not self.current_item:
            return

        scale = value / 100.0
        self.current_item.scale_factor = scale
        self.current_item.setScale(scale)

    def _on_z_changed(self, value):
        """层级改变"""
        if self._updating or not self.current_item:
            return

        self.current_item.setZValue(value)

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

                # 启用清除按钮
                self.clear_road_button.setEnabled(True)

    def _on_clear_road(self):
        """清除道路"""
        if self.canvas:
            self.canvas.road_image_path = None
            self.canvas.road_pixmap = None
            self.canvas.viewport().update()

            # 重置预览
            self.road_preview.clear()
            self.road_preview.setText("未选择道路图片")
            self.road_filename_label.setText("文件: 无")
            self.clear_road_button.setEnabled(False)

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
                "on_time_reach": "时间到达"
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


class SceneEditorWindow(QMainWindow):
    """场景编辑器主窗口"""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("GaiYa 场景编辑器 v1.0.0")
        self.setGeometry(100, 100, 1400, 800)

        # 创建撤销栈
        self.undo_stack = QUndoStack(self)

        # 创建工具栏
        self.create_toolbar()

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

        # 中间：画布（传递撤销栈）
        self.canvas = SceneCanvas(undo_stack=self.undo_stack)
        self.canvas.item_selected.connect(self.on_item_selected)
        splitter.addWidget(self.canvas)

        # 右侧：属性面板（传递canvas引用）
        self.property_panel = PropertyPanel(canvas=self.canvas)
        splitter.addWidget(self.property_panel)

        # 设置分割比例（1:3:1）
        splitter.setSizes([250, 800, 350])

        main_layout.addWidget(splitter)

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

        status_layout.addStretch()

        export_btn = QPushButton("导出场景配置")
        export_btn.clicked.connect(self.export_config)
        status_layout.addWidget(export_btn)

        main_layout.addLayout(status_layout)

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

        # 删除元素动作
        delete_action = QAction("删除", self)
        delete_action.setShortcut(QKeySequence.Delete)
        delete_action.triggered.connect(self.delete_selected)
        toolbar.addAction(delete_action)

    def toggle_grid(self, checked):
        """切换网格显示"""
        self.canvas.show_grid = checked
        self.canvas.viewport().update()

    def toggle_snap(self, checked):
        """切换网格吸附"""
        self.canvas.snap_to_grid = checked

    def delete_selected(self):
        """删除选中的元素"""
        # TODO: 实现删除功能
        pass

    def on_item_selected(self, item: SceneItemGraphics):
        """处理元素选中事件"""
        self.property_panel.set_selected_item(item)

    def export_config(self):
        """导出场景配置"""
        # 生成配置字典
        config = {
            "scene_id": "scene_001",
            "name": self.property_panel.scene_name_input.text() or "未命名场景",
            "version": "1.0.0",
            "canvas": {
                "width": self.canvas.canvas_width,
                "height": self.canvas.canvas_height
            },
            "layers": {
                "scene": {
                    "items": [
                        item.to_config_dict()
                        for item in self.canvas.scene_items
                    ]
                }
            }
        }

        # 保存到文件
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存场景配置",
            "",
            "JSON文件 (*.json)"
        )

        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            QMessageBox.information(
                self,
                "导出成功",
                f"场景配置已保存到:\n{file_path}"
            )


def main():
    """主函数"""
    app = QApplication(sys.argv)

    window = SceneEditorWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
