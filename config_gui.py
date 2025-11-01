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
from PySide6.QtCore import Qt, QTime, Signal, QThread, QTimer
from PySide6.QtGui import QColor, QIcon
from timeline_editor import TimelineEditor
from ai_client import PyDayBarAIClient
from backend_manager import BackendManager
import requests
from theme_manager import ThemeManager
from theme_ai_helper import ThemeAIHelper
import logging


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
        
        # 延迟加载配置和任务，先让窗口显示
        self.config = {}
        self.tasks = []
        
        # 延迟初始化AI相关组件(避免阻塞UI显示)
        self.ai_client = None
        self.ai_worker = None
        self.backend_manager = None
        self.theme_ai_helper = None

        # 延迟初始化主题管理器(避免同步文件I/O阻塞UI)
        self.theme_manager = None

        # 先初始化UI,让窗口快速显示
        self.init_ui()
        
        # UI显示后再异步加载配置和任务
        QTimer.singleShot(50, self._load_config_and_tasks)

        # UI显示后再异步初始化主题管理器和AI组件
        QTimer.singleShot(100, self._init_theme_manager)
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

    def _init_ai_components(self):
        """延迟初始化AI相关组件(在后台运行,不阻塞UI)"""
        try:
            # 初始化AI客户端（默认使用代理服务器）
            self.ai_client = PyDayBarAIClient()
            
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
            # 如果根logger没有文件处理器，添加一个（指向pydaybar.log）
            if not any(isinstance(h, logging.FileHandler) for h in root_logger.handlers):
                # 获取应用目录（支持打包后的环境）
                if getattr(sys, 'frozen', False):
                    app_dir = Path(sys.executable).parent
                else:
                    app_dir = Path(__file__).parent
                log_file = app_dir / "pydaybar.log"
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setLevel(logging.INFO)
                file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
                root_logger.addHandler(file_handler)
            
            # 创建BackendManager实例（但不启动本地服务，因为使用代理服务器）
            self.backend_manager = BackendManager(root_logger)
            # 注意：不调用 ensure_backend_running_async()，因为使用代理服务器

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
                    response = requests.get(f"{self.backend_url}/health", timeout=2)
                    self.finished.emit(response.status_code == 200)
                except Exception:
                    self.finished.emit(False)
        
        # 创建并启动工作线程
        worker = HealthCheckWorker(self.ai_client.backend_url)
        worker.finished.connect(self._on_health_check_finished)
        worker.start()
        
        # 保存worker引用，避免被垃圾回收
        if not hasattr(self, '_health_check_workers'):
            self._health_check_workers = []
        self._health_check_workers.append(worker)
        
        # 清理旧的worker引用（保留最近3个）
        if len(self._health_check_workers) > 3:
            self._health_check_workers.pop(0)
    
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

        # 创建标签页(使用懒加载,只在切换到标签页时才创建内容)
        tabs = QTabWidget()
        
        # 立即创建外观配置和任务管理标签页(基础功能)
        tabs.addTab(self.create_config_tab(), "外观配置")
        tabs.addTab(self.create_tasks_tab(), "任务管理")
        
        # 延迟创建主题设置和通知设置标签页(避免初始化时阻塞)
        self.theme_tab_widget = None
        self.notification_tab_widget = None
        tabs.addTab(QWidget(), "🎨 主题设置")  # 占位widget
        tabs.addTab(QWidget(), "🔔 通知设置")  # 占位widget
        
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
        save_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px; font-weight: bold; }")

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.close)

        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def on_tab_changed(self, index):
        """标签页切换时的处理(实现懒加载)"""
        if index == 2:  # 主题设置标签页
            if self.theme_tab_widget is None:
                # 检查主题管理器是否已初始化
                if self.theme_manager is None:
                    # 如果还未初始化,先初始化
                    self._init_theme_manager()
                    # 等待一小段时间让初始化完成
                    QTimer.singleShot(100, lambda: self._load_theme_tab())
                else:
                    self._load_theme_tab()
        elif index == 3:  # 通知设置标签页
            if self.notification_tab_widget is None:
                self._load_notification_tab()
    
    def _load_theme_tab(self):
        """加载主题设置标签页"""
        if self.theme_tab_widget is not None:
            return  # 已经加载过了
        
        try:
            self.theme_tab_widget = self.create_theme_tab()
            self.tabs.setTabEnabled(2, True)  # 确保标签页可用
            # 替换占位widget
            self.tabs.removeTab(2)
            self.tabs.insertTab(2, self.theme_tab_widget, "🎨 主题设置")
            self.tabs.setCurrentIndex(2)  # 切换到主题设置标签页
        except Exception as e:
            logging.error(f"加载主题设置标签页失败: {e}")
            # 显示错误提示
            from PySide6.QtWidgets import QLabel
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_label = QLabel(f"加载主题设置失败: {e}")
            error_label.setStyleSheet("color: red; padding: 20px;")
            error_layout.addWidget(error_label)
            self.theme_tab_widget = error_widget
            self.tabs.removeTab(2)
            self.tabs.insertTab(2, self.theme_tab_widget, "🎨 主题设置")
    
    def _load_notification_tab(self):
        """加载通知设置标签页"""
        if self.notification_tab_widget is not None:
            return  # 已经加载过了
        
        try:
            self.notification_tab_widget = self.create_notification_tab()
            self.tabs.setTabEnabled(3, True)  # 确保标签页可用
            # 替换占位widget
            self.tabs.removeTab(3)
            self.tabs.insertTab(3, self.notification_tab_widget, "🔔 通知设置")
            self.tabs.setCurrentIndex(3)  # 切换到通知设置标签页
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
            self.tabs.removeTab(3)
            self.tabs.insertTab(3, self.notification_tab_widget, "🔔 通知设置")

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

        # 位置选择
        self.position_combo = QComboBox()
        self.position_combo.addItems(["bottom", "top"])
        self.position_combo.setCurrentText(self.config.get('position', 'bottom') if self.config else 'bottom')
        basic_layout.addRow("屏幕位置:", self.position_combo)

        # 显示器索引
        self.screen_spin = QSpinBox()
        self.screen_spin.setRange(0, 10)
        self.screen_spin.setValue(self.config.get('screen_index', 0) if self.config else 0)
        basic_layout.addRow("显示器索引:", self.screen_spin)

        # 更新间隔
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(100, 60000)
        self.interval_spin.setValue(self.config.get('update_interval', 1000) if self.config else 1000)
        self.interval_spin.setSuffix(" 毫秒")
        basic_layout.addRow("更新间隔:", self.interval_spin)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # 颜色设置组
        color_group = QGroupBox("颜色设置")
        color_layout = QFormLayout()

        # 背景颜色
        bg_color_layout = QHBoxLayout()
        bg_color = self.config.get('background_color', '#505050') if self.config else '#505050'
        self.bg_color_input = QLineEdit(bg_color)
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
        self.opacity_spin.setValue(self.config.get('background_opacity', 180) if self.config else 180)
        color_layout.addRow("背景透明度:", self.opacity_spin)

        # 时间标记颜色
        marker_color_layout = QHBoxLayout()
        marker_color = self.config.get('marker_color', '#FF0000') if self.config else '#FF0000'
        self.marker_color_input = QLineEdit(marker_color)
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
        self.marker_width_spin.setValue(self.config.get('marker_width', 2) if self.config else 2)
        self.marker_width_spin.setSuffix(" 像素")
        color_layout.addRow("时间标记宽度:", self.marker_width_spin)

        # 时间标记类型
        marker_type_layout = QHBoxLayout()
        self.marker_type_combo = QComboBox()
        self.marker_type_combo.addItems(["line", "image", "gif"])
        marker_type = self.config.get('marker_type', 'line') if self.config else 'line'
        self.marker_type_combo.setCurrentText(marker_type)
        self.marker_type_combo.currentTextChanged.connect(self.on_marker_type_changed)
        marker_type_layout.addWidget(self.marker_type_combo)

        marker_type_hint = QLabel("(line=线条, image=图片, gif=动画)")
        marker_type_hint.setStyleSheet("color: #666; font-size: 9pt;")
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
        marker_size = self.config.get('marker_size', 50) if self.config else 50
        self.marker_size_spin.setValue(marker_size)
        self.marker_size_spin.setSuffix(" px")
        self.marker_size_spin.setMaximumWidth(80)
        self.marker_size_spin.valueChanged.connect(self.on_marker_size_value_changed)
        marker_size_layout.addWidget(self.marker_size_spin)

        marker_size_layout.addStretch()

        color_layout.addRow("标记图片大小:", marker_size_container)

        # 延迟更新按钮状态
        # 将在 _load_config_and_tasks 中更新

        # 标记图片 X 轴偏移
        self.marker_x_offset_spin = QSpinBox()
        self.marker_x_offset_spin.setRange(-100, 100)
        self.marker_x_offset_spin.setValue(self.config.get('marker_x_offset', 0))
        self.marker_x_offset_spin.setSuffix(" px")
        self.marker_x_offset_spin.setMaximumWidth(100)
        x_offset_hint = QLabel("(正值向右,负值向左)")
        x_offset_hint.setStyleSheet("color: #666; font-size: 9pt;")
        x_offset_layout = QHBoxLayout()
        x_offset_layout.addWidget(self.marker_x_offset_spin)
        x_offset_layout.addWidget(x_offset_hint)
        x_offset_layout.addStretch()
        color_layout.addRow("标记图片 X 偏移:", x_offset_layout)

        # 标记图片 Y 轴偏移
        self.marker_y_offset_spin = QSpinBox()
        self.marker_y_offset_spin.setRange(-100, 100)
        self.marker_y_offset_spin.setValue(self.config.get('marker_y_offset', 0))
        self.marker_y_offset_spin.setSuffix(" px")
        self.marker_y_offset_spin.setMaximumWidth(100)
        y_offset_hint = QLabel("(正值向上,负值向下)")
        y_offset_hint.setStyleSheet("color: #666; font-size: 9pt;")
        y_offset_layout = QHBoxLayout()
        y_offset_layout.addWidget(self.marker_y_offset_spin)
        y_offset_layout.addWidget(y_offset_hint)
        y_offset_layout.addStretch()
        color_layout.addRow("标记图片 Y 偏移:", y_offset_layout)

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

        # AI任务规划区域
        ai_group = QGroupBox("🤖 AI智能规划")
        ai_layout = QVBoxLayout()

        # 说明标签
        ai_hint = QLabel("💡 用自然语言描述您的计划,AI将自动生成任务时间表")
        ai_hint.setStyleSheet("color: #FF9800; font-style: italic; padding: 3px;")
        ai_layout.addWidget(ai_hint)

        # AI输入框
        input_container = QHBoxLayout()
        input_label = QLabel("描述您的计划:")
        input_label.setStyleSheet("font-weight: bold;")
        input_container.addWidget(input_label)

        self.ai_input = QLineEdit()
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
        self.quota_label.setStyleSheet("color: #666; padding: 5px;")
        ai_button_layout.addWidget(self.quota_label)

        # 刷新配额按钮
        refresh_quota_btn = QPushButton("🔄 刷新配额")
        refresh_quota_btn.clicked.connect(self.refresh_quota_status)
        refresh_quota_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 6px 12px;
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
            self.quota_label.setText("⏳ AI服务正在初始化...")
            self.quota_label.setStyleSheet("color: #ff9800; padding: 5px; font-weight: bold;")
        if hasattr(self, 'generate_btn'):
            self.generate_btn.setEnabled(False)

        # 说明标签
        info_label = QLabel("双击表格单元格可以编辑任务内容")
        info_label.setStyleSheet("color: #666; font-style: italic;")
        top_layout.addWidget(info_label)

        # 模板加载区域 - 单行显示所有模板
        template_group = QGroupBox("📋 预设模板")
        template_layout = QHBoxLayout()

        template_label = QLabel("快速加载:")
        template_layout.addWidget(template_label)

        # 24小时模板按钮
        template_24h_btn = QPushButton("24小时")
        template_24h_btn.clicked.connect(lambda: self.load_template("tasks_template_24h.json"))
        template_24h_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 6px; }")
        template_layout.addWidget(template_24h_btn)

        # 工作日模板按钮
        template_work_btn = QPushButton("工作日")
        template_work_btn.clicked.connect(lambda: self.load_template("tasks_template_workday.json"))
        template_work_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 6px; }")
        template_layout.addWidget(template_work_btn)

        # 学生模板按钮
        template_student_btn = QPushButton("学生")
        template_student_btn.clicked.connect(lambda: self.load_template("tasks_template_student.json"))
        template_student_btn.setStyleSheet("QPushButton { background-color: #9C27B0; color: white; padding: 6px; }")
        template_layout.addWidget(template_student_btn)

        # 自由职业者模板
        template_freelancer_btn = QPushButton("自由职业")
        template_freelancer_btn.clicked.connect(lambda: self.load_template("tasks_template_freelancer.json"))
        template_freelancer_btn.setStyleSheet("QPushButton { background-color: #00BCD4; color: white; padding: 6px; }")
        template_layout.addWidget(template_freelancer_btn)

        # 夜班作息模板
        template_night_btn = QPushButton("夜班")
        template_night_btn.clicked.connect(lambda: self.load_template("tasks_template_night_shift.json"))
        template_night_btn.setStyleSheet("QPushButton { background-color: #3F51B5; color: white; padding: 6px; }")
        template_layout.addWidget(template_night_btn)

        # 内容创作者模板
        template_creator_btn = QPushButton("创作者")
        template_creator_btn.clicked.connect(lambda: self.load_template("tasks_template_creator.json"))
        template_creator_btn.setStyleSheet("QPushButton { background-color: #E91E63; color: white; padding: 6px; }")
        template_layout.addWidget(template_creator_btn)

        # 健身达人模板
        template_fitness_btn = QPushButton("健身")
        template_fitness_btn.clicked.connect(lambda: self.load_template("tasks_template_fitness.json"))
        template_fitness_btn.setStyleSheet("QPushButton { background-color: #FF5722; color: white; padding: 6px; }")
        template_layout.addWidget(template_fitness_btn)

        # 创业者模板
        template_entrepreneur_btn = QPushButton("创业者")
        template_entrepreneur_btn.clicked.connect(lambda: self.load_template("tasks_template_entrepreneur.json"))
        template_entrepreneur_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; padding: 6px; }")
        template_layout.addWidget(template_entrepreneur_btn)

        template_layout.addStretch()
        template_group.setLayout(template_layout)
        top_layout.addWidget(template_group)

        layout.addLayout(top_layout)

        # 可视化时间轴编辑器（延迟创建，避免初始化时阻塞）
        timeline_group = QGroupBox("🎨 可视化时间轴编辑器")
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
        self.tasks_table.setColumnCount(5)
        self.tasks_table.setHorizontalHeaderLabels(["开始时间", "结束时间", "任务名称", "颜色", "操作"])
        self.tasks_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        # 监听表格项的变化,实时同步到时间轴
        self.tasks_table.itemChanged.connect(self.on_table_item_changed)

        # 延迟加载任务到表格，避免初始化时阻塞UI
        QTimer.singleShot(100, self.load_tasks_to_table)

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

    def create_theme_tab(self):
        """创建主题设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 说明标签
        info_label = QLabel("选择或自定义主题，让进度条更符合您的喜好")
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        layout.addWidget(info_label)

        # 预设主题选择组（带预览）
        preset_group = QGroupBox("预设主题")
        preset_layout = QFormLayout()

        # 获取所有预设主题(检查主题管理器是否已初始化)
        if not self.theme_manager:
            # 如果主题管理器还未初始化,尝试初始化
            self._init_theme_manager()
            # 如果仍然失败,使用默认主题
            if not self.theme_manager:
                preset_themes = ThemeManager.DEFAULT_PRESET_THEMES.copy()
            else:
                all_themes = self.theme_manager.get_all_themes()
                preset_themes = all_themes.get('preset_themes', {})
        else:
            all_themes = self.theme_manager.get_all_themes()
            preset_themes = all_themes.get('preset_themes', {})

        # 当前选中的主题ID（从config中获取）
        theme_config = self.config.get('theme', {})
        current_theme_id = theme_config.get('current_theme_id', 'business')
        self.selected_theme_id = current_theme_id

        # 创建主题下拉框和预览区域
        theme_container = QHBoxLayout()
        
        self.theme_combo = QComboBox()
        for theme_id, theme_data in preset_themes.items():
            theme_name = theme_data.get('name', theme_id)
            self.theme_combo.addItem(theme_name, theme_id)
        
        # 设置当前选中项
        index = self.theme_combo.findData(current_theme_id)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        
        self.theme_combo.currentIndexChanged.connect(self.on_preset_theme_changed)
        theme_container.addWidget(self.theme_combo)
        
        # 主题预览区域
        preview_container = QHBoxLayout()
        preview_container.setSpacing(5)
        
        # 背景色预览
        bg_preview = QLabel("背景:")
        bg_preview.setStyleSheet("font-size: 10px; color: #666;")
        preview_container.addWidget(bg_preview)
        
        self.bg_preview_label = QLabel()
        self.bg_preview_label.setFixedSize(30, 20)
        self.bg_preview_label.setStyleSheet(f"""
            QLabel {{
                background-color: {preset_themes.get(current_theme_id, {}).get('background_color', '#FFFFFF')};
                border: 1px solid #CCC;
                border-radius: 3px;
            }}
        """)
        preview_container.addWidget(self.bg_preview_label)
        
        # 任务配色预览
        task_colors_preview = QLabel("配色:")
        task_colors_preview.setStyleSheet("font-size: 10px; color: #666;")
        preview_container.addWidget(task_colors_preview)
        
        self.colors_preview_widget = QWidget()
        colors_preview_layout = QHBoxLayout(self.colors_preview_widget)
        colors_preview_layout.setContentsMargins(0, 0, 0, 0)
        colors_preview_layout.setSpacing(3)
        
        # 初始化颜色预览
        current_theme_data = preset_themes.get(current_theme_id, {})
        task_colors = current_theme_data.get('task_colors', [])
        self.update_colors_preview(task_colors)
        
        preview_container.addWidget(self.colors_preview_widget)
        preview_container.addStretch()
        
        theme_container.addLayout(preview_container, 1)
        
        preset_layout.addRow("选择主题:", theme_container)

        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)

        # 操作按钮组
        action_group = QGroupBox("操作")
        action_layout = QHBoxLayout()

        # 说明：主题选择后会自动应用，此按钮用于手动重新应用
        apply_theme_btn = QPushButton("🔄 重新应用主题")
        apply_theme_btn.clicked.connect(self.apply_selected_theme)
        apply_theme_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        action_layout.addWidget(apply_theme_btn)
        
        # 添加提示标签
        hint_label = QLabel("💡 提示：选择主题后会自动应用，无需点击按钮")
        hint_label.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
        action_layout.addWidget(hint_label)

        # 应用主题配色到任务按钮
        apply_colors_btn = QPushButton("🎨 应用主题配色到任务")
        apply_colors_btn.clicked.connect(self.apply_theme_colors_to_tasks)
        apply_colors_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        action_layout.addWidget(apply_colors_btn)

        action_layout.addStretch()

        action_group.setLayout(action_layout)
        layout.addWidget(action_group)

        # AI 智能推荐组
        ai_recommend_group = QGroupBox("🤖 AI 智能推荐")
        ai_recommend_layout = QVBoxLayout()

        # 说明标签
        ai_hint = QLabel("💡 AI会根据您的任务安排智能推荐3-5种适合的主题配色方案")
        ai_hint.setStyleSheet("color: #FF9800; font-style: italic; padding: 3px;")
        ai_recommend_layout.addWidget(ai_hint)

        # AI推荐按钮
        recommend_btn = QPushButton("✨ 获取AI推荐")
        recommend_btn.clicked.connect(self.on_ai_recommend_clicked)
        recommend_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF6B00;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #FF8500;
            }
        """)
        ai_recommend_layout.addWidget(recommend_btn)

        # AI推荐结果区域（滚动区域）
        from PySide6.QtWidgets import QScrollArea
        self.ai_recommend_scroll = QScrollArea()
        self.ai_recommend_scroll.setWidgetResizable(True)
        self.ai_recommend_scroll.setMaximumHeight(200)
        self.ai_recommend_scroll.setVisible(False)  # 初始隐藏
        
        ai_recommend_container = QWidget()
        self.ai_recommend_layout = QVBoxLayout(ai_recommend_container)
        self.ai_recommend_layout.setSpacing(10)
        
        self.ai_recommend_scroll.setWidget(ai_recommend_container)
        ai_recommend_layout.addWidget(self.ai_recommend_scroll)

        ai_recommend_group.setLayout(ai_recommend_layout)
        layout.addWidget(ai_recommend_group)

        # AI 主题生成组
        ai_generate_group = QGroupBox("🎨 AI 主题生成")
        ai_generate_layout = QVBoxLayout()

        # 说明标签
        generate_hint = QLabel("💡 用自然语言描述您想要的主题风格，AI将自动生成配色方案")
        generate_hint.setStyleSheet("color: #FF9800; font-style: italic; padding: 3px;")
        ai_generate_layout.addWidget(generate_hint)

        # 输入框
        input_container = QHBoxLayout()
        input_label = QLabel("描述:")
        input_label.setStyleSheet("font-weight: bold;")
        input_container.addWidget(input_label)

        self.theme_generate_input = QLineEdit()
        self.theme_generate_input.setPlaceholderText("例如: 清新自然的工作主题、温暖舒适的日常主题...")
        self.theme_generate_input.setMinimumHeight(35)
        self.theme_generate_input.returnPressed.connect(self.on_ai_generate_theme_clicked)
        input_container.addWidget(self.theme_generate_input)

        ai_generate_layout.addLayout(input_container)

        # 生成按钮
        generate_theme_btn = QPushButton("✨ 生成主题")
        generate_theme_btn.clicked.connect(self.on_ai_generate_theme_clicked)
        generate_theme_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF6B00;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #FF8500;
            }
        """)
        ai_generate_layout.addWidget(generate_theme_btn)

        ai_generate_group.setLayout(ai_generate_layout)
        layout.addWidget(ai_generate_group)

        layout.addStretch()

        return widget

    def create_theme_card(self, theme_id, theme_config, is_selected=False):
        """创建主题选择卡片"""
        from PySide6.QtWidgets import QFrame
        
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        card.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {'#4CAF50' if is_selected else '#E0E0E0'};
                border-radius: 8px;
                padding: 10px;
                background-color: {'#F0F8F0' if is_selected else 'white'};
            }}
            QFrame:hover {{
                border-color: #2196F3;
                background-color: #F5F5F5;
            }}
        """)

        card_layout = QHBoxLayout(card)

        # 主题预览（颜色块）
        preview_widget = QWidget()
        preview_widget.setFixedSize(60, 60)
        preview_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {theme_config.get('background_color', '#FFFFFF')};
                border: 1px solid #CCC;
                border-radius: 4px;
            }}
        """)
        card_layout.addWidget(preview_widget)

        # 主题信息
        info_layout = QVBoxLayout()
        
        name_label = QLabel(theme_config.get('name', theme_id))
        name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        info_layout.addWidget(name_label)

        desc_label = QLabel(theme_config.get('description', ''))
        desc_label.setStyleSheet("color: #666; font-size: 11px;")
        desc_label.setWordWrap(True)
        info_layout.addWidget(desc_label)

        # 颜色预览
        colors_layout = QHBoxLayout()
        colors_layout.setSpacing(5)
        task_colors = theme_config.get('task_colors', [])
        for color in task_colors[:4]:  # 最多显示4个颜色
            color_label = QLabel()
            color_label.setFixedSize(20, 20)
            color_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {color};
                    border: 1px solid #CCC;
                    border-radius: 10px;
                }}
            """)
            colors_layout.addWidget(color_label)
        colors_layout.addStretch()
        info_layout.addLayout(colors_layout)

        card_layout.addLayout(info_layout, 1)

        # 选中标记
        if is_selected:
            check_label = QLabel("✓")
            check_label.setStyleSheet("font-size: 24px; color: #4CAF50; font-weight: bold;")
            card_layout.addWidget(check_label)

        # 点击事件
        def on_card_clicked():
            # 取消其他卡片的选中状态
            for tid, c in self.theme_cards.items():
                if tid != theme_id:
                    c.setStyleSheet("""
                        QFrame {
                            border: 2px solid #E0E0E0;
                            border-radius: 8px;
                            padding: 10px;
                            background-color: white;
                        }
                        QFrame:hover {
                            border-color: #2196F3;
                            background-color: #F5F5F5;
                        }
                    """)
                    # 移除选中标记
                    c_layout = c.layout()
                    if c_layout:
                        for i in range(c_layout.count() - 1, -1, -1):  # 从后往前遍历
                            item = c_layout.itemAt(i)
                            if item and item.widget():
                                widget = item.widget()
                                if isinstance(widget, QLabel) and widget.text() == "✓":
                                    widget.deleteLater()
                                    break
            
            # 选中当前卡片
            card.setStyleSheet("""
                QFrame {
                    border: 2px solid #4CAF50;
                    border-radius: 8px;
                    padding: 10px;
                    background-color: #F0F8F0;
                }
            """)
            check_label = QLabel("✓")
            check_label.setStyleSheet("font-size: 24px; color: #4CAF50; font-weight: bold;")
            card_layout.addWidget(check_label)
            
            self.selected_theme_id = theme_id

        card.mousePressEvent = lambda e: on_card_clicked()

        return card

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

    def on_preset_theme_changed(self, index):
        """预设主题下拉框改变时的处理"""
        if index >= 0:
            theme_id = self.theme_combo.itemData(index)
            if theme_id:
                self.selected_theme_id = theme_id
                
                # 更新预览(检查主题管理器是否已初始化)
                if not self.theme_manager:
                    # 如果未初始化,使用默认主题
                    preset_themes = ThemeManager.DEFAULT_PRESET_THEMES.copy()
                else:
                    all_themes = self.theme_manager.get_all_themes()
                    preset_themes = all_themes.get('preset_themes', {})
                
                theme_data = preset_themes.get(theme_id, {})
                
                # 更新背景色预览
                if hasattr(self, 'bg_preview_label'):
                    bg_color = theme_data.get('background_color', '#FFFFFF')
                    self.bg_preview_label.setStyleSheet(f"""
                        QLabel {{
                            background-color: {bg_color};
                            border: 1px solid #CCC;
                            border-radius: 3px;
                        }}
                    """)
                
                # 更新任务配色预览
                task_colors = theme_data.get('task_colors', [])
                if hasattr(self, 'colors_preview_widget'):
                    self.update_colors_preview(task_colors)
                
                # 自动应用主题（无需点击按钮）
                self.apply_selected_theme_silent()

    # 已移除主题模式选择功能，只保留预设主题

    def update_preview_from_current_theme(self):
        """从当前主题更新预览"""
        if not self.theme_manager:
            return
        
        theme = self.theme_manager.get_current_theme()
        if not theme:
            return
        
        # 更新背景色预览
        if hasattr(self, 'bg_preview_label'):
            bg_color = theme.get('background_color', '#FFFFFF')
            self.bg_preview_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {bg_color};
                    border: 1px solid #CCC;
                    border-radius: 3px;
                }}
            """)
        
        # 更新任务配色预览
        task_colors = theme.get('task_colors', [])
        if hasattr(self, 'colors_preview_widget'):
            self.update_colors_preview(task_colors)

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
    
    def on_ai_recommend_clicked(self):
        """AI推荐主题按钮点击事件"""
        if not self.tasks:
            QMessageBox.warning(self, "提示", "请先添加任务后再获取AI推荐")
            return

        # 检查AI组件是否已初始化
        if not hasattr(self, 'theme_ai_helper') or not self.theme_ai_helper:
            QMessageBox.warning(
                self,
                "AI服务未就绪",
                "AI服务正在初始化中,请稍候片刻再试...",
                QMessageBox.Ok
            )
            return

        # 检查后端服务是否运行
        # 异步检查后端服务状态（不阻塞UI）
        if not hasattr(self, 'ai_client') or not self.ai_client:
            # 如果AI客户端未初始化，直接返回，不显示推荐
            return
            reply = QMessageBox.question(
                self,
                "AI服务未启动",
                "AI后端服务未启动。\n\n是否需要帮助?\n\n提示:\n1. 确保已安装依赖: pip install flask flask-cors openai python-dotenv\n2. 确保.env文件包含有效的TUZI_API_KEY\n3. 手动运行: python backend_api.py",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                # 尝试启动后端服务
                if hasattr(self, 'backend_manager'):
                    QMessageBox.information(
                        self,
                        "正在启动",
                        "正在尝试启动AI后端服务,请稍候...",
                        QMessageBox.Ok
                    )
                    self.backend_manager.ensure_backend_running_async()
            return

        # 禁用按钮，显示加载状态
        sender = self.sender()
        sender.setEnabled(False)
        sender.setText("生成中...")

        # 在后台线程中执行AI请求
        class ThemeRecommendWorker(QThread):
            finished = Signal(object)
            error = Signal(str)

            def __init__(self, ai_helper, tasks):
                super().__init__()
                self.ai_helper = ai_helper
                self.tasks = tasks

            def run(self):
                try:
                    result = self.ai_helper.recommend_themes(self.tasks, {})
                    self.finished.emit(result)
                except Exception as e:
                    import traceback
                    error_detail = traceback.format_exc()
                    logging.error(f"AI推荐失败: {error_detail}")
                    self.error.emit(str(e))

        self.recommend_worker = ThemeRecommendWorker(self.theme_ai_helper, self.tasks)
        self.recommend_worker.finished.connect(self.on_ai_recommend_finished)
        self.recommend_worker.error.connect(self.on_ai_recommend_error)
        self.recommend_worker.start()
    
    def on_ai_recommend_finished(self, recommendations):
        """AI推荐完成"""
        # 恢复按钮状态
        for widget in self.findChildren(QPushButton):
            if widget.text() == "生成中...":
                widget.setEnabled(True)
                widget.setText("✨ 获取AI推荐")
                break
        
        if not recommendations:
            return
        
        # 显示推荐结果
        if hasattr(self, 'ai_recommend_scroll'):
            self.ai_recommend_scroll.setVisible(True)
        
        # 清空旧推荐
        if hasattr(self, 'ai_recommend_layout'):
            while self.ai_recommend_layout.count():
                item = self.ai_recommend_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # 创建推荐卡片
            for i, rec in enumerate(recommendations):
                card = self.create_ai_recommend_card(rec, i)
                self.ai_recommend_layout.addWidget(card)
            
            self.ai_recommend_layout.addStretch()
        
        QMessageBox.information(self, "成功", f"已生成 {len(recommendations)} 个推荐主题")
    
    def on_ai_recommend_error(self, error_msg):
        """AI推荐错误"""
        # 恢复按钮状态
        for widget in self.findChildren(QPushButton):
            if widget.text() == "生成中...":
                widget.setEnabled(True)
                widget.setText("✨ 获取AI推荐")
                break
        
        QMessageBox.warning(self, "错误", f"AI推荐失败: {error_msg}")
    
    def create_ai_recommend_card(self, recommendation, index):
        """创建AI推荐主题卡片"""
        from PySide6.QtWidgets import QFrame
        
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        card.setStyleSheet("""
            QFrame {
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 10px;
                background-color: white;
            }
            QFrame:hover {
                border-color: #FF6B00;
                background-color: #FFF8F0;
            }
        """)
        
        card_layout = QHBoxLayout(card)
        
        # 主题预览
        preview_widget = QWidget()
        preview_widget.setFixedSize(50, 50)
        config = recommendation.get('config', {})
        preview_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {config.get('background_color', '#FFFFFF')};
                border: 1px solid #CCC;
                border-radius: 4px;
            }}
        """)
        card_layout.addWidget(preview_widget)
        
        # 主题信息
        info_layout = QVBoxLayout()
        
        name_label = QLabel(recommendation.get('name', f'推荐主题 {index + 1}'))
        name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        info_layout.addWidget(name_label)
        
        reason_label = QLabel(recommendation.get('reason', ''))
        reason_label.setStyleSheet("color: #666; font-size: 11px;")
        reason_label.setWordWrap(True)
        info_layout.addWidget(reason_label)
        
        # 颜色预览
        colors_layout = QHBoxLayout()
        colors_layout.setSpacing(5)
        task_colors = config.get('task_colors', [])
        for color in task_colors[:4]:
            color_label = QLabel()
            color_label.setFixedSize(18, 18)
            color_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {color};
                    border: 1px solid #CCC;
                    border-radius: 9px;
                }}
            """)
            colors_layout.addWidget(color_label)
        colors_layout.addStretch()
        info_layout.addLayout(colors_layout)
        
        card_layout.addLayout(info_layout, 1)
        
        # 应用按钮
        apply_btn = QPushButton("应用")
        apply_btn.setMaximumWidth(60)
        apply_btn.clicked.connect(lambda: self.apply_ai_recommendation(recommendation))
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        card_layout.addWidget(apply_btn)
        
        return card
    
    def apply_ai_recommendation(self, recommendation):
        """应用AI推荐的主题"""
        config = recommendation.get('config', {})
        theme_id = recommendation.get('theme_id', f"ai_recommended_{recommendation.get('name', 'unknown')}")
        
        # 创建主题配置
        theme_config = {
            'id': theme_id,
            'name': recommendation.get('name', 'AI推荐主题'),
            'type': 'ai_generated',
            'background_color': config.get('background_color', '#1E1E1E'),
            'background_opacity': config.get('background_opacity', 220),
            'task_colors': config.get('task_colors', []),
            'marker_color': config.get('marker_color', '#FF5252'),
            'text_color': config.get('text_color', '#FFFFFF'),
            'accent_color': config.get('accent_color', '#2196F3'),
            'description': recommendation.get('reason', '')
        }
        
        # 应用主题
        if not self.theme_manager:
            QMessageBox.warning(self, "错误", "主题管理器未初始化，请稍后再试")
            return
        
        success = self.theme_manager.apply_custom_theme(theme_config, theme_id)
        if success:
            QMessageBox.information(self, "成功", f"已应用主题: {theme_config['name']}")
            # 更新当前选中主题
            self.selected_theme_id = theme_id
        else:
            QMessageBox.warning(self, "错误", "应用主题失败")
    
    def on_ai_generate_theme_clicked(self):
        """AI生成主题按钮点击事件"""
        if not hasattr(self, 'theme_generate_input'):
            return
        
        description = self.theme_generate_input.text().strip()
        if not description:
            QMessageBox.warning(self, "提示", "请输入主题描述")
            return
        
        # 禁用按钮，显示加载状态
        sender = self.sender()
        sender.setEnabled(False)
        sender.setText("生成中...")
        
        # 在后台线程中执行AI请求
        class ThemeGenerateWorker(QThread):
            finished = Signal(object)
            error = Signal(str)
            
            def __init__(self, ai_helper, description):
                super().__init__()
                self.ai_helper = ai_helper
                self.description = description
            
            def run(self):
                try:
                    result = self.ai_helper.generate_theme_from_description(self.description)
                    self.finished.emit(result)
                except Exception as e:
                    self.error.emit(str(e))
        
        self.generate_worker = ThemeGenerateWorker(self.theme_ai_helper, description)
        self.generate_worker.finished.connect(self.on_ai_generate_finished)
        self.generate_worker.error.connect(self.on_ai_generate_error)
        self.generate_worker.start()
    
    def on_ai_generate_finished(self, theme):
        """AI生成主题完成"""
        # 恢复按钮状态
        for widget in self.findChildren(QPushButton):
            if widget.text() == "生成中...":
                widget.setEnabled(True)
                widget.setText("✨ 生成主题")
                break
        
        if not theme:
            return
        
        # 应用生成的主题
        theme_config = theme.get('config', {})
        theme_id = theme.get('theme_id', 'ai_generated_unknown')
        
        full_theme_config = {
            'id': theme_id,
            'name': theme.get('name', 'AI生成主题'),
            'type': 'ai_generated',
            'background_color': theme_config.get('background_color', '#1E1E1E'),
            'background_opacity': theme_config.get('background_opacity', 220),
            'task_colors': theme_config.get('task_colors', []),
            'marker_color': theme_config.get('marker_color', '#FF5252'),
            'text_color': theme_config.get('text_color', '#FFFFFF'),
            'accent_color': theme_config.get('accent_color', '#2196F3'),
            'description': theme.get('description', '基于AI生成的主题')
        }
        
        # 保存并应用主题
        if not self.theme_manager:
            QMessageBox.warning(self, "错误", "主题管理器未初始化，请稍后再试")
            return
        
        success = self.theme_manager.apply_custom_theme(full_theme_config, theme_id)
        if success:
            QMessageBox.information(self, "成功", f"已生成并应用主题: {full_theme_config['name']}")
            # 清空输入框
            if hasattr(self, 'theme_generate_input'):
                self.theme_generate_input.clear()
            # 更新当前选中主题
            self.selected_theme_id = theme_id
        else:
            QMessageBox.warning(self, "错误", "应用主题失败")
    
    def on_ai_generate_error(self, error_msg):
        """AI生成主题错误"""
        # 恢复按钮状态
        for widget in self.findChildren(QPushButton):
            if widget.text() == "生成中...":
                widget.setEnabled(True)
                widget.setText("✨ 生成主题")
                break
        
        QMessageBox.warning(self, "错误", f"AI生成失败: {error_msg}")

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

            # 删除按钮
            delete_btn = QPushButton("🗑️ 删除")
            delete_btn.clicked.connect(lambda checked, r=row: self.delete_task(r))
            delete_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
            self.tasks_table.setCellWidget(row, 4, delete_btn)

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
                delete_btn = self.tasks_table.cellWidget(r, 4)
                if delete_btn:
                    delete_btn.clicked.disconnect()
                    delete_btn.clicked.connect(lambda checked, row=r: self.delete_task(row))

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
                "marker_x_offset": self.marker_x_offset_spin.value(),
                "marker_y_offset": self.marker_y_offset_spin.value(),
                "screen_index": self.screen_spin.value(),
                "update_interval": self.interval_spin.value(),
                "enable_shadow": self.shadow_check.isChecked(),
                "corner_radius": self.radius_spin.value(),
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
                self.quota_label.setText("⏳ AI服务正在初始化...")
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
                    response = requests.get(
                        f"{self.backend_url}/api/quota-status",
                        params={
                            "user_id": self.user_id,
                            "user_tier": self.user_tier
                        },
                        timeout=5  # 缩短超时时间
                    )
                    if response.status_code == 200:
                        self.finished.emit(response.json())
                    else:
                        self.finished.emit(None)
                except Exception:
                    self.finished.emit(None)
        
        # 创建并启动工作线程
        worker = QuotaCheckWorker(
            self.ai_client.backend_url,
            self.ai_client.user_id,
            self.ai_client.user_tier
        )
        worker.finished.connect(self._on_quota_status_finished)
        worker.start()
        
        # 保存worker引用，避免被垃圾回收
        if not hasattr(self, '_quota_check_workers'):
            self._quota_check_workers = []
        self._quota_check_workers.append(worker)
        
        # 清理旧的worker引用（保留最近3个）
        if len(self._quota_check_workers) > 3:
            self._quota_check_workers.pop(0)
    
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
            # 配额检查失败，可能是后端服务崩溃或接口有问题
            self.quota_label.setText("⚠️ 无法获取配额状态")
            self.quota_label.setStyleSheet("color: #999; padding: 5px;")
            if hasattr(self, 'generate_btn'):
                self.generate_btn.setEnabled(True)  # 仍然允许尝试
            
            # 配额检查失败，可能是代理服务器暂时不可用或网络问题
            # 使用代理服务器时，不需要检查本地后端服务
            # 延迟后重试配额检查
            logging.warning("配额检查失败，可能是代理服务器暂时不可用，3秒后重试...")
            QTimer.singleShot(3000, self.refresh_quota_status_async)

    def on_ai_generate_clicked(self):
        """处理AI生成按钮点击"""
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
        
        # 对于按钮点击，仍然使用同步检查（但已在后台线程中）
        # 如果后端未启动，给出提示并返回
        # 注意：这里不阻塞UI，因为后端服务应该已经在后台启动
        try:
            import requests
            response = requests.get(f"{self.ai_client.backend_url}/health", timeout=1)
            if response.status_code != 200:
                QMessageBox.critical(
                    self,
                    "AI服务未启动",
                    "无法连接到AI后端服务器!\n\nAI服务正在后台启动,请稍候片刻再试...",
                    QMessageBox.Ok
                )
                return
        except Exception:
            QMessageBox.critical(
                self,
                "AI服务未启动",
                "无法连接到AI后端服务器!\n\nAI服务正在后台启动,请稍候片刻再试...",
                QMessageBox.Ok
            )
            return

        # 禁用按钮并显示加载状态
        self.generate_btn.setEnabled(False)
        self.generate_btn.setText("⏳ AI正在生成...")

        # 创建并启动工作线程
        self.ai_worker = AIWorker(self.ai_client, user_input)
        self.ai_worker.finished.connect(self.on_ai_generation_finished)
        self.ai_worker.error.connect(self.on_ai_generation_error)
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

    def closeEvent(self, event):
        """窗口关闭事件，清理所有资源"""
        # 停止AI状态定时器
        if hasattr(self, 'ai_status_timer') and self.ai_status_timer:
            if self.ai_status_timer.isActive():
                self.ai_status_timer.stop()
            self.ai_status_timer = None
        
        # 取消正在运行的AI工作线程
        if hasattr(self, 'ai_worker') and self.ai_worker:
            if self.ai_worker.isRunning():
                self.ai_worker.terminate()
                self.ai_worker.wait(1000)  # 等待最多1秒
            self.ai_worker = None
        
        # 取消注册主题管理器组件（如果已注册）
        if hasattr(self, 'theme_manager') and self.theme_manager:
            try:
                self.theme_manager.unregister_ui_component(self)
            except Exception:
                pass
        
        # 停止AI后端服务（如果配置管理器启动的）
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

    # 设置应用样式
    app.setStyle("Fusion")

    window = ConfigManager()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
