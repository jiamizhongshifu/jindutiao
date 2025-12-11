# -*- coding: utf-8 -*-
"""
GaiYa每日进度条 - 可视化配置界面
提供图形化界面来管理配置和任务
"""

import json
import os
import sys
from pathlib import Path
from functools import partial
from typing import Dict, List, Any, Optional, Tuple
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QPushButton, QColorDialog,
    QComboBox, QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QTimeEdit, QGroupBox, QFormLayout, QFileDialog, QDialog,
    QDialogButtonBox, QButtonGroup, QRadioButton, QProgressDialog, QSlider
)
from PySide6.QtCore import Qt, QTime, Signal, QThread, QTimer
from PySide6.QtGui import QColor, QIcon
from timeline_editor import TimelineEditor
from ai_client import GaiyaAIClient
from autostart_manager import AutoStartManager
import requests
from gaiya.core.theme_manager import ThemeManager
from gaiya.core.theme_ai_helper import ThemeAIHelper
import logging
from gaiya.utils import path_utils, time_utils, data_loader
from version import __version__, VERSION_STRING, VERSION_STRING_ZH

# i18n国际化支持
from i18n.translator import tr

# 浅色主题支持（MacOS极简风格）
from gaiya.ui.style_manager import StyleManager, apply_light_theme

# 场景编辑器
from scene_editor import SceneEditorWindow


# 使用gaiya.core.async_worker中的异步类(统一管理)
from gaiya.core.async_worker import AsyncAIWorker as AIWorker
from gaiya.core.marker_presets import MarkerPresetManager


class PaymentOptionCard(QWidget):
    """Payment option card widget - uses QPainter for reliable rendering in PyInstaller

    Card-based selection without radio buttons:
    - Normal: white background + 2px gray border #D0D0D0
    - Hover: light gray background + darker border #999999
    - Selected: white background + 3px cyan border #4ECDC4 (matches plan cards)

    Implementation note:
    Uses QPainter manual drawing instead of setStyleSheet to avoid PyInstaller
    packaging issues where stylesheet borders appear on child components instead
    of parent container (reference: membership_ui.py SolidCardWidget).
    """

    # Signal emitted when card is clicked with payment method ID
    clicked = Signal(str)

    def __init__(self, pay_method_id, parent=None):
        super().__init__(parent)
        self._pay_method_id = pay_method_id
        self._is_selected = False
        self._is_hovering = False

        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)

        # CRITICAL: Clear QWidget default border and background (prevents black border in packaging)
        self.setStyleSheet("""
            PaymentOptionCard {
                border: none;
                background: transparent;
            }
        """)

        # CRITICAL: Disable focus to prevent Windows from drawing black focus frame
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # CRITICAL: Disable system default rendering (exactly like SolidCardWidget)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAutoFillBackground(False)

        self.setMinimumHeight(70)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_selected(self, selected: bool):
        """Set selection state and trigger repaint"""
        self._is_selected = selected
        self.update()  # Trigger paintEvent

    def enterEvent(self, event):
        """Mouse enter event - trigger hover state"""
        self._is_hovering = True
        self.update()  # Trigger paintEvent
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Mouse leave event - clear hover state"""
        self._is_hovering = False
        self.update()  # Trigger paintEvent
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """Mouse press event - emit clicked signal"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._pay_method_id)
        super().mousePressEvent(event)

    def paintEvent(self, event):
        """Manual drawing using QPainter - ensures consistent rendering in PyInstaller"""
        from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath
        from PySide6.QtCore import Qt, QRectF

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # Anti-aliasing for smooth edges

        rect = self.rect()

        # 1. Draw background
        if self._is_selected:
            bg_color = QColor("#FFFFFF")  # White
        elif self._is_hovering:
            bg_color = QColor("#EEEEEE")  # Light gray
        else:
            bg_color = QColor("#FFFFFF")  # White

        # Create rounded rectangle path
        border_radius = 8
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), border_radius, border_radius)

        painter.fillPath(path, QBrush(bg_color))

        # 2. Draw border
        if self._is_selected:
            # Selected: cyan thick border (3px #4ECDC4)
            pen = QPen(QColor("#4ECDC4"), 3)
        elif self._is_hovering:
            # Hover: dark gray border (2px #999999)
            pen = QPen(QColor("#999999"), 2)
        else:
            # Normal: light gray border (2px #D0D0D0)
            pen = QPen(QColor("#D0D0D0"), 2)

        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Adjust rect to prevent border clipping
        border_width = 3 if self._is_selected else 2
        adjusted_rect = rect.adjusted(
            border_width // 2,
            border_width // 2,
            -border_width // 2,
            -border_width // 2
        )

        path_border = QPainterPath()
        path_border.addRoundedRect(QRectF(adjusted_rect), border_radius, border_radius)
        painter.drawPath(path_border)

        # 确保 painter 正确结束,防止 QBackingStore::endPaint() 错误
        painter.end()


class SaveTemplateDialog(QDialog):
    """保存模板对话框 - 智能适应有无历史模板的情况"""

    def __init__(self, existing_templates, parent=None):
        """
        初始化对话框

        Args:
            existing_templates: 现有模板列表 [{"name": "模板名", ...}, ...]
            parent: 父窗口
        """
        super().__init__(parent)

        # Initialize i18n translator
        from i18n.translator import _translator
        self.i18n = _translator

        self.existing_templates = existing_templates
        self.template_name = None
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(self.i18n.tr("dialog.save_template_title"))
        self.setMinimumWidth(400)

        layout = QVBoxLayout()

        # 提示文本
        if self.existing_templates:
            hint_label = QLabel(self.i18n.tr("dialog.select_or_new"))
        else:
            hint_label = QLabel(self.i18n.tr("dialog.enter_name"))

        layout.addWidget(hint_label)

        # 根据是否有历史模板决定使用下拉框还是输入框
        if self.existing_templates:
            # 有历史模板,使用可编辑的下拉框
            self.input_widget = QComboBox()
            self.input_widget.setEditable(True)
            self.input_widget.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

            # 添加历史模板到下拉框
            for template in self.existing_templates:
                template_name = template.get('name', '')
                task_count = template.get('task_count', 0)
                display_text = self.i18n.tr("config.templates.task_count", template_name=template_name, task_count=task_count)
                self.input_widget.addItem(display_text, template_name)

            # 设置当前文本为空,引导用户选择或输入
            self.input_widget.setCurrentIndex(-1)
            self.input_widget.setPlaceholderText(self.i18n.tr("templates.dialog.placeholder_select"))
        else:
            # 无历史模板,使用普通输入框
            self.input_widget = QLineEdit()
            self.input_widget.setPlaceholderText(self.i18n.tr("templates.dialog.placeholder_example"))

        layout.addWidget(self.input_widget)

        # 提示信息
        if self.existing_templates:
            tip_label = QLabel(
                "💡 提示:\n"
                + self.i18n.tr("config.dialogs.overwrite_template_warning")
                + "\n• 输入新名称将创建新的模板"
            )
            tip_label.setStyleSheet(StyleManager.label_hint())
            layout.addWidget(tip_label)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def accept(self):
        """确定按钮点击"""
        # 获取模板名称
        if isinstance(self.input_widget, QComboBox):
            # 下拉框:可能是选择的历史模板,也可能是手动输入的新名称
            current_text = self.input_widget.currentText()

            # 检查是否选择了历史模板(通过匹配显示文本)
            current_data = self.input_widget.currentData()
            if current_data:
                # 选择了历史模板
                self.template_name = current_data
            else:
                # 手动输入的新名称
                # 需要去掉可能的任务数量后缀
                template_name = current_text.strip()
                # 如果输入的恰好和某个显示文本一致,提取实际名称
                for i in range(self.input_widget.count()):
                    if self.input_widget.itemText(i) == template_name:
                        template_name = self.input_widget.itemData(i)
                        break
                self.template_name = template_name
        else:
            # 输入框
            self.template_name = self.input_widget.text().strip()

        # 验证名称不为空
        if not self.template_name:
            QMessageBox.warning(self, self.i18n.tr("message.text_2881"), "模板名称不能为空!")
            return

        super().accept()

    def get_template_name(self):
        """获取用户输入/选择的模板名称"""
        return self.template_name


class ConfigManager(QMainWindow):
    """配置管理主窗口"""

    config_saved = Signal()  # 配置保存信号

    # 预设色板:定义新任务的默认颜色循环顺序
    COLOR_PALETTE = [
        "#4CAF50",  # 绿色 - Material Green
        "#2196F3",  # 蓝色 - Material Blue
        "#FF9800",  # 橙色 - Material Orange
        "#E91E63",  # 粉红色 - Material Pink
        "#9C27B0",  # 紫色 - Material Purple
        "#00BCD4",  # 青色 - Material Cyan
        "#FFC107",  # 琥珀色 - Material Amber
        "#F44336",  # 红色 - Material Red
        "#8BC34A",  # 浅绿色 - Material Light Green
        "#3F51B5",  # 靛蓝色 - Material Indigo
        "#FFEB3B",  # 黄色 - Material Yellow
        "#795548",  # 棕色 - Material Brown
    ]

    def __init__(self, main_window=None):
        super().__init__()
        # 保存主窗口引用（用于访问 scene_manager 等）
        self.main_window = main_window

        # Initialize i18n translator
        from i18n.translator import _translator
        self.i18n = _translator

        # 获取应用程序目录(使用统一的path_utils)
        self.app_dir = path_utils.get_app_dir()

        self.config_file = self.app_dir / 'config.json'
        self.tasks_file = self.app_dir / 'tasks.json'

        # 延迟加载配置和任务，先让窗口显示
        self.config = {}
        self.tasks = []

        # ✅ 性能优化: 配置文件防抖动保存器(减少磁盘I/O)
        from gaiya.utils.config_debouncer import ConfigDebouncer
        self.config_debouncer = ConfigDebouncer(
            config_file=self.config_file,
            delay_ms=500,  # 500ms防抖动延迟
            on_save_callback=lambda: self.config_saved.emit()  # 保存完成后发送信号
        )
        
        # 延迟初始化AI相关组件(避免阻塞UI显示)
        self.ai_client = None
        self.ai_worker = None
        self.auth_client = None  # ✅ Fix: Initialize AuthClient lazily to avoid UI blocking
        self.autostart_manager = AutoStartManager()  # 自启动管理器
        self.theme_ai_helper = None

        # 延迟初始化主题管理器(避免同步文件I/O阻塞UI)
        self.theme_manager = None
        # 延迟初始化模板管理器
        self.template_manager = None
        self.schedule_manager = None
        # 初始化标记图片预设管理器
        self.marker_preset_manager = MarkerPresetManager()

        # 场景编辑器窗口引用（延迟创建）
        self.scene_editor_window = None

        # 行为识别统计信息实时更新
        self.behavior_stats_timer = None  # 统计信息更新定时器
        self.stats_labels = {}  # 统计标签引用字典 {category: QLabel}

        # 先初始化UI,让窗口快速显示
        self.init_ui()

        # UI显示后再异步加载配置和任务
        QTimer.singleShot(50, self._load_config_and_tasks)

        # UI显示后再异步初始化主题管理器和AI组件
        QTimer.singleShot(100, self._init_theme_manager)
        QTimer.singleShot(150, self._init_template_manager)
        QTimer.singleShot(160, self._init_schedule_manager)
        QTimer.singleShot(200, self._init_ai_components)

    def _load_config_and_tasks(self):
        """延迟加载配置和任务（不阻塞UI显示）"""
        try:
            self.config = self.load_config()
            self.tasks = self.load_tasks()
            
            # 如果任务为空,默认加载24小时模板
            if not self.tasks:
                self.load_default_template()
            
            # 更新UI控件的值（如果已创建）
            self._update_ui_from_config()
            
            # 如果任务表格已创建，加载任务
            if hasattr(self, 'tasks_table') and self.tasks_table is not None:
                self.load_tasks_to_table()
            
            logging.info("配置和任务加载完成")
        except Exception as e:
            logging.error(f"加载配置和任务失败: {e}")
    
    def _update_ui_from_config(self):
        """从配置更新UI控件值"""
        if not self.config:
            return
        
        try:
            # 更新高度控件
            if hasattr(self, 'height_spin'):
                self.height_spin.setValue(self.config.get('bar_height', 20))
                if hasattr(self, 'height_preset_buttons'):
                    self.update_height_preset_buttons()
            
            # 更新位置控件
            if hasattr(self, 'position_combo'):
                self.position_combo.setCurrentText(self.config.get('position', 'bottom'))
            
            # 更新显示器索引
            if hasattr(self, 'screen_spin'):
                self.screen_spin.setValue(self.config.get('screen_index', 0))
            
            # 更新间隔
            if hasattr(self, 'interval_spin'):
                self.interval_spin.setValue(self.config.get('update_interval', 1000))

            # 更新自启动复选框（从注册表读取真实状态）
            if hasattr(self, 'autostart_check') and self.autostart_manager:
                registry_status = self.autostart_manager.is_enabled()
                self.autostart_check.setChecked(registry_status)
                self._update_autostart_status_label()

            # 更新颜色控件
            if hasattr(self, 'bg_color_input'):
                bg_color = self.config.get('background_color', '#505050')
                self.bg_color_input.setText(bg_color)
                # 更新颜色预览按钮样式
                if hasattr(self, 'bg_color_preview'):
                    self.bg_color_preview.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {bg_color};
                            border: 2px solid #CCCCCC;
                            border-radius: 4px;
                        }}
                        QPushButton:hover {{
                            border: 2px solid #999999;
                        }}
                    """)

            # 更新背景透明度滑块(将0-255转换为0-100百分比)
            if hasattr(self, 'opacity_slider'):
                opacity_value = self.config.get('background_opacity', 180)
                opacity_percent = int(opacity_value / 255 * 100)
                self.opacity_slider.setValue(opacity_percent)
                if hasattr(self, 'opacity_label'):
                    self.opacity_label.setText(f"{opacity_percent}%")

            if hasattr(self, 'marker_color_input'):
                marker_color = self.config.get('marker_color', '#FF0000')
                self.marker_color_input.setText(marker_color)
                # 更新颜色预览按钮样式
                if hasattr(self, 'marker_color_preview'):
                    self.marker_color_preview.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {marker_color};
                            border: 2px solid #CCCCCC;
                            border-radius: 4px;
                        }}
                        QPushButton:hover {{
                            border: 2px solid #999999;
                        }}
                    """)
            
            if hasattr(self, 'marker_width_spin'):
                self.marker_width_spin.setValue(self.config.get('marker_width', 2))
            
            if hasattr(self, 'marker_type_combo'):
                self.marker_type_combo.setCurrentText(self.config.get('marker_type', 'line'))
            
            if hasattr(self, 'marker_image_input'):
                self.marker_image_input.setText(self.config.get('marker_image_path', ''))
            
            if hasattr(self, 'marker_size_spin'):
                self.marker_size_spin.setValue(self.config.get('marker_size', 50))
                if hasattr(self, 'marker_size_preset_buttons'):
                    self.update_marker_size_preset_buttons()
            
            if hasattr(self, 'marker_speed_spin'):
                self.marker_speed_spin.setValue(self.config.get('marker_speed', 100))

            if hasattr(self, 'marker_always_visible_check'):
                self.marker_always_visible_check.setChecked(self.config.get('marker_always_visible', True))

            if hasattr(self, 'marker_x_offset_spin'):
                self.marker_x_offset_spin.setValue(self.config.get('marker_x_offset', 0))

            if hasattr(self, 'marker_y_offset_spin'):
                self.marker_y_offset_spin.setValue(self.config.get('marker_y_offset', 0))

            # 加载标记图片预设配置
            if self.marker_preset_manager:
                self.marker_preset_manager.load_from_config(self.config)

                # 同步预设下拉框选中项
                if hasattr(self, 'marker_preset_combo'):
                    current_preset_id = self.marker_preset_manager.get_current_preset_id()
                    # 查找对应的下拉框索引
                    for i in range(self.marker_preset_combo.count()):
                        if self.marker_preset_combo.itemData(i) == current_preset_id:
                            self.marker_preset_combo.setCurrentIndex(i)
                            break

            # 更新弹幕参数
            danmaku_config = self.config.get('danmaku', {})
            if hasattr(self, 'danmaku_enabled_check'):
                self.danmaku_enabled_check.setChecked(danmaku_config.get('enabled', True))
            if hasattr(self, 'danmaku_frequency_spin'):
                self.danmaku_frequency_spin.setValue(danmaku_config.get('frequency', 30))
            if hasattr(self, 'danmaku_speed_spin'):
                self.danmaku_speed_spin.setValue(danmaku_config.get('speed', 1.0))
            if hasattr(self, 'danmaku_font_size_spin'):
                self.danmaku_font_size_spin.setValue(danmaku_config.get('font_size', 14))

            # 更新弹幕透明度滑块(将0-1转换为0-100百分比)
            if hasattr(self, 'danmaku_opacity_slider'):
                opacity_value = danmaku_config.get('opacity', 1.0)
                opacity_percent = int(opacity_value * 100)
                self.danmaku_opacity_slider.setValue(opacity_percent)
                if hasattr(self, 'danmaku_opacity_label'):
                    self.danmaku_opacity_label.setText(f"{opacity_percent}%")

            if hasattr(self, 'danmaku_max_count_spin'):
                self.danmaku_max_count_spin.setValue(danmaku_config.get('max_count', 3))
            if hasattr(self, 'danmaku_y_offset_spin'):
                self.danmaku_y_offset_spin.setValue(danmaku_config.get('y_offset', 80))
            if hasattr(self, 'danmaku_color_mode_combo'):
                color_mode = danmaku_config.get('color_mode', 'auto')
                index = self.danmaku_color_mode_combo.findData(color_mode)
                if index >= 0:
                    self.danmaku_color_mode_combo.setCurrentIndex(index)

            # Update language combo box
            if hasattr(self, 'language_combo'):
                current_lang = self.config.get('language', 'zh_CN')
                index = self.language_combo.findData(current_lang)
                if index >= 0:
                    self.language_combo.setCurrentIndex(index)
        except Exception as e:
            logging.error(f"更新UI控件失败: {e}")
    
    def _init_timeline_editor(self, layout, placeholder):
        """延迟初始化时间轴编辑器"""
        try:
            # 设置全局 QToolTip 样式（与进度条悬停提示统一）
            QApplication.instance().setStyleSheet(
                QApplication.instance().styleSheet() + """
                QToolTip {
                    background-color: rgba(0, 0, 0, 180);
                    color: white;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 4px;
                    padding: 8px;
                    font-size: 12px;
                }
                """
            )

            # 创建时间轴编辑器
            self.timeline_editor = TimelineEditor()
            self.timeline_editor.task_time_changed.connect(self.on_timeline_task_changed)
            
            # 移除占位符，添加实际编辑器
            layout.removeWidget(placeholder)
            placeholder.deleteLater()
            layout.addWidget(self.timeline_editor)
            
            # 如果任务已加载，设置任务
            if hasattr(self, 'tasks') and self.tasks:
                QTimer.singleShot(50, lambda: self.timeline_editor.set_tasks(self.tasks) if self.timeline_editor else None)
            
            logging.info("时间轴编辑器初始化完成")
        except Exception as e:
            logging.error(f"初始化时间轴编辑器失败: {e}")
    
    def _init_theme_manager(self):
        """延迟初始化主题管理器(在后台运行,不阻塞UI)"""
        try:
            # 初始化主题管理器
            self.theme_manager = ThemeManager(self.app_dir)
            logging.info("主题管理器初始化完成")
        except Exception as e:
            logging.error(f"初始化主题管理器失败: {e}")

    def _init_template_manager(self):
        """延迟初始化模板管理器(在后台运行,不阻塞UI)"""
        try:
            from gaiya.core.template_manager import TemplateManager
            self.template_manager = TemplateManager(self.app_dir, logging.getLogger(__name__))
            logging.info("模板管理器初始化完成")

            # 如果模板UI已创建,刷新显示
            if hasattr(self, 'template_auto_apply_table'):
                self._load_template_auto_apply_settings()
        except Exception as e:
            logging.error(f"初始化模板管理器失败: {e}")



    def _init_schedule_manager(self):
        """延迟初始化时间表管理器"""
        try:
            from gaiya.core.schedule_manager import ScheduleManager
            self.schedule_manager = ScheduleManager(self.app_dir, logging.getLogger(__name__))
            logging.info("时间表管理器初始化完成")

            # 如果时间表UI已创建，刷新显示
            if hasattr(self, 'schedule_table'):
                self._load_schedule_table()
        except Exception as e:
            logging.error(f"初始化时间表管理器失败: {e}")

    def _load_schedule_table(self):
        """加载时间表规则到表格"""
        try:
            if not hasattr(self, 'schedule_manager') or not self.schedule_manager:
                logging.warning("ScheduleManager未初始化，延迟500ms后重试")
                QTimer.singleShot(500, self._load_schedule_table)
                return

            schedules = self.schedule_manager.get_all_schedules()
            self.schedule_table.setRowCount(len(schedules))

            # 获取模板名称映射
            template_names = {}
            if hasattr(self, 'template_manager') and self.template_manager:
                for template in self.template_manager.get_all_templates():
                    template_names[template['id']] = template['name']

            for row, schedule in enumerate(schedules):
                # 设置行高以适配36px按钮
                self.schedule_table.setRowHeight(row, 48)

                # 模板名称
                template_id = schedule.get('template_id', '')
                template_name = template_names.get(template_id, template_id)
                name_item = QTableWidgetItem(template_name)
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.schedule_table.setItem(row, 0, name_item)

                # 应用时间描述
                time_desc = self.schedule_manager._describe_schedule(schedule)
                time_item = QTableWidgetItem(time_desc)
                time_item.setFlags(time_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.schedule_table.setItem(row, 1, time_item)

                # 状态
                enabled = schedule.get('enabled', True)
                status_item = QTableWidgetItem("✅ 启用" if enabled else "❌ 禁用")
                status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.schedule_table.setItem(row, 2, status_item)

                # 操作按钮容器
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(4, 2, 4, 2)
                actions_layout.setSpacing(4)

                # 切换启用状态按钮
                toggle_btn = QPushButton("⏸️" if enabled else "▶️")
                toggle_btn.setToolTip(self.i18n.tr("account.message.disabled") if enabled else "启用")
                toggle_btn.setFixedSize(36, 36)
                toggle_btn.setStyleSheet("QPushButton { padding: 4px; font-size: 14px; }")
                # 使用 partial 避免 Lambda 循环引用
                toggle_btn.clicked.connect(partial(self._toggle_schedule, row))
                actions_layout.addWidget(toggle_btn)

                # 编辑按钮
                edit_btn = QPushButton("✏️")
                edit_btn.setToolTip(self.i18n.tr("button.edit"))
                edit_btn.setFixedSize(36, 36)
                edit_btn.setStyleSheet("QPushButton { padding: 4px; font-size: 14px; }")
                # 使用 partial 避免 Lambda 循环引用
                edit_btn.clicked.connect(partial(self._edit_schedule, row))
                actions_layout.addWidget(edit_btn)

                # 删除按钮
                delete_btn = QPushButton("🗑️")
                delete_btn.setToolTip(self.i18n.tr("button.delete"))
                delete_btn.setFixedSize(36, 36)
                delete_btn.setStyleSheet("QPushButton { padding: 4px; font-size: 14px; }")
                # 使用 partial 避免 Lambda 循环引用
                delete_btn.clicked.connect(partial(self._delete_schedule, row))
                actions_layout.addWidget(delete_btn)

                actions_layout.addStretch()

                self.schedule_table.setCellWidget(row, 3, actions_widget)

            logging.info(f"已加载 {len(schedules)} 条时间表规则")

        except Exception as e:
            logging.error(f"加载时间表规则失败: {e}")

    def _add_schedule_dialog(self):
        """打开添加时间表规则对话框"""
        # 首先检查是否已登录
        if not self._check_login_and_guide(tr('auth.features.template_auto_apply')):
            return

        try:
            if not hasattr(self, 'schedule_manager') or not self.schedule_manager:
                QMessageBox.warning(self, self.i18n.tr("message.warning"), "时间表管理器未初始化")
                return

            if not hasattr(self, 'template_manager') or not self.template_manager:
                QMessageBox.warning(self, self.i18n.tr("message.warning"), "模板管理器未初始化")
                return

            from PySide6.QtWidgets import (
                QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                QRadioButton, QButtonGroup, QCheckBox, QPushButton,
                QDateEdit, QSpinBox, QGroupBox
            )
            from datetime import date

            dialog = QDialog(self)
            dialog.setWindowTitle(self.i18n.tr("schedule.dialogs.add_rule"))
            dialog.setMinimumWidth(500)

            layout = QVBoxLayout()

            # 模板选择
            template_layout = QHBoxLayout()
            template_layout.addWidget(QLabel(self.i18n.tr("templates.auto_apply.select_template")))

            template_combo = QComboBox()
            template_combo.setStyleSheet(StyleManager.dropdown())
            templates = self.template_manager.get_all_templates()
            for template in templates:
                template_combo.addItem(template['name'], template['id'])
            template_layout.addWidget(template_combo)
            template_layout.addStretch()

            layout.addLayout(template_layout)

            # 规则类型选择
            type_group = QGroupBox("规则类型")
            type_layout = QVBoxLayout()

            rule_type_group = QButtonGroup()
            weekdays_radio = QRadioButton(self.i18n.tr("general.text_3012"))
            monthly_radio = QRadioButton(self.i18n.tr("general.text_4222"))
            specific_radio = QRadioButton(self.i18n.tr("general.text_7678"))

            rule_type_group.addButton(weekdays_radio, 1)
            rule_type_group.addButton(monthly_radio, 2)
            rule_type_group.addButton(specific_radio, 3)

            type_layout.addWidget(weekdays_radio)
            type_layout.addWidget(monthly_radio)
            type_layout.addWidget(specific_radio)

            type_group.setLayout(type_layout)
            layout.addWidget(type_group)

            # 星期选择（weekdays）
            weekdays_widget = QWidget()
            weekdays_layout = QHBoxLayout()
            weekdays_checks = {}
            for i, name in [(1, "周一"), (2, "周二"), (3, "周三"), (4, "周四"),
                           (5, "周五"), (6, "周六"), (7, "周日")]:
                check = QCheckBox(name)
                weekdays_checks[i] = check
                weekdays_layout.addWidget(check)
            weekdays_widget.setLayout(weekdays_layout)
            weekdays_widget.setVisible(False)

            # 每月日期选择（monthly）
            monthly_widget = QWidget()
            monthly_layout = QVBoxLayout()
            monthly_label = QLabel(self.i18n.tr("general.text_1240"))
            monthly_layout.addWidget(monthly_label)

            from PySide6.QtWidgets import QLineEdit
            monthly_input = QLineEdit()
            monthly_input.setPlaceholderText("1,15,28")
            monthly_layout.addWidget(monthly_input)

            monthly_widget.setLayout(monthly_layout)
            monthly_widget.setVisible(False)

            # 具体日期选择（specific_dates）
            specific_widget = QWidget()
            specific_layout = QVBoxLayout()
            specific_label = QLabel(self.i18n.tr("dialog.text_9512"))
            specific_layout.addWidget(specific_label)

            dates_list_widget = QWidget()
            dates_list_layout = QVBoxLayout()
            dates_list_layout.setContentsMargins(0, 0, 0, 0)
            dates_list_widget.setLayout(dates_list_layout)

            specific_layout.addWidget(dates_list_widget)

            add_date_layout = QHBoxLayout()
            date_picker = QDateEdit()
            date_picker.setCalendarPopup(True)
            date_picker.setDate(date.today())

            add_date_btn = QPushButton(self.i18n.tr("general.text_6594"))

            specific_dates = []

            def add_specific_date():
                selected_date = date_picker.date().toString("yyyy-MM-dd")
                if selected_date not in specific_dates:
                    specific_dates.append(selected_date)

                    # 创建日期标签和删除按钮
                    date_row = QWidget()
                    date_row_layout = QHBoxLayout()
                    date_row_layout.setContentsMargins(0, 2, 0, 2)

                    date_label = QLabel(selected_date)
                    date_row_layout.addWidget(date_label)

                    remove_btn = QPushButton("×")
                    remove_btn.setFixedSize(25, 25)
                    # 使用 partial 避免 Lambda 循环引用
                    remove_btn.clicked.connect(partial(remove_date, date_row, selected_date))
                    date_row_layout.addWidget(remove_btn)

                    date_row_layout.addStretch()

                    date_row.setLayout(date_row_layout)
                    dates_list_layout.addWidget(date_row)

            def remove_date(widget, date_str):
                widget.deleteLater()
                if date_str in specific_dates:
                    specific_dates.remove(date_str)

            add_date_btn.clicked.connect(add_specific_date)

            add_date_layout.addWidget(date_picker)
            add_date_layout.addWidget(add_date_btn)
            add_date_layout.addStretch()

            specific_layout.addLayout(add_date_layout)

            specific_widget.setLayout(specific_layout)
            specific_widget.setVisible(False)

            layout.addWidget(weekdays_widget)
            layout.addWidget(monthly_widget)
            layout.addWidget(specific_widget)

            # 规则类型切换
            def on_rule_type_changed():
                checked_id = rule_type_group.checkedId()
                weekdays_widget.setVisible(checked_id == 1)
                monthly_widget.setVisible(checked_id == 2)
                specific_widget.setVisible(checked_id == 3)

            weekdays_radio.toggled.connect(on_rule_type_changed)
            monthly_radio.toggled.connect(on_rule_type_changed)
            specific_radio.toggled.connect(on_rule_type_changed)

            weekdays_radio.setChecked(True)  # 默认选择星期

            # 按钮组
            button_layout = QHBoxLayout()
            button_layout.addStretch()

            cancel_btn = QPushButton(self.i18n.tr("button.cancel"))
            cancel_btn.clicked.connect(dialog.reject)
            button_layout.addWidget(cancel_btn)

            save_btn = QPushButton(self.i18n.tr("button.save"))
            save_btn.setStyleSheet(StyleManager.button_primary())
            save_btn.clicked.connect(dialog.accept)
            button_layout.addWidget(save_btn)

            layout.addLayout(button_layout)

            dialog.setLayout(layout)

            if dialog.exec() == QDialog.Accepted:
                # 获取选择的模板ID
                template_id = template_combo.currentData()

                # 根据规则类型保存
                checked_id = rule_type_group.checkedId()

                if checked_id == 1:  # 星期
                    weekdays = [i for i, check in weekdays_checks.items() if check.isChecked()]
                    if not weekdays:
                        QMessageBox.warning(self, self.i18n.tr("message.warning"), "请至少选择一个星期")
                        return

                    success = self.schedule_manager.add_schedule(
                        template_id=template_id,
                        schedule_type='weekdays',
                        weekdays=weekdays
                    )

                elif checked_id == 2:  # 每月
                    days_text = monthly_input.text().strip()
                    if not days_text:
                        QMessageBox.warning(self, self.i18n.tr("message.warning"), "请输入每月的日期")
                        return

                    try:
                        days_of_month = [int(d.strip()) for d in days_text.split(',')]
                        # 验证日期范围
                        if any(d < 1 or d > 31 for d in days_of_month):
                            QMessageBox.warning(self, self.i18n.tr("message.warning"), "日期必须在1-31之间")
                            return

                        success = self.schedule_manager.add_schedule(
                            template_id=template_id,
                            schedule_type='monthly',
                            days_of_month=days_of_month
                        )

                    except ValueError:
                        QMessageBox.warning(self, self.i18n.tr("message.warning"), "日期格式错误，请使用逗号分隔的数字")
                        return

                elif checked_id == 3:  # 具体日期
                    if not specific_dates:
                        QMessageBox.warning(self, self.i18n.tr("message.warning"), "请至少添加一个日期")
                        return

                    success = self.schedule_manager.add_schedule(
                        template_id=template_id,
                        schedule_type='specific_dates',
                        dates=specific_dates
                    )

                else:
                    QMessageBox.warning(self, self.i18n.tr("message.warning"), "请选择规则类型")
                    return

                if success:
                    QMessageBox.information(self, self.i18n.tr("message.success"), "时间表规则已添加")
                    self._load_schedule_table()  # 刷新表格
                else:
                    QMessageBox.warning(self, self.i18n.tr("general.text_5397"), "该规则与现有规则冲突，请检查")

        except Exception as e:
            logging.error(f"添加时间表规则失败: {e}")
            QMessageBox.critical(self, self.i18n.tr("membership.payment.error"), f"添加规则失败:\n{str(e)}")

    def _edit_schedule(self, row):
        """编辑时间表规则"""
        # 首先检查是否已登录
        if not self._check_login_and_guide(tr('auth.features.template_auto_apply')):
            return

        try:
            if not hasattr(self, 'schedule_manager') or not self.schedule_manager:
                QMessageBox.warning(self, self.i18n.tr("message.warning"), "时间表管理器未初始化")
                return

            if not hasattr(self, 'template_manager') or not self.template_manager:
                QMessageBox.warning(self, self.i18n.tr("message.warning"), "模板管理器未初始化")
                return

            # 获取当前规则
            schedules = self.schedule_manager.get_all_schedules()
            if row < 0 or row >= len(schedules):
                QMessageBox.warning(self, self.i18n.tr("message.warning"), "无效的规则索引")
                return

            current_schedule = schedules[row]

            from PySide6.QtWidgets import (
                QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                QRadioButton, QButtonGroup, QCheckBox, QPushButton,
                QDateEdit, QSpinBox, QGroupBox, QLineEdit
            )
            from datetime import date, datetime

            dialog = QDialog(self)
            dialog.setWindowTitle(self.i18n.tr("schedule.dialogs.edit_rule"))
            dialog.setMinimumWidth(500)

            layout = QVBoxLayout()

            # 模板选择
            template_layout = QHBoxLayout()
            template_layout.addWidget(QLabel(self.i18n.tr("templates.auto_apply.select_template")))

            template_combo = QComboBox()
            template_combo.setStyleSheet(StyleManager.dropdown())
            templates = self.template_manager.get_all_templates()
            current_template_id = current_schedule.get('template_id', '')

            for i, template in enumerate(templates):
                template_combo.addItem(template['name'], template['id'])
                if template['id'] == current_template_id:
                    template_combo.setCurrentIndex(i)

            template_layout.addWidget(template_combo)
            template_layout.addStretch()

            layout.addLayout(template_layout)

            # 规则类型选择
            type_group = QGroupBox("规则类型")
            type_layout = QVBoxLayout()

            rule_type_group = QButtonGroup()
            weekdays_radio = QRadioButton(self.i18n.tr("general.text_3012"))
            monthly_radio = QRadioButton(self.i18n.tr("general.text_4222"))
            specific_radio = QRadioButton(self.i18n.tr("general.text_7678"))

            rule_type_group.addButton(weekdays_radio, 1)
            rule_type_group.addButton(monthly_radio, 2)
            rule_type_group.addButton(specific_radio, 3)

            type_layout.addWidget(weekdays_radio)
            type_layout.addWidget(monthly_radio)
            type_layout.addWidget(specific_radio)

            type_group.setLayout(type_layout)
            layout.addWidget(type_group)

            # 星期选择（weekdays）
            weekdays_widget = QWidget()
            weekdays_layout = QHBoxLayout()
            weekdays_checks = {}
            for i, name in [(1, "周一"), (2, "周二"), (3, "周三"), (4, "周四"),
                           (5, "周五"), (6, "周六"), (7, "周日")]:
                check = QCheckBox(name)
                weekdays_checks[i] = check
                weekdays_layout.addWidget(check)
            weekdays_widget.setLayout(weekdays_layout)
            weekdays_widget.setVisible(False)

            # 每月日期选择（monthly）
            monthly_widget = QWidget()
            monthly_layout = QVBoxLayout()
            monthly_label = QLabel(self.i18n.tr("general.text_1240"))
            monthly_layout.addWidget(monthly_label)

            from PySide6.QtWidgets import QLineEdit
            monthly_input = QLineEdit()
            monthly_input.setPlaceholderText("1,15,28")
            monthly_layout.addWidget(monthly_input)

            monthly_widget.setLayout(monthly_layout)
            monthly_widget.setVisible(False)

            # 具体日期选择（specific_dates）
            specific_widget = QWidget()
            specific_layout = QVBoxLayout()
            specific_label = QLabel(self.i18n.tr("dialog.text_9512"))
            specific_layout.addWidget(specific_label)

            dates_list_widget = QWidget()
            dates_list_layout = QVBoxLayout()
            dates_list_layout.setContentsMargins(0, 0, 0, 0)
            dates_list_widget.setLayout(dates_list_layout)

            specific_layout.addWidget(dates_list_widget)

            add_date_layout = QHBoxLayout()
            date_picker = QDateEdit()
            date_picker.setCalendarPopup(True)
            date_picker.setDate(date.today())

            add_date_btn = QPushButton(self.i18n.tr("general.text_6594"))

            specific_dates = []

            def add_specific_date():
                selected_date = date_picker.date().toString("yyyy-MM-dd")
                if selected_date not in specific_dates:
                    specific_dates.append(selected_date)

                    # 创建日期标签和删除按钮
                    date_row = QWidget()
                    date_row_layout = QHBoxLayout()
                    date_row_layout.setContentsMargins(0, 2, 0, 2)

                    date_label = QLabel(selected_date)
                    date_row_layout.addWidget(date_label)

                    remove_btn = QPushButton("×")
                    remove_btn.setFixedSize(25, 25)
                    # 使用 partial 避免 Lambda 循环引用
                    remove_btn.clicked.connect(partial(remove_date, date_row, selected_date))
                    date_row_layout.addWidget(remove_btn)

                    date_row_layout.addStretch()

                    date_row.setLayout(date_row_layout)
                    dates_list_layout.addWidget(date_row)

            def remove_date(widget, date_str):
                widget.deleteLater()
                if date_str in specific_dates:
                    specific_dates.remove(date_str)

            add_date_btn.clicked.connect(add_specific_date)

            add_date_layout.addWidget(date_picker)
            add_date_layout.addWidget(add_date_btn)
            add_date_layout.addStretch()

            specific_layout.addLayout(add_date_layout)

            specific_widget.setLayout(specific_layout)
            specific_widget.setVisible(False)

            layout.addWidget(weekdays_widget)
            layout.addWidget(monthly_widget)
            layout.addWidget(specific_widget)

            # 预填充现有规则数据
            schedule_type = current_schedule.get('schedule_type', '')

            if schedule_type == 'weekdays':
                weekdays_radio.setChecked(True)
                for day in current_schedule.get('weekdays', []):
                    if day in weekdays_checks:
                        weekdays_checks[day].setChecked(True)
            elif schedule_type == 'monthly':
                monthly_radio.setChecked(True)
                days = current_schedule.get('days_of_month', [])
                monthly_input.setText(','.join(map(str, days)))
            elif schedule_type == 'specific_dates':
                specific_radio.setChecked(True)
                for date_str in current_schedule.get('dates', []):
                    specific_dates.append(date_str)
                    # 创建日期标签和删除按钮
                    date_row = QWidget()
                    date_row_layout = QHBoxLayout()
                    date_row_layout.setContentsMargins(0, 2, 0, 2)

                    date_label = QLabel(date_str)
                    date_row_layout.addWidget(date_label)

                    remove_btn = QPushButton("×")
                    remove_btn.setFixedSize(25, 25)
                    # 使用 partial 避免 Lambda 循环引用
                    remove_btn.clicked.connect(partial(remove_date, date_row, date_str))
                    date_row_layout.addWidget(remove_btn)

                    date_row_layout.addStretch()

                    date_row.setLayout(date_row_layout)
                    dates_list_layout.addWidget(date_row)

            # 规则类型切换
            def on_rule_type_changed():
                checked_id = rule_type_group.checkedId()
                weekdays_widget.setVisible(checked_id == 1)
                monthly_widget.setVisible(checked_id == 2)
                specific_widget.setVisible(checked_id == 3)

            weekdays_radio.toggled.connect(on_rule_type_changed)
            monthly_radio.toggled.connect(on_rule_type_changed)
            specific_radio.toggled.connect(on_rule_type_changed)

            # 触发一次以显示正确的widget
            on_rule_type_changed()

            # 按钮组
            button_layout = QHBoxLayout()
            button_layout.addStretch()

            cancel_btn = QPushButton(self.i18n.tr("button.cancel"))
            cancel_btn.clicked.connect(dialog.reject)
            button_layout.addWidget(cancel_btn)

            save_btn = QPushButton(self.i18n.tr("button.save"))
            save_btn.setStyleSheet(StyleManager.button_primary())
            save_btn.clicked.connect(dialog.accept)
            button_layout.addWidget(save_btn)

            layout.addLayout(button_layout)

            dialog.setLayout(layout)

            if dialog.exec() == QDialog.Accepted:
                # 获取选择的模板ID
                template_id = template_combo.currentData()

                # 根据规则类型保存
                checked_id = rule_type_group.checkedId()

                update_data = {'template_id': template_id}

                if checked_id == 1:  # 星期
                    weekdays = [i for i, check in weekdays_checks.items() if check.isChecked()]
                    if not weekdays:
                        QMessageBox.warning(self, self.i18n.tr("message.warning"), "请至少选择一个星期")
                        return

                    update_data['schedule_type'] = 'weekdays'
                    update_data['weekdays'] = weekdays

                elif checked_id == 2:  # 每月
                    days_text = monthly_input.text().strip()
                    if not days_text:
                        QMessageBox.warning(self, self.i18n.tr("message.warning"), "请输入每月的日期")
                        return

                    try:
                        days_of_month = [int(d.strip()) for d in days_text.split(',')]
                        # 验证日期范围
                        if any(d < 1 or d > 31 for d in days_of_month):
                            QMessageBox.warning(self, self.i18n.tr("message.warning"), "日期必须在1-31之间")
                            return

                        update_data['schedule_type'] = 'monthly'
                        update_data['days_of_month'] = days_of_month

                    except ValueError:
                        QMessageBox.warning(self, self.i18n.tr("message.warning"), "日期格式错误，请使用逗号分隔的数字")
                        return

                elif checked_id == 3:  # 具体日期
                    if not specific_dates:
                        QMessageBox.warning(self, self.i18n.tr("message.warning"), "请至少添加一个日期")
                        return

                    update_data['schedule_type'] = 'specific_dates'
                    update_data['dates'] = specific_dates

                else:
                    QMessageBox.warning(self, self.i18n.tr("message.warning"), "请选择规则类型")
                    return

                success = self.schedule_manager.update_schedule(row, **update_data)

                if success:
                    QMessageBox.information(self, self.i18n.tr("message.success"), "时间表规则已更新")
                    self._load_schedule_table()  # 刷新表格
                else:
                    QMessageBox.warning(self, self.i18n.tr("message.text_8834"), "更新规则失败，请检查")

        except Exception as e:
            logging.error(f"编辑时间表规则失败: {e}")
            QMessageBox.critical(self, self.i18n.tr("membership.payment.error"), f"编辑规则失败:\n{str(e)}")

    def _toggle_schedule(self, row):
        """切换时间表规则的启用状态"""
        # 首先检查是否已登录
        if not self._check_login_and_guide(tr('auth.features.template_auto_apply')):
            return

        try:
            success = self.schedule_manager.toggle_schedule(row)
            if success:
                self._load_schedule_table()  # 刷新表格
        except Exception as e:
            logging.error(f"切换规则状态失败: {e}")
            QMessageBox.critical(self, self.i18n.tr("membership.payment.error"), f"操作失败:\n{str(e)}")

    def _delete_schedule(self, row):
        """删除时间表规则"""
        # 首先检查是否已登录
        if not self._check_login_and_guide(tr('auth.features.template_auto_apply')):
            return

        try:
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self,
                "确认删除",
                "确定要删除这条规则吗?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                success = self.schedule_manager.remove_schedule(row)
                if success:
                    self._load_schedule_table()  # 刷新表格
                    QMessageBox.information(self, self.i18n.tr("message.success"), "规则已删除")

        except Exception as e:
            logging.error(f"删除规则失败: {e}")
            QMessageBox.critical(self, self.i18n.tr("membership.payment.error"), f"删除失败:\n{str(e)}")

    def _test_date_matching(self):
        """测试指定日期会匹配到哪个模板"""
        try:
            if not hasattr(self, 'schedule_manager') or not self.schedule_manager:
                QMessageBox.warning(self, self.i18n.tr("message.warning"), "时间表管理器未初始化")
                return

            from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDateEdit, QPushButton, QTextEdit
            from datetime import datetime

            dialog = QDialog(self)
            dialog.setWindowTitle(self.i18n.tr("general.text_4326"))
            dialog.setMinimumWidth(500)
            dialog.setMinimumHeight(350)

            layout = QVBoxLayout()

            # 说明
            hint_label = QLabel(self.i18n.tr("templates.auto_apply.test_instruction"))
            hint_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
            layout.addWidget(hint_label)

            # 日期选择器
            date_edit = QDateEdit()
            date_edit.setCalendarPopup(True)
            date_edit.setDate(datetime.now().date())
            date_edit.setDisplayFormat("yyyy-MM-dd")
            layout.addWidget(date_edit)

            # 结果显示区域
            result_text = QTextEdit()
            result_text.setReadOnly(True)
            result_text.setMinimumHeight(150)
            layout.addWidget(result_text)

            def perform_test():
                selected_date = date_edit.date().toPython()

                # 获取匹配的模板
                matched_template_id = self.schedule_manager.get_template_for_date(selected_date)

                # 获取该日期的所有冲突模板
                all_matched = self.schedule_manager.get_conflicts_for_date(selected_date)

                # 构建结果文本
                result_lines = []
                result_lines.append(self.i18n.tr("config.schedule.test_date_display", test_date=selected_date.strftime('%Y-%m-%d %A')))
                result_lines.append("")

                if matched_template_id:
                    # 获取模板名称
                    template_name = matched_template_id
                    if hasattr(self, 'template_manager') and self.template_manager:
                        template = self.template_manager.get_template_by_id(matched_template_id)
                        if template:
                            template_name = template['name']

                    result_lines.append(self.i18n.tr("config.schedule.date_will_load_template", template_name=template_name))
                    result_lines.append("")

                    if len(all_matched) > 1:
                        result_lines.append(self.i18n.tr("config.schedule.date_conflict_warning", conflict_count=len(all_matched)))
                        result_lines.append("冲突的模板：")
                        for tid in all_matched:
                            tname = tid
                            if hasattr(self, 'template_manager') and self.template_manager:
                                t = self.template_manager.get_template_by_id(tid)
                                if t:
                                    tname = t['name']
                            result_lines.append(f"  - {tname}")
                        result_lines.append("")
                        result_lines.append("建议：删除或禁用其中某些规则，避免冲突")

                else:
                    result_lines.append("❌ 该日期没有匹配到任何模板规则")
                    result_lines.append("")
                    result_lines.append("将使用默认24小时模板")

                result_text.setText("\n".join(result_lines))

            # 测试按钮
            test_btn = QPushButton(self.i18n.tr("general.text_8461"))
            test_btn.setStyleSheet(StyleManager.button_minimal())
            test_btn.clicked.connect(perform_test)
            layout.addWidget(test_btn)

            # 关闭按钮
            close_btn = QPushButton(self.i18n.tr("button.close"))
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)

            dialog.setLayout(layout)

            # 初始执行一次测试
            perform_test()

            dialog.exec()

        except Exception as e:
            logging.error(f"测试日期匹配失败: {e}")
            QMessageBox.critical(self, self.i18n.tr("membership.payment.error"), f"测试失败:\n{str(e)}")

    def _init_ai_components(self):
        """延迟初始化AI相关组件(在后台运行,不阻塞UI)"""
        try:
            # ✅ Fix: Initialize AuthClient in background thread to avoid UI blocking
            from gaiya.core.auth_client import AuthClient
            self.auth_client = AuthClient()
            logging.info("AuthClient initialized successfully in background")

            # ✅ P1-1.5: 关键修复 - 初始化AI客户端时直接使用正确的user_id和tier
            if self.auth_client.is_logged_in():
                user_id = self.auth_client.get_user_id() or "user_demo"
                user_tier = self.auth_client.get_user_tier()
                logging.info(f"[AI Client] 使用已登录用户信息初始化: tier={user_tier}, user_id={user_id}")
            else:
                user_id = "user_demo"
                user_tier = "free"
                logging.info("[AI Client] 用户未登录,使用默认配置: tier=free, user_id=user_demo")

            # 初始化AI客户端（使用正确的user_id）
            self.ai_client = GaiyaAIClient(user_id=user_id)
            # 设置正确的tier
            self.ai_client.set_user_tier(user_tier)

            # 注意：使用代理服务器模式时，不需要启动本地后端服务
            # BackendManager仅用于向后兼容（如果用户需要本地模式）
            # 使用代理服务器时，不需要BackendManager

            # 初始化AI主题助手
            self.theme_ai_helper = ThemeAIHelper(self.ai_client)

            # 启动定时器持续更新AI状态（仅在标签页可见时检查）
            self.ai_status_timer = QTimer()
            self.ai_status_timer.timeout.connect(self._update_ai_status_async)
            # 延迟启动，避免初始化时立即检查
            QTimer.singleShot(1000, lambda: self._start_ai_status_timer_if_needed())

            # 初始化后端管理器（仅用于向后兼容，代理模式下不启动本地服务）
            # 获取根logger，它应该已经配置了文件处理器
            root_logger = logging.getLogger()
            # 如果根logger没有文件处理器，添加一个（指向gaiya.log）
            if not any(isinstance(h, logging.FileHandler) for h in root_logger.handlers):
                # 获取应用目录（支持打包后的环境）
                if getattr(sys, 'frozen', False):
                    app_dir = Path(sys.executable).parent
                else:
                    app_dir = Path(__file__).parent
                log_file = app_dir / "gaiya.log"
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setLevel(logging.INFO)
                file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
                root_logger.addHandler(file_handler)
            
            # 已切换到Vercel云服务，不再需要本地BackendManager
            # self.backend_manager = BackendManager(root_logger)
            self.backend_manager = None  # 标记为None，避免后续引用报错

            # 初次更新UI状态（异步）
            QTimer.singleShot(500, self._update_ai_status_async)

        except Exception as e:
            logging.error(f"初始化AI组件失败: {e}")
            # 如果初始化失败,确保显示错误状态
            self._update_ai_status_error(str(e))

    def _start_ai_status_timer_if_needed(self):
        """如果需要，启动AI状态定时器（仅在任务管理标签页可见时）"""
        if not hasattr(self, 'tabs'):
            return
        
        # 仅在任务管理标签页（索引1）可见时启动定时器
        if self.tabs.currentIndex() == 1:  # 任务管理标签页
            if hasattr(self, 'ai_status_timer') and self.ai_status_timer:
                if not self.ai_status_timer.isActive():
                    self.ai_status_timer.start(300000)  # 5分钟检查一次,大幅减少API调用频率(从162次/6小时降至~3次/6小时)
        else:
            # 如果不在任务管理标签页，停止定时器
            if hasattr(self, 'ai_status_timer') and self.ai_status_timer:
                if self.ai_status_timer.isActive():
                    self.ai_status_timer.stop()
    
    def _update_ai_status_async(self):
        """异步更新AI服务状态显示（不阻塞UI）"""
        # 检查是否有配额标签(在任务规划标签页)
        if not hasattr(self, 'quota_label'):
            return

        # 检查AI客户端是否已初始化
        if not hasattr(self, 'ai_client') or not self.ai_client:
            self.quota_label.setText(self.i18n.tr("ai.text_9372"))
            self.quota_label.setStyleSheet("color: #ff9800; padding: 5px; font-weight: bold;")
            if hasattr(self, 'generate_btn'):
                self.generate_btn.setEnabled(False)
            return

        # 使用异步方式检查后端服务器状态
        self._check_backend_health_async()

    def _check_backend_health_async(self):
        """异步检查后端服务器健康状态"""
        class HealthCheckWorker(QThread):
            finished = Signal(bool)

            def __init__(self, backend_url):
                super().__init__()
                self.backend_url = backend_url

            def run(self):
                try:
                    # Vercel冷启动可能需要10-15秒，增加超时时间
                    response = requests.get(f"{self.backend_url}/api/health", timeout=15)
                    self.finished.emit(response.status_code == 200)
                except Exception as e:
                    logging.warning(f"健康检查失败: {str(e)}")
                    self.finished.emit(False)

        # 创建并启动工作线程
        worker = HealthCheckWorker(self.ai_client.backend_url)

        # 使用lambda包装回调，确保worker在完成后被清理
        def on_finished(is_healthy):
            self._on_health_check_finished(is_healthy)
            # 断开信号连接
            worker.finished.disconnect()
            # 延迟删除worker对象
            worker.deleteLater()

        worker.finished.connect(on_finished)
        worker.start()
    
    def _on_health_check_finished(self, is_healthy):
        """后端健康检查完成回调"""
        if not hasattr(self, 'quota_label'):
            return

        # Always try to refresh quota, even if health check fails
        # The quota API might be ready even if health endpoint is not
        self.refresh_quota_status_async()

        # Note: Timer will be stopped in _on_quota_status_finished if quota check succeeds

    def _update_ai_status_error(self, error_msg):
        """显示AI服务错误状态"""
        if hasattr(self, 'quota_label'):
            self.quota_label.setText(self.i18n.tr("ai.text_857"))
            self.quota_label.setStyleSheet("color: #f44336; padding: 5px; font-weight: bold;")
            logging.error(f"AI服务错误: {error_msg}")
        if hasattr(self, 'generate_btn'):
            self.generate_btn.setEnabled(False)

    def get_resource_path(self, relative_path: str) -> Path:
        """Get absolute path to bundled resource file

        Args:
            relative_path: Resource file path relative to app root

        Returns:
            Path: Absolute path to resource file
        """
        return path_utils.get_resource_path(relative_path)

    def init_ui(self) -> None:
        """Initialize main window UI components"""
        self.setWindowTitle(self.i18n.tr("config.config_2", VERSION_STRING=VERSION_STRING, VERSION_STRING_ZH=VERSION_STRING_ZH))

        # 设置窗口图标
        icon_path = self.get_resource_path('gaiya-logo2-wbk.png')
        if os.path.exists(icon_path):
            from PySide6.QtGui import QIcon
            self.setWindowIcon(QIcon(str(icon_path)))

        self.setFixedSize(1000, 900)  # 固定窗口大小，防止拉伸导致控件变形

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        layout = QVBoxLayout(central_widget)

        # 添加AI功能横幅 (可关闭)
        try:
            from gaiya.ui.components import AiFeatureBanner
            self.ai_banner = AiFeatureBanner(self)
            self.ai_banner.ai_generate_clicked.connect(self.on_banner_ai_clicked)
            self.ai_banner.learn_more_clicked.connect(self.on_banner_learn_more)
            self.ai_banner.close_clicked.connect(self.on_banner_closed)

            # 检查是否已关闭横幅(从配置读取)
            banner_closed = self.config.get('ai_banner_closed', False)
            if banner_closed:
                self.ai_banner.hide()
                logging.info("AI功能横幅已隐藏(用户之前关闭)")
            else:
                logging.info("AI功能横幅已显示")

            layout.addWidget(self.ai_banner)
        except Exception as e:
            logging.error(f"加载AI功能横幅失败: {type(e).__name__}: {e}", exc_info=True)
            # 如果横幅加载失败,继续加载其他UI

        # 创建标签页(使用懒加载,只在切换到标签页时才创建内容)
        tabs = QTabWidget()

        # 自定义Tab样式：总高度40px
        tabs.setStyleSheet("""
            QTabBar::tab {
                padding: 8px 15px;            /* 上下8px, 左右15px */
                font-size: 13px;               /* 字体适中 */
                min-height: 22px;              /* 内容高度22px，总高度≈40px (22+8+8+2边框) */
                border: 1px solid #e0e0e0;
                border-bottom: none;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                background-color: #f5f5f5;
                color: #666;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #333;
                border-bottom: 2px solid white;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #eeeeee;
            }
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
            }
        """)

        # 立即创建外观配置和任务管理标签页(基础功能)
        tabs.addTab(self.create_config_tab(), "🎨 " + self.i18n.tr("config.tabs.appearance"))
        tabs.addTab(self.create_tasks_tab(), "📋 " + self.i18n.tr("config.tabs.tasks"))

        # 延迟创建场景设置标签页
        self.scene_tab_widget = None
        tabs.addTab(QWidget(), "🎬 " + self.i18n.tr("config.tabs.scene"))  # 占位widget

        # 延迟创建通知设置标签页(避免初始化时阻塞)
        self.notification_tab_widget = None
        tabs.addTab(QWidget(), "🔔 " + self.i18n.tr("config.tabs.notifications"))  # 占位widget

        # 延迟创建行为识别标签页
        self.behavior_tab_widget = None
        tabs.addTab(QWidget(), "🔍 行为识别")  # 占位widget

        # 延迟创建个人中心标签页
        self.account_tab_widget = None
        tabs.addTab(QWidget(), tr("account.tab_title"))  # 占位widget

        # 延迟创建关于标签页
        self.about_tab_widget = None
        tabs.addTab(QWidget(), "📖 " + self.i18n.tr("config.tabs.about"))  # 占位widget

        # 连接标签页切换信号,实现懒加载
        tabs.currentChanged.connect(self.on_tab_changed)
        # 连接标签页切换信号,控制AI状态定时器
        tabs.currentChanged.connect(self._on_tab_changed_for_ai_status)
        self.tabs = tabs  # 保存引用

        layout.addWidget(tabs)

        # 底部按钮
        button_layout = QHBoxLayout()

        save_btn = QPushButton(self.i18n.tr("config.settings_2"))
        save_btn.clicked.connect(self.save_all)
        save_btn.setFixedHeight(36)
        save_btn.setStyleSheet(StyleManager.button_primary())

        cancel_btn = QPushButton(self.i18n.tr("button.cancel"))
        cancel_btn.clicked.connect(self.close)
        cancel_btn.setFixedHeight(36)
        cancel_btn.setStyleSheet("QPushButton { padding: 8px 20px; border-radius: 4px; }")

        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        # 保存按钮引用，用于在不同标签页控制显示/隐藏
        self.save_btn = save_btn
        self.cancel_btn = cancel_btn

    def on_tab_changed(self, index: int) -> None:
        """Handle tab change event with lazy loading

        Args:
            index: Tab index that was switched to
        """
        # 控制底部按钮的显示/隐藏
        # 在"个人中心"(5)和"关于"(6)页面隐藏按钮
        if index in [5, 6]:  # 个人中心或关于页面
            self.save_btn.hide()
            self.cancel_btn.hide()
        else:  # 其他页面显示按钮
            self.save_btn.show()
            self.cancel_btn.show()

        # 懒加载各标签页
        if index == 2:  # 场景设置标签页
            if self.scene_tab_widget is None:
                self._load_scene_tab()
        elif index == 3:  # 通知设置标签页
            if self.notification_tab_widget is None:
                self._load_notification_tab()
        elif index == 4:  # 行为识别标签页
            if self.behavior_tab_widget is None:
                self._load_behavior_tab()
        elif index == 5:  # 个人中心标签页
            if self.account_tab_widget is None:
                self._load_account_tab()
        elif index == 6:  # 关于标签页
            if self.about_tab_widget is None:
                self._load_about_tab()

    def _load_scene_tab(self):
        """加载场景设置标签页"""
        if self.scene_tab_widget is not None:
            return  # 已经加载过了

        try:
            # Block signals to prevent recursive tab change events
            self.tabs.blockSignals(True)

            self.scene_tab_widget = self.create_scene_tab()
            self.tabs.setTabEnabled(2, True)  # 确保标签页可用
            # 替换占位widget
            self.tabs.removeTab(2)
            self.tabs.insertTab(2, self.scene_tab_widget, "🎬 " + self.i18n.tr("config.tabs.scene"))
            self.tabs.setCurrentIndex(2)  # 切换到场景设置标签页

            # Restore signals
            self.tabs.blockSignals(False)
        except Exception as e:
            logging.error(f"加载场景设置标签页失败: {e}")
            # Ensure signals are restored even on error
            self.tabs.blockSignals(False)
            # 显示错误提示
            from PySide6.QtWidgets import QLabel
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_label = QLabel(self.i18n.tr("config.settings_4"))
            error_label.setStyleSheet("color: red; padding: 20px;")
            error_layout.addWidget(error_label)
            self.scene_tab_widget = error_widget
            self.tabs.removeTab(2)
            self.tabs.insertTab(2, self.scene_tab_widget, "🎬 " + self.i18n.tr("config.tabs.scene"))

    def _load_notification_tab(self):
        """加载通知设置标签页"""
        if self.notification_tab_widget is not None:
            return  # 已经加载过了

        try:
            # Block signals to prevent recursive tab change events
            self.tabs.blockSignals(True)

            self.notification_tab_widget = self.create_notification_tab()
            self.tabs.setTabEnabled(3, True)  # 确保标签页可用
            # 替换占位widget
            self.tabs.removeTab(3)
            self.tabs.insertTab(3, self.notification_tab_widget, "🔔 " + self.i18n.tr("config.tabs.notifications"))
            self.tabs.setCurrentIndex(3)  # 切换到通知设置标签页

            # Restore signals
            self.tabs.blockSignals(False)
        except Exception as e:
            logging.error(f"加载通知设置标签页失败: {e}")
            # Ensure signals are restored even on error
            self.tabs.blockSignals(False)
            # 显示错误提示
            from PySide6.QtWidgets import QLabel
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_label = QLabel(self.i18n.tr("config.settings_6"))
            error_label.setStyleSheet("color: red; padding: 20px;")
            error_layout.addWidget(error_label)
            self.notification_tab_widget = error_widget
            self.tabs.removeTab(3)
            self.tabs.insertTab(3, self.notification_tab_widget, "🔔 " + self.i18n.tr("config.tabs.notifications"))

    def _load_behavior_tab(self):
        """加载行为识别标签页"""
        if self.behavior_tab_widget is not None:
            return  # 已经加载过了

        try:
            # Block signals to prevent recursive tab change events
            self.tabs.blockSignals(True)

            self.behavior_tab_widget = self.create_behavior_tab()
            self.tabs.setTabEnabled(4, True)  # 确保标签页可用
            # 替换占位widget
            self.tabs.removeTab(4)
            self.tabs.insertTab(4, self.behavior_tab_widget, "🔍 行为识别")
            self.tabs.setCurrentIndex(4)  # 切换到行为识别标签页

            # 启动统计信息实时更新定时器 (每5秒更新一次)
            if self.behavior_stats_timer is None:
                self.behavior_stats_timer = QTimer(self)
                self.behavior_stats_timer.timeout.connect(self.update_behavior_stats)
                self.behavior_stats_timer.start(5000)  # 5秒间隔
                logging.info("行为识别统计信息定时器已启动 (5秒/次)")

            # Restore signals
            self.tabs.blockSignals(False)
        except Exception as e:
            logging.error(f"加载行为识别标签页失败: {e}")
            # Ensure signals are restored even on error
            self.tabs.blockSignals(False)
            # 显示错误提示
            from PySide6.QtWidgets import QLabel
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_label = QLabel("加载行为识别设置失败，请查看日志")
            error_label.setStyleSheet("color: red; padding: 20px;")
            error_layout.addWidget(error_label)
            self.behavior_tab_widget = error_widget
            self.tabs.removeTab(4)
            self.tabs.insertTab(4, self.behavior_tab_widget, "🔍 行为识别")


    def _load_account_tab(self):
        """加载个人中心标签页"""
        import logging
        logging.info(f"[_load_account_tab] 被调用, account_tab_widget={self.account_tab_widget}")

        if self.account_tab_widget is not None:
            logging.info("[_load_account_tab] account_tab_widget不为None,跳过重新加载")
            return  # 已经加载过了

        logging.info("[_load_account_tab] 开始创建新的account_tab")
        try:
            # Block signals to prevent recursive tab change events
            self.tabs.blockSignals(True)

            self.account_tab_widget = self._create_account_tab()
            logging.info(f"[_load_account_tab] 创建account_tab完成, 开始替换tab")
            self.tabs.setTabEnabled(5, True)  # 确保标签页可用
            # 替换占位widget
            self.tabs.removeTab(5)
            self.tabs.insertTab(5, self.account_tab_widget, tr("account.tab_title"))
            self.tabs.setCurrentIndex(5)  # 切换到个人中心标签页
            logging.info(f"[_load_account_tab] tab替换完成, 当前tab index={self.tabs.currentIndex()}")

            # Restore signals
            self.tabs.blockSignals(False)
        except Exception as e:
            import logging
            import traceback
            logging.error(f"加载个人中心标签页失败: {e}")
            traceback.print_exc()
            # Ensure signals are restored even on error
            self.tabs.blockSignals(False)
            from PySide6.QtWidgets import QLabel
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_label = QLabel(self.i18n.tr("message.text_347"))
            error_label.setStyleSheet("color: red; padding: 20px;")
            error_layout.addWidget(error_label)
            self.account_tab_widget = error_widget
            self.tabs.removeTab(5)
            self.tabs.insertTab(5, self.account_tab_widget, tr("account.tab_title"))

    def _load_about_tab(self):
        """加载关于标签页"""
        if self.about_tab_widget is not None:
            return  # 已经加载过了

        try:
            # Block signals to prevent recursive tab change events
            self.tabs.blockSignals(True)

            self.about_tab_widget = self.create_about_tab()
            self.tabs.setTabEnabled(6, True)  # 确保标签页可用
            # 替换占位widget
            self.tabs.removeTab(6)
            self.tabs.insertTab(6, self.about_tab_widget, "📖 " + self.i18n.tr("tabs.about"))
            self.tabs.setCurrentIndex(6)  # 切换到关于标签页

            # Restore signals
            self.tabs.blockSignals(False)
        except Exception as e:
            import logging
            import traceback
            logging.error(f"加载关于标签页失败: {e}")
            logging.error(traceback.format_exc())
            # Ensure signals are restored even on error
            self.tabs.blockSignals(False)
            from PySide6.QtWidgets import QLabel
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_label = QLabel(self.i18n.tr("message.text_9945"))
            error_label.setStyleSheet("color: red; padding: 20px;")
            error_layout.addWidget(error_label)
            self.about_tab_widget = error_widget
            self.tabs.removeTab(6)
            self.tabs.insertTab(6, self.about_tab_widget, "📖 " + self.i18n.tr("tabs.about"))
            self.tabs.setCurrentIndex(6)  # 确保切换到关于标签页显示错误信息

    def create_config_tab(self):
        """创建外观配置标签页"""
        # 创建滚动区域容器
        from PySide6.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 创建内容widget
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 基本设置组
        basic_group = QGroupBox(tr("appearance.basic_settings"))
        basic_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        basic_layout = QFormLayout()
        basic_layout.setVerticalSpacing(12)
        basic_layout.setHorizontalSpacing(10)

        # 进度条高度 - 预设档位 + 自定义
        height_container = QWidget()
        height_layout = QHBoxLayout(height_container)
        height_layout.setContentsMargins(0, 0, 0, 0)

        # 预设档位按钮组
        self.height_preset_group = QWidget()
        height_preset_layout = QHBoxLayout(self.height_preset_group)
        height_preset_layout.setContentsMargins(0, 0, 0, 0)
        height_preset_layout.setSpacing(5)

        # 预设高度选项 - 精简为4个档位
        self.height_presets = [
            ("config.presets.height_extra_thin", 6),
            ("config.presets.height_thin", 10),
            ("config.presets.height_standard", 20),
            ("config.presets.height_thick", 30)
        ]

        self.height_preset_buttons = []
        for name_key, height in self.height_presets:
            name = self.i18n.tr(name_key)
            btn = QPushButton(f"{name} ({height}px)")
            btn.setCheckable(True)
            btn.setMaximumWidth(100)
            # 使用 partial 避免 Lambda 循环引用
            btn.clicked.connect(partial(self.set_height_preset, height))
            height_preset_layout.addWidget(btn)
            self.height_preset_buttons.append((btn, height))

        height_layout.addWidget(self.height_preset_group)

        # 自定义高度输入
        custom_label = QLabel(self.i18n.tr("config.custom_label"))
        height_layout.addWidget(custom_label)

        self.height_spin = QSpinBox()
        self.height_spin.setStyleSheet(StyleManager.input_number())
        self.height_spin.setRange(2, 50)
        # 延迟读取配置值，避免配置未加载时出错
        current_height = self.config.get('bar_height', 20) if self.config else 20
        self.height_spin.setValue(current_height)
        self.height_spin.setSuffix(" px")
        self.height_spin.setMaximumWidth(80)
        self.height_spin.valueChanged.connect(self.on_height_value_changed)
        height_layout.addWidget(self.height_spin)

        height_layout.addStretch()

        basic_layout.addRow(tr("appearance.bar_height") + ":", height_container)

        # 延迟更新按钮状态，避免配置未加载时出错
        QTimer.singleShot(100, self.update_height_preset_buttons)

        # 显示器索引 (隐藏,使用默认值)
        self.screen_spin = QSpinBox()
        self.screen_spin.setStyleSheet(StyleManager.input_number())
        self.screen_spin.setRange(0, 10)
        self.screen_spin.setValue(self.config.get('screen_index', 0) if self.config else 0)
        self.screen_spin.setVisible(False)  # 隐藏控件
        # basic_layout.addRow(self.i18n.tr("config.labels.show_index") + ":", self.screen_spin)  # 不添加到布局

        # 更新间隔 (隐藏,使用默认值)
        self.interval_spin = QSpinBox()
        self.interval_spin.setStyleSheet(StyleManager.input_number())
        self.interval_spin.setRange(100, 60000)
        self.interval_spin.setValue(self.config.get('update_interval', 1000) if self.config else 1000)
        self.interval_spin.setSuffix(" " + tr("appearance.milliseconds"))
        self.interval_spin.setVisible(False)  # 隐藏控件
        # basic_layout.addRow(self.i18n.tr("config.labels.update_interval") + ":", self.interval_spin)  # 不添加到布局

        # 语言选择
        language_container = QWidget()
        language_layout = QHBoxLayout(language_container)
        language_layout.setContentsMargins(0, 0, 0, 0)

        self.language_combo = QComboBox()
        self.language_combo.setStyleSheet(StyleManager.dropdown())
        self.language_combo.addItem(tr("config.language_zh_cn"), "zh_CN")
        self.language_combo.addItem(tr("config.language_en_us"), "en_US")

        # 设置当前语言
        current_lang = self.config.get('language', 'zh_CN') if self.config else 'zh_CN'
        index = self.language_combo.findData(current_lang)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)

        self.language_combo.currentIndexChanged.connect(self.on_language_changed)
        language_layout.addWidget(self.language_combo)
        language_layout.addStretch()

        basic_layout.addRow(tr("config.language") + ":", language_container)

                # 开机自启动
        autostart_container = QWidget()
        autostart_layout = QHBoxLayout(autostart_container)
        autostart_layout.setContentsMargins(0, 0, 0, 0)

        self.autostart_check = QCheckBox(tr("appearance.autostart"))
        self.autostart_check.setToolTip(self.i18n.tr("config.auto_start_tooltip"))
        # 从注册表读取当前状态
        if self.autostart_manager:
            self.autostart_check.setChecked(self.autostart_manager.is_enabled())
        autostart_layout.addWidget(self.autostart_check)

        # 添加状态提示标签
        self.autostart_status_label = QLabel()
        self.autostart_status_label.setStyleSheet("color: #888888; font-size: 11px;")
        self._update_autostart_status_label()
        autostart_layout.addWidget(self.autostart_status_label)
        autostart_layout.addStretch()

        # 连接复选框变化信号，实时更新状态标签
        self.autostart_check.stateChanged.connect(self._update_autostart_status_label)

        basic_layout.addRow(self.i18n.tr("config.labels.autostart") + ":", autostart_container)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # 颜色设置组
        color_group = QGroupBox(tr("appearance.color_settings"))
        color_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        color_layout = QVBoxLayout()  # 改用VBoxLayout以避免QFormLayout的标签间距
        color_layout.setSpacing(15)
        color_layout.setContentsMargins(10, 10, 10, 10)

        # 背景颜色和时间标记颜色 (合并到同一行,色块缩小50%)
        colors_row_layout = QHBoxLayout()

        # 背景颜色
        bg_color = self.config.get('background_color', '#505050') if self.config else '#505050'
        self.bg_color_input = QLineEdit(bg_color)
        self.bg_color_input.setVisible(False)  # 隐藏色值输入框

        colors_row_layout.addWidget(QLabel(tr("appearance.background_color") + ":"))
        self.bg_color_preview = QPushButton()
        self.bg_color_preview.setFixedSize(20, 18)  # 再次缩小50%宽度+高度减半: 40->20, 36->18
        self.bg_color_preview.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                border: 2px solid #CCCCCC;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border: 2px solid #999999;
            }}
        """)
        self.bg_color_preview.setCursor(Qt.CursorShape.PointingHandCursor)
        self.bg_color_preview.clicked.connect(partial(self.choose_color, self.bg_color_input))
        colors_row_layout.addWidget(self.bg_color_preview)

        colors_row_layout.addSpacing(30)  # 两个颜色选择器之间的间距

        # 时间标记颜色
        marker_color = self.config.get('marker_color', '#FF0000') if self.config else '#FF0000'
        self.marker_color_input = QLineEdit(marker_color)
        self.marker_color_input.setVisible(False)  # 隐藏色值输入框

        colors_row_layout.addWidget(QLabel(tr("appearance.marker_color") + ":"))
        self.marker_color_preview = QPushButton()
        self.marker_color_preview.setFixedSize(20, 18)  # 再次缩小50%宽度+高度减半: 40->20, 36->18
        self.marker_color_preview.setStyleSheet(f"""
            QPushButton {{
                background-color: {marker_color};
                border: 2px solid #CCCCCC;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border: 2px solid #999999;
            }}
        """)
        self.marker_color_preview.setCursor(Qt.CursorShape.PointingHandCursor)
        self.marker_color_preview.clicked.connect(partial(self.choose_color, self.marker_color_input))
        colors_row_layout.addWidget(self.marker_color_preview)

        colors_row_layout.addStretch()
        color_layout.addLayout(colors_row_layout)  # 直接添加到VBoxLayout,无标签间距

        # 背景透明度 (使用滑块控制,范围0-100%,缩短长度)
        opacity_layout = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 100)
        # 将0-255转换为0-100百分比
        opacity_value = self.config.get('background_opacity', 180) if self.config else 180
        opacity_percent = int(opacity_value / 255 * 100)
        self.opacity_slider.setValue(opacity_percent)
        self.opacity_slider.setFixedWidth(150)  # 缩短滑块长度

        self.opacity_label = QLabel(f"{opacity_percent}%")
        self.opacity_label.setMinimumWidth(50)
        self.opacity_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # 滑块值变化时更新标签
        self.opacity_slider.valueChanged.connect(
            lambda value: self.opacity_label.setText(f"{value}%")
        )

        opacity_layout.addWidget(QLabel(tr("appearance.background_opacity") + ":"))
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_label)
        opacity_layout.addStretch()
        color_layout.addLayout(opacity_layout)

        # 隐藏旧的spin控件,保留用于保存配置时的转换
        self.opacity_spin = QSpinBox()
        self.opacity_spin.setVisible(False)

        # 时间标记宽度 (缩小输入框宽度)
        marker_width_layout = QHBoxLayout()
        marker_width_layout.addWidget(QLabel(self.i18n.tr("config.labels.marker_width") + ":"))
        self.marker_width_spin = QSpinBox()
        self.marker_width_spin.setStyleSheet(StyleManager.input_number())
        self.marker_width_spin.setRange(1, 10)
        self.marker_width_spin.setValue(self.config.get('marker_width', 2) if self.config else 2)
        self.marker_width_spin.setSuffix(" " + tr("appearance.pixels"))
        self.marker_width_spin.setFixedWidth(100)  # 稍微增加宽度以容纳后缀
        marker_width_layout.addWidget(self.marker_width_spin)
        marker_width_layout.addStretch()
        color_layout.addLayout(marker_width_layout)

        # 时间标记类型
        marker_type_layout = QHBoxLayout()
        marker_type_layout.addWidget(QLabel(self.i18n.tr("config.labels.marker_type") + ":"))
        self.marker_type_combo = QComboBox()
        self.marker_type_combo.setStyleSheet(StyleManager.dropdown())
        self.marker_type_combo.addItems(["line", "image", "gif"])
        marker_type = self.config.get('marker_type', 'line') if self.config else 'line'
        self.marker_type_combo.setCurrentText(marker_type)
        self.marker_type_combo.currentTextChanged.connect(self.on_marker_type_changed)
        marker_type_layout.addWidget(self.marker_type_combo)

        marker_type_hint = QLabel(tr("appearance.marker_type_note"))
        marker_type_hint.setStyleSheet("color: #888888; font-size: 9pt;")
        marker_type_layout.addWidget(marker_type_hint)
        marker_type_layout.addStretch()

        color_layout.addLayout(marker_type_layout)

        # 标记图片预设选择器(下拉框)
        preset_selector_layout = QHBoxLayout()
        preset_selector_layout.addWidget(QLabel("📦 标记图片预设:"))

        self.marker_preset_combo = QComboBox()
        self.marker_preset_combo.setStyleSheet(StyleManager.dropdown())

        # 添加所有预设到下拉框
        current_preset_id = self.marker_preset_manager.get_current_preset_id()
        for preset in self.marker_preset_manager.get_all_presets():
            preset_id = preset["id"]
            preset_name = preset["name"]

            self.marker_preset_combo.addItem(preset_name, preset_id)

            # 设置当前选中项
            if preset_id == current_preset_id:
                self.marker_preset_combo.setCurrentIndex(self.marker_preset_combo.count() - 1)

        self.marker_preset_combo.currentIndexChanged.connect(self._on_preset_combo_changed)
        preset_selector_layout.addWidget(self.marker_preset_combo)
        preset_selector_layout.addStretch()

        color_layout.addLayout(preset_selector_layout)

        # 标记图片路径(仅在选择自定义预设时显示整行)
        # 创建包含标签和内容的整行容器
        self.marker_image_row = QWidget()
        marker_image_row_layout = QHBoxLayout(self.marker_image_row)
        marker_image_row_layout.setContentsMargins(0, 0, 0, 0)
        marker_image_row_layout.setSpacing(10)

        # 标签
        marker_image_label = QLabel(tr("appearance.marker_image") + ":")
        marker_image_label.setMinimumWidth(120)
        marker_image_row_layout.addWidget(marker_image_label)

        # 输入框和按钮容器
        marker_image_content = QWidget()
        marker_image_layout = QHBoxLayout(marker_image_content)
        marker_image_layout.setContentsMargins(0, 0, 0, 0)

        marker_image_path = self.config.get('marker_image_path', '') if self.config else ''
        self.marker_image_input = QLineEdit(marker_image_path)
        self.marker_image_input.setPlaceholderText(self.i18n.tr("config.choose_image_file"))
        marker_image_layout.addWidget(self.marker_image_input)

        marker_image_btn = QPushButton(tr("appearance.browse"))
        marker_image_btn.clicked.connect(self.choose_marker_image)
        marker_image_btn.setFixedSize(90, 36)
        marker_image_btn.setStyleSheet("QPushButton { padding: 8px 12px; font-size: 12px; }")
        marker_image_layout.addWidget(marker_image_btn)

        marker_image_row_layout.addWidget(marker_image_content)

        # 添加整行到布局
        color_layout.addWidget(self.marker_image_row)

        # 初始化时根据当前预设决定是否显示整行
        self._update_marker_image_visibility()

        # 标记图片大小 - 预设档位 + 自定义
        marker_size_container = QWidget()
        marker_size_layout = QHBoxLayout(marker_size_container)
        marker_size_layout.setContentsMargins(0, 0, 0, 0)

        # 预设档位按钮组
        self.marker_size_preset_group = QWidget()
        marker_size_preset_layout = QHBoxLayout(self.marker_size_preset_group)
        marker_size_preset_layout.setContentsMargins(0, 0, 0, 0)
        marker_size_preset_layout.setSpacing(5)

        # 预设大小选项 - 3个档位
        self.marker_size_presets = [
            ("config.presets.size_small", 25),
            ("config.presets.size_medium", 35),
            ("config.presets.size_large", 50)
        ]

        self.marker_size_preset_buttons = []
        for name_key, size in self.marker_size_presets:
            name = self.i18n.tr(name_key)
            btn = QPushButton(f"{name} ({size}px)")
            btn.setCheckable(True)
            btn.setMaximumWidth(80)
            # 使用 partial 避免 Lambda 循环引用
            btn.clicked.connect(partial(self.set_marker_size_preset, size))
            marker_size_preset_layout.addWidget(btn)
            self.marker_size_preset_buttons.append((btn, size))

        marker_size_layout.addWidget(self.marker_size_preset_group)

        # 自定义大小输入
        custom_size_label = QLabel(self.i18n.tr("config.custom_label"))
        marker_size_layout.addWidget(custom_size_label)

        self.marker_size_spin = QSpinBox()
        self.marker_size_spin.setStyleSheet(StyleManager.input_number())
        self.marker_size_spin.setRange(20, 200)
        marker_size = self.config.get('marker_size', 50) if self.config else 50
        self.marker_size_spin.setValue(marker_size)
        self.marker_size_spin.setSuffix(" px")
        self.marker_size_spin.setMaximumWidth(110)  # 增加宽度以显示完整内容
        self.marker_size_spin.valueChanged.connect(self.on_marker_size_value_changed)
        marker_size_layout.addWidget(self.marker_size_spin)

        marker_size_layout.addStretch()

        # 添加标记图片大小到布局
        marker_size_full_layout = QHBoxLayout()
        marker_size_full_layout.addWidget(QLabel(tr("appearance.marker_size") + ":"))
        marker_size_full_layout.addWidget(marker_size_container)
        marker_size_full_layout.addStretch()
        color_layout.addLayout(marker_size_full_layout)

        # 延迟更新按钮状态
        # 将在 _load_config_and_tasks 中更新

        # 标记图片偏移 (X和Y放在同一行)
        offset_layout = QHBoxLayout()

        # X轴偏移
        offset_layout.addWidget(QLabel("X:"))
        self.marker_x_offset_spin = QSpinBox()
        self.marker_x_offset_spin.setStyleSheet(StyleManager.input_number())
        self.marker_x_offset_spin.setRange(-100, 100)
        self.marker_x_offset_spin.setValue(self.config.get('marker_x_offset', 0))
        self.marker_x_offset_spin.setSuffix(" px")
        self.marker_x_offset_spin.setFixedWidth(80)
        self.marker_x_offset_spin.valueChanged.connect(self._save_current_preset_params)
        offset_layout.addWidget(self.marker_x_offset_spin)

        offset_layout.addSpacing(20)

        # Y轴偏移
        offset_layout.addWidget(QLabel("Y:"))
        self.marker_y_offset_spin = QSpinBox()
        self.marker_y_offset_spin.setStyleSheet(StyleManager.input_number())
        self.marker_y_offset_spin.setRange(-100, 100)
        self.marker_y_offset_spin.setValue(self.config.get('marker_y_offset', 0))
        self.marker_y_offset_spin.setSuffix(" px")
        self.marker_y_offset_spin.setFixedWidth(80)
        self.marker_y_offset_spin.valueChanged.connect(self._save_current_preset_params)
        offset_layout.addWidget(self.marker_y_offset_spin)

        # 合并的提示信息
        offset_hint = QLabel(tr("appearance.marker_offset_note"))
        offset_hint.setStyleSheet("color: #888888; font-size: 9pt;")
        offset_layout.addWidget(offset_hint)
        offset_layout.addStretch()

        # 添加偏移到布局
        offset_full_layout = QHBoxLayout()
        offset_full_layout.addWidget(QLabel(self.i18n.tr("config.labels.marker_offset") + ":"))
        offset_full_layout.addLayout(offset_layout)
        color_layout.addLayout(offset_full_layout)

        # 标记动画播放速度
        self.marker_speed_spin = QSpinBox()
        self.marker_speed_spin.setStyleSheet(StyleManager.input_number())
        self.marker_speed_spin.setRange(10, 500)
        self.marker_speed_spin.setValue(self.config.get('marker_speed', 100))
        self.marker_speed_spin.setSuffix(" %")
        self.marker_speed_spin.setSingleStep(10)
        self.marker_speed_spin.setMaximumWidth(100)
        speed_hint = QLabel(tr("appearance.marker_speed_note"))
        speed_hint.setStyleSheet("color: #888888; font-size: 9pt;")
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel(self.i18n.tr("config.labels.animation_speed") + ":"))
        speed_layout.addWidget(self.marker_speed_spin)
        speed_layout.addWidget(speed_hint)
        speed_layout.addStretch()
        color_layout.addLayout(speed_layout)

        # 标记图片始终显示
        self.marker_always_visible_check = QCheckBox("标记图片始终显示")
        self.marker_always_visible_check.setChecked(self.config.get('marker_always_visible', True))
        always_visible_hint = QLabel("取消勾选后,标记图片仅在鼠标悬停时显示")
        always_visible_hint.setStyleSheet("color: #888888; font-size: 11px;")
        always_visible_layout = QHBoxLayout()
        always_visible_layout.addWidget(self.marker_always_visible_check)
        always_visible_layout.addWidget(always_visible_hint)
        always_visible_layout.addStretch()
        color_layout.addLayout(always_visible_layout)

        color_group.setLayout(color_layout)
        layout.addWidget(color_group)

        # 初始化时根据类型显示/隐藏相关控件
        self.on_marker_type_changed(self.marker_type_combo.currentText())

        # 弹幕设置组
        danmaku_group = QGroupBox("弹幕设置")
        danmaku_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        danmaku_layout = QVBoxLayout()  # 改用VBoxLayout以避免左侧标签间距
        danmaku_layout.setSpacing(12)
        danmaku_layout.setContentsMargins(10, 10, 10, 10)

        # 弹幕开关
        self.danmaku_enabled_check = QCheckBox("启用弹幕")
        danmaku_config = self.config.get('danmaku', {})
        self.danmaku_enabled_check.setChecked(danmaku_config.get('enabled', True))
        danmaku_hint = QLabel("在进度条上方显示B站风格的滚动弹幕")
        danmaku_hint.setStyleSheet("color: #888888; font-size: 9pt;")
        danmaku_enable_layout = QHBoxLayout()
        danmaku_enable_layout.addWidget(self.danmaku_enabled_check)
        danmaku_enable_layout.addWidget(danmaku_hint)
        danmaku_enable_layout.addStretch()
        danmaku_layout.addLayout(danmaku_enable_layout)

        # 弹幕频率
        self.danmaku_frequency_spin = QSpinBox()
        self.danmaku_frequency_spin.setStyleSheet(StyleManager.input_number())
        self.danmaku_frequency_spin.setRange(5, 120)
        self.danmaku_frequency_spin.setValue(danmaku_config.get('frequency', 30))
        self.danmaku_frequency_spin.setSuffix(" 秒")
        self.danmaku_frequency_spin.setMaximumWidth(80)
        freq_hint = QLabel("每隔多少秒生成一条弹幕")
        freq_hint.setStyleSheet("color: #888888; font-size: 9pt;")
        freq_layout = QHBoxLayout()
        freq_layout.addWidget(QLabel("生成频率:"))
        freq_layout.addWidget(self.danmaku_frequency_spin)
        freq_layout.addWidget(freq_hint)
        freq_layout.addStretch()
        danmaku_layout.addLayout(freq_layout)

        # 弹幕速度
        self.danmaku_speed_spin = QDoubleSpinBox()
        self.danmaku_speed_spin.setStyleSheet(StyleManager.input_number())
        self.danmaku_speed_spin.setRange(0.5, 3.0)
        self.danmaku_speed_spin.setValue(danmaku_config.get('speed', 1.0))
        self.danmaku_speed_spin.setSingleStep(0.1)
        self.danmaku_speed_spin.setSuffix(" x")
        self.danmaku_speed_spin.setMaximumWidth(80)
        speed_hint = QLabel("弹幕移动速度倍率")
        speed_hint.setStyleSheet("color: #888888; font-size: 9pt;")
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("移动速度:"))
        speed_layout.addWidget(self.danmaku_speed_spin)
        speed_layout.addWidget(speed_hint)
        speed_layout.addStretch()
        danmaku_layout.addLayout(speed_layout)

        # 字体大小
        self.danmaku_font_size_spin = QSpinBox()
        self.danmaku_font_size_spin.setStyleSheet(StyleManager.input_number())
        self.danmaku_font_size_spin.setRange(10, 24)
        self.danmaku_font_size_spin.setValue(danmaku_config.get('font_size', 14))
        self.danmaku_font_size_spin.setSuffix(" px")
        self.danmaku_font_size_spin.setMaximumWidth(80)
        font_hint = QLabel("弹幕文字大小")
        font_hint.setStyleSheet("color: #888888; font-size: 9pt;")
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("字体大小:"))
        font_layout.addWidget(self.danmaku_font_size_spin)
        font_layout.addWidget(font_hint)
        font_layout.addStretch()
        danmaku_layout.addLayout(font_layout)

        # 透明度 (使用滑块控制,范围0-100%)
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("透明度:"))
        self.danmaku_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.danmaku_opacity_slider.setRange(0, 100)
        # 将0-1转换为0-100百分比
        opacity_value = danmaku_config.get('opacity', 1.0)
        opacity_percent = int(opacity_value * 100)
        self.danmaku_opacity_slider.setValue(opacity_percent)
        self.danmaku_opacity_slider.setFixedWidth(150)  # 和背景透明度滑块长度一致

        self.danmaku_opacity_label = QLabel(f"{opacity_percent}%")
        self.danmaku_opacity_label.setMinimumWidth(50)
        self.danmaku_opacity_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # 滑块值变化时更新标签
        self.danmaku_opacity_slider.valueChanged.connect(
            lambda value: self.danmaku_opacity_label.setText(f"{value}%")
        )

        opacity_layout.addWidget(self.danmaku_opacity_slider)
        opacity_layout.addWidget(self.danmaku_opacity_label)
        opacity_layout.addStretch()
        danmaku_layout.addLayout(opacity_layout)

        # 隐藏旧的spin控件,保留用于保存配置时的转换
        self.danmaku_opacity_spin = QDoubleSpinBox()
        self.danmaku_opacity_spin.setVisible(False)

        # 同屏数量
        self.danmaku_max_count_spin = QSpinBox()
        self.danmaku_max_count_spin.setStyleSheet(StyleManager.input_number())
        self.danmaku_max_count_spin.setRange(1, 10)
        self.danmaku_max_count_spin.setValue(danmaku_config.get('max_count', 3))
        self.danmaku_max_count_spin.setMaximumWidth(80)
        count_hint = QLabel("同时显示的最大弹幕数量")
        count_hint.setStyleSheet("color: #888888; font-size: 9pt;")
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("同屏数量:"))
        count_layout.addWidget(self.danmaku_max_count_spin)
        count_layout.addWidget(count_hint)
        count_layout.addStretch()
        danmaku_layout.addLayout(count_layout)

        # Y轴偏移
        self.danmaku_y_offset_spin = QSpinBox()
        self.danmaku_y_offset_spin.setStyleSheet(StyleManager.input_number())
        self.danmaku_y_offset_spin.setRange(20, 200)
        self.danmaku_y_offset_spin.setValue(danmaku_config.get('y_offset', 80))
        self.danmaku_y_offset_spin.setSuffix(" px")
        self.danmaku_y_offset_spin.setMaximumWidth(80)
        y_offset_hint = QLabel("弹幕距离进度条的垂直距离")
        y_offset_hint.setStyleSheet("color: #888888; font-size: 9pt;")
        y_offset_layout = QHBoxLayout()
        y_offset_layout.addWidget(QLabel("垂直位置:"))
        y_offset_layout.addWidget(self.danmaku_y_offset_spin)
        y_offset_layout.addWidget(y_offset_hint)
        y_offset_layout.addStretch()
        danmaku_layout.addLayout(y_offset_layout)

        # 颜色模式
        self.danmaku_color_mode_combo = QComboBox()
        self.danmaku_color_mode_combo.setStyleSheet(StyleManager.dropdown())
        self.danmaku_color_mode_combo.addItem("自动(根据任务类型)", "auto")
        self.danmaku_color_mode_combo.addItem("固定白色", "fixed")
        current_color_mode = danmaku_config.get('color_mode', 'auto')
        index = 0 if current_color_mode == 'auto' else 1
        self.danmaku_color_mode_combo.setCurrentIndex(index)
        color_mode_hint = QLabel("弹幕颜色显示方式")
        color_mode_hint.setStyleSheet("color: #888888; font-size: 9pt;")
        color_mode_layout = QHBoxLayout()
        color_mode_layout.addWidget(QLabel("颜色模式:"))
        color_mode_layout.addWidget(self.danmaku_color_mode_combo)
        color_mode_layout.addWidget(color_mode_hint)
        color_mode_layout.addStretch()
        danmaku_layout.addLayout(color_mode_layout)

        # 阴影效果 - 删除此选项,改为隐藏控件以保持向后兼容
        self.shadow_check = QCheckBox("启用阴影")
        self.shadow_check.setChecked(self.config.get('enable_shadow', True))
        self.shadow_check.setVisible(False)  # 隐藏控件,不显示给用户

        # 圆角半径(隐藏UI,使用固定值0)
        self.radius_spin = QSpinBox()
        self.radius_spin.setValue(0)  # 固定为0,不显示圆角
        self.radius_spin.setVisible(False)  # 隐藏控件

        danmaku_group.setLayout(danmaku_layout)
        layout.addWidget(danmaku_group)

        layout.addStretch()
        # 将内容widget设置到滚动区域
        scroll_area.setWidget(widget)
        return scroll_area

    def create_tasks_tab(self):
        """创建任务管理标签页"""
        # 创建滚动区域容器
        from PySide6.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 创建内容widget
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 顶部信息和模板加载区域
        top_layout = QVBoxLayout()

        # AI任务规划区域
        ai_group = QGroupBox("🤖 " + self.i18n.tr("tasks.sections.ai_planning"))
        ai_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        ai_layout = QVBoxLayout()

        # 说明标签
        ai_hint = QLabel(self.i18n.tr("tasks.hints.ai_description"))
        ai_hint.setStyleSheet("color: #FF9800; font-style: italic; padding: 3px;")
        ai_layout.addWidget(ai_hint)

        # AI输入框
        input_container = QHBoxLayout()
        input_label = QLabel(self.i18n.tr("tasks.labels.describe_plan"))
        input_label.setStyleSheet(StyleManager.label_subtitle())
        input_container.addWidget(input_label)

        self.ai_input = QLineEdit()
        self.ai_input.setStyleSheet(StyleManager.input_text())
        self.ai_input.setPlaceholderText(self.i18n.tr("general.text_5947"))
        self.ai_input.setMinimumHeight(35)
        self.ai_input.returnPressed.connect(self.on_ai_generate_clicked)  # 支持回车键
        input_container.addWidget(self.ai_input)

        ai_layout.addLayout(input_container)

        # 按钮行
        ai_button_layout = QHBoxLayout()

        # AI生成按钮
        self.generate_btn = QPushButton(self.i18n.tr("account.ui.ai_smart_generate"))
        self.generate_btn.clicked.connect(self.on_ai_generate_clicked)
        self.generate_btn.setFixedHeight(36)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF6B00;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #FF8500;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #666;
            }
        """)
        ai_button_layout.addWidget(self.generate_btn)

        # 配额状态标签
        self.quota_label = QLabel(self.i18n.tr("tasks.labels.quota_status_loading"))
        self.quota_label.setStyleSheet("color: #333333; padding: 5px;")
        ai_button_layout.addWidget(self.quota_label)

        # 刷新配额按钮
        self.refresh_quota_btn = QPushButton(self.i18n.tr("tasks.buttons.refresh_quota"))
        self.refresh_quota_btn.clicked.connect(self.refresh_quota_status)
        self.refresh_quota_btn.setFixedHeight(36)
        self.refresh_quota_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        ai_button_layout.addWidget(self.refresh_quota_btn)

        ai_button_layout.addStretch()
        ai_layout.addLayout(ai_button_layout)

        ai_group.setLayout(ai_layout)
        top_layout.addWidget(ai_group)

        # 延迟加载配额状态，避免初始化时阻塞
        QTimer.singleShot(300, self.refresh_quota_status_async)

        # 立即显示初始状态（不需要等待）
        if hasattr(self, 'quota_label'):
            self.quota_label.setText(self.i18n.tr("general.text_3841"))
            self.quota_label.setStyleSheet("color: #ff9800; padding: 5px; font-weight: bold;")
        if hasattr(self, 'generate_btn'):
            self.generate_btn.setEnabled(False)

        # 说明标签
        info_label = QLabel(self.i18n.tr("tasks.hints.double_click_edit"))
        info_label.setStyleSheet("color: #333333; font-style: italic;")
        top_layout.addWidget(info_label)

        # 预设主题选择区域
        theme_group = QGroupBox("🎨 " + self.i18n.tr("tasks.sections.preset_themes"))
        theme_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        theme_layout = QHBoxLayout()

        theme_label = QLabel(self.i18n.tr("tasks.labels.select_theme"))
        theme_layout.addWidget(theme_label)

        # 创建主题下拉框
        self.theme_combo = QComboBox()
        self.theme_combo.setStyleSheet(StyleManager.dropdown())
        self.theme_combo.setMinimumWidth(150)

        # 延迟加载主题列表
        QTimer.singleShot(200, self._load_preset_themes)

        self.theme_combo.currentIndexChanged.connect(self.on_preset_theme_changed_with_preview)
        theme_layout.addWidget(self.theme_combo)

        # 主题配色预览区域
        preview_label = QLabel(self.i18n.tr("tasks.labels.color_preview"))
        preview_label.setStyleSheet("color: #333333; margin-left: 10px;")
        theme_layout.addWidget(preview_label)

        self.colors_preview_widget = QWidget()
        colors_preview_layout = QHBoxLayout(self.colors_preview_widget)
        colors_preview_layout.setContentsMargins(0, 0, 0, 0)
        colors_preview_layout.setSpacing(3)
        theme_layout.addWidget(self.colors_preview_widget)

        theme_layout.addStretch()
        theme_group.setLayout(theme_layout)
        top_layout.addWidget(theme_group)

        # 合并的模板管理区域
        self.template_group = QGroupBox("📋 模板管理")
        self.template_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")

        template_container = QVBoxLayout()

        # 统一的模板选择布局
        self.template_layout = QHBoxLayout()
        self.template_layout.setSpacing(12)

        # 模板类型选择下拉框
        type_label = QLabel("模板类型:")
        self.template_layout.addWidget(type_label)

        self.template_type_combo = QComboBox()
        self.template_type_combo.setStyleSheet(StyleManager.dropdown())
        self.template_type_combo.setMinimumWidth(120)
        self.template_type_combo.addItem("📋 预设模板", "preset")
        self.template_type_combo.addItem("💾 我的模板", "custom")
        self.template_type_combo.currentIndexChanged.connect(self._on_template_type_changed)
        self.template_layout.addWidget(self.template_type_combo)

        # 选择模板标签
        template_select_label = QLabel(self.i18n.tr("templates.auto_apply.select_template") + ":")
        self.template_layout.addWidget(template_select_label)

        # 统一的模板选择下拉框(动态内容)
        self.unified_template_combo = QComboBox()
        self.unified_template_combo.setStyleSheet(StyleManager.dropdown())
        self.unified_template_combo.setMinimumWidth(200)
        self.template_layout.addWidget(self.unified_template_combo)

        # 加载按钮
        self.load_template_btn = QPushButton(self.i18n.tr("tasks.buttons.load"))
        self.load_template_btn.setToolTip("加载选中的模板")
        self.load_template_btn.setFixedHeight(36)
        self.load_template_btn.setStyleSheet("QPushButton { padding: 8px 16px; border-radius: 4px; }")
        self.load_template_btn.clicked.connect(self._load_unified_template)
        self.template_layout.addWidget(self.load_template_btn)

        # 删除按钮(初始隐藏,只在"我的模板"时显示)
        self.delete_template_btn = QPushButton(self.i18n.tr("general.text_1284"))
        self.delete_template_btn.setToolTip(self.i18n.tr("config.tooltips.delete_custom_template"))
        self.delete_template_btn.setFixedHeight(36)
        self.delete_template_btn.setStyleSheet("QPushButton { padding: 8px 12px; border-radius: 4px; }")
        self.delete_template_btn.clicked.connect(self._delete_selected_custom_template)
        self.delete_template_btn.setVisible(False)  # 初始隐藏
        self.template_layout.addWidget(self.delete_template_btn)

        self.template_layout.addStretch()

        template_container.addLayout(self.template_layout)
        self.template_group.setLayout(template_container)
        top_layout.addWidget(self.template_group)

        # 初始化加载预设模板
        self._load_templates_by_type("preset")

        layout.addLayout(top_layout)

        # 可视化时间轴编辑器（延迟创建，避免初始化时阻塞）
        timeline_group = QGroupBox("🎨 " + self.i18n.tr("tasks.sections.visual_timeline"))
        timeline_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        timeline_layout = QVBoxLayout()

        timeline_hint = QLabel(self.i18n.tr("tasks.hints.drag_to_adjust"))
        timeline_hint.setStyleSheet("color: #666666; font-style: italic; padding: 5px;")
        timeline_layout.addWidget(timeline_hint)

        # 创建占位符，延迟初始化时间轴编辑器
        timeline_placeholder = QWidget()
        timeline_placeholder.setMinimumHeight(100)
        timeline_placeholder.setStyleSheet("background-color: #f5f5f5; border: 1px dashed #ccc;")
        timeline_layout.addWidget(timeline_placeholder)
        
        self.timeline_editor = None  # 延迟初始化

        timeline_group.setLayout(timeline_layout)
        layout.addWidget(timeline_group)
        
        # 延迟创建时间轴编辑器
        QTimer.singleShot(150, lambda: self._init_timeline_editor(timeline_layout, timeline_placeholder))

        # 任务表格
        self.tasks_table = QTableWidget()
        self.tasks_table.setStyleSheet(StyleManager.table())
        self.tasks_table.setColumnCount(6)
        self.tasks_table.setHorizontalHeaderLabels([self.i18n.tr("config.table.start_time"), self.i18n.tr("config.table.end_time"), self.i18n.tr("config.table.task_name"), self.i18n.tr("config.table.bg_color"), self.i18n.tr("config.table.text_color"), self.i18n.tr("config.table.actions")])
        self.tasks_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        # 设置列宽以适应英文文本
        self.tasks_table.setColumnWidth(0, 100)  # Start Time
        self.tasks_table.setColumnWidth(1, 100)  # End Time
        # Column 2 (Task Name) is set to Stretch
        self.tasks_table.setColumnWidth(3, 195)  # Background Color
        self.tasks_table.setColumnWidth(4, 195)  # Text Color
        self.tasks_table.setColumnWidth(5, 80)   # Actions (Delete)

        # 根据任务数量动态计算表格高度
        # 每行约60px高度 + 表头30px + 一些padding
        row_height = 60
        header_height = 30
        min_visible_rows = 8  # 至少显示8行
        max_visible_rows = 15  # 最多显示15行,超出则显示滚动条

        # 计算实际高度 (初始化时使用 self.tasks)
        actual_row_count = len(self.tasks) if hasattr(self, 'tasks') else 0
        visible_rows = max(min_visible_rows, min(actual_row_count, max_visible_rows))
        calculated_height = header_height + (visible_rows * row_height) + 20  # +20 padding

        self.tasks_table.setMinimumHeight(calculated_height)
        self.tasks_table.setMaximumHeight(calculated_height)

        # 启用垂直滚动条(仅在需要时显示)
        self.tasks_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tasks_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 监听表格项的变化,实时同步到时间轴
        self.tasks_table.itemChanged.connect(self.on_table_item_changed)

        # 延迟加载任务到表格，避免初始化时阻塞UI
        QTimer.singleShot(100, self.load_tasks_to_table)

        layout.addWidget(self.tasks_table)

        # 按钮组
        button_layout = QHBoxLayout()

        add_btn = QPushButton(self.i18n.tr("tasks.buttons.add_task"))
        add_btn.clicked.connect(self.add_task)
        add_btn.setFixedHeight(36)
        add_btn.setStyleSheet(StyleManager.button_minimal())

        save_template_btn = QPushButton(self.i18n.tr("account.other.save_as_template"))
        save_template_btn.clicked.connect(self.save_as_template)
        save_template_btn.setFixedHeight(36)
        save_template_btn.setStyleSheet(StyleManager.button_minimal())

        # 智能添加图标,避免重复
        clear_text = self.i18n.tr("tasks.buttons.clear_all_tasks")
        if not clear_text.startswith("🗑"):
            clear_text = "🗑 " + clear_text
        clear_btn = QPushButton(clear_text)
        clear_btn.clicked.connect(self.clear_all_tasks)
        clear_btn.setFixedHeight(36)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #333333;
                border: 1px solid #CCCCCC;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #F5F5F5;
                border: 1px solid #999999;
            }
        """)

        button_layout.addWidget(add_btn)
        button_layout.addWidget(save_template_btn)
        button_layout.addStretch()  # 隔离危险按钮,防止误操作
        button_layout.addWidget(clear_btn)

        layout.addLayout(button_layout)

        # ========== 模板自动应用管理（放在最底部） ==========
        # 智能添加图标,避免重复
        schedule_title = self.i18n.tr("tasks.sections.auto_apply_management")
        if not schedule_title.startswith("📅"):
            schedule_title = "📅 " + schedule_title
        schedule_panel = QGroupBox(schedule_title)
        schedule_panel.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        schedule_layout = QVBoxLayout()

        # 说明文字
        schedule_hint = QLabel(self.i18n.tr("config.settings_9"))
        schedule_hint.setStyleSheet("color: #333333; font-style: italic; padding: 5px;")
        schedule_layout.addWidget(schedule_hint)

        # 已配置规则表格
        self.schedule_table = QTableWidget()
        self.schedule_table.setStyleSheet(StyleManager.table())
        self.schedule_table.setColumnCount(4)
        self.schedule_table.setHorizontalHeaderLabels([
            self.i18n.tr("config.template.template_name"),
            self.i18n.tr("config.template.apply_time"),
            self.i18n.tr("config.template.status"),
            self.i18n.tr("config.table.actions")
        ])
        self.schedule_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.schedule_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.schedule_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.schedule_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.schedule_table.setMinimumHeight(150)
        self.schedule_table.setMaximumHeight(300)
        self.schedule_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.schedule_table.setSelectionMode(QTableWidget.SingleSelection)

        # 延迟加载时间表数据
        QTimer.singleShot(300, self._load_schedule_table)

        schedule_layout.addWidget(self.schedule_table)

        # 操作按钮行
        button_row = QHBoxLayout()

        add_schedule_btn = QPushButton(self.i18n.tr("tasks.buttons.add_rule"))
        add_schedule_btn.setFixedHeight(36)
        add_schedule_btn.setStyleSheet(StyleManager.button_primary())
        add_schedule_btn.clicked.connect(self._add_schedule_dialog)
        button_row.addWidget(add_schedule_btn)

        test_date_btn = QPushButton(self.i18n.tr("tasks.buttons.test_date"))
        test_date_btn.setToolTip(self.i18n.tr("config.tooltips.test_date_match"))
        test_date_btn.setFixedHeight(36)
        test_date_btn.setStyleSheet("QPushButton { padding: 8px 16px; border-radius: 4px; }")
        test_date_btn.clicked.connect(self._test_date_matching)
        button_row.addWidget(test_date_btn)

        button_row.addStretch()

        schedule_layout.addLayout(button_row)

        schedule_panel.setLayout(schedule_layout)
        layout.addWidget(schedule_panel)

        # 将内容widget设置到滚动区域
        scroll_area.setWidget(widget)
        return scroll_area


    def update_colors_preview(self, task_colors: List[str]) -> None:
        """Update task color preview widget

        Args:
            task_colors: List of color hex codes (e.g., ["#FF5733", "#33FF57"])
        """
        # 清空旧的预览
        while self.colors_preview_widget.layout().count():
            item = self.colors_preview_widget.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 添加颜色预览（最多显示6个）
        for color in task_colors[:6]:
            color_label = QLabel()
            color_label.setFixedSize(18, 18)
            color_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {color};
                    border: 1px solid #CCC;
                    border-radius: 9px;
                }}
            """)
            self.colors_preview_widget.layout().addWidget(color_label)
        
        self.colors_preview_widget.layout().addStretch()


    def apply_selected_theme_silent(self) -> None:
        """Apply selected theme silently without showing notification

        Used during initialization to avoid redundant user notifications.
        """
        if not self.selected_theme_id:
            return
        
        if not self.theme_manager:
            return  # 主题管理器未初始化，静默失败
        
        # 应用预设主题
        success = self.theme_manager.apply_preset_theme(self.selected_theme_id)
        if success:
            # 更新配置中的主题模式（强制设置为preset）
            self.config.setdefault('theme', {})['mode'] = 'preset'
            self.config.setdefault('theme', {})['current_theme_id'] = self.selected_theme_id
            
            # 立即保存配置（确保主题设置持久化）
            # 使用防抖动保存（主题切换通常是单次操作，但防抖动可以防止快速切换时的多次写入）
            self.config_debouncer.save_debounced(self.config)

    def apply_selected_theme(self) -> None:
        """Apply selected theme with user notification

        Shows confirmation message after theme is successfully applied.
        """
        if not self.theme_manager:
            QMessageBox.warning(self, self.i18n.tr("membership.payment.error"), "主题管理器未初始化，请稍后再试")
            return
        
        # 从下拉框获取当前选中的主题ID
        if hasattr(self, 'theme_combo'):
            index = self.theme_combo.currentIndex()
            if index >= 0:
                theme_id = self.theme_combo.itemData(index)
                if theme_id:
                    self.selected_theme_id = theme_id
        
        if not self.selected_theme_id:
            QMessageBox.warning(self, self.i18n.tr("message.info"), "请先选择一个主题")
            return

        # 应用预设主题
        success = self.theme_manager.apply_preset_theme(self.selected_theme_id)
        if success:
            QMessageBox.information(self, "成功", self.i18n.tr("config.dialogs.theme_applied", theme_name=self.theme_manager.get_current_theme().get('name', 'Unknown')))
            # 更新配置中的主题模式
            self.config.setdefault('theme', {})['mode'] = 'preset'
            self.config.setdefault('theme', {})['current_theme_id'] = self.selected_theme_id
        else:
            QMessageBox.warning(self, self.i18n.tr("membership.payment.error"), "应用主题失败")

    def apply_theme_colors_to_tasks(self):
        """应用主题配色到任务"""
        if not self.theme_manager:
            QMessageBox.warning(self, self.i18n.tr("membership.payment.error"), "主题管理器未初始化，请稍后再试")
            return
        
        theme = self.theme_manager.get_current_theme()
        if not theme:
            QMessageBox.warning(self, self.i18n.tr("message.info"), "请先选择一个主题")
            return

        # 确认对话框
        reply = QMessageBox.question(
            self,
            "确认",
            "确定要将当前主题的配色应用到所有任务吗？\n这将覆盖现有的任务颜色。",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # 应用主题配色
            adapted_tasks = self.theme_manager.adapt_task_colors(
                self.tasks,
                theme,
                apply_theme_colors=True
            )
            
            # 更新任务列表
            self.tasks = adapted_tasks
            
            # 更新任务表格和编辑器
            if hasattr(self, 'load_tasks_to_table'):
                self.load_tasks_to_table()
            if hasattr(self, 'timeline_editor') and self.timeline_editor:
                QTimer.singleShot(50, lambda: self.timeline_editor.set_tasks(self.tasks) if self.timeline_editor else None)
            
            QMessageBox.information(self, self.i18n.tr("message.success"), "已应用主题配色到任务")

    def _load_preset_themes(self):
        """加载预设主题列表到下拉框"""
        if not hasattr(self, 'theme_combo'):
            return

        # 初始化主题管理器（如果还未初始化）
        if not self.theme_manager:
            self._init_theme_manager()

        # 获取所有预设主题
        if not self.theme_manager:
            preset_themes = ThemeManager.DEFAULT_PRESET_THEMES.copy()
        else:
            all_themes = self.theme_manager.get_all_themes()
            preset_themes = all_themes.get('preset_themes', {})

        # 当前选中的主题ID（从config中获取）
        theme_config = self.config.get('theme', {})
        current_theme_id = theme_config.get('current_theme_id', 'business')
        self.selected_theme_id = current_theme_id

        # 填充下拉框
        self.theme_combo.clear()
        for theme_id, theme_data in preset_themes.items():
            theme_name = theme_data.get('name', theme_id)
            self.theme_combo.addItem(theme_name, theme_id)

        # 设置当前选中项
        index = self.theme_combo.findData(current_theme_id)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

        # 初始化配色预览
        if current_theme_id in preset_themes:
            task_colors = preset_themes[current_theme_id].get('task_colors', [])
            if hasattr(self, 'colors_preview_widget'):
                self.update_colors_preview(task_colors)

    def on_preset_theme_changed_with_preview(self, index):
        """预设主题切换时的处理（带实时预览）"""
        if index < 0:
            return

        theme_id = self.theme_combo.itemData(index)
        if not theme_id:
            return

        self.selected_theme_id = theme_id

        # 获取主题数据
        if not self.theme_manager:
            preset_themes = ThemeManager.DEFAULT_PRESET_THEMES.copy()
        else:
            all_themes = self.theme_manager.get_all_themes()
            preset_themes = all_themes.get('preset_themes', {})

        theme_data = preset_themes.get(theme_id, {})
        task_colors = theme_data.get('task_colors', [])

        # 更新配色预览
        if hasattr(self, 'colors_preview_widget'):
            self.update_colors_preview(task_colors)

        # 实时更新时间轴编辑器预览（不修改实际任务数据）
        if hasattr(self, 'timeline_editor') and self.timeline_editor:
            # 创建临时任务列表，应用主题配色
            temp_tasks = []
            for i, task in enumerate(self.tasks):
                temp_task = task.copy()
                # 循环应用主题配色
                if task_colors:
                    color_index = i % len(task_colors)
                    temp_task['color'] = task_colors[color_index]
                temp_tasks.append(temp_task)

            # 更新时间轴编辑器显示（仅预览，不保存）
            QTimer.singleShot(50, lambda: self.timeline_editor.set_tasks(temp_tasks) if self.timeline_editor else None)


    def create_scene_tab(self):
        """创建场景设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 说明标签
        info_label = QLabel(self.i18n.tr("config.config_4"))
        info_label.setStyleSheet("color: #333333; font-style: italic; padding: 5px;")
        layout.addWidget(info_label)

        # 基础设置组
        basic_group = QGroupBox("⚙️ " + self.i18n.tr("config.scene.basic_settings"))
        basic_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        basic_layout = QFormLayout()
        basic_layout.setVerticalSpacing(12)

        # 启用场景系统
        self.scene_enabled_check = QCheckBox(self.i18n.tr("general.text_9791"))
        scene_config = self.config.get('scene', {})
        self.scene_enabled_check.setChecked(scene_config.get('enabled', False))
        self.scene_enabled_check.setMinimumHeight(36)
        self.scene_enabled_check.setStyleSheet("font-weight: bold;")
        basic_layout.addRow(self.scene_enabled_check)

        # 依然展示进度条
        self.show_progress_in_scene_check = QCheckBox(self.i18n.tr("general.text_889"))
        self.show_progress_in_scene_check.setChecked(scene_config.get('show_progress_bar', False))
        self.show_progress_in_scene_check.setMinimumHeight(36)
        self.show_progress_in_scene_check.setToolTip(self.i18n.tr("general.display_1"))
        basic_layout.addRow(self.show_progress_in_scene_check)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # 场景选择组
        scene_select_group = QGroupBox("🎬 " + self.i18n.tr("config.scene.scene_selection"))
        scene_select_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        scene_select_layout = QVBoxLayout()
        scene_select_layout.setSpacing(10)

        # 场景选择下拉框
        scene_combo_layout = QHBoxLayout()
        scene_label = QLabel(self.i18n.tr("general.text_5026"))
        scene_label.setStyleSheet("font-weight: bold;")
        scene_combo_layout.addWidget(scene_label)

        self.scene_combo = QComboBox()
        self.scene_combo.setMinimumHeight(36)
        self.scene_combo.setStyleSheet("""
            QComboBox {
                padding: 5px 10px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #888888;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)

        # 从main_window的scene_manager加载场景列表
        if hasattr(self, 'main_window') and hasattr(self.main_window, 'scene_manager'):
            scene_manager = self.main_window.scene_manager
            scene_list = scene_manager.get_scene_list()

            # 添加"无场景"选项
            self.scene_combo.addItem(self.i18n.tr("general.text_6942"), None)

            # 添加所有可用场景
            for scene_name in scene_list:
                metadata = scene_manager.get_scene_metadata(scene_name)
                if metadata:
                    display_name = metadata.get('name', scene_name)
                    self.scene_combo.addItem(display_name, scene_name)

            # 设置当前选中的场景
            current_scene = scene_config.get('current_scene')
            if current_scene:
                index = self.scene_combo.findData(current_scene)
                if index >= 0:
                    self.scene_combo.setCurrentIndex(index)
        else:
            self.scene_combo.addItem(self.i18n.tr("general.text_1681"), None)
            self.scene_combo.setEnabled(False)

        # 连接场景切换事件
        self.scene_combo.currentIndexChanged.connect(self.on_scene_changed)

        scene_combo_layout.addWidget(self.scene_combo)

        # 添加刷新按钮
        refresh_button = QPushButton(self.i18n.tr("menu.refresh_scene"))
        refresh_button.setMinimumHeight(36)
        refresh_button.setStyleSheet("""
            QPushButton {
                padding: 5px 15px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
                color: #333333;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                border-color: #888888;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
            }
        """)
        refresh_button.clicked.connect(self._refresh_scene_list)
        refresh_button.setToolTip(self.i18n.tr("general.text_7449"))
        scene_combo_layout.addWidget(refresh_button)

        scene_combo_layout.addStretch()
        scene_select_layout.addLayout(scene_combo_layout)

        # 场景描述
        self.scene_description_label = QLabel(self.i18n.tr("dialog.text_7655"))
        self.scene_description_label.setStyleSheet("color: #666666; padding: 5px; font-style: italic;")
        self.scene_description_label.setWordWrap(True)
        scene_select_layout.addWidget(self.scene_description_label)

        # 更新场景描述
        self.update_scene_description()

        scene_select_group.setLayout(scene_select_layout)
        layout.addWidget(scene_select_group)

        # 高级功能组
        advanced_group = QGroupBox("🛠️ " + self.i18n.tr("config.scene.advanced_features"))
        advanced_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        advanced_layout = QVBoxLayout()
        advanced_layout.setSpacing(10)

        # 打开场景编辑器按钮
        editor_btn_layout = QHBoxLayout()
        self.open_scene_editor_btn = QPushButton(self.i18n.tr("general.text_1288"))
        self.open_scene_editor_btn.setMinimumHeight(40)
        self.open_scene_editor_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.open_scene_editor_btn.clicked.connect(self.open_scene_editor)
        editor_btn_layout.addWidget(self.open_scene_editor_btn)
        editor_btn_layout.addStretch()
        advanced_layout.addLayout(editor_btn_layout)

        # 编辑器说明
        editor_hint = QLabel(self.i18n.tr("general.text_3998"))
        editor_hint.setStyleSheet("color: #888888; padding: 5px; font-size: 9pt;")
        advanced_layout.addWidget(editor_hint)

        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)

        # 添加弹簧,将内容推到顶部
        layout.addStretch()

        return widget

    def on_scene_changed(self, index):
        """场景选择改变时的处理"""
        self.update_scene_description()

    def update_scene_description(self):
        """更新场景描述信息"""
        if not hasattr(self, 'scene_combo') or not hasattr(self, 'scene_description_label'):
            return

        index = self.scene_combo.currentIndex()
        if index < 0:
            return

        scene_name = self.scene_combo.itemData(index)

        if not scene_name:
            self.scene_description_label.setText(self.i18n.tr("dialog.display"))
            return

        # 获取场景元数据
        if hasattr(self, 'main_window') and hasattr(self.main_window, 'scene_manager'):
            scene_manager = self.main_window.scene_manager
            metadata = scene_manager.get_scene_metadata(scene_name)

            if metadata:
                description = metadata.get('description', '无描述')
                version = metadata.get('version', '1.0')
                author = metadata.get('author', '未知')

                desc_text = f"描述: {description}\n版本: {version}  作者: {author}"
                self.scene_description_label.setText(desc_text)
            else:
                self.scene_description_label.setText(self.i18n.tr("general.text_8358"))
        else:
            self.scene_description_label.setText(self.i18n.tr("general.text_7526"))

    def open_scene_editor(self):
        """打开场景编辑器"""
        try:
            # 如果编辑器已打开,激活窗口
            if self.scene_editor_window is not None:
                self.scene_editor_window.show()
                self.scene_editor_window.activateWindow()
                self.scene_editor_window.raise_()
                return

            # 创建新的编辑器窗口
            self.scene_editor_window = SceneEditorWindow()

            # 连接窗口关闭信号,刷新场景列表
            self.scene_editor_window.editor_closed.connect(self._on_scene_editor_closed)
            # 连接窗口销毁信号,清理引用
            self.scene_editor_window.destroyed.connect(lambda: setattr(self, 'scene_editor_window', None))

            # 显示编辑器
            self.scene_editor_window.show()

            logging.info("场景编辑器已打开")

        except Exception as e:
            logging.error(f"打开场景编辑器失败: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "错误",
                f"打开场景编辑器失败:\n{str(e)}\n\n请检查日志文件获取详细信息"
            )

    def _on_scene_editor_closed(self):
        """场景编辑器窗口关闭时的处理"""
        self.scene_editor_window = None
        logging.info("场景编辑器已关闭")

        # 刷新场景列表(用户可能在编辑器中创建了新场景)
        if hasattr(self, 'scene_combo') and self.scene_combo:
            self._refresh_scene_list()

    def _refresh_scene_list(self):
        """刷新场景选择下拉框"""
        if not hasattr(self, 'scene_combo') or not self.scene_combo:
            return

        try:
            # 保存当前选中的场景
            current_scene = self.scene_combo.itemData(self.scene_combo.currentIndex())

            # 清空下拉框
            self.scene_combo.clear()

            # 重新加载场景列表
            if hasattr(self, 'main_window') and hasattr(self.main_window, 'scene_manager'):
                scene_manager = self.main_window.scene_manager

                # 重新扫描场景目录
                scene_manager.scan_scenes()
                scene_list = scene_manager.get_scene_list()

                # 添加"无场景"选项
                self.scene_combo.addItem(self.i18n.tr("general.text_6942"), None)

                # 添加所有可用场景
                for scene_name in scene_list:
                    metadata = scene_manager.get_scene_metadata(scene_name)
                    if metadata:
                        display_name = metadata.get('name', scene_name)
                        self.scene_combo.addItem(display_name, scene_name)

                # 恢复之前选中的场景
                if current_scene:
                    index = self.scene_combo.findData(current_scene)
                    if index >= 0:
                        self.scene_combo.setCurrentIndex(index)

                # 更新场景描述（必须在日志之前，确保combo box状态稳定）
                self.update_scene_description()

                logging.info(f"场景列表已刷新,共 {len(scene_list)} 个场景")
        except Exception as e:
            logging.error(f"刷新场景列表失败: {e}", exc_info=True)
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "刷新失败",
                f"刷新场景列表时出错:\n{e}"
            )

    def create_notification_tab(self):
        """创建通知设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 说明标签
        info_label = QLabel(self.i18n.tr("config.config_5"))
        info_label.setStyleSheet("color: #333333; font-style: italic; padding: 5px;")
        layout.addWidget(info_label)

        # 基础设置组
        basic_group = QGroupBox("⚙️ " + self.i18n.tr("config.notifications.basic_settings"))
        basic_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        basic_layout = QFormLayout()

        # 启用通知
        self.notify_enabled_check = QCheckBox(self.i18n.tr("notification.enable_notifications"))
        notification_config = self.config.get('notification', {})
        self.notify_enabled_check.setChecked(notification_config.get('enabled', True))
        self.notify_enabled_check.setMinimumHeight(36)
        self.notify_enabled_check.setStyleSheet("font-weight: bold;")
        basic_layout.addRow(self.notify_enabled_check)

        # 启用声音
        self.notify_sound_check = QCheckBox(self.i18n.tr("message.text_1045"))
        self.notify_sound_check.setChecked(notification_config.get('sound_enabled', True))
        self.notify_sound_check.setMinimumHeight(36)
        basic_layout.addRow(self.notify_sound_check)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # 提醒时机设置组
        timing_group = QGroupBox("⏰ " + self.i18n.tr("config.notifications.timing"))
        timing_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        timing_layout = QVBoxLayout()
        timing_layout.setSpacing(15)  # 设置子元素之间的间距

        # 任务开始前提醒
        before_start_group = QGroupBox("🔔 " + self.i18n.tr("config.notifications.before_start"))
        before_start_group.setStyleSheet("""
            QGroupBox {
                margin-bottom: 10px;
            }
            QGroupBox::title {
                color: #333333;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        before_start_group.setMinimumHeight(110)
        before_start_layout = QVBoxLayout()
        before_start_layout.setSpacing(8)
        before_start_layout.setContentsMargins(10, 15, 10, 10)

        # 标题行布局：提示文本 + "任务开始时提醒"复选框
        before_start_title_row = QHBoxLayout()
        before_start_hint = QLabel(self.i18n.tr("notification.before_start_hint"))
        before_start_hint.setStyleSheet("color: #888888; font-size: 9pt;")
        before_start_title_row.addWidget(before_start_hint)

        before_start_title_row.addStretch()

        # "任务开始时提醒"复选框放在右侧
        self.notify_on_start_check = QCheckBox(self.i18n.tr("notification.notify_at_start"))
        self.notify_on_start_check.setChecked(notification_config.get('on_start', True))
        self.notify_on_start_check.setMinimumHeight(36)
        before_start_title_row.addWidget(self.notify_on_start_check)

        before_start_layout.addLayout(before_start_title_row)

        before_start_minutes = notification_config.get('before_start_minutes', [10, 5])

        # 提前提醒选项
        before_start_checkboxes_layout = QHBoxLayout()
        self.notify_before_start_checks = {}

        for minutes in [30, 15, 10, 5]:
            checkbox = QCheckBox(self.i18n.tr("general.text_9462", minutes=minutes))
            checkbox.setChecked(minutes in before_start_minutes)
            checkbox.setMinimumHeight(36)
            self.notify_before_start_checks[minutes] = checkbox
            before_start_checkboxes_layout.addWidget(checkbox)

        before_start_checkboxes_layout.addStretch()
        before_start_layout.addLayout(before_start_checkboxes_layout)

        before_start_group.setLayout(before_start_layout)
        timing_layout.addWidget(before_start_group)

        # 任务结束前提醒
        before_end_group = QGroupBox("🔕 " + self.i18n.tr("config.notifications.before_end"))
        before_end_group.setStyleSheet("""
            QGroupBox {
                margin-bottom: 10px;
            }
            QGroupBox::title {
                color: #333333;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        before_end_group.setMinimumHeight(110)
        before_end_layout = QVBoxLayout()
        before_end_layout.setSpacing(8)
        before_end_layout.setContentsMargins(10, 15, 10, 10)

        # 标题行布局：提示文本 + "任务结束时提醒"复选框
        before_end_title_row = QHBoxLayout()
        before_end_hint = QLabel(self.i18n.tr("notification.before_end_hint"))
        before_end_hint.setStyleSheet("color: #888888; font-size: 9pt;")
        before_end_title_row.addWidget(before_end_hint)

        before_end_title_row.addStretch()

        # "任务结束时提醒"复选框放在右侧
        self.notify_on_end_check = QCheckBox(self.i18n.tr("notification.notify_at_end"))
        self.notify_on_end_check.setChecked(notification_config.get('on_end', False))
        self.notify_on_end_check.setMinimumHeight(36)
        before_end_title_row.addWidget(self.notify_on_end_check)

        before_end_layout.addLayout(before_end_title_row)

        before_end_minutes = notification_config.get('before_end_minutes', [5])

        before_end_checkboxes_layout = QHBoxLayout()
        self.notify_before_end_checks = {}

        for minutes in [10, 5, 3]:
            checkbox = QCheckBox(self.i18n.tr("general.text_9462", minutes=minutes))
            checkbox.setChecked(minutes in before_end_minutes)
            checkbox.setMinimumHeight(36)
            self.notify_before_end_checks[minutes] = checkbox
            before_end_checkboxes_layout.addWidget(checkbox)

        before_end_checkboxes_layout.addStretch()
        before_end_layout.addLayout(before_end_checkboxes_layout)

        before_end_group.setLayout(before_end_layout)
        timing_layout.addWidget(before_end_group)

        timing_group.setLayout(timing_layout)
        layout.addWidget(timing_group)

        # 免打扰时段设置组
        quiet_group = QGroupBox("🌙 " + self.i18n.tr("config.notifications.dnd_title"))
        quiet_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        quiet_layout = QFormLayout()

        quiet_hours = notification_config.get('quiet_hours', {})

        # 启用免打扰
        self.quiet_enabled_check = QCheckBox(self.i18n.tr("general.text_1681_1"))
        self.quiet_enabled_check.setChecked(quiet_hours.get('enabled', False))
        self.quiet_enabled_check.setMinimumHeight(36)
        quiet_layout.addRow(self.quiet_enabled_check)

        # 免打扰开始时间
        quiet_start_layout = QHBoxLayout()
        self.quiet_start_time = QTimeEdit()
        self.quiet_start_time.setStyleSheet(StyleManager.input_time())
        self.quiet_start_time.setDisplayFormat("HH:mm")
        self.quiet_start_time.setFixedHeight(36)
        start_time_str = quiet_hours.get('start', '22:00')
        self.quiet_start_time.setTime(QTime.fromString(start_time_str, "HH:mm"))
        quiet_start_layout.addWidget(self.quiet_start_time)
        quiet_start_hint = QLabel(self.i18n.tr("notification.after_time_hint"))
        quiet_start_hint.setStyleSheet("color: #888888; font-size: 9pt;")
        quiet_start_layout.addWidget(quiet_start_hint)
        quiet_start_layout.addStretch()
        quiet_layout.addRow(self.i18n.tr("config.notifications.dnd_start") + ":", quiet_start_layout)

        # 免打扰结束时间
        quiet_end_layout = QHBoxLayout()
        self.quiet_end_time = QTimeEdit()
        self.quiet_end_time.setStyleSheet(StyleManager.input_time())
        self.quiet_end_time.setDisplayFormat("HH:mm")
        self.quiet_end_time.setFixedHeight(36)
        end_time_str = quiet_hours.get('end', '08:00')
        self.quiet_end_time.setTime(QTime.fromString(end_time_str, "HH:mm"))
        quiet_end_layout.addWidget(self.quiet_end_time)
        quiet_end_hint = QLabel(self.i18n.tr("notification.before_time_hint"))
        quiet_end_hint.setStyleSheet("color: #888888; font-size: 9pt;")
        quiet_end_layout.addWidget(quiet_end_hint)
        quiet_end_layout.addStretch()
        quiet_layout.addRow(self.i18n.tr("config.notifications.dnd_end") + ":", quiet_end_layout)

        quiet_example = QLabel(self.i18n.tr("general.text_1040"))
        quiet_example.setStyleSheet("color: #888888; font-size: 8pt; font-style: italic;")
        quiet_layout.addRow(quiet_example)

        quiet_group.setLayout(quiet_layout)
        layout.addWidget(quiet_group)

        layout.addStretch()
        return widget

    def create_behavior_tab(self):
        """创建行为识别标签页 - 整合应用分类管理和弹幕行为识别配置"""
        from PySide6.QtWidgets import QScrollArea, QSplitter

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title_label = QLabel("🔍 行为识别设置")
        title_font = title_label.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        # 创建水平分割器
        splitter = QSplitter(Qt.Horizontal)

        # === 左侧面板：基本设置和弹幕配置 ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(15)

        # 1. 基本设置组
        basic_group = QGroupBox("⚙️ 基本设置")
        basic_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        basic_layout = QFormLayout(basic_group)
        basic_layout.setSpacing(10)

        # 启用行为追踪 (旧的activity_tracking)
        activity_config = self.config.get('activity_tracking', {})
        self.activity_tracking_enabled = QCheckBox("启用应用活动追踪")
        self.activity_tracking_enabled.setChecked(activity_config.get('enabled', False))
        self.activity_tracking_enabled.setMinimumHeight(36)
        basic_layout.addRow("行为追踪:", self.activity_tracking_enabled)

        # 采样间隔
        self.activity_polling_interval = QSpinBox()
        self.activity_polling_interval.setRange(1, 60)
        self.activity_polling_interval.setSuffix(" 秒")
        self.activity_polling_interval.setValue(activity_config.get('polling_interval', 5))
        self.activity_polling_interval.setMinimumHeight(36)
        basic_layout.addRow("采样间隔:", self.activity_polling_interval)

        # 数据保留天数
        self.activity_retention_days = QSpinBox()
        self.activity_retention_days.setRange(7, 365)
        self.activity_retention_days.setSuffix(" 天")
        self.activity_retention_days.setValue(activity_config.get('data_retention_days', 90))
        self.activity_retention_days.setMinimumHeight(36)
        basic_layout.addRow("数据保留:", self.activity_retention_days)

        left_layout.addWidget(basic_group)

        # 2. 弹幕行为识别组
        behavior_group = QGroupBox("💬 弹幕行为识别")
        behavior_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        behavior_layout = QFormLayout(behavior_group)
        behavior_layout.setSpacing(10)

        # 获取 behavior_recognition 配置
        behavior_config = self.config.get('behavior_recognition', {})

        # 启用弹幕行为识别
        self.behavior_danmaku_enabled = QCheckBox("启用行为感知弹幕")
        self.behavior_danmaku_enabled.setChecked(behavior_config.get('enabled', False))
        self.behavior_danmaku_enabled.setMinimumHeight(36)
        behavior_layout.addRow("弹幕识别:", self.behavior_danmaku_enabled)

        # 采集间隔
        self.behavior_collection_interval = QSpinBox()
        self.behavior_collection_interval.setRange(1, 60)
        self.behavior_collection_interval.setSuffix(" 秒")
        self.behavior_collection_interval.setValue(behavior_config.get('collection_interval', 5))
        self.behavior_collection_interval.setMinimumHeight(36)
        behavior_layout.addRow("采集间隔:", self.behavior_collection_interval)

        # 触发概率
        self.behavior_trigger_probability = QDoubleSpinBox()
        self.behavior_trigger_probability.setRange(0.0, 1.0)
        self.behavior_trigger_probability.setSingleStep(0.1)
        self.behavior_trigger_probability.setDecimals(2)
        self.behavior_trigger_probability.setValue(behavior_config.get('trigger_probability', 0.4))
        self.behavior_trigger_probability.setMinimumHeight(36)
        behavior_layout.addRow("触发概率:", self.behavior_trigger_probability)

        # 全局冷却
        self.behavior_global_cooldown = QSpinBox()
        self.behavior_global_cooldown.setRange(5, 300)
        self.behavior_global_cooldown.setSuffix(" 秒")
        self.behavior_global_cooldown.setValue(behavior_config.get('global_cooldown', 30))
        self.behavior_global_cooldown.setMinimumHeight(36)
        behavior_layout.addRow("全局冷却:", self.behavior_global_cooldown)

        # 分类冷却
        self.behavior_category_cooldown = QSpinBox()
        self.behavior_category_cooldown.setRange(10, 600)
        self.behavior_category_cooldown.setSuffix(" 秒")
        self.behavior_category_cooldown.setValue(behavior_config.get('category_cooldown', 60))
        self.behavior_category_cooldown.setMinimumHeight(36)
        behavior_layout.addRow("分类冷却:", self.behavior_category_cooldown)

        left_layout.addWidget(behavior_group)

        # 3. 帮助说明
        help_group = QGroupBox("💡 使用说明")
        help_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        help_layout = QVBoxLayout(help_group)

        help_text = QLabel(
            "• <b>行为追踪</b>: 记录您使用各个应用的时间\n"
            "• <b>弹幕识别</b>: 根据行为模式智能触发弹幕\n"
            "• <b>采样间隔</b>: 检测活动的时间间隔\n"
            "• <b>触发概率</b>: 控制弹幕出现频率(0.0-1.0)\n"
            "• <b>冷却时间</b>: 避免弹幕过度频繁\n"
            "• 所有数据仅存储在本地,不会上传云端"
        )
        help_text.setWordWrap(True)
        help_text.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 12px;
                line-height: 1.6;
            }
        """)
        help_layout.addWidget(help_text)

        left_layout.addWidget(help_group)
        left_layout.addStretch()

        # === 右侧面板：应用分类管理 ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(10)

        # 标题
        app_title = QLabel("📱 应用分类管理")
        app_title_font = app_title.font()
        app_title_font.setPointSize(13)
        app_title_font.setBold(True)
        app_title.setFont(app_title_font)
        app_title.setStyleSheet("color: #2c3e50;")
        right_layout.addWidget(app_title)

        # 提示
        app_hint = QLabel("设置应用的生产力分类,用于统计和行为分析")
        app_hint.setStyleSheet("color: #7f8c8d; font-size: 10pt;")
        right_layout.addWidget(app_hint)

        # 使用 ActivitySettingsWindow 的内容
        # 由于 ActivitySettingsWindow 是独立窗口,这里直接创建一个简化版
        # 或者在 save_all() 方法中打开 ActivitySettingsWindow

        app_settings_button = QPushButton("🔧 打开应用分类设置")
        app_settings_button.setMinimumHeight(44)
        app_settings_button.setStyleSheet(StyleManager.button_primary())
        app_settings_button.clicked.connect(self.open_activity_settings_window)
        right_layout.addWidget(app_settings_button)

        # 添加间距
        right_layout.addSpacing(20)

        # === 快速访问区域 ===
        access_group = QGroupBox("📊 快速访问")
        access_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        access_layout = QVBoxLayout(access_group)
        access_layout.setSpacing(10)

        # 查看今日回放按钮
        today_replay_button = QPushButton("📊 查看今日回放")
        today_replay_button.setMinimumHeight(40)
        today_replay_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        today_replay_button.clicked.connect(self.open_today_replay_window)
        access_layout.addWidget(today_replay_button)

        # 查看统计报告按钮
        stats_report_button = QPushButton("📈 查看统计报告")
        stats_report_button.setMinimumHeight(40)
        stats_report_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        stats_report_button.clicked.connect(self.open_stats_report_window)
        access_layout.addWidget(stats_report_button)

        right_layout.addWidget(access_group)
        right_layout.addStretch()

        # 添加到分割器
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 300])  # 设置初始比例

        main_layout.addWidget(splitter)

        scroll_area.setWidget(content_widget)
        return scroll_area

    def open_activity_settings_window(self):
        """打开应用分类设置窗口"""
        try:
            from gaiya.ui.activity_settings_window import ActivitySettingsWindow

            # 创建窗口
            settings_window = ActivitySettingsWindow(self)

            # 连接信号 - 当设置更改时更新统计信息
            settings_window.settings_changed.connect(lambda: logging.info("应用分类设置已更改"))
            settings_window.settings_changed.connect(self.update_behavior_stats)

            # 显示窗口
            settings_window.exec()

        except Exception as e:
            logging.error(f"打开应用分类设置窗口失败: {e}")
            QMessageBox.critical(self, "错误", f"打开应用分类设置窗口失败: {e}")

    def open_today_replay_window(self):
        """打开今日时间回放窗口"""
        try:
            from gaiya.ui.time_review_window import TimeReviewWindow

            # 创建窗口
            replay_window = TimeReviewWindow(self)

            # 显示窗口
            replay_window.exec()

        except Exception as e:
            logging.error(f"打开今日时间回放窗口失败: {e}")
            QMessageBox.critical(self, "错误", f"打开今日时间回放窗口失败: {e}")

    def open_stats_report_window(self):
        """打开统计报告窗口"""
        try:
            # 使用保存的main_window引用,调用正确的方法名 show_statistics
            if self.main_window and hasattr(self.main_window, 'show_statistics'):
                # ❌ 不再关闭配置窗口,让两个窗口可以同时存在
                # self.close()  # 移除此行,保持配置窗口打开

                # 调用主窗口的统计报告方法 (正确的方法名是 show_statistics)
                self.main_window.show_statistics()
            else:
                QMessageBox.warning(self, "提示", "无法打开统计报告窗口,请从主界面访问")
        except Exception as e:
            logging.error(f"打开统计报告窗口失败: {e}")
            QMessageBox.critical(self, "错误", f"打开统计报告窗口失败: {e}")

    def update_behavior_stats(self):
        """更新行为识别统计信息"""
        # 注意: stats_labels已被移除,此方法保留用于向后兼容
        logging.debug("update_behavior_stats被调用,但统计显示已移除")


    def _create_account_tab(self):
        """创建个人中心标签页"""
        import logging
        from PySide6.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # 创建横向布局的头部（标题 + 用户信息）
        header_layout = QHBoxLayout()

        title_label = QLabel(tr("account.title"))
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #333333;")
        header_layout.addWidget(title_label)

        # ✅ Fix: Reuse cached AuthClient instance instead of creating new one
        # This avoids blocking UI thread with file I/O, keyring reads, and SSL setup
        if not self.auth_client:
            # Fallback: if auth_client not initialized yet, create placeholder
            email = "Loading..."
            user_tier = "free"
            logging.info("[_create_account_tab] auth_client未初始化")
        else:
            email = self.auth_client.get_user_email() or "未登录"
            user_tier = self.auth_client.get_user_tier()
            logging.info(f"[_create_account_tab] 创建个人中心tab, email={email}, user_tier={user_tier}")

        if email != "未登录":
            # 添加弹性空间，推动右侧内容到右边
            header_layout.addStretch()

            # 合并邮箱和会员等级到一行，右对齐显示
            tier_name = self.i18n.tr(f"account.tiers.{user_tier}", fallback=user_tier)
            info_label = QLabel(self.i18n.tr("account.text_7480", email=email, tier_name=tier_name))
            info_label.setStyleSheet("color: #333333; font-size: 14px;")
            header_layout.addWidget(info_label)

            # 添加刷新按钮（用于支付成功后手动刷新会员状态）
            header_layout.addSpacing(10)
            refresh_btn = QPushButton("🔄 " + self.i18n.tr("button.refresh"))
            refresh_btn.setFixedSize(100, 28)
            refresh_btn.setStyleSheet(StyleManager.button_minimal())
            refresh_btn.setToolTip(self.i18n.tr("account.refresh_tooltip"))
            refresh_btn.clicked.connect(self._on_refresh_account_clicked)
            header_layout.addWidget(refresh_btn)

            # 添加退出登录按钮
            header_layout.addSpacing(10)
            logout_btn = QPushButton(self.i18n.tr("button.logout"))
            logout_btn.setFixedSize(100, 28)  # 增加宽度以防止文字被截断
            logout_btn.setStyleSheet(StyleManager.button_minimal())
            logout_btn.clicked.connect(self._on_logout_clicked)
            header_layout.addWidget(logout_btn)

        # 将横向布局添加到主布局
        layout.addLayout(header_layout)
        layout.addSpacing(20)  # 添加间距与下方内容分隔

        if email != "未登录":
            # ✅ 会员合伙人: 隐藏套餐卡片,显示邀请函入口
            if user_tier == "lifetime":
                # 显示感谢信息
                thank_you_label = QLabel("🎉 感谢您成为 GaiYa 会员合伙人!")
                thank_you_label.setStyleSheet("color: #FF9800; font-size: 20px; font-weight: bold; margin: 20px 0;")
                thank_you_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(thank_you_label)

                layout.addSpacing(20)

                # 合伙人邀请函入口
                invitation_frame = QFrame()
                invitation_frame.setStyleSheet("""
                    QFrame {
                        background-color: #FFF3E0;
                        border: 2px solid #FF9800;
                        border-radius: 12px;
                        padding: 20px;
                    }
                """)
                invitation_layout = QVBoxLayout(invitation_frame)

                invitation_title = QLabel("📖 阅读合伙人邀请函")
                invitation_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333333;")
                invitation_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
                invitation_layout.addWidget(invitation_title)

                invitation_layout.addSpacing(10)

                invitation_desc = QLabel("了解更多合伙人权益、推荐返现机制和成长计划")
                invitation_desc.setStyleSheet("font-size: 14px; color: #666666;")
                invitation_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
                invitation_layout.addWidget(invitation_desc)

                invitation_layout.addSpacing(15)

                invitation_btn = QPushButton("📨 查看邀请函")
                invitation_btn.setFixedHeight(45)
                invitation_btn.setStyleSheet(StyleManager.button_primary())
                invitation_btn.clicked.connect(self._on_view_invitation_clicked)
                invitation_layout.addWidget(invitation_btn)

                layout.addWidget(invitation_frame)
                layout.addStretch()

            # ✅ 免费用户或付费会员(pro): 显示套餐卡片
            elif user_tier in ["free", "pro"]:
                tip_label = QLabel(self.i18n.tr("account.membership_comparison"))
                tip_label.setStyleSheet("color: #333333; font-size: 18px; font-weight: bold; margin-bottom: 15px;")
                tip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(tip_label)

                cards_layout = QHBoxLayout()
                cards_layout.setSpacing(30)  # 增加卡片间距，避免拥挤
                cards_layout.addStretch()

                # 三个套餐：月度、年度（中间突出）、会员合伙人
                plans = [
                    {
                        "id": "pro_monthly",
                        "name": self.i18n.tr("account.plan_monthly_name"),
                        "price": "¥29",
                        "period": self.i18n.tr("account.plan_period_month"),
                        "validity": self.i18n.tr("account.plan_validity_30days"),
                        "renewal": self.i18n.tr("account.plan_no_auto_renewal"),
                        "type": "monthly",
                        "features": [tr("account.feature.all_free_features_plus"), tr("account.feature.ai_quota_20_per_day"), tr("account.feature.statistics_reports"), tr("account.feature.no_watermark"), tr("account.feature.pomodoro_timer"), tr("account.feature.cloud_sync"), tr("account.feature.scene_system"), tr("account.feature.early_access"), tr("account.feature.vip_group")]
                    },
                    {
                        "id": "pro_yearly",
                        "name": self.i18n.tr("account.plan_yearly_name"),
                        "price": "¥199",
                        "period": self.i18n.tr("account.plan_period_year"),
                        "monthly_price": "¥16.6",
                        "original_price": "¥348",
                        "discount_badge": self.i18n.tr("account.plan_save_40_percent"),
                        "validity": self.i18n.tr("account.plan_validity_365days"),
                        "renewal": self.i18n.tr("account.plan_no_auto_renewal"),
                        "type": "yearly",
                        "features": [tr("account.feature.all_free_features_plus"), tr("account.feature.ai_quota_20_per_day"), tr("account.feature.statistics_reports"), tr("account.feature.no_watermark"), tr("account.feature.pomodoro_timer"), tr("account.feature.cloud_sync"), tr("account.feature.scene_system"), tr("account.feature.early_access"), tr("account.feature.vip_group")]
                    },
                    {
                        "id": "lifetime",
                        "name": self.i18n.tr("account.plan_lifetime_name"),
                        "price": "¥599",
                        "period": "",
                        "validity": self.i18n.tr("account.plan_validity_lifetime"),
                        "renewal": self.i18n.tr("account.plan_one_time_payment"),
                        "type": "lifetime",
                        "features": [tr("account.feature.all_free_features_plus"), tr("account.feature.ai_quota_50_per_day"), tr("account.feature.statistics_reports"), tr("account.feature.no_watermark"), tr("account.feature.pomodoro_timer"), tr("account.feature.cloud_sync"), tr("account.feature.scene_system"), tr("account.feature.referral_cashback"), tr("account.feature.partner_community"), tr("account.feature.priority_updates"), tr("account.feature.one_on_one_consulting"), tr("account.feature.grow_together")]
                    },
                ]

                self.plan_cards = []
                self.selected_plan_id = "pro_yearly"

                # ✅ 传递 user_tier 以便修改按钮文案
                for i, plan in enumerate(plans):
                    if plan['type'] == 'yearly':
                        card = self._create_featured_plan_card(plan, is_selected=True, user_tier=user_tier)
                    elif plan['type'] == 'lifetime':
                        card = self._create_lifetime_plan_card(plan, user_tier=user_tier)
                    else:  # monthly
                        card = self._create_regular_plan_card(plan, user_tier=user_tier)

                    cards_layout.addWidget(card)
                    self.plan_cards.append(card)

                cards_layout.addStretch()
                layout.addLayout(cards_layout)

                # 新增会员提示区域
                layout.addSpacing(30)
                tips_frame = self._create_membership_tips()
                layout.addWidget(tips_frame)

                # 新增会员方案详细对比表
                layout.addSpacing(40)
                comparison_table = self._create_comparison_table()
                layout.addWidget(comparison_table)

                # 添加支付方式选择 - 已屏蔽，默认使用微信支付
                # payment_container = QWidget()
                # payment_container.setStyleSheet("""
                #     QWidget {
                #         background-color: rgba(248, 249, 250, 0.1);
                #         border-radius: 12px;
                #         border: none;
                #     }
                # """)
                # payment_layout = QVBoxLayout(payment_container)
                # payment_layout.setContentsMargins(60, 20, 60, 20)
                # payment_layout.setSpacing(12)

                # payment_title = QLabel(self.i18n.tr("account.select_payment_method"))
                # payment_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
                # payment_title.setStyleSheet("""
                #     QLabel {
                #         color: white;
                #         font-size: 14px;
                #         font-weight: 600;
                #         background: transparent;
                #         border: none;
                #     }
                # """)
                # payment_layout.addWidget(payment_title)

                # payment_options_layout = QHBoxLayout()
                # payment_options_layout.addStretch()

                # self.payment_method_group = QButtonGroup()

                # alipay_radio = QRadioButton(self.i18n.tr("account.payment_alipay"))
                # alipay_radio.setProperty("pay_type", "alipay")
                # alipay_radio.setChecked(True)

                # # ⚠️ 关键修复：禁用焦点策略，防止Windows绘制焦点框
                # alipay_radio.setFocusPolicy(Qt.FocusPolicy.NoFocus)

                # # ⚠️ 底层修复：使用Qt属性完全禁用系统默认绘制
                # alipay_radio.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
                # alipay_radio.setAutoFillBackground(False)

                # alipay_radio.setStyleSheet("""
                #     QRadioButton {
                #         color: white;
                #         font-size: 14px;
                #         spacing: 8px;
                #         background: transparent;
                #         border: none;
                #         outline: none;
                #     }
                #     QRadioButton::indicator {
                #         width: 20px;
                #         height: 20px;
                #         border: none;
                #         outline: none;
                #     }
                #     QRadioButton::indicator:checked {
                #         background-color: #00b8a9;
                #         border: none;
                #         border-radius: 10px;
                #     }
                #     QRadioButton::indicator:unchecked {
                #         background-color: rgba(51, 51, 51, 0.08);
                #         border: 1px solid rgba(255, 255, 255, 0.15);
                #         border-radius: 10px;
                #     }
                #     QRadioButton::indicator:hover:unchecked {
                #         background-color: rgba(51, 51, 51, 0.12);
                #         border: 1px solid rgba(255, 255, 255, 0.25);
                #     }
                #     QRadioButton:focus {
                #         border: none;
                #         outline: none;
                #     }
                # """)
                # self.payment_method_group.addButton(alipay_radio)
                # payment_options_layout.addWidget(alipay_radio)

                # # 增加两个单选按钮之间的间距
                # payment_options_layout.addSpacing(20)

                # wxpay_radio = QRadioButton(self.i18n.tr("account.payment_wechat"))
                # wxpay_radio.setProperty("pay_type", "wxpay")

                # # ⚠️ 关键修复：禁用焦点策略，防止Windows绘制焦点框
                # wxpay_radio.setFocusPolicy(Qt.FocusPolicy.NoFocus)

                # # ⚠️ 底层修复：使用Qt属性完全禁用系统默认绘制
                # wxpay_radio.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
                # wxpay_radio.setAutoFillBackground(False)

                # wxpay_radio.setStyleSheet(alipay_radio.styleSheet())
                # self.payment_method_group.addButton(wxpay_radio)
                # payment_options_layout.addWidget(wxpay_radio)

                # payment_options_layout.addStretch()
                # payment_layout.addLayout(payment_options_layout)

                # layout.addSpacing(20)
                # layout.addWidget(payment_container)
                # layout.addSpacing(20)

                # "前往付费"按钮已移除 - 现在每个套餐卡片都有直接付费按钮
            else:
                info_label = QLabel(self.i18n.tr("account.thank_you"))
                info_label.setStyleSheet("color: #333333; font-size: 14px;")
                layout.addWidget(info_label)
        else:
            # 未登录状态：显示登录/注册UI
            from gaiya.ui.auth_ui import AuthDialog

            # 创建说明文字
            welcome_label = QLabel(self.i18n.tr("account.welcome_message"))
            welcome_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333333; margin-bottom: 10px;")
            welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(welcome_label)

            tip_label = QLabel(self.i18n.tr("account.text_789"))
            tip_label.setStyleSheet("color: #AAAAAA; font-size: 14px; margin-bottom: 20px;")
            tip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(tip_label)

            # 创建登录按钮
            login_button = QPushButton(self.i18n.tr("account.text_9039"))
            login_button.setFixedSize(300, 50)
            login_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                }
            """)
            login_button.clicked.connect(self._on_show_login_dialog)

            # 居中显示按钮
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            button_layout.addWidget(login_button)
            button_layout.addStretch()
            layout.addLayout(button_layout)

            layout.addSpacing(30)

            # 功能介绍
            features_label = QLabel(self.i18n.tr("account.text_8733"))
            features_label.setStyleSheet("color: #333333; font-size: 16px; font-weight: bold; margin-bottom: 15px;")
            layout.addWidget(features_label)

            features = [
                "• 免费用户：每天 3 次 AI智能规划配额",
                "• Pro会员：每天 20 次 AI智能规划配额",
                "• 数据云同步：自定义模板和历史统计同步到云端",
                "• 模板自动应用：根据日期规则自动切换任务模板",
                "• 优先获取新功能和更新",
                "• 加入专属VIP会员群，获取更多支持"
            ]

            for feature_text in features:
                feature_label = QLabel(feature_text)
                feature_label.setStyleSheet("color: #555555; font-size: 14px; margin: 5px 0px;")
                layout.addWidget(feature_label)

        layout.addStretch()
        scroll_area.setWidget(content_widget)
        return scroll_area

    def _on_show_login_dialog(self):
        """显示登录/注册对话框"""
        from gaiya.ui.auth_ui import AuthDialog

        # 创建登录对话框
        dialog = AuthDialog(self, self.auth_client if hasattr(self, 'auth_client') else None)

        # 连接登录成功信号
        dialog.login_success.connect(self._on_login_success)

        # 显示对话框
        dialog.exec()

    def _on_login_success(self, user_info):
        """处理登录成功"""
        from PySide6.QtWidgets import QMessageBox

        # 根据用户等级显示不同的提示
        user_tier = user_info.get('user_tier', 'free')
        if user_tier == 'free':
            tier_message = "您当前是免费用户。升级高级版可解锁更多功能。"
        elif user_tier == 'premium':
            tier_message = "您是高级版用户，可以使用所有功能。"
        elif user_tier == 'lifetime':
            tier_message = "您是终身会员，尊享所有高级功能。"
        else:
            tier_message = "您的账户信息已更新。"

        # 显示成功提示
        QMessageBox.information(
            self,
            "登录成功",
            self.i18n.tr("config.membership.welcome_back", user_email=user_info.get('email', 'User')) + "\n"
            f"{tier_message}"
        )

        # 重新加载个人中心tab以显示登录后的内容
        self.account_tab_widget = None
        self._load_account_tab()

        # ⚠️ 关键修复：登录成功后需要更新AI客户端的user_tier并刷新配额
        if hasattr(self, 'ai_client') and self.ai_client:
            # 同步更新ai_client的user_tier
            self.ai_client.user_tier = user_tier
            logging.info(f"[LOGIN] 已更新ai_client.user_tier: {user_tier}")

        # 刷新任务管理tab中的配额显示
        if hasattr(self, 'quota_label'):
            logging.info("[LOGIN] 刷新任务管理tab中的配额显示")
            self.refresh_quota_status_async()

    def _on_refresh_account_clicked(self):
        """
        处理刷新账户按钮点击

        ⚠️ 关键功能：用于支付成功后手动刷新会员状态
        流程：
        1. 调用后端API获取最新订阅状态
        2. 更新本地缓存的用户信息
        3. 重新加载个人中心页面显示最新状态
        """
        from PySide6.QtWidgets import QMessageBox
        from gaiya.core.auth_client import AuthClient
        from gaiya.core.async_worker import AsyncNetworkWorker
        import logging

        logging.info("[ACCOUNT] 用户手动刷新会员状态...")

        # 显示加载提示
        loading_dialog = QMessageBox(self)
        loading_dialog.setWindowTitle("刷新中")
        loading_dialog.setText("正在刷新会员状态,请稍候...")
        loading_dialog.setStandardButtons(QMessageBox.StandardButton.NoButton)
        loading_dialog.setIcon(QMessageBox.Icon.Information)
        loading_dialog.show()

        # 强制刷新UI
        QApplication.processEvents()

        # ⚠️ 关键修复：必须使用self.auth_client实例,而不是创建新实例
        # 否则新实例更新的user_info不会影响self.auth_client,导致UI刷新后仍显示旧数据
        if not self.auth_client:
            logging.error("[ACCOUNT] self.auth_client未初始化,无法刷新")
            loading_dialog.close()
            QMessageBox.warning(self, "刷新失败", "认证客户端未初始化")
            return

        # 创建异步Worker获取订阅状态
        self._refresh_worker = AsyncNetworkWorker(self.auth_client.get_subscription_status)
        self._refresh_worker.success.connect(lambda result: self._on_refresh_success(result, loading_dialog))
        self._refresh_worker.error.connect(lambda error: self._on_refresh_error(error, loading_dialog))
        self._refresh_worker.start()

    def _on_refresh_success(self, result: dict, loading_dialog):
        """刷新成功回调"""
        from PySide6.QtWidgets import QMessageBox, QApplication
        import logging

        # ⚠️ 关键修复：先关闭加载对话框,确保UI更新
        loading_dialog.close()
        loading_dialog.deleteLater()  # 立即释放资源
        QApplication.processEvents()  # 强制处理UI事件,确保对话框关闭

        if result.get("success"):
            user_tier = result.get("user_tier", "free")
            is_active = result.get("is_active", False)

            logging.info(f"[ACCOUNT] 会员状态刷新成功: tier={user_tier}, active={is_active}")

            # 检查auth_client的user_info是否已更新
            if self.auth_client and self.auth_client.user_info:
                cached_tier = self.auth_client.user_info.get("user_tier", "unknown")
                logging.info(f"[ACCOUNT] 刷新前auth_client.user_info中的tier: {cached_tier}")

            # ⚠️ 关键修复：先更新AI客户端的user_tier,再刷新UI
            if hasattr(self, 'ai_client') and self.ai_client:
                self.ai_client.user_tier = user_tier
                logging.info(f"[ACCOUNT] 已更新ai_client.user_tier: {user_tier}")

            # ⚠️ 关键修复：刷新任务管理tab中的配额显示(在重新加载account_tab之前)
            if hasattr(self, 'quota_label'):
                logging.info("[ACCOUNT] 刷新任务管理tab中的配额显示")
                self.refresh_quota_status_async()

            # 重新加载个人中心tab以显示最新状态
            logging.info(f"[ACCOUNT] 准备重新加载个人中心tab")
            # 先安全地清理旧widget
            if self.account_tab_widget:
                old_widget = self.account_tab_widget
                logging.info(f"[ACCOUNT] 清理旧的account_tab_widget: {old_widget}")
                # 延迟删除旧widget,避免在使用中被删除
                old_widget.deleteLater()

            self.account_tab_widget = None
            logging.info(f"[ACCOUNT] 调用_load_account_tab()重新加载个人中心")
            self._load_account_tab()
            logging.info(f"[ACCOUNT] _load_account_tab()调用完成")

            QMessageBox.information(
                self,
                "刷新成功",
                f"会员状态已更新！\n\n当前等级: {user_tier.upper()}"
            )
        else:
            error_msg = result.get("error", "未知错误")
            logging.error(f"[ACCOUNT] 刷新失败: {error_msg}")

            QMessageBox.warning(
                self,
                "刷新失败",
                f"无法获取最新会员状态：{error_msg}\n\n请稍后重试或联系客服。"
            )

    def _on_refresh_error(self, error_msg: str, loading_dialog):
        """刷新失败回调"""
        from PySide6.QtWidgets import QMessageBox, QApplication
        import logging

        # ⚠️ 关键修复：先关闭加载对话框,确保UI更新
        loading_dialog.close()
        loading_dialog.deleteLater()  # 立即释放资源
        QApplication.processEvents()  # 强制处理UI事件,确保对话框关闭

        logging.error(f"[ACCOUNT] 刷新出错: {error_msg}")

        QMessageBox.warning(
            self,
            "刷新失败",
            f"网络错误：{error_msg}\n\n请检查网络连接后重试。"
        )

    def _on_logout_clicked(self):
        """处理退出登录按钮点击"""
        from PySide6.QtWidgets import QMessageBox

        # 确认对话框
        reply = QMessageBox.question(
            self,
            "确认退出",
            "确定要退出当前账号吗？\n\n退出后将以游客身份继续使用，免费用户功能将受到限制。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # ✅ 性能优化: 使用异步Worker避免UI卡顿
            from gaiya.core.auth_client import AuthClient
            from gaiya.core.async_worker import AsyncNetworkWorker

            auth_client = AuthClient()

            # 创建异步Worker
            self._logout_worker = AsyncNetworkWorker(auth_client.signout)
            self._logout_worker.success.connect(self._on_logout_success)
            self._logout_worker.error.connect(self._on_logout_error)
            self._logout_worker.start()

    def _on_logout_success(self, result: dict):
        """登出成功回调"""
        from PySide6.QtWidgets import QMessageBox

        # 提示用户
        QMessageBox.information(
            self,
            "退出成功",
            "已退出当前账号。\n\n请重新启动应用以切换到游客模式。"
        )

        # 关闭配置管理器
        self.close()

    def _on_logout_error(self, error_msg: str):
        """登出失败回调(实际上本地Token已清除,仍然提示成功)"""
        from PySide6.QtWidgets import QMessageBox

        # 即使失败也提示成功（因为本地Token已清除）
        QMessageBox.information(
            self,
            "退出成功",
            "已退出当前账号。\n\n请重新启动应用以切换到游客模式。"
        )
        self.close()

    def _on_view_invitation_clicked(self):
        """处理查看合伙人邀请函按钮点击"""
        from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QTextBrowser, QPushButton

        # 创建自定义对话框显示邀请函内容
        dialog = QDialog(self)
        dialog.setWindowTitle("GaiYa 会员合伙人邀请函")
        dialog.setMinimumSize(600, 500)

        layout = QVBoxLayout(dialog)

        # 使用 QTextBrowser 显示富文本内容
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)
        text_browser.setHtml("""
            <h2 style="color: #FF9800; text-align: center;">🎉 欢迎成为 GaiYa 会员合伙人</h2>
            <hr>
            <h3>🌟 专属权益</h3>
            <ul>
                <li><strong>所有高级版功能</strong> - 无限制使用所有 Pro 功能</li>
                <li><strong>50次/天 AI智能规划</strong> - 超大额度,满足高频使用</li>
                <li><strong>终身免费更新</strong> - 一次购买,永久享受</li>
                <li><strong>优先客服支持</strong> - 专属客服通道</li>
                <li><strong>未来新功能抢先体验</strong> - 新功能优先推送</li>
            </ul>

            <h3>💰 推荐返现机制</h3>
            <ul>
                <li><strong>33%推荐返现</strong> - 每成功推荐1位用户购买,返现33%</li>
                <li><strong>专属推荐链接</strong> - 自动追踪您的推荐业绩</li>
                <li><strong>长期收益</strong> - 持续推荐,持续获利</li>
            </ul>

            <h3>🚀 合伙人成长计划</h3>
            <ul>
                <li><strong>专属合伙人社群</strong> - 加入核心用户群,参与产品规划</li>
                <li><strong>1v1咨询服务</strong> - 定期与产品团队深度交流</li>
                <li><strong>共同成长价值</strong> - 与 GaiYa 一起成长,共享收益</li>
            </ul>

            <hr>
            <p style="text-align: center; color: #666;">
                <strong>如需了解更多合伙人详情,请联系客服</strong><br>
                邮箱: support@gaiyatime.com
            </p>
        """)
        layout.addWidget(text_browser)

        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet(StyleManager.button_minimal())
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)

        dialog.exec()

    def _check_login_and_guide(self, feature_name: str = None) -> bool:
        """
        检查用户是否已登录，如果未登录则显示引导对话框

        Args:
            feature_name: 功能名称，用于提示。如果为None，使用默认值

        Returns:
            True: 已登录，可以继续
            False: 未登录，已显示引导对话框
        """
        from gaiya.core.auth_client import AuthClient
        from PySide6.QtWidgets import QMessageBox

        auth_client = AuthClient()

        # 检查是否已登录
        if auth_client.is_logged_in():
            return True

        # 如果没有指定功能名称，使用默认值
        if feature_name is None:
            feature_name = tr('auth.features.this_feature')

        # 未登录，显示引导对话框
        message = (
            f"💡 {feature_name}{tr('auth.guide.requires_login')}\n\n"
            f"{tr('auth.guide.benefits_intro')}\n"
            f"{tr('auth.guide.free_user_quota')}\n"
            f"• {tr('account.membership.pro')}: {tr('account.feature.ai_quota_20_per_day')}\n"
            f"{tr('auth.guide.more_features')}\n\n"
            f"{tr('auth.guide.go_to_login')}"
        )

        reply = QMessageBox.question(
            self,
            tr('auth.login_required'),
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 切换到个人中心tab（index=3）
            self.tabs.setCurrentIndex(3)

        return False

    def _check_ai_quota(self) -> bool:
        """检查AI配额是否充足

        Returns:
            True: 配额充足,可以继续
            False: 配额已用完,显示升级对话框
        """
        from gaiya.core.auth_client import AuthClient
        from gaiya.ui.onboarding import QuotaExhaustedDialog

        try:
            logging.info("[配额检查] 开始检查AI配额...")
            auth_client = AuthClient()
            user_tier = auth_client.get_user_tier()
            logging.info(f"[配额检查] 用户等级: {user_tier}")

            # Pro会员或以上不受限制
            if user_tier in ['pro', 'lifetime']:
                logging.info("[配额检查] Pro/Lifetime会员,配额充足")
                return True

            # 免费用户检查配额
            quota_status = auth_client.get_quota_status()
            logging.info(f"[配额检查] 免费用户,配额状态: {quota_status}")

            # 检查 daily_plan 配额 - 处理嵌套结构
            remaining_quota = 0
            if isinstance(quota_status, dict):
                # 新API格式: {'remaining': {'daily_plan': 3, ...}}
                if 'remaining' in quota_status and isinstance(quota_status['remaining'], dict):
                    remaining_quota = quota_status['remaining'].get('daily_plan', 0)
                    logging.info(f"[配额检查] 嵌套格式 - daily_plan剩余配额: {remaining_quota}")
                # 兼容直接格式: {'daily_plan': 3, ...}
                elif 'daily_plan' in quota_status:
                    remaining_quota = quota_status.get('daily_plan', 0)
                    logging.info(f"[配额检查] 扁平格式 - daily_plan剩余配额: {remaining_quota}")
                else:
                    logging.warning(f"[配额检查] 未识别的配额格式: {quota_status}")
            else:
                logging.warning(f"[配额检查] 配额状态不是字典: {type(quota_status)}")

            if remaining_quota <= 0:
                # 配额已用完,显示升级对话框
                logging.warning("[配额检查] 配额已用完,显示升级对话框")
                dialog = QuotaExhaustedDialog(self)
                dialog.upgrade_requested.connect(self._on_quota_upgrade_requested)
                result = dialog.exec()
                logging.info(f"[配额检查] 升级对话框关闭,返回值: {result}")
                return False

            logging.info("[配额检查] 配额充足,可以继续")
            return True
        except Exception as e:
            logging.error(f"[配额检查] 检查配额时发生异常: {type(e).__name__}: {e}", exc_info=True)
            # 发生异常时保守处理,允许继续
            return True

    def _on_quota_upgrade_requested(self):
        """配额用尽对话框中用户请求升级会员"""
        import logging
        logging.info("[配额检查] 用户点击升级会员,切换到个人中心tab")
        # 切换到个人中心tab（index=5,因为有AI规划tab）
        self.tabs.setCurrentIndex(5)
        logging.info(f"[配额检查] 已切换到tab index={self.tabs.currentIndex()}")

    def _bind_card_click(self, card, plan_id):
        """绑定卡片点击事件，使用weakref避免循环引用"""
        import weakref
        weak_self = weakref.ref(self)

        def handler(event):
            self = weak_self()
            if self is not None:
                self._on_plan_card_clicked(plan_id)

        card.mousePressEvent = handler

    def _create_simple_plan_card(self, plan: dict, is_selected: bool = False):
        """创建简单的套餐卡片"""
        from PySide6.QtWidgets import QFrame
        card = QFrame()
        card.setObjectName(f"plan_card_{plan['id']}")
        card.setFixedSize(220, 200)
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        border_color = "#4ECDC4" if is_selected else "#555"  # 使用绿色作为选中描边
        border_width = "3px" if is_selected else "2px"

        card.setStyleSheet(f"""
            QFrame#plan_card_{plan['id']} {{
                background-color: rgba(40, 40, 40, 200);
                border: {border_width} solid {border_color};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(15, 15, 15, 15)

        name_label = QLabel(plan['name'])
        name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: white; background: transparent;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)

        price_layout = QHBoxLayout()
        price_layout.setSpacing(2)
        price_label = QLabel(plan['price'])
        price_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white; background: transparent;")
        period_label = QLabel(plan['period'])
        period_label.setStyleSheet("font-size: 13px; color: rgba(255,255,255,0.8); background: transparent;")
        period_label.setAlignment(Qt.AlignmentFlag.AlignBottom)
        price_layout.addStretch()
        price_layout.addWidget(price_label)
        price_layout.addWidget(period_label)
        price_layout.addStretch()
        layout.addLayout(price_layout)

        layout.addSpacing(5)

        for feature in plan['features']:
            feature_label = QLabel(f"• {feature}")
            feature_label.setStyleSheet("font-size: 11px; color: rgba(255,255,255,0.85); background: transparent;")
            layout.addWidget(feature_label)

        layout.addStretch()
        card.plan_id = plan['id']
        self._bind_card_click(card, plan['id'])
        return card

    def _create_featured_plan_card(self, plan: dict, is_selected: bool = False, user_tier: str = "free"):
        """创建年度卡片（中间，突出显示）

        Args:
            plan: 套餐信息
            is_selected: 是否选中
            user_tier: 用户等级 (free/pro/lifetime)
        """
        from PySide6.QtWidgets import QFrame
        card = QFrame()
        card.setObjectName(f"plan_card_{plan['id']}")
        card.setFixedSize(240, 650)  # 统一三个卡片高度为650px
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        # 突出显示的样式
        border_color = "#FF9800" if is_selected else "#E0E0E0"
        border_width = "3px" if is_selected else "2px"

        card.setStyleSheet(f"""
            QFrame#plan_card_{plan['id']} {{
                background-color: #FFFFFF;
                border: {border_width} solid {border_color};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(6)  # 减小默认间距，改用 addSpacing 精确控制
        layout.setContentsMargins(15, 15, 15, 20)

        # 顶部标题和徽章容器
        header_layout = QHBoxLayout()

        # 标题
        name_label = QLabel(plan['name'])
        name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333333; background: transparent;")
        header_layout.addWidget(name_label)

        header_layout.addStretch()

        # 徽章
        if 'discount_badge' in plan:
            badge = QLabel(plan['discount_badge'])
            badge.setStyleSheet("""
                QLabel {
                    background-color: #FF5722;
                    color: white;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 4px 8px;
                    border-radius: 4px;
                }
            """)
            header_layout.addWidget(badge)

        layout.addLayout(header_layout)

        layout.addSpacing(12)  # 从 10 增加到 12

        # 月均价格（大号突出）- 价格和"/月"在同一行
        if 'monthly_price' in plan:
            # 创建水平布局容器
            price_row_layout = QHBoxLayout()
            price_row_layout.setSpacing(4)
            price_row_layout.setContentsMargins(0, 0, 0, 0)

            # 添加弹性空间使内容居中
            price_row_layout.addStretch()

            # 价格
            monthly_price_label = QLabel(plan['monthly_price'])
            monthly_price_label.setStyleSheet("font-size: 36px; font-weight: bold; color: #FF9800; background: transparent;")
            price_row_layout.addWidget(monthly_price_label)

            # "/月" - 与价格在同一行，对齐到价格底部
            monthly_period_label = QLabel(self.i18n.tr("account.per_month"))
            monthly_period_label.setStyleSheet("font-size: 14px; color: #888888; background: transparent;")
            monthly_period_label.setAlignment(Qt.AlignmentFlag.AlignBottom)
            price_row_layout.addWidget(monthly_period_label)

            # 添加弹性空间使内容居中
            price_row_layout.addStretch()

            layout.addLayout(price_row_layout)

        layout.addSpacing(8)  # 从 5 增加到 8

        # 年费价格
        price_label = QLabel(plan['price'] + plan['period'])
        price_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #333333; background: transparent;")
        price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(price_label)

        # 原价（删除线）
        if 'original_price' in plan:
            original_price_label = QLabel(plan['original_price'] + plan['period'])
            original_price_label.setStyleSheet("""
                font-size: 13px;
                color: #999999;
                background: transparent;
                text-decoration: line-through;
            """)
            original_price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(original_price_label)

        layout.addSpacing(15)  # 从 10 增加到 15

        # 按钮（突出显示）
        # ✅ 根据用户等级修改按钮文案
        if user_tier == "pro":
            button_text = "会员续费"  # 已付费会员显示续费
        else:
            button_text = self.i18n.tr("button.upgrade")  # 免费用户显示升级

        button = QPushButton(button_text)
        button.setFixedHeight(40)
        button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:pressed {
                background-color: #E65100;
            }
        """)
        # 绑定点击事件：直接触发支付流程（使用 partial 避免 Lambda 循环引用）
        button.clicked.connect(partial(self._on_plan_button_clicked, plan['id']))
        layout.addWidget(button)

        layout.addSpacing(12)  # 从 8 增加到 12

        # 功能列表
        for i, feature in enumerate(plan['features']):
            if i == 0:
                # 第一项是标题
                feature_label = QLabel(f"✓ {feature}")
                feature_label.setStyleSheet("font-size: 12px; color: #333333; background: transparent; font-weight: 600;")
            else:
                feature_label = QLabel(f"✓ {feature}")
                feature_label.setStyleSheet("font-size: 11px; color: #666666; background: transparent;")
            layout.addWidget(feature_label)
            if i < len(plan['features']) - 1:  # 除了最后一项，每项后添加间距
                layout.addSpacing(4)

        layout.addStretch()

        # 底部信息：分隔线 + 有效期 + 续费说明
        separator = QLabel("─" * 32)
        separator.setStyleSheet("color: #E0E0E0; background: transparent; font-size: 10px;")
        separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(separator)

        layout.addSpacing(8)

        validity_label = QLabel(plan['validity'])
        validity_label.setStyleSheet("font-size: 11px; color: #666666; background: transparent;")
        validity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(validity_label)

        layout.addSpacing(4)

        renewal_label = QLabel(plan['renewal'])
        renewal_label.setStyleSheet("font-size: 10px; color: #888888; background: transparent;")
        renewal_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(renewal_label)

        layout.addSpacing(10)

        card.plan_id = plan['id']
        self._bind_card_click(card, plan['id'])
        return card

    def _create_regular_plan_card(self, plan: dict, user_tier: str = "free"):
        """创建月度卡片（普通样式）

        Args:
            plan: 套餐信息
            user_tier: 用户等级 (free/pro/lifetime)
        """
        from PySide6.QtWidgets import QFrame
        card = QFrame()
        card.setObjectName(f"plan_card_{plan['id']}")
        card.setFixedSize(220, 650)  # 统一三个卡片高度为650px
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        card.setStyleSheet(f"""
            QFrame#plan_card_{plan['id']} {{
                background-color: #FFFFFF;
                border: 2px solid #E0E0E0;
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(8)  # 减小默认间距，改用 addSpacing 精确控制
        layout.setContentsMargins(15, 20, 15, 20)

        # 标题
        name_label = QLabel(plan['name'])
        name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333333; background: transparent;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)

        layout.addSpacing(15)  # 从 10 增加到 15

        # 价格区域
        price_layout = QHBoxLayout()
        price_layout.setSpacing(2)
        price_label = QLabel(plan['price'])
        price_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #333333; background: transparent;")
        period_label = QLabel(plan['period'])
        period_label.setStyleSheet("font-size: 14px; color: rgba(51, 51, 51, 0.8); background: transparent;")
        period_label.setAlignment(Qt.AlignmentFlag.AlignBottom)
        price_layout.addStretch()
        price_layout.addWidget(price_label)
        price_layout.addWidget(period_label)
        price_layout.addStretch()
        layout.addLayout(price_layout)

        # 年费价格
        if 'yearly_price' in plan:
            yearly_price_label = QLabel(plan['yearly_price'])
            yearly_price_label.setStyleSheet("font-size: 12px; color: rgba(51, 51, 51, 0.6); background: transparent;")
            yearly_price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(yearly_price_label)

        layout.addSpacing(15)  # 从 10 增加到 15

        # 按钮
        # ✅ 根据用户等级修改按钮文案
        if user_tier == "pro":
            button_text = "会员续费"  # 已付费会员显示续费
        else:
            button_text = self.i18n.tr("button.upgrade")  # 免费用户显示升级

        button = QPushButton(button_text)
        button.setFixedHeight(36)
        button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 152, 0, 0.15);
                color: #FF9800;
                border: 1px solid #FF9800;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(255, 152, 0, 0.25);
            }
            QPushButton:pressed {
                background-color: rgba(255, 152, 0, 0.35);
            }
        """)
        # 绑定点击事件：直接触发支付流程（使用 partial 避免 Lambda 循环引用）
        button.clicked.connect(partial(self._on_plan_button_clicked, plan['id']))
        layout.addWidget(button)

        layout.addSpacing(15)  # 从 10 增加到 15

        # 功能列表
        for i, feature in enumerate(plan['features']):
            if i == 0:
                # 第一项是标题
                feature_label = QLabel(f"✓ {feature}")
                feature_label.setStyleSheet("font-size: 12px; color: #333333; background: transparent; font-weight: 600;")
            else:
                feature_label = QLabel(f"✓ {feature}")
                feature_label.setStyleSheet("font-size: 11px; color: rgba(51, 51, 51, 0.85); background: transparent;")
            layout.addWidget(feature_label)
            if i < len(plan['features']) - 1:  # 除了最后一项，每项后添加间距
                layout.addSpacing(3)

        layout.addStretch()

        # 底部信息：分隔线 + 有效期 + 续费说明
        separator = QLabel("─" * 30)
        separator.setStyleSheet("color: rgba(51, 51, 51, 0.2); background: transparent; font-size: 10px;")
        separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(separator)

        layout.addSpacing(8)

        validity_label = QLabel(plan['validity'])
        validity_label.setStyleSheet("font-size: 11px; color: rgba(51, 51, 51, 0.6); background: transparent;")
        validity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(validity_label)

        layout.addSpacing(4)

        renewal_label = QLabel(plan['renewal'])
        renewal_label.setStyleSheet("font-size: 10px; color: rgba(51, 51, 51, 0.5); background: transparent;")
        renewal_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(renewal_label)

        layout.addSpacing(10)

        card.plan_id = plan['id']
        self._bind_card_click(card, plan['id'])
        return card

    def _create_lifetime_plan_card(self, plan: dict, user_tier: str = "free"):
        """创建会员合伙人卡片（右侧，特殊样式）

        Args:
            plan: 套餐信息
            user_tier: 用户等级 (free/pro/lifetime)
        """
        from PySide6.QtWidgets import QFrame
        card = QFrame()
        card.setObjectName(f"plan_card_{plan['id']}")
        card.setFixedSize(220, 650)  # 统一三个卡片高度为650px
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        card.setStyleSheet(f"""
            QFrame#plan_card_{plan['id']} {{
                background-color: #FFFFFF;
                border: 2px solid #E0E0E0;
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(15, 20, 15, 20)

        # 标题文字（居中显示）
        name_label = QLabel(plan['name'])
        name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333333; background: transparent;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)

        layout.addSpacing(10)  # 标题后间距

        # 价格区域(优先展示)
        price_layout = QHBoxLayout()
        price_layout.setSpacing(2)
        price_label = QLabel(plan['price'])
        price_label.setStyleSheet("font-size: 36px; font-weight: bold; color: #FFD700; background: transparent;")
        price_label.setMinimumHeight(45)  # 确保价格数字有足够高度显示完整
        price_layout.addStretch()
        price_layout.addWidget(price_label)
        price_layout.addStretch()
        layout.addLayout(price_layout)

        layout.addSpacing(5)  # 价格和文案之间间距

        # 一次付费，终身可用（合并成一行显示）
        lifetime_label = QLabel(self.i18n.tr("membership.ui.one_time_lifetime"))
        lifetime_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #FFD700; background: transparent;")
        lifetime_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lifetime_label)

        layout.addSpacing(8)  # 说明文案和限量标签之间间距

        # 限量标签（移到价格和说明之后）
        limited_badge = QLabel(self.i18n.tr("membership.ui.limited_offer"))
        limited_badge.setStyleSheet("""
            QLabel {
                background-color: #B8860B;
                color: #FFFFFF;
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: normal;
            }
        """)
        limited_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(limited_badge, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(12)  # 限量标签和邀请函之间间距(减小)

        # 邀请函链接
        invitation_link = QLabel(f'<a href="#" style="color: #666666; text-decoration: none;">{self.i18n.tr("config.membership.read_partner_invitation")}</a>')
        invitation_link.setStyleSheet("font-size: 12px; background: transparent;")
        invitation_link.setAlignment(Qt.AlignmentFlag.AlignCenter)
        invitation_link.setOpenExternalLinks(False)
        invitation_link.linkActivated.connect(lambda: self._show_invitation_dialog())
        invitation_link.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(invitation_link)

        layout.addSpacing(8)

        # 按钮（渐变样式）
        button = QPushButton(self.i18n.tr("membership.ui.become_partner"))
        button.setFixedHeight(36)
        button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FFD700,
                    stop:1 #FFA500);
                color: #333;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FFC700,
                    stop:1 #FF9500);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FFB700,
                    stop:1 #FF8500);
            }
        """)
        # 绑定点击事件：直接触发支付流程（使用 partial 避免 Lambda 循环引用）
        button.clicked.connect(partial(self._on_plan_button_clicked, plan['id']))
        layout.addWidget(button)

        layout.addSpacing(15)

        # 功能列表
        for i, feature in enumerate(plan['features']):
            if i == 0:
                # 第一项是标题
                feature_label = QLabel(f"✓ {feature}")
                feature_label.setStyleSheet("font-size: 12px; color: #333333; background: transparent; font-weight: 600;")
            else:
                feature_label = QLabel(f"✓ {feature}")
                feature_label.setStyleSheet("font-size: 11px; color: #666666; background: transparent;")
            layout.addWidget(feature_label)
            if i < len(plan['features']) - 1:
                layout.addSpacing(3)

        layout.addStretch()

        # 底部信息：分隔线 + 有效期 + 续费说明
        separator = QLabel("─" * 30)
        separator.setStyleSheet("color: #E0E0E0; background: transparent; font-size: 10px;")
        separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(separator)

        layout.addSpacing(8)

        validity_label = QLabel(plan['validity'])
        validity_label.setStyleSheet("font-size: 11px; color: rgba(255,215,0,0.8); background: transparent; font-weight: 600;")
        validity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(validity_label)

        layout.addSpacing(4)

        renewal_label = QLabel(plan['renewal'])
        renewal_label.setStyleSheet("font-size: 10px; color: #888888; background: transparent;")
        renewal_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(renewal_label)

        layout.addSpacing(10)

        card.plan_id = plan['id']
        self._bind_card_click(card, plan['id'])
        return card

    def _show_invitation_dialog(self):
        """显示会员合伙人邀请函弹窗"""
        from PySide6.QtWidgets import QDialog, QTextEdit, QScrollArea

        dialog = QDialog(self)
        dialog.setWindowTitle(self.i18n.tr("app.name"))
        dialog.setFixedSize(700, 600)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #F5E6D3;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # 标题
        title_label = QLabel(self.i18n.tr("about.letter_title"))
        title_label.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: #654321;
            background: transparent;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 副标题
        subtitle_label = QLabel(self.i18n.tr("about.letter_subtitle"))
        subtitle_label.setStyleSheet("""
            font-size: 14px;
            color: #8B7355;
            background: transparent;
            margin-bottom: 10px;
        """)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)

        # 分隔线
        separator = QLabel("══════════════════════")
        separator.setStyleSheet("color: #D4A574; background: transparent; font-size: 12px;")
        separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(separator)

        # 信件内容（可滚动）
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(212, 165, 116, 0.2);
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: rgba(139, 115, 85, 0.5);
                border-radius: 5px;
            }
        """)

        content_widget = QLabel()
        content_widget.setWordWrap(True)
        content_widget.setTextFormat(Qt.TextFormat.RichText)
        content_widget.setStyleSheet("""
            font-size: 13px;
            color: #3E2723;
            background: transparent;
            padding: 10px;
            line-height: 1.8;
        """)

        # 邀请信完整内容
        content_text = """
        <p style="margin-bottom: 15px;"><b>亲爱的朋友：</b></p>

        <p style="margin-bottom: 15px;">如果你正在读这封信，我猜你和我一样，曾无数次感受到时间的无声流逝。</p>

        <p style="margin-bottom: 15px;">从2023年初的深夜构想到今天，GaiYa 已陪伴了<b>几百位早期用户</b>度过他们的每一个工作日。有人用它管理番茄钟，有人用它切换工作与生活，还有人说："看到进度条走到'下班'那一刻，终于能心安理得地关电脑了。"</p>

        <p style="margin-bottom: 15px;">我是 GaiYa 的创造者，一名产品经理，也是时间管理的长期实践者。2023年初的某个深夜，我盯着屏幕上密密麻麻的任务清单，突然意识到：<b>我们需要的不是更多任务管理工具，而是一种让时间「看得见、摸得着」的方式</b>。</p>

        <p style="margin-bottom: 15px;">于是有了 GaiYa —— 一条桌面进度条，让每一天都清晰可见。</p>

        <p style="margin-bottom: 15px; margin-top: 20px;"><b style="color: #8B4513;">✨ 为什么做 GaiYa？</b></p>

        <p style="margin-bottom: 15px;">我曾亲手打造过多个从0到1的产品，有成功也有失败。但每次复盘，最深的感悟都是：<b>时间管理的本质，不是效率，而是觉察</b>。</p>

        <p style="margin-bottom: 15px;">当你看见那条进度条一点点推进，看见今天已经过去了63%，看见"下班"色块还有2小时才到 —— 你会做出不同的选择。这就是 GaiYa 想做的事：<b>让时间可视化，让选择更自主</b>。</p>

        <p style="margin-bottom: 15px; margin-top: 20px;"><b style="color: #8B4513;">🤝 会员合伙人意味着什么？</b></p>

        <p style="margin-bottom: 15px;">GaiYa 现在还很年轻。我希望找到一群真正认同这个理念的人，不只是用户，而是<b>产品的共创者</b>。</p>

        <p style="margin-bottom: 15px;">成为会员合伙人，你将获得：</p>

        <p style="margin-bottom: 10px;"><b>1. 终身的工具陪伴</b></p>
        <p style="margin-bottom: 15px; margin-left: 20px;">一次付费，永久使用。50次/天AI任务生成、去水印、数据云同步、场景系统、所有未来新功能 —— 我会持续打磨，让它真正成为你效率工作流的一部分。</p>

        <p style="margin-bottom: 10px;"><b>2. 产品决策的话语权</b></p>
        <p style="margin-bottom: 15px; margin-left: 20px;">你将获邀加入<b>会员合伙人专属微信群（首批限额1000人）</b>，与我和其他种子用户直接对话。作为首批成员，你将亲历社群从0到1的搭建过程。你的需求、你的吐槽、你的建议 —— 都会直接影响产品的走向。</p>

        <p style="margin-bottom: 10px;"><b>3. 优先体验与专属支持</b></p>
        <p style="margin-bottom: 15px; margin-left: 20px;">所有新功能，你将第一时间体验。遇到问题？<b>专属1v1咨询通道</b>，我会亲自回复，帮你定制最适合的工作流。</p>

        <p style="margin-bottom: 10px;"><b>4. 共享成长的价值（规划中）</b></p>
        <p style="margin-bottom: 15px; margin-left: 20px;">我正在搭建<b>33%推荐返现机制</b>。当 GaiYa 帮到你的朋友时，你也将获得实际收益。这不是分销，而是价值共享 —— 好产品，值得一起传播。</p>

        <p style="margin-bottom: 15px; margin-top: 20px;"><b style="color: #8B4513;">💰 关于599元会员费用</b></p>

        <p style="margin-bottom: 15px;">这不是一个拍脑袋的数字。让我和你算笔账：</p>

        <p style="margin-bottom: 10px; margin-left: 20px;">• AI任务生成的API成本，每次约0.5元，月度会员每月20次 = 10元/月</p>
        <p style="margin-bottom: 10px; margin-left: 20px;">• 云同步服务器费用，每用户每年约50元</p>
        <p style="margin-bottom: 10px; margin-left: 20px;">• 持续开发投入（新功能、bug修复、1v1客服支持）</p>

        <p style="margin-bottom: 15px;">599元换算下来，相当于<b>年费199元使用3年</b>——而我承诺的是<b style="color: #4CAF50;">终身使用</b>。这是我对产品长期主义的承诺。</p>

        <p style="margin-bottom: 15px;">这笔费用将100%投入到：<b>产品研发（60%）</b>、<b>服务器成本（30%）</b>、<b>用户运营（10%）</b>。每一分钱，都会让 GaiYa 变得更好。</p>

        <p style="margin-bottom: 15px; margin-top: 20px;"><b style="color: #8B4513;">⏰ 为什么是现在？</b></p>

        <p style="margin-bottom: 15px;">GaiYa 刚刚完成品牌升级（v1.5），会员系统刚刚上线。此刻加入的你，是真正的<b>种子用户</b>，你的每一个反馈都能塑造产品的未来形态。</p>

        <p style="margin-bottom: 15px;">此次会员合伙人招募，<b style="color: #FF9800;">首批仅开放1000个名额</b>，且<b>一旦售罄将永不再开放此优惠价格</b>。我希望每一位加入的人，都是真正认同「时间可视化」理念的同路人。</p>

        <p style="margin-bottom: 15px; margin-top: 20px;"><b style="color: #8B4513;">💬 来自早期用户的声音</b></p>

        <p style="margin-bottom: 10px; font-style: italic; margin-left: 20px; color: #666;">
        "进度条让我第一次感受到'时间握在手里'的踏实感。" —— @产品经理 Alex
        </p>
        <p style="margin-bottom: 15px; font-style: italic; margin-left: 20px; color: #666;">
        "工作配色和休息配色的切换，让我学会了按时下班。" —— @UI设计师 小林
        </p>

        <p style="margin-bottom: 15px; margin-top: 20px;"><b style="color: #8B4513;">📋 最后的话</b></p>

        <p style="margin-bottom: 15px;">会员合伙人计划属于数字服务，一旦加入<b>无法退款</b>。但我相信，如果你真的认同这个理念，599元换来的不只是一个工具，而是：</p>

        <p style="margin-bottom: 10px; margin-left: 20px;">• 终身的时间管理解决方案</p>
        <p style="margin-bottom: 10px; margin-left: 20px;">• 一个与你志同道合的效率社群</p>
        <p style="margin-bottom: 10px; margin-left: 20px;">• 参与打磨一个真正有用产品的机会</p>

        <p style="margin-bottom: 15px; margin-top: 20px;">请在充分理解后再做决定。这份信任，我会倍加珍惜。</p>

        <p style="margin-bottom: 15px;">现在，我期待与你一起，让每一分钟都清晰可见。</p>

        <p style="margin-top: 30px; text-align: right;"><b>GaiYa 创造者</b></p>
        <p style="text-align: right; color: #8B7355;">2025 年 11 月</p>
        """

        content_widget.setText(content_text)
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

        # 底部按钮
        button = QPushButton(self.i18n.tr("membership.buttons.become_partner"))
        button.setFixedHeight(44)
        button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8B6914,
                    stop:1 #B8860B);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #9A7714,
                    stop:1 #C8960B);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7B5914,
                    stop:1 #A8760B);
            }
        """)
        # 使用 partial 避免 Lambda 循环引用
        button.clicked.connect(partial(self._on_invitation_accepted, dialog))
        layout.addWidget(button)

        dialog.exec()

    def _on_invitation_accepted(self, dialog):
        """点击邀请函底部按钮后的处理"""
        # 关闭弹窗
        dialog.close()

        # 选中会员合伙人套餐
        self.selected_plan_id = "lifetime"

        # 更新卡片选中状态
        for card in self.plan_cards:
            if hasattr(card, 'plan_id'):
                if card.plan_id == "lifetime":
                    card.setStyleSheet("""
                        QFrame#plan_card_lifetime {
                            background-color: rgba(50, 50, 50, 200);
                            border: 2px solid #FFD700;
                            border-radius: 12px;
                        }
                    """)
                elif card.plan_id == "pro_yearly":
                    card.setStyleSheet("""
                        QFrame#plan_card_pro_yearly {
                            background-color: rgba(50, 50, 50, 200);
                            border: 3px solid #FF9800;
                            border-radius: 12px;
                        }
                    """)
                else:  # monthly
                    card.setStyleSheet("""
                        QFrame#plan_card_pro_monthly {
                            background-color: rgba(50, 50, 50, 200);
                            border: 2px solid #666;
                            border-radius: 12px;
                        }
                    """)

        # 触发支付流程
        self._on_plan_button_clicked("lifetime")

    def _create_membership_tips(self):
        """创建会员提示区域"""
        from PySide6.QtWidgets import QFrame, QTextEdit

        tips_frame = QFrame()
        tips_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 0px;
            }
        """)

        layout = QVBoxLayout(tips_frame)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        # 标题
        title_label = QLabel(self.i18n.tr("membership.ui.member_tips"))
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333333; background: transparent;")
        layout.addWidget(title_label)

        # 说明文字
        tips_text = self.i18n.tr("account.member_tips_text")

        tips_label = QLabel(tips_text)
        tips_label.setStyleSheet("""
            font-size: 13px;
            color: rgba(51, 51, 51, 0.85);
            line-height: 1.6;
            background: transparent;
            border: none;
        """)
        tips_label.setWordWrap(True)
        tips_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        layout.addWidget(tips_label)

        return tips_frame

    def _create_comparison_table(self):
        """创建会员方案详细对比表"""
        from PySide6.QtWidgets import QFrame, QTableWidget, QTableWidgetItem, QHeaderView
        from PySide6.QtCore import Qt

        # 创建容器
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
            }
        """)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("""
            QFrame {
                background-color: rgba(51, 51, 51, 0.1);
                max-height: 2px;
                border: none;
            }
        """)
        layout.addWidget(separator)

        # 添加标题
        title_label = QLabel(self.i18n.tr("membership.ui.comparison_title"))
        title_label.setStyleSheet("color: #333333; font-size: 18px; font-weight: bold; margin: 10px 0px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 创建表格
        table = QTableWidget()
        table.setStyleSheet(StyleManager.table())
        table.setColumnCount(5)  # 功能名称 + 4个等级
        table.setHorizontalHeaderLabels([
            self.i18n.tr("account.comparison_table_features"),
            self.i18n.tr("account.comparison_table_free"),
            self.i18n.tr("account.comparison_table_monthly"),
            self.i18n.tr("account.comparison_table_yearly"),
            self.i18n.tr("account.comparison_table_lifetime")
        ])

        # 设置表格样式
        table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                gridline-color: #E0E0E0;
                color: #333333;
            }
            QTableWidget::item {
                padding: 12px 8px;
                border-bottom: 1px solid #F0F0F0;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                color: #333333;
                font-weight: bold;
                font-size: 14px;
                padding: 12px 8px;
                border: none;
                border-right: 1px solid #E0E0E0;
                border-bottom: 1px solid #E0E0E0;
            }
            QHeaderView::section:first {
                border-top-left-radius: 8px;
            }
            QHeaderView::section:last {
                border-top-right-radius: 8px;
                border-right: none;
            }
        """)

        # 定义表格数据
        table_data = [
            # 【核心功能】分组标题
            {
                "type": "group",
                "name": self.i18n.tr("account.features_group_core"),
            },
            # 每日进度条
            {
                "type": "feature",
                "name": self.i18n.tr("account.feature_progress_bar"),
                "free": self.i18n.tr("account.feature_progress_bar_free"),
                "monthly": self.i18n.tr("account.feature_progress_bar_paid"),
                "yearly": self.i18n.tr("account.feature_progress_bar_paid"),
                "lifetime": self.i18n.tr("account.feature_progress_bar_paid"),
            },
            # AI任务规划
            {
                "type": "feature",
                "name": self.i18n.tr("account.feature_ai_planning"),
                "free": self.i18n.tr("account.feature_ai_planning_free"),
                "monthly": self.i18n.tr("account.feature_ai_planning_monthly"),
                "yearly": self.i18n.tr("account.feature_ai_planning_yearly"),
                "lifetime": self.i18n.tr("account.feature_ai_planning_lifetime"),
            },
            # 统计报告分析
            {
                "type": "feature",
                "name": tr("account.feature.statistics_reports"),
                "free": "✗",
                "monthly": "✓",
                "yearly": "✓",
                "lifetime": "✓",
            },
            # 【高级功能】分组标题
            {
                "type": "group",
                "name": self.i18n.tr("account.features_group_advanced"),
            },
            # 主题自定义
            {
                "type": "feature",
                "name": self.i18n.tr("account.feature_theme_custom"),
                "free": "✓",
                "monthly": "✓",
                "yearly": "✓",
                "lifetime": "✓",
            },
            # 番茄时钟
            {
                "type": "feature",
                "name": tr("account.feature.pomodoro_timer"),
                "free": "✓",
                "monthly": "✓",
                "yearly": "✓",
                "lifetime": "✓",
            },
            # 数据云同步
            {
                "type": "feature",
                "name": tr("account.feature.cloud_sync"),
                "free": "✗",
                "monthly": "✓",
                "yearly": "✓",
                "lifetime": "✓",
            },
            # 场景系统
            {
                "type": "feature",
                "name": tr("account.feature.scene_system"),
                "free": "✗",
                "monthly": "✓",
                "yearly": "✓",
                "lifetime": "✓",
            },
            # 抢先体验新功能
            {
                "type": "feature",
                "name": tr("account.feature.early_access"),
                "free": "✗",
                "monthly": "✓",
                "yearly": "✓",
                "lifetime": "✓",
            },
            # 加入VIP会员群
            {
                "type": "feature",
                "name": tr("account.feature.vip_group"),
                "free": "✗",
                "monthly": "✓",
                "yearly": "✓",
                "lifetime": "✓",
            },
            # 【会员权益】分组标题
            {
                "type": "group",
                "name": self.i18n.tr("account.features_group_benefits"),
            },
            # 有效期
            {
                "type": "feature",
                "name": self.i18n.tr("account.feature_validity"),
                "free": self.i18n.tr("account.feature_validity_free"),
                "monthly": self.i18n.tr("account.feature_validity_monthly"),
                "yearly": self.i18n.tr("account.feature_validity_yearly"),
                "lifetime": self.i18n.tr("account.feature_validity_lifetime"),
            },
            # 引荐返现比例（会员合伙人独有）
            {
                "type": "feature",
                "name": self.i18n.tr("account.feature_referral_rate"),
                "free": "✗",
                "monthly": "✗",
                "yearly": "✗",
                "lifetime": "33%",
            },
            # 专属合伙人社群（会员合伙人独有）
            {
                "type": "feature",
                "name": tr("account.feature.partner_community"),
                "free": "✗",
                "monthly": "✗",
                "yearly": "✗",
                "lifetime": "✓",
            },
            # 1v1咨询服务（会员合伙人独有）
            {
                "type": "feature",
                "name": "1v1咨询服务",
                "free": "✗",
                "monthly": "✗",
                "yearly": "✗",
                "lifetime": "✓",
            },
        ]

        # 设置行数
        table.setRowCount(len(table_data))

        # 填充表格数据
        for row, data in enumerate(table_data):
            if data["type"] == "group":
                # 分组标题行
                item = QTableWidgetItem(data["name"])
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                item.setBackground(QColor(245, 245, 245))  # #F5F5F5
                item.setForeground(QColor(51, 51, 51))  # #333333
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                table.setItem(row, 0, item)

                # 合并分组标题行的所有列
                table.setSpan(row, 0, 1, 5)

            else:
                # 功能行
                # 功能名称
                name_item = QTableWidgetItem(data["name"])
                name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                table.setItem(row, 0, name_item)

                # 免费版
                free_item = QTableWidgetItem(data["free"])
                free_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, 1, free_item)

                # Pro 月度
                monthly_item = QTableWidgetItem(data["monthly"])
                monthly_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, 2, monthly_item)

                # Pro 年度
                yearly_item = QTableWidgetItem(data["yearly"])
                yearly_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, 3, yearly_item)

                # 永久会员
                lifetime_item = QTableWidgetItem(data["lifetime"])
                lifetime_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, 4, lifetime_item)

        # 设置表格属性
        table.verticalHeader().setVisible(False)  # 隐藏行号
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # 禁止编辑
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)  # 禁止选择
        table.setWordWrap(True)  # 启用自动换行

        # 禁用滚动条，让表格完全展开
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 设置列宽
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # 功能名称列自适应
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(1, 120)  # 免费版
        table.setColumnWidth(2, 120)  # Pro 月度
        table.setColumnWidth(3, 120)  # Pro 年度
        table.setColumnWidth(4, 120)  # 会员合伙人

        # 设置行高
        for row in range(table.rowCount()):
            table.setRowHeight(row, 60)

        # 计算并设置表格总高度，使其完全展开
        # 表头高度 + 所有行高度
        header_height = table.horizontalHeader().height()
        total_height = header_height + (table.rowCount() * 60)
        table.setFixedHeight(total_height)

        layout.addWidget(table)

        return container

    def _on_plan_card_clicked(self, plan_id: str):
        """处理套餐卡片点击"""
        # 只处理付费套餐（月度、年度、会员合伙人）
        if plan_id not in ["pro_monthly", "pro_yearly", "lifetime"]:
            return

        self.selected_plan_id = plan_id

        # 更新卡片样式
        for card in self.plan_cards:
            if hasattr(card, 'plan_id'):
                if card.plan_id == "pro_yearly":
                    # 年度卡片
                    is_selected = (card.plan_id == plan_id)
                    border_color = "#FF9800" if is_selected else "#E0E0E0"
                    border_width = "3px" if is_selected else "2px"
                    card.setStyleSheet(f"""
                        QFrame#plan_card_{card.plan_id} {{
                            background-color: #FFFFFF;
                            border: {border_width} solid {border_color};
                            border-radius: 12px;
                        }}
                    """)
                elif card.plan_id == "pro_monthly":
                    # 月度卡片
                    is_selected = (card.plan_id == plan_id)
                    border_color = "#FF9800" if is_selected else "#E0E0E0"
                    border_width = "3px" if is_selected else "2px"
                    card.setStyleSheet(f"""
                        QFrame#plan_card_{card.plan_id} {{
                            background-color: #FFFFFF;
                            border: {border_width} solid {border_color};
                            border-radius: 12px;
                        }}
                    """)
                elif card.plan_id == "lifetime":
                    # 会员合伙人卡片
                    is_selected = (card.plan_id == plan_id)
                    border_color = "#FFD700" if is_selected else "#E0E0E0"
                    border_width = "3px" if is_selected else "2px"
                    card.setStyleSheet(f"""
                        QFrame#plan_card_{card.plan_id} {{
                            background-color: #FFFFFF;
                            border: {border_width} solid {border_color};
                            border-radius: 12px;
                        }}
                    """)

    def _show_payment_method_dialog(self, plan_id: str):
        """显示支付方式选择对话框"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton, QButtonGroup, QPushButton
        from PySide6.QtCore import Qt

        # 套餐信息映射
        plan_info = {
            "pro_monthly": {"name": "Pro 月度", "price_cny": "¥29", "price_usd": "$4.99", "period": "/月"},
            "pro_yearly": {"name": "Pro 年度", "price_cny": "¥199", "price_usd": "$39.99", "period": "/年"},
            "lifetime": {"name": "会员合伙人", "price_cny": "¥599", "price_usd": "$89.99", "period": ""}
        }

        plan = plan_info.get(plan_id, {})

        # Add defensive check for empty plan
        if not plan:
            QMessageBox.warning(
                self,
                "错误",
                f"无效的套餐ID: {plan_id}\n\n请联系客服处理。"
            )
            return

        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle(self.i18n.tr("account.select_payment_method"))
        dialog.setFixedWidth(420)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # 标题 - 直接使用中文文本
        title_text = f"您选择的套餐：{plan['name']} - {plan['price_cny']}{plan['period']}"
        title_label = QLabel(title_text)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333333;
                background: transparent;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 分隔线
        separator = QLabel()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #E0E0E0;")
        layout.addWidget(separator)

        # 提示文字 - 直接使用中文文本
        hint_text = "请选择支付方式："
        hint_label = QLabel(hint_text)
        hint_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #666666;
                background: transparent;
            }
        """)
        layout.addWidget(hint_label)

        # Payment cards - no radio buttons, card-based selection
        # Track selected payment method
        selected_payment = ["alipay"]  # Use list to allow modification in nested function

        # Create payment cards
        alipay_card = self._create_payment_option_card(
            "alipay",
            "🔵 支付宝",
            f"{plan['price_cny']}{plan['period']}",
            ""
        )
        layout.addWidget(alipay_card)

        wxpay_card = self._create_payment_option_card(
            "wxpay",
            "💚 微信支付",
            f"{plan['price_cny']}{plan['period']}",
            ""
        )
        layout.addWidget(wxpay_card)

        stripe_card = self._create_payment_option_card(
            "stripe",
            "💳 国际支付 (Stripe)",
            f"{plan['price_usd']}{plan['period']}",
            "支持 Visa/Mastercard/Amex"
        )
        layout.addWidget(stripe_card)

        # Store cards for easy access
        cards = {
            "alipay": alipay_card,
            "wxpay": wxpay_card,
            "stripe": stripe_card
        }

        # Handle card selection
        def on_card_clicked(pay_method_id):
            """Update selection when card is clicked"""
            selected_payment[0] = pay_method_id
            # Update visual state of all cards
            for method_id, card in cards.items():
                card.set_selected(method_id == pay_method_id)

        # Connect card click signals
        alipay_card.clicked.connect(on_card_clicked)
        wxpay_card.clicked.connect(on_card_clicked)
        stripe_card.clicked.connect(on_card_clicked)

        # Set initial selection (alipay)
        on_card_clicked("alipay")

        layout.addSpacing(10)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        cancel_button = QPushButton(self.i18n.tr("button.cancel"))
        cancel_button.setFixedHeight(40)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F5;
                color: #666666;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #EEEEEE;
            }
            QPushButton:pressed {
                background-color: #E0E0E0;
            }
        """)
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_button)

        confirm_button = QPushButton(self.i18n.tr("membership.payment.confirm_payment"))
        confirm_button.setFixedHeight(40)
        confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)

        def on_confirm():
            """Handle confirm button click - use selected payment method"""
            pay_method = selected_payment[0]
            dialog.accept()

            if pay_method == "alipay":
                self._on_alipay_selected(plan_id)
            elif pay_method == "wxpay":
                self._on_wxpay_selected(plan_id)
            elif pay_method == "stripe":
                self._on_stripe_selected(plan_id)

        confirm_button.clicked.connect(on_confirm)
        button_layout.addWidget(confirm_button)

        layout.addLayout(button_layout)

        # 显示对话框
        dialog.exec()

    def _create_payment_option_card(self, pay_method_id, title, price, subtitle):
        """创建支付选项卡片 - 无单选按钮的卡片风格"""
        from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel
        from PySide6.QtCore import Qt

        # Create card without radio button
        card = PaymentOptionCard(pay_method_id)

        main_layout = QHBoxLayout(card)
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(15)

        # Content area - no radio button
        content_layout = QVBoxLayout()
        content_layout.setSpacing(5)

        # Title and price in one row
        title_row = QHBoxLayout()
        title_row.setSpacing(10)

        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 15px;
                font-weight: bold;
                color: #333333;
                background: transparent;
                border: none;
            }
        """)
        title_row.addWidget(title_label)

        title_row.addStretch()

        price_label = QLabel(price)
        price_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333333;
                background: transparent;
                border: none;
            }
        """)
        title_row.addWidget(price_label)

        content_layout.addLayout(title_row)

        # Subtitle (if provided)
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #666666;
                    background: transparent;
                    border: none;
                }
            """)
            content_layout.addWidget(subtitle_label)

        main_layout.addLayout(content_layout)

        return card

    def _on_alipay_selected(self, plan_id: str):
        """处理支付宝支付"""
        from gaiya.core.auth_client import AuthClient
        from gaiya.core.async_worker import AsyncNetworkWorker
        import logging

        pay_type = "alipay"
        self._current_pay_type = pay_type  # 保存支付类型用于回调
        self._current_plan_id = plan_id  # 保存套餐ID用于回调

        logging.info(f"[支付调试] 支付宝支付 - plan_type: {plan_id}, pay_type: {pay_type}")

        # Create progress dialog
        self._payment_progress = QProgressDialog(
            "正在创建支付订单...",
            "取消",
            0, 0,  # Indeterminate progress bar
            self
        )
        self._payment_progress.setWindowTitle("请稍候")
        self._payment_progress.setWindowModality(Qt.WindowModal)
        self._payment_progress.setMinimumDuration(0)  # Show immediately
        self._payment_progress.show()

        # ✅ 性能优化: 使用异步Worker避免UI卡顿
        auth_client = AuthClient()
        self._payment_worker = AsyncNetworkWorker(
            auth_client.create_payment_order,
            plan_type=plan_id,
            pay_type=pay_type
        )
        self._payment_worker.success.connect(self._on_alipay_order_created)
        self._payment_worker.error.connect(self._on_payment_error)
        self._payment_worker.start()

    def _on_alipay_order_created(self, result: dict):
        """支付宝订单创建成功回调"""
        from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton
        from PySide6.QtCore import QUrl, QTimer, Qt
        from PySide6.QtGui import QDesktopServices, QPixmap
        from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
        from gaiya.core.auth_client import AuthClient
        import logging

        # Close progress dialog
        if hasattr(self, '_payment_progress') and self._payment_progress:
            self._payment_progress.close()
            self._payment_progress = None

        logging.info(f"[支付调试] 支付宝订单创建结果: {result}")

        if result.get("success"):
            # 新方式: 使用二维码支付
            qrcode_url = result.get("qrcode_url")
            out_trade_no = result.get("out_trade_no")
            trade_no = result.get("trade_no")
            amount = result.get("amount")
            plan_name = result.get("plan_name", "Pro月度订阅")
            pay_type = getattr(self, "_current_pay_type", "") or result.get("pay_type", "") or "alipay"
            if pay_type == "alipay":
                pay_type_name = "支付宝"
            elif pay_type == "wxpay":
                pay_type_name = "微信支付"
            else:
                pay_type_name = "支付宝或微信"

            logging.info(f"[PAYMENT] Order created: {out_trade_no}, trade_no: {trade_no}")
            logging.info(f"[PAYMENT] QR code URL: {qrcode_url[:80] if qrcode_url else 'None'}...")

            # 创建二维码支付对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("扫码支付")
            dialog.setModal(True)
            dialog.setMinimumSize(400, 500)

            layout = QVBoxLayout(dialog)
            layout.setSpacing(20)
            layout.setContentsMargins(30, 30, 30, 30)

            # 标题
            title = QLabel(f"购买 {plan_name}")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title.setStyleSheet("font-size: 18px; font-weight: bold;")
            layout.addWidget(title)

            # 金额
            amount_label = QLabel(f"¥{amount:.2f}")
            amount_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            amount_label.setStyleSheet("font-size: 24px; color: #FF6B35; font-weight: bold;")
            layout.addWidget(amount_label)

            # 二维码占位符
            qr_label = QLabel("正在加载二维码...")
            qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            qr_label.setMinimumSize(300, 300)
            qr_label.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ddd; border-radius: 8px;")
            layout.addWidget(qr_label)

            # 提示信息
            hint = QLabel(f"请使用{pay_type_name}扫描二维码完成支付")
            hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hint.setStyleSheet("color: #666; font-size: 14px;")
            layout.addWidget(hint)

            # 订单号
            order_label = QLabel(f"订单号: {out_trade_no}")
            order_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            order_label.setStyleSheet("color: #999; font-size: 12px;")
            layout.addWidget(order_label)

            # 按钮布局
            from PySide6.QtWidgets import QHBoxLayout
            button_layout = QHBoxLayout()

            # 取消按钮
            cancel_btn = QPushButton("取消支付")
            cancel_btn.clicked.connect(lambda: self._cancel_payment_dialog(dialog))
            button_layout.addWidget(cancel_btn)

            # 已完成支付按钮
            confirm_btn = QPushButton("已完成支付")
            confirm_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
            confirm_btn.clicked.connect(lambda: self._confirm_payment_manually(dialog, out_trade_no, plan_name))
            button_layout.addWidget(confirm_btn)

            layout.addLayout(button_layout)

            # 保存对话框引用
            self.payment_polling_dialog = dialog
            self.current_out_trade_no = out_trade_no
            self.current_trade_no = trade_no
            self.current_plan_name = plan_name

            # 下载并显示二维码
            def download_qrcode():
                if not hasattr(self, 'network_manager'):
                    self.network_manager = QNetworkAccessManager(self)

                request = QNetworkRequest(QUrl(qrcode_url))
                reply = self.network_manager.get(request)

                def on_finished():
                    if reply.error() == QNetworkReply.NetworkError.NoError:
                        data = reply.readAll()
                        pixmap = QPixmap()
                        pixmap.loadFromData(data)

                        if not pixmap.isNull():
                            scaled_pixmap = pixmap.scaled(280, 280, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                            qr_label.setPixmap(scaled_pixmap)
                            logging.info(f"[PAYMENT] QR code loaded successfully")
                        else:
                            qr_label.setText("二维码加载失败\n请刷新重试")
                            logging.error(f"[PAYMENT] Failed to parse QR code image")
                    else:
                        error_msg = reply.errorString()
                        qr_label.setText(f"二维码加载失败\n{error_msg}")
                        logging.error(f"[PAYMENT] Failed to download QR code: {error_msg}")

                    reply.deleteLater()

                reply.finished.connect(on_finished)

            download_qrcode()

            # 启动支付状态轮询
            auth_client = AuthClient()
            self.payment_timer = QTimer()
            self.payment_timer.setInterval(3000)
            self.payment_timer.timeout.connect(partial(self._check_payment_status, out_trade_no, trade_no, auth_client))
            self.payment_timer.start()

            # 显示对话框
            dialog.exec()
        else:
            error_msg = result.get("error", "创建订单失败")
            plan_id = self._current_plan_id

            if "MERCHANT_STATUS_NOT_NORMAL" in error_msg or "渠道" in error_msg:
                detailed_msg = (
                    f"支付渠道暂时不可用：{error_msg}\n\n"
                    "可能的原因：\n"
                    "• 支付渠道临时维护中\n"
                    "• 需要在商户后台完成渠道签约\n\n"
                    "建议操作：\n"
                    "1. 稍后重试（5-10分钟后）\n"
                    "2. 联系支付服务商客服（zpayz.cn）"
                )
                logging.error(f"[PAYMENT] Channel error: {error_msg}")
            else:
                detailed_msg = (
                    f"创建订单失败：{error_msg}\n\n"
                    f"调试信息：\n"
                    f"• 套餐类型: {plan_id}\n"
                    f"• 支付方式: alipay"
                )
                logging.error(f"[PAYMENT] Create order failed - plan_type: {plan_id}, error: {error_msg}")

            QMessageBox.critical(self, self.i18n.tr("membership.payment.create_order_failed"), detailed_msg)

    def _on_wxpay_selected(self, plan_id: str):
        """处理微信支付"""
        from gaiya.core.auth_client import AuthClient
        from gaiya.core.async_worker import AsyncNetworkWorker
        import logging

        pay_type = "wxpay"
        self._current_pay_type = pay_type  # 保存支付类型用于回调
        self._current_plan_id = plan_id  # 保存套餐ID用于回调

        logging.info(f"[支付调试] 微信支付 - plan_type: {plan_id}, pay_type: {pay_type}")

        # Create progress dialog
        self._payment_progress = QProgressDialog(
            "正在创建支付订单...",
            "取消",
            0, 0,  # Indeterminate progress bar
            self
        )
        self._payment_progress.setWindowTitle("请稍候")
        self._payment_progress.setWindowModality(Qt.WindowModal)
        self._payment_progress.setMinimumDuration(0)  # Show immediately
        self._payment_progress.show()

        # ✅ 性能优化: 使用异步Worker避免UI卡顿
        auth_client = AuthClient()
        self._payment_worker = AsyncNetworkWorker(
            auth_client.create_payment_order,
            plan_type=plan_id,
            pay_type=pay_type
        )
        self._payment_worker.success.connect(self._on_wxpay_order_created)
        self._payment_worker.error.connect(self._on_payment_error)
        self._payment_worker.start()

    def _on_wxpay_order_created(self, result: dict):
        """微信支付订单创建成功回调"""
        from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton
        from PySide6.QtCore import QUrl, QTimer, Qt
        from PySide6.QtGui import QDesktopServices, QPixmap
        from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
        from gaiya.core.auth_client import AuthClient
        import logging

        # Close progress dialog
        if hasattr(self, '_payment_progress') and self._payment_progress:
            self._payment_progress.close()
            self._payment_progress = None

        logging.info(f"[支付调试] 微信支付订单创建结果: {result}")

        if result.get("success"):
            # 新方式: 使用二维码支付
            qrcode_url = result.get("qrcode_url")
            out_trade_no = result.get("out_trade_no")
            trade_no = result.get("trade_no")
            amount = result.get("amount")
            plan_name = result.get("plan_name", "Pro月度订阅")
            pay_type = getattr(self, "_current_pay_type", "") or result.get("pay_type", "") or "wxpay"
            if pay_type == "alipay":
                pay_type_name = "支付宝"
            elif pay_type == "wxpay":
                pay_type_name = "微信支付"
            else:
                pay_type_name = "支付宝或微信"

            logging.info(f"[PAYMENT] Order created: {out_trade_no}, trade_no: {trade_no}")
            logging.info(f"[PAYMENT] QR code URL: {qrcode_url[:80] if qrcode_url else 'None'}...")

            # 创建二维码支付对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("扫码支付")
            dialog.setModal(True)
            dialog.setMinimumSize(400, 500)

            layout = QVBoxLayout(dialog)
            layout.setSpacing(20)
            layout.setContentsMargins(30, 30, 30, 30)

            # 标题
            title = QLabel(f"购买 {plan_name}")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title.setStyleSheet("font-size: 18px; font-weight: bold;")
            layout.addWidget(title)

            # 金额
            amount_label = QLabel(f"¥{amount:.2f}")
            amount_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            amount_label.setStyleSheet("font-size: 24px; color: #FF6B35; font-weight: bold;")
            layout.addWidget(amount_label)

            # 二维码占位符
            qr_label = QLabel("正在加载二维码...")
            qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            qr_label.setMinimumSize(300, 300)
            qr_label.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ddd; border-radius: 8px;")
            layout.addWidget(qr_label)

            # 提示信息
            hint = QLabel(f"请使用{pay_type_name}扫描二维码完成支付")
            hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hint.setStyleSheet("color: #666; font-size: 14px;")
            layout.addWidget(hint)

            # 订单号
            order_label = QLabel(f"订单号: {out_trade_no}")
            order_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            order_label.setStyleSheet("color: #999; font-size: 12px;")
            layout.addWidget(order_label)

            # 按钮布局
            from PySide6.QtWidgets import QHBoxLayout
            button_layout = QHBoxLayout()

            # 取消按钮
            cancel_btn = QPushButton("取消支付")
            cancel_btn.clicked.connect(lambda: self._cancel_payment_dialog(dialog))
            button_layout.addWidget(cancel_btn)

            # 已完成支付按钮
            confirm_btn = QPushButton("已完成支付")
            confirm_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
            confirm_btn.clicked.connect(lambda: self._confirm_payment_manually(dialog, out_trade_no, plan_name))
            button_layout.addWidget(confirm_btn)

            layout.addLayout(button_layout)

            # 保存对话框引用
            self.payment_polling_dialog = dialog
            self.current_out_trade_no = out_trade_no
            self.current_trade_no = trade_no
            self.current_plan_name = plan_name

            # 下载并显示二维码
            def download_qrcode():
                if not hasattr(self, 'network_manager'):
                    self.network_manager = QNetworkAccessManager(self)

                request = QNetworkRequest(QUrl(qrcode_url))
                reply = self.network_manager.get(request)

                def on_finished():
                    if reply.error() == QNetworkReply.NetworkError.NoError:
                        data = reply.readAll()
                        pixmap = QPixmap()
                        pixmap.loadFromData(data)

                        if not pixmap.isNull():
                            scaled_pixmap = pixmap.scaled(280, 280, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                            qr_label.setPixmap(scaled_pixmap)
                            logging.info(f"[PAYMENT] QR code loaded successfully")
                        else:
                            qr_label.setText("二维码加载失败\n请刷新重试")
                            logging.error(f"[PAYMENT] Failed to parse QR code image")
                    else:
                        error_msg = reply.errorString()
                        qr_label.setText(f"二维码加载失败\n{error_msg}")
                        logging.error(f"[PAYMENT] Failed to download QR code: {error_msg}")

                    reply.deleteLater()

                reply.finished.connect(on_finished)

            download_qrcode()

            # 启动支付状态轮询
            auth_client = AuthClient()
            self.payment_timer = QTimer()
            self.payment_timer.setInterval(3000)
            self.payment_timer.timeout.connect(partial(self._check_payment_status, out_trade_no, trade_no, auth_client))
            self.payment_timer.start()

            # 显示对话框
            dialog.exec()
        else:
            error_msg = result.get("error", "创建订单失败")

            if "MERCHANT_STATUS_NOT_NORMAL" in error_msg or "渠道" in error_msg:
                detailed_msg = (
                    f"支付渠道暂时不可用：{error_msg}\n\n"
                    "可能的原因：\n"
                    "• 支付渠道临时维护中\n"
                    "• 需要在商户后台完成渠道签约\n\n"
                    "建议操作：\n"
                    "1. 稍后重试（5-10分钟后）\n"
                    "2. 联系支付服务商客服（zpayz.cn）"
                )
                logging.error(f"[PAYMENT] Channel error: {error_msg}")
            else:
                detailed_msg = (
                    f"创建订单失败：{error_msg}\n\n"
                    f"调试信息：\n"
                    f"• 套餐类型: {plan_id}\n"
                    f"• 支付方式: wxpay"
                )
                logging.error(f"[PAYMENT] Create order failed - plan_type: {plan_id}, error: {error_msg}")

            QMessageBox.critical(self, self.i18n.tr("membership.payment.create_order_failed"), detailed_msg)

    def _on_payment_error(self, error_msg: str):
        """支付订单创建失败的通用错误处理"""
        from PySide6.QtWidgets import QMessageBox
        import logging

        # Close progress dialog
        if hasattr(self, '_payment_progress') and self._payment_progress:
            self._payment_progress.close()
            self._payment_progress = None

        # 从保存的上下文获取套餐和支付类型
        plan_id = getattr(self, '_current_plan_id', 'unknown')
        pay_type = getattr(self, '_current_pay_type', 'unknown')

        # 根据错误类型生成详细消息
        if "MERCHANT_STATUS_NOT_NORMAL" in error_msg or "渠道" in error_msg:
            detailed_msg = (
                f"支付渠道暂时不可用：{error_msg}\n\n"
                "可能的原因：\n"
                "• 支付渠道临时维护中\n"
                "• 需要在商户后台完成渠道签约\n\n"
                "建议操作：\n"
                "1. 稍后重试（5-10分钟后）\n"
                "2. 联系支付服务商客服（zpayz.cn）"
            )
            logging.error(f"[PAYMENT] Channel error: {error_msg}")
        else:
            detailed_msg = (
                f"创建订单失败：{error_msg}\n\n"
                f"调试信息：\n"
                f"• 套餐类型: {plan_id}\n"
                f"• 支付方式: {pay_type}"
            )
            logging.error(f"[PAYMENT] Create order failed - plan_type: {plan_id}, error: {error_msg}")

        QMessageBox.critical(self, self.i18n.tr("membership.payment.create_order_failed"), detailed_msg)

    def _on_stripe_selected(self, plan_id: str):
        """处理Stripe国际支付"""
        from PySide6.QtWidgets import QMessageBox
        from gaiya.core.auth_client import AuthClient
        from gaiya.core.async_worker import AsyncNetworkWorker
        import logging

        auth_client = AuthClient()

        logging.info(f"[STRIPE] 创建Stripe Checkout Session - plan_type: {plan_id}")

        # 获取用户信息
        user_id = auth_client.get_user_id()
        email = auth_client.get_user_email()

        logging.info(f"[STRIPE] 用户信息 - user_id: {user_id}, email: {email}")

        if not user_id or not email:
            error_msg = "用户信息不完整，请重新登录"
            logging.error(f"[STRIPE] {error_msg}")
            QMessageBox.critical(self, self.i18n.tr("membership.payment.error"), error_msg)
            return

        # Save context for callbacks
        self._current_pay_type = "stripe"
        self._current_plan_id = plan_id

        # Create progress dialog
        self._payment_progress = QProgressDialog(
            "正在创建支付订单...",
            "取消",
            0, 0,  # Indeterminate progress bar
            self
        )
        self._payment_progress.setWindowTitle("请稍候")
        self._payment_progress.setWindowModality(Qt.WindowModal)
        self._payment_progress.setMinimumDuration(0)  # Show immediately
        self._payment_progress.show()

        # 使用异步Worker避免UI卡顿
        self._payment_worker = AsyncNetworkWorker(
            auth_client.create_stripe_checkout_session,
            plan_type=plan_id,
            user_id=user_id,
            user_email=email
        )
        self._payment_worker.success.connect(self._on_stripe_session_created)
        self._payment_worker.error.connect(self._on_payment_error)
        self._payment_worker.start()

    def _on_stripe_session_created(self, result: dict):
        """Stripe Checkout Session创建成功回调"""
        from PySide6.QtWidgets import QMessageBox
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        import logging

        # Close progress dialog
        if hasattr(self, '_payment_progress') and self._payment_progress:
            self._payment_progress.close()
            self._payment_progress = None

        logging.info(f"[STRIPE] Checkout Session创建结果: {result}")

        if result.get("success"):
            checkout_url = result.get("checkout_url")
            session_id = result.get("session_id")

            logging.info(f"[STRIPE] Opening Stripe Checkout: {checkout_url[:100] if checkout_url else 'None'}...")
            logging.info(f"[STRIPE] Session ID: {session_id}")

            # 在浏览器中打开Stripe Checkout页面
            QDesktopServices.openUrl(QUrl(checkout_url))

            # 显示提示信息
            QMessageBox.information(
                self,
                "支付窗口已打开",
                "Stripe支付页面已在浏览器中打开。\n\n"
                "请在浏览器中完成支付。\n"
                "支付成功后，会员权益将自动激活。"
            )
        else:
            error_msg = result.get("error", "创建支付会话失败")
            plan_id = self._current_plan_id
            detailed_msg = (
                f"创建Stripe支付会话失败：{error_msg}\n\n"
                f"调试信息：\n"
                f"• 套餐类型: {plan_id}"
            )
            logging.error(f"[STRIPE] Create checkout session failed: {error_msg}")
            QMessageBox.critical(self, self.i18n.tr("membership.payment.create_session_failed"), detailed_msg)

    def _on_plan_button_clicked(self, plan_id: str):
        """处理套餐按钮点击 - 显示支付方式选择对话框"""
        try:
            # 设置选中的套餐
            self.selected_plan_id = plan_id

            # 更新卡片样式（选中状态）
            self._on_plan_card_clicked(plan_id)

            # 显示支付方式选择对话框
            self._show_payment_method_dialog(plan_id)
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"点击升级会员按钮时发生错误：\n\n{str(e)}")

    def _on_purchase_clicked(self):
        """处理前往付费按钮点击 - 使用真实支付流程"""
        from PySide6.QtWidgets import QMessageBox
        from PySide6.QtCore import QUrl, QTimer
        from PySide6.QtGui import QDesktopServices
        from gaiya.core.auth_client import AuthClient

        # 默认使用微信支付（支付方式选择UI已屏蔽）
        pay_type = "wxpay"

        # 获取选中的支付方式（已屏蔽）
        # selected_button = self.payment_method_group.checkedButton()
        # if not selected_button:
        #     QMessageBox.warning(self, self.i18n.tr("message.info"), "请选择支付方式")
        #     return
        # pay_type = selected_button.property("pay_type")

        # ✅ 性能优化: 使用异步Worker避免UI卡顿
        from gaiya.core.async_worker import AsyncNetworkWorker
        auth_client = AuthClient()

        # 保存支付上下文
        self._current_pay_type = pay_type
        self._current_plan_id = self.selected_plan_id

        # 添加日志输出以便调试
        import logging
        logging.info(f"[支付调试] 准备创建订单 - plan_type: {self.selected_plan_id}, pay_type: {pay_type}")

        # 创建异步Worker
        self._payment_worker = AsyncNetworkWorker(
            auth_client.create_payment_order,
            plan_type=self.selected_plan_id,
            pay_type=pay_type
        )
        self._payment_worker.success.connect(self._on_purchase_order_created)
        self._payment_worker.error.connect(self._on_payment_error)
        self._payment_worker.start()

    def _on_purchase_order_created(self, result: dict):
        """订单创建成功回调"""
        from PySide6.QtWidgets import QMessageBox
        from PySide6.QtCore import QUrl, QTimer
        from PySide6.QtGui import QDesktopServices
        from gaiya.core.auth_client import AuthClient
        from functools import partial
        from urllib.parse import urlencode
        import logging

        # 获取支付上下文
        pay_type = self._current_pay_type

        logging.info(f"[支付调试] 订单创建结果: {result}")

        # 订单创建成功，直接打开支付页面
        payment_url = result.get("payment_url")
        params = result.get("params", {})
        out_trade_no = result.get("out_trade_no")
        trade_no = result.get("trade_no")

        # 拼接支付参数到URL
        query_string = urlencode(params)
        full_payment_url = f"{payment_url}?{query_string}"

        logging.info(f"[PAYMENT] Opening payment URL: {full_payment_url[:100]}...")
        logging.info(f"[PAYMENT] Order No: {out_trade_no}, Type: {pay_type}")

        # 在浏览器中打开支付URL
        QDesktopServices.openUrl(QUrl(full_payment_url))

        # 显示等待支付对话框（非阻塞）
        self.payment_polling_dialog = QMessageBox(self)
        self.payment_polling_dialog.setWindowTitle(self.i18n.tr("account.payment.waiting_payment"))
        self.payment_polling_dialog.setText(
            "正在等待支付完成...\n\n"
            "请在打开的浏览器页面中完成支付。\n"
            "支付完成后，此窗口将自动关闭。"
        )
        self.payment_polling_dialog.setStandardButtons(QMessageBox.StandardButton.Cancel)
        self.payment_polling_dialog.setIcon(QMessageBox.Icon.Information)

        # 创建定时器轮询支付状态
        self.payment_timer = QTimer()
        self.payment_timer.setInterval(3000)  # 每3秒查询一次

        # 创建AuthClient实例用于轮询
        auth_client = AuthClient()

        # 使用 partial 避免 Lambda 循环引用
        self.payment_timer.timeout.connect(partial(self._check_payment_status, out_trade_no, trade_no, auth_client))
        self.payment_timer.start()
        logging.info(f"[PAYMENT] Started payment polling for order: {out_trade_no}")

        # 监听取消按钮
        self.payment_polling_dialog.rejected.connect(self._stop_payment_polling)

        # 显示对话框（非阻塞）
        self.payment_polling_dialog.show()

    def _check_payment_status(self, out_trade_no: str, trade_no: str, auth_client):
        """检查支付状态 - 异步调用"""
        # ✅ 性能优化: 使用异步Worker避免UI卡顿
        from gaiya.core.async_worker import AsyncNetworkWorker

        # 如果上一次查询还在进行中，跳过本次查询
        if hasattr(self, '_status_check_worker') and self._status_check_worker.isRunning():
            import logging
            logging.info("[PAYMENT] Previous status check still running, skipping...")
            return
        
        # 记录轮询开始
        import logging
        logging.info(f"[PAYMENT] Checking payment status for order: {out_trade_no}")

        # 创建异步Worker
        self._status_check_worker = AsyncNetworkWorker(
            auth_client.query_payment_order,
            out_trade_no,
            trade_no=trade_no
        )
        self._status_check_worker.success.connect(self._on_payment_status_checked)
        self._status_check_worker.error.connect(self._on_payment_status_check_error)
        self._status_check_worker.start()

    def _on_payment_status_checked(self, result: dict):
        """支付状态查询成功回调"""
        from PySide6.QtWidgets import QMessageBox
        import logging

        order = result.get("order", {})
        status = order.get("status")

        logging.info(f"[PAYMENT] Status check result: {status}")

        # ✅ 新增: 绕过 Vercel 缓存 - 无论查询结果如何,都尝试调用 manual_upgrade
        # 该接口会主动查询 Z-Pay 真实状态并激活会员(如果已支付)
        from gaiya.core.auth_client import AuthClient
        try:
            auth_client = AuthClient()
            user_id = auth_client.get_user_id()
            plan_name = getattr(self, "current_plan_name", "Pro订阅")
            out_trade_no = getattr(self, "current_out_trade_no", None)

            plan_type_map = {
                "Pro月度订阅": "pro_monthly",
                "Pro年度订阅": "pro_yearly",
                "团队合伙人": "team_partner"
            }
            plan_type = plan_type_map.get(plan_name, "pro_monthly")

            if out_trade_no and user_id:
                logging.info(f"[PAYMENT] Vercel query returned: {status}, trying manual upgrade to verify real status...")
                upgrade_result = auth_client.manual_upgrade_subscription(
                    user_id=user_id,
                    plan_type=plan_type,
                    out_trade_no=out_trade_no
                )

                if upgrade_result.get("success"):
                    # 真实支付成功!
                    logging.info("[PAYMENT] Manual upgrade succeeded - payment is CONFIRMED!")
                    self._stop_payment_polling()

                    # ✅ P1-1.5: 刷新会员状态后同步到AI客户端
                    new_tier = upgrade_result.get("user_tier", "free")
                    if hasattr(self, "ai_client") and self.ai_client:
                        self.ai_client.set_user_tier(new_tier)
                        logging.info(f"[AI Client] 会员升级后已同步tier: {new_tier}")

                    # 刷新会员状态
                    self.account_tab_widget = None
                    self._load_account_tab()
                    if hasattr(self, "update_account_display"):
                        self.update_account_display()

                    QMessageBox.information(
                        self,
                        "支付成功",
                        f"{plan_name}已成功激活!\n\n会员状态已更新"
                    )
                else:
                    # 真的未支付
                    error_msg = upgrade_result.get('error', '')
                    if 'not paid' in error_msg.lower() or 'unpaid' in error_msg.lower():
                        logging.info("[PAYMENT] Manual upgrade confirms: order not paid yet, continue polling...")
                    else:
                        logging.warning(f"[PAYMENT] Manual upgrade failed: {error_msg}")

        except Exception as e:
            logging.error(f"[PAYMENT] Manual upgrade check error: {e}")

    def _on_payment_status_check_error(self, error_msg: str):
        """支付状态查询失败回调(不中断轮询,静默记录)"""
        import logging
        logging.warning(f"[PAYMENT] Status check error (continuing polling): {error_msg}")

    def _confirm_payment_manually(self, dialog, out_trade_no, plan_name):
        """手动确认支付完成"""
        from PySide6.QtWidgets import QMessageBox
        from gaiya.core.auth_client import AuthClient
        import logging

        # 停止轮询
        if hasattr(self, 'payment_timer'):
            self.payment_timer.stop()

        # 关闭对话框
        dialog.close()

        logging.info(f"[PAYMENT] User manually confirmed payment: {out_trade_no}")

        # 直接触发会员升级
        try:
            # 提取user_id和plan_type
            auth_client = AuthClient()
            user_id = auth_client.get_user_id()

            # 从plan_name推断plan_type
            plan_type_map = {
                "Pro月度订阅": "pro_monthly",
                "Pro年度订阅": "pro_yearly",
                "团队合伙人": "team_partner"
            }
            plan_type = plan_type_map.get(plan_name, "pro_monthly")

            logging.info(f"[PAYMENT] Triggering manual upgrade for user {user_id}, plan {plan_type}")

            # 调用手动升级API
            result = auth_client.trigger_manual_upgrade(
                out_trade_no=out_trade_no,
                user_id=user_id,
                plan_type=plan_type
            )

            if result.get("success"):
                # 刷新会员状态
                from gaiya.core.auth_client import AuthClient
                auth_client = AuthClient()
                subscription_result = auth_client.get_subscription_status()

                if subscription_result.get("success"):
                    new_tier = subscription_result.get('user_tier', 'free')
                    logging.info(f"[PAYMENT] Subscription status refreshed: {new_tier}")

                    # ✅ P1-1.5: 支付成功后同步tier到AI客户端
                    if hasattr(self, "ai_client") and self.ai_client:
                        self.ai_client.set_user_tier(new_tier)
                        logging.info(f"[AI Client] 会员升级后已同步tier: {new_tier}")

                    QMessageBox.information(self, "支付成功", f"{plan_name}已成功激活!\n\n会员状态已更新")

                    # 刷新UI显示
                    if hasattr(self, 'update_account_display'):
                        self.update_account_display()
                else:
                    QMessageBox.information(self, "支付成功", f"{plan_name}已成功激活!\n\n请重启应用以刷新会员状态。")

                logging.info(f"[PAYMENT] Manual upgrade successful: {out_trade_no}")
            else:
                error_msg = result.get("error", "激活失败")
                QMessageBox.warning(self, "激活失败", f"会员激活失败: {error_msg}\n\n请联系客服处理")
                logging.error(f"[PAYMENT] Manual upgrade failed: {error_msg}")

        except Exception as e:
            logging.error(f"[PAYMENT] Manual upgrade error: {e}")
            QMessageBox.critical(self, "错误", f"激活过程出错: {str(e)}\n\n请联系客服处理")

    def _cancel_payment_dialog(self, dialog):
        """取消支付对话框"""
        import logging
        # 停止轮询
        if hasattr(self, 'payment_timer'):
            self.payment_timer.stop()

        # 关闭对话框
        dialog.close()

        logging.info(f"[PAYMENT] Payment cancelled by user")

    def _stop_payment_polling(self):
        """停止支付状态轮询"""
        if hasattr(self, 'payment_timer'):
            self.payment_timer.stop()

        if hasattr(self, 'payment_polling_dialog'):
            self.payment_polling_dialog.close()

    def on_timeline_task_changed(self, task_index, new_start_minutes, new_end_minutes):
        """时间轴任务时间改变时更新表格"""
        if 0 <= task_index < len(self.timeline_editor.tasks):
            # 更新表格中的时间
            if task_index < self.tasks_table.rowCount():
                # 获取时间控件
                start_widget = self.tasks_table.cellWidget(task_index, 0)
                end_widget = self.tasks_table.cellWidget(task_index, 1)

                if start_widget and end_widget:
                    # 转换分钟为 QTime
                    start_hours = new_start_minutes // 60
                    start_mins = new_start_minutes % 60
                    end_hours = new_end_minutes // 60
                    end_mins = new_end_minutes % 60

                    start_widget.setTime(QTime(start_hours, start_mins))
                    end_widget.setTime(QTime(end_hours, end_mins))

            # 如果有相邻任务也被影响，同步更新
            # 更新下一个任务
            if task_index + 1 < len(self.timeline_editor.tasks):
                next_task = self.timeline_editor.tasks[task_index + 1]
                next_start_min = self.timeline_editor.time_to_minutes(next_task['start'])
                next_end_min = self.timeline_editor.time_to_minutes(next_task['end'])

                if task_index + 1 < self.tasks_table.rowCount():
                    next_start_widget = self.tasks_table.cellWidget(task_index + 1, 0)
                    next_end_widget = self.tasks_table.cellWidget(task_index + 1, 1)

                    if next_start_widget and next_end_widget:
                        next_start_widget.setTime(QTime(next_start_min // 60, next_start_min % 60))
                        next_end_widget.setTime(QTime(next_end_min // 60, next_end_min % 60))

            # 更新上一个任务
            if task_index > 0:
                prev_task = self.timeline_editor.tasks[task_index - 1]
                prev_start_min = self.timeline_editor.time_to_minutes(prev_task['start'])
                prev_end_min = self.timeline_editor.time_to_minutes(prev_task['end'])

                prev_start_widget = self.tasks_table.cellWidget(task_index - 1, 0)
                prev_end_widget = self.tasks_table.cellWidget(task_index - 1, 1)

                if prev_start_widget and prev_end_widget:
                    prev_start_widget.setTime(QTime(prev_start_min // 60, prev_start_min % 60))
                    prev_end_widget.setTime(QTime(prev_end_min // 60, prev_end_min % 60))

    def on_table_item_changed(self, item):
        """表格项改变时的处理(任务名称修改)"""
        # 只处理任务名称列(第2列)的修改
        if item and item.column() == 2:
            # 使用防抖，避免频繁刷新时间轴
            if not hasattr(self, '_table_refresh_timer'):
                self._table_refresh_timer = QTimer()
                self._table_refresh_timer.setSingleShot(True)
                self._table_refresh_timer.timeout.connect(self.refresh_timeline_from_table)
            
            # 重置定时器
            if self._table_refresh_timer.isActive():
                self._table_refresh_timer.stop()
            self._table_refresh_timer.start(300)  # 300ms防抖

    def refresh_timeline_from_table(self):
        """从表格刷新时间轴"""
        tasks = []
        for row in range(self.tasks_table.rowCount()):
            start_widget = self.tasks_table.cellWidget(row, 0)
            end_widget = self.tasks_table.cellWidget(row, 1)
            name_item = self.tasks_table.item(row, 2)
            color_widget = self.tasks_table.cellWidget(row, 3)

            if start_widget and end_widget and name_item and color_widget:
                color_input = color_widget.findChild(QLineEdit)

                start_time = start_widget.time().toString("HH:mm")
                end_time = end_widget.time().toString("HH:mm")

                # 处理 24:00
                if end_widget.property("is_midnight"):
                    end_time = "24:00"
                elif end_time == "00:00" and row == self.tasks_table.rowCount() - 1:
                    end_time = "24:00"

                task = {
                    "start": start_time,
                    "end": end_time,
                    "task": name_item.text(),
                    "color": color_input.text() if color_input else "#4CAF50"
                }
                tasks.append(task)

        # 刷新时间轴编辑器（延迟执行，避免阻塞）
        if hasattr(self, 'timeline_editor') and self.timeline_editor:
            QTimer.singleShot(50, lambda: self.timeline_editor.set_tasks(tasks) if self.timeline_editor else None)

    def load_tasks_to_table(self):
        """加载任务到表格（优化性能，分批创建UI组件）"""
        # 暂时阻塞itemChanged信号,避免在加载时触发同步
        self.tasks_table.blockSignals(True)
        
        # 禁用UI更新，加快批量操作
        self.tasks_table.setUpdatesEnabled(False)

        self.tasks_table.setRowCount(len(self.tasks))

        # 批量创建UI组件，使用延迟刷新避免阻塞
        for row, task in enumerate(self.tasks):
            # 设置行高以适配36px按钮
            self.tasks_table.setRowHeight(row, 48)

            # 开始时间
            start_time = QTimeEdit()
            start_time.setStyleSheet(StyleManager.input_time())
            start_time.setDisplayFormat("HH:mm")
            # 特殊处理 24:00
            if task['start'] == "24:00":
                start_time.setTime(QTime(0, 0))  # 显示为 00:00
            else:
                start_time.setTime(QTime.fromString(task['start'], "HH:mm"))
            self.tasks_table.setCellWidget(row, 0, start_time)

            # 结束时间
            end_time = QTimeEdit()
            end_time.setStyleSheet(StyleManager.input_time())
            end_time.setDisplayFormat("HH:mm")
            # 特殊处理 24:00
            if task['end'] == "24:00":
                end_time.setTime(QTime(0, 0))  # 显示为 00:00,但保存时会处理
                # 添加一个属性标记这是 24:00
                end_time.setProperty("is_midnight", True)
            else:
                end_time.setTime(QTime.fromString(task['end'], "HH:mm"))
            self.tasks_table.setCellWidget(row, 1, end_time)

            # 任务名称
            name_item = QTableWidgetItem(task['task'])
            self.tasks_table.setItem(row, 2, name_item)

            # 颜色选择
            color_widget = QWidget()
            color_layout = QHBoxLayout(color_widget)
            color_layout.setContentsMargins(4, 4, 4, 4)

            # 隐藏的颜色值输入框(用于存储数据)
            color_input = QLineEdit(task['color'])
            color_input.setVisible(False)

            # 可点击的色块按钮
            color_btn = QPushButton()
            color_btn.setFixedSize(50, 30)
            color_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {task['color']};
                    border: 2px solid #CCCCCC;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    border: 2px solid #999999;
                }}
            """)
            color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            color_btn.setToolTip("点击选择颜色")
            # 点击色块直接打开颜色选择器
            color_btn.clicked.connect(partial(self.choose_color, color_input))

            # 当颜色值改变时,更新色块样式
            def on_color_changed(text):
                color_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {text};
                        border: 2px solid #CCCCCC;
                        border-radius: 4px;
                    }}
                    QPushButton:hover {{
                        border: 2px solid #999999;
                    }}
                """)
                # 使用防抖，避免频繁刷新时间轴
                if not hasattr(self, '_timeline_refresh_timer'):
                    self._timeline_refresh_timer = QTimer()
                    self._timeline_refresh_timer.setSingleShot(True)
                    self._timeline_refresh_timer.timeout.connect(self.refresh_timeline_from_table)

                # 重置定时器
                if self._timeline_refresh_timer.isActive():
                    self._timeline_refresh_timer.stop()
                self._timeline_refresh_timer.start(300)  # 300ms防抖

            color_input.textChanged.connect(on_color_changed)

            color_layout.addWidget(color_input)
            color_layout.addWidget(color_btn)
            color_layout.addStretch()

            self.tasks_table.setCellWidget(row, 3, color_widget)

            # 文字颜色选择
            text_color = task.get('text_color', '#FFFFFF')  # 默认白色
            text_color_widget = QWidget()
            text_color_layout = QHBoxLayout(text_color_widget)
            text_color_layout.setContentsMargins(4, 4, 4, 4)

            # 隐藏的颜色值输入框(用于存储数据)
            text_color_input = QLineEdit(text_color)
            text_color_input.setVisible(False)

            # 可点击的色块按钮
            text_color_btn = QPushButton()
            text_color_btn.setFixedSize(50, 30)
            text_color_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {text_color};
                    border: 2px solid #CCCCCC;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    border: 2px solid #999999;
                }}
            """)
            text_color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            text_color_btn.setToolTip("点击选择颜色")
            # 点击色块直接打开颜色选择器
            text_color_btn.clicked.connect(partial(self.choose_color, text_color_input))

            # 当颜色值改变时,更新色块样式
            def on_text_color_changed(text):
                text_color_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {text};
                        border: 2px solid #CCCCCC;
                        border-radius: 4px;
                    }}
                    QPushButton:hover {{
                        border: 2px solid #999999;
                    }}
                """)
                # 使用防抖，避免频繁刷新时间轴
                if not hasattr(self, '_timeline_refresh_timer'):
                    self._timeline_refresh_timer = QTimer()
                    self._timeline_refresh_timer.setSingleShot(True)
                    self._timeline_refresh_timer.timeout.connect(self.refresh_timeline_from_table)

                # 重置定时器
                if self._timeline_refresh_timer.isActive():
                    self._timeline_refresh_timer.stop()
                self._timeline_refresh_timer.start(300)  # 300ms防抖

            text_color_input.textChanged.connect(on_text_color_changed)

            text_color_layout.addWidget(text_color_input)
            text_color_layout.addWidget(text_color_btn)
            text_color_layout.addStretch()

            self.tasks_table.setCellWidget(row, 4, text_color_widget)

            # 删除按钮 (仅图标,极简风格)
            delete_btn = QPushButton("🗑")
            # 使用 partial 避免 Lambda 循环引用
            delete_btn.clicked.connect(partial(self.delete_task, row))
            delete_btn.setFixedSize(32, 32)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: 1px solid #CCCCCC;
                    border-radius: 4px;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #F5F5F5;
                    border: 1px solid #999999;
                }
            """)
            delete_btn.setToolTip("删除任务")
            delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.tasks_table.setCellWidget(row, 5, delete_btn)

        # 恢复UI更新
        self.tasks_table.setUpdatesEnabled(True)

        # 延迟调整列宽，避免阻塞
        QTimer.singleShot(100, lambda: self.tasks_table.resizeColumnsToContents() if hasattr(self, 'tasks_table') else None)

        # 恢复itemChanged信号
        self.tasks_table.blockSignals(False)

        # 更新表格高度
        self.update_table_height()

        # 延迟刷新时间轴编辑器，避免阻塞UI
        if hasattr(self, 'timeline_editor') and self.timeline_editor:
            QTimer.singleShot(100, lambda: self.timeline_editor.set_tasks(self.tasks) if self.timeline_editor else None)

    def add_task(self):
        """添加新任务,自动接续上一个任务的结束时间"""
        row = self.tasks_table.rowCount()
        self.tasks_table.insertRow(row)

        # 设置行高以适配36px按钮
        self.tasks_table.setRowHeight(row, 48)

        # 智能计算开始时间:接续上一个任务的结束时间
        if row > 0:
            # 获取上一个任务的结束时间
            prev_end_widget = self.tasks_table.cellWidget(row - 1, 1)
            if prev_end_widget:
                prev_end_time = prev_end_widget.time()
                new_start_time = prev_end_time
                # 默认新任务持续1小时
                new_end_time = prev_end_time.addSecs(3600)
            else:
                # 如果获取失败,使用默认值
                new_start_time = QTime(9, 0)
                new_end_time = QTime(10, 0)
        else:
            # 第一个任务,使用默认值
            new_start_time = QTime(9, 0)
            new_end_time = QTime(10, 0)

        # 设置开始时间
        start_time = QTimeEdit()
        start_time.setStyleSheet(StyleManager.input_time())
        start_time.setDisplayFormat("HH:mm")
        start_time.setTime(new_start_time)
        self.tasks_table.setCellWidget(row, 0, start_time)

        # 设置结束时间
        end_time = QTimeEdit()
        end_time.setStyleSheet(StyleManager.input_time())
        end_time.setDisplayFormat("HH:mm")
        end_time.setTime(new_end_time)
        self.tasks_table.setCellWidget(row, 1, end_time)

        name_item = QTableWidgetItem("新任务")
        self.tasks_table.setItem(row, 2, name_item)

        # 根据当前任务数量从色板中循环选择颜色
        default_color = self.COLOR_PALETTE[row % len(self.COLOR_PALETTE)]

        # 颜色选择
        color_widget = QWidget()
        color_layout = QHBoxLayout(color_widget)
        color_layout.setContentsMargins(4, 4, 4, 4)

        # 隐藏的颜色值输入框(用于存储数据)
        color_input = QLineEdit(default_color)
        color_input.setVisible(False)

        # 可点击的色块按钮
        color_btn = QPushButton()
        color_btn.setFixedSize(50, 30)
        color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {default_color};
                border: 2px solid #CCCCCC;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border: 2px solid #999999;
            }}
        """)
        color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        color_btn.setToolTip("点击选择颜色")
        color_btn.clicked.connect(partial(self.choose_color, color_input))

        # 当颜色值改变时,更新色块样式
        def on_color_changed(text):
            color_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {text};
                    border: 2px solid #CCCCCC;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    border: 2px solid #999999;
                }}
            """)

        color_input.textChanged.connect(on_color_changed)

        color_layout.addWidget(color_input)
        color_layout.addWidget(color_btn)
        color_layout.addStretch()

        self.tasks_table.setCellWidget(row, 3, color_widget)

        # 文字颜色选择（默认白色）
        text_color_widget = QWidget()
        text_color_layout = QHBoxLayout(text_color_widget)
        text_color_layout.setContentsMargins(4, 4, 4, 4)

        # 隐藏的颜色值输入框(用于存储数据)
        text_color_input = QLineEdit("#FFFFFF")
        text_color_input.setVisible(False)

        # 可点击的色块按钮
        text_color_btn = QPushButton()
        text_color_btn.setFixedSize(50, 30)
        text_color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFFFFF;
                border: 2px solid #CCCCCC;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border: 2px solid #999999;
            }}
        """)
        text_color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        text_color_btn.setToolTip("点击选择颜色")
        text_color_btn.clicked.connect(partial(self.choose_color, text_color_input))

        # 当颜色值改变时,更新色块样式
        def on_text_color_changed(text):
            text_color_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {text};
                    border: 2px solid #CCCCCC;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    border: 2px solid #999999;
                }}
            """)

        text_color_input.textChanged.connect(on_text_color_changed)

        text_color_layout.addWidget(text_color_input)
        text_color_layout.addWidget(text_color_btn)
        text_color_layout.addStretch()

        self.tasks_table.setCellWidget(row, 4, text_color_widget)

        # 删除按钮 (仅图标,极简风格)
        delete_btn = QPushButton("🗑")
        # 使用 partial 避免 Lambda 循环引用
        delete_btn.clicked.connect(partial(self.delete_task, row))
        delete_btn.setFixedSize(32, 32)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #F5F5F5;
                border: 1px solid #999999;
            }
        """)
        delete_btn.setToolTip("删除任务")
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tasks_table.setCellWidget(row, 5, delete_btn)

        # 刷新时间轴
        self.refresh_timeline_from_table()

        # 更新表格高度
        self.update_table_height()

    def update_table_height(self):
        """根据当前任务数量动态更新表格高度"""
        row_height = 60
        header_height = 30
        min_visible_rows = 8
        max_visible_rows = 15

        actual_row_count = self.tasks_table.rowCount()
        visible_rows = max(min_visible_rows, min(actual_row_count, max_visible_rows))
        calculated_height = header_height + (visible_rows * row_height) + 20

        self.tasks_table.setMinimumHeight(calculated_height)
        self.tasks_table.setMaximumHeight(calculated_height)

    def delete_task(self, row):
        """删除任务"""
        reply = QMessageBox.question(
            self, '确认删除',
            f'确定要删除第 {row + 1} 个任务吗?',
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.tasks_table.removeRow(row)
            # 重新绑定删除按钮
            for r in range(self.tasks_table.rowCount()):
                delete_btn = self.tasks_table.cellWidget(r, 5)
                if delete_btn:
                    delete_btn.clicked.disconnect()
                    # 使用 partial 避免 Lambda 循环引用
                    delete_btn.clicked.connect(partial(self.delete_task, r))

            # 刷新时间轴
            self.refresh_timeline_from_table()

            # 更新表格高度
            self.update_table_height()

    def clear_all_tasks(self):
        """清空所有任务"""
        reply = QMessageBox.question(
            self, '确认清空',
            '确定要清空所有任务吗?\n\n这将删除表格中的所有任务(不会立即保存,需要点击【保存所有设置】)',
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.tasks_table.setRowCount(0)
            # 刷新时间轴（延迟执行）
            if hasattr(self, 'timeline_editor') and self.timeline_editor:
                QTimer.singleShot(50, lambda: self.timeline_editor.set_tasks([]) if self.timeline_editor else None)
            # 更新表格高度
            self.update_table_height()
            QMessageBox.information(self, self.i18n.tr("message.info"), "所有任务已清空\n\n记得点击【保存所有设置】按钮来保存更改")

    def load_default_template(self):
        """在初始化时默认加载24小时模板(静默加载,不弹窗)"""
        template_path = self.get_resource_path("tasks_template_24h.json")

        if not template_path.exists():
            return

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                self.tasks = json.load(f)
        except Exception:
            # 如果加载失败,保持空列表
            self.tasks = []

    def save_as_template(self):
        """将当前任务保存为自定义模板"""
        if self.tasks_table.rowCount() == 0:
            QMessageBox.warning(self, self.i18n.tr("account.message.cannot_save_empty"), "当前没有任何任务,无法保存为模板!")
            return

        # 获取现有模板列表
        meta_data = self._get_custom_templates_meta()
        existing_templates = meta_data.get('templates', [])

        # 显示智能保存对话框
        dialog = SaveTemplateDialog(existing_templates, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        template_name = dialog.get_template_name()
        if not template_name:
            return

        # 收集当前所有任务
        tasks = []
        for row in range(self.tasks_table.rowCount()):
            start_widget = self.tasks_table.cellWidget(row, 0)
            end_widget = self.tasks_table.cellWidget(row, 1)
            name_item = self.tasks_table.item(row, 2)
            color_widget = self.tasks_table.cellWidget(row, 3)

            if start_widget and end_widget and name_item and color_widget:
                color_input = color_widget.findChild(QLineEdit)

                start_time = start_widget.time().toString("HH:mm")
                end_time = end_widget.time().toString("HH:mm")

                # 处理 24:00
                if end_widget.property("is_midnight"):
                    end_time = "24:00"
                elif end_time == "00:00" and row == self.tasks_table.rowCount() - 1:
                    end_time = "24:00"

                task = {
                    "start": start_time,
                    "end": end_time,
                    "task": name_item.text(),
                    "color": color_input.text() if color_input else "#4CAF50"
                }
                tasks.append(task)

        # 保存到用户目录
        template_filename = f"tasks_custom_{template_name}.json"
        template_path = self.app_dir / template_filename

        try:
            # 保存任务文件
            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, indent=4, ensure_ascii=False)

            # 保存元数据
            from datetime import datetime
            meta_data = self._get_custom_templates_meta()

            # 检查是否已存在同名模板
            existing_template = None
            is_update = False
            for t in meta_data['templates']:
                if t['filename'] == template_filename:
                    existing_template = t
                    is_update = True
                    break

            if existing_template:
                # 更新现有模板
                existing_template['task_count'] = len(tasks)
                existing_template['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            else:
                # 添加新模板
                import uuid
                template_meta = {
                    "id": f"custom_{uuid.uuid4().hex[:8]}",
                    "name": template_name,
                    "filename": template_filename,
                    "description": f"自定义模板 ({len(tasks)}个任务)",
                    "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "task_count": len(tasks)
                }
                meta_data['templates'].append(template_meta)

            # 保存元数据
            self._save_custom_templates_meta(meta_data)

            # 刷新self.i18n.tr("config.templates.custom_label")UI
            self._reload_custom_template_combo()

            # 根据是新建还是更新显示不同的提示
            if is_update:
                success_msg = self.i18n.tr("config.messages.template_updated", template_filename=template_filename, task_count=len(tasks))
            else:
                success_msg = self.i18n.tr("config.messages.template_created", template_filename=template_filename, task_count=len(tasks))

            QMessageBox.information(
                self,
                "保存成功",
                success_msg
            )
        except Exception as e:
            QMessageBox.critical(self, "保存失败", self.i18n.tr("config.errors.template_save_failed", error=str(e)))

    def load_custom_template(self):
        """加载用户自定义模板"""
        from PySide6.QtWidgets import QFileDialog
        import glob

        # 查找所有自定义模板
        custom_templates = list(self.app_dir.glob("tasks_custom_*.json"))

        if not custom_templates:
            QMessageBox.information(
                self,
                "没有自定义模板",
                "当前没有找到任何自定义模板。\n\n您可以先配置任务,然后点击【保存为模板】按钮创建模板。"
            )
            return

        # 让用户选择模板
        from PySide6.QtWidgets import QInputDialog

        template_names = [t.name for t in custom_templates]
        template_name, ok = QInputDialog.getItem(
            self,
            "选择模板",
            "请选择要加载的自定义模板:",
            template_names,
            0,
            False
        )

        if not ok:
            return

        template_path = self.app_dir / template_name

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_tasks = json.load(f)

            # 确认加载
            reply = QMessageBox.question(
                self,
                '确认加载模板',
                self.i18n.tr("config.prompts.confirm_load_template", template_name=template_name, task_count=len(template_tasks)),
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # 清空当前任务
                self.tasks_table.setRowCount(0)

                # 加载模板任务
                self.tasks = template_tasks
                self.load_tasks_to_table()

                # 刷新时间轴（延迟执行）
                if hasattr(self, 'timeline_editor') and self.timeline_editor:
                    QTimer.singleShot(50, lambda: self.timeline_editor.set_tasks(template_tasks) if self.timeline_editor else None)

                QMessageBox.information(
                    self,
                    "加载成功",
                    f"已加载 {len(template_tasks)} 个任务\n\n记得点击【保存所有设置】按钮来应用更改"
                )

        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "错误", self.i18n.tr("config.errors.template_format_error", error=str(e)))
        except Exception as e:
            QMessageBox.critical(self, "错误", self.i18n.tr("config.errors.template_load_failed", error=str(e)))


    def _reload_preset_template_combo(self):
        """重新加载预设模板下拉框（当template_manager延迟初始化完成后调用）"""
        try:
            if not hasattr(self, 'template_manager') or not self.template_manager:
                logging.warning("TemplateManager尚未初始化，延迟500ms后重试")
                # 延迟重试
                QTimer.singleShot(500, self._reload_preset_template_combo)
                return

            if not hasattr(self, 'preset_template_combo'):
                logging.error("preset_template_combo未找到，无法重新加载预设模板下拉框")
                return

            logging.info("TemplateManager已初始化，重新加载预设模板下拉框")

            # 清空下拉框
            self.preset_template_combo.clear()

            # 重新添加所有预设模板到下拉框
            templates = self.template_manager.get_all_templates(include_custom=False)
            for template in templates:
                # Use i18n translation for template name if available
                template_name = self.i18n.tr(f"templates.names.{template['id']}", fallback=template['name'])
                # 存储模板信息:显示名称,数据为filename
                self.preset_template_combo.addItem(template_name, template['filename'])
                # 设置工具提示
                idx = self.preset_template_combo.count() - 1
                self.preset_template_combo.setItemData(idx, template.get('description', ''), Qt.ItemDataRole.ToolTipRole)

            logging.info(f"成功加载 {len(templates)} 个预设模板到下拉框")

        except Exception as e:
            logging.error(f"重新加载预设模板下拉框失败: {e}")

    def _load_selected_preset_template(self):
        """加载选中的预设模板"""
        if not hasattr(self, 'preset_template_combo'):
            return

        # 获取选中项的filename
        current_data = self.preset_template_combo.currentData()

        if not current_data:
            QMessageBox.warning(self, self.i18n.tr("message.warning"), "请先选择一个预设模板")
            return

        # 调用已有的load_template方法
        self.load_template(current_data)

    def _on_template_type_changed(self, index):
        """模板类型切换时的处理"""
        if not hasattr(self, 'template_type_combo'):
            return

        # 获取当前选中的类型
        template_type = self.template_type_combo.currentData()

        # 根据类型加载模板列表
        self._load_templates_by_type(template_type)

    def _load_templates_by_type(self, template_type):
        """根据类型加载模板列表到统一下拉框"""
        if not hasattr(self, 'unified_template_combo'):
            return

        # 清空下拉框
        self.unified_template_combo.clear()

        if template_type == "preset":
            # 加载预设模板
            if hasattr(self, 'template_manager') and self.template_manager:
                templates = self.template_manager.get_all_templates(include_custom=False)
                for template in templates:
                    template_name = self.i18n.tr(f"templates.names.{template['id']}", fallback=template['name'])
                    # 存储: (类型, 数据)
                    self.unified_template_combo.addItem(template_name, ("preset", template['filename']))
                    # 设置工具提示
                    idx = self.unified_template_combo.count() - 1
                    self.unified_template_combo.setItemData(idx, template.get('description', ''), Qt.ItemDataRole.ToolTipRole)
            else:
                self.unified_template_combo.addItem(self.i18n.tr("tasks.labels.template_loading"), ("preset", ""))
                QTimer.singleShot(500, lambda: self._load_templates_by_type("preset"))

            # 隐藏删除按钮
            if hasattr(self, 'delete_template_btn'):
                self.delete_template_btn.setVisible(False)

        elif template_type == "custom":
            # 加载自定义模板
            meta_data = self._get_custom_templates_meta()
            templates = meta_data.get('templates', [])

            if not templates:
                self.unified_template_combo.addItem(self.i18n.tr("account.message.no_custom_templates_placeholder"), ("custom", None))
            else:
                for template in templates:
                    display_name = f"{template['name']} ({template.get('task_count', 0)}个任务)"
                    self.unified_template_combo.addItem(display_name, ("custom", template))

            # 显示删除按钮
            if hasattr(self, 'delete_template_btn'):
                self.delete_template_btn.setVisible(True)

    def _load_unified_template(self):
        """统一的模板加载方法"""
        if not hasattr(self, 'unified_template_combo'):
            return

        current_data = self.unified_template_combo.currentData()
        if not current_data:
            QMessageBox.warning(self, self.i18n.tr("message.warning"), "请先选择一个模板")
            return

        template_type, template_data = current_data

        if template_type == "preset":
            # 加载预设模板
            if not template_data:
                QMessageBox.warning(self, self.i18n.tr("message.warning"), "模板数据无效")
                return
            self.load_template(template_data)

        elif template_type == "custom":
            # 加载自定义模板
            if not template_data:
                QMessageBox.information(self, self.i18n.tr("message.info"), "请先创建自定义模板")
                return
            filename = template_data['filename']
            self._load_custom_template_by_filename(filename)


    def _get_custom_templates_meta(self):
        """获取自定义模板元数据"""
        meta_file = self.app_dir / "custom_templates_meta.json"

        if not meta_file.exists():
            return {"version": "1.0", "templates": []}

        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"加载自定义模板元数据失败: {e}")
            return {"version": "1.0", "templates": []}


    def _save_custom_templates_meta(self, meta_data):
        """保存自定义模板元数据"""
        meta_file = self.app_dir / "custom_templates_meta.json"

        try:
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(meta_data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            logging.error(f"保存自定义模板元数据失败: {e}")
            return False


    def _reload_custom_template_combo(self):
        """重新加载自定义模板下拉框"""
        try:
            if not hasattr(self, 'custom_template_combo'):
                logging.warning("custom_template_combo未找到")
                return

            # 清空下拉框
            self.custom_template_combo.clear()

            # 获取自定义模板元数据
            meta_data = self._get_custom_templates_meta()
            templates = meta_data.get('templates', [])

            if not templates:
                # 没有自定义模板时显示提示
                self.custom_template_combo.addItem(self.i18n.tr("account.message.no_custom_templates_placeholder"), None)
            else:
                # 添加自定义模板到下拉框
                for template in templates:
                    display_name = f"{template['name']} ({template.get('task_count', 0)}个任务)"
                    self.custom_template_combo.addItem(display_name, template)

            logging.info(f"成功加载 {len(templates)} 个自定义模板到下拉框")

        except Exception as e:
            logging.error(f"重新加载自定义模板下拉框失败: {e}")


    def _load_selected_custom_template(self):
        """加载选中的自定义模板"""
        if not hasattr(self, 'custom_template_combo'):
            return

        index = self.custom_template_combo.currentIndex()
        if index < 0:
            return

        template = self.custom_template_combo.itemData(index)
        if not template:
            QMessageBox.information(self, self.i18n.tr("message.info"), "请先创建自定义模板")
            return

        filename = template['filename']
        self._load_custom_template_by_filename(filename)


    def _delete_selected_custom_template(self):
        """删除选中的自定义模板"""
        if not hasattr(self, 'custom_template_combo'):
            return

        index = self.custom_template_combo.currentIndex()
        if index < 0:
            return

        template = self.custom_template_combo.itemData(index)
        if not template:
            QMessageBox.information(self, self.i18n.tr("message.info"), "请先创建自定义模板")
            return

        self._delete_custom_template(template)


    def _load_custom_template_by_filename(self, filename):
        """通过文件名加载自定义模板"""
        template_path = self.app_dir / filename

        if not template_path.exists():
            QMessageBox.warning(self, self.i18n.tr("membership.payment.error"), f"模板文件不存在:\n{filename}")
            return

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_tasks = json.load(f)

            # 确认加载
            reply = QMessageBox.question(
                self,
                '确认加载模板',
                f'即将加载自定义模板: {filename}\n\n包含 {len(template_tasks)} 个任务\n\n当前表格中的任务将被替换,是否继续?',
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # 清空当前任务
                self.tasks_table.setRowCount(0)

                # 加载模板任务
                self.tasks = template_tasks
                self.load_tasks_to_table()

                # 刷新时间轴（延迟执行）
                if hasattr(self, 'timeline_editor') and self.timeline_editor:
                    QTimer.singleShot(50, lambda: self.timeline_editor.set_tasks(template_tasks) if self.timeline_editor else None)

                QMessageBox.information(
                    self,
                    "加载成功",
                    f"已加载 {len(template_tasks)} 个任务\n\n记得点击【保存所有设置】按钮来应用更改"
                )

        except json.JSONDecodeError as e:
            QMessageBox.critical(self, self.i18n.tr("membership.payment.error"), f"模板文件格式错误:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, self.i18n.tr("membership.payment.error"), f"加载模板失败:\n{str(e)}")


    def _delete_custom_template(self, template):
        """删除自定义模板"""
        try:
            # 确认删除
            reply = QMessageBox.question(
                self,
                '确认删除',
                self.i18n.tr("config.dialogs.confirm_delete_template", template_name=template["name"]),
                QMessageBox.Yes | QMessageBox.No
            )

            if reply != QMessageBox.Yes:
                return

            # 删除模板文件
            template_path = self.app_dir / template['filename']
            if template_path.exists():
                template_path.unlink()

            # 从元数据中移除
            meta_data = self._get_custom_templates_meta()
            meta_data['templates'] = [t for t in meta_data['templates'] if t['filename'] != template['filename']]
            self._save_custom_templates_meta(meta_data)

            # 刷新UI
            self._reload_custom_template_combo()

            QMessageBox.information(self, "删除成功", self.i18n.tr("config.dialogs.template_deleted", template_name=template['name']))

        except Exception as e:
            QMessageBox.critical(self, self.i18n.tr("account.message.delete_failed"), f"无法删除模板:\n{str(e)}")


    def _load_template_auto_apply_settings(self):
        """加载模板自动应用设置到表格"""
        try:
            if not hasattr(self, 'template_manager') or not self.template_manager:
                logging.warning("TemplateManager未初始化，延迟加载自动应用设置")
                # 延迟重试
                QTimer.singleShot(500, self._load_template_auto_apply_settings)
                return

            # 模板自动应用只针对预设模板（自定义模板使用时间表规则）
            templates = self.template_manager.get_all_templates(include_custom=False)
            self.template_auto_apply_table.setRowCount(len(templates))

            for row, template in enumerate(templates):
                # 模板名称（只读）
                name_item = QTableWidgetItem(template['name'])
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                name_item.setToolTip(template.get('description', ''))
                self.template_auto_apply_table.setItem(row, 0, name_item)

                # 启用自动应用（复选框）
                auto_apply = template.get('auto_apply', {})
                enabled_check = QCheckBox()
                enabled_check.setChecked(auto_apply.get('enabled', False))
                enabled_check.setStyleSheet("QCheckBox { margin-left: 20%; }")
                self.template_auto_apply_table.setCellWidget(row, 1, enabled_check)

                # 工作日复选框
                weekday_check = QCheckBox()
                conditions = auto_apply.get('conditions', [])
                weekday_check.setChecked('weekday' in conditions)
                weekday_check.setStyleSheet("QCheckBox { margin-left: 20%; }")
                self.template_auto_apply_table.setCellWidget(row, 2, weekday_check)

                # 周末复选框
                weekend_check = QCheckBox()
                weekend_check.setChecked('weekend' in conditions)
                weekend_check.setStyleSheet("QCheckBox { margin-left: 20%; }")
                self.template_auto_apply_table.setCellWidget(row, 3, weekend_check)

                # 节假日复选框
                holiday_check = QCheckBox()
                holiday_check.setChecked('holiday' in conditions)
                holiday_check.setStyleSheet("QCheckBox { margin-left: 20%; }")
                self.template_auto_apply_table.setCellWidget(row, 4, holiday_check)

            logging.info(f"已加载 {len(templates)} 个模板的自动应用设置")

        except Exception as e:
            logging.error(f"加载模板自动应用设置失败: {e}")

    def _save_template_auto_apply_settings(self):
        """保存表格中的自动应用设置到templates_config.json"""
        try:
            if not hasattr(self, 'template_manager') or not self.template_manager:
                QMessageBox.warning(self, self.i18n.tr("message.warning"), "模板管理器未初始化")
                return

            # 模板自动应用只针对预设模板（自定义模板使用时间表规则）
            templates = self.template_manager.get_all_templates(include_custom=False)
            row_count = self.template_auto_apply_table.rowCount()

            updated_count = 0
            for row in range(row_count):
                if row >= len(templates):
                    break

                template = templates[row]
                template_id = template['id']

                # 读取复选框状态
                enabled_widget = self.template_auto_apply_table.cellWidget(row, 1)
                weekday_widget = self.template_auto_apply_table.cellWidget(row, 2)
                weekend_widget = self.template_auto_apply_table.cellWidget(row, 3)
                holiday_widget = self.template_auto_apply_table.cellWidget(row, 4)

                enabled = enabled_widget.isChecked() if enabled_widget else False

                # 构建conditions列表
                conditions = []
                if weekday_widget and weekday_widget.isChecked():
                    conditions.append('weekday')
                if weekend_widget and weekend_widget.isChecked():
                    conditions.append('weekend')
                if holiday_widget and holiday_widget.isChecked():
                    conditions.append('holiday')

                # 使用TemplateManager的set_auto_apply方法保存
                success = self.template_manager.set_auto_apply(
                    template_id=template_id,
                    enabled=enabled,
                    conditions=conditions,
                    priority=5 if enabled else 0  # 启用时设置默认优先级
                )

                if success:
                    updated_count += 1

            if updated_count > 0:
                QMessageBox.information(
                    self,
                    "保存成功",
                    f"已保存 {updated_count} 个模板的自动应用设置"
                )
                logging.info(f"已保存 {updated_count} 个模板的自动应用设置")
            else:
                QMessageBox.warning(self, self.i18n.tr("message.warning"), "没有设置被保存")

        except Exception as e:
            logging.error(f"保存模板自动应用设置失败: {e}")
            QMessageBox.critical(self, self.i18n.tr("membership.payment.error"), f"保存失败:\n{str(e)}")

    def _test_template_matching(self):
        """测试日期匹配功能"""
        try:
            from datetime import datetime
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDateEdit, QPushButton, QTextEdit

            if not hasattr(self, 'template_manager') or not self.template_manager:
                QMessageBox.warning(self, self.i18n.tr("message.warning"), "模板管理器未初始化")
                return

            # 创建测试对话框
            dialog = QDialog(self)
            dialog.setWindowTitle(self.i18n.tr("tasks.messages.test_template_match"))
            dialog.setMinimumWidth(500)
            dialog.setMinimumHeight(350)

            layout = QVBoxLayout()

            # 说明
            hint_label = QLabel(self.i18n.tr("templates.auto_apply.test_instruction"))
            hint_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
            layout.addWidget(hint_label)

            # 日期选择器
            date_edit = QDateEdit()
            date_edit.setCalendarPopup(True)
            date_edit.setDate(datetime.now().date())
            date_edit.setDisplayFormat("yyyy-MM-dd")
            layout.addWidget(date_edit)

            # 结果显示区域
            result_text = QTextEdit()
            result_text.setReadOnly(True)
            result_text.setMinimumHeight(150)
            layout.addWidget(result_text)

            def perform_test():
                selected_date = date_edit.date().toPython()
                test_datetime = datetime(selected_date.year, selected_date.month, selected_date.day)

                # 获取日期类型
                date_type = self.template_manager.get_date_type(test_datetime)

                # 获取匹配的模板
                matching_templates = self.template_manager.get_matching_templates(test_datetime)
                best_match = self.template_manager.get_best_match_template(test_datetime)

                # 构建结果文本
                result_lines = []
                result_lines.append(f"测试日期: {test_datetime.strftime('%Y-%m-%d %A')}")
                result_lines.append(f"\n日期类型: {date_type}")
                result_lines.append(f"  - weekday: 工作日")
                result_lines.append(f"  - weekend: 周末")
                result_lines.append(f"  - holiday: 节假日")

                result_lines.append(f"\n匹配到 {len(matching_templates)} 个启用自动应用的模板:")

                if matching_templates:
                    for i, tmpl in enumerate(matching_templates, 1):
                        auto_apply = tmpl.get('auto_apply', {})
                        priority = auto_apply.get('priority', 0)
                        conditions = auto_apply.get('conditions', [])
                        result_lines.append(
                            f"  {i}. {tmpl['name']} (优先级: {priority}, 条件: {', '.join(conditions) if conditions else '任意'})"
                        )

                    if best_match:
                        result_lines.append(f"\n✅ 最佳匹配（优先级最高）: {best_match['name']}")
                        result_lines.append(f"   → 将自动加载: {best_match['filename']}")
                else:
                    result_lines.append("  (无匹配模板)")
                    result_lines.append("\n❌ 没有模板会在该日期自动应用")
                    result_lines.append("   → 将使用默认24小时模板")

                result_text.setText("\n".join(result_lines))

            # 测试按钮
            test_btn = QPushButton(self.i18n.tr("general.text_8461"))
            test_btn.setStyleSheet(StyleManager.button_minimal())
            test_btn.clicked.connect(perform_test)
            layout.addWidget(test_btn)

            # 关闭按钮
            close_btn = QPushButton(self.i18n.tr("button.close"))
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)

            dialog.setLayout(layout)

            # 初始执行一次测试
            perform_test()

            dialog.exec()

        except Exception as e:
            logging.error(f"测试模板匹配失败: {e}")
            QMessageBox.critical(self, self.i18n.tr("membership.payment.error"), f"测试失败:\n{str(e)}")

    def load_template(self, template_filename):
        """加载预设模板"""
        template_path = self.get_resource_path(template_filename)

        if not template_path.exists():
            QMessageBox.warning(
                self,
                "模板不存在",
                f"找不到模板文件: {template_filename}\n\n请确保模板文件在程序目录中"
            )
            return

        try:
            # 读取模板文件
            with open(template_path, 'r', encoding='utf-8') as f:
                template_tasks = json.load(f)

            # 确认加载
            reply = QMessageBox.question(
                self,
                '确认加载模板',
                f'即将加载 {template_filename}\n\n包含 {len(template_tasks)} 个任务\n\n当前表格中的任务将被替换,是否继续?',
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # 清空当前任务
                self.tasks_table.setRowCount(0)

                # 加载模板任务
                self.tasks = template_tasks
                self.load_tasks_to_table()

                # 刷新时间轴（延迟执行）
                if hasattr(self, 'timeline_editor') and self.timeline_editor:
                    QTimer.singleShot(50, lambda: self.timeline_editor.set_tasks(template_tasks) if self.timeline_editor else None)

                QMessageBox.information(
                    self,
                    "加载成功",
                    f"已加载 {len(template_tasks)} 个任务\n\n记得点击【保存所有设置】按钮来应用更改"
                )

        except json.JSONDecodeError as e:
            QMessageBox.critical(self, self.i18n.tr("membership.payment.error"), f"模板文件格式错误:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, self.i18n.tr("membership.payment.error"), f"加载模板失败:\n{str(e)}")

    def set_height_preset(self, height):
        """设置预设高度"""
        self.height_spin.setValue(height)
        self.update_height_preset_buttons()

    def on_height_value_changed(self, value):
        """高度值改变时更新按钮状态"""
        self.update_height_preset_buttons()

    def update_height_preset_buttons(self):
        """更新预设高度按钮的选中状态"""
        current_height = self.height_spin.value()
        for btn, height in self.height_preset_buttons:
            # 只有当前值等于预设值时才选中按钮
            is_selected = current_height == height
            btn.setChecked(is_selected)

            # 更新按钮样式
            if is_selected:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2196F3;
                        color: white;
                        border: 2px solid #1976D2;
                        padding: 5px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #1976D2;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f0f0f0;
                        color: #333;
                        border: 1px solid #ccc;
                        padding: 5px;
                    }
                    QPushButton:hover {
                        background-color: #e0e0e0;
                        border: 1px solid #999;
                    }
                """)

    def _update_autostart_status_label(self):
        """更新自启动状态标签"""
        if not hasattr(self, 'autostart_status_label'):
            return

        if self.autostart_check.isChecked():
            self.autostart_status_label.setText(self.i18n.tr("account.message.autostart_enabled"))
            self.autostart_status_label.setStyleSheet("color: #4CAF50; font-size: 11px;")
        else:
            self.autostart_status_label.setText(self.i18n.tr("account.message.autostart_disabled"))
            self.autostart_status_label.setStyleSheet("color: #888888; font-size: 11px;")

    def on_marker_type_changed(self, marker_type):
        """时间标记类型改变时的处理"""
        # 根据类型启用/禁用相关控件
        is_image_mode = marker_type in ['image', 'gif']

        # 查找控件(需要通过父widget查找)
        try:
            # 启用/禁用图片路径输入
            self.marker_image_input.setEnabled(is_image_mode)
            # 启用/禁用图片大小设置
            self.marker_size_spin.setEnabled(is_image_mode)
            # 启用/禁用 X 轴偏移设置
            self.marker_x_offset_spin.setEnabled(is_image_mode)
            # 启用/禁用 Y 轴偏移设置
            self.marker_y_offset_spin.setEnabled(is_image_mode)

            # 禁用/启用线条相关设置
            self.marker_color_input.setEnabled(not is_image_mode)
            self.marker_color_btn.setEnabled(not is_image_mode)
            self.marker_width_spin.setEnabled(not is_image_mode)
        except Exception as e:
            pass  # 初始化时可能还没有创建所有控件

    def set_marker_size_preset(self, size):
        """设置预设标记大小"""
        self.marker_size_spin.setValue(size)
        self.update_marker_size_preset_buttons()

    def on_marker_size_value_changed(self, value):
        """标记大小改变时更新按钮状态并保存到预设"""
        self.update_marker_size_preset_buttons()
        self._save_current_preset_params()

    def update_marker_size_preset_buttons(self):
        """更新预设标记大小按钮的选中状态"""
        current_size = self.marker_size_spin.value()
        for btn, size in self.marker_size_preset_buttons:
            # 只有当前值等于预设值时才选中按钮
            is_selected = current_size == size
            btn.setChecked(is_selected)

            # 更新按钮样式
            if is_selected:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2196F3;
                        color: white;
                        border: 2px solid #1976D2;
                        padding: 5px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #1976D2;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f0f0f0;
                        color: #333;
                        border: 1px solid #ccc;
                        padding: 5px;
                    }
                    QPushButton:hover {
                        background-color: #e0e0e0;
                        border: 1px solid #999;
                    }
                """)

    def _save_current_preset_params(self):
        """保存当前预设的参数(从UI控件读取)"""
        if not hasattr(self, 'marker_preset_manager') or not self.marker_preset_manager:
            return

        current_preset_id = self.marker_preset_manager.get_current_preset_id()
        params = {
            "size": self.marker_size_spin.value(),
            "x_offset": self.marker_x_offset_spin.value(),
            "y_offset": self.marker_y_offset_spin.value()
        }

        self.marker_preset_manager.save_preset_params(current_preset_id, params)
        logging.debug(f"Saved params for preset {current_preset_id}: {params}")

    def _on_preset_combo_changed(self, index):
        """处理预设下拉框切换事件"""
        preset_id = self.marker_preset_combo.itemData(index)
        if not preset_id:
            return

        # 更新预设管理器当前预设
        self.marker_preset_manager.set_current_preset_id(preset_id)

        # 获取预设参数并更新UI控件
        params = self.marker_preset_manager.get_preset_params(preset_id)
        self.marker_size_spin.setValue(params["size"])
        self.marker_x_offset_spin.setValue(params["x_offset"])
        self.marker_y_offset_spin.setValue(params["y_offset"])

        # 更新文件选择器可见性
        self._update_marker_image_visibility()

        # 获取预设图片路径并更新
        preset = self.marker_preset_manager.get_preset(preset_id)
        if preset:
            if preset_id == "custom":
                # 自定义预设:保持用户上次选择的路径
                pass
            else:
                # 内置预设:使用预设图片路径
                marker_path = self.marker_preset_manager.get_marker_path(preset["file"])
                self.marker_image_input.setText(marker_path)

                # 自动切换到image/gif类型
                ext = Path(preset["file"]).suffix.lower()
                if ext in ['.gif', '.webp']:
                    self.marker_type_combo.setCurrentText('gif')
                else:
                    self.marker_type_combo.setCurrentText('image')

        logging.info(f"Switched to marker preset: {preset_id}, params: {params}")

    def _update_marker_image_visibility(self):
        """更新标记图片整行的可见性(仅在自定义预设时显示)"""
        if not hasattr(self, 'marker_image_row') or not hasattr(self, 'marker_preset_combo'):
            return

        current_preset_id = self.marker_preset_combo.currentData()
        is_custom = (current_preset_id == "custom")

        # 显示或隐藏整行(包括标签和控件)
        self.marker_image_row.setVisible(is_custom)

        logging.debug(f"Marker image row visibility: {'visible' if is_custom else 'hidden'} (preset={current_preset_id})")

    def choose_marker_image(self):
        """选择时间标记图片"""
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("图片文件 (*.jpg *.jpeg *.png *.gif *.webp)")
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setViewMode(QFileDialog.Detail)

        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                file_path = selected_files[0]
                # 使用相对路径(如果文件在应用目录下)
                try:
                    rel_path = Path(file_path).relative_to(self.app_dir)
                    self.marker_image_input.setText(str(rel_path))
                except ValueError:
                    # 不在应用目录下,使用绝对路径
                    self.marker_image_input.setText(file_path)

                # 根据文件扩展名自动切换类型
                ext = Path(file_path).suffix.lower()
                if ext in ['.gif', '.webp']:
                    self.marker_type_combo.setCurrentText('gif')
                else:
                    self.marker_type_combo.setCurrentText('image')

                # 自动切换到自定义预设
                self.marker_preset_manager.set_custom_image_path(file_path)
                self.marker_preset_manager.set_current_preset_id("custom")

                # 更新下拉框选中"自定义图片"
                for i in range(self.marker_preset_combo.count()):
                    if self.marker_preset_combo.itemData(i) == "custom":
                        self.marker_preset_combo.setCurrentIndex(i)
                        break

    def choose_color(self, input_widget):
        """选择颜色"""
        current_color = QColor(input_widget.text())
        color = QColorDialog.getColor(current_color, self, "选择颜色")

        if color.isValid():
            input_widget.setText(color.name())

            # 更新对应的颜色预览按钮样式
            if input_widget == self.bg_color_input:
                self.bg_color_preview.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color.name()};
                        border: 2px solid #CCCCCC;
                        border-radius: 4px;
                    }}
                    QPushButton:hover {{
                        border: 2px solid #999999;
                    }}
                """)
            elif input_widget == self.marker_color_input:
                self.marker_color_preview.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color.name()};
                        border: 2px solid #CCCCCC;
                        border-radius: 4px;
                    }}
                    QPushButton:hover {{
                        border: 2px solid #999999;
                    }}
                """)

    def update_color_preview(self, input_widget, preview_label):
        """更新颜色预览"""
        color = input_widget.text()
        preview_label.setFixedSize(30, 20)
        preview_label.setStyleSheet(f"background-color: {color}; border: 1px solid #ccc;")
        input_widget.textChanged.connect(lambda text: preview_label.setStyleSheet(f"background-color: {text}; border: 1px solid #ccc;"))

    def load_config(self):
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                logging.error(f"配置文件JSON解析错误: {e}")
            except Exception as e:
                logging.error(f"加载配置文件失败: {e}")
        return {}

    def load_tasks(self):
        """加载任务"""
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                logging.error(f"任务文件JSON解析错误: {e}")
            except Exception as e:
                logging.error(f"加载任务文件失败: {e}")
        return []

    def check_task_overlap(self, tasks):
        """检查任务时间是否重叠"""
        for i in range(len(tasks)):
            for j in range(i + 1, len(tasks)):
                task1 = tasks[i]
                task2 = tasks[j]

                # 转换为分钟数进行比较
                start1 = self.time_to_minutes(task1['start'])
                end1 = self.time_to_minutes(task1['end'])
                start2 = self.time_to_minutes(task2['start'])
                end2 = self.time_to_minutes(task2['end'])

                # 检查重叠:任务1的结束时间 > 任务2的开始时间 AND 任务1的开始时间 < 任务2的结束时间
                if (end1 > start2 and start1 < end2):
                    return (i + 1, j + 1, task1['task'], task2['task'])

        return None

    def time_to_minutes(self, time_str):
        """将 HH:mm 转换为分钟数(使用统一的time_utils)

        特殊处理: 24:00 表示一天结束(午夜),返回 1440 分钟
        """
        seconds = time_utils.time_str_to_seconds(time_str)
        return seconds // 60

    def save_all(self) -> None:
        """Save all settings to config file

        Collects configuration from UI widgets and persists to disk using debounced save.
        Also updates tasks.json with current task list.
        """
        try:
            # 收集通知配置
            # 收集开始前提醒时间（安全检查，避免属性不存在）
            before_start_minutes = []
            if hasattr(self, 'notify_before_start_checks'):
                before_start_minutes = [
                    minutes for minutes, checkbox in self.notify_before_start_checks.items()
                    if checkbox.isChecked()
                ]
            else:
                # 如果属性不存在，使用配置中的默认值
                notification_config = self.config.get('notification', {})
                before_start_minutes = notification_config.get('before_start_minutes', [10, 5])

            # 收集结束前提醒时间（安全检查，避免属性不存在）
            before_end_minutes = []
            if hasattr(self, 'notify_before_end_checks'):
                before_end_minutes = [
                    minutes for minutes, checkbox in self.notify_before_end_checks.items()
                    if checkbox.isChecked()
                ]
            else:
                # 如果属性不存在，使用配置中的默认值
                notification_config = self.config.get('notification', {})
                before_end_minutes = notification_config.get('before_end_minutes', [5])

            # 处理开机自启动设置
            autostart_enabled = self.autostart_check.isChecked() if hasattr(self, 'autostart_check') else False
            if hasattr(self, 'autostart_manager') and self.autostart_manager:
                if self.autostart_manager.set_enabled(autostart_enabled):
                    logging.info(f"自启动设置{'启用' if autostart_enabled else '禁用'}成功")
                else:
                    logging.error(f"自启动设置{'启用' if autostart_enabled else '禁用'}失败")
                    QMessageBox.warning(
                        self,
                        "警告",
                        f"开机自启动设置失败\n\n可能需要管理员权限或系统限制"
                    )

            # 保存配置
            config = {
                "bar_height": self.height_spin.value(),
                "position": "bottom",  # 固定位置为屏幕底部
                "background_color": self.bg_color_input.text(),
                # 将百分比(0-100)转换为0-255
                "background_opacity": int(self.opacity_slider.value() * 255 / 100),
                "marker_color": self.marker_color_input.text(),
                "marker_width": self.marker_width_spin.value(),
                "marker_type": self.marker_type_combo.currentText(),
                # 标记图片路径:使用预设系统的正确路径(而非UI输入框的文本)
                "marker_image_path": self.marker_preset_manager.get_current_marker_path() if self.marker_preset_manager else self.marker_image_input.text(),
                "marker_size": self.marker_size_spin.value(),
                "marker_speed": self.marker_speed_spin.value(),
                "marker_always_visible": self.marker_always_visible_check.isChecked(),
                "marker_x_offset": self.marker_x_offset_spin.value(),
                "marker_y_offset": self.marker_y_offset_spin.value(),
                "screen_index": self.screen_spin.value(),
                "update_interval": self.interval_spin.value(),
                "enable_shadow": self.shadow_check.isChecked(),
                "corner_radius": self.radius_spin.value(),
                "autostart_enabled": autostart_enabled,
                "theme": {
                    "mode": "preset",
                    "current_theme_id": self.selected_theme_id if hasattr(self, 'selected_theme_id') and self.selected_theme_id else self.config.get('theme', {}).get('current_theme_id', 'business'),
                    "auto_apply_task_colors": False
                },
                "notification": {
                    "enabled": (getattr(self, 'notify_enabled_check', None) and self.notify_enabled_check.isChecked()) if hasattr(self, 'notify_enabled_check') else self.config.get('notification', {}).get('enabled', True),
                    "before_start_minutes": before_start_minutes,
                    "on_start": (getattr(self, 'notify_on_start_check', None) and self.notify_on_start_check.isChecked()) if hasattr(self, 'notify_on_start_check') else self.config.get('notification', {}).get('on_start', True),
                    "before_end_minutes": before_end_minutes,
                    "on_end": (getattr(self, 'notify_on_end_check', None) and self.notify_on_end_check.isChecked()) if hasattr(self, 'notify_on_end_check') else self.config.get('notification', {}).get('on_end', False),
                    "sound_enabled": (getattr(self, 'notify_sound_check', None) and self.notify_sound_check.isChecked()) if hasattr(self, 'notify_sound_check') else self.config.get('notification', {}).get('sound_enabled', True),
                    "sound_file": "",
                    "quiet_hours": {
                        "enabled": (getattr(self, 'quiet_enabled_check', None) and self.quiet_enabled_check.isChecked()) if hasattr(self, 'quiet_enabled_check') else self.config.get('notification', {}).get('quiet_hours', {}).get('enabled', False),
                        "start": self.quiet_start_time.time().toString("HH:mm") if hasattr(self, 'quiet_start_time') else self.config.get('notification', {}).get('quiet_hours', {}).get('start', '22:00'),
                        "end": self.quiet_end_time.time().toString("HH:mm") if hasattr(self, 'quiet_end_time') else self.config.get('notification', {}).get('quiet_hours', {}).get('end', '08:00')
                    }
                },
                "scene": {
                    "enabled": (getattr(self, 'scene_enabled_check', None) and self.scene_enabled_check.isChecked()) if hasattr(self, 'scene_enabled_check') else self.config.get('scene', {}).get('enabled', False),
                    "current_scene": self.scene_combo.itemData(self.scene_combo.currentIndex()) if hasattr(self, 'scene_combo') and self.scene_combo.currentIndex() >= 0 else self.config.get('scene', {}).get('current_scene'),
                    "show_progress_bar": (getattr(self, 'show_progress_in_scene_check', None) and self.show_progress_in_scene_check.isChecked()) if hasattr(self, 'show_progress_in_scene_check') else self.config.get('scene', {}).get('show_progress_bar', False)
                },
                "danmaku": {
                    "enabled": (getattr(self, 'danmaku_enabled_check', None) and self.danmaku_enabled_check.isChecked()) if hasattr(self, 'danmaku_enabled_check') else self.config.get('danmaku', {}).get('enabled', True),
                    "frequency": self.danmaku_frequency_spin.value() if hasattr(self, 'danmaku_frequency_spin') else self.config.get('danmaku', {}).get('frequency', 30),
                    "speed": self.danmaku_speed_spin.value() if hasattr(self, 'danmaku_speed_spin') else self.config.get('danmaku', {}).get('speed', 1.0),
                    "font_size": self.danmaku_font_size_spin.value() if hasattr(self, 'danmaku_font_size_spin') else self.config.get('danmaku', {}).get('font_size', 14),
                    # 将百分比(0-100)转换为0-1浮点数
                    "opacity": round(self.danmaku_opacity_slider.value() / 100, 2) if hasattr(self, 'danmaku_opacity_slider') else self.config.get('danmaku', {}).get('opacity', 1.0),
                    "max_count": self.danmaku_max_count_spin.value() if hasattr(self, 'danmaku_max_count_spin') else self.config.get('danmaku', {}).get('max_count', 3),
                    "y_offset": self.danmaku_y_offset_spin.value() if hasattr(self, 'danmaku_y_offset_spin') else self.config.get('danmaku', {}).get('y_offset', 80),
                    "color_mode": self.danmaku_color_mode_combo.itemData(self.danmaku_color_mode_combo.currentIndex()) if hasattr(self, 'danmaku_color_mode_combo') else self.config.get('danmaku', {}).get('color_mode', 'auto')
                },
                "activity_tracking": {
                    "enabled": self.activity_tracking_enabled.isChecked() if hasattr(self, 'activity_tracking_enabled') else self.config.get('activity_tracking', {}).get('enabled', False),
                    "polling_interval": self.activity_polling_interval.value() if hasattr(self, 'activity_polling_interval') else self.config.get('activity_tracking', {}).get('polling_interval', 5),
                    "min_session_duration": self.config.get('activity_tracking', {}).get('min_session_duration', 5),
                    "data_retention_days": self.activity_retention_days.value() if hasattr(self, 'activity_retention_days') else self.config.get('activity_tracking', {}).get('data_retention_days', 90)
                },
                "behavior_recognition": {
                    "enabled": self.behavior_danmaku_enabled.isChecked() if hasattr(self, 'behavior_danmaku_enabled') else self.config.get('behavior_recognition', {}).get('enabled', False),
                    "collection_interval": self.behavior_collection_interval.value() if hasattr(self, 'behavior_collection_interval') else self.config.get('behavior_recognition', {}).get('collection_interval', 5),
                    "trigger_probability": self.behavior_trigger_probability.value() if hasattr(self, 'behavior_trigger_probability') else self.config.get('behavior_recognition', {}).get('trigger_probability', 0.4),
                    "global_cooldown": self.behavior_global_cooldown.value() if hasattr(self, 'behavior_global_cooldown') else self.config.get('behavior_recognition', {}).get('global_cooldown', 30),
                    "category_cooldown": self.behavior_category_cooldown.value() if hasattr(self, 'behavior_category_cooldown') else self.config.get('behavior_recognition', {}).get('category_cooldown', 60),
                    "tone_cooldown": self.config.get('behavior_recognition', {}).get('tone_cooldown', 120)
                }
            }

            # 合并标记图片预设配置
            if self.marker_preset_manager:
                preset_config = self.marker_preset_manager.save_to_config()
                config.update(preset_config)

            # 使用防抖动保存（此处是save_all函数，通常是手动点击保存按钮触发）
            # 更新内存中的配置
            self.config = config
            # 防抖动保存到磁盘
            self.config_debouncer.save_debounced(config)

            # 获取主题颜色（如果用户选择了预设主题）
            theme_colors = []
            if hasattr(self, 'selected_theme_id') and self.selected_theme_id:
                # 获取主题数据
                if not self.theme_manager:
                    preset_themes = ThemeManager.DEFAULT_PRESET_THEMES.copy()
                else:
                    all_themes = self.theme_manager.get_all_themes()
                    preset_themes = all_themes.get('preset_themes', {})

                theme_data = preset_themes.get(self.selected_theme_id, {})
                theme_colors = theme_data.get('task_colors', [])

            # 保存任务
            tasks = []
            logging.info(f"[保存任务] 开始从表格读取任务,表格行数: {self.tasks_table.rowCount()}")
            for row in range(self.tasks_table.rowCount()):
                start_widget = self.tasks_table.cellWidget(row, 0)
                end_widget = self.tasks_table.cellWidget(row, 1)
                name_item = self.tasks_table.item(row, 2)
                color_widget = self.tasks_table.cellWidget(row, 3)
                text_color_widget = self.tasks_table.cellWidget(row, 4)  # 文字颜色

                if start_widget and end_widget and name_item and color_widget and text_color_widget:
                    color_input = color_widget.findChild(QLineEdit)
                    text_color_input = text_color_widget.findChild(QLineEdit)

                    # 如果选择了预设主题，使用主题颜色
                    if theme_colors:
                        color_index = row % len(theme_colors)
                        task_color = theme_colors[color_index]
                    else:
                        task_color = color_input.text() if color_input else "#4CAF50"

                    start_time = start_widget.time().toString("HH:mm")
                    end_time = end_widget.time().toString("HH:mm")

                    # 检查是否是标记为午夜的 00:00(实际是 24:00)
                    if end_widget.property("is_midnight"):
                        end_time = "24:00"
                    # 如果结束时间是 00:00 且是最后一个任务或下一个任务从 00:00 开始,可能是 24:00
                    elif end_time == "00:00" and row == self.tasks_table.rowCount() - 1:
                        # 最后一个任务且结束时间是 00:00,很可能是 24:00
                        end_time = "24:00"

                    # ✅ P1-1.5: 修复跨天任务验证逻辑
                    # 验证结束时间必须大于开始时间(允许跨天任务,如23:00-07:00)
                    start_minutes = self.time_to_minutes(start_time)
                    end_minutes = self.time_to_minutes(end_time)

                    # 如果结束时间小于等于开始时间,检查是否是跨天任务
                    if end_minutes <= start_minutes:
                        # 跨天任务:计算实际时长(从开始时间到午夜 + 午夜到结束时间)
                        # 例如 23:00-07:00 = (1440-1380) + 420 = 60 + 420 = 480分钟 = 8小时
                        actual_duration = (1440 - start_minutes) + end_minutes

                        # 拒绝不合理的时长:
                        # - 太短(<5分钟):可能是输入错误
                        # - 太长(>20小时):跨天任务超过20小时不合理
                        if actual_duration < 5:
                            QMessageBox.warning(
                                self,
                                "时间错误",
                                f"第 {row + 1} 个任务的时长过短!\n\n"
                                f"任务: {name_item.text()}\n"
                                f"开始: {start_time}, 结束: {end_time}\n"
                                f"实际时长: {actual_duration}分钟\n\n"
                                f"请检查时间设置"
                            )
                            return
                        elif actual_duration > 1200:  # 20小时 = 1200分钟
                            QMessageBox.warning(
                                self,
                                "时间错误",
                                f"第 {row + 1} 个任务的时长过长!\n\n"
                                f"任务: {name_item.text()}\n"
                                f"开始: {start_time}, 结束: {end_time}\n"
                                f"实际时长: {actual_duration // 60}小时{actual_duration % 60}分钟\n\n"
                                f"跨天任务不应超过20小时"
                            )
                            return

                    # Generate stable ID based on time and task name
                    import hashlib
                    task_name = name_item.text()
                    stable_key = f"{start_time}|{end_time}|{task_name}"
                    task_id = hashlib.sha1(stable_key.encode('utf-8')).hexdigest()

                    task = {
                        "id": task_id,  # Stable ID for focus session tracking
                        "start": start_time,
                        "end": end_time,
                        "task": task_name,
                        "color": task_color,  # 使用主题颜色或用户自定义颜色
                        "text_color": text_color_input.text() if text_color_input else "#FFFFFF"
                    }
                    tasks.append(task)

            # 检查任务时间重叠
            overlap = self.check_task_overlap(tasks)
            if overlap:
                row1, row2, task1_name, task2_name = overlap
                reply = QMessageBox.warning(
                    self,
                    "时间重叠警告",
                    f"第 {row1} 个任务 ({task1_name}) 和第 {row2} 个任务 ({task2_name}) 的时间段有重叠!\n\n是否仍要保存?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return

            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, indent=4, ensure_ascii=False)

            logging.info(f"[任务保存] 任务已保存到文件: {len(tasks)}个任务")
            if tasks:
                logging.info(f"[任务保存] 第一个任务: {tasks[0].get('task', 'N/A')}, 开始: {tasks[0].get('start', 'N/A')}")
                logging.info(f"[任务保存] 最后一个任务: {tasks[-1].get('task', 'N/A')}, 结束: {tasks[-1].get('end', 'N/A')}")
            logging.info(f"[任务保存] 即将发送config_saved信号")

            QMessageBox.information(self, self.i18n.tr("message.success"), "配置和任务已保存!\n\n如果 Gaiya 正在运行,更改会自动生效。")

            self.config_saved.emit()
            logging.info(f"[任务保存] config_saved信号已发送")

        except Exception as e:
            QMessageBox.critical(self, self.i18n.tr("membership.payment.error"), f"保存失败:\n{str(e)}")

    def _on_tab_changed_for_ai_status(self, index):
        """标签页切换时，控制AI状态定时器"""
        self._start_ai_status_timer_if_needed()
    
    def refresh_quota_status(self):
        """刷新配额状态（同步版本，用于按钮点击）"""
        self.refresh_quota_status_async()
    
    def refresh_quota_status_async(self):
        """异步刷新配额状态（不阻塞UI）"""
        # 检查AI客户端是否已初始化
        if not self.ai_client:
            if hasattr(self, 'quota_label'):
                self.quota_label.setText(self.i18n.tr("account.ui.connecting_cloud"))
                self.quota_label.setStyleSheet("color: #ff9800; padding: 5px; font-weight: bold;")
            if hasattr(self, 'generate_btn'):
                self.generate_btn.setEnabled(False)
            return

        # 异步获取配额状态
        class QuotaCheckWorker(QThread):
            finished = Signal(object)

            def __init__(self, backend_url, user_id, user_tier):
                super().__init__()
                self.backend_url = backend_url
                self.user_id = user_id
                self.user_tier = user_tier

            def run(self):
                try:
                    # Vercel冷启动可能需要10-15秒，增加超时时间
                    response = requests.get(
                        f"{self.backend_url}/api/quota-status",
                        params={
                            "user_id": self.user_id,
                            "user_tier": self.user_tier
                        },
                        timeout=20  # 增加超时时间以应对Vercel冷启动
                    )
                    if response.status_code == 200:
                        self.finished.emit(response.json())
                    elif response.status_code == 404:
                        # API未部署,使用本地默认配额(不显示错误)
                        logging.debug(f"配额API未部署(404),使用默认配额")
                        default_quota = {
                            "remaining": {
                                "daily_plan": 3 if self.user_tier == "free" else 50,
                                "weekly_report": 1 if self.user_tier == "free" else 10,
                                "chat": 10 if self.user_tier == "free" else 100
                            },
                            "user_tier": self.user_tier,
                            "fallback": True  # 标记为fallback数据
                        }
                        self.finished.emit(default_quota)
                    else:
                        logging.warning(f"配额查询返回错误状态码: {response.status_code}")
                        self.finished.emit(None)
                except Exception as e:
                    logging.warning(f"配额查询失败: {str(e)}")
                    self.finished.emit(None)

        # 创建并启动工作线程
        # ⚠️ 关键修复: 使用 auth_client 的 user_tier,确保使用最新值
        current_user_tier = self.ai_client.user_tier
        if hasattr(self, 'auth_client') and self.auth_client and self.auth_client.user_info:
            current_user_tier = self.auth_client.user_info.get('user_tier', current_user_tier)
            logging.info(f"[QUOTA] 使用auth_client的tier: {current_user_tier}")

        logging.info(f"[QUOTA] 开始查询配额: user_id={self.ai_client.user_id}, user_tier={current_user_tier}")
        worker = QuotaCheckWorker(
            self.ai_client.backend_url,
            self.ai_client.user_id,
            current_user_tier
        )

        # 使用lambda包装回调，确保worker在完成后被清理
        def on_finished(quota_info):
            self._on_quota_status_finished(quota_info)
            # 断开信号连接
            worker.finished.disconnect()
            # 延迟删除worker对象
            worker.deleteLater()

        worker.finished.connect(on_finished)
        worker.start()
    
    def _on_quota_status_finished(self, quota_info):
        """配额状态检查完成回调"""
        if not hasattr(self, 'quota_label'):
            return

        if quota_info:
            remaining = quota_info.get('remaining', {})
            daily_plan_remaining = remaining.get('daily_plan', 0)
            is_fallback = quota_info.get('fallback', False)
            logging.info(f"[QUOTA] 配额查询结果: daily_plan_remaining={daily_plan_remaining}, user_tier={quota_info.get('user_tier', 'unknown')}, fallback={is_fallback}")

            if daily_plan_remaining > 0:
                self.quota_label.setText(self.i18n.tr("account.message.quota_remaining", daily_plan_remaining=daily_plan_remaining))
                self.quota_label.setStyleSheet("color: #4CAF50; padding: 5px; font-weight: bold;")
                if hasattr(self, 'generate_btn'):
                    self.generate_btn.setEnabled(True)
            else:
                self.quota_label.setText(self.i18n.tr("account.message.quota_exhausted"))
                self.quota_label.setStyleSheet("color: #FF9800; padding: 5px; font-weight: bold;")
                if hasattr(self, 'generate_btn'):
                    self.generate_btn.setEnabled(False)

            # 配额检查成功(包括fallback),停止定时器（节省资源）
            if hasattr(self, 'ai_status_timer') and self.ai_status_timer:
                if self.ai_status_timer.isActive():
                    self.ai_status_timer.stop()
                    if is_fallback:
                        logging.debug("使用默认配额(API未部署),已停止定时器")
                    else:
                        logging.info("AI状态定时器已停止（配额检查成功）")
        else:
            # 配额检查失败，可能是云服务冷启动或网络问题
            self.quota_label.setText(self.i18n.tr("account.ui.cannot_connect_cloud"))
            self.quota_label.setStyleSheet("color: #f44336; padding: 5px; font-weight: bold;")
            if hasattr(self, 'generate_btn'):
                self.generate_btn.setEnabled(True)  # 仍然允许尝试

            # 配额检查失败，可能是云服务冷启动或网络问题
            # 延迟后重试配额检查
            logging.warning("配额查询失败，可能是云服务冷启动或网络问题，5秒后重试...")
            QTimer.singleShot(5000, self.refresh_quota_status_async)

    def on_ai_generate_clicked(self):
        """处理AI生成按钮点击"""
        # 首先检查是否已登录
        if not self._check_login_and_guide(self.i18n.tr("config.ai.title")):
            return

        # 检查AI配额
        if not self._check_ai_quota():
            return

        user_input = self.ai_input.text().strip()

        if not user_input:
            QMessageBox.warning(
                self,
                "输入为空",
                "请先描述您的计划!\n\n例如: 明天9点开会1小时,然后写代码到下午5点"
            )
            return

        # 检查是否有正在运行的任务
        if self.ai_worker is not None and self.ai_worker.isRunning():
            QMessageBox.warning(
                self,
                "请稍候",
                "AI正在处理上一个请求,请稍候..."
            )
            return

        # 检查后端服务器（使用异步检查，但这里是按钮点击，需要快速反馈）
        # 先尝试快速检查，如果失败则显示提示
        if not hasattr(self, 'ai_client') or not self.ai_client:
            QMessageBox.warning(
                self,
                "AI服务正在初始化",
                "AI服务正在后台启动中,请稍候片刻再试...",
                QMessageBox.Ok
            )
            return
        
        # 云服务架构下，直接发起任务生成请求
        # 如果服务不可用，ai_client会在内部处理并显示错误信息

        # 禁用按钮并显示加载状态
        self.generate_btn.setEnabled(False)
        self.generate_btn.setText(self.i18n.tr("ai.text_3863"))

        # 创建并启动工作线程
        self.ai_worker = AIWorker(self.ai_client, user_input)

        # 使用lambda包装回调，确保worker在完成后被清理
        def on_finished(result):
            self.on_ai_generation_finished(result)
            # 断开所有信号连接
            self.ai_worker.finished.disconnect()
            self.ai_worker.error.disconnect()
            # 延迟删除worker对象
            self.ai_worker.deleteLater()
            self.ai_worker = None

        def on_error(error_msg):
            self.on_ai_generation_error(error_msg)
            # 断开所有信号连接
            self.ai_worker.finished.disconnect()
            self.ai_worker.error.disconnect()
            # 延迟删除worker对象
            self.ai_worker.deleteLater()
            self.ai_worker = None

        self.ai_worker.finished.connect(on_finished)
        self.ai_worker.error.connect(on_error)
        self.ai_worker.start()

    def on_ai_generation_finished(self, result):
        """AI生成完成的回调"""
        try:
            if result and result.get('success'):
                tasks = result.get('tasks', [])

                if not tasks:
                    QMessageBox.warning(
                        self,
                        "生成失败",
                        "AI未能生成任何任务,请尝试更详细地描述您的计划。"
                    )
                    return

                # 询问是否替换当前任务
                if self.tasks_table.rowCount() > 0:
                    reply = QMessageBox.question(
                        self,
                        '确认替换',
                        f'AI已生成 {len(tasks)} 个任务\n\n是否替换当前表格中的所有任务?',
                        QMessageBox.Yes | QMessageBox.No
                    )

                    if reply == QMessageBox.No:
                        return

                # 清空当前任务表格
                self.tasks_table.setRowCount(0)

                # 加载AI生成的任务
                self.tasks = tasks
                logging.info(f"[AI生成] 更新self.tasks,任务数: {len(self.tasks)}")
                logging.info(f"[AI生成] 第一个任务: {self.tasks[0].get('task', 'N/A') if self.tasks else 'N/A'}")
                self.load_tasks_to_table()
                logging.info(f"[AI生成] load_tasks_to_table完成,tasks_table行数: {self.tasks_table.rowCount()}")

                # ✅ P1-1.5: 自动切换到任务管理tab
                if hasattr(self, 'main_tabs'):
                    # 找到任务管理tab的索引(通常是第1个tab,索引为0)
                    task_mgmt_tab_index = 0
                    for i in range(self.main_tabs.count()):
                        if "任务" in self.main_tabs.tabText(i) or "Task" in self.main_tabs.tabText(i):
                            task_mgmt_tab_index = i
                            break
                    self.main_tabs.setCurrentIndex(task_mgmt_tab_index)
                    logging.info(f"[AI生成] 已自动切换到任务管理tab(索引={task_mgmt_tab_index})")

                # 显示成功消息
                token_usage = result.get('token_usage', 0)
                QMessageBox.information(
                    self,
                    "生成成功",
                    f"✓ 已生成 {len(tasks)} 个任务\n"
                    f"📊 Token使用: {token_usage}\n\n"
                    "记得点击【保存所有设置】按钮来保存更改"
                )

                # 清空输入框
                self.ai_input.clear()

                # 刷新配额状态
                self.refresh_quota_status()

            else:
                # result为None表示已经在ai_client中显示了错误对话框
                pass

        except Exception as e:
            QMessageBox.critical(
                self,
                "发生错误",
                f"生成任务时发生错误:\n\n{str(e)}"
            )

        finally:
            # 恢复按钮状态
            self.generate_btn.setEnabled(True)
            self.generate_btn.setText(self.i18n.tr("account.ui.ai_smart_generate"))

    def on_ai_generation_error(self, error_msg):
        """AI生成失败的回调"""
        try:
            QMessageBox.critical(
                self,
                "AI生成失败",
                f"生成任务时发生错误:\n\n{error_msg}\n\n请检查:\n1. 后端服务器是否正常运行\n2. 网络连接是否正常\n3. API密钥是否有效"
            )
        finally:
            # 恢复按钮状态
            self.generate_btn.setEnabled(True)
            self.generate_btn.setText(self.i18n.tr("account.ui.ai_smart_generate"))

    def on_banner_ai_clicked(self):
        """横幅AI生成按钮点击"""
        logging.info("[Banner] AI生成按钮被点击")
        # 打开改进版AI生成对话框
        from gaiya.ui.components import ImprovedAIGenerationDialog

        dialog = ImprovedAIGenerationDialog(self)
        logging.info("[Banner] 创建对话框实例完成")
        dialog.generation_requested.connect(self.on_improved_ai_generation)
        logging.info("[Banner] 信号连接完成,准备显示对话框")
        result = dialog.exec()
        logging.info(f"[Banner] 对话框关闭,返回值: {result}")

    def on_improved_ai_generation(self, prompt: str):
        """改进版AI对话框生成请求"""
        logging.info(f"[改进版AI生成] 收到生成请求,prompt长度: {len(prompt)}")

        # 首先检查是否已登录
        logging.info("[改进版AI生成] 检查登录状态...")
        if not self._check_login_and_guide(self.i18n.tr("config.ai.title")):
            logging.warning("[改进版AI生成] 登录检查失败,终止")
            return

        # 检查AI配额
        logging.info("[改进版AI生成] 检查AI配额...")
        if not self._check_ai_quota():
            logging.warning("[改进版AI生成] AI配额检查失败,终止")
            return

        # 检查是否有正在运行的任务
        logging.info("[改进版AI生成] 检查是否有正在运行的任务...")
        if self.ai_worker is not None and self.ai_worker.isRunning():
            logging.warning("[改进版AI生成] 发现正在运行的任务,已显示进度对话框")
            # 如果进度对话框已经存在,将其显示到前台
            if hasattr(self, 'ai_progress_dialog') and self.ai_progress_dialog:
                self.ai_progress_dialog.raise_()
                self.ai_progress_dialog.activateWindow()
            return

        # 检查后端服务器
        logging.info("[改进版AI生成] 检查AI客户端...")
        if not hasattr(self, 'ai_client') or not self.ai_client:
            logging.warning("[改进版AI生成] AI客户端未初始化,终止")
            QMessageBox.warning(
                self,
                "AI服务正在初始化",
                "AI服务正在后台启动中,请稍候片刻再试...",
                QMessageBox.Ok
            )
            return

        # 创建并显示进度对话框
        from gaiya.ui.components import AiProgressDialog
        self.ai_progress_dialog = AiProgressDialog(self)
        self.ai_progress_dialog.cancel_requested.connect(self.on_ai_generation_cancelled)

        # 创建并启动工作线程
        logging.info("[改进版AI生成] 创建AI工作线程...")
        self.ai_worker = AIWorker(self.ai_client, prompt)

        # 使用lambda包装回调
        def on_finished(result):
            logging.info(f"[改进版AI生成] on_finished回调触发, 结果: {type(result)}")
            self.on_ai_generation_finished(result)
            self.ai_worker.finished.disconnect()
            self.ai_worker.error.disconnect()
            self.ai_worker.deleteLater()
            self.ai_worker = None
            # 关闭进度对话框
            if hasattr(self, 'ai_progress_dialog') and self.ai_progress_dialog:
                logging.info("[改进版AI生成] 关闭进度对话框(成功)")
                self.ai_progress_dialog.accept()
                self.ai_progress_dialog = None

        def on_error(error_msg):
            logging.error(f"[改进版AI生成] on_error回调触发: {error_msg}")
            self.on_ai_generation_error(error_msg)
            self.ai_worker.finished.disconnect()
            self.ai_worker.error.disconnect()
            self.ai_worker.deleteLater()
            self.ai_worker = None
            # 关闭进度对话框
            if hasattr(self, 'ai_progress_dialog') and self.ai_progress_dialog:
                logging.info("[改进版AI生成] 关闭进度对话框(失败)")
                self.ai_progress_dialog.reject()
                self.ai_progress_dialog = None

        self.ai_worker.finished.connect(on_finished)
        self.ai_worker.error.connect(on_error)
        logging.info("[改进版AI生成] 启动AI工作线程...")
        self.ai_worker.start()
        logging.info(f"[改进版AI生成] AI生成任务已启动,prompt长度: {len(prompt)}")
        logging.info(f"[改进版AI生成] 工作线程isRunning: {self.ai_worker.isRunning()}")

        # 显示进度对话框(非阻塞)
        self.ai_progress_dialog.show()

    def on_ai_generation_cancelled(self):
        """用户取消AI生成"""
        logging.info("[改进版AI生成] 用户请求取消AI生成")
        if self.ai_worker and self.ai_worker.isRunning():
            # 终止工作线程
            self.ai_worker.quit()
            self.ai_worker.wait(2000)  # 等待最多2秒
            if self.ai_worker.isRunning():
                self.ai_worker.terminate()
            self.ai_worker.deleteLater()
            self.ai_worker = None
            logging.info("[改进版AI生成] AI工作线程已终止")

        # 清理进度对话框
        if hasattr(self, 'ai_progress_dialog') and self.ai_progress_dialog:
            self.ai_progress_dialog = None

    def on_banner_learn_more(self):
        """横幅了解更多点击"""
        # 切换到账户标签页的AI说明区域
        if self.tabs:
            # 个人中心在索引5
            self.tabs.setCurrentIndex(5)

    def on_banner_closed(self):
        """横幅关闭按钮点击"""
        # 保存到配置
        self.config['ai_banner_closed'] = True
        self.save_config()
        logging.info("AI功能横幅已关闭")

    def create_about_tab(self):
        """创建关于标签页"""
        from version import __version__, __app_name__, __slogan__, APP_METADATA
        from PySide6.QtGui import QPixmap
        from gaiya.utils.path_utils import get_resource_path

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(40, 40, 40, 40)

        # 顶部弹性空间（实现垂直居中）
        layout.addStretch()

        # Logo区域（使用图片）
        logo_label = QLabel()
        logo_path = get_resource_path("gaiya-logo2.png")
        logo_pixmap = QPixmap(str(logo_path))
        if not logo_pixmap.isNull():
            # 设置logo大小为150x150
            scaled_pixmap = logo_pixmap.scaled(
                150, 150,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            logo_label.setPixmap(scaled_pixmap)
        else:
            # 如果图片加载失败，显示应用名称作为后备
            logo_label.setText(__app_name__)
            logo_label.setStyleSheet("""
                QLabel {
                    font-size: 48px;
                    font-weight: bold;
                    color: #4CAF50;
                    padding: 20px;
                }
            """)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)

        # 应用名称
        app_name_label = QLabel(self.i18n.tr("app.name"))
        app_name_label.setStyleSheet("""
            QLabel {
                font-size: 36px;
                font-weight: bold;
                color: #2C3E50;
                padding: 10px;
            }
        """)
        app_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(app_name_label)

        # Slogan
        slogan_label = QLabel(self.i18n.tr("app.tagline"))
        slogan_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #888;
                padding: 10px;
            }
        """)
        slogan_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(slogan_label)

        # 版本号
        version_label = QLabel(self.i18n.tr("general.text_7718", __version__=__version__))
        version_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #666;
                padding: 5px;
            }
        """)
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)

        layout.addSpacing(30)

        # 检查更新按钮
        self.check_update_btn = QPushButton(self.i18n.tr("general.text_5645"))
        self.check_update_btn.setFixedSize(200, 40)
        self.check_update_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 20px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self.check_update_btn.clicked.connect(self._check_for_updates)

        # 居中按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.check_update_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addSpacing(20)

        # 反馈链接
        feedback_link = QLabel(f'<a href="#" style="color: #2196F3; text-decoration: none;">{self.i18n.tr("config.feedback.report_to_founder")}</a>')
        feedback_link.setStyleSheet("""
            QLabel {
                font-size: 13px;
                padding: 5px;
            }
        """)
        feedback_link.setAlignment(Qt.AlignmentFlag.AlignCenter)
        feedback_link.setOpenExternalLinks(False)  # 禁用默认的外部链接打开
        feedback_link.linkActivated.connect(self._show_wechat_qrcode)
        layout.addWidget(feedback_link)

        layout.addStretch()

        # 底部版权信息
        copyright_label = QLabel(self.i18n.tr("about.copyright"))
        copyright_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #666;
                padding: 10px;
            }
        """)
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(copyright_label)

        return widget

    def _extract_changelog_highlights(self, full_changelog):
        """提取更新日志的核心亮点

        只显示主要功能更新，移除markdown格式符号
        """
        import re

        if not full_changelog:
            return "无更新说明"

        lines = full_changelog.split('\n')
        highlights = []

        # 跟踪当前章节
        current_section = None
        section_items = []

        for line in lines:
            line = line.strip()

            # 跳过空行
            if not line:
                continue

            # 识别二级标题（## 开头）
            if line.startswith('##'):
                # 保存上一个章节的内容
                if current_section and section_items:
                    highlights.append(f"{current_section}")
                    highlights.extend(section_items[:3])  # 每个章节最多显示3条
                    section_items = []

                # 提取新章节标题，移除markdown符号
                current_section = re.sub(r'^##\s*', '', line)
                current_section = re.sub(r'[#*_`]', '', current_section).strip()

            # 识别列表项（- 或 数字. 开头，包含 emoji 的重点内容）
            elif re.match(r'^[-\d.]\s*[✨💎👤📊🔒✅⚡💰🎁💡🌐🏗🔧]', line):
                # 移除列表符号和markdown格式
                item = re.sub(r'^[-\d.]\s*', '', line)
                item = re.sub(r'\*\*([^*]+)\*\*', r'\1', item)  # 加粗
                item = re.sub(r'[`_]', '', item)  # 内联代码和斜体
                section_items.append(f"  • {item}")

        # 添加最后一个章节
        if current_section and section_items:
            highlights.append(f"{current_section}")
            highlights.extend(section_items[:3])

        # 限制总条数，避免弹窗过高
        if len(highlights) > 15:
            highlights = highlights[:15]
            highlights.append("\n详细内容请访问 GitHub Release 页面查看...")

        return '\n'.join(highlights) if highlights else "无更新说明"

    def _auto_update(self, latest_release, latest_version):
        """自动下载并安装更新"""
        import os
        import sys
        import tempfile
        import subprocess
        from PySide6.QtWidgets import QProgressDialog
        from PySide6.QtCore import Qt, QThread, Signal

        # 查找 .exe 文件的下载链接
        assets = latest_release.get('assets', [])
        exe_asset = None
        for asset in assets:
            if asset['name'].endswith('.exe'):
                exe_asset = asset
                break

        if not exe_asset:
            QMessageBox.warning(
                self,
                "更新失败",
                "未找到可执行文件，请手动前往 GitHub 下载"
            )
            return

        download_url = exe_asset['browser_download_url']
        file_size = exe_asset['size']

        # 创建进度对话框
        progress = QProgressDialog("正在下载更新...", "取消", 0, 100, self)
        progress.setWindowTitle(self.i18n.tr("general.text_9339"))
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        # 使用异步工作线程下载
        from gaiya.core.async_worker import AsyncNetworkWorker

        class DownloadWorker(QThread):
            """下载文件的工作线程"""
            progress_update = Signal(int)
            finished_signal = Signal(str)
            error_signal = Signal(str)

            def __init__(self, url, dest_path, file_size):
                super().__init__()
                self.url = url
                self.dest_path = dest_path
                self.file_size = file_size
                self._cancelled = False

            def run(self):
                try:
                    import requests
                    response = requests.get(self.url, stream=True, timeout=60)
                    response.raise_for_status()

                    downloaded = 0
                    with open(self.dest_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if self._cancelled:
                                return

                            f.write(chunk)
                            downloaded += len(chunk)

                            # 更新进度
                            if self.file_size > 0:
                                percent = int((downloaded / self.file_size) * 100)
                                self.progress_update.emit(percent)

                    self.finished_signal.emit(self.dest_path)

                except Exception as e:
                    self.error_signal.emit(str(e))

            def cancel(self):
                self._cancelled = True

        # 下载到临时目录
        temp_dir = tempfile.gettempdir()
        temp_exe_path = os.path.join(temp_dir, f"GaiYa-v{latest_version}.exe")

        worker = DownloadWorker(download_url, temp_exe_path, file_size)

        def on_progress(value):
            progress.setValue(value)

        def on_finished(file_path):
            # 先断开 canceled 信号连接，防止 close() 触发取消消息
            try:
                progress.canceled.disconnect(on_cancel)
            except:
                pass  # 如果已经断开则忽略

            progress.close()

            # 下载完成，准备安装
            reply = QMessageBox.question(
                self,
                "下载完成",
                f"新版本已下载完成，是否立即安装并重启应用？\n\n下载位置：{file_path}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self._install_update(file_path)

        def on_error(error_msg):
            progress.close()
            QMessageBox.warning(
                self,
                "下载失败",
                f"自动更新失败：{error_msg}\n\n请手动前往 GitHub 下载"
            )

        def on_cancel():
            worker.cancel()
            QMessageBox.information(self, self.i18n.tr("dialog.text_6870"), "更新已取消")

        worker.progress_update.connect(on_progress)
        worker.finished_signal.connect(on_finished)
        worker.error_signal.connect(on_error)
        progress.canceled.connect(on_cancel)

        worker.start()

    def _install_update(self, new_exe_path):
        """安装更新并重启程序"""
        import os
        import sys
        import subprocess

        # 获取当前程序路径
        if getattr(sys, 'frozen', False):
            # 打包后的exe
            current_exe = sys.executable
        else:
            # 源码运行，无法自动更新
            QMessageBox.information(
                self,
                "无法自动更新",
                "当前以源码方式运行，无法自动替换程序。\n请手动替换可执行文件。"
            )
            return

        # 创建批处理脚本来替换文件并重启
        # Windows 上运行中的 exe 无法直接替换，需要在程序退出后执行
        import tempfile
        bat_path = os.path.join(tempfile.gettempdir(), "gaiya_update.bat")

        bat_content = f'''@echo off
echo 正在更新 GaiYa...
echo 等待应用关闭...
timeout /t 3 /nobreak >nul

REM 确保旧进程完全终止
taskkill /F /IM GaiYa*.exe 2>nul
timeout /t 1 /nobreak >nul

:retry
del /f /q "{current_exe}"
if exist "{current_exe}" (
    echo 等待文件解锁...
    timeout /t 1 /nobreak >nul
    goto retry
)

move /y "{new_exe_path}" "{current_exe}"
if errorlevel 1 (
    echo 更新失败！无法移动文件。
    pause
    exit /b 1
)

echo 更新完成，正在启动...
start "" "{current_exe}"
del /f /q "%~f0"
'''

        try:
            with open(bat_path, 'w', encoding='gb2312') as f:
                f.write(bat_content)

            # 启动批处理脚本
            subprocess.Popen(
                ['cmd', '/c', bat_path],
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            # 关闭当前程序
            QMessageBox.information(
                self,
                "准备更新",
                "程序将关闭并自动完成更新，请稍候..."
            )

            # 触发程序退出
            from PySide6.QtWidgets import QApplication
            QApplication.quit()

        except Exception as e:
            QMessageBox.warning(
                self,
                "安装失败",
                f"无法安装更新：{str(e)}\n\n请手动替换程序文件"
            )

    def _check_for_updates(self):
        """检查更新 - 异步版本"""
        from gaiya.core.async_worker import AsyncNetworkWorker

        # 更新按钮状态
        self.check_update_btn.setEnabled(False)
        self.check_update_btn.setText(self.i18n.tr("general.text_2760"))

        # ✅ 性能优化: 使用异步Worker避免UI卡顿
        self._update_check_worker = AsyncNetworkWorker(self._fetch_latest_release)
        self._update_check_worker.success.connect(self._on_update_check_success)
        self._update_check_worker.error.connect(self._on_update_check_error)
        self._update_check_worker.start()

    def _fetch_latest_release(self) -> dict:
        """获取最新版本信息(在后台线程中执行)"""
        from version import __version__, APP_METADATA
        import requests

        # 调用GitHub API获取最新版本
        repo = APP_METADATA['repository'].replace('https://github.com/', '')
        api_url = f"https://api.github.com/repos/{repo}/releases/latest"

        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        latest_release = response.json()
        latest_version = latest_release['tag_name'].lstrip('v')
        current_version = __version__

        return {
            "success": True,
            "latest_release": latest_release,
            "latest_version": latest_version,
            "current_version": current_version,
            "has_update": self._compare_versions(latest_version, current_version) > 0
        }

    def _on_update_check_success(self, result: dict):
        """版本检查成功回调"""
        from PySide6.QtWidgets import QMessageBox
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl

        latest_release = result["latest_release"]
        latest_version = result["latest_version"]
        current_version = result["current_version"]
        has_update = result["has_update"]

        if has_update:
            # 有新版本
            self.check_update_btn.setText(self.i18n.tr("general.text_8527"))
            self.check_update_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF5722;
                    color: white;
                    font-size: 14px;
                    font-weight: bold;
                    border-radius: 20px;
                    padding: 10px 20px;
                }
                QPushButton:hover {
                    background-color: #E64A19;
                }
                QPushButton:pressed {
                    background-color: #BF360C;
                }
            """)

            # 弹出更新提示
            # 提取核心更新内容
            changelog_highlights = self._extract_changelog_highlights(latest_release.get('body', ''))

            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle(self.i18n.tr("general.text_377"))
            msg.setText(self.i18n.tr("general.text_1975"))
            msg.setInformativeText(f"当前版本: v{current_version}\n\n核心更新:\n{changelog_highlights}")
            msg.setStandardButtons(QMessageBox.StandardButton.Cancel)

            # 添加两个按钮：立即更新 和 前往下载
            auto_update_btn = msg.addButton(self.i18n.tr("general.text_2613"), QMessageBox.ButtonRole.AcceptRole)
            manual_download_btn = msg.addButton(self.i18n.tr("general.text_7203"), QMessageBox.ButtonRole.ActionRole)
            msg.exec()

            if msg.clickedButton() == auto_update_btn:
                # 自动更新
                self._auto_update(latest_release, latest_version)
            elif msg.clickedButton() == manual_download_btn:
                # 打开下载页面
                QDesktopServices.openUrl(QUrl(latest_release['html_url']))
        else:
            # 已是最新版本
            QMessageBox.information(
                self,
                "已是最新版本",
                f"当前版本 v{current_version} 已是最新版本！"
            )
            self.check_update_btn.setText(self.i18n.tr("general.text_5645"))

        # 恢复按钮状态
        self.check_update_btn.setEnabled(True)

    def _on_update_check_error(self, error_msg: str):
        """版本检查失败回调"""
        from PySide6.QtWidgets import QMessageBox
        from version import __version__, APP_METADATA
        import logging

        logging.error(f"检查更新失败: {error_msg}")

        # 根据错误类型给出不同的提示
        if "Timeout" in error_msg or "timeout" in error_msg:
            QMessageBox.warning(self, self.i18n.tr("message.text_8308"), "网络请求超时，请检查网络连接")
        elif "404" in error_msg:
            # 仓库还没有发布任何 Release
            QMessageBox.information(
                self,
                "暂无发布版本",
                f"当前版本: v{__version__}\n\n项目仓库暂未发布正式版本，敬请期待！\n\n您可以访问 GitHub 仓库查看最新开发进展：\n{APP_METADATA['repository']}"
            )
        elif "HTTPError" in error_msg or "RequestException" in error_msg:
            QMessageBox.warning(self, self.i18n.tr("message.text_8308"), f"无法连接到更新服务器\n\n{error_msg}")
        else:
            QMessageBox.warning(self, self.i18n.tr("message.text_8308"), f"发生未知错误\n\n{error_msg}")

        self.check_update_btn.setText(self.i18n.tr("general.text_5645"))
        self.check_update_btn.setEnabled(True)

    def _compare_versions(self, version1, version2):
        """比较版本号

        Returns:
            1: version1 > version2
            0: version1 == version2
            -1: version1 < version2
        """
        v1_parts = [int(x) for x in version1.split('.')]
        v2_parts = [int(x) for x in version2.split('.')]

        # 补齐长度
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))

        for v1, v2 in zip(v1_parts, v2_parts):
            if v1 > v2:
                return 1
            elif v1 < v2:
                return -1

        return 0

    def _show_wechat_qrcode(self):
        """显示微信二维码弹窗"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
        from PySide6.QtGui import QPixmap
        from PySide6.QtCore import Qt
        import os
        import sys

        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle(self.i18n.tr("general.text_6717"))
        dialog.setFixedSize(550, 750)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        title_label = QLabel(self.i18n.tr("about.labels.scan_qr_feedback"))
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: white;
                padding: 10px;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 加载二维码图片（兼容打包后的路径）
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller打包后的临时目录
            qrcode_path = os.path.join(sys._MEIPASS, "qun.jpg")
        else:
            # 开发环境
            qrcode_path = os.path.join(os.path.dirname(__file__), "qun.jpg")

        if os.path.exists(qrcode_path):
            pixmap = QPixmap(qrcode_path)
            if not pixmap.isNull():
                # 缩放图片以适应对话框
                scaled_pixmap = pixmap.scaled(
                    480, 600,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )

                qrcode_label = QLabel()
                qrcode_label.setPixmap(scaled_pixmap)
                qrcode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(qrcode_label)
            else:
                error_label = QLabel(self.i18n.tr("general.image_2"))
                error_label.setStyleSheet("color: red; padding: 20px;")
                error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(error_label)
        else:
            error_label = QLabel(self.i18n.tr("general.image_3"))
            error_label.setStyleSheet("color: red; padding: 20px;")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(error_label)

        # 提示文字
        hint_label = QLabel(self.i18n.tr("about.labels.scan_add_friend"))
        hint_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #888;
                padding: 10px;
            }
        """)
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint_label)

        # 显示对话框
        dialog.exec()

    def on_language_changed(self, index):
        """处理语言切换"""
        if not self.config:
            return

        new_lang = self.language_combo.currentData()
        old_lang = self.config.get('language', 'zh_CN')

        if new_lang == old_lang:
            return

        # 在切换语言前,先收集并保存当前UI的所有配置值,避免重置
        # 这样新窗口加载时就能得到最新的配置
        try:
            # 收集当前UI的配置值,保证语言切换后不会丢失用户修改
            self.config['bar_height'] = self.height_spin.value() if hasattr(self, 'height_spin') else self.config.get('bar_height', 10)
            self.config['background_color'] = self.bg_color_input.text() if hasattr(self, 'bg_color_input') else self.config.get('background_color', '#F5F5F5')
            self.config['background_opacity'] = self.opacity_spin.value() if hasattr(self, 'opacity_spin') else self.config.get('background_opacity', 240)
            self.config['marker_color'] = self.marker_color_input.text() if hasattr(self, 'marker_color_input') else self.config.get('marker_color', '#FF5252')
            self.config['marker_width'] = self.marker_width_spin.value() if hasattr(self, 'marker_width_spin') else self.config.get('marker_width', 2)
            self.config['marker_type'] = self.marker_type_combo.currentText() if hasattr(self, 'marker_type_combo') else self.config.get('marker_type', 'line')
            self.config['marker_image_path'] = self.marker_image_input.text() if hasattr(self, 'marker_image_input') else self.config.get('marker_image_path', '')
            self.config['marker_size'] = self.marker_size_spin.value() if hasattr(self, 'marker_size_spin') else self.config.get('marker_size', 50)
            self.config['marker_speed'] = self.marker_speed_spin.value() if hasattr(self, 'marker_speed_spin') else self.config.get('marker_speed', 100)
            self.config['marker_always_visible'] = self.marker_always_visible_check.isChecked() if hasattr(self, 'marker_always_visible_check') else self.config.get('marker_always_visible', True)
            self.config['marker_x_offset'] = self.marker_x_offset_spin.value() if hasattr(self, 'marker_x_offset_spin') else self.config.get('marker_x_offset', 0)
            self.config['marker_y_offset'] = self.marker_y_offset_spin.value() if hasattr(self, 'marker_y_offset_spin') else self.config.get('marker_y_offset', 0)
            self.config['screen_index'] = self.screen_spin.value() if hasattr(self, 'screen_spin') else self.config.get('screen_index', 0)
            self.config['update_interval'] = self.interval_spin.value() if hasattr(self, 'interval_spin') else self.config.get('update_interval', 1000)
            self.config['enable_shadow'] = self.shadow_check.isChecked() if hasattr(self, 'shadow_check') else self.config.get('enable_shadow', True)
            self.config['corner_radius'] = self.radius_spin.value() if hasattr(self, 'radius_spin') else self.config.get('corner_radius', 0)

            # 保留其他不在外观tab的配置(theme, notification, scene等),避免丢失
            # 这些配置项通常在对应的tab中,如果尚未加载则保持原配置
            if 'theme' not in self.config or not self.config['theme']:
                self.config['theme'] = {'mode': 'preset', 'current_theme_id': 'business', 'auto_apply_task_colors': False}
            if 'notification' not in self.config or not self.config['notification']:
                self.config['notification'] = {'enabled': True, 'before_start_minutes': [10, 5], 'on_start': True, 'before_end_minutes': [5], 'on_end': False, 'sound_enabled': True, 'sound_file': '', 'quiet_hours': {'enabled': False, 'start': '22:00', 'end': '08:00'}}
            if 'scene' not in self.config or not self.config['scene']:
                self.config['scene'] = {'enabled': False, 'current_scene': None, 'show_progress_bar': False}

            # 更新语言配置
            self.config['language'] = new_lang

            # 保存完整配置（使用防抖动保存）
            self.config_debouncer.save_debounced(self.config)

            # Get language display name
            language_names = {
                'zh_CN': '简体中文',
                'en_US': 'English'
            }
            language_name = language_names.get(new_lang, new_lang)

            # Show confirmation dialog with Apply Now / Later options
            self._show_language_change_dialog(language_name)

        except Exception as e:
            logging.error(f"Failed to save language setting: {e}")

    def _show_language_change_dialog(self, language_name):
        """Show language change confirmation dialog with Apply Now / Later options"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton

        dialog = QDialog(self)
        dialog.setWindowTitle(self.i18n.tr("config.language_changed_title", fallback="Language Changed"))
        dialog.setMinimumWidth(350)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Message label
        message = self.i18n.tr("config.language_changed_message", language_name=language_name, fallback=f"Language has been changed to {language_name}")
        message_label = QLabel(message)
        message_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(message_label)

        # Hint label
        hint = self.i18n.tr("config.language_change_hint", fallback="Click \"Apply Now\" to reload the configuration window with the new language.")
        hint_label = QLabel(hint)
        hint_label.setWordWrap(True)
        hint_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(hint_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        apply_now_btn = QPushButton(self.i18n.tr("config.apply_now", fallback="Apply Now"))
        apply_now_btn.setFixedHeight(36)
        apply_now_btn.setStyleSheet(StyleManager.button_primary())

        apply_later_btn = QPushButton(self.i18n.tr("config.apply_later", fallback="Later"))
        apply_later_btn.setFixedHeight(36)

        button_layout.addStretch()
        button_layout.addWidget(apply_now_btn)
        button_layout.addWidget(apply_later_btn)

        layout.addLayout(button_layout)

        # Connect signals
        apply_now_btn.clicked.connect(lambda: self._apply_language_now(dialog))
        apply_later_btn.clicked.connect(dialog.accept)

        dialog.exec()

    def _apply_language_now(self, dialog):
        """Apply language change immediately by recreating the window"""
        dialog.accept()

        # Save current tab index for restoration
        current_tab_index = self.tabs.currentIndex() if hasattr(self, 'tabs') else 0

        # Reload the i18n translator with new language
        try:
            from i18n.translator import _translator
            new_lang = self.config.get('language', 'zh_CN')
            _translator.set_language(new_lang)
            logging.info(f"Language switched to: {new_lang}")
        except Exception as e:
            logging.error(f"Failed to reload i18n translator: {e}")

        # Recreate the window
        self._recreate_config_window(current_tab_index)

    def _recreate_config_window(self, restore_tab_index=0):
        """Recreate the configuration window with new language"""
        # Get reference to main window before closing
        main_window = self.main_window

        def create_new_window():
            """Create new window after current one is closed"""
            try:
                new_window = ConfigManager(main_window=main_window)
                new_window.show()

                # Restore tab index after a short delay (wait for lazy loading)
                QTimer.singleShot(100, lambda: new_window.tabs.setCurrentIndex(restore_tab_index))

                # Update main window's reference if needed
                if main_window and hasattr(main_window, 'config_window'):
                    main_window.config_window = new_window

                logging.info(f"Config window recreated, restored to tab {restore_tab_index}")
            except Exception as e:
                logging.error(f"Failed to recreate config window: {e}")
                import traceback
                traceback.print_exc()

        # Schedule new window creation BEFORE closing current window
        # Use QTimer to ensure the new window is created after event loop processes the close
        QTimer.singleShot(100, create_new_window)

        # Now close current window
        self.close()

    def closeEvent(self, event):
        """窗口关闭事件，清理所有资源"""
        # 停止行为识别统计定时器
        if hasattr(self, 'behavior_stats_timer') and self.behavior_stats_timer:
            if self.behavior_stats_timer.isActive():
                self.behavior_stats_timer.stop()
            self.behavior_stats_timer = None
            logging.info("行为识别统计信息定时器已停止")

        # 停止AI状态定时器
        if hasattr(self, 'ai_status_timer') and self.ai_status_timer:
            if self.ai_status_timer.isActive():
                self.ai_status_timer.stop()
            self.ai_status_timer = None

        # 取消正在运行的AI工作线程
        if hasattr(self, 'ai_worker') and self.ai_worker:
            try:
                # 断开所有信号连接
                self.ai_worker.finished.disconnect()
                self.ai_worker.error.disconnect()
            except RuntimeError:
                # 信号已经断开，忽略
                pass
            except Exception as e:
                logging.debug(f"断开AI worker信号时出错: {e}")

            if self.ai_worker.isRunning():
                # 优先使用requestInterruption()，而不是terminate()
                self.ai_worker.requestInterruption()
                # 等待线程自然结束（最多1秒）
                if not self.ai_worker.wait(1000):
                    # 如果1秒后还未结束，强制终止
                    self.ai_worker.terminate()
                    self.ai_worker.wait()

            # 延迟删除worker对象
            self.ai_worker.deleteLater()
            self.ai_worker = None

        # 停止支付轮询定时器
        if hasattr(self, 'payment_timer') and self.payment_timer:
            if self.payment_timer.isActive():
                self.payment_timer.stop()
            self.payment_timer = None

        # 取消注册主题管理器组件（如果已注册）
        if hasattr(self, 'theme_manager') and self.theme_manager:
            try:
                self.theme_manager.unregister_ui_component(self)
            except Exception:
                pass

        # 已切换到Vercel云服务，不再需要停止本地后端服务
        # 保留此检查以保持向后兼容性
        if hasattr(self, 'backend_manager') and self.backend_manager:
            try:
                self.backend_manager.stop_backend()
            except Exception:
                pass

        # ✅ 性能优化: 应用关闭时立即保存待处理的配置（防抖动刷新）
        if hasattr(self, 'config_debouncer') and self.config_debouncer:
            try:
                if self.config_debouncer.flush():
                    logging.info("ConfigDebouncer: 关闭时已刷新待处理的配置")
            except Exception as e:
                logging.error(f"ConfigDebouncer刷新失败: {e}")

        # 接受关闭事件
        event.accept()
        logging.info("配置管理器已关闭，资源已清理")


def main():
    """主程序入口"""
    app = QApplication(sys.argv)

    # 应用浅色主题（MacOS极简风格）
    try:
        apply_light_theme(app)
    except Exception as e:
        logging.warning(f"[警告] 应用浅色主题失败: {e}，使用默认样式")
        app.setStyle("Fusion")

    window = ConfigManager()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
