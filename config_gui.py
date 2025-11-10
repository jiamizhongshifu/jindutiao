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
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QLineEdit, QSpinBox, QPushButton, QColorDialog,
    QComboBox, QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QTimeEdit, QGroupBox, QFormLayout, QFileDialog, QDialog,
    QDialogButtonBox, QButtonGroup, QRadioButton
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

# 浅色主题支持（MacOS极简风格）
from gaiya.ui.style_manager import StyleManager, apply_light_theme


class AIWorker(QThread):
    """AI请求工作线程,防止阻塞UI"""
    # 定义信号
    finished = Signal(object)  # 完成信号,传递结果
    error = Signal(str)  # 错误信号,传递错误消息

    def __init__(self, ai_client, user_input):
        super().__init__()
        self.ai_client = ai_client
        self.user_input = user_input

    def run(self):
        """在后台线程中执行AI请求"""
        try:
            result = self.ai_client.plan_tasks(self.user_input, parent_widget=None)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


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
        self.existing_templates = existing_templates
        self.template_name = None
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("保存为模板")
        self.setMinimumWidth(400)

        layout = QVBoxLayout()

        # 提示文本
        if self.existing_templates:
            hint_label = QLabel("选择要覆盖的模板或输入新的模板名称:")
        else:
            hint_label = QLabel("请输入模板名称:")

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
                display_text = f"{template_name} ({task_count}个任务)"
                self.input_widget.addItem(display_text, template_name)

            # 设置当前文本为空,引导用户选择或输入
            self.input_widget.setCurrentIndex(-1)
            self.input_widget.setPlaceholderText("选择历史模板或输入新名称")
        else:
            # 无历史模板,使用普通输入框
            self.input_widget = QLineEdit()
            self.input_widget.setPlaceholderText("例如: 工作日模板")

        layout.addWidget(self.input_widget)

        # 提示信息
        if self.existing_templates:
            tip_label = QLabel(
                "💡 提示:\n"
                "• 选择历史模板将直接覆盖该模板\n"
                "• 输入新名称将创建新的模板"
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
            QMessageBox.warning(self, "输入错误", "模板名称不能为空!")
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

    def __init__(self):
        super().__init__()
        # 获取应用程序目录(使用统一的path_utils)
        self.app_dir = path_utils.get_app_dir()

        self.config_file = self.app_dir / 'config.json'
        self.tasks_file = self.app_dir / 'tasks.json'
        
        # 延迟加载配置和任务，先让窗口显示
        self.config = {}
        self.tasks = []
        
        # 延迟初始化AI相关组件(避免阻塞UI显示)
        self.ai_client = None
        self.ai_worker = None
        self.autostart_manager = AutoStartManager()  # 自启动管理器
        self.theme_ai_helper = None

        # 延迟初始化主题管理器(避免同步文件I/O阻塞UI)
        self.theme_manager = None
        # 延迟初始化模板管理器
        self.template_manager = None
        self.schedule_manager = None

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
                self.bg_color_input.setText(self.config.get('background_color', '#505050'))
                if hasattr(self, 'bg_color_preview'):
                    self.update_color_preview(self.bg_color_input, self.bg_color_preview)
            
            if hasattr(self, 'opacity_spin'):
                self.opacity_spin.setValue(self.config.get('background_opacity', 180))
            
            if hasattr(self, 'marker_color_input'):
                self.marker_color_input.setText(self.config.get('marker_color', '#FF0000'))
                if hasattr(self, 'marker_color_preview'):
                    self.update_color_preview(self.marker_color_input, self.marker_color_preview)
            
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

            if hasattr(self, 'marker_x_offset_spin'):
                self.marker_x_offset_spin.setValue(self.config.get('marker_x_offset', 0))

            if hasattr(self, 'marker_y_offset_spin'):
                self.marker_y_offset_spin.setValue(self.config.get('marker_y_offset', 0))
        except Exception as e:
            logging.error(f"更新UI控件失败: {e}")
    
    def _init_timeline_editor(self, layout, placeholder):
        """延迟初始化时间轴编辑器"""
        try:
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
                toggle_btn.setToolTip("禁用" if enabled else "启用")
                toggle_btn.setFixedSize(36, 36)
                toggle_btn.setStyleSheet("QPushButton { padding: 4px; font-size: 14px; }")
                # 使用 partial 避免 Lambda 循环引用
                toggle_btn.clicked.connect(partial(self._toggle_schedule, row))
                actions_layout.addWidget(toggle_btn)

                # 编辑按钮
                edit_btn = QPushButton("✏️")
                edit_btn.setToolTip("编辑")
                edit_btn.setFixedSize(36, 36)
                edit_btn.setStyleSheet("QPushButton { padding: 4px; font-size: 14px; }")
                # 使用 partial 避免 Lambda 循环引用
                edit_btn.clicked.connect(partial(self._edit_schedule, row))
                actions_layout.addWidget(edit_btn)

                # 删除按钮
                delete_btn = QPushButton("🗑️")
                delete_btn.setToolTip("删除")
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
        if not self._check_login_and_guide("模板自动应用"):
            return

        try:
            if not hasattr(self, 'schedule_manager') or not self.schedule_manager:
                QMessageBox.warning(self, "警告", "时间表管理器未初始化")
                return

            if not hasattr(self, 'template_manager') or not self.template_manager:
                QMessageBox.warning(self, "警告", "模板管理器未初始化")
                return

            from PySide6.QtWidgets import (
                QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                QRadioButton, QButtonGroup, QCheckBox, QPushButton,
                QDateEdit, QSpinBox, QGroupBox
            )
            from datetime import date

            dialog = QDialog(self)
            dialog.setWindowTitle("添加模板应用规则")
            dialog.setMinimumWidth(500)

            layout = QVBoxLayout()

            # 模板选择
            template_layout = QHBoxLayout()
            template_layout.addWidget(QLabel("选择模板:"))

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
            weekdays_radio = QRadioButton("按星期重复")
            monthly_radio = QRadioButton("每月重复")
            specific_radio = QRadioButton("特定日期")

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
            monthly_label = QLabel("每月的哪些天?（用逗号分隔，例如: 1,15,28）")
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
            specific_label = QLabel("选择具体日期:")
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

            add_date_btn = QPushButton("+ 添加日期")

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

            cancel_btn = QPushButton("取消")
            cancel_btn.clicked.connect(dialog.reject)
            button_layout.addWidget(cancel_btn)

            save_btn = QPushButton("保存")
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
                        QMessageBox.warning(self, "警告", "请至少选择一个星期")
                        return

                    success = self.schedule_manager.add_schedule(
                        template_id=template_id,
                        schedule_type='weekdays',
                        weekdays=weekdays
                    )

                elif checked_id == 2:  # 每月
                    days_text = monthly_input.text().strip()
                    if not days_text:
                        QMessageBox.warning(self, "警告", "请输入每月的日期")
                        return

                    try:
                        days_of_month = [int(d.strip()) for d in days_text.split(',')]
                        # 验证日期范围
                        if any(d < 1 or d > 31 for d in days_of_month):
                            QMessageBox.warning(self, "警告", "日期必须在1-31之间")
                            return

                        success = self.schedule_manager.add_schedule(
                            template_id=template_id,
                            schedule_type='monthly',
                            days_of_month=days_of_month
                        )

                    except ValueError:
                        QMessageBox.warning(self, "警告", "日期格式错误，请使用逗号分隔的数字")
                        return

                elif checked_id == 3:  # 具体日期
                    if not specific_dates:
                        QMessageBox.warning(self, "警告", "请至少添加一个日期")
                        return

                    success = self.schedule_manager.add_schedule(
                        template_id=template_id,
                        schedule_type='specific_dates',
                        dates=specific_dates
                    )

                else:
                    QMessageBox.warning(self, "警告", "请选择规则类型")
                    return

                if success:
                    QMessageBox.information(self, "成功", "时间表规则已添加")
                    self._load_schedule_table()  # 刷新表格
                else:
                    QMessageBox.warning(self, "冲突", "该规则与现有规则冲突，请检查")

        except Exception as e:
            logging.error(f"添加时间表规则失败: {e}")
            QMessageBox.critical(self, "错误", f"添加规则失败:\n{str(e)}")

    def _edit_schedule(self, row):
        """编辑时间表规则"""
        # 首先检查是否已登录
        if not self._check_login_and_guide("模板自动应用"):
            return

        try:
            if not hasattr(self, 'schedule_manager') or not self.schedule_manager:
                QMessageBox.warning(self, "警告", "时间表管理器未初始化")
                return

            if not hasattr(self, 'template_manager') or not self.template_manager:
                QMessageBox.warning(self, "警告", "模板管理器未初始化")
                return

            # 获取当前规则
            schedules = self.schedule_manager.get_all_schedules()
            if row < 0 or row >= len(schedules):
                QMessageBox.warning(self, "警告", "无效的规则索引")
                return

            current_schedule = schedules[row]

            from PySide6.QtWidgets import (
                QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                QRadioButton, QButtonGroup, QCheckBox, QPushButton,
                QDateEdit, QSpinBox, QGroupBox, QLineEdit
            )
            from datetime import date, datetime

            dialog = QDialog(self)
            dialog.setWindowTitle("编辑模板应用规则")
            dialog.setMinimumWidth(500)

            layout = QVBoxLayout()

            # 模板选择
            template_layout = QHBoxLayout()
            template_layout.addWidget(QLabel("选择模板:"))

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
            weekdays_radio = QRadioButton("按星期重复")
            monthly_radio = QRadioButton("每月重复")
            specific_radio = QRadioButton("特定日期")

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
            monthly_label = QLabel("每月的哪些天?（用逗号分隔，例如: 1,15,28）")
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
            specific_label = QLabel("选择具体日期:")
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

            add_date_btn = QPushButton("+ 添加日期")

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

            cancel_btn = QPushButton("取消")
            cancel_btn.clicked.connect(dialog.reject)
            button_layout.addWidget(cancel_btn)

            save_btn = QPushButton("保存")
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
                        QMessageBox.warning(self, "警告", "请至少选择一个星期")
                        return

                    update_data['schedule_type'] = 'weekdays'
                    update_data['weekdays'] = weekdays

                elif checked_id == 2:  # 每月
                    days_text = monthly_input.text().strip()
                    if not days_text:
                        QMessageBox.warning(self, "警告", "请输入每月的日期")
                        return

                    try:
                        days_of_month = [int(d.strip()) for d in days_text.split(',')]
                        # 验证日期范围
                        if any(d < 1 or d > 31 for d in days_of_month):
                            QMessageBox.warning(self, "警告", "日期必须在1-31之间")
                            return

                        update_data['schedule_type'] = 'monthly'
                        update_data['days_of_month'] = days_of_month

                    except ValueError:
                        QMessageBox.warning(self, "警告", "日期格式错误，请使用逗号分隔的数字")
                        return

                elif checked_id == 3:  # 具体日期
                    if not specific_dates:
                        QMessageBox.warning(self, "警告", "请至少添加一个日期")
                        return

                    update_data['schedule_type'] = 'specific_dates'
                    update_data['dates'] = specific_dates

                else:
                    QMessageBox.warning(self, "警告", "请选择规则类型")
                    return

                success = self.schedule_manager.update_schedule(row, **update_data)

                if success:
                    QMessageBox.information(self, "成功", "时间表规则已更新")
                    self._load_schedule_table()  # 刷新表格
                else:
                    QMessageBox.warning(self, "失败", "更新规则失败，请检查")

        except Exception as e:
            logging.error(f"编辑时间表规则失败: {e}")
            QMessageBox.critical(self, "错误", f"编辑规则失败:\n{str(e)}")

    def _toggle_schedule(self, row):
        """切换时间表规则的启用状态"""
        # 首先检查是否已登录
        if not self._check_login_and_guide("模板自动应用"):
            return

        try:
            success = self.schedule_manager.toggle_schedule(row)
            if success:
                self._load_schedule_table()  # 刷新表格
        except Exception as e:
            logging.error(f"切换规则状态失败: {e}")
            QMessageBox.critical(self, "错误", f"操作失败:\n{str(e)}")

    def _delete_schedule(self, row):
        """删除时间表规则"""
        # 首先检查是否已登录
        if not self._check_login_and_guide("模板自动应用"):
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
                    QMessageBox.information(self, "成功", "规则已删除")

        except Exception as e:
            logging.error(f"删除规则失败: {e}")
            QMessageBox.critical(self, "错误", f"删除失败:\n{str(e)}")

    def _test_date_matching(self):
        """测试指定日期会匹配到哪个模板"""
        try:
            if not hasattr(self, 'schedule_manager') or not self.schedule_manager:
                QMessageBox.warning(self, "警告", "时间表管理器未初始化")
                return

            from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDateEdit, QPushButton, QTextEdit
            from datetime import datetime

            dialog = QDialog(self)
            dialog.setWindowTitle("测试日期匹配")
            dialog.setMinimumWidth(500)
            dialog.setMinimumHeight(350)

            layout = QVBoxLayout()

            # 说明
            hint_label = QLabel("选择一个日期，查看该日期会匹配到哪个模板：")
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
                result_lines.append(f"测试日期: {selected_date.strftime('%Y-%m-%d %A')}")
                result_lines.append("")

                if matched_template_id:
                    # 获取模板名称
                    template_name = matched_template_id
                    if hasattr(self, 'template_manager') and self.template_manager:
                        template = self.template_manager.get_template_by_id(matched_template_id)
                        if template:
                            template_name = template['name']

                    result_lines.append(f"✅ 该日期会自动加载模板: {template_name}")
                    result_lines.append("")

                    if len(all_matched) > 1:
                        result_lines.append(f"⚠️ 警告：该日期有 {len(all_matched)} 个模板规则冲突！")
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
            test_btn = QPushButton("🔍 执行测试")
            test_btn.setStyleSheet(StyleManager.button_minimal())
            test_btn.clicked.connect(perform_test)
            layout.addWidget(test_btn)

            # 关闭按钮
            close_btn = QPushButton("关闭")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)

            dialog.setLayout(layout)

            # 初始执行一次测试
            perform_test()

            dialog.exec()

        except Exception as e:
            logging.error(f"测试日期匹配失败: {e}")
            QMessageBox.critical(self, "错误", f"测试失败:\n{str(e)}")

    def _init_ai_components(self):
        """延迟初始化AI相关组件(在后台运行,不阻塞UI)"""
        try:
            # 初始化AI客户端（默认使用代理服务器）
            self.ai_client = GaiyaAIClient()
            
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
                    self.ai_status_timer.start(5000)  # 改为5秒检查一次，减少频率
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
            self.quota_label.setText("⏳ AI服务正在初始化...")
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
        
        if not is_healthy:
            # 代理服务器未响应，继续显示"正在启动"状态
            self.quota_label.setText("⚠️ AI服务正在启动...")
            self.quota_label.setStyleSheet("color: #ff9800; padding: 5px; font-weight: bold;")
            if hasattr(self, 'generate_btn'):
                self.generate_btn.setEnabled(False)
            
            # 注意：使用代理服务器时，不需要启动本地后端服务
            # 如果代理服务器不可用，可能是网络问题或服务器暂时不可用
            
            # 不停止定时器，继续检查（每5秒检查一次）
            return

        # 代理服务器已响应,异步更新配额状态
        self.refresh_quota_status_async()

        # 注意：不在这里停止定时器，等配额检查成功后再停止
        # 这样可以确保如果代理服务器崩溃，定时器会继续检查

    def _update_ai_status_error(self, error_msg):
        """显示AI服务错误状态"""
        if hasattr(self, 'quota_label'):
            self.quota_label.setText(f"❌ AI服务初始化失败")
            self.quota_label.setStyleSheet("color: #f44336; padding: 5px; font-weight: bold;")
            logging.error(f"AI服务错误: {error_msg}")
        if hasattr(self, 'generate_btn'):
            self.generate_btn.setEnabled(False)

    def get_resource_path(self, relative_path):
        """获取资源文件路径(使用统一的path_utils)"""
        return path_utils.get_resource_path(relative_path)

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle(f'{VERSION_STRING_ZH} - 配置管理器')

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

        # 创建标签页(使用懒加载,只在切换到标签页时才创建内容)
        tabs = QTabWidget()

        # 立即创建外观配置和任务管理标签页(基础功能)
        tabs.addTab(self.create_config_tab(), "🎨 外观配置")
        tabs.addTab(self.create_tasks_tab(), "📋 任务管理")

        # 延迟创建通知设置标签页(避免初始化时阻塞)
        self.notification_tab_widget = None
        tabs.addTab(QWidget(), "🔔 通知设置")  # 占位widget

        # 延迟创建个人中心标签页
        self.account_tab_widget = None
        tabs.addTab(QWidget(), "👤 个人中心")  # 占位widget

        # 延迟创建关于标签页
        self.about_tab_widget = None
        tabs.addTab(QWidget(), "📖 关于")  # 占位widget

        # 连接标签页切换信号,实现懒加载
        tabs.currentChanged.connect(self.on_tab_changed)
        # 连接标签页切换信号,控制AI状态定时器
        tabs.currentChanged.connect(self._on_tab_changed_for_ai_status)
        self.tabs = tabs  # 保存引用

        layout.addWidget(tabs)

        # 底部按钮
        button_layout = QHBoxLayout()

        save_btn = QPushButton("保存所有设置")
        save_btn.clicked.connect(self.save_all)
        save_btn.setFixedHeight(36)
        save_btn.setStyleSheet(StyleManager.button_primary())

        cancel_btn = QPushButton("取消")
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

    def on_tab_changed(self, index):
        """标签页切换时的处理(实现懒加载)"""
        # 控制底部按钮的显示/隐藏
        # 在"个人中心"(3)和"关于"(4)页面隐藏按钮
        if index in [3, 4]:  # 个人中心或关于页面
            self.save_btn.hide()
            self.cancel_btn.hide()
        else:  # 其他页面显示按钮
            self.save_btn.show()
            self.cancel_btn.show()

        # 懒加载各标签页
        if index == 2:  # 通知设置标签页（主题设置已移除）
            if self.notification_tab_widget is None:
                self._load_notification_tab()
        elif index == 3:  # 个人中心标签页
            if self.account_tab_widget is None:
                self._load_account_tab()
        elif index == 4:  # 关于标签页
            if self.about_tab_widget is None:
                self._load_about_tab()

    
    def _load_notification_tab(self):
        """加载通知设置标签页"""
        if self.notification_tab_widget is not None:
            return  # 已经加载过了

        try:
            self.notification_tab_widget = self.create_notification_tab()
            self.tabs.setTabEnabled(2, True)  # 确保标签页可用
            # 替换占位widget
            self.tabs.removeTab(2)
            self.tabs.insertTab(2, self.notification_tab_widget, "🔔 通知设置")
            self.tabs.setCurrentIndex(2)  # 切换到通知设置标签页
        except Exception as e:
            logging.error(f"加载通知设置标签页失败: {e}")
            # 显示错误提示
            from PySide6.QtWidgets import QLabel
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_label = QLabel(f"加载通知设置失败: {e}")
            error_label.setStyleSheet("color: red; padding: 20px;")
            error_layout.addWidget(error_label)
            self.notification_tab_widget = error_widget
            self.tabs.removeTab(2)
            self.tabs.insertTab(2, self.notification_tab_widget, "🔔 通知设置")


    def _load_account_tab(self):
        """加载个人中心标签页"""  
        if self.account_tab_widget is not None:  
            return  # 已经加载过了  
  
        try:  
            self.account_tab_widget = self._create_account_tab()  
            self.tabs.setTabEnabled(3, True)  # 确保标签页可用
            # 替换占位widget
            self.tabs.removeTab(3)
            self.tabs.insertTab(3, self.account_tab_widget, "👤 个人中心")
            self.tabs.setCurrentIndex(3)  # 切换到个人中心标签页  
        except Exception as e:
            import logging
            logging.error(f"加载个人中心标签页失败: {e}")
            from PySide6.QtWidgets import QLabel
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_label = QLabel(f"加载个人中心标签页失败: {e}")  
            error_label.setStyleSheet("color: red; padding: 20px;")  
            error_layout.addWidget(error_label)
            self.account_tab_widget = error_widget
            self.tabs.removeTab(3)
            self.tabs.insertTab(3, self.account_tab_widget, "👤 个人中心")

    def _load_about_tab(self):
        """加载关于标签页"""
        if self.about_tab_widget is not None:
            return  # 已经加载过了

        try:
            self.about_tab_widget = self.create_about_tab()
            self.tabs.setTabEnabled(4, True)  # 确保标签页可用
            # 替换占位widget
            self.tabs.removeTab(4)
            self.tabs.insertTab(4, self.about_tab_widget, "📖 关于")
            self.tabs.setCurrentIndex(4)  # 切换到关于标签页
        except Exception as e:
            import logging
            import traceback
            logging.error(f"加载关于标签页失败: {e}")
            logging.error(traceback.format_exc())
            from PySide6.QtWidgets import QLabel
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_label = QLabel(f"加载关于标签页失败: {e}\n\n请检查日志文件获取详细信息")
            error_label.setStyleSheet("color: red; padding: 20px;")
            error_layout.addWidget(error_label)
            self.about_tab_widget = error_widget
            self.tabs.removeTab(4)
            self.tabs.insertTab(4, self.about_tab_widget, "📖 关于")
            self.tabs.setCurrentIndex(4)  # 确保切换到关于标签页显示错误信息

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
        basic_group = QGroupBox("🔧 基本设置")
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

        # 预设高度选项 - 精简为3个档位
        self.height_presets = [
            ("细", 10),
            ("标准", 20),
            ("粗", 30)
        ]

        self.height_preset_buttons = []
        for name, height in self.height_presets:
            btn = QPushButton(f"{name} ({height}px)")
            btn.setCheckable(True)
            btn.setMaximumWidth(100)
            # 使用 partial 避免 Lambda 循环引用
            btn.clicked.connect(partial(self.set_height_preset, height))
            height_preset_layout.addWidget(btn)
            self.height_preset_buttons.append((btn, height))

        height_layout.addWidget(self.height_preset_group)

        # 自定义高度输入
        custom_label = QLabel("自定义:")
        height_layout.addWidget(custom_label)

        self.height_spin = QSpinBox()
        self.height_spin.setStyleSheet(StyleManager.input_number())
        self.height_spin.setRange(8, 100)
        # 延迟读取配置值，避免配置未加载时出错
        current_height = self.config.get('bar_height', 20) if self.config else 20
        self.height_spin.setValue(current_height)
        self.height_spin.setSuffix(" px")
        self.height_spin.setMaximumWidth(80)
        self.height_spin.valueChanged.connect(self.on_height_value_changed)
        height_layout.addWidget(self.height_spin)

        height_layout.addStretch()

        basic_layout.addRow("进度条高度:", height_container)

        # 延迟更新按钮状态，避免配置未加载时出错
        QTimer.singleShot(100, self.update_height_preset_buttons)

        # 显示器索引
        self.screen_spin = QSpinBox()
        self.screen_spin.setStyleSheet(StyleManager.input_number())
        self.screen_spin.setRange(0, 10)
        self.screen_spin.setValue(self.config.get('screen_index', 0) if self.config else 0)
        basic_layout.addRow("显示器索引:", self.screen_spin)

        # 更新间隔
        self.interval_spin = QSpinBox()
        self.interval_spin.setStyleSheet(StyleManager.input_number())
        self.interval_spin.setRange(100, 60000)
        self.interval_spin.setValue(self.config.get('update_interval', 1000) if self.config else 1000)
        self.interval_spin.setSuffix(" 毫秒")
        basic_layout.addRow("更新间隔:", self.interval_spin)

        # 开机自启动
        autostart_container = QWidget()
        autostart_layout = QHBoxLayout(autostart_container)
        autostart_layout.setContentsMargins(0, 0, 0, 0)

        self.autostart_check = QCheckBox("开机自动启动")
        self.autostart_check.setToolTip("勾选后，GaiYa每日进度条将在Windows开机时自动启动")
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

        basic_layout.addRow("自启动:", autostart_container)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # 颜色设置组
        color_group = QGroupBox("🎨 颜色设置")
        color_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        color_layout = QFormLayout()
        color_layout.setVerticalSpacing(15)  # 增加纵向间距
        color_layout.setHorizontalSpacing(10)

        # 背景颜色
        bg_color_layout = QHBoxLayout()
        bg_color = self.config.get('background_color', '#505050') if self.config else '#505050'
        self.bg_color_input = QLineEdit(bg_color)
        self.bg_color_input.setMaximumWidth(100)
        self.bg_color_input.setFixedHeight(36)
        self.bg_color_btn = QPushButton("选择颜色")
        self.bg_color_btn.setFixedSize(80, 36)
        self.bg_color_btn.setStyleSheet("QPushButton { padding: 8px 12px; font-size: 12px; }")
        # 使用 partial 避免 Lambda 循环引用
        self.bg_color_btn.clicked.connect(partial(self.choose_color, self.bg_color_input))
        self.bg_color_preview = QLabel()
        self.update_color_preview(self.bg_color_input, self.bg_color_preview)
        bg_color_layout.addWidget(self.bg_color_input)
        bg_color_layout.addSpacing(10)  # 横向间距
        bg_color_layout.addWidget(self.bg_color_btn)
        bg_color_layout.addSpacing(10)  # 横向间距
        bg_color_layout.addWidget(self.bg_color_preview)
        bg_color_layout.addStretch()
        color_layout.addRow("背景颜色:", bg_color_layout)

        # 背景透明度
        self.opacity_spin = QSpinBox()
        self.opacity_spin.setStyleSheet(StyleManager.input_number())
        self.opacity_spin.setRange(0, 255)
        self.opacity_spin.setValue(self.config.get('background_opacity', 180) if self.config else 180)
        color_layout.addRow("背景透明度:", self.opacity_spin)

        # 时间标记颜色
        marker_color_layout = QHBoxLayout()
        marker_color = self.config.get('marker_color', '#FF0000') if self.config else '#FF0000'
        self.marker_color_input = QLineEdit(marker_color)
        self.marker_color_input.setMaximumWidth(100)
        self.marker_color_input.setFixedHeight(36)
        self.marker_color_btn = QPushButton("选择颜色")
        self.marker_color_btn.setFixedSize(80, 36)
        self.marker_color_btn.setStyleSheet("QPushButton { padding: 8px 12px; font-size: 12px; }")
        # 使用 partial 避免 Lambda 循环引用
        self.marker_color_btn.clicked.connect(partial(self.choose_color, self.marker_color_input))
        self.marker_color_preview = QLabel()
        self.update_color_preview(self.marker_color_input, self.marker_color_preview)
        marker_color_layout.addWidget(self.marker_color_input)
        marker_color_layout.addSpacing(10)  # 横向间距
        marker_color_layout.addWidget(self.marker_color_btn)
        marker_color_layout.addSpacing(10)  # 横向间距
        marker_color_layout.addWidget(self.marker_color_preview)
        marker_color_layout.addStretch()
        color_layout.addRow("时间标记颜色:", marker_color_layout)

        # 时间标记宽度
        self.marker_width_spin = QSpinBox()
        self.marker_width_spin.setStyleSheet(StyleManager.input_number())
        self.marker_width_spin.setRange(1, 10)
        self.marker_width_spin.setValue(self.config.get('marker_width', 2) if self.config else 2)
        self.marker_width_spin.setSuffix(" 像素")
        color_layout.addRow("时间标记宽度:", self.marker_width_spin)

        # 时间标记类型
        marker_type_layout = QHBoxLayout()
        self.marker_type_combo = QComboBox()
        self.marker_type_combo.setStyleSheet(StyleManager.dropdown())
        self.marker_type_combo.addItems(["line", "image", "gif"])
        marker_type = self.config.get('marker_type', 'line') if self.config else 'line'
        self.marker_type_combo.setCurrentText(marker_type)
        self.marker_type_combo.currentTextChanged.connect(self.on_marker_type_changed)
        marker_type_layout.addWidget(self.marker_type_combo)

        marker_type_hint = QLabel("(line=线条, image=图片, gif=动画)")
        marker_type_hint.setStyleSheet("color: #888888; font-size: 9pt;")
        marker_type_layout.addWidget(marker_type_hint)
        marker_type_layout.addStretch()

        color_layout.addRow("时间标记类型:", marker_type_layout)

        # 标记图片路径
        marker_image_layout = QHBoxLayout()
        marker_image_path = self.config.get('marker_image_path', '') if self.config else ''
        self.marker_image_input = QLineEdit(marker_image_path)
        self.marker_image_input.setPlaceholderText("选择图片文件 (JPG/PNG/GIF/WebP)")
        marker_image_layout.addWidget(self.marker_image_input)

        marker_image_btn = QPushButton("📁 浏览")
        marker_image_btn.clicked.connect(self.choose_marker_image)
        marker_image_btn.setFixedSize(70, 36)
        marker_image_btn.setStyleSheet("QPushButton { padding: 8px 12px; font-size: 12px; }")
        marker_image_layout.addWidget(marker_image_btn)

        color_layout.addRow("标记图片:", marker_image_layout)

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
            ("小", 25),
            ("中", 35),
            ("大", 50)
        ]

        self.marker_size_preset_buttons = []
        for name, size in self.marker_size_presets:
            btn = QPushButton(f"{name} ({size}px)")
            btn.setCheckable(True)
            btn.setMaximumWidth(80)
            # 使用 partial 避免 Lambda 循环引用
            btn.clicked.connect(partial(self.set_marker_size_preset, size))
            marker_size_preset_layout.addWidget(btn)
            self.marker_size_preset_buttons.append((btn, size))

        marker_size_layout.addWidget(self.marker_size_preset_group)

        # 自定义大小输入
        custom_size_label = QLabel("自定义:")
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

        color_layout.addRow("标记图片大小:", marker_size_container)

        # 延迟更新按钮状态
        # 将在 _load_config_and_tasks 中更新

        # 标记图片 X 轴偏移
        self.marker_x_offset_spin = QSpinBox()
        self.marker_x_offset_spin.setStyleSheet(StyleManager.input_number())
        self.marker_x_offset_spin.setRange(-100, 100)
        self.marker_x_offset_spin.setValue(self.config.get('marker_x_offset', 0))
        self.marker_x_offset_spin.setSuffix(" px")
        self.marker_x_offset_spin.setMaximumWidth(100)
        x_offset_hint = QLabel("(正值向右,负值向左)")
        x_offset_hint.setStyleSheet("color: #888888; font-size: 9pt;")
        x_offset_layout = QHBoxLayout()
        x_offset_layout.addWidget(self.marker_x_offset_spin)
        x_offset_layout.addWidget(x_offset_hint)
        x_offset_layout.addStretch()
        color_layout.addRow("标记图片 X 偏移:", x_offset_layout)

        # 标记图片 Y 轴偏移
        self.marker_y_offset_spin = QSpinBox()
        self.marker_y_offset_spin.setStyleSheet(StyleManager.input_number())
        self.marker_y_offset_spin.setRange(-100, 100)
        self.marker_y_offset_spin.setValue(self.config.get('marker_y_offset', 0))
        self.marker_y_offset_spin.setSuffix(" px")
        self.marker_y_offset_spin.setMaximumWidth(100)
        y_offset_hint = QLabel("(正值向上,负值向下)")
        y_offset_hint.setStyleSheet("color: #888888; font-size: 9pt;")
        y_offset_layout = QHBoxLayout()
        y_offset_layout.addWidget(self.marker_y_offset_spin)
        y_offset_layout.addWidget(y_offset_hint)
        y_offset_layout.addStretch()
        color_layout.addRow("标记图片 Y 偏移:", y_offset_layout)

        # 标记动画播放速度
        self.marker_speed_spin = QSpinBox()
        self.marker_speed_spin.setStyleSheet(StyleManager.input_number())
        self.marker_speed_spin.setRange(10, 500)
        self.marker_speed_spin.setValue(self.config.get('marker_speed', 100))
        self.marker_speed_spin.setSuffix(" %")
        self.marker_speed_spin.setSingleStep(10)
        self.marker_speed_spin.setMaximumWidth(100)
        speed_hint = QLabel("(100%=原速, 200%=2倍速)")
        speed_hint.setStyleSheet("color: #888888; font-size: 9pt;")
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(self.marker_speed_spin)
        speed_layout.addWidget(speed_hint)
        speed_layout.addStretch()
        color_layout.addRow("动画播放速度:", speed_layout)

        color_group.setLayout(color_layout)
        layout.addWidget(color_group)

        # 初始化时根据类型显示/隐藏相关控件
        self.on_marker_type_changed(self.marker_type_combo.currentText())

        # 效果设置组
        effect_group = QGroupBox("✨ 视觉效果")
        effect_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        effect_layout = QFormLayout()
        effect_layout.setVerticalSpacing(12)
        effect_layout.setHorizontalSpacing(10)

        # 启用阴影
        self.shadow_check = QCheckBox("启用阴影效果")
        self.shadow_check.setChecked(self.config.get('enable_shadow', True))
        effect_layout.addRow(self.shadow_check)

        # 圆角半径
        self.radius_spin = QSpinBox()
        self.radius_spin.setStyleSheet(StyleManager.input_number())
        self.radius_spin.setRange(0, 20)
        self.radius_spin.setValue(self.config.get('corner_radius', 0))
        self.radius_spin.setSuffix(" 像素")
        effect_layout.addRow("圆角半径:", self.radius_spin)

        effect_group.setLayout(effect_layout)
        layout.addWidget(effect_group)

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
        ai_group = QGroupBox("🤖 AI智能规划")
        ai_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        ai_layout = QVBoxLayout()

        # 说明标签
        ai_hint = QLabel("💡 用自然语言描述您的计划,AI将自动生成任务时间表")
        ai_hint.setStyleSheet("color: #FF9800; font-style: italic; padding: 3px;")
        ai_layout.addWidget(ai_hint)

        # AI输入框
        input_container = QHBoxLayout()
        input_label = QLabel("描述您的计划:")
        input_label.setStyleSheet(StyleManager.label_subtitle())
        input_container.addWidget(input_label)

        self.ai_input = QLineEdit()
        self.ai_input.setStyleSheet(StyleManager.input_text())
        self.ai_input.setPlaceholderText("例如: 明天9点开会1小时,然后写代码到下午5点,中午12点休息1小时,晚上6点健身...")
        self.ai_input.setMinimumHeight(35)
        self.ai_input.returnPressed.connect(self.on_ai_generate_clicked)  # 支持回车键
        input_container.addWidget(self.ai_input)

        ai_layout.addLayout(input_container)

        # 按钮行
        ai_button_layout = QHBoxLayout()

        # AI生成按钮
        self.generate_btn = QPushButton("✨ 智能生成任务")
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
        self.quota_label = QLabel("配额状态: 加载中...")
        self.quota_label.setStyleSheet("color: #333333; padding: 5px;")
        ai_button_layout.addWidget(self.quota_label)

        # 刷新配额按钮
        refresh_quota_btn = QPushButton("🔄 刷新配额")
        refresh_quota_btn.clicked.connect(self.refresh_quota_status)
        refresh_quota_btn.setFixedHeight(36)
        refresh_quota_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        ai_button_layout.addWidget(refresh_quota_btn)

        ai_button_layout.addStretch()
        ai_layout.addLayout(ai_button_layout)

        ai_group.setLayout(ai_layout)
        top_layout.addWidget(ai_group)

        # 延迟加载配额状态，避免初始化时阻塞
        QTimer.singleShot(300, self.refresh_quota_status_async)

        # 立即显示初始状态（不需要等待）
        if hasattr(self, 'quota_label'):
            self.quota_label.setText("⏳ 正在连接云服务（可能需要10-15秒）...")
            self.quota_label.setStyleSheet("color: #ff9800; padding: 5px; font-weight: bold;")
        if hasattr(self, 'generate_btn'):
            self.generate_btn.setEnabled(False)

        # 说明标签
        info_label = QLabel("双击表格单元格可以编辑任务内容")
        info_label.setStyleSheet("color: #333333; font-style: italic;")
        top_layout.addWidget(info_label)

        # 预设主题选择区域
        theme_group = QGroupBox("🎨 预设主题配色")
        theme_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        theme_layout = QHBoxLayout()

        theme_label = QLabel("选择主题:")
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
        preview_label = QLabel("配色预览:")
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

        # 模板加载区域 - 单行显示所有模板
        self.template_group = QGroupBox("📋 预设模板")
        self.template_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        self.template_layout = QHBoxLayout()

        template_label = QLabel("快速加载:")
        self.template_layout.addWidget(template_label)

        # 动态生成所有模板按钮（从templates_config.json，只显示预设模板）
        if hasattr(self, 'template_manager') and self.template_manager:
            templates = self.template_manager.get_all_templates(include_custom=False)
            for template in templates:
                btn = QPushButton(template['name'])
                # 使用 partial 避免 Lambda 循环引用
                btn.clicked.connect(partial(self.load_template, template['filename']))
                btn.setStyleSheet(f"QPushButton {{ background-color: white; color: {template['button_color']}; border: 2px solid {template['button_color']}; border-radius: 6px; padding: 6px; }}")
                btn.setToolTip(template.get('description', ''))
                self.template_layout.addWidget(btn)
        else:
            # 备用：如果template_manager未初始化，显示提示
            fallback_label = QLabel("模板加载中...")
            fallback_label.setStyleSheet("color: #333333; font-style: italic;")
            self.template_layout.addWidget(fallback_label)
            # 延迟重新创建模板按钮
            QTimer.singleShot(500, self._reload_template_buttons)

        self.template_layout.addStretch()
        self.template_group.setLayout(self.template_layout)
        top_layout.addWidget(self.template_group)

        # 我的模板区域 - 下拉框选择样式
        self.custom_template_group = QGroupBox("💾 我的模板")
        self.custom_template_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        self.custom_template_layout = QHBoxLayout()

        custom_label = QLabel("选择模板:")
        self.custom_template_layout.addWidget(custom_label)

        # 创建自定义模板下拉框
        self.custom_template_combo = QComboBox()
        self.custom_template_combo.setStyleSheet(StyleManager.dropdown())
        self.custom_template_combo.setMinimumWidth(200)
        self.custom_template_layout.addWidget(self.custom_template_combo)

        # 加载按钮
        load_custom_btn = QPushButton("📂 加载")
        load_custom_btn.setToolTip("加载选中的自定义模板")
        load_custom_btn.setFixedHeight(36)
        load_custom_btn.setStyleSheet("QPushButton { padding: 8px 12px; border-radius: 4px; }")
        load_custom_btn.clicked.connect(self._load_selected_custom_template)
        self.custom_template_layout.addWidget(load_custom_btn)

        # 删除按钮
        delete_custom_btn = QPushButton("🗑️ 删除")
        delete_custom_btn.setToolTip("删除选中的自定义模板")
        delete_custom_btn.setFixedHeight(36)
        delete_custom_btn.setStyleSheet("QPushButton { padding: 8px 12px; border-radius: 4px; }")
        delete_custom_btn.clicked.connect(self._delete_selected_custom_template)
        self.custom_template_layout.addWidget(delete_custom_btn)

        # 动态加载自定义模板列表
        self._reload_custom_template_combo()

        self.custom_template_layout.addStretch()
        self.custom_template_group.setLayout(self.custom_template_layout)
        top_layout.addWidget(self.custom_template_group)

        layout.addLayout(top_layout)

        # 可视化时间轴编辑器（延迟创建，避免初始化时阻塞）
        timeline_group = QGroupBox("🎨 可视化时间轴编辑器")
        timeline_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        timeline_layout = QVBoxLayout()

        timeline_hint = QLabel("💡 提示：拖动色块边缘可调整任务时长")
        timeline_hint.setStyleSheet("color: #FFD700; font-style: italic; padding: 5px;")
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
        self.tasks_table.setHorizontalHeaderLabels(["开始时间", "结束时间", "任务名称", "背景颜色", "文字颜色", "操作"])
        self.tasks_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tasks_table.setMinimumHeight(300)

        # 监听表格项的变化,实时同步到时间轴
        self.tasks_table.itemChanged.connect(self.on_table_item_changed)

        # 延迟加载任务到表格，避免初始化时阻塞UI
        QTimer.singleShot(100, self.load_tasks_to_table)

        layout.addWidget(self.tasks_table)

        # 按钮组
        button_layout = QHBoxLayout()

        add_btn = QPushButton("➕ 添加任务")
        add_btn.clicked.connect(self.add_task)
        add_btn.setFixedHeight(36)
        add_btn.setStyleSheet(StyleManager.button_minimal())

        save_template_btn = QPushButton("💾 保存为模板")
        save_template_btn.clicked.connect(self.save_as_template)
        save_template_btn.setFixedHeight(36)
        save_template_btn.setStyleSheet(StyleManager.button_minimal())

        load_custom_btn = QPushButton("📂 加载自定义模板")
        load_custom_btn.clicked.connect(self.load_custom_template)
        load_custom_btn.setFixedHeight(36)
        load_custom_btn.setStyleSheet(StyleManager.button_minimal())

        clear_btn = QPushButton("🗑️ 清空所有任务")
        clear_btn.clicked.connect(self.clear_all_tasks)
        clear_btn.setFixedHeight(36)
        clear_btn.setStyleSheet(StyleManager.button_danger())

        button_layout.addWidget(add_btn)
        button_layout.addWidget(save_template_btn)
        button_layout.addWidget(load_custom_btn)
        button_layout.addWidget(clear_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # ========== 模板自动应用管理（放在最底部） ==========
        schedule_panel = QGroupBox("📅 模板自动应用管理")
        schedule_panel.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        schedule_layout = QVBoxLayout()

        # 说明文字
        schedule_hint = QLabel("💡 为每个模板设置自动应用的日期规则，到了指定时间会自动加载对应模板")
        schedule_hint.setStyleSheet("color: #333333; font-style: italic; padding: 5px;")
        schedule_layout.addWidget(schedule_hint)

        # 已配置规则表格
        self.schedule_table = QTableWidget()
        self.schedule_table.setStyleSheet(StyleManager.table())
        self.schedule_table.setColumnCount(4)
        self.schedule_table.setHorizontalHeaderLabels([
            "模板名称", "应用时间", "状态", "操作"
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

        add_schedule_btn = QPushButton("➕ 添加规则")
        add_schedule_btn.setFixedHeight(36)
        add_schedule_btn.setStyleSheet(StyleManager.button_primary())
        add_schedule_btn.clicked.connect(self._add_schedule_dialog)
        button_row.addWidget(add_schedule_btn)

        test_date_btn = QPushButton("🔍 测试日期")
        test_date_btn.setToolTip("测试指定日期会匹配到哪个模板")
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


    def update_colors_preview(self, task_colors):
        """更新任务配色预览"""
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


    def apply_selected_theme_silent(self):
        """静默应用选中的主题（不显示提示框）"""
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
            try:
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=4, ensure_ascii=False)
            except Exception as e:
                self.logger.error(f"保存主题配置失败: {e}")

    def apply_selected_theme(self):
        """应用选中的主题（显示提示）"""
        if not self.theme_manager:
            QMessageBox.warning(self, "错误", "主题管理器未初始化，请稍后再试")
            return
        
        # 从下拉框获取当前选中的主题ID
        if hasattr(self, 'theme_combo'):
            index = self.theme_combo.currentIndex()
            if index >= 0:
                theme_id = self.theme_combo.itemData(index)
                if theme_id:
                    self.selected_theme_id = theme_id
        
        if not self.selected_theme_id:
            QMessageBox.warning(self, "提示", "请先选择一个主题")
            return

        # 应用预设主题
        success = self.theme_manager.apply_preset_theme(self.selected_theme_id)
        if success:
            QMessageBox.information(self, "成功", f"已应用主题: {self.theme_manager.get_current_theme().get('name', 'Unknown')}")
            # 更新配置中的主题模式
            self.config.setdefault('theme', {})['mode'] = 'preset'
            self.config.setdefault('theme', {})['current_theme_id'] = self.selected_theme_id
        else:
            QMessageBox.warning(self, "错误", "应用主题失败")

    def apply_theme_colors_to_tasks(self):
        """应用主题配色到任务"""
        if not self.theme_manager:
            QMessageBox.warning(self, "错误", "主题管理器未初始化，请稍后再试")
            return
        
        theme = self.theme_manager.get_current_theme()
        if not theme:
            QMessageBox.warning(self, "提示", "请先选择一个主题")
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
            
            QMessageBox.information(self, "成功", "已应用主题配色到任务")

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


    def create_notification_tab(self):
        """创建通知设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 说明标签
        info_label = QLabel("配置任务提醒通知,让您不会错过任何重要时刻")
        info_label.setStyleSheet("color: #333333; font-style: italic; padding: 5px;")
        layout.addWidget(info_label)

        # 基础设置组
        basic_group = QGroupBox("⚙️ 基础设置")
        basic_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        basic_layout = QFormLayout()

        # 启用通知
        self.notify_enabled_check = QCheckBox("启用任务提醒通知")
        notification_config = self.config.get('notification', {})
        self.notify_enabled_check.setChecked(notification_config.get('enabled', True))
        self.notify_enabled_check.setMinimumHeight(36)
        self.notify_enabled_check.setStyleSheet("font-weight: bold;")
        basic_layout.addRow(self.notify_enabled_check)

        # 启用声音
        self.notify_sound_check = QCheckBox("播放提示音")
        self.notify_sound_check.setChecked(notification_config.get('sound_enabled', True))
        self.notify_sound_check.setMinimumHeight(36)
        basic_layout.addRow(self.notify_sound_check)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # 提醒时机设置组
        timing_group = QGroupBox("⏰ 提醒时机")
        timing_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        timing_layout = QVBoxLayout()
        timing_layout.setSpacing(15)  # 设置子元素之间的间距

        # 任务开始前提醒
        before_start_group = QGroupBox("🔔 任务开始前提醒")
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
        before_start_hint = QLabel("选择在任务开始前多久提醒(可多选):")
        before_start_hint.setStyleSheet("color: #888888; font-size: 9pt;")
        before_start_title_row.addWidget(before_start_hint)

        before_start_title_row.addStretch()

        # "任务开始时提醒"复选框放在右侧
        self.notify_on_start_check = QCheckBox("任务开始时提醒")
        self.notify_on_start_check.setChecked(notification_config.get('on_start', True))
        self.notify_on_start_check.setMinimumHeight(36)
        before_start_title_row.addWidget(self.notify_on_start_check)

        before_start_layout.addLayout(before_start_title_row)

        before_start_minutes = notification_config.get('before_start_minutes', [10, 5])

        # 提前提醒选项
        before_start_checkboxes_layout = QHBoxLayout()
        self.notify_before_start_checks = {}

        for minutes in [30, 15, 10, 5]:
            checkbox = QCheckBox(f"提前 {minutes} 分钟")
            checkbox.setChecked(minutes in before_start_minutes)
            checkbox.setMinimumHeight(36)
            self.notify_before_start_checks[minutes] = checkbox
            before_start_checkboxes_layout.addWidget(checkbox)

        before_start_checkboxes_layout.addStretch()
        before_start_layout.addLayout(before_start_checkboxes_layout)

        before_start_group.setLayout(before_start_layout)
        timing_layout.addWidget(before_start_group)

        # 任务结束前提醒
        before_end_group = QGroupBox("🔕 任务结束前提醒")
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
        before_end_hint = QLabel("选择在任务结束前多久提醒(可多选):")
        before_end_hint.setStyleSheet("color: #888888; font-size: 9pt;")
        before_end_title_row.addWidget(before_end_hint)

        before_end_title_row.addStretch()

        # "任务结束时提醒"复选框放在右侧
        self.notify_on_end_check = QCheckBox("任务结束时提醒")
        self.notify_on_end_check.setChecked(notification_config.get('on_end', False))
        self.notify_on_end_check.setMinimumHeight(36)
        before_end_title_row.addWidget(self.notify_on_end_check)

        before_end_layout.addLayout(before_end_title_row)

        before_end_minutes = notification_config.get('before_end_minutes', [5])

        before_end_checkboxes_layout = QHBoxLayout()
        self.notify_before_end_checks = {}

        for minutes in [10, 5, 3]:
            checkbox = QCheckBox(f"提前 {minutes} 分钟")
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
        quiet_group = QGroupBox("🌙 免打扰时段")
        quiet_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        quiet_layout = QFormLayout()

        quiet_hours = notification_config.get('quiet_hours', {})

        # 启用免打扰
        self.quiet_enabled_check = QCheckBox("启用免打扰时段")
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
        quiet_start_hint = QLabel("(在此时间后不发送通知)")
        quiet_start_hint.setStyleSheet("color: #888888; font-size: 9pt;")
        quiet_start_layout.addWidget(quiet_start_hint)
        quiet_start_layout.addStretch()
        quiet_layout.addRow("开始时间:", quiet_start_layout)

        # 免打扰结束时间
        quiet_end_layout = QHBoxLayout()
        self.quiet_end_time = QTimeEdit()
        self.quiet_end_time.setStyleSheet(StyleManager.input_time())
        self.quiet_end_time.setDisplayFormat("HH:mm")
        self.quiet_end_time.setFixedHeight(36)
        end_time_str = quiet_hours.get('end', '08:00')
        self.quiet_end_time.setTime(QTime.fromString(end_time_str, "HH:mm"))
        quiet_end_layout.addWidget(self.quiet_end_time)
        quiet_end_hint = QLabel("(在此时间前不发送通知)")
        quiet_end_hint.setStyleSheet("color: #888888; font-size: 9pt;")
        quiet_end_layout.addWidget(quiet_end_hint)
        quiet_end_layout.addStretch()
        quiet_layout.addRow("结束时间:", quiet_end_layout)

        quiet_example = QLabel("示例: 22:00 - 08:00 表示晚上10点到早上8点不打扰")
        quiet_example.setStyleSheet("color: #888888; font-size: 8pt; font-style: italic;")
        quiet_layout.addRow(quiet_example)

        quiet_group.setLayout(quiet_layout)
        layout.addWidget(quiet_group)

        layout.addStretch()
        return widget


    def _create_account_tab(self):
        """创建个人中心标签页"""
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

        title_label = QLabel("个人中心")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #333333;")
        header_layout.addWidget(title_label)

        from gaiya.core.auth_client import AuthClient
        auth_client = AuthClient()

        email = auth_client.get_user_email() or "未登录"
        user_tier = auth_client.get_user_tier()

        if email != "未登录":
            # 添加弹性空间，推动右侧内容到右边
            header_layout.addStretch()

            # 合并邮箱和会员等级到一行，右对齐显示
            tier_names = {"free": "免费用户", "pro": "高级版", "lifetime": "会员合伙人"}
            tier_name = tier_names.get(user_tier, user_tier)
            info_label = QLabel(f"邮箱：{email}  |  会员等级：{tier_name}")
            info_label.setStyleSheet("color: #333333; font-size: 14px;")
            header_layout.addWidget(info_label)

            # 添加退出登录按钮
            header_layout.addSpacing(15)
            logout_btn = QPushButton("退出登录")
            logout_btn.setFixedSize(100, 28)  # 增加宽度以防止文字被截断
            logout_btn.setStyleSheet(StyleManager.button_minimal())
            logout_btn.clicked.connect(self._on_logout_clicked)
            header_layout.addWidget(logout_btn)

        # 将横向布局添加到主布局
        layout.addLayout(header_layout)
        layout.addSpacing(20)  # 添加间距与下方内容分隔

        if email != "未登录":
            if user_tier == "free":
                tip_label = QLabel("会员套餐对比")
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
                        "name": "Pro 月度",
                        "price": "¥29",
                        "period": "/月",
                        "validity": "有效期30天",
                        "renewal": "到期后不会自动扣费",
                        "type": "monthly",
                        "features": ["所有免费功能 +", "20次/天 AI智能规划", "统计报告分析", "去除进度条水印", "数据云同步", "抢先体验新功能", "加入VIP会员群"]
                    },
                    {
                        "id": "pro_yearly",
                        "name": "Pro 年度",
                        "price": "¥199",
                        "period": "/年",
                        "monthly_price": "¥16.6",
                        "original_price": "¥348",
                        "discount_badge": "节省 40%",
                        "validity": "有效期365天",
                        "renewal": "到期后不会自动扣费",
                        "type": "yearly",
                        "features": ["所有免费功能 +", "20次/天 AI智能规划", "统计报告分析", "去除进度条水印", "数据云同步", "抢先体验新功能", "加入VIP会员群"]
                    },
                    {
                        "id": "lifetime",
                        "name": "会员合伙人",
                        "price": "¥1200",
                        "period": "",
                        "validity": "永久有效",
                        "renewal": "一次购买,终身可用",
                        "type": "lifetime",
                        "features": ["所有免费功能 +", "无限次 AI智能规划", "统计报告分析", "去除进度条水印", "数据云同步", "33%引荐返现比例", "专属合伙人社群", "优先体验所有新功能", "专属1v1咨询服务", "共同成长,分享价值"]
                    },
                ]

                self.plan_cards = []
                self.selected_plan_id = "pro_yearly"

                for i, plan in enumerate(plans):
                    if plan['type'] == 'yearly':
                        card = self._create_featured_plan_card(plan, is_selected=True)
                    elif plan['type'] == 'lifetime':
                        card = self._create_lifetime_plan_card(plan)
                    else:  # monthly
                        card = self._create_regular_plan_card(plan)

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

                # payment_title = QLabel("选择支付方式")
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

                # alipay_radio = QRadioButton("支付宝")
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

                # wxpay_radio = QRadioButton("微信支付")
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
                info_label = QLabel("感谢您的支持！")
                info_label.setStyleSheet("color: #333333; font-size: 14px;")
                layout.addWidget(info_label)
        else:
            # 未登录状态：显示登录/注册UI
            from gaiya.ui.auth_ui import AuthDialog

            # 创建说明文字
            welcome_label = QLabel("👋 欢迎使用 GaiYa 每日进度条")
            welcome_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333333; margin-bottom: 10px;")
            welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(welcome_label)

            tip_label = QLabel("登录后即可使用 AI智能规划、数据云同步等高级功能")
            tip_label.setStyleSheet("color: #AAAAAA; font-size: 14px; margin-bottom: 20px;")
            tip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(tip_label)

            # 创建登录按钮
            login_button = QPushButton("🔑 点击登录 / 注册")
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
            features_label = QLabel("🎁 登录后享受的权益：")
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
                feature_label.setStyleSheet("color: #CCCCCC; font-size: 14px; margin: 5px 0px;")
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

        # 显示成功提示
        QMessageBox.information(
            self,
            "登录成功",
            f"欢迎回来，{user_info.get('email', '用户')}！\n\n"
            f"您的账户信息已更新，现在可以使用所有高级功能。"
        )

        # 重新加载个人中心tab以显示登录后的内容
        self.account_tab_widget = None
        self._load_account_tab()

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
            # 调用登出
            from gaiya.core.auth_client import AuthClient
            auth_client = AuthClient()
            result = auth_client.signout()

            if result.get("success"):
                # 提示用户
                QMessageBox.information(
                    self,
                    "退出成功",
                    "已退出当前账号。\n\n请重新启动应用以切换到游客模式。"
                )

                # 关闭配置管理器
                self.close()
            else:
                # 即使失败也提示成功（因为本地Token已清除）
                QMessageBox.information(
                    self,
                    "退出成功",
                    "已退出当前账号。\n\n请重新启动应用以切换到游客模式。"
                )
                self.close()

    def _check_login_and_guide(self, feature_name: str = "此功能") -> bool:
        """
        检查用户是否已登录，如果未登录则显示引导对话框

        Args:
            feature_name: 功能名称，用于提示

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

        # 未登录，显示引导对话框
        reply = QMessageBox.question(
            self,
            "需要登录",
            f"💡 {feature_name}需要登录后才能使用。\n\n"
            f"登录后您将享有：\n"
            f"• 免费用户：3次/天 AI智能规划\n"
            f"• Pro会员：20次/天 AI智能规划\n"
            f"• 更多高级功能和服务\n\n"
            f"是否前往个人中心登录？",
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
            True: 配额充足，可以继续
            False: 配额已用完，显示升级对话框
        """
        from gaiya.core.auth_client import AuthClient
        from gaiya.ui.onboarding import QuotaExhaustedDialog

        auth_client = AuthClient()
        user_tier = auth_client.get_user_tier()

        # Pro会员或以上不受限制
        if user_tier in ['pro', 'lifetime']:
            return True

        # 免费用户检查配额
        remaining_quota = auth_client.get_quota_status().get('remaining', 0)

        if remaining_quota <= 0:
            # 配额已用完，显示升级对话框
            dialog = QuotaExhaustedDialog(self)
            dialog.upgrade_requested.connect(self._on_quota_upgrade_requested)
            dialog.exec()
            return False

        return True

    def _on_quota_upgrade_requested(self):
        """配额用尽对话框中用户请求升级会员"""
        # 切换到个人中心tab（index=3）
        self.tabs.setCurrentIndex(3)

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

    def _create_featured_plan_card(self, plan: dict, is_selected: bool = False):
        """创建年度卡片（中间，突出显示）"""
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
            monthly_period_label = QLabel("/月")
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
        button = QPushButton("升级会员")
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

    def _create_regular_plan_card(self, plan: dict):
        """创建月度卡片（普通样式）"""
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
        button = QPushButton("升级会员")
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

    def _create_lifetime_plan_card(self, plan: dict):
        """创建会员合伙人卡片（右侧，特殊样式）"""
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

        # 标题区域（标题 + 限量标签）
        title_row = QHBoxLayout()
        title_row.setSpacing(0)
        title_row.setContentsMargins(0, 0, 0, 0)

        # 左侧弹性空间（用于居中对齐）
        title_row.addStretch()

        # 标题文字
        name_label = QLabel(plan['name'])
        name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333333; background: transparent;")
        title_row.addWidget(name_label)

        # 标题与标签之间的间距
        title_row.addSpacing(10)

        # 限量标签（深金色背景）
        limited_badge = QLabel("限量1000名")
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
        limited_badge.setMinimumWidth(90)
        limited_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_row.addWidget(limited_badge)

        # 右侧弹性空间（用于居中对齐）
        title_row.addStretch()

        layout.addLayout(title_row)

        layout.addSpacing(15)

        # 价格区域
        price_layout = QHBoxLayout()
        price_layout.setSpacing(2)
        price_label = QLabel(plan['price'])
        price_label.setStyleSheet("font-size: 36px; font-weight: bold; color: #FFD700; background: transparent;")
        price_layout.addStretch()
        price_layout.addWidget(price_label)
        price_layout.addStretch()
        layout.addLayout(price_layout)

        # 一次付费说明
        onetime_label = QLabel("一次付费")
        onetime_label.setStyleSheet("font-size: 12px; color: #888888; background: transparent;")
        onetime_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(onetime_label)

        # 终身可用强调
        lifetime_label = QLabel("终身可用")
        lifetime_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #FFD700; background: transparent;")
        lifetime_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lifetime_label)

        layout.addSpacing(15)

        # 邀请函链接
        invitation_link = QLabel('<a href="#" style="color: #666666; text-decoration: none;">📜 阅读合伙人邀请函</a>')
        invitation_link.setStyleSheet("font-size: 12px; background: transparent;")
        invitation_link.setAlignment(Qt.AlignmentFlag.AlignCenter)
        invitation_link.setOpenExternalLinks(False)
        invitation_link.linkActivated.connect(lambda: self._show_invitation_dialog())
        invitation_link.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(invitation_link)

        layout.addSpacing(8)

        # 按钮（渐变样式）
        button = QPushButton("成为合伙人")
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
        dialog.setWindowTitle("GaiYa每日进度条")
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
        title_label = QLabel("致 GaiYa 会员合伙人的一封信")
        title_label.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: #654321;
            background: transparent;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 副标题
        subtitle_label = QLabel("邀请您共同成长，共享价值")
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

        <p style="margin-bottom: 15px;">于是有了 GaiYa —— 一条桌面进度条，默默守护你的每一分钟。</p>

        <p style="margin-bottom: 15px; margin-top: 20px;"><b style="color: #8B4513;">✨ 为什么做 GaiYa？</b></p>

        <p style="margin-bottom: 15px;">我曾亲手打造过多个从0到1的产品，有成功也有失败。但每次复盘，最深的感悟都是：<b>时间管理的本质，不是效率，而是觉察</b>。</p>

        <p style="margin-bottom: 15px;">当你看见那条进度条一点点推进，看见今天已经过去了63%，看见"下班"色块还有2小时才到 —— 你会做出不同的选择。这就是 GaiYa 想做的事：<b>让时间可视化，让选择更自主</b>。</p>

        <p style="margin-bottom: 15px; margin-top: 20px;"><b style="color: #8B4513;">🤝 会员合伙人意味着什么？</b></p>

        <p style="margin-bottom: 15px;">GaiYa 现在还很年轻。我希望找到一群真正认同这个理念的人，不只是用户，而是<b>产品的共创者</b>。</p>

        <p style="margin-bottom: 15px;">成为会员合伙人，你将获得：</p>

        <p style="margin-bottom: 10px;"><b>1. 终身的工具陪伴</b></p>
        <p style="margin-bottom: 15px; margin-left: 20px;">一次付费，永久使用。无限次AI任务生成、去水印、数据云同步、所有未来新功能 —— 我会持续打磨，让它真正成为你效率工作流的一部分。</p>

        <p style="margin-bottom: 10px;"><b>2. 产品决策的话语权</b></p>
        <p style="margin-bottom: 15px; margin-left: 20px;">你将获邀加入<b>会员合伙人专属微信群（首批限额1000人）</b>，与我和其他种子用户直接对话。作为首批成员，你将亲历社群从0到1的搭建过程。你的需求、你的吐槽、你的建议 —— 都会直接影响产品的走向。</p>

        <p style="margin-bottom: 10px;"><b>3. 优先体验与专属支持</b></p>
        <p style="margin-bottom: 15px; margin-left: 20px;">所有新功能，你将第一时间体验。遇到问题？<b>专属1v1咨询通道</b>，我会亲自回复，帮你定制最适合的工作流。</p>

        <p style="margin-bottom: 10px;"><b>4. 共享成长的价值（规划中）</b></p>
        <p style="margin-bottom: 15px; margin-left: 20px;">我正在搭建<b>33%推荐返现机制</b>。当 GaiYa 帮到你的朋友时，你也将获得实际收益。这不是分销，而是价值共享 —— 好产品，值得一起传播。</p>

        <p style="margin-bottom: 15px; margin-top: 20px;"><b style="color: #8B4513;">💰 关于1200元会员费用</b></p>

        <p style="margin-bottom: 15px;">这不是一个拍脑袋的数字。让我和你算笔账：</p>

        <p style="margin-bottom: 10px; margin-left: 20px;">• AI任务生成的API成本，每次约0.5元，月度会员每月20次 = 10元/月</p>
        <p style="margin-bottom: 10px; margin-left: 20px;">• 云同步服务器费用，每用户每年约50元</p>
        <p style="margin-bottom: 10px; margin-left: 20px;">• 持续开发投入（新功能、bug修复、1v1客服支持）</p>

        <p style="margin-bottom: 15px;">1200元换算下来，相当于<b>年费200元使用6年</b>——而我承诺的是<b style="color: #4CAF50;">终身使用</b>。这是我对产品长期主义的承诺。</p>

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

        <p style="margin-bottom: 15px;">会员合伙人计划属于数字服务，一旦加入<b>无法退款</b>。但我相信，如果你真的认同这个理念，1200元换来的不只是一个工具，而是：</p>

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
        button = QPushButton("我愿意成为会员合伙人")
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
        title_label = QLabel("💡 会员提示")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333333; background: transparent;")
        layout.addWidget(title_label)

        # 说明文字
        tips_text = """GaiYa 致力于做优秀的时间管理工具，始终坚持无广告、无打扰、无冗余，简单而纯粹，我们将继续提供更加令人愉悦的用户体验。

与此同时，我们深知，一个产品能够长久持续地运营下去，也需要有稳定的发展模式。如果你有意支持我们，可以开通会员，享受更丰富的 AI 功能，非常感谢你的支持！"""

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
        title_label = QLabel("💎 会员方案详细对比")
        title_label.setStyleSheet("color: #333333; font-size: 18px; font-weight: bold; margin: 10px 0px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 创建表格
        table = QTableWidget()
        table.setStyleSheet(StyleManager.table())
        table.setColumnCount(5)  # 功能名称 + 4个等级
        table.setHorizontalHeaderLabels(["功能特性", "免费版", "Pro 月度", "Pro 年度", "永久会员"])

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
                "name": "【核心功能】",
            },
            # 每日进度条
            {
                "type": "feature",
                "name": "每日进度条显示",
                "free": "✓ 带水印",
                "monthly": "✓ 无水印",
                "yearly": "✓ 无水印",
                "lifetime": "✓ 无水印",
            },
            # AI任务规划
            {
                "type": "feature",
                "name": "AI 智能任务规划",
                "free": "3次/天",
                "monthly": "20次/天",
                "yearly": "20次/天",
                "lifetime": "无限制",
            },
            # 统计报告分析
            {
                "type": "feature",
                "name": "统计报告分析",
                "free": "✗",
                "monthly": "✓",
                "yearly": "✓",
                "lifetime": "✓",
            },
            # 【高级功能】分组标题
            {
                "type": "group",
                "name": "【高级功能】",
            },
            # 主题自定义
            {
                "type": "feature",
                "name": "主题自定义",
                "free": "✗",
                "monthly": "✓",
                "yearly": "✓",
                "lifetime": "✓",
            },
            # 数据云同步
            {
                "type": "feature",
                "name": "数据云同步",
                "free": "✗",
                "monthly": "✓",
                "yearly": "✓",
                "lifetime": "✓",
            },
            # 抢先体验新功能
            {
                "type": "feature",
                "name": "抢先体验新功能",
                "free": "✗",
                "monthly": "✓",
                "yearly": "✓",
                "lifetime": "✓",
            },
            # 加入VIP会员群
            {
                "type": "feature",
                "name": "加入VIP会员群",
                "free": "✗",
                "monthly": "✓",
                "yearly": "✓",
                "lifetime": "✓",
            },
            # 【会员权益】分组标题
            {
                "type": "group",
                "name": "【会员权益】",
            },
            # 有效期
            {
                "type": "feature",
                "name": "有效期",
                "free": "-",
                "monthly": "30天",
                "yearly": "365天",
                "lifetime": "永久",
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
        table.setColumnWidth(4, 120)  # 永久会员

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

    def _on_plan_button_clicked(self, plan_id: str):
        """处理套餐按钮点击 - 直接触发支付流程"""
        # 设置选中的套餐
        self.selected_plan_id = plan_id
        # 更新卡片样式（选中状态）
        self._on_plan_card_clicked(plan_id)
        # 直接触发支付
        self._on_purchase_clicked()

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
        #     QMessageBox.warning(self, "提示", "请选择支付方式")
        #     return
        # pay_type = selected_button.property("pay_type")

        # 创建订单
        auth_client = AuthClient()

        # 添加日志输出以便调试
        import logging
        logging.info(f"[支付调试] 准备创建订单 - plan_type: {self.selected_plan_id}, pay_type: {pay_type}")

        result = auth_client.create_payment_order(
            plan_type=self.selected_plan_id,
            pay_type=pay_type
        )

        logging.info(f"[支付调试] 订单创建结果: {result}")

        if result.get("success"):
            # 订单创建成功，直接打开支付页面
            payment_url = result.get("payment_url")
            params = result.get("params", {})
            out_trade_no = result.get("out_trade_no")

            # 拼接支付参数到URL
            from urllib.parse import urlencode
            query_string = urlencode(params)
            full_payment_url = f"{payment_url}?{query_string}"

            logging.info(f"[PAYMENT] Opening payment URL: {full_payment_url[:100]}...")
            logging.info(f"[PAYMENT] Order No: {out_trade_no}, Type: {pay_type}")

            # 在浏览器中打开支付URL
            QDesktopServices.openUrl(QUrl(full_payment_url))

            # 显示等待支付对话框（非阻塞）
            self.payment_polling_dialog = QMessageBox(self)
            self.payment_polling_dialog.setWindowTitle("等待支付")
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
            # 使用 partial 避免 Lambda 循环引用
            self.payment_timer.timeout.connect(partial(self._check_payment_status, out_trade_no, auth_client))
            self.payment_timer.start()

            # 监听取消按钮
            self.payment_polling_dialog.rejected.connect(self._stop_payment_polling)

            # 显示对话框（非阻塞）
            self.payment_polling_dialog.show()
        else:
            # 订单创建失败
            error_msg = result.get("error", "创建订单失败")

            # 针对支付渠道错误给出更详细的提示
            if "MERCHANT_STATUS_NOT_NORMAL" in error_msg or "渠道" in error_msg:
                detailed_msg = (
                    f"支付渠道暂时不可用：{error_msg}\n\n"
                    "可能的原因：\n"
                    "• 支付渠道临时维护中\n"
                    "• 需要在商户后台完成渠道签约\n\n"
                    "建议操作：\n"
                    "1. 稍后重试（5-10分钟后）\n"
                    "2. 尝试切换支付方式（支付宝/微信）\n"
                    "3. 联系支付服务商客服（zpayz.cn）"
                )
                logging.error(f"[PAYMENT] Channel error: {error_msg}")
            else:
                # 显示详细的调试信息
                detailed_msg = (
                    f"创建订单失败：{error_msg}\n\n"
                    f"调试信息：\n"
                    f"• 套餐类型: {self.selected_plan_id}\n"
                    f"• 支付方式: {pay_type}"
                )
                logging.error(f"[PAYMENT] Create order failed - plan_type: {self.selected_plan_id}, error: {error_msg}")

            QMessageBox.critical(self, "创建订单失败", detailed_msg)

    def _check_payment_status(self, out_trade_no: str, auth_client):
        """检查支付状态"""
        from PySide6.QtWidgets import QMessageBox
        result = auth_client.query_payment_order(out_trade_no)

        if result.get("success"):
            order = result.get("order", {})
            status = order.get("status")

            if status == "paid":
                # 支付成功
                self._stop_payment_polling()

                QMessageBox.information(
                    self,
                    "支付成功",
                    "支付已完成！\n您的会员权益已激活。\n\n请重新启动应用以生效。"
                )

                # 重新加载个人中心tab以刷新会员状态
                self.account_tab_widget = None
                self._load_account_tab()

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

            color_input = QLineEdit(task['color'])
            color_input.setMaximumWidth(80)
            color_input.setFixedHeight(36)

            color_btn = QPushButton("选色")
            color_btn.setFixedSize(50, 36)
            color_btn.setStyleSheet("QPushButton { padding: 8px; font-size: 12px; }")
            # 使用 partial 避免 Lambda 循环引用
            color_btn.clicked.connect(partial(self.choose_color, color_input))

            color_preview = QLabel()
            color_preview.setFixedSize(30, 20)
            color_preview.setStyleSheet(f"background-color: {task['color']}; border: 1px solid #ccc;")

            # 更新颜色预览并同步到时间轴（使用防抖，避免频繁刷新）
            def on_color_changed(text, prev_label):
                prev_label.setStyleSheet(f"background-color: {text}; border: 1px solid #ccc;")
                # 使用防抖，避免频繁刷新时间轴
                if not hasattr(self, '_timeline_refresh_timer'):
                    self._timeline_refresh_timer = QTimer()
                    self._timeline_refresh_timer.setSingleShot(True)
                    self._timeline_refresh_timer.timeout.connect(self.refresh_timeline_from_table)
                
                # 重置定时器
                if self._timeline_refresh_timer.isActive():
                    self._timeline_refresh_timer.stop()
                self._timeline_refresh_timer.start(300)  # 300ms防抖

            color_input.textChanged.connect(lambda text, prev=color_preview: on_color_changed(text, prev))

            color_layout.addWidget(color_input)
            color_layout.addWidget(color_btn)
            color_layout.addWidget(color_preview)

            self.tasks_table.setCellWidget(row, 3, color_widget)

            # 文字颜色选择
            text_color = task.get('text_color', '#FFFFFF')  # 默认白色
            text_color_widget = QWidget()
            text_color_layout = QHBoxLayout(text_color_widget)
            text_color_layout.setContentsMargins(4, 4, 4, 4)

            text_color_input = QLineEdit(text_color)
            text_color_input.setMaximumWidth(80)
            text_color_input.setFixedHeight(36)

            text_color_btn = QPushButton("选色")
            text_color_btn.setFixedSize(50, 36)
            text_color_btn.setStyleSheet("QPushButton { padding: 8px; font-size: 12px; }")
            # 使用 partial 避免 Lambda 循环引用
            text_color_btn.clicked.connect(partial(self.choose_color, text_color_input))

            text_color_preview = QLabel()
            text_color_preview.setFixedSize(30, 20)
            text_color_preview.setStyleSheet(f"background-color: {text_color}; border: 1px solid #ccc;")

            # 更新文字颜色预览并同步到时间轴
            def on_text_color_changed(text, prev_label):
                prev_label.setStyleSheet(f"background-color: {text}; border: 1px solid #ccc;")
                # 使用防抖，避免频繁刷新时间轴
                if not hasattr(self, '_timeline_refresh_timer'):
                    self._timeline_refresh_timer = QTimer()
                    self._timeline_refresh_timer.setSingleShot(True)
                    self._timeline_refresh_timer.timeout.connect(self.refresh_timeline_from_table)

                # 重置定时器
                if self._timeline_refresh_timer.isActive():
                    self._timeline_refresh_timer.stop()
                self._timeline_refresh_timer.start(300)  # 300ms防抖

            text_color_input.textChanged.connect(lambda text, prev=text_color_preview: on_text_color_changed(text, prev))

            text_color_layout.addWidget(text_color_input)
            text_color_layout.addWidget(text_color_btn)
            text_color_layout.addWidget(text_color_preview)

            self.tasks_table.setCellWidget(row, 4, text_color_widget)

            # 删除按钮
            delete_btn = QPushButton("🗑️ 删除")
            # 使用 partial 避免 Lambda 循环引用
            delete_btn.clicked.connect(partial(self.delete_task, row))
            delete_btn.setFixedHeight(36)
            delete_btn.setStyleSheet(StyleManager.button_danger())
            self.tasks_table.setCellWidget(row, 5, delete_btn)

        # 恢复UI更新
        self.tasks_table.setUpdatesEnabled(True)
        
        # 延迟调整列宽，避免阻塞
        QTimer.singleShot(100, lambda: self.tasks_table.resizeColumnsToContents() if hasattr(self, 'tasks_table') else None)

        # 恢复itemChanged信号
        self.tasks_table.blockSignals(False)

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

        color_input = QLineEdit(default_color)
        color_input.setMaximumWidth(80)
        color_input.setFixedHeight(36)

        color_btn = QPushButton("选色")
        color_btn.setFixedSize(50, 36)
        color_btn.setStyleSheet("QPushButton { padding: 8px; font-size: 12px; }")
        # 使用 partial 避免 Lambda 循环引用
        color_btn.clicked.connect(partial(self.choose_color, color_input))

        color_preview = QLabel()
        color_preview.setFixedSize(30, 20)
        color_preview.setStyleSheet(f"background-color: {default_color}; border: 1px solid #ccc;")

        color_input.textChanged.connect(lambda text, prev=color_preview: prev.setStyleSheet(f"background-color: {text}; border: 1px solid #ccc;"))

        color_layout.addWidget(color_input)
        color_layout.addWidget(color_btn)
        color_layout.addWidget(color_preview)

        self.tasks_table.setCellWidget(row, 3, color_widget)

        # 文字颜色选择（默认白色）
        text_color_widget = QWidget()
        text_color_layout = QHBoxLayout(text_color_widget)
        text_color_layout.setContentsMargins(4, 4, 4, 4)

        text_color_input = QLineEdit("#FFFFFF")
        text_color_input.setMaximumWidth(80)
        text_color_input.setFixedHeight(36)

        text_color_btn = QPushButton("选色")
        text_color_btn.setFixedSize(50, 36)
        text_color_btn.setStyleSheet("QPushButton { padding: 8px; font-size: 12px; }")
        # 使用 partial 避免 Lambda 循环引用
        text_color_btn.clicked.connect(partial(self.choose_color, text_color_input))

        text_color_preview = QLabel()
        text_color_preview.setFixedSize(30, 20)
        text_color_preview.setStyleSheet("background-color: #FFFFFF; border: 1px solid #ccc;")

        text_color_input.textChanged.connect(lambda text, prev=text_color_preview: prev.setStyleSheet(f"background-color: {text}; border: 1px solid #ccc;"))

        text_color_layout.addWidget(text_color_input)
        text_color_layout.addWidget(text_color_btn)
        text_color_layout.addWidget(text_color_preview)

        self.tasks_table.setCellWidget(row, 4, text_color_widget)

        # 删除按钮
        delete_btn = QPushButton("🗑️ 删除")
        # 使用 partial 避免 Lambda 循环引用
        delete_btn.clicked.connect(partial(self.delete_task, row))
        delete_btn.setFixedHeight(36)
        delete_btn.setStyleSheet(StyleManager.button_danger())
        self.tasks_table.setCellWidget(row, 5, delete_btn)

        # 刷新时间轴
        self.refresh_timeline_from_table()

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
            QMessageBox.information(self, "提示", "所有任务已清空\n\n记得点击【保存所有设置】按钮来保存更改")

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
            QMessageBox.warning(self, "无法保存", "当前没有任何任务,无法保存为模板!")
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

            # 刷新"我的模板"UI
            self._reload_custom_template_combo()

            # 根据是新建还是更新显示不同的提示
            if is_update:
                success_msg = f"模板已更新:\n{template_filename}\n\n包含 {len(tasks)} 个任务。"
            else:
                success_msg = f"模板已创建:\n{template_filename}\n\n已添加到【我的模板】列表中,包含 {len(tasks)} 个任务。"

            QMessageBox.information(
                self,
                "保存成功",
                success_msg
            )
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"无法保存模板:\n{str(e)}")

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
                f'即将加载自定义模板: {template_name}\n\n包含 {len(template_tasks)} 个任务\n\n当前表格中的任务将被替换,是否继续?',
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
            QMessageBox.critical(self, "错误", f"模板文件格式错误:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载模板失败:\n{str(e)}")


    def _reload_template_buttons(self):
        """重新加载模板按钮（当template_manager延迟初始化完成后调用）"""
        try:
            if not hasattr(self, 'template_manager') or not self.template_manager:
                logging.warning("TemplateManager尚未初始化，延迟500ms后重试")
                # 延迟重试
                QTimer.singleShot(500, self._reload_template_buttons)
                return

            if not hasattr(self, 'template_layout'):
                logging.error("template_layout未找到，无法重新加载模板按钮")
                return

            logging.info("TemplateManager已初始化，重新构建模板按钮")

            # 清空布局中的所有控件
            while self.template_layout.count():
                item = self.template_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # 重新添加"快速加载:"标签
            template_label = QLabel("快速加载:")
            self.template_layout.addWidget(template_label)

            # 重新添加所有模板按钮（只显示预设模板）
            templates = self.template_manager.get_all_templates(include_custom=False)
            for template in templates:
                btn = QPushButton(template['name'])
                # 使用 partial 避免 Lambda 循环引用
                btn.clicked.connect(partial(self.load_template, template['filename']))
                btn.setStyleSheet(f"QPushButton {{ background-color: white; color: {template['button_color']}; border: 2px solid {template['button_color']}; border-radius: 6px; padding: 6px; }}")
                btn.setToolTip(template.get('description', ''))
                self.template_layout.addWidget(btn)

            # 添加弹性空间
            self.template_layout.addStretch()

            logging.info(f"成功加载 {len(templates)} 个模板按钮")

        except Exception as e:
            logging.error(f"重新加载模板按钮失败: {e}")


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
                self.custom_template_combo.addItem("(暂无自定义模板)", None)
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
            QMessageBox.information(self, "提示", "请先创建自定义模板")
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
            QMessageBox.information(self, "提示", "请先创建自定义模板")
            return

        self._delete_custom_template(template)


    def _load_custom_template_by_filename(self, filename):
        """通过文件名加载自定义模板"""
        template_path = self.app_dir / filename

        if not template_path.exists():
            QMessageBox.warning(self, "错误", f"模板文件不存在:\n{filename}")
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
            QMessageBox.critical(self, "错误", f"模板文件格式错误:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载模板失败:\n{str(e)}")


    def _delete_custom_template(self, template):
        """删除自定义模板"""
        try:
            # 确认删除
            reply = QMessageBox.question(
                self,
                '确认删除',
                f'确定要删除模板 "{template["name"]}" 吗?\n\n此操作不可撤销!',
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

            QMessageBox.information(self, "删除成功", f"模板 \"{template['name']}\" 已删除")

        except Exception as e:
            QMessageBox.critical(self, "删除失败", f"无法删除模板:\n{str(e)}")


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
                QMessageBox.warning(self, "警告", "模板管理器未初始化")
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
                QMessageBox.warning(self, "警告", "没有设置被保存")

        except Exception as e:
            logging.error(f"保存模板自动应用设置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")

    def _test_template_matching(self):
        """测试日期匹配功能"""
        try:
            from datetime import datetime
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDateEdit, QPushButton, QTextEdit

            if not hasattr(self, 'template_manager') or not self.template_manager:
                QMessageBox.warning(self, "警告", "模板管理器未初始化")
                return

            # 创建测试对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("测试模板匹配")
            dialog.setMinimumWidth(500)
            dialog.setMinimumHeight(350)

            layout = QVBoxLayout()

            # 说明
            hint_label = QLabel("选择一个日期，查看该日期会匹配到哪个模板：")
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
            test_btn = QPushButton("🔍 执行测试")
            test_btn.setStyleSheet(StyleManager.button_minimal())
            test_btn.clicked.connect(perform_test)
            layout.addWidget(test_btn)

            # 关闭按钮
            close_btn = QPushButton("关闭")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)

            dialog.setLayout(layout)

            # 初始执行一次测试
            perform_test()

            dialog.exec()

        except Exception as e:
            logging.error(f"测试模板匹配失败: {e}")
            QMessageBox.critical(self, "错误", f"测试失败:\n{str(e)}")

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
            QMessageBox.critical(self, "错误", f"模板文件格式错误:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载模板失败:\n{str(e)}")

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
            self.autostart_status_label.setText("(将在开机时自动启动)")
            self.autostart_status_label.setStyleSheet("color: #4CAF50; font-size: 11px;")
        else:
            self.autostart_status_label.setText("(未启用)")
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
        """标记大小改变时更新按钮状态"""
        self.update_marker_size_preset_buttons()

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

    def choose_color(self, input_widget):
        """选择颜色"""
        current_color = QColor(input_widget.text())
        color = QColorDialog.getColor(current_color, self, "选择颜色")

        if color.isValid():
            input_widget.setText(color.name())

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

    def save_all(self):
        """保存所有设置"""
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
                "background_opacity": self.opacity_spin.value(),
                "marker_color": self.marker_color_input.text(),
                "marker_width": self.marker_width_spin.value(),
                "marker_type": self.marker_type_combo.currentText(),
                "marker_image_path": self.marker_image_input.text(),
                "marker_size": self.marker_size_spin.value(),
                "marker_speed": self.marker_speed_spin.value(),
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
                }
            }

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)

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

                    # 验证结束时间必须大于开始时间
                    if self.time_to_minutes(end_time) <= self.time_to_minutes(start_time):
                        QMessageBox.warning(
                            self,
                            "时间错误",
                            f"第 {row + 1} 个任务的结束时间必须大于开始时间!\n\n任务: {name_item.text()}"
                        )
                        return

                    task = {
                        "start": start_time,
                        "end": end_time,
                        "task": name_item.text(),
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

            QMessageBox.information(self, "成功", "配置和任务已保存!\n\n如果 Gaiya 正在运行,更改会自动生效。")
            self.config_saved.emit()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")

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
                self.quota_label.setText("⏳ 正在连接云服务...")
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
                    else:
                        logging.warning(f"配额查询返回错误状态码: {response.status_code}")
                        self.finished.emit(None)
                except Exception as e:
                    logging.warning(f"配额查询失败: {str(e)}")
                    self.finished.emit(None)

        # 创建并启动工作线程
        worker = QuotaCheckWorker(
            self.ai_client.backend_url,
            self.ai_client.user_id,
            self.ai_client.user_tier
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

            if daily_plan_remaining > 0:
                self.quota_label.setText(f"✓ 今日剩余: {daily_plan_remaining} 次规划")
                self.quota_label.setStyleSheet("color: #4CAF50; padding: 5px; font-weight: bold;")
                if hasattr(self, 'generate_btn'):
                    self.generate_btn.setEnabled(True)
            else:
                self.quota_label.setText("⚠️ 今日配额已用完")
                self.quota_label.setStyleSheet("color: #FF9800; padding: 5px; font-weight: bold;")
                if hasattr(self, 'generate_btn'):
                    self.generate_btn.setEnabled(False)
            
            # 配额检查成功，停止定时器（节省资源）
            if hasattr(self, 'ai_status_timer') and self.ai_status_timer:
                if self.ai_status_timer.isActive():
                    self.ai_status_timer.stop()
                    logging.info("AI状态定时器已停止（配额检查成功）")
        else:
            # 配额检查失败，可能是云服务冷启动或网络问题
            self.quota_label.setText("⚠️ 无法连接云服务（请点击刷新重试）")
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
        if not self._check_login_and_guide("AI智能规划"):
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
        self.generate_btn.setText("⏳ AI正在生成...")

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
                self.load_tasks_to_table()

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
            self.generate_btn.setText("✨ 智能生成任务")

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
            self.generate_btn.setText("✨ 智能生成任务")

    def create_about_tab(self):
        """创建关于标签页"""
        from version import __version__, __app_name_zh__, __slogan__, APP_METADATA
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
            logo_label.setText(__app_name_zh__)
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
        app_name_label = QLabel("GaiYa")
        app_name_label.setStyleSheet("""
            QLabel {
                font-size: 36px;
                font-weight: bold;
                color: #FFFFFF;
                padding: 10px;
            }
        """)
        app_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(app_name_label)

        # Slogan
        slogan_label = QLabel(__slogan__)
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
        version_label = QLabel(f"版本 v{__version__}")
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
        self.check_update_btn = QPushButton("检查更新")
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
        feedback_link = QLabel('<a href="#" style="color: #2196F3; text-decoration: none;">直接向创始人反馈问题</a>')
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
        copyright_label = QLabel(f"© 2025 {APP_METADATA['author']}")
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

    def _check_for_updates(self):
        """检查更新"""
        from version import __version__, APP_METADATA
        import requests
        from PySide6.QtWidgets import QMessageBox

        # 更新按钮状态
        self.check_update_btn.setEnabled(False)
        self.check_update_btn.setText("检查中...")

        try:
            # 调用GitHub API获取最新版本
            repo = APP_METADATA['repository'].replace('https://github.com/', '')
            api_url = f"https://api.github.com/repos/{repo}/releases/latest"

            response = requests.get(api_url, timeout=10)
            response.raise_for_status()

            latest_release = response.json()
            latest_version = latest_release['tag_name'].lstrip('v')
            current_version = __version__

            # 比较版本号
            if self._compare_versions(latest_version, current_version) > 0:
                # 有新版本
                self.check_update_btn.setText(f"v{latest_version} 可更新")
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
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setWindowTitle("发现新版本")
                msg.setText(f"发现新版本 v{latest_version}")
                msg.setInformativeText(f"当前版本: v{current_version}\n\n{latest_release.get('body', '无更新说明')}")
                msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                download_btn = msg.addButton("前往下载", QMessageBox.ButtonRole.AcceptRole)
                msg.exec()

                if msg.clickedButton() == download_btn:
                    # 打开下载页面
                    from PySide6.QtGui import QDesktopServices
                    from PySide6.QtCore import QUrl
                    QDesktopServices.openUrl(QUrl(latest_release['html_url']))
            else:
                # 已是最新版本
                QMessageBox.information(
                    self,
                    "已是最新版本",
                    f"当前版本 v{current_version} 已是最新版本！"
                )
                self.check_update_btn.setText("检查更新")

        except requests.exceptions.Timeout:
            QMessageBox.warning(self, "检查更新失败", "网络请求超时，请检查网络连接")
            self.check_update_btn.setText("检查更新")
        except requests.exceptions.HTTPError as e:
            # 特殊处理 404：表示仓库还没有发布任何 Release
            if e.response.status_code == 404:
                QMessageBox.information(
                    self,
                    "暂无发布版本",
                    f"当前版本: v{__version__}\n\n项目仓库暂未发布正式版本，敬请期待！\n\n您可以访问 GitHub 仓库查看最新开发进展：\n{APP_METADATA['repository']}"
                )
            else:
                QMessageBox.warning(self, "检查更新失败", f"无法连接到更新服务器\n\n{str(e)}")
            self.check_update_btn.setText("检查更新")
        except requests.exceptions.RequestException as e:
            QMessageBox.warning(self, "检查更新失败", f"无法连接到更新服务器\n\n{str(e)}")
            self.check_update_btn.setText("检查更新")
        except Exception as e:
            import logging
            logging.error(f"检查更新失败: {e}")
            QMessageBox.warning(self, "检查更新失败", f"发生未知错误\n\n{str(e)}")
            self.check_update_btn.setText("检查更新")
        finally:
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
        dialog.setWindowTitle("添加创始人微信")
        dialog.setFixedSize(550, 750)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        title_label = QLabel("扫描二维码，直接反馈问题")
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
                error_label = QLabel("无法加载二维码图片")
                error_label.setStyleSheet("color: red; padding: 20px;")
                error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(error_label)
        else:
            error_label = QLabel(f"二维码图片不存在\n路径: {qrcode_path}")
            error_label.setStyleSheet("color: red; padding: 20px;")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(error_label)

        # 提示文字
        hint_label = QLabel("扫一扫上面的二维码图案，加我为朋友。")
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

    def closeEvent(self, event):
        """窗口关闭事件，清理所有资源"""
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
        print(f"[警告] 应用浅色主题失败: {e}，使用默认样式")
        app.setStyle("Fusion")

    window = ConfigManager()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
