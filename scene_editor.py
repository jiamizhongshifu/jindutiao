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
    QTextEdit, QDialogButtonBox, QSlider
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

        # 设置初始层级（默认为51，确保在道路层上方）
        # 道路层的z-index是50
        self.setZValue(51)

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

        # 连接场景选中信号
        self.scene.selectionChanged.connect(self._on_selection_changed)

    def _on_selection_changed(self):
        """场景选中项改变时触发"""
        selected_items = self.scene.selectedItems()
        if selected_items:
            # 只处理SceneItemGraphics类型的元素
            for item in selected_items:
                if isinstance(item, SceneItemGraphics):
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

        # 设置道路层不可选中、不可移动
        self.road_item.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.road_item.setFlag(QGraphicsItem.ItemIsMovable, False)

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
        print(f"[DEBUG] dropEvent triggered")  # 调试
        file_path = None
        is_road_layer = False  # 是否来自道路层列表

        # 优先检查是否从QListWidget拖拽
        source_widget = event.source()
        print(f"[DEBUG] source_widget: {source_widget}, type: {type(source_widget)}")  # 调试

        if isinstance(source_widget, QListWidget):
            # 从素材库拖拽
            current_item = source_widget.currentItem()
            print(f"[DEBUG] current_item: {current_item}")  # 调试
            if current_item:
                file_path = current_item.data(Qt.UserRole)
                print(f"[DEBUG] file_path from UserRole: {file_path}")  # 调试
                # 检查是否来自道路层列表
                parent = source_widget.parent()
                if parent and isinstance(parent, QGroupBox):
                    is_road_layer = parent.title() == "道路层"
                    print(f"[DEBUG] is_road_layer: {is_road_layer}, parent title: {parent.title()}")  # 调试

        # 如果不是从QListWidget，检查是否从文件管理器拖拽
        elif event.mimeData().hasUrls():
            file_path = event.mimeData().urls()[0].toLocalFile()
            print(f"[DEBUG] file_path from URLs: {file_path}")  # 调试

        # 如果获取到了有效的文件路径
        print(f"[DEBUG] final file_path: {file_path}, is_road_layer: {is_road_layer}")  # 调试
        if file_path and file_path.lower().endswith('.png'):
            if is_road_layer:
                # 设置为道路背景
                print(f"[DEBUG] Setting road image: {file_path}")  # 调试
                self.set_road_image(file_path)
            else:
                # 在放下位置添加场景元素
                pos = self.mapToScene(event.position().toPoint())
                print(f"[DEBUG] Adding scene item at pos: {pos.x()}, {pos.y()}")  # 调试
                self.add_scene_item(file_path, pos.x(), pos.y())
            event.acceptProposedAction()
        else:
            print(f"[DEBUG] Ignoring drop - invalid file_path or not PNG")  # 调试
            event.ignore()

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        super().mousePressEvent(event)

        # 获取点击位置的元素
        item = self.itemAt(event.position().toPoint())
        if isinstance(item, SceneItemGraphics):
            self.item_selected.emit(item)

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
        self.scene_list.setIconSize(QSize(64, 64))
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

        # 道路缩放控制（滑块形式）
        road_scale_container = QWidget()
        road_scale_layout = QHBoxLayout(road_scale_container)
        road_scale_layout.setContentsMargins(0, 0, 0, 0)

        self.road_scale_slider = QSlider(Qt.Horizontal)
        self.road_scale_slider.setRange(10, 300)  # 0.1x 到 3.0x（乘以100）
        self.road_scale_slider.setValue(100)  # 默认1.0x
        self.road_scale_slider.setEnabled(False)
        self.road_scale_slider.valueChanged.connect(self._on_road_scale_slider_changed)

        self.road_scale_label = QLabel("1.0x")
        self.road_scale_label.setMinimumWidth(50)
        self.road_scale_label.setAlignment(Qt.AlignCenter)

        road_scale_layout.addWidget(self.road_scale_slider)
        road_scale_layout.addWidget(self.road_scale_label)

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

        # 场景元素缩放控制（滑块形式）
        element_scale_container = QWidget()
        element_scale_layout = QHBoxLayout(element_scale_container)
        element_scale_layout.setContentsMargins(0, 0, 0, 0)

        self.element_scale_slider = QSlider(Qt.Horizontal)
        self.element_scale_slider.setRange(10, 300)  # 10% 到 300%
        self.element_scale_slider.setValue(100)  # 默认100%
        self.element_scale_slider.valueChanged.connect(self._on_scale_slider_changed)

        self.element_scale_label = QLabel("100%")
        self.element_scale_label.setMinimumWidth(50)
        self.element_scale_label.setAlignment(Qt.AlignCenter)

        element_scale_layout.addWidget(self.element_scale_slider)
        element_scale_layout.addWidget(self.element_scale_label)

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
        self.element_id_label.setText(item.item_id)
        self.element_x_input.setValue(item.x_percent * 100)
        self.element_y_input.setValue(item.y_pixel)

        # 更新缩放滑块和标签
        scale_value = int(item.scale_factor * 100)
        self.element_scale_slider.setValue(scale_value)
        self.element_scale_label.setText(f"{scale_value}%")

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

            # 更新缩放滑块和标签
            scale_value = int(self.canvas.road_scale * 100)
            self.road_scale_slider.setValue(scale_value)
            self.road_scale_label.setText(f"{self.canvas.road_scale:.1f}x")

            # 更新层级（从道路层item读取）
            if self.canvas.road_item:
                self.road_z_input.setValue(int(self.canvas.road_item.zValue()))

            self.road_x_input.setEnabled(True)
            self.road_y_input.setEnabled(True)
            self.road_scale_slider.setEnabled(True)
            self.road_z_input.setEnabled(True)
            self.clear_road_button.setEnabled(True)
        else:
            self.road_x_input.setEnabled(False)
            self.road_y_input.setEnabled(False)
            self.road_scale_slider.setEnabled(False)
            self.road_z_input.setEnabled(False)
            self.clear_road_button.setEnabled(False)

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

    def _on_scale_slider_changed(self, value):
        """缩放滑块改变"""
        if self._updating or not self.current_item:
            return

        # 更新标签显示
        self.element_scale_label.setText(f"{value}%")

        # 应用缩放
        scale = value / 100.0
        self.current_item.scale_factor = scale
        self.current_item.setScale(scale)

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
                self.road_scale_input.setEnabled(True)

    def _on_clear_road(self):
        """清除道路"""
        if self.canvas:
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
            self.road_scale_input.setValue(1.0)
            self.road_scale_input.setEnabled(False)

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

        # 更新标签显示
        self.road_scale_label.setText(f"{scale:.1f}x")

        # 应用缩放
        if self.canvas:
            self.canvas.road_scale = scale
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
            "layers": {}
        }

        # 添加道路层（如果有）
        if self.canvas.road_image_path:
            import os
            config["layers"]["road"] = {
                "type": "tiled",
                "image": os.path.basename(self.canvas.road_image_path)
            }

        # 添加场景层
        config["layers"]["scene"] = {
            "items": [
                item.to_config_dict()
                for item in self.canvas.scene_items
            ]
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
