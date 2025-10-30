# -*- coding: utf-8 -*-
"""
PyDayBar 可视化配置界面
提供图形化界面来管理配置和任务
"""

import json
import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QLineEdit, QSpinBox, QPushButton, QColorDialog,
    QComboBox, QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QTimeEdit, QGroupBox, QFormLayout, QFileDialog
)
from PySide6.QtCore import Qt, QTime, Signal
from PySide6.QtGui import QColor, QIcon


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
        # 获取应用程序目录(支持打包后的 exe)
        if getattr(sys, 'frozen', False):
            self.app_dir = Path(sys.executable).parent
        else:
            self.app_dir = Path(__file__).parent

        self.config_file = self.app_dir / 'config.json'
        self.tasks_file = self.app_dir / 'tasks.json'
        self.config = self.load_config()
        self.tasks = self.load_tasks()

        # 如果任务为空,默认加载24小时模板
        if not self.tasks:
            self.load_default_template()

        self.init_ui()

    def get_resource_path(self, relative_path):
        """获取资源文件路径(支持打包后的 exe)"""
        if getattr(sys, 'frozen', False):
            # 打包后的 exe,资源文件在临时目录
            base_path = Path(sys._MEIPASS)
        else:
            # 开发环境,资源文件在脚本目录
            base_path = Path(__file__).parent
        return base_path / relative_path

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle('PyDayBar 配置管理器')
        self.setMinimumSize(800, 600)

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        layout = QVBoxLayout(central_widget)

        # 创建标签页
        tabs = QTabWidget()
        tabs.addTab(self.create_config_tab(), "外观配置")
        tabs.addTab(self.create_tasks_tab(), "任务管理")
        tabs.addTab(self.create_notification_tab(), "🔔 通知设置")

        layout.addWidget(tabs)

        # 底部按钮
        button_layout = QHBoxLayout()

        save_btn = QPushButton("保存所有设置")
        save_btn.clicked.connect(self.save_all)
        save_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px; font-weight: bold; }")

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.close)

        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def create_config_tab(self):
        """创建外观配置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 基本设置组
        basic_group = QGroupBox("基本设置")
        basic_layout = QFormLayout()

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
            btn.clicked.connect(lambda checked, h=height: self.set_height_preset(h))
            height_preset_layout.addWidget(btn)
            self.height_preset_buttons.append((btn, height))

        height_layout.addWidget(self.height_preset_group)

        # 自定义高度输入
        custom_label = QLabel("自定义:")
        height_layout.addWidget(custom_label)

        self.height_spin = QSpinBox()
        self.height_spin.setRange(8, 100)
        self.height_spin.setValue(self.config.get('bar_height', 20))
        self.height_spin.setSuffix(" px")
        self.height_spin.setMaximumWidth(80)
        self.height_spin.valueChanged.connect(self.on_height_value_changed)
        height_layout.addWidget(self.height_spin)

        height_layout.addStretch()

        basic_layout.addRow("进度条高度:", height_container)

        # 初始化时更新按钮状态
        self.update_height_preset_buttons()

        # 位置选择
        self.position_combo = QComboBox()
        self.position_combo.addItems(["bottom", "top"])
        self.position_combo.setCurrentText(self.config.get('position', 'bottom'))
        basic_layout.addRow("屏幕位置:", self.position_combo)

        # 显示器索引
        self.screen_spin = QSpinBox()
        self.screen_spin.setRange(0, 10)
        self.screen_spin.setValue(self.config.get('screen_index', 0))
        basic_layout.addRow("显示器索引:", self.screen_spin)

        # 更新间隔
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(100, 60000)
        self.interval_spin.setValue(self.config.get('update_interval', 1000))
        self.interval_spin.setSuffix(" 毫秒")
        basic_layout.addRow("更新间隔:", self.interval_spin)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # 颜色设置组
        color_group = QGroupBox("颜色设置")
        color_layout = QFormLayout()

        # 背景颜色
        bg_color_layout = QHBoxLayout()
        self.bg_color_input = QLineEdit(self.config.get('background_color', '#505050'))
        self.bg_color_btn = QPushButton("选择颜色")
        self.bg_color_btn.clicked.connect(lambda: self.choose_color(self.bg_color_input))
        self.bg_color_preview = QLabel()
        self.update_color_preview(self.bg_color_input, self.bg_color_preview)
        bg_color_layout.addWidget(self.bg_color_input)
        bg_color_layout.addWidget(self.bg_color_btn)
        bg_color_layout.addWidget(self.bg_color_preview)
        color_layout.addRow("背景颜色:", bg_color_layout)

        # 背景透明度
        self.opacity_spin = QSpinBox()
        self.opacity_spin.setRange(0, 255)
        self.opacity_spin.setValue(self.config.get('background_opacity', 180))
        color_layout.addRow("背景透明度:", self.opacity_spin)

        # 时间标记颜色
        marker_color_layout = QHBoxLayout()
        self.marker_color_input = QLineEdit(self.config.get('marker_color', '#FF0000'))
        self.marker_color_btn = QPushButton("选择颜色")
        self.marker_color_btn.clicked.connect(lambda: self.choose_color(self.marker_color_input))
        self.marker_color_preview = QLabel()
        self.update_color_preview(self.marker_color_input, self.marker_color_preview)
        marker_color_layout.addWidget(self.marker_color_input)
        marker_color_layout.addWidget(self.marker_color_btn)
        marker_color_layout.addWidget(self.marker_color_preview)
        color_layout.addRow("时间标记颜色:", marker_color_layout)

        # 时间标记宽度
        self.marker_width_spin = QSpinBox()
        self.marker_width_spin.setRange(1, 10)
        self.marker_width_spin.setValue(self.config.get('marker_width', 2))
        self.marker_width_spin.setSuffix(" 像素")
        color_layout.addRow("时间标记宽度:", self.marker_width_spin)

        # 时间标记类型
        marker_type_layout = QHBoxLayout()
        self.marker_type_combo = QComboBox()
        self.marker_type_combo.addItems(["line", "image", "gif"])
        self.marker_type_combo.setCurrentText(self.config.get('marker_type', 'line'))
        self.marker_type_combo.currentTextChanged.connect(self.on_marker_type_changed)
        marker_type_layout.addWidget(self.marker_type_combo)

        marker_type_hint = QLabel("(line=线条, image=图片, gif=动画)")
        marker_type_hint.setStyleSheet("color: #666; font-size: 9pt;")
        marker_type_layout.addWidget(marker_type_hint)
        marker_type_layout.addStretch()

        color_layout.addRow("时间标记类型:", marker_type_layout)

        # 标记图片路径
        marker_image_layout = QHBoxLayout()
        self.marker_image_input = QLineEdit(self.config.get('marker_image_path', ''))
        self.marker_image_input.setPlaceholderText("选择图片文件 (JPG/PNG/GIF/WebP)")
        marker_image_layout.addWidget(self.marker_image_input)

        marker_image_btn = QPushButton("📁 浏览")
        marker_image_btn.clicked.connect(self.choose_marker_image)
        marker_image_btn.setMaximumWidth(80)
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
            btn.clicked.connect(lambda checked, s=size: self.set_marker_size_preset(s))
            marker_size_preset_layout.addWidget(btn)
            self.marker_size_preset_buttons.append((btn, size))

        marker_size_layout.addWidget(self.marker_size_preset_group)

        # 自定义大小输入
        custom_size_label = QLabel("自定义:")
        marker_size_layout.addWidget(custom_size_label)

        self.marker_size_spin = QSpinBox()
        self.marker_size_spin.setRange(20, 200)
        self.marker_size_spin.setValue(self.config.get('marker_size', 50))
        self.marker_size_spin.setSuffix(" px")
        self.marker_size_spin.setMaximumWidth(80)
        self.marker_size_spin.valueChanged.connect(self.on_marker_size_value_changed)
        marker_size_layout.addWidget(self.marker_size_spin)

        marker_size_layout.addStretch()

        color_layout.addRow("标记图片大小:", marker_size_container)

        # 初始化时更新按钮状态
        self.update_marker_size_preset_buttons()

        # 标记图片 Y 轴偏移
        self.marker_y_offset_spin = QSpinBox()
        self.marker_y_offset_spin.setRange(-100, 100)
        self.marker_y_offset_spin.setValue(self.config.get('marker_y_offset', 0))
        self.marker_y_offset_spin.setSuffix(" px")
        self.marker_y_offset_spin.setMaximumWidth(100)
        offset_hint = QLabel("(正值向上,负值向下)")
        offset_hint.setStyleSheet("color: #666; font-size: 9pt;")
        offset_layout = QHBoxLayout()
        offset_layout.addWidget(self.marker_y_offset_spin)
        offset_layout.addWidget(offset_hint)
        offset_layout.addStretch()
        color_layout.addRow("标记图片 Y 偏移:", offset_layout)

        color_group.setLayout(color_layout)
        layout.addWidget(color_group)

        # 初始化时根据类型显示/隐藏相关控件
        self.on_marker_type_changed(self.marker_type_combo.currentText())

        # 效果设置组
        effect_group = QGroupBox("视觉效果")
        effect_layout = QFormLayout()

        # 启用阴影
        self.shadow_check = QCheckBox("启用阴影效果")
        self.shadow_check.setChecked(self.config.get('enable_shadow', True))
        effect_layout.addRow(self.shadow_check)

        # 圆角半径
        self.radius_spin = QSpinBox()
        self.radius_spin.setRange(0, 20)
        self.radius_spin.setValue(self.config.get('corner_radius', 0))
        self.radius_spin.setSuffix(" 像素")
        effect_layout.addRow("圆角半径:", self.radius_spin)

        effect_group.setLayout(effect_layout)
        layout.addWidget(effect_group)

        layout.addStretch()
        return widget

    def create_tasks_tab(self):
        """创建任务管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 顶部信息和模板加载区域
        top_layout = QVBoxLayout()

        # 说明标签
        info_label = QLabel("双击表格单元格可以编辑任务内容")
        info_label.setStyleSheet("color: #666; font-style: italic;")
        top_layout.addWidget(info_label)

        # 模板加载区域
        template_group = QGroupBox("📋 预设模板")
        template_main_layout = QVBoxLayout()

        # 第一行模板
        template_row1 = QHBoxLayout()
        template_label = QLabel("快速加载预设任务模板:")
        template_row1.addWidget(template_label)

        # 24小时模板按钮
        template_24h_btn = QPushButton("24小时完整作息")
        template_24h_btn.clicked.connect(lambda: self.load_template("tasks_template_24h.json"))
        template_24h_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 6px; }")
        template_row1.addWidget(template_24h_btn)

        # 工作日模板按钮
        template_work_btn = QPushButton("工作日作息")
        template_work_btn.clicked.connect(lambda: self.load_template("tasks_template_workday.json"))
        template_work_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 6px; }")
        template_row1.addWidget(template_work_btn)

        # 学生模板按钮
        template_student_btn = QPushButton("学生作息")
        template_student_btn.clicked.connect(lambda: self.load_template("tasks_template_student.json"))
        template_student_btn.setStyleSheet("QPushButton { background-color: #9C27B0; color: white; padding: 6px; }")
        template_row1.addWidget(template_student_btn)

        # 自由职业者模板
        template_freelancer_btn = QPushButton("自由职业")
        template_freelancer_btn.clicked.connect(lambda: self.load_template("tasks_template_freelancer.json"))
        template_freelancer_btn.setStyleSheet("QPushButton { background-color: #00BCD4; color: white; padding: 6px; }")
        template_row1.addWidget(template_freelancer_btn)

        template_row1.addStretch()
        template_main_layout.addLayout(template_row1)

        # 第二行模板
        template_row2 = QHBoxLayout()
        template_row2.addWidget(QLabel("更多场景:"))

        # 夜班作息模板
        template_night_btn = QPushButton("夜班作息")
        template_night_btn.clicked.connect(lambda: self.load_template("tasks_template_night_shift.json"))
        template_night_btn.setStyleSheet("QPushButton { background-color: #3F51B5; color: white; padding: 6px; }")
        template_row2.addWidget(template_night_btn)

        # 内容创作者模板
        template_creator_btn = QPushButton("内容创作者")
        template_creator_btn.clicked.connect(lambda: self.load_template("tasks_template_creator.json"))
        template_creator_btn.setStyleSheet("QPushButton { background-color: #E91E63; color: white; padding: 6px; }")
        template_row2.addWidget(template_creator_btn)

        # 健身达人模板
        template_fitness_btn = QPushButton("健身达人")
        template_fitness_btn.clicked.connect(lambda: self.load_template("tasks_template_fitness.json"))
        template_fitness_btn.setStyleSheet("QPushButton { background-color: #FF5722; color: white; padding: 6px; }")
        template_row2.addWidget(template_fitness_btn)

        # 创业者模板
        template_entrepreneur_btn = QPushButton("创业者")
        template_entrepreneur_btn.clicked.connect(lambda: self.load_template("tasks_template_entrepreneur.json"))
        template_entrepreneur_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; padding: 6px; }")
        template_row2.addWidget(template_entrepreneur_btn)

        template_row2.addStretch()
        template_main_layout.addLayout(template_row2)

        template_group.setLayout(template_main_layout)
        top_layout.addWidget(template_group)

        layout.addLayout(top_layout)

        # 任务表格
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(5)
        self.tasks_table.setHorizontalHeaderLabels(["开始时间", "结束时间", "任务名称", "颜色", "操作"])
        self.tasks_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.load_tasks_to_table()

        layout.addWidget(self.tasks_table)

        # 按钮组
        button_layout = QHBoxLayout()

        add_btn = QPushButton("➕ 添加任务")
        add_btn.clicked.connect(self.add_task)
        add_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 8px; }")

        save_template_btn = QPushButton("💾 保存为模板")
        save_template_btn.clicked.connect(self.save_as_template)
        save_template_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; padding: 8px; }")

        load_custom_btn = QPushButton("📂 加载自定义模板")
        load_custom_btn.clicked.connect(self.load_custom_template)
        load_custom_btn.setStyleSheet("QPushButton { background-color: #9C27B0; color: white; padding: 8px; }")

        clear_btn = QPushButton("🗑️ 清空所有任务")
        clear_btn.clicked.connect(self.clear_all_tasks)
        clear_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; padding: 8px; }")

        button_layout.addWidget(add_btn)
        button_layout.addWidget(save_template_btn)
        button_layout.addWidget(load_custom_btn)
        button_layout.addWidget(clear_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        return widget

    def create_notification_tab(self):
        """创建通知设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 说明标签
        info_label = QLabel("配置任务提醒通知,让您不会错过任何重要时刻")
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        layout.addWidget(info_label)

        # 基础设置组
        basic_group = QGroupBox("基础设置")
        basic_layout = QFormLayout()

        # 启用通知
        self.notify_enabled_check = QCheckBox("启用任务提醒通知")
        notification_config = self.config.get('notification', {})
        self.notify_enabled_check.setChecked(notification_config.get('enabled', True))
        self.notify_enabled_check.setStyleSheet("font-weight: bold;")
        basic_layout.addRow(self.notify_enabled_check)

        # 启用声音
        self.notify_sound_check = QCheckBox("播放提示音")
        self.notify_sound_check.setChecked(notification_config.get('sound_enabled', True))
        basic_layout.addRow(self.notify_sound_check)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # 提醒时机设置组
        timing_group = QGroupBox("提醒时机")
        timing_layout = QVBoxLayout()

        # 任务开始前提醒
        before_start_group = QGroupBox("任务开始前提醒")
        before_start_layout = QVBoxLayout()

        before_start_hint = QLabel("选择在任务开始前多久提醒(可多选):")
        before_start_hint.setStyleSheet("color: #666; font-size: 9pt;")
        before_start_layout.addWidget(before_start_hint)

        before_start_minutes = notification_config.get('before_start_minutes', [10, 5])

        # 提前提醒选项
        before_start_checkboxes_layout = QHBoxLayout()
        self.notify_before_start_checks = {}

        for minutes in [30, 15, 10, 5]:
            checkbox = QCheckBox(f"提前 {minutes} 分钟")
            checkbox.setChecked(minutes in before_start_minutes)
            self.notify_before_start_checks[minutes] = checkbox
            before_start_checkboxes_layout.addWidget(checkbox)

        before_start_checkboxes_layout.addStretch()
        before_start_layout.addLayout(before_start_checkboxes_layout)

        before_start_group.setLayout(before_start_layout)
        timing_layout.addWidget(before_start_group)

        # 任务开始时提醒
        self.notify_on_start_check = QCheckBox("任务开始时提醒")
        self.notify_on_start_check.setChecked(notification_config.get('on_start', True))
        self.notify_on_start_check.setStyleSheet("padding: 5px;")
        timing_layout.addWidget(self.notify_on_start_check)

        # 任务结束前提醒
        before_end_group = QGroupBox("任务结束前提醒")
        before_end_layout = QVBoxLayout()

        before_end_hint = QLabel("选择在任务结束前多久提醒(可多选):")
        before_end_hint.setStyleSheet("color: #666; font-size: 9pt;")
        before_end_layout.addWidget(before_end_hint)

        before_end_minutes = notification_config.get('before_end_minutes', [5])

        before_end_checkboxes_layout = QHBoxLayout()
        self.notify_before_end_checks = {}

        for minutes in [10, 5, 3]:
            checkbox = QCheckBox(f"提前 {minutes} 分钟")
            checkbox.setChecked(minutes in before_end_minutes)
            self.notify_before_end_checks[minutes] = checkbox
            before_end_checkboxes_layout.addWidget(checkbox)

        before_end_checkboxes_layout.addStretch()
        before_end_layout.addLayout(before_end_checkboxes_layout)

        before_end_group.setLayout(before_end_layout)
        timing_layout.addWidget(before_end_group)

        # 任务结束时提醒
        self.notify_on_end_check = QCheckBox("任务结束时提醒")
        self.notify_on_end_check.setChecked(notification_config.get('on_end', False))
        self.notify_on_end_check.setStyleSheet("padding: 5px;")
        timing_layout.addWidget(self.notify_on_end_check)

        timing_group.setLayout(timing_layout)
        layout.addWidget(timing_group)

        # 免打扰时段设置组
        quiet_group = QGroupBox("免打扰时段")
        quiet_layout = QFormLayout()

        quiet_hours = notification_config.get('quiet_hours', {})

        # 启用免打扰
        self.quiet_enabled_check = QCheckBox("启用免打扰时段")
        self.quiet_enabled_check.setChecked(quiet_hours.get('enabled', False))
        quiet_layout.addRow(self.quiet_enabled_check)

        # 免打扰开始时间
        quiet_start_layout = QHBoxLayout()
        self.quiet_start_time = QTimeEdit()
        self.quiet_start_time.setDisplayFormat("HH:mm")
        start_time_str = quiet_hours.get('start', '22:00')
        self.quiet_start_time.setTime(QTime.fromString(start_time_str, "HH:mm"))
        quiet_start_layout.addWidget(self.quiet_start_time)
        quiet_start_hint = QLabel("(在此时间后不发送通知)")
        quiet_start_hint.setStyleSheet("color: #666; font-size: 9pt;")
        quiet_start_layout.addWidget(quiet_start_hint)
        quiet_start_layout.addStretch()
        quiet_layout.addRow("开始时间:", quiet_start_layout)

        # 免打扰结束时间
        quiet_end_layout = QHBoxLayout()
        self.quiet_end_time = QTimeEdit()
        self.quiet_end_time.setDisplayFormat("HH:mm")
        end_time_str = quiet_hours.get('end', '08:00')
        self.quiet_end_time.setTime(QTime.fromString(end_time_str, "HH:mm"))
        quiet_end_layout.addWidget(self.quiet_end_time)
        quiet_end_hint = QLabel("(在此时间前不发送通知)")
        quiet_end_hint.setStyleSheet("color: #666; font-size: 9pt;")
        quiet_end_layout.addWidget(quiet_end_hint)
        quiet_end_layout.addStretch()
        quiet_layout.addRow("结束时间:", quiet_end_layout)

        quiet_example = QLabel("示例: 22:00 - 08:00 表示晚上10点到早上8点不打扰")
        quiet_example.setStyleSheet("color: #999; font-size: 8pt; font-style: italic;")
        quiet_layout.addRow(quiet_example)

        quiet_group.setLayout(quiet_layout)
        layout.addWidget(quiet_group)

        layout.addStretch()
        return widget

    def load_tasks_to_table(self):
        """加载任务到表格"""
        self.tasks_table.setRowCount(len(self.tasks))

        for row, task in enumerate(self.tasks):
            # 开始时间
            start_time = QTimeEdit()
            start_time.setDisplayFormat("HH:mm")
            # 特殊处理 24:00
            if task['start'] == "24:00":
                start_time.setTime(QTime(0, 0))  # 显示为 00:00
            else:
                start_time.setTime(QTime.fromString(task['start'], "HH:mm"))
            self.tasks_table.setCellWidget(row, 0, start_time)

            # 结束时间
            end_time = QTimeEdit()
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
            color_input.setMaximumWidth(100)

            color_btn = QPushButton("选色")
            color_btn.setMaximumWidth(50)
            color_btn.clicked.connect(lambda checked, inp=color_input: self.choose_color(inp))

            color_preview = QLabel()
            color_preview.setFixedSize(30, 20)
            color_preview.setStyleSheet(f"background-color: {task['color']}; border: 1px solid #ccc;")

            color_input.textChanged.connect(lambda text, prev=color_preview: prev.setStyleSheet(f"background-color: {text}; border: 1px solid #ccc;"))

            color_layout.addWidget(color_input)
            color_layout.addWidget(color_btn)
            color_layout.addWidget(color_preview)

            self.tasks_table.setCellWidget(row, 3, color_widget)

            # 删除按钮
            delete_btn = QPushButton("🗑️ 删除")
            delete_btn.clicked.connect(lambda checked, r=row: self.delete_task(r))
            delete_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
            self.tasks_table.setCellWidget(row, 4, delete_btn)

        self.tasks_table.resizeColumnsToContents()

    def add_task(self):
        """添加新任务,自动接续上一个任务的结束时间"""
        row = self.tasks_table.rowCount()
        self.tasks_table.insertRow(row)

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
        start_time.setDisplayFormat("HH:mm")
        start_time.setTime(new_start_time)
        self.tasks_table.setCellWidget(row, 0, start_time)

        # 设置结束时间
        end_time = QTimeEdit()
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
        color_input.setMaximumWidth(100)

        color_btn = QPushButton("选色")
        color_btn.setMaximumWidth(50)
        color_btn.clicked.connect(lambda checked, inp=color_input: self.choose_color(inp))

        color_preview = QLabel()
        color_preview.setFixedSize(30, 20)
        color_preview.setStyleSheet(f"background-color: {default_color}; border: 1px solid #ccc;")

        color_input.textChanged.connect(lambda text, prev=color_preview: prev.setStyleSheet(f"background-color: {text}; border: 1px solid #ccc;"))

        color_layout.addWidget(color_input)
        color_layout.addWidget(color_btn)
        color_layout.addWidget(color_preview)

        self.tasks_table.setCellWidget(row, 3, color_widget)

        # 删除按钮
        delete_btn = QPushButton("🗑️ 删除")
        delete_btn.clicked.connect(lambda checked, r=row: self.delete_task(r))
        delete_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
        self.tasks_table.setCellWidget(row, 4, delete_btn)

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
                delete_btn = self.tasks_table.cellWidget(r, 4)
                if delete_btn:
                    delete_btn.clicked.disconnect()
                    delete_btn.clicked.connect(lambda checked, row=r: self.delete_task(row))

    def clear_all_tasks(self):
        """清空所有任务"""
        reply = QMessageBox.question(
            self, '确认清空',
            '确定要清空所有任务吗?\n\n这将删除表格中的所有任务(不会立即保存,需要点击【保存所有设置】)',
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.tasks_table.setRowCount(0)
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
        from PySide6.QtWidgets import QInputDialog, QFileDialog

        if self.tasks_table.rowCount() == 0:
            QMessageBox.warning(self, "无法保存", "当前没有任何任务,无法保存为模板!")
            return

        # 询问模板名称
        template_name, ok = QInputDialog.getText(
            self,
            "保存模板",
            "请输入模板名称(不需要输入.json后缀):",
            text="我的自定义模板"
        )

        if not ok or not template_name.strip():
            return

        template_name = template_name.strip()

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
            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, indent=4, ensure_ascii=False)

            QMessageBox.information(
                self,
                "保存成功",
                f"模板已保存:\n{template_filename}\n\n可以通过【加载自定义模板】按钮加载此模板。"
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

                QMessageBox.information(
                    self,
                    "加载成功",
                    f"已加载 {len(template_tasks)} 个任务\n\n记得点击【保存所有设置】按钮来应用更改"
                )

        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "错误", f"模板文件格式错误:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载模板失败:\n{str(e)}")

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
            except:
                pass
        return {}

    def load_tasks(self):
        """加载任务"""
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
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
        """将 HH:mm 转换为分钟数

        特殊处理: 24:00 表示一天结束(午夜),返回 1440 分钟
        """
        try:
            hours, minutes = map(int, time_str.split(':'))
            # 特殊处理 24:00
            if hours == 24 and minutes == 0:
                return 1440  # 24 * 60
            return hours * 60 + minutes
        except:
            return 0

    def save_all(self):
        """保存所有设置"""
        try:
            # 收集通知配置
            # 收集开始前提醒时间
            before_start_minutes = [
                minutes for minutes, checkbox in self.notify_before_start_checks.items()
                if checkbox.isChecked()
            ]

            # 收集结束前提醒时间
            before_end_minutes = [
                minutes for minutes, checkbox in self.notify_before_end_checks.items()
                if checkbox.isChecked()
            ]

            # 保存配置
            config = {
                "bar_height": self.height_spin.value(),
                "position": self.position_combo.currentText(),
                "background_color": self.bg_color_input.text(),
                "background_opacity": self.opacity_spin.value(),
                "marker_color": self.marker_color_input.text(),
                "marker_width": self.marker_width_spin.value(),
                "marker_type": self.marker_type_combo.currentText(),
                "marker_image_path": self.marker_image_input.text(),
                "marker_size": self.marker_size_spin.value(),
                "marker_y_offset": self.marker_y_offset_spin.value(),
                "screen_index": self.screen_spin.value(),
                "update_interval": self.interval_spin.value(),
                "enable_shadow": self.shadow_check.isChecked(),
                "corner_radius": self.radius_spin.value(),
                "notification": {
                    "enabled": self.notify_enabled_check.isChecked(),
                    "before_start_minutes": before_start_minutes,
                    "on_start": self.notify_on_start_check.isChecked(),
                    "before_end_minutes": before_end_minutes,
                    "on_end": self.notify_on_end_check.isChecked(),
                    "sound_enabled": self.notify_sound_check.isChecked(),
                    "sound_file": "",
                    "quiet_hours": {
                        "enabled": self.quiet_enabled_check.isChecked(),
                        "start": self.quiet_start_time.time().toString("HH:mm"),
                        "end": self.quiet_end_time.time().toString("HH:mm")
                    }
                }
            }

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)

            # 保存任务
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
                        "color": color_input.text() if color_input else "#4CAF50"
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

            QMessageBox.information(self, "成功", "配置和任务已保存!\n\n如果 PyDayBar 正在运行,更改会自动生效。")
            self.config_saved.emit()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")


def main():
    """主程序入口"""
    app = QApplication(sys.argv)

    # 设置应用样式
    app.setStyle("Fusion")

    window = ConfigManager()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
