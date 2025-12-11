"""
GaiYa每日进度条 - 桌面时间可视化工具
用进度条让时间流逝清晰可见
一个透明、置顶、可点击穿透的桌面时间进度条应用
"""

import sys
import json
import copy
import logging
import platform
import time
from pathlib import Path
from datetime import datetime, date
from version import __version__, VERSION_STRING, VERSION_STRING_ZH, get_version_info
from PySide6.QtWidgets import (QApplication, QWidget, QSystemTrayIcon, QMenu, QLabel,
                                QHBoxLayout, QVBoxLayout, QDialog, QFormLayout, QSpinBox, QPushButton, QMessageBox, QToolTip)
from PySide6.QtCore import Qt, QRectF, QTimer, QTime, QFileSystemWatcher, QPoint, Signal, QEventLoop, QSize
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPixmap, QMovie, QCursor, QPainterPath, QAction
from enum import Enum
from statistics_manager import StatisticsManager
# 已切换到Vercel云服务，无需本地后端管理器
# from backend_manager import BackendManager
from gaiya.core.theme_manager import ThemeManager
from gaiya.core.auth_client import AuthClient
# 确保 config_gui 模块被 PyInstaller 检测到（必须在顶部导入）
import config_gui
from config_gui import ConfigManager
# 确保 scene_editor 模块被 PyInstaller 检测到
import scene_editor
from scene_editor import SceneEditorWindow
from gaiya.core.pomodoro_state import PomodoroState
from gaiya.core.notification_manager import NotificationManager
from gaiya.ui.pomodoro_panel import PomodoroPanel, PomodoroSettingsDialog
from gaiya.data.db_manager import db
from gaiya.utils import time_utils, path_utils, data_loader, task_calculator, window_utils
from gaiya.utils.time_block_utils import generate_time_block_id, legacy_time_block_keys
from gaiya.scene import SceneLoader, SceneRenderer, SceneEventManager, ResourceCache, SceneManager
from gaiya.core.marker_presets import MarkerPresetManager
from gaiya.core.danmaku_manager import DanmakuManager

# i18n support
try:
    from i18n import tr
except ImportError:
    # Fallback if i18n not available
    def tr(key, fallback=None, **kwargs):
        return fallback or key

# Qt-Material主题支持（已移除，改用自定义浅色主题）
# try:
#     from qt_material import apply_stylesheet
#     QT_MATERIAL_AVAILABLE = True
# except ImportError:
#     QT_MATERIAL_AVAILABLE = False
#     logging.warning("qt-material未安装，将使用系统默认样式")
QT_MATERIAL_AVAILABLE = False  # 强制禁用qt-material

# Windows 特定导入
if platform.system() == 'Windows':
    import ctypes
    from ctypes import wintypes


class TimeProgressBar(QWidget):
    """时间进度条主窗口"""

    # 定义信号：从工作线程触发任务回顾窗口（必须在主线程中显示UI）
    task_review_requested = Signal(str, list)  # (date, unconfirmed_tasks)

    def __init__(self):
        super().__init__()
        self.app_dir = path_utils.get_app_dir()  # Get app directory
        self.setup_logging()  # Setup logging
        self.config = data_loader.load_config(self.app_dir, self.logger)  # Load config
        data_loader.init_i18n(self.config, self.logger)  # Initialize i18n
        self.tasks = data_loader.load_tasks(self.app_dir, self.logger)  # Load task data
        self.calculate_time_range()  # 计算任务的时间范围
        self.current_time_percentage = 0.0  # 初始化时间百分比
        self.hovered_task_index = -1  # 当前悬停的任务索引(-1表示没有悬停)
        self.is_mouse_over_progress_bar = False  # 鼠标是否在进度条上（用于控制标记图片显示）

        # 编辑模式状态管理
        self.edit_mode = False  # 编辑模式标志
        self.temp_tasks = None  # 临时任务数据副本（用于编辑时的临时修改）
        self.dragging = False  # 拖拽状态
        self.drag_task_index = -1  # 正在拖拽的任务索引
        self.drag_edge = None  # 拖拽的边缘：'left' or 'right'
        self.drag_start_x = 0  # 拖拽开始的X坐标
        self.drag_start_minutes = 0  # 拖拽开始时的分钟数
        self.hover_edge = None  # 悬停在哪个边缘：'left' or 'right'
        self.edge_detect_width = 8  # 边缘检测宽度（像素）
        self.min_task_duration = 15  # 最小任务时长（分钟）

        # 初始化时间标记相关变量
        self.marker_pixmap = None  # 静态图片
        self.marker_movie = None   # GIF 动画
        self.marker_frame_timer = None  # 手动控制GIF帧切换的定时器
        self.marker_current_frame = 0  # 手动跟踪当前帧索引（用于WebP修复）

        # GIF 帧率监控变量（用于诊断播放速度问题）
        self.gif_frame_count = 0  # 总帧数计数
        self.gif_last_frame_time = None  # 上一帧的时间
        self.gif_start_time = None  # 开始监控的时间
        self.gif_loop_count = 0  # 循环次数
        self.paint_event_count = 0  # paintEvent 调用次数

        # 初始化标记图片预设管理器
        self.marker_preset_manager = MarkerPresetManager()
        self.marker_preset_manager.load_from_config(self.config)

        self.init_marker_image()   # 加载时间标记图片

        # 初始化弹幕管理器
        self.danmaku_manager = DanmakuManager(self.app_dir, self.config, self.logger)

        # 番茄钟面板实例
        self.pomodoro_panel = None

        # 统计窗口实例
        self.statistics_window = None

        # 场景编辑器窗口实例
        self.scene_editor_window = None

        # Focus session state management
        self.active_focus_sessions = {}  # {time_block_id: session_id}
        self.completed_focus_blocks = set()  # time_block_ids with completed sessions today
        self.task_focus_states = {}  # {time_block_id: focus_state}
        self.completed_focus_start_times = {}  # {time_block_id: actual_start_time (datetime)}

        # ✅ P1-1.5: 日志去重 - 追踪专注记录数量,只在变化时输出日志
        self._last_completed_count = None

        # Focus mode state (immersive pomodoro timer in progress bar)
        self.focus_mode = False  # Whether focus mode is active
        self.focus_mode_type = None  # 'work' or 'break'
        self.focus_start_time = None  # When focus started (datetime)
        self.focus_duration_minutes = 25  # Total duration in minutes
        self.focus_task_name = None  # Name of the focused task
        self.focus_session_id = None  # Database session ID

        # 初始化主题管理器（延迟加载主题，避免初始化时触发信号）
        self.theme_manager = ThemeManager(self.app_dir)
        # 暂时不注册UI组件，等窗口完全初始化后再注册
        # self.theme_manager.register_ui_component(self)
        # self.theme_manager.theme_changed.connect(self.apply_theme)

        # 初始化用户认证客户端
        self.auth_client = AuthClient()

        # 初始化行为追踪服务
        from gaiya.services.activity_tracker import ActivityTracker
        self.activity_tracker = None

        # 初始化场景系统
        self.scene_manager = SceneManager()
        self.scene_renderer = SceneRenderer()
        self.scene_event_manager = SceneEventManager()

        # 加载场景配置
        self.scene_manager.load_config(self.config)
        # 如果场景系统已启用，加载当前场景
        if self.scene_manager.is_enabled() and self.scene_manager.get_current_scene_name():
            scene_name = self.scene_manager.get_current_scene_name()
            self.load_scene(scene_name)

        self.init_ui()
        self.init_timer()  # 初始化定时器
        self.init_tray()  # 初始化托盘
        self.init_notification_manager()  # 初始化通知管理器
        self.init_statistics_manager()  # 初始化统计管理器
        self.init_task_tracking_system()  # 初始化任务完成追踪系统
        self.init_file_watcher()  # 初始化文件监视器
        self.installEventFilter(self)  # 安装事件过滤器
        self.setMouseTracking(True)  # 启用鼠标追踪
        
        # 窗口完全初始化后再注册主题管理器和应用主题
        # 注册时不立即应用主题（避免在初始化时调用apply_theme）
        self.theme_manager.register_ui_component(self, apply_immediately=False)
        self.theme_manager.theme_changed.connect(self.apply_theme)
        
        # 使用QTimer延迟应用主题，确保窗口完全显示后再应用
        QTimer.singleShot(100, self.apply_theme)

        # 延迟检查是否首次运行，显示新手引导
        QTimer.singleShot(500, self.check_first_run)

        # 延迟初始化行为追踪服务（确保所有组件都已加载完成）
        QTimer.singleShot(1000, self.init_activity_tracker)

    def check_first_run(self):
        """检查是否首次运行，显示新手引导"""
        from gaiya.utils.first_run import FirstRunDetector

        detector = FirstRunDetector(self.app_dir)
        if detector.is_first_run():
            self.logger.info("检测到首次运行，显示新手引导")
            self.show_onboarding()

    def show_onboarding(self):
        """显示新手引导流程"""
        from gaiya.ui.onboarding import WelcomeDialog, SetupWizard
        from gaiya.utils.first_run import FirstRunDetector

        # 1. 显示欢迎对话框
        welcome = WelcomeDialog(self)
        welcome_result = welcome.exec()
        self.logger.info(f"[Onboarding] 欢迎对话框返回结果: {welcome_result}, Accepted={WelcomeDialog.DialogCode.Accepted}")

        if welcome_result == WelcomeDialog.DialogCode.Accepted:
            # 用户选择"开始配置"
            self.logger.info("[Onboarding] 用户点击了'开始配置',准备显示配置向导")
            try:
                wizard = SetupWizard(self)
                self.logger.info("[Onboarding] SetupWizard实例已创建")
            except Exception as e:
                self.logger.error(f"[Onboarding] 创建SetupWizard失败: {type(e).__name__}: {e}")
                self.logger.error(f"[Onboarding] 错误堆栈:", exc_info=True)
                return

            # 连接AI生成信号
            wizard.ai_generate_requested.connect(self.on_onboarding_ai_requested)

            self.logger.info("[Onboarding] 准备显示配置向导对话框")
            wizard_result = wizard.exec()
            self.logger.info(f"[Onboarding] 配置向导返回结果: {wizard_result}, Accepted={SetupWizard.DialogCode.Accepted}")

            if wizard_result == SetupWizard.DialogCode.Accepted:
                # 用户完成了向导配置
                template_id = wizard.get_selected_template()
                self.logger.info(f"新手引导完成，选择模板: {template_id}")

                # 应用选择的模板
                self.apply_template(template_id)

                # 标记新手引导已完成
                detector = FirstRunDetector(self.app_dir)
                detector.mark_completed()
        else:
            # 用户选择"暂时跳过"
            self.logger.info("用户跳过新手引导")
            # 仍然标记为已完成，避免下次再提示
            detector = FirstRunDetector(self.app_dir)
            detector.mark_completed()

    def on_onboarding_ai_requested(self):
        """新手引导中用户请求AI生成"""
        self.logger.info("新手引导：用户请求AI生成任务")
        # 标记新手引导完成
        from gaiya.utils.first_run import FirstRunDetector
        detector = FirstRunDetector(self.app_dir)
        detector.mark_completed()

        # 打开配置界面到任务管理标签页
        self.open_config_gui(initial_tab=1)  # 1 = 任务管理标签页

    def apply_template(self, template_id):
        """应用任务模板

        Args:
            template_id: 模板ID（work_weekday, student, freelancer）
        """
        from gaiya.utils import templates

        try:
            # 获取模板任务
            template_tasks = templates.get_template_tasks(template_id)
            if template_tasks:
                # 保存任务
                tasks_file = self.app_dir / 'tasks.json'
                import json
                with open(tasks_file, 'w', encoding='utf-8') as f:
                    json.dump(template_tasks, f, indent=4, ensure_ascii=False)

                # 重新加载任务
                self.reload_all()
                self.logger.info(f"成功应用模板: {template_id}")
            else:
                self.logger.warning(f"模板不存在: {template_id}")
        except Exception as e:
            self.logger.error(f"应用模板失败: {e}", exc_info=True)

    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口标题(虽然无边框窗口看不到，但在任务管理器中可见)
        self.setWindowTitle(f'{VERSION_STRING_ZH}')

        # 窗口标志组合
        # 移除 WindowTransparentForInput 以支持鼠标交互
        flags = (
            Qt.FramelessWindowHint |           # 无边框
            Qt.WindowStaysOnTopHint |          # 始终置顶
            Qt.WindowDoesNotAcceptFocus |      # 不接受焦点(避免影响其他窗口)
            Qt.BypassWindowManagerHint         # 绕过窗口管理器(防止被隐藏)
        )
        self.setWindowFlags(flags)

        # 设置背景透明(关键属性)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 设置为不在任务栏显示,但保持始终可见
        self.setAttribute(Qt.WA_X11DoNotAcceptFocus)

        # 设置窗口布局和位置
        self.setup_geometry()

        # 注意：不在init_ui中调用show()，避免在初始化时显示窗口
        # show()将在main()函数中调用

    def showEvent(self, event):
        """窗口显示事件"""
        super().showEvent(event)
        # 验证窗口实际位置
        actual_geometry = self.geometry()
        self.logger.info(f"窗口显示事件触发")
        self.logger.info(f"[窗口验证] 实际窗口位置: x={actual_geometry.x()}, y={actual_geometry.y()}, w={actual_geometry.width()}, h={actual_geometry.height()}")

        # Start focus state update timer (only once)
        if not hasattr(self, 'focus_state_timer'):
            self.focus_state_timer = QTimer(self)
            self.focus_state_timer.timeout.connect(self.update_focus_state)
            self.focus_state_timer.start(1000)  # Update every second
            self.logger.info("Focus state timer started")

    def hideEvent(self, event):
        """窗口隐藏事件"""
        super().hideEvent(event)
        self.logger.warning("窗口隐藏事件触发! 这不应该发生")

    def changeEvent(self, event):
        """窗口状态变化事件"""
        super().changeEvent(event)
        if event.type() == event.Type.WindowStateChange:
            self.logger.info(f"窗口状态变化: {self.windowState()}")

    def eventFilter(self, obj, event):
        """事件过滤器:防止窗口被意外隐藏"""
        from PySide6.QtCore import QEvent

        # 拦截隐藏事件并阻止
        if obj == self and event.type() == QEvent.Hide:
            self.logger.warning("检测到窗口隐藏事件,阻止并强制显示")
            # 阻止隐藏事件
            event.ignore()
            # 使用 QTimer 延迟强制显示,避免事件循环冲突
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, self.force_show)
            return True  # 事件已处理,不继续传播

        return super().eventFilter(obj, event)

    def force_show(self):
        """强制显示窗口"""
        self.setVisible(True)
        self.show()
        self.raise_()
        self.activateWindow()

        # Windows 特定:设置窗口始终在最顶层
        if platform.system() == 'Windows':
            self.set_windows_topmost()

        self.logger.info("强制显示窗口")

    def set_windows_topmost(self):
        """设置窗口始终置顶,在任务栏之上 (跨平台)"""
        try:
            hwnd = int(self.winId())
            window_utils.set_always_on_top(hwnd, True)
            self.logger.info("已设置 TOPMOST 属性")
        except Exception as e:
            self.logger.error(f"设置 TOPMOST 失败: {e}")

    def setup_geometry(self):
        """设置窗口几何属性(位置和大小)"""
        # 获取所有屏幕
        screens = QApplication.screens()
        screen_index = min(self.config['screen_index'], len(screens) - 1)
        screen = screens[screen_index]
        screen_geometry = screen.geometry()

        # 从配置读取参数
        bar_height = self.config['bar_height']
        bar_width = screen_geometry.width()

        # 悬停时需要额外的空间来显示扩展色块
        # 固定50像素的额外空间用于悬停效果,确保文本有足够空间
        hover_extra_space = 50

        # 计算标记图片需要的额外空间
        marker_extra_space = 0
        if self.config.get('marker_type') in ['image', 'gif']:
            marker_size = self.config.get('marker_size', 100)
            marker_y_offset = self.config.get('marker_y_offset', -30)
            # 标记图片可能超出进度条高度,需要预留额外空间
            # 如果图片底对齐,可能需要的高度 = 图片高度 - 进度条高度 + Y轴偏移
            marker_extra_space = max(0, marker_size - bar_height + abs(marker_y_offset))

        # 计算场景需要的额外空间
        scene_extra_space = 0
        if self.scene_manager.is_enabled():
            scene_config = self.scene_manager.get_current_scene_config()
            if scene_config and scene_config.canvas:
                # 场景需要的总高度减去进度条高度
                scene_extra_space = max(0, scene_config.canvas.height - bar_height)
                self.logger.info(f"[场景几何] 场景已启用: {scene_config.name}, 画布高度: {scene_config.canvas.height}, 额外空间: {scene_extra_space}")
            else:
                self.logger.warning(f"[场景几何] 场景已启用但配置无效: scene_config={scene_config}")
        else:
            self.logger.debug(f"[场景几何] 场景未启用")

        # 计算弹幕空间（如果启用）
        danmaku_extra_space = 0
        if hasattr(self, 'danmaku_manager') and self.danmaku_manager.enabled:
            # 弹幕区域高度 = y_offset + (max_count * 30px 行高)
            danmaku_extra_space = self.danmaku_manager.y_offset + (self.danmaku_manager.max_count * 40)
            self.logger.debug(f"[弹幕几何] 弹幕空间: {danmaku_extra_space}px")

        # 取悬停空间、标记空间、场景空间和弹幕空间的最大值
        hover_extra_space = max(hover_extra_space, marker_extra_space, scene_extra_space, danmaku_extra_space)
        self.logger.info(f"[场景几何] 悬停空间: {hover_extra_space} (悬停50, 标记{marker_extra_space}, 场景{scene_extra_space}, 弹幕{danmaku_extra_space})")

        # 根据配置定位到屏幕顶部或任务栏上方
        if self.config['position'] == 'bottom':
            # 使用可用几何(available geometry)而不是完整屏幕几何
            # 可用几何会排除任务栏、Dock等系统UI的空间
            available_geometry = screen.availableGeometry()
            self.logger.info(f"[场景几何] 可用区域: x={available_geometry.x()}, y={available_geometry.y()}, w={available_geometry.width()}, h={available_geometry.height()}")

            # 增加窗口高度以容纳悬停效果或场景
            total_height = bar_height + hover_extra_space

            # 窗口底部紧贴任务栏上方（不留空白间距）
            y_pos = available_geometry.y() + available_geometry.height() - total_height
            self.logger.info(f"[场景几何] 底部定位计算: y_pos = {available_geometry.y()} + {available_geometry.height()} - {total_height} = {y_pos}")
        else:
            # 顶部位置:使用可用区域的顶部
            available_geometry = screen.availableGeometry()
            total_height = bar_height + hover_extra_space
            y_pos = available_geometry.y()
            self.logger.info(f"[场景几何] 顶部定位: y_pos = {y_pos}")

        # 设置窗口几何属性
        # 注意：X坐标也使用available_geometry，确保坐标系一致
        self.setGeometry(
            available_geometry.x(),  # 使用可用区域的X坐标
            y_pos,                   # 计算后的Y坐标
            bar_width,
            total_height             # 窗口总高度
        )

        self.logger.info(f"[场景几何] ✓ 窗口位置设置: x={available_geometry.x()}, y={y_pos}, w={bar_width}, h={total_height} (bar_h={bar_height}), position={self.config['position']}")

    def setup_logging(self):
        """设置日志系统"""
        log_file = self.app_dir / 'gaiya.log'

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()  # 同时输出到控制台
            ]
        )
        self.logger = logging.getLogger(__name__)

        # 输出版本信息
        version_info = get_version_info()
        self.logger.info("=" * 60)
        self.logger.info(f"{VERSION_STRING_ZH} 启动")
        self.logger.info(f"版本: {version_info['version']}")
        self.logger.info(f"发布日期: {version_info['release_date']}")
        self.logger.info(f"构建类型: {version_info['build_type']}")
        self.logger.info(f"可执行文件: {version_info['exe_name']}")
        self.logger.info(f"Python: {sys.version.split()[0]}")
        self.logger.info(f"系统: {platform.system()} {platform.release()}")
        self.logger.info("=" * 60)


    def init_marker_image(self):
        """初始化时间标记图片"""
        marker_type = self.config.get('marker_type', 'gif')

        # 清理旧的资源
        self.marker_pixmap = None

        # 清理旧的QMovie
        if self.marker_movie:
            # 断开所有信号连接，防止重复连接导致帧率异常
            try:
                self.marker_movie.frameChanged.disconnect(self._on_gif_frame_changed)
                self.marker_movie.finished.disconnect(self._on_marker_animation_finished)
            except RuntimeError:
                # 信号已经断开，忽略
                pass
            except Exception as e:
                self.logger.debug(f"断开标记动画信号时出错: {e}")
            self.marker_movie.stop()
            self.marker_movie.deleteLater()  # 确保对象被正确清理
            self.marker_movie = None

            # 重置监控变量
            self.gif_frame_count = 0
            self.gif_last_frame_time = None
            self.gif_start_time = None
            self.gif_loop_count = 0
            self.paint_event_count = 0

        # 清理旧的帧定时器(WebP手动控制)
        if self.marker_frame_timer:
            self.marker_frame_timer.stop()
            try:
                self.marker_frame_timer.timeout.disconnect()
            except RuntimeError:
                pass
            self.marker_frame_timer.deleteLater()
            self.marker_frame_timer = None
            self.marker_current_frame = 0

        # 清理帧缓存
        if hasattr(self, 'marker_cached_frames'):
            self.marker_cached_frames = []

        if marker_type == 'line':
            # 线条模式,不需要加载图片
            return

        # 使用预设管理器获取标记图片路径
        image_path = self.marker_preset_manager.get_current_marker_path()

        # Fallback: 如果预设管理器返回空路径,尝试从配置读取旧格式路径
        if not image_path:
            self.logger.warning("预设管理器未返回路径,尝试使用配置中的marker_image_path")
            image_path = self.config.get('marker_image_path', '')

        if not image_path:
            self.logger.info("未配置时间标记图片,使用线条模式")
            self.config['marker_type'] = 'line'
            return

        # 预设管理器返回的已经是绝对路径
        image_file = Path(image_path)

        self.logger.info(f"[标记图片] 预设ID: {self.marker_preset_manager.get_current_preset_id()}")
        self.logger.info(f"[标记图片] 图片路径: {image_file}")
        self.logger.info(f"[标记图片] 文件存在: {image_file.exists()}")

        if not image_file.exists():
            self.logger.error(f"时间标记图片不存在: {image_file}")
            self.logger.error(f"[标记图片] 当前预设: {self.marker_preset_manager.get_current_preset_id()}")
            self.logger.error(f"[标记图片] 请检查PyInstaller spec文件中是否包含: ('assets/markers/', 'assets/markers/')")
            self.config['marker_type'] = 'line'
            return

        # 根据文件扩展名判断类型
        ext = image_file.suffix.lower()

        try:
            if ext in ['.gif', '.webp']:
                # GIF 或 WebP 动画
                self.logger.info(f"[QMovie诊断] 开始加载动画文件: {image_file}")
                self.marker_movie = QMovie(str(image_file))

                # 详细的QMovie验证日志
                is_valid = self.marker_movie.isValid()
                self.logger.info(f"[QMovie诊断] isValid(): {is_valid}")
                if is_valid:
                    self.logger.info(f"[QMovie诊断] frameCount(): {self.marker_movie.frameCount()}")
                    self.logger.info(f"[QMovie诊断] loopCount(): {self.marker_movie.loopCount()}")
                    # 尝试跳到第一帧测试
                    self.marker_movie.jumpToFrame(0)
                    first_frame = self.marker_movie.currentPixmap()
                    self.logger.info(f"[QMovie诊断] 第一帧尺寸: {first_frame.width()}x{first_frame.height()}")
                    self.logger.info(f"[QMovie诊断] 第一帧是否为空: {first_frame.isNull()}")

                if not is_valid:
                    self.logger.error(f"无效的动画文件: {image_file}")
                    self.logger.error(f"[QMovie诊断] QMovie.lastErrorString(): {self.marker_movie.lastErrorString()}")
                    self.marker_movie = None
                    self.config['marker_type'] = 'line'
                    return

                # 缩放到配置的大小
                marker_size = self.config.get('marker_size', 100)
                self.marker_movie.setScaledSize(QPixmap(marker_size, marker_size).size())

                # 设置播放速度 (100 = 原速, 200 = 2倍速, 50 = 0.5倍速)
                marker_speed = self.config.get('marker_speed', 100)
                self.marker_movie.setSpeed(marker_speed)

                # 设置缓存模式以优化播放性能
                self.marker_movie.setCacheMode(QMovie.CacheAll)

                # 预先缓存所有帧到内存（避免每次jumpToFrame解码）
                # 注意：必须在缓存之前断开finished信号，否则jumpToFrame会触发大量finished事件
                self.marker_cached_frames = []
                frame_count = self.marker_movie.frameCount()
                self.logger.info(f"[帧缓存] 开始缓存 {frame_count} 帧到内存（目标尺寸: {marker_size}x{marker_size}）...")

                # 缓存所有帧并手动缩放（QMovie的setScaledSize在某些情况下不可靠）
                from PySide6.QtCore import Qt
                target_size = QSize(marker_size, marker_size)

                for i in range(frame_count):
                    self.marker_movie.jumpToFrame(i)
                    original_pixmap = self.marker_movie.currentPixmap()

                    # 手动缩放到目标尺寸（保持宽高比，平滑变换）
                    scaled_pixmap = original_pixmap.scaled(
                        target_size,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    ).copy()  # 深拷贝

                    self.marker_cached_frames.append(scaled_pixmap)
                    self.logger.info(f"[帧缓存] 缓存帧 {i+1}/{frame_count}: {original_pixmap.width()}x{original_pixmap.height()} → {scaled_pixmap.width()}x{scaled_pixmap.height()}")

                # 重置到第一帧
                self.marker_movie.jumpToFrame(0)
                self.logger.info(f"[帧缓存] 完成！共缓存 {len(self.marker_cached_frames)} 帧")

                # 检测WebP格式 - 需要手动控制帧切换
                is_webp = str(image_file).lower().endswith('.webp')

                if is_webp:
                    # WebP格式：使用帧缓存 + 定时器手动控制（不启动QMovie）
                    self.logger.warning(f"[GIF修复] 检测到WebP格式，启用帧缓存+定时器手动控制")

                    # 创建高精度定时器手动控制帧切换
                    from PySide6.QtCore import QTimer, Qt
                    self.marker_frame_timer = QTimer(self)
                    self.marker_frame_timer.setTimerType(Qt.TimerType.PreciseTimer)  # 使用高精度定时器
                    self.marker_frame_timer.timeout.connect(self._advance_marker_frame)

                    # 计算实际帧延迟: 基础150ms * (100 / 速度)
                    marker_speed = self.config.get('marker_speed', 100)
                    base_delay = 150  # 基础延迟150ms
                    actual_delay = int(base_delay * (100 / marker_speed))
                    self.marker_frame_timer.setInterval(actual_delay)
                    self.marker_frame_timer.start()

                    self.logger.info(f"[GIF修复] 高精度定时器已启动，间隔={actual_delay}ms（使用预缓存帧）")

                else:
                    # GIF格式：也使用定时器手动控制帧（与WebP保持一致，避免QMovie的各种兼容性问题）
                    self.logger.info(f"[GIF播放] GIF格式，使用定时器手动控制帧")

                    # 创建高精度定时器手动控制帧切换
                    from PySide6.QtCore import QTimer, Qt
                    self.marker_frame_timer = QTimer(self)
                    self.marker_frame_timer.setTimerType(Qt.TimerType.PreciseTimer)
                    self.marker_frame_timer.timeout.connect(self._advance_marker_frame)

                    # 计算实际帧延迟: 基础150ms * (100 / 速度)
                    marker_speed = self.config.get('marker_speed', 100)
                    base_delay = 150  # 基础延迟150ms
                    actual_delay = int(base_delay * (100 / marker_speed))
                    self.marker_frame_timer.setInterval(actual_delay)
                    self.marker_frame_timer.start()

                    self.logger.info(f"[GIF播放] 高精度定时器已启动，间隔={actual_delay}ms（使用预缓存帧）")

                loop_count = self.marker_movie.loopCount()
                loop_info = "无限循环" if loop_count == -1 else f"{loop_count}次循环"
                self.logger.info(f"加载动画时间标记 ({ext}): {image_file}, 速度={marker_speed}%, {loop_info}")

            elif ext in ['.jpg', '.jpeg', '.png', '.webp']:
                # 静态图片(包括静态的 WebP)
                self.marker_pixmap = QPixmap(str(image_file))
                if self.marker_pixmap.isNull():
                    self.logger.error(f"无法加载图片: {image_file}")
                    self.marker_pixmap = None
                    self.config['marker_type'] = 'line'
                    return

                # 缩放到配置的大小,保持宽高比
                marker_size = self.config.get('marker_size', 100)
                self.marker_pixmap = self.marker_pixmap.scaled(
                    marker_size,
                    marker_size,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )

                self.logger.info(f"加载静态图片时间标记 ({ext}): {image_file}")
            else:
                self.logger.error(f"不支持的图片格式: {ext}")
                self.config['marker_type'] = 'line'

        except Exception as e:
            self.logger.error(f"加载时间标记图片失败: {e}", exc_info=True)
            self.config['marker_type'] = 'line'

    def calculate_time_range(self):
        """计算任务的紧凑排列映射

        将任务按时间顺序排列,计算每个任务在进度条上的位置
        忽略任务之间的时间间隔,所有任务紧密排列

        注意：在编辑模式下，使用temp_tasks而不是tasks，确保视觉反馈正确
        """
        # 在编辑模式下使用临时任务数据，否则使用实际任务数据
        # 使用hasattr检查edit_mode是否存在，避免初始化阶段的AttributeError
        tasks_to_use = self.temp_tasks if (hasattr(self, 'edit_mode') and self.edit_mode and self.temp_tasks) else self.tasks

        result = task_calculator.calculate_task_positions(tasks_to_use, self.logger)
        self.task_positions = result['task_positions']
        self.time_range_start = result['time_range_start']
        self.time_range_end = result['time_range_end']
        self.time_range_duration = result['time_range_duration']

    def save_config(self):
        """Persist current configuration to config.json."""
        try:
            config_file = self.app_dir / 'config.json'
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            self.logger.info("配置文件已更新")
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")

    def init_timer(self):
        """初始化定时器"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time_marker)
        # 使用配置文件中的更新间隔
        self.timer.start(self.config['update_interval'])

        # 立即更新一次,避免启动时等待
        self.update_time_marker()

        # 添加窗口可见性监控定时器(每500ms检查一次,提高响应速度)
        self.visibility_timer = QTimer(self)
        self.visibility_timer.timeout.connect(self.check_visibility)
        self.visibility_timer.start(500)  # 从1000ms优化到500ms

        # 添加窗口置顶刷新定时器(每3秒刷新一次,确保始终在最上层)
        self.topmost_timer = QTimer(self)
        self.topmost_timer.timeout.connect(self.refresh_topmost)
        self.topmost_timer.start(3000)  # 每3秒刷新一次置顶状态

        # 添加弹幕动画专用定时器(高频率更新,实现流畅动画,不影响其他功能)
        self.danmaku_animation_timer = QTimer(self)
        self.danmaku_animation_timer.timeout.connect(self.update_danmaku_animation)
        self.danmaku_animation_timer.start(16)  # 16ms ≈ 60fps, 电影级流畅度
        self.danmaku_last_update_time = time.time()  # 记录上次更新时间用于计算delta_time

    def check_visibility(self):
        """检查并确保窗口始终可见"""
        if not self.isVisible():
            self.logger.warning("检测到窗口不可见,强制显示")
            self.force_show()

    def refresh_topmost(self):
        """定期刷新窗口置顶状态,确保始终在最上层"""
        if platform.system() == 'Windows':
            try:
                hwnd = int(self.winId())
                window_utils.set_always_on_top(hwnd, True)
            except Exception as e:
                self.logger.debug(f"刷新置顶状态失败: {e}")

    def init_activity_tracker(self):
        """初始化行为追踪服务"""
        if self.activity_tracker:
            self.stop_activity_tracker()

        settings = self.config.get('activity_tracking', {})
        activity_tracking_enabled = settings.get('enabled', False)

        if not activity_tracking_enabled:
            self.logger.info("行为追踪服务已禁用")
            return

        from gaiya.services.activity_tracker import ActivityTracker

        polling_interval = max(1, int(settings.get('polling_interval', 5)))
        min_session_duration = max(1, int(settings.get('min_session_duration', 5)))

        self.logger.info(f"启动行为追踪服务 (间隔{polling_interval}s, 最短会话{min_session_duration}s)")
        self.activity_tracker = ActivityTracker(
            polling_interval=polling_interval,
            min_session_duration=min_session_duration
        )
        self.activity_tracker.session_ended.connect(self.on_activity_session_ended)
        self.activity_tracker.start()

    def stop_activity_tracker(self):
        """停止行为追踪服务"""
        if self.activity_tracker:
            self.logger.info("停止行为追踪服务")
            self.activity_tracker.stop()
            self.activity_tracker = None

    def on_activity_session_ended(self, process_name, window_title, duration):
        """处理行为会话结束事件"""
        self.logger.debug(f"行为会话结束: {process_name} - {duration}秒")
        # 这里可以添加实时UI更新逻辑
        pass

    def show_time_review_window(self):
        """显示时间回放窗口"""
        try:
            from gaiya.ui.time_review_window import TimeReviewWindow

            # 传递当前任务数据
            time_review_window = TimeReviewWindow(self)
            time_review_window.exec()

        except Exception as e:
            self.logger.error(f"显示时间回放窗口失败: {e}")
            QMessageBox.warning(self, "错误", f"无法打开时间回放窗口: {e}")

    def show_activity_settings_window(self):
        """显示行为识别设置窗口"""
        try:
            from gaiya.ui.activity_settings_window import ActivitySettingsWindow

            activity_settings_window = ActivitySettingsWindow(self)
            activity_settings_window.settings_changed.connect(self.on_activity_settings_changed)
            activity_settings_window.activity_tracking_toggled.connect(self.on_activity_tracking_toggled)
            activity_settings_window.exec()

        except Exception as e:
            self.logger.error(f"显示行为识别设置窗口失败: {e}")
            QMessageBox.warning(self, "错误", f"无法打开行为识别设置: {e}")

    def on_activity_settings_changed(self):
        """处理行为识别设置变更"""
        self.logger.info("行为识别设置已更新")

    def on_activity_tracking_toggled(self, enabled: bool):
        """处理行为识别开关变更"""
        self.logger.info(f"行为识别状态变更: {enabled}")
        # 重新初始化行为追踪服务
        if hasattr(self, 'activity_tracker') and self.activity_tracker:
            self.stop_activity_tracker()

        # 更新配置
        if 'activity_tracking' not in self.config:
            self.config['activity_tracking'] = {}
        self.config['activity_tracking']['enabled'] = enabled
        self.save_config()

        # 如果启用，延迟重新启动
        if enabled:
            QTimer.singleShot(2000, self.init_activity_tracker)

    def update_focus_state(self):
        """Update focus session state from database."""
        try:
            # Query active focus sessions
            self.active_focus_sessions = db.get_active_focus_sessions() or {}

            # Query completed focus sessions for today
            block_candidates = []
            query_ids = []
            for idx, task in enumerate(self.tasks):
                primary_id = generate_time_block_id(task, idx)
                legacy_ids = legacy_time_block_keys(task)
                block_candidates.append((primary_id, legacy_ids))
                query_ids.append(primary_id)
                query_ids.extend(legacy_ids)

            # 去重查询ID，避免SQL语句过长
            if query_ids:
                query_ids = list(dict.fromkeys(query_ids))
            completed_raw = db.get_completed_focus_sessions_for_blocks(query_ids)
            # Also get actual start times for completed sessions
            completed_with_times = db.get_completed_focus_sessions_with_time(query_ids)

            normalized_completed = set()
            task_focus_states = {}
            completed_start_times = {}
            for primary_id, legacy_ids in block_candidates:
                is_active = (
                    primary_id in self.active_focus_sessions or
                    any(key in self.active_focus_sessions for key in legacy_ids)
                )
                is_completed = (
                    primary_id in completed_raw or
                    any(key in completed_raw for key in legacy_ids)
                )

                if is_active:
                    task_focus_states[primary_id] = 'FOCUS_ACTIVE'
                elif is_completed:
                    task_focus_states[primary_id] = 'FOCUS_DONE'
                    normalized_completed.add(primary_id)
                    # Store actual start time
                    if primary_id in completed_with_times:
                        completed_start_times[primary_id] = completed_with_times[primary_id]
                    else:
                        # Check legacy IDs
                        for legacy_id in legacy_ids:
                            if legacy_id in completed_with_times:
                                completed_start_times[primary_id] = completed_with_times[legacy_id]
                                break
                else:
                    task_focus_states[primary_id] = 'NORMAL'

            self.completed_focus_blocks = normalized_completed
            self.task_focus_states = task_focus_states
            # Use task-specific completed times for task state (original logic)
            self.task_completed_focus_start_times = completed_start_times

            # Also load ALL completed focus sessions for today (for global fire markers)
            all_completed_today = db.get_all_completed_focus_sessions_today()
            self.completed_focus_start_times = all_completed_today

            # ✅ P1-1.5: 日志去重 - 只在专注记录数量变化时输出日志
            current_count = len(all_completed_today) if all_completed_today else 0

            if current_count != self._last_completed_count:
                # 状态发生变化,输出日志
                if all_completed_today:
                    self.logger.info(f"✅ 全局加载到 {len(all_completed_today)} 个已完成的专注记录")
                    for session_key, start_time in all_completed_today.items():
                        self.logger.info(f"  - {session_key}: {start_time.strftime('%H:%M:%S')}")
                else:
                    self.logger.info("📝 今日暂无已完成的专注记录")
                self._last_completed_count = current_count

            # 如果没有任务，确保状态被清空
            if not self.tasks:
                self.completed_focus_blocks = set()
                self.task_focus_states = {}

            # Check if focus mode timer finished
            if self.focus_mode and self.focus_start_time:
                from datetime import datetime
                elapsed_seconds = (datetime.now() - self.focus_start_time).total_seconds()
                total_seconds = self.focus_duration_minutes * 60

                if elapsed_seconds >= total_seconds:
                    # Focus timer finished
                    self._on_focus_timer_finished()

            # Trigger repaint to show updated focus state
            self.update()
        except Exception as e:
            self.logger.error(f"更新专注状态失败: {e}")

    def _render_focus_mode(self, painter, width, height, bar_y_offset, bar_height):
        """Render immersive focus mode progress bar."""
        from datetime import datetime

        # Calculate progress
        if not self.focus_start_time:
            return

        elapsed_seconds = (datetime.now() - self.focus_start_time).total_seconds()
        total_seconds = self.focus_duration_minutes * 60
        progress = min(1.0, elapsed_seconds / total_seconds)

        # Choose color based on focus type
        if self.focus_mode_type == 'work':
            # Red progress bar for work
            progress_color = QColor(255, 80, 50, 200)
            bg_color = QColor(50, 50, 50, 230)
        else:  # break
            # Green progress bar for break
            progress_color = QColor(76, 175, 80, 200)
            bg_color = QColor(50, 50, 50, 230)

        # Draw background
        painter.fillRect(0, bar_y_offset, width, bar_height, bg_color)

        # Draw progress
        progress_width = int(width * progress)
        painter.fillRect(0, bar_y_offset, progress_width, bar_height, progress_color)

        # Draw fire icon at progress position
        icon = "🔥" if self.focus_mode_type == 'work' else "☕"
        font = QFont("Segoe UI Emoji", 16, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))

        # Icon position: follows progress from left to right, moved up above the bar
        # Icon starts off-screen (negative x) at 0% and slides into view as progress increases
        icon_width = 25
        icon_height = 25
        # No min/max constraints - allow icon to start off-screen
        icon_x = progress_width - icon_width + 17  # Offset slightly to the right
        icon_y = bar_y_offset - icon_height + min(12, bar_height * 0.2) + 6
        icon_rect = QRectF(icon_x, icon_y, icon_width, icon_height)
        painter.drawText(icon_rect, Qt.AlignCenter, icon)

    def _update_focus_tooltip_text(self):
        """Update focus mode tooltip text with current progress."""
        from datetime import datetime

        if not self.focus_start_time:
            return

        elapsed_seconds = (datetime.now() - self.focus_start_time).total_seconds()
        elapsed_minutes = int(elapsed_seconds / 60)
        elapsed_secs = int(elapsed_seconds % 60)
        total_minutes = self.focus_duration_minutes

        # Build tooltip with task name, elapsed time, and total duration
        if self.focus_mode_type == 'work':
            tooltip_text = f"🔥 {self.focus_task_name} | {elapsed_minutes:02d}:{elapsed_secs:02d} / {total_minutes}:00"
        else:
            tooltip_text = f"☕ 休息中 | {elapsed_minutes:02d}:{elapsed_secs:02d} / {total_minutes}:00"

        # Always update tooltip to ensure it's fresh
        self.setToolTip(tooltip_text)

    def _start_focus_work(self, task):
        """Start focus work mode for a task."""
        from datetime import datetime

        task_name = task.get('task', 'Unknown Task')
        time_block_id = generate_time_block_id(task)
        self.logger.info(f"开启红温专注仓: {task_name}")

        # Hide pomodoro panel if exists
        if self.pomodoro_panel:
            self.pomodoro_panel.hide()
            self.pomodoro_panel = None

        # Create focus session in database
        self.focus_session_id = db.create_focus_session(time_block_id)

        # Set focus mode state
        self.focus_mode = True
        self.focus_mode_type = 'work'
        self.focus_start_time = datetime.now()
        self.focus_duration_minutes = 25
        self.focus_task_name = task_name

        # Update tray menu visibility
        self._update_tray_menu_for_focus_mode()

        # Trigger repaint
        self.update()

    def _on_focus_timer_finished(self):
        """Handle focus timer completion."""
        from datetime import datetime

        if self.focus_mode_type == 'work':
            # Work completed - mark session as completed
            if self.focus_session_id:
                db.complete_focus_session(self.focus_session_id)

            # Show notification
            self.show_notification(
                "✅ 专注完成!",
                f"已完成 {self.focus_duration_minutes} 分钟专注: {self.focus_task_name}\n\n开始 5 分钟休息"
            )

            # Start break
            self.focus_mode_type = 'break'
            self.focus_start_time = datetime.now()
            self.focus_duration_minutes = 5
            self.focus_session_id = None  # Break doesn't need session ID

            # Update tray menu to show skip break option
            self._update_tray_menu_for_focus_mode()
        else:
            # Break completed - return to normal mode
            self.show_notification(
                "✅ 休息完成!",
                "休息时间结束,恢复正常模式"
            )
            self._exit_focus_mode()

    def _end_focus_mode(self):
        """End focus mode with confirmation."""
        from datetime import datetime

        if not self.focus_mode:
            return

        # Calculate elapsed time
        elapsed_seconds = (datetime.now() - self.focus_start_time).total_seconds()
        elapsed_minutes = int(elapsed_seconds / 60)

        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "⚠️ 确认结束专注?",
            f"已专注 {elapsed_minutes} 分钟 / {self.focus_duration_minutes} 分钟\n\n确定要结束专注吗?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Interrupt session
            if self.focus_session_id:
                db.interrupt_focus_session(self.focus_session_id)

            self._exit_focus_mode()

    def _update_tray_menu_for_focus_mode(self):
        """Update tray menu visibility based on focus mode state."""
        if not hasattr(self, 'focus_work_action'):
            return

        if self.focus_mode:
            # In focus mode
            self.focus_work_action.setVisible(False)

            if self.focus_mode_type == 'work':
                # Work phase: show adjust and end actions
                self.adjust_focus_action.setVisible(True)
                self.end_focus_action.setVisible(True)
                self.skip_break_action.setVisible(False)
            elif self.focus_mode_type == 'break':
                # Break phase: show skip break action only
                self.adjust_focus_action.setVisible(False)
                self.end_focus_action.setVisible(False)
                self.skip_break_action.setVisible(True)
        else:
            # Not in focus mode: show start action, hide all others
            self.focus_work_action.setVisible(True)
            self.adjust_focus_action.setVisible(False)
            self.end_focus_action.setVisible(False)
            self.skip_break_action.setVisible(False)

    def _skip_break(self):
        """Skip break and return to normal mode."""
        self._exit_focus_mode()

    def _exit_focus_mode(self):
        """Exit focus mode and return to normal."""
        self.focus_mode = False
        self.focus_mode_type = None
        self.focus_start_time = None
        self.focus_session_id = None
        self.focus_task_name = None

        # Update tray menu visibility
        self._update_tray_menu_for_focus_mode()

        # Trigger repaint
        self.update()

    def _adjust_focus_duration(self):
        """Adjust focus duration while in focus mode."""
        from PySide6.QtWidgets import QInputDialog

        new_duration, ok = QInputDialog.getInt(
            self,
            "调整专注时长",
            "请输入新的专注时长 (分钟):",
            self.focus_duration_minutes,
            5,
            120,
            5
        )

        if ok:
            # Calculate remaining time with new duration
            from datetime import datetime
            elapsed_seconds = (datetime.now() - self.focus_start_time).total_seconds()
            elapsed_minutes = int(elapsed_seconds / 60)

            self.focus_duration_minutes = new_duration
            self.logger.info(f"专注时长调整为: {new_duration} 分钟 (已用: {elapsed_minutes} 分钟)")
            self.update()

    def show_notification(self, title, message):
        """Show system notification."""
        try:
            from PySide6.QtWidgets import QSystemTrayIcon
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.showMessage(title, message, QSystemTrayIcon.Information, 5000)
        except Exception as e:
            self.logger.error(f"显示通知失败: {e}")

    def show_time_review_window(self):
        """显示时间回放窗口"""
        try:
            from gaiya.ui.time_review_window import TimeReviewWindow

            # 传递当前任务数据
            time_review_window = TimeReviewWindow(self)
            time_review_window.exec()

        except Exception as e:
            self.logger.error(f"显示时间回放窗口失败: {e}")
            QMessageBox.warning(self, "错误", f"无法打开时间回放窗口: {e}")

    def show_activity_settings_window(self):
        """显示行为识别设置窗口"""
        try:
            from gaiya.ui.activity_settings_window import ActivitySettingsWindow

            activity_settings_window = ActivitySettingsWindow(self)
            activity_settings_window.settings_changed.connect(self.on_activity_settings_changed)
            activity_settings_window.activity_tracking_toggled.connect(self.on_activity_tracking_toggled)
            activity_settings_window.exec()

        except Exception as e:
            self.logger.error(f"显示行为识别设置窗口失败: {e}")
            QMessageBox.warning(self, "错误", f"无法打开行为识别设置: {e}")

    def on_activity_settings_changed(self):
        """处理行为识别设置变更"""
        self.logger.info("行为识别设置已更新")

    def on_activity_tracking_toggled(self, enabled: bool):
        """处理行为识别开关变更"""
        self.logger.info(f"行为识别状态变更: {enabled}")
        # 重新初始化行为追踪服务
        if hasattr(self, 'activity_tracker') and self.activity_tracker:
            self.stop_activity_tracker()

        # 更新配置
        if 'activity_tracking' not in self.config:
            self.config['activity_tracking'] = {}
        self.config['activity_tracking']['enabled'] = enabled

        # 如果启用，延迟重新启动
        if enabled:
            QTimer.singleShot(2000, self.init_activity_tracker)

    def init_tray(self):
        """初始化系统托盘图标"""
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)

        # 使用自定义图标
        from PySide6.QtGui import QIcon
        from gaiya.utils.path_utils import get_resource_path

        icon_path = get_resource_path("gaiya-logo2-wbk.png")
        icon = QIcon(str(icon_path))
        if icon.isNull():
            # 如果自定义图标加载失败，使用Qt内置图标作为后备
            icon = self.style().standardIcon(
                self.style().StandardPixmap.SP_ComputerIcon
            )
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip(tr('tray.tooltip'))

        # 创建右键菜单
        tray_menu = QMenu()

        # 优化托盘菜单样式（增加间距和内边距）
        tray_menu.setStyleSheet("""
            QMenu {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                padding: 6px 0;
            }
            QMenu::item {
                padding: 8px 30px 8px 20px;
                color: #333333;
            }
            QMenu::item:selected {
                background-color: #F5F5F5;
            }
            QMenu::separator {
                height: 1px;
                background-color: #E0E0E0;
                margin: 8px 12px;
            }
        """)

        # Edit task time action (dynamic text)
        self.edit_mode_action = QAction(tr('menu.edit_task_time'), self)
        self.edit_mode_action.triggered.connect(self.toggle_edit_mode)
        tray_menu.addAction(self.edit_mode_action)

        # Save/Cancel actions (only visible in edit mode)
        self.save_edit_action = QAction(tr('menu.save_changes'), self)
        self.save_edit_action.triggered.connect(self.save_edit_changes)
        self.save_edit_action.setVisible(False)
        tray_menu.addAction(self.save_edit_action)

        self.cancel_edit_action = QAction(tr('menu.cancel_edit'), self)
        self.cancel_edit_action.triggered.connect(self.cancel_edit)
        self.cancel_edit_action.setVisible(False)
        tray_menu.addAction(self.cancel_edit_action)

        tray_menu.addSeparator()

        # Open config action
        config_action = QAction(tr('menu.config'), self)
        config_action.triggered.connect(self.open_config_gui)
        tray_menu.addAction(config_action)

        # Time review action
        time_review_action = QAction("⏰ 今日时间回放", self)
        time_review_action.triggered.connect(self.show_time_review_window)
        tray_menu.addAction(time_review_action)

        # Task completion review action
        # 注释掉: 已集成到统计报告界面,不需要独立入口
        # task_review_action = QAction("✅ 任务完成回顾", self)
        # task_review_action.triggered.connect(self.show_today_task_review)
        # tray_menu.addAction(task_review_action)

        # Focus work action (红温专注仓)
        self.focus_work_action = QAction("🔥 开启红温专注仓", self)
        self.focus_work_action.triggered.connect(self.start_focus_from_tray)
        tray_menu.addAction(self.focus_work_action)

        # Focus mode controls (only visible when in focus mode)
        self.adjust_focus_action = QAction("⏱️ 调整专注时长", self)
        self.adjust_focus_action.triggered.connect(self._adjust_focus_duration)
        self.adjust_focus_action.setVisible(False)
        tray_menu.addAction(self.adjust_focus_action)

        self.end_focus_action = QAction("⏹️ 结束专注", self)
        self.end_focus_action.triggered.connect(self._end_focus_mode)
        self.end_focus_action.setVisible(False)
        tray_menu.addAction(self.end_focus_action)

        self.skip_break_action = QAction("⏭️ 跳过休息", self)
        self.skip_break_action.triggered.connect(self._skip_break)
        self.skip_break_action.setVisible(False)
        tray_menu.addAction(self.skip_break_action)

        # Statistics report
        statistics_action = QAction(tr('menu.statistics'), self)
        statistics_action.triggered.connect(self.show_statistics)
        tray_menu.addAction(statistics_action)

        # Scene editor
        scene_editor_action = QAction(tr('menu.scene_editor'), self)
        scene_editor_action.triggered.connect(self.open_scene_editor)
        tray_menu.addAction(scene_editor_action)

        tray_menu.addSeparator()

        # Reload config action
        reload_action = QAction(tr('menu.reload_config'), self)
        reload_action.triggered.connect(self.reload_all)
        tray_menu.addAction(reload_action)

        tray_menu.addSeparator()

        # Quit action
        quit_action = QAction(tr('menu.quit'), self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)

        # 绑定左键点击事件：点击托盘图标打开配置管理器
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

        self.tray_icon.show()

    def on_tray_icon_activated(self, reason):
        """
        托盘图标点击事件处理

        Args:
            reason: 点击类型（QSystemTrayIcon.ActivationReason）
        """
        # 左键单击：打开配置管理器
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.logger.info("托盘图标左键点击：打开配置管理器")
            self.open_config_gui()
        # 双击：也打开配置管理器
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.logger.info("托盘图标双击：打开配置管理器")
            self.open_config_gui()
        # 右键已经由 setContextMenu 处理，无需额外操作

    def init_notification_manager(self):
        """初始化通知管理器"""
        self.notification_manager = NotificationManager(
            self.config,
            self.tasks,
            self.tray_icon,
            self.logger
        )
        self.logger.info("通知管理器初始化完成")

    def init_statistics_manager(self):
        """初始化统计管理器"""
        self.statistics_manager = StatisticsManager(
            self.app_dir,
            self.logger
        )
        self.logger.info("统计管理器初始化完成")

    def init_task_tracking_system(self):
        """初始化任务完成追踪系统"""
        self.logger.info("="*60)
        self.logger.info("开始初始化任务完成追踪系统...")
        self.logger.info("="*60)
        try:
            self.logger.info("正在导入任务追踪系统模块...")
            from gaiya.utils.data_migration import DataMigration
            from gaiya.services.user_behavior_model import UserBehaviorModel
            from gaiya.services.task_inference_engine import SignalCollector, InferenceEngine
            from gaiya.services.task_completion_scheduler import TaskCompletionScheduler
            self.logger.info("模块导入成功")

            # 运行数据迁移检查
            self.logger.info("开始数据迁移检查...")
            migration = DataMigration(db, self.app_dir)
            if not migration.check_and_run_migrations():
                self.logger.warning("任务完成追踪系统初始化失败")
                return

            self.logger.info("任务完成追踪系统数据迁移完成")

            # 初始化用户行为模型
            model_path = self.app_dir / "user_behavior_model.json"
            self.behavior_model = UserBehaviorModel(model_path)
            self.logger.info("用户行为模型已加载")

            # 初始化推理引擎
            signal_collector = SignalCollector(db, self.behavior_model)
            self.inference_engine = InferenceEngine(signal_collector)
            self.logger.info("任务推理引擎已初始化")

            # 初始化调度器
            scheduler_config = self.config.get('task_completion_scheduler', {})
            self.task_completion_scheduler = TaskCompletionScheduler(
                db_manager=db,
                behavior_model=self.behavior_model,
                inference_engine=self.inference_engine,
                config=scheduler_config,
                ui_trigger_callback=self.show_task_review_window
            )

            # 连接任务回顾信号到槽（确保在主线程中显示UI）
            self.task_review_requested.connect(self._show_task_review_window_slot)

            # 启动调度器
            self.task_completion_scheduler.start()
            self.logger.info("任务完成推理调度器已启动")

            # 初始化自动推理引擎 (方案A: 全自动推理模式)
            self.logger.info("开始初始化自动推理引擎...")
            from gaiya.core.auto_inference_engine import AutoInferenceEngine

            self.auto_inference_engine = AutoInferenceEngine(
                db_manager=db,
                behavior_analyzer=None,  # 可选,未来可集成
                interval_minutes=5       # 每5分钟推理一次
            )

            # 连接信号槽
            self.auto_inference_engine.inference_completed.connect(self._on_inference_completed)
            self.auto_inference_engine.inference_failed.connect(self._on_inference_failed)

            # 启动引擎
            self.auto_inference_engine.start()
            self.logger.info("自动推理引擎已启动 (间隔: 5分钟)")

        except Exception as e:
            self.logger.error(f"任务完成追踪系统初始化异常: {e}", exc_info=True)

    def send_test_notification(self):
        """发送测试通知"""
        if hasattr(self, 'notification_manager'):
            self.notification_manager.send_test_notification()
        else:
            self.logger.warning("通知管理器未初始化")

    def show_notification_history(self):
        """显示通知历史"""
        if not hasattr(self, 'notification_manager'):
            self.tray_icon.showMessage(
                "PyDayBar",
                "通知管理器未初始化",
                QSystemTrayIcon.Information,
                3000
            )
            return

        history = self.notification_manager.get_notification_history()

        if not history:
            self.tray_icon.showMessage(
                "PyDayBar 通知历史",
                "暂无通知记录",
                QSystemTrayIcon.Information,
                3000
            )
            return

        # 格式化历史记录
        history_text = "\n".join([
            f"[{item['time']}] {item['title']}"
            for item in history[-5:]  # 只显示最近5条
        ])

        self.tray_icon.showMessage(
            "PyDayBar 通知历史",
            f"最近的通知:\n{history_text}",
            QSystemTrayIcon.Information,
            5000
        )

    def start_focus_from_tray(self):
        """从托盘启动红温专注仓 - 使用当前时间块"""
        try:
            # Check if already in focus mode
            if self.focus_mode:
                self.tray_icon.showMessage(
                    "红温专注仓",
                    "已在专注模式中",
                    QSystemTrayIcon.Information,
                    3000
                )
                return

            # Find current task at current time
            from datetime import datetime
            now = datetime.now()
            current_hour = now.hour
            current_minute = now.minute
            current_time_minutes = current_hour * 60 + current_minute

            current_task = None
            for task in self.tasks:
                start_parts = task['start'].split(':')
                end_parts = task['end'].split(':')

                start_minutes = int(start_parts[0]) * 60 + int(start_parts[1])
                end_minutes = int(end_parts[0]) * 60 + int(end_parts[1])

                # Handle overnight tasks
                if end_minutes <= start_minutes:
                    end_minutes += 24 * 60
                    if current_time_minutes < start_minutes:
                        current_time_minutes += 24 * 60

                if start_minutes <= current_time_minutes < end_minutes:
                    current_task = task
                    break

            if not current_task:
                self.tray_icon.showMessage(
                    "红温专注仓",
                    "当前时间没有对应的任务块",
                    QSystemTrayIcon.Warning,
                    3000
                )
                return

            # Start focus work with current task
            self._start_focus_work(current_task)

            # Show notification
            self.tray_icon.showMessage(
                "红温专注仓",
                f"为「{current_task.get('task', '未知任务')}」开启了红温专注仓 (25分钟)",
                QSystemTrayIcon.Information,
                3000
            )

        except Exception as e:
            self.logger.error(f"从托盘启动红温专注仓失败: {e}", exc_info=True)
            self.tray_icon.showMessage(
                "错误",
                f"启动红温专注仓失败: {str(e)}",
                QSystemTrayIcon.Critical,
                5000
            )

    def start_pomodoro(self):
        """启动番茄钟"""
        try:
            # 如果已经有番茄钟面板在运行,显示提示
            if self.pomodoro_panel is not None and self.pomodoro_panel.isVisible():
                self.tray_icon.showMessage(
                    "番茄钟",
                    "番茄钟已在运行中",
                    QSystemTrayIcon.Information,
                    3000
                )
                return

            # 创建番茄钟面板
            self.pomodoro_panel = PomodoroPanel(
                self.config,
                self.tray_icon,
                self.logger,
                parent=None  # 独立窗口
            )

            # 连接关闭信号
            self.pomodoro_panel.closed.connect(self.on_pomodoro_closed)

            # 定位面板(在进度条上方)
            self.pomodoro_panel.position_above_progress_bar(self)

            # 显示面板
            self.pomodoro_panel.show()

            # 自动开始工作
            self.pomodoro_panel.start_work()

            self.logger.info("番茄钟面板已启动")

        except Exception as e:
            self.logger.error(f"启动番茄钟失败: {e}", exc_info=True)
            self.tray_icon.showMessage(
                "错误",
                f"启动番茄钟失败: {str(e)}",
                QSystemTrayIcon.Critical,
                5000
            )

    def on_pomodoro_closed(self):
        """番茄钟面板关闭时的回调"""
        self.logger.info("番茄钟面板已关闭")
        self.pomodoro_panel = None

    def show_today_task_review(self):
        """从托盘菜单显示今日任务回顾"""
        try:
            from datetime import datetime

            # 获取今日日期
            today = datetime.now().strftime('%Y-%m-%d')

            # 获取所有任务(不仅仅是未确认的)
            all_tasks = db.get_today_task_completions(today)

            if not all_tasks:
                self.tray_icon.showMessage(
                    "任务完成回顾",
                    f"今天({today})还没有任务完成记录\n\n提示: 系统会在每天 {self.config.get('task_completion_scheduler', {}).get('trigger_time', '21:00')} 自动推理任务完成情况",
                    QSystemTrayIcon.Information,
                    5000
                )
                return

            # 显示回顾窗口
            self.show_task_review_window(today, all_tasks)

        except Exception as e:
            self.logger.error(f"显示今日任务回顾失败: {e}", exc_info=True)
            self.tray_icon.showMessage(
                "错误",
                f"显示任务回顾失败: {str(e)}",
                QSystemTrayIcon.Critical,
                3000
            )

    def show_task_review_window(self, date: str, unconfirmed_tasks: list):
        """
        显示任务完成回顾窗口（线程安全版本）

        此方法可能从工作线程调用，因此发射信号到主线程处理

        Args:
            date: 日期 (YYYY-MM-DD)
            unconfirmed_tasks: 未确认的任务列表
        """
        try:
            # 发射信号，让主线程显示窗口（避免跨线程UI操作）
            self.task_review_requested.emit(date, unconfirmed_tasks)
            self.logger.info(f"任务回顾请求已发送: {date}, {len(unconfirmed_tasks)} 个任务")

        except Exception as e:
            self.logger.error(f"发送任务回顾请求失败: {e}", exc_info=True)

    def _show_task_review_window_slot(self, date: str, unconfirmed_tasks: list):
        """
        实际显示任务回顾窗口（槽函数，在主线程中执行）

        Args:
            date: 日期 (YYYY-MM-DD)
            unconfirmed_tasks: 未确认的任务列表
        """
        try:
            from gaiya.ui.task_review_window import TaskReviewWindow

            # 创建回顾窗口（现在在主线程中）
            review_window = TaskReviewWindow(
                date=date,
                task_completions=unconfirmed_tasks,
                on_confirm=self.on_task_review_confirmed,
                parent=self  # 设置父窗口为主窗口
            )

            # 显示窗口（非模态）
            review_window.show()

            self.logger.info(f"任务回顾窗口已显示: {date}, {len(unconfirmed_tasks)} 个任务")

        except Exception as e:
            self.logger.error(f"显示任务回顾窗口失败: {e}", exc_info=True)

    def on_task_review_confirmed(self, results: list):
        """
        任务回顾确认回调

        Args:
            results: 确认结果列表
                [{
                    'completion_id': str,
                    'new_completion': int,
                    'original_completion': int,
                    'is_modified': bool,
                    'note': str
                }]
        """
        try:
            modified_count = 0
            learned_count = 0

            for result in results:
                completion_id = result['completion_id']
                new_completion = result['new_completion']
                is_modified = result['is_modified']

                if is_modified:
                    # 用户修改了完成度
                    original_completion = result['original_completion']

                    # 更新数据库
                    db.confirm_task_completion(
                        completion_id=completion_id,
                        new_completion=new_completion,
                        note=result.get('note', '')
                    )

                    modified_count += 1

                    # 触发学习反馈
                    # 获取任务详情用于学习
                    task_completion = db.get_task_completion(completion_id)
                    if task_completion:
                        self._trigger_learning_from_correction(
                            task_completion,
                            original_completion,
                            new_completion
                        )
                        learned_count += 1

                else:
                    # 用户未修改,直接确认
                    db.update_task_completion_confirmation(
                        completion_id=completion_id,
                        user_confirmed=True,
                        user_corrected=False
                    )

            self.logger.info(
                f"任务回顾完成: 共 {len(results)} 个任务, "
                f"修改 {modified_count} 个, 学习 {learned_count} 个"
            )

        except Exception as e:
            self.logger.error(f"任务回顾确认处理失败: {e}", exc_info=True)

    def _trigger_learning_from_correction(self, task_completion: dict,
                                         original_completion: int,
                                         new_completion: int):
        """
        从用户修正中触发学习

        Args:
            task_completion: 任务完成记录
            original_completion: AI推理的原始完成度
            new_completion: 用户修正后的完成度
        """
        try:
            # 判断修正类型
            if new_completion > original_completion + 10:
                correction_type = 'underestimated'
            elif new_completion < original_completion - 10:
                correction_type = 'overestimated'
            else:
                correction_type = 'accurate'

            # 解析推理数据,获取使用的应用列表
            import json
            inference_data = json.loads(task_completion.get('inference_data', '{}'))
            details = inference_data.get('details', {})

            # 构建应用使用列表
            apps_used = []

            # 从主要应用中提取
            primary_apps = details.get('primary_apps', [])
            for app_str in primary_apps:
                # 格式: "Cursor.exe(90min)"
                import re
                match = re.match(r'(.+?)\((\d+)min\)', app_str)
                if match:
                    app_name = match.group(1)
                    duration = int(match.group(2))
                    apps_used.append({'app': app_name, 'duration': duration})

            # 调用行为模型学习
            if apps_used:
                self.behavior_model.learn_from_correction(
                    task_name=task_completion['task_name'],
                    apps_used=apps_used,
                    correction_type=correction_type
                )

                self.logger.info(
                    f"学习反馈: {task_completion['task_name']} - {correction_type}, "
                    f"{len(apps_used)} 个应用"
                )

        except Exception as e:
            self.logger.error(f"学习反馈失败: {e}", exc_info=True)

    def _on_inference_completed(self, inferred_tasks: list):
        """
        自动推理完成回调 (方案A)

        Args:
            inferred_tasks: 推理任务列表
                [{
                    'name': str,
                    'type': str,
                    'confidence': float,
                    'start_time': str,
                    'end_time': str,
                    'duration_minutes': int,
                    'apps': list,
                    'auto_generated': bool
                }]
        """
        try:
            self.logger.info(f"[自动推理] 推理完成: {len(inferred_tasks)} 个任务")

            # 记录推理摘要
            if inferred_tasks:
                avg_confidence = sum(t['confidence'] for t in inferred_tasks) / len(inferred_tasks)
                self.logger.info(
                    f"[自动推理] 平均置信度: {avg_confidence:.1%}, "
                    f"任务类型分布: {self._get_task_type_summary(inferred_tasks)}"
                )

            # TODO: 未来可以在这里添加通知功能
            # 例如: 推理出重要任务时,发送托盘通知

        except Exception as e:
            self.logger.error(f"[自动推理] 处理推理结果失败: {e}", exc_info=True)

    def _on_inference_failed(self, error_msg: str):
        """
        自动推理失败回调 (方案A)

        Args:
            error_msg: 错误信息
        """
        self.logger.error(f"[自动推理] 推理失败: {error_msg}")

        # TODO: 未来可以添加错误通知
        # 例如: 连续失败3次以上时,发送托盘通知

    def _get_task_type_summary(self, tasks: list) -> str:
        """
        获取任务类型分布摘要

        Args:
            tasks: 任务列表

        Returns:
            类型分布摘要字符串,如: "work:3, learning:1"
        """
        from collections import Counter
        type_counts = Counter(task['type'] for task in tasks)
        return ", ".join(f"{t}:{c}" for t, c in type_counts.items())

    def show_statistics(self):
        """显示统计报告窗口"""
        try:
            # 统计报告功能对所有用户开放
            # 如果窗口已经打开,则激活它
            if self.statistics_window is not None and self.statistics_window.isVisible():
                self.statistics_window.activateWindow()
                self.statistics_window.raise_()
                return

            # 导入统计GUI
            from statistics_gui import StatisticsWindow

            # 创建统计窗口 (不设置parent,避免成为子窗口导致其他窗口关闭)
            self.statistics_window = StatisticsWindow(
                self.statistics_manager,
                self.logger,
                parent=None  # 设置为None,使其成为独立的顶层窗口
            )

            # 保存主窗口引用,以便访问task_completion_scheduler和open_config_gui
            self.statistics_window.main_window = self

            # 连接关闭信号
            self.statistics_window.closed.connect(self.on_statistics_closed)

            # 显示窗口
            self.statistics_window.show()

            self.logger.info("统计报告窗口已打开")

        except Exception as e:
            self.logger.error(f"打开统计报告窗口失败: {e}", exc_info=True)
            self.tray_icon.showMessage(
                "错误",
                f"打开统计报告失败: {str(e)}",
                QSystemTrayIcon.Critical,
                5000
            )

    def on_statistics_closed(self):
        """统计窗口关闭时的回调"""
        self.logger.info("统计报告窗口已关闭")
        self.statistics_window = None

    def open_scene_editor(self):
        """打开场景编辑器窗口"""
        try:
            # 如果窗口已经打开,则激活它
            if self.scene_editor_window is not None and self.scene_editor_window.isVisible():
                self.scene_editor_window.activateWindow()
                self.scene_editor_window.raise_()
                self.logger.info("场景编辑器窗口已激活")
                return

            # 创建场景编辑器窗口
            self.scene_editor_window = SceneEditorWindow()

            # 连接关闭信号
            self.scene_editor_window.editor_closed.connect(self.on_scene_editor_closed)

            # 显示窗口
            self.scene_editor_window.show()

            self.logger.info("场景编辑器窗口已打开")

        except Exception as e:
            self.logger.error(f"打开场景编辑器失败: {e}", exc_info=True)
            self.tray_icon.showMessage(
                "错误",
                f"打开场景编辑器失败: {str(e)}",
                QSystemTrayIcon.Critical,
                5000
            )

    def on_scene_editor_closed(self):
        """场景编辑器窗口关闭时的回调"""
        self.logger.info("场景编辑器窗口已关闭")
        self.scene_editor_window = None
        # 刷新主窗口的场景列表（用户可能添加/修改了场景）
        if hasattr(self, 'scene_manager'):
            self.scene_manager.refresh_scenes()
            self.logger.info("已刷新场景列表")

    def open_config_gui(self, initial_tab=0):
        """打开配置界面

        Args:
            initial_tab: 初始显示的标签页索引（0=基本设置, 1=任务管理, 2=个人中心, etc.）
        """
        try:
            # 使用已导入的 ConfigManager（在文件顶部已导入）
            # 如果已经打开,则显示现有窗口
            if hasattr(self, 'config_window') and self.config_window.isVisible():
                self.config_window.activateWindow()
                self.config_window.raise_()
                # 切换到指定标签页
                if hasattr(self.config_window, 'tab_widget'):
                    self.config_window.tab_widget.setCurrentIndex(initial_tab)
                return

            # 创建新窗口（传递主窗口引用以便访问 scene_manager）
            self.config_window = ConfigManager(main_window=self)
            self.config_window.config_saved.connect(self.reload_all)
            self.config_window.show()

            # 切换到指定标签页
            if hasattr(self.config_window, 'tab_widget'):
                from PySide6.QtCore import QTimer
                # 延迟切换，确保窗口完全显示
                QTimer.singleShot(100, lambda: self.config_window.tab_widget.setCurrentIndex(initial_tab))

            self.logger.info(f"配置界面已打开 (标签页={initial_tab})")

        except Exception as e:
            self.logger.error(f"打开配置界面失败: {e}", exc_info=True)
            # 如果导入失败,显示错误消息
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                None,
                "错误",
                f"无法打开配置界面:\n{str(e)}\n\n请确保 config_gui.py 文件存在。"
            )

    def reload_all(self):
        """重载配置和任务"""
        self.logger.info("开始重载配置和任务...")
        self.logger.info(f"[reload_all] 当前任务数量: {len(self.tasks)}")
        old_height = self.config.get('bar_height', 20)
        old_position = self.config.get('position', 'bottom')
        old_screen_index = self.config.get('screen_index', 0)

        # 保存旧的场景启用状态
        old_scene_enabled = self.scene_manager.is_enabled()
        old_scene_id = None
        if old_scene_enabled:
            scene_config = self.scene_manager.get_current_scene_config()
            if scene_config:
                old_scene_id = scene_config.scene_id

        # 保存旧的动画配置
        old_marker_type = self.config.get('marker_type', 'gif')
        old_marker_image = self.config.get('marker_image_path', '')
        old_marker_size = self.config.get('marker_size', 40)

        # 保存旧的弹幕配置
        old_danmaku_enabled = False
        if hasattr(self, 'danmaku_manager'):
            old_danmaku_enabled = self.danmaku_manager.enabled

        # 重新加载配置和任务
        self.config = data_loader.load_config(self.app_dir, self.logger)
        self.tasks = data_loader.load_tasks(self.app_dir, self.logger)
        self.logger.info(f"[reload_all] 重新加载后任务数量: {len(self.tasks)}")
        if len(self.tasks) > 0:
            self.logger.info(f"[reload_all] 第一个任务: {self.tasks[0].get('task', 'unknown')}")

        # 重新加载预设管理器配置(配置文件可能包含新的预设ID)
        if hasattr(self, 'marker_preset_manager'):
            self.marker_preset_manager.load_from_config(self.config)

        # 检查动画配置是否改变
        new_marker_type = self.config.get('marker_type', 'gif')
        new_marker_image = self.config.get('marker_image_path', '')
        new_marker_size = self.config.get('marker_size', 40)

        marker_config_changed = (
            old_marker_type != new_marker_type or
            old_marker_image != new_marker_image or
            old_marker_size != new_marker_size
        )

        # 只有当动画配置真的改变时才重新初始化，避免中断正在播放的动画
        if marker_config_changed:
            self.logger.info(f"检测到动画配置变化，重新初始化动画")
            self.init_marker_image()
        else:
            self.logger.debug(f"动画配置未变化，跳过重新初始化")

        # 重新计算时间范围
        self.calculate_time_range()
        self.logger.info(f"[reload_all] 重新计算时间范围后task_positions数量: {len(self.task_positions)}")

        # 重新加载通知管理器配置
        if hasattr(self, 'notification_manager'):
            self.notification_manager.reload_config(self.config, self.tasks)

        # 重新加载弹幕管理器配置
        if hasattr(self, 'danmaku_manager'):
            self.danmaku_manager.reload_config(self.config)

        # 检查弹幕启用状态是否改变
        new_danmaku_enabled = False
        if hasattr(self, 'danmaku_manager'):
            new_danmaku_enabled = self.danmaku_manager.enabled
        danmaku_changed = (old_danmaku_enabled != new_danmaku_enabled)

        # 如果高度、位置、屏幕索引、场景启用状态或弹幕启用状态改变,需要重新设置窗口几何
        new_height = self.config.get('bar_height', 20)
        new_position = self.config.get('position', 'bottom')
        new_screen_index = self.config.get('screen_index', 0)

        # 检查场景启用状态是否改变
        new_scene_enabled = self.scene_manager.is_enabled()
        new_scene_id = None
        if new_scene_enabled:
            scene_config = self.scene_manager.get_current_scene_config()
            if scene_config:
                new_scene_id = scene_config.scene_id

        scene_changed = (old_scene_enabled != new_scene_enabled or old_scene_id != new_scene_id)

        if (old_height != new_height or
            old_position != new_position or
            old_screen_index != new_screen_index or
            scene_changed or
            danmaku_changed):
            self.logger.info(f"检测到几何变化: 高度 {old_height}->{new_height}, 位置 {old_position}->{new_position}, 屏幕 {old_screen_index}->{new_screen_index}, 场景 {old_scene_enabled}/{old_scene_id}->{new_scene_enabled}/{new_scene_id}, 弹幕 {old_danmaku_enabled}->{new_danmaku_enabled}")
            # 重新设置窗口几何
            self.setup_geometry()

        # 更新定时器间隔
        self.timer.setInterval(self.config['update_interval'])

        # 重新应用主题（确保主题配置立即生效）
        if hasattr(self, 'theme_manager') and self.theme_manager:
            # 重新加载主题管理器的配置
            self.theme_manager._load_current_theme()
            # 应用主题到进度条
            self.apply_theme()

        # 重新加载场景配置
        if hasattr(self, 'scene_manager'):
            self.scene_manager.load_config(self.config)
            # 如果场景系统已启用，重新加载当前场景
            if self.scene_manager.is_enabled() and self.scene_manager.get_current_scene_name():
                scene_name = self.scene_manager.get_current_scene_name()
                self.load_scene(scene_name)

        # 触发重绘
        self.update()
        self.logger.info("[reload_all] 已调用update()触发重绘")
        self.logger.info("配置和任务重载完成")

    def load_scene(self, scene_name: str):
        """加载场景配置并准备资源

        Args:
            scene_name: 场景名称（对应scenes/目录下的文件夹名）
        """
        try:
            # 使用SceneManager加载场景
            scene_config = self.scene_manager.load_scene(scene_name)

            if not scene_config:
                self.logger.error(f"场景加载失败: {scene_name}")
                return False

            # 设置场景到渲染器和事件管理器
            self.scene_renderer.set_scene(scene_config)
            self.scene_event_manager.set_scene(scene_config)

            # 预加载场景资源
            self.scene_renderer.prepare_resources()

            # 触发重绘以显示场景
            self.update()

            self.logger.info(f"场景加载成功: {scene_name}")
            return True

        except Exception as e:
            self.logger.error(f"加载场景时出错: {e}", exc_info=True)
            return False

    def unload_scene(self):
        """卸载当前场景"""
        self.scene_manager.unload_scene()
        self.logger.info("场景已卸载")
        self.update()

    def toggle_edit_mode(self):
        """切换编辑模式"""
        if self.edit_mode:
            # 退出编辑模式（相当于取消）
            self.cancel_edit()
        else:
            # 进入编辑模式
            self.enter_edit_mode()

    def enter_edit_mode(self):
        """进入编辑模式"""
        self.logger.info("进入编辑模式")
        self.edit_mode = True

        # 创建临时任务副本
        import copy
        self.temp_tasks = copy.deepcopy(self.tasks)

        # 更新菜单文字
        self.edit_mode_action.setText(tr('menu.exit_edit_mode'))
        self.save_edit_action.setVisible(True)
        self.cancel_edit_action.setVisible(True)

        # 显示提示
        self.tray_icon.showMessage(
            "编辑模式",
            "进入编辑模式\n拖拽任务边缘调整时间\n完成后请到托盘菜单保存",
            QSystemTrayIcon.Information,
            3000
        )

        # 刷新显示
        self.update()

    def save_edit_changes(self):
        """保存编辑的修改"""
        if not self.edit_mode or self.temp_tasks is None:
            return

        self.logger.info("保存任务时间修改")

        try:
            # 将临时任务数据写入tasks.json
            tasks_file = self.app_dir / 'tasks.json'
            with open(tasks_file, 'w', encoding='utf-8') as f:
                json.dump(self.temp_tasks, f, indent=4, ensure_ascii=False)

            # 更新当前任务数据
            self.tasks = copy.deepcopy(self.temp_tasks)

            # 重新计算时间范围
            self.calculate_time_range()

            # 退出编辑模式
            self.exit_edit_mode()

            # 显示成功提示
            self.tray_icon.showMessage(
                "保存成功",
                "任务时间已保存",
                QSystemTrayIcon.Information,
                2000
            )

            self.logger.info("任务时间保存成功")

        except Exception as e:
            self.logger.error(f"保存任务时间失败: {e}", exc_info=True)
            self.tray_icon.showMessage(
                "保存失败",
                f"保存失败: {str(e)}",
                QSystemTrayIcon.Critical,
                5000
            )

    def cancel_edit(self):
        """取消编辑"""
        if not self.edit_mode:
            return

        self.logger.info("取消编辑")

        # 丢弃临时数据
        self.temp_tasks = None

        # 退出编辑模式
        self.exit_edit_mode()

        # 显示提示
        self.tray_icon.showMessage(
            "已取消",
            "已取消编辑，未保存修改",
            QSystemTrayIcon.Information,
            2000
        )

    def exit_edit_mode(self):
        """退出编辑模式（内部方法）"""
        self.edit_mode = False
        self.dragging = False
        self.drag_task_index = -1
        self.drag_edge = None
        self.hover_edge = None

        # Restore menu text
        self.edit_mode_action.setText(tr('menu.edit_task_time'))
        self.save_edit_action.setVisible(False)
        self.cancel_edit_action.setVisible(False)

        # 刷新显示
        self.update()

    def init_file_watcher(self):
        """初始化文件监视器"""
        # 禁用文件监视器以避免Windows上QFileSystemWatcher的bug
        # 该bug会导致fileChanged信号被反复触发（每300ms一次），造成动画卡顿
        # 用户可以通过重启应用或使用配置窗口来重新加载配置
        self.logger.info("文件监视器已禁用（避免Windows QFileSystemWatcher bug导致的动画卡顿）")
        return

        # 以下代码已禁用
        self.file_watcher = QFileSystemWatcher(self)

        # 获取文件路径
        tasks_file = str(self.app_dir / 'tasks.json')
        config_file = str(self.app_dir / 'config.json')

        # 添加到监视列表
        self.file_watcher.addPath(tasks_file)
        self.file_watcher.addPath(config_file)

        # 连接信号
        self.file_watcher.fileChanged.connect(self.on_file_changed)
        self.logger.info("文件监视器已启动")

    def on_file_changed(self, path):
        """文件变化时的回调"""
        self.logger.info(f"检测到文件变化: {path}")

        # 防止重复触发: 使用定时器去抖
        if hasattr(self, '_reload_timer') and self._reload_timer.isActive():
            self.logger.debug(f"重载定时器已激活，重置定时器")
            self._reload_timer.stop()

        # Windows 某些编辑器会先删除再创建文件
        # 需要重新添加到监视列表
        # 注意：重新添加可能会触发新的fileChanged信号，导致无限循环
        # 所以只在文件真正不存在于监视列表时才添加
        tasks_file = str(self.app_dir / 'tasks.json')
        config_file = str(self.app_dir / 'config.json')

        current_files = self.file_watcher.files()

        # 只有当文件确实不在监视列表中，且文件确实存在时，才重新添加
        import os
        if tasks_file not in current_files and os.path.exists(tasks_file):
            self.logger.warning(f"文件被移出监视列表，重新添加: {tasks_file}")
            self.file_watcher.addPath(tasks_file)
        if config_file not in current_files and os.path.exists(config_file):
            self.logger.warning(f"文件被移出监视列表，重新添加: {config_file}")
            self.file_watcher.addPath(config_file)

        # 延迟重载,避免频繁触发
        # 复用同一个定时器而不是每次创建新的
        if not hasattr(self, '_reload_timer'):
            self._reload_timer = QTimer(self)
            self._reload_timer.setSingleShot(True)
            self._reload_timer.timeout.connect(self.reload_all)

        self._reload_timer.start(300)  # 300毫秒延迟

    def _advance_marker_frame(self):
        """手动推进GIF动画到下一帧(使用预缓存的帧)"""
        if hasattr(self, 'marker_cached_frames') and self.marker_cached_frames:
            # 使用预缓存的帧数组，避免jumpToFrame的解码开销
            total_frames = len(self.marker_cached_frames)

            # 切换到下一帧（循环）
            self.marker_current_frame = (self.marker_current_frame + 1) % total_frames

            # 触发重绘（paintEvent会从marker_cached_frames读取当前帧）
            self.update()

    def _on_marker_animation_finished(self):
        """动画播放完成时的回调,确保循环重启"""
        # 如果启用了WebP手动帧控制,finished信号会被定时器处理,这里直接返回
        if hasattr(self, 'marker_frame_timer') and self.marker_frame_timer is not None:
            return

        if self.marker_movie and self.marker_movie.isValid():
            # 即使GIF设置了无限循环,在某些情况下finished信号仍可能被触发
            # 手动重启动画确保循环不中断
            self.gif_loop_count += 1
            self.logger.warning(f"[GIF监控] finished信号触发! 循环次数={self.gif_loop_count}")
            self.marker_movie.start()

    def _on_gif_frame_changed(self, frame_num):
        """GIF 帧变化回调，用于监控播放速度"""
        import time
        current_time = time.time()

        # 初始化监控
        if self.gif_start_time is None:
            self.gif_start_time = current_time
            self.gif_last_frame_time = current_time
            self.gif_frame_count = 0
            self.logger.info(f"[GIF监控] 开始监控 - 配置速度={self.config.get('marker_speed', 100)}%, 总帧数={self.marker_movie.frameCount()}")

            # 首次回调时检查：WebP格式存在QMovie播放bug，需要手动控制
            # Bug现象：nextFrameDelay()返回正确值(147ms)，但实际播放延迟为0
            marker_image_path = self.config.get('marker_image_path', '')
            is_webp = marker_image_path.lower().endswith('.webp')

            if is_webp and self.marker_frame_timer is None:
                self.logger.warning(f"[GIF修复] 检测到WebP格式，启用手动帧控制（QMovie对WebP的已知bug）")

                # 停止QMovie的自动播放
                self.marker_movie.setPaused(True)

                # 断开frameChanged信号，避免继续触发监控
                try:
                    self.marker_movie.frameChanged.disconnect(self._on_gif_frame_changed)
                    self.logger.info(f"[GIF修复] 已断开frameChanged信号连接")
                except RuntimeError:
                    # 信号已经断开，忽略
                    pass
                except Exception as e:
                    self.logger.debug(f"断开frameChanged信号时出错: {e}")

                # 断开finished信号，避免jumpToFrame(0)时触发finished回调
                try:
                    self.marker_movie.finished.disconnect(self._on_marker_animation_finished)
                    self.logger.info(f"[GIF修复] 已断开finished信号连接")
                except RuntimeError:
                    # 信号已经断开，忽略
                    pass
                except Exception as e:
                    self.logger.debug(f"断开finished信号时出错: {e}")

                # 创建高精度定时器手动控制帧切换
                from PySide6.QtCore import QTimer, Qt
                self.marker_frame_timer = QTimer(self)
                self.marker_frame_timer.setTimerType(Qt.TimerType.PreciseTimer)  # 使用高精度定时器
                self.marker_frame_timer.timeout.connect(self._advance_marker_frame)

                # 计算实际帧延迟: 基础150ms * (100 / 速度)
                marker_speed = self.config.get('marker_speed', 100)
                base_delay = 150  # 基础延迟150ms
                actual_delay = int(base_delay * (100 / marker_speed))
                self.marker_frame_timer.setInterval(actual_delay)
                self.marker_frame_timer.start()

                self.logger.info(f"[GIF修复] 高精度定时器已启动，间隔={actual_delay}ms，QMovie已暂停")
                return  # 不再继续监控，交给定时器控制

        self.gif_frame_count += 1

        # 计算帧间隔
        if self.gif_last_frame_time:
            frame_interval = (current_time - self.gif_last_frame_time) * 1000  # 毫秒

            # 检测异常帧间隔（正常应该是 ~147ms）
            if frame_interval < 100:
                self.logger.warning(f"[GIF监控] 帧 {frame_num}: 间隔过短! {frame_interval:.1f}ms (预期 ~147ms)")
            elif frame_interval > 200:
                self.logger.warning(f"[GIF监控] 帧 {frame_num}: 间隔过长! {frame_interval:.1f}ms (预期 ~147ms)")

        self.gif_last_frame_time = current_time

        # 每完成一轮循环输出统计
        if frame_num == 0 and self.gif_frame_count > 1:
            elapsed = current_time - self.gif_start_time
            avg_fps = self.gif_frame_count / elapsed if elapsed > 0 else 0
            expected_fps = 6.8  # 8帧 / (8 * 147ms) = 6.8 FPS

            self.logger.info(
                f"[GIF监控] 循环完成 - "
                f"总帧数={self.gif_frame_count}, "
                f"时长={elapsed:.2f}s, "
                f"平均FPS={avg_fps:.2f} "
                f"(预期={expected_fps:.1f})"
            )

            if avg_fps > 8.0:
                self.logger.error(f"[GIF监控] FPS过高! ({avg_fps:.2f} vs {expected_fps:.1f})")
            elif avg_fps > 7.5:
                self.logger.warning(f"[GIF监控] FPS偏高 ({avg_fps:.2f} vs {expected_fps:.1f})")

        # 触发重绘
        self.update()

    def update_time_marker(self):
        """更新时间标记的位置(紧凑模式)"""
        current_time = QTime.currentTime()

        # 计算当前时间的秒数
        total_seconds = (
            current_time.hour() * 3600 +
            current_time.minute() * 60 +
            current_time.second()
        )

        # 更新任务统计(每分钟更新一次,避免频繁写入)
        if hasattr(self, 'statistics_manager') and current_time.second() == 0:
            self._update_task_statistics(total_seconds)

        # 在紧凑模式下,找到当前时间所在的任务
        new_percentage = 0.0

        if not self.task_positions:
            # 没有任务时使用全天计算
            new_percentage = total_seconds / 86400
            self.logger.debug(f"[时间标记] 无任务列表,使用全天计算: {current_time.toString('HH:mm:ss')} -> {new_percentage:.4f}")
        else:
            # 查找当前时间所在的任务
            found = False
            cumulative_duration = 0

            for i, pos in enumerate(self.task_positions):
                task_start = pos['original_start']
                task_end = pos['original_end']
                task_duration = task_end - task_start
                task_name = pos['task'].get('task', '未命名')

                if task_start <= total_seconds <= task_end:
                    # 当前时间在这个任务内
                    # 计算在任务内的进度
                    progress_in_task = (total_seconds - task_start) / task_duration if task_duration > 0 else 0
                    # 计算在整个进度条上的位置
                    new_percentage = pos['compact_start_pct'] + (pos['compact_end_pct'] - pos['compact_start_pct']) * progress_in_task

                    self.logger.debug(
                        f"[时间标记] 当前时间 {current_time.toString('HH:mm:ss')} "
                        f"在任务[{i}]'{task_name}'内 "
                        f"({time_utils.seconds_to_time_str(task_start)}-{time_utils.seconds_to_time_str(task_end)}) "
                        f"任务进度={progress_in_task:.2%} "
                        f"紧凑位置={pos['compact_start_pct']:.4f}-{pos['compact_end_pct']:.4f} "
                        f"标记位置={new_percentage:.4f}"
                    )
                    found = True
                    break
                elif total_seconds < task_start:
                    # 当前时间在这个任务之前(处于间隔中)
                    # 显示在这个任务的起始位置
                    new_percentage = pos['compact_start_pct']

                    self.logger.debug(
                        f"[时间标记] 当前时间 {current_time.toString('HH:mm:ss')} "
                        f"在任务[{i}]'{task_name}'之前(间隔中) "
                        f"({time_utils.seconds_to_time_str(task_start)}-{time_utils.seconds_to_time_str(task_end)}) "
                        f"标记位置={new_percentage:.4f}(任务起点)"
                    )
                    found = True
                    break

                cumulative_duration += task_duration

            # 如果当前时间在所有任务之后
            if not found:
                new_percentage = 1.0
                self.logger.debug(
                    f"[时间标记] 当前时间 {current_time.toString('HH:mm:ss')} "
                    f"在所有任务之后,标记位置=1.0(最右端)"
                )

        # 仅当百分比实际变化时才重绘(避免浮点误差)
        if abs(new_percentage - self.current_time_percentage) > 0.00001:
            self.current_time_percentage = new_percentage

            # 场景事件检测(时间触发) - 在进度更新时检查
            if self.scene_manager.is_enabled() and self.scene_manager.get_current_scene_config():
                try:
                    self.scene_event_manager.check_time_events(self.current_time_percentage)
                except Exception as e:
                    self.logger.error(f"场景时间事件检查失败: {e}", exc_info=True)

            # 弹幕生成逻辑（低频率检查,位置更新已移到update_danmaku_animation）
            if hasattr(self, 'danmaku_manager'):
                try:
                    # 判断是否应该生成新弹幕
                    if self.danmaku_manager.should_spawn_danmaku(time.time()):
                        screen_width = self.width()
                        window_height = self.height()  # 使用窗口高度（已扩展以容纳弹幕）
                        self.danmaku_manager.spawn_danmaku(
                            screen_width, window_height,
                            self.tasks, self.current_time_percentage
                        )
                except Exception as e:
                    self.logger.error(f"弹幕生成失败: {e}", exc_info=True)

            self.update()

    def update_danmaku_animation(self):
        """弹幕动画专用更新方法(高频率调用,仅更新位置)

        与update_time_marker分离:
        - 此方法: 20fps更新弹幕位置,流畅动画
        - update_time_marker: 1Hz生成新弹幕,性能友好
        """
        if not hasattr(self, 'danmaku_manager') or not self.danmaku_manager.enabled:
            return

        try:
            # 计算真实的delta_time(自上次更新经过的时间)
            current_time = time.time()
            delta_time = current_time - self.danmaku_last_update_time
            self.danmaku_last_update_time = current_time

            # 仅更新弹幕位置,不生成新弹幕
            self.danmaku_manager.update(delta_time)

            # 触发重绘(仅当有弹幕时)
            if self.danmaku_manager.danmakus:
                self.update()
        except Exception as e:
            self.logger.error(f"弹幕动画更新失败: {e}", exc_info=True)

    def _update_task_statistics(self, current_seconds: int):
        """更新任务统计数据 (批量更新所有任务,然后延迟写入一次)

        Args:
            current_seconds: 当前时间的秒数

        性能优化:
        - 批量更新所有任务状态到内存
        - 所有任务更新完成后,延迟5秒写入一次文件
        - 减少文件写入次数: 14次/分钟 → 1次/5秒 = 12次/小时 (性能提升98.6%)
        """
        try:
            for task in self.tasks:
                task_name = task.get('task', '')
                task_start = task.get('start', '')
                task_end = task.get('end', '')
                task_color = task.get('color', '#808080')

                # 计算任务的时间范围(秒)
                start_seconds = time_utils.time_str_to_seconds(task_start)
                end_seconds = time_utils.time_str_to_seconds(task_end)

                # 判断任务状态
                if end_seconds <= current_seconds:
                    status = "completed"
                elif start_seconds <= current_seconds < end_seconds:
                    status = "in_progress"
                else:
                    status = "not_started"

                # ✅ 更新统计 (只更新内存,不立即写入文件)
                self.statistics_manager.update_task_status(
                    task_name,
                    task_start,
                    task_end,
                    task_color,
                    status
                )

            # ✅ 所有任务更新完成后,延迟保存一次 (5秒后批量写入)
            self.statistics_manager.schedule_save(delay_ms=5000)

        except Exception as e:
            self.logger.error(f"更新任务统计失败: {e}", exc_info=True)

    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 检测悬停在哪个任务上(紧凑模式) + 编辑模式下的拖拽"""
        # 标记鼠标在进度条上（用于标记图片显示控制）
        if not self.is_mouse_over_progress_bar:
            self.is_mouse_over_progress_bar = True
            self.update()  # 触发重绘以显示标记图片

        mouse_x = event.position().x()
        mouse_y = event.position().y()
        width = self.width()
        height = self.height()
        bar_height = self.config['bar_height']
        bar_y_offset = height - bar_height

        # 检测鼠标是否真的在进度条区域内
        # 进度条区域: Y坐标在 [bar_y_offset, height] 范围内
        is_mouse_on_progress_bar = (bar_y_offset <= mouse_y <= height)

        # Focus mode tooltip - update tooltip text in real-time and show at cursor's top-right
        if self.focus_mode and self.focus_start_time:
            self._update_focus_tooltip_text()
            # Show tooltip at cursor's top-right corner for better visibility
            cursor_pos = self.mapToGlobal(event.position().toPoint())
            tooltip_pos = QPoint(cursor_pos.x() + 15, cursor_pos.y() - 30)
            QToolTip.showText(tooltip_pos, self.toolTip(), self)
        elif not self.focus_mode:
            self.setToolTip("")  # Clear tooltip when not in focus mode

        # 编辑模式下的拖拽处理
        if self.edit_mode:
            if self.dragging:
                # 正在拖拽：处理拖拽逻辑
                self.handle_drag(mouse_x, mouse_y)
                return
            else:
                # 未拖拽：检测边缘悬停
                self.update_hover_edge(mouse_x, mouse_y, bar_y_offset, bar_height)

        # 普通模式：计算鼠标位置对应的百分比
        mouse_percentage = mouse_x / width if width > 0 else 0

        # 查找鼠标所在的任务(使用紧凑位置)
        # 只有当鼠标真的在进度条区域内时才检测任务悬停
        old_hovered_index = self.hovered_task_index
        self.hovered_task_index = -1

        if is_mouse_on_progress_bar:  # 仅当鼠标在进度条区域内时才检测任务悬停
            for i, pos in enumerate(self.task_positions):
                if pos['compact_start_pct'] <= mouse_percentage <= pos['compact_end_pct']:
                    self.hovered_task_index = i
                    break

        # 如果悬停任务改变,触发重绘
        if old_hovered_index != self.hovered_task_index:
            self.update()

        # 场景事件检测(hover)
        scene_config = self.scene_manager.get_current_scene_config()
        if self.scene_manager.is_enabled() and scene_config:
            try:
                # 更新画布区域 - 使用场景配置的画布高度
                if scene_config.canvas:
                    canvas_height = scene_config.canvas.height
                else:
                    canvas_height = bar_height
                canvas_y = height - canvas_height
                canvas_rect = QRectF(0, canvas_y, width, canvas_height)

                self.scene_event_manager.set_canvas_rect(canvas_rect)
                # 检查hover事件
                mouse_pos = event.position()
                self.scene_event_manager.check_hover_events(mouse_pos, self.current_time_percentage)
            except Exception as e:
                self.logger.error(f"场景hover事件检查失败: {e}", exc_info=True)

        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        """鼠标离开窗口事件"""
        # 标记鼠标离开进度条（用于标记图片隐藏）
        if self.is_mouse_over_progress_bar:
            self.is_mouse_over_progress_bar = False
            self.update()  # 触发重绘以隐藏标记图片

        if self.hovered_task_index != -1:
            self.hovered_task_index = -1
            self.update()

        # 清除编辑模式的悬停状态
        if self.edit_mode and self.hover_edge is not None:
            self.hover_edge = None
            self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """鼠标按下事件 - 场景点击事件 + 编辑模式下检测边缘点击"""
        # 检查右键事件 - 添加调试支持
        if event.button() == Qt.RightButton:
            print(f"[DEBUG] Right button clicked in mousePressEvent at: {event.globalPos()}")
            try:
                # 直接调用右键菜单方法
                self.contextMenuEvent(event)
                return
            except Exception as e:
                print(f"[DEBUG] Error handling right click in mousePressEvent: {e}")
                import traceback
                traceback.print_exc()
                return

        # 场景事件检测(click) - 优先处理
        scene_config = self.scene_manager.get_current_scene_config()
        if self.scene_manager.is_enabled() and scene_config and event.button() == Qt.LeftButton:
            try:
                width = self.width()
                height = self.height()
                bar_height = self.config['bar_height']

                # 使用场景配置的画布高度
                if scene_config.canvas:
                    canvas_height = scene_config.canvas.height
                else:
                    canvas_height = bar_height
                canvas_y = height - canvas_height
                canvas_rect = QRectF(0, canvas_y, width, canvas_height)

                self.scene_event_manager.set_canvas_rect(canvas_rect)
                mouse_pos = event.position()
                self.scene_event_manager.check_click_events(mouse_pos, self.current_time_percentage)
            except Exception as e:
                self.logger.error(f"场景click事件检查失败: {e}", exc_info=True)

        # 编辑模式下的边缘检测
        if not self.edit_mode or event.button() != Qt.LeftButton:
            return super().mousePressEvent(event)

        mouse_x = event.position().x()
        mouse_y = event.position().y()
        width = self.width()
        height = self.height()
        bar_height = self.config['bar_height']
        bar_y_offset = height - bar_height

        # 检查鼠标是否在进度条区域内
        if not (bar_y_offset <= mouse_y <= height):
            return super().mousePressEvent(event)

        # 检测是否点击在任务边缘
        for i, pos in enumerate(self.task_positions):
            start_pct = pos['compact_start_pct']
            end_pct = pos['compact_end_pct']

            start_x = start_pct * width
            end_x = end_pct * width

            # 检测左边缘
            if abs(mouse_x - start_x) <= self.edge_detect_width:
                self.dragging = True
                self.drag_task_index = i
                self.drag_edge = 'left'
                self.drag_start_x = mouse_x
                # 获取当前任务的开始时间（分钟）
                task = self.temp_tasks[i] if self.temp_tasks else self.tasks[i]
                self.drag_start_minutes = self.time_to_minutes(task['start'])
                self.logger.debug(f"开始拖拽任务 {i} 的左边缘")
                return

            # 检测右边缘
            if abs(mouse_x - end_x) <= self.edge_detect_width:
                self.dragging = True
                self.drag_task_index = i
                self.drag_edge = 'right'
                self.drag_start_x = mouse_x
                # 获取当前任务的结束时间（分钟）
                task = self.temp_tasks[i] if self.temp_tasks else self.tasks[i]
                self.drag_start_minutes = self.time_to_minutes(task['end'])
                self.logger.debug(f"开始拖拽任务 {i} 的右边缘")
                return

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 停止拖拽"""
        if self.dragging:
            self.logger.debug(f"停止拖拽任务 {self.drag_task_index}")
            self.dragging = False
            self.drag_task_index = -1
            self.drag_edge = None
            # 重新计算任务位置（因为temp_tasks已被修改）
            self.calculate_time_range()
            self.update()
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        """右键菜单事件 - 为时间块添加"开启红温专注仓"选项"""
        try:
            print(f"[DEBUG] contextMenuEvent triggered at position: {event.globalPos()}")

            # 获取点击位置对应的时间块
            mouse_pos = event.position()
            task_index = self.get_task_at_position(mouse_pos.x(), mouse_pos.y())
            print(f"[DEBUG] task_index at position: {task_index}")

            # 创建右键菜单
            menu = QMenu(self)
            print(f"[DEBUG] Created menu: {menu}")

            # Check if in focus mode first - only show focus controls
            if self.focus_mode:
                # In focus mode - ONLY show focus control options
                if self.focus_mode_type == 'work':
                    # In work mode
                    adjust_action = QAction("⏱️ 调整专注时长", self)
                    adjust_action.triggered.connect(self._adjust_focus_duration)
                    menu.addAction(adjust_action)

                    end_action = QAction("❌ 结束专注", self)
                    end_action.triggered.connect(self._end_focus_mode)
                    menu.addAction(end_action)
                else:
                    # In break mode
                    skip_action = QAction("⏭️ 跳过休息", self)
                    skip_action.triggered.connect(self._skip_break)
                    menu.addAction(skip_action)
            else:
                # Not in focus mode - show normal menu
                # Add general options first
                time_review_action = QAction("⏰ 今日时间回放", self)
                time_review_action.triggered.connect(self.show_time_review_window)
                menu.addAction(time_review_action)

                # If clicked on a task, add task-specific options
                if task_index is not None:
                    task = self.tasks[task_index]
                    print(f"[DEBUG] Found task: {task.get('task', 'Unknown')}")

                    menu.addSeparator()

                    # 添加"开启红温专注仓"选项
                    focus_action = QAction("🔥 开启红温专注仓 (25分钟)", self)
                    focus_action.triggered.connect(lambda checked=False, t=task: self._start_focus_work(t))
                    menu.addAction(focus_action)
                    print(f"[DEBUG] Added focus action")
                else:
                    print(f"[DEBUG] No task found at clicked position")

            # Calculate menu position - show at top-right of cursor
            # This provides better UX: menu appears near cursor but doesn't obscure the progress bar
            menu_pos = event.globalPos()

            # Offset menu to top-right of cursor (slightly right and up)
            menu_pos.setX(menu_pos.x() + 5)   # 5px to the right
            menu_pos.setY(menu_pos.y() - 30)  # 30px upward

            print(f"[DEBUG] About to show menu at adjusted position: {menu_pos}")
            result = menu.exec_(menu_pos)
            print(f"[DEBUG] Menu closed with result: {result}")

        except Exception as e:
            print(f"[DEBUG] Error in contextMenuEvent: {e}")
            import traceback
            traceback.print_exc()

    def get_task_at_position(self, x, y):
        """获取指定位置对应的时间块索引"""
        try:
            # 检查鼠标是否在进度条区域内
            width = self.width()
            height = self.height()
            bar_height = self.config['bar_height']
            bar_y_offset = height - bar_height

            if not (bar_y_offset <= y <= height):
                return None

            # 检查是否点击在时间块内
            for i, pos in enumerate(self.task_positions):
                start_pct = pos['compact_start_pct']
                end_pct = pos['compact_end_pct']
                start_x = start_pct * width
                end_x = end_pct * width

                if start_x <= x <= end_x:
                    return i

            return None
        except Exception as e:
            self.logger.error(f"获取时间块位置失败: {e}")
            return None

    def start_focus_mode(self, task):
        """为指定时间块开启红温专注仓"""
        try:
            task_name = task.get('name', '未知任务')
            self.logger.info(f"为时间块 '{task_name}' 开启红温专注仓")

            # 如果番茄钟已经在运行，先停止它
            if self.pomodoro_panel:
                self.pomodoro_panel.stop()

            # 创建绑定到时间块的番茄钟面板
            task_id = generate_time_block_id(task)

            self.pomodoro_panel = PomodoroPanel(
                self.config,
                self.tray_icon,
                self.logger,
                parent=None,  # 独立窗口
                time_block_id=task_id  # 传递时间块ID
            )

            # 连接关闭信号
            self.pomodoro_panel.closed.connect(self.on_pomodoro_closed)

            # 定位面板（在进度条上方）
            self.pomodoro_panel.position_above_progress_bar(self)

            # 显示面板
            self.pomodoro_panel.show()

            # 自动开始工作
            self.pomodoro_panel.start_work()

            # 显示通知
            self.tray_icon.showMessage(
                "红温专注仓",
                f"为「{task.get('task', '未知任务')}」开启了红温专注仓",
                QSystemTrayIcon.Information,
                3000
            )

        except Exception as e:
            self.logger.error(f"开启红温专注仓失败: {e}", exc_info=True)
            self.tray_icon.showMessage(
                "错误",
                f"开启红温专注仓失败: {str(e)}",
                QSystemTrayIcon.Critical,
                5000
            )

    def on_pomodoro_closed(self):
        """番茄钟面板关闭时的回调"""
        self.logger.info("红温专注仓面板已关闭")
        self.pomodoro_panel = None

    def update_hover_edge(self, mouse_x, mouse_y, bar_y_offset, bar_height):
        """更新边缘悬停状态（编辑模式）"""
        width = self.width()
        height = self.height()

        # 检查鼠标是否在进度条区域内
        if not (bar_y_offset <= mouse_y <= height):
            if self.hover_edge is not None:
                self.hover_edge = None
                self.update()
            return

        old_hover_edge = self.hover_edge
        self.hover_edge = None

        # 检测悬停在哪个边缘
        for i, pos in enumerate(self.task_positions):
            start_pct = pos['compact_start_pct']
            end_pct = pos['compact_end_pct']

            start_x = start_pct * width
            end_x = end_pct * width

            # 检测左边缘
            if abs(mouse_x - start_x) <= self.edge_detect_width:
                self.hover_edge = ('left', i)
                break

            # 检测右边缘
            if abs(mouse_x - end_x) <= self.edge_detect_width:
                self.hover_edge = ('right', i)
                break

        # 如果悬停状态改变，刷新显示
        if old_hover_edge != self.hover_edge:
            self.update()

    def handle_drag(self, mouse_x, mouse_y):
        """处理拖拽逻辑（核心方法）"""
        if self.drag_task_index < 0 or not self.temp_tasks:
            return

        width = self.width()
        delta_x = mouse_x - self.drag_start_x

        # 计算总时长（所有任务的总分钟数）
        total_minutes = 0
        for t in self.temp_tasks:
            start_min = self.time_to_minutes(t['start'])
            end_min = self.time_to_minutes(t['end'])
            duration = end_min - start_min
            if duration < 0:
                duration += 1440  # 跨午夜
            total_minutes += duration

        if total_minutes == 0:
            return

        # 将像素转换为分钟
        minutes_per_pixel = total_minutes / width
        delta_minutes = int(delta_x * minutes_per_pixel)

        if self.drag_edge == 'right':
            # 拖动右边缘：调整当前任务的结束时间
            current_task = self.temp_tasks[self.drag_task_index]
            start_min = self.time_to_minutes(current_task['start'])
            new_end_min = self.drag_start_minutes + delta_minutes

            # 限制最小时长
            if new_end_min - start_min < self.min_task_duration:
                new_end_min = start_min + self.min_task_duration

            # 如果有下一个任务，确保不会让下一个任务小于最小时长
            if self.drag_task_index < len(self.temp_tasks) - 1:
                next_task = self.temp_tasks[self.drag_task_index + 1]
                next_end_min = self.time_to_minutes(next_task['end'])
                min_next_start = next_end_min - self.min_task_duration
                if new_end_min > min_next_start:
                    new_end_min = min_next_start

            # 更新当前任务和下一个任务
            current_task['end'] = self.minutes_to_time(new_end_min)
            if self.drag_task_index < len(self.temp_tasks) - 1:
                next_task = self.temp_tasks[self.drag_task_index + 1]
                next_task['start'] = self.minutes_to_time(new_end_min)

        elif self.drag_edge == 'left':
            # 拖动左边缘：调整当前任务的开始时间
            current_task = self.temp_tasks[self.drag_task_index]
            end_min = self.time_to_minutes(current_task['end'])
            new_start_min = self.drag_start_minutes + delta_minutes

            # 限制最小时长
            if end_min - new_start_min < self.min_task_duration:
                new_start_min = end_min - self.min_task_duration

            # 如果有上一个任务，确保不会让上一个任务小于最小时长
            if self.drag_task_index > 0:
                prev_task = self.temp_tasks[self.drag_task_index - 1]
                prev_start_min = self.time_to_minutes(prev_task['start'])
                max_prev_end = prev_start_min + self.min_task_duration
                if new_start_min < max_prev_end:
                    new_start_min = max_prev_end

            # 更新当前任务和上一个任务
            current_task['start'] = self.minutes_to_time(new_start_min)
            if self.drag_task_index > 0:
                prev_task = self.temp_tasks[self.drag_task_index - 1]
                prev_task['end'] = self.minutes_to_time(new_start_min)

        # 重新计算任务位置
        # calculate_time_range会自动检测编辑模式并使用temp_tasks
        self.calculate_time_range()

        self.update()

    def time_to_minutes(self, time_str):
        """将 HH:MM 转换为分钟数"""
        try:
            hours, minutes = map(int, time_str.split(':'))
            if hours == 24 and minutes == 0:
                return 1440
            return hours * 60 + minutes
        except (ValueError, AttributeError) as e:
            # 时间格式错误或time_str不是字符串
            self.logger.debug(f"时间转换失败 '{time_str}': {e}")
            return 0

    def minutes_to_time(self, minutes):
        """将分钟数转换为 HH:MM"""
        minutes = int(minutes) % 1440  # 确保在 0-1439 范围内
        hours = minutes // 60
        mins = minutes % 60
        if hours == 24:
            return "24:00"
        return f"{hours:02d}:{mins:02d}"

    def paintEvent(self, event):
        """自定义绘制事件"""
        self.paint_event_count += 1

        # 每100次paintEvent输出一次统计（避免日志过多）
        if self.paint_event_count % 100 == 0:
            self.logger.debug(f"[GIF监控] paintEvent 调用次数: {self.paint_event_count}")

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # 抗锯齿
        painter.setPen(Qt.NoPen)  # 设置默认无描边，避免主题切换时出现边框

        width = self.width()
        height = self.height()
        bar_height = self.config['bar_height']

        # 计算进度条的实际位置(在窗口底部)
        bar_y_offset = height - bar_height

        # 1. 绘制半透明背景条(只在进度条区域)
        # 如果场景已启用，跳过背景绘制（场景的道路层将作为背景）
        scene_enabled = self.scene_manager.is_enabled()
        scene_config = self.scene_manager.get_current_scene_config()

        if not (scene_enabled and scene_config):
            bg_color = QColor(self.config['background_color'])
            bg_color.setAlpha(self.config['background_opacity'])
            painter.fillRect(0, bar_y_offset, width, bar_height, bg_color)

        # 1.5. 绘制场景(如果已启用) - 在任务色块之前绘制,让道路层作为背景
        if scene_enabled and scene_config:
            try:
                # 定义画布原始尺寸（配置中定义的设计尺寸）
                if scene_config.canvas:
                    canvas_width = scene_config.canvas.width   # 1200px (设计宽度)
                    canvas_height = scene_config.canvas.height # 150px
                else:
                    canvas_width = width
                    canvas_height = bar_height  # 回退到进度条尺寸

                # 不缩放场景,使用原始尺寸渲染
                # 场景编辑器中1200px可视范围对应屏幕中间的1200px区域
                # 左右两侧超出部分由道路层平铺填充

                # 画布底部对齐到窗口底部，并向下偏移21px
                canvas_y = height - canvas_height + 21

                # 画布水平居中显示
                canvas_x = (width - canvas_width) / 2  # 居中: (2560 - 1200) / 2 = 680

                # 场景画布区域 - 使用原始尺寸,水平居中
                canvas_rect = QRectF(canvas_x, canvas_y, canvas_width, canvas_height)

                # 计算当前进度(0.0-1.0)
                progress = self.current_time_percentage

                # 设置裁剪区域，防止场景元素绘制到窗口外（避免左下角闪现深色块）
                painter.save()  # 保存当前painter状态
                painter.setClipRect(0, 0, width, height)  # 裁剪到窗口范围内

                # 渲染场景 - 使用原始尺寸,不缩放
                self.scene_renderer.render(painter, canvas_rect, progress)

                painter.restore()  # 恢复painter状态
            except Exception as e:
                self.logger.error(f"场景渲染失败: {e}", exc_info=True)

        # 2. Check if in focus mode - if yes, render immersive pomodoro timer instead
        if self.focus_mode:
            self._render_focus_mode(painter, width, height, bar_y_offset, bar_height)
            return  # Skip normal task rendering

        # 3. 绘制任务色块(使用紧凑模式位置) - 先绘制所有色块,不绘制悬停文字
        # 如果场景已启用，跳过任务色块的绘制（但仍然处理悬停逻辑以显示提示）
        current_time = QTime.currentTime()
        current_seconds = current_time.hour() * 3600 + current_time.minute() * 60 + current_time.second()

        hover_info = None  # 保存悬停信息,最后绘制

        # 在任务循环前强制重置pen状态（防止fillRect等操作修改了pen）
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.NoBrush)

        # 判断是否需要绘制进度条:
        # 1. 场景未启用时,正常绘制进度条
        # 2. 场景已启用,但用户勾选了"依然展示进度条",则在场景上方叠加进度条
        show_progress_in_scene = self.config.get('scene', {}).get('show_progress_bar', False)
        should_draw_progress_bar = not (scene_enabled and scene_config) or show_progress_in_scene

        if should_draw_progress_bar:
            for i, pos in enumerate(self.task_positions):
                task = pos['task']

                # 使用紧凑模式的百分比位置
                start_pct = pos['compact_start_pct']
                end_pct = pos['compact_end_pct']

                # 三种状态:未开始、进行中、已完成
                is_completed = pos['original_end'] <= current_seconds  # 已完成
                is_in_progress = pos['original_start'] <= current_seconds < pos['original_end']  # 进行中
                is_not_started = current_seconds < pos['original_start']  # 未开始

                # 计算任务块的位置和宽度
                x = start_pct * width

                # 为避免浮点数舍入导致的像素间隙，让每个任务块延伸到下一个任务的起始位置
                if i < len(self.task_positions) - 1:
                    # 不是最后一个任务,使用下一个任务的起始位置作为结束位置
                    next_start_pct = self.task_positions[i + 1]['compact_start_pct']
                    task_width = next_start_pct * width - x
                else:
                    # 最后一个任务,延伸到进度条末端
                    task_width = width - x

                # 解析颜色
                color = QColor(task['color'])

                # 绘制任务块（根据状态分层绘制）
                painter.setPen(Qt.NoPen)

                # 1. 先绘制整个任务块的背景（未开始或进行中的任务都需要背景）
                if is_not_started or is_in_progress:
                    # 背景使用半透明灰色
                    gray_value = int(color.red() * 0.299 + color.green() * 0.587 + color.blue() * 0.114)
                    bg_color = QColor(gray_value, gray_value, gray_value, 80)  # 半透明灰色背景

                    bg_rect = QRectF(x, bar_y_offset, task_width, bar_height)
                    painter.setBrush(bg_color)

                    if self.config.get('corner_radius', 0) > 0:
                        path = QPainterPath()
                        path.addRoundedRect(bg_rect, self.config['corner_radius'], self.config['corner_radius'])
                        painter.fillPath(path, bg_color)
                    else:
                        painter.fillRect(bg_rect, bg_color)

                # 2. 绘制已完成或进行中的部分（使用任务原色）
                if is_completed or is_in_progress:
                    # 计算实际绘制宽度
                    if is_in_progress:
                        # 进行中：只绘制到当前时间
                        task_duration = pos['original_end'] - pos['original_start']
                        elapsed_time = current_seconds - pos['original_start']
                        progress_ratio = elapsed_time / task_duration if task_duration > 0 else 0
                        actual_task_width = task_width * progress_ratio
                    else:
                        # 已完成：绘制整个任务块
                        actual_task_width = task_width

                    # 绘制进度部分（使用任务原色）
                    rect = QRectF(x, bar_y_offset, actual_task_width, bar_height)
                    painter.setBrush(color)

                    if self.config.get('corner_radius', 0) > 0:
                        path = QPainterPath()
                        path.addRoundedRect(rect, self.config['corner_radius'], self.config['corner_radius'])
                        painter.fillPath(path, color)
                    else:
                        painter.fillRect(rect, color)

                # 编辑模式下的视觉反馈（使用完整任务块矩形）
                if self.edit_mode:
                    # 为编辑模式定义完整的任务块矩形
                    full_rect = QRectF(x, bar_y_offset, task_width, bar_height)

                    # 1. 金色边缘高亮（悬停或拖拽）
                    if self.hover_edge and self.hover_edge[1] == i:
                        edge_type = self.hover_edge[0]
                        painter.setPen(QPen(QColor("#FFD700"), 3))  # 金色，3像素
                        if edge_type == 'left':
                            # 左边缘高亮
                            painter.drawLine(int(full_rect.left()), int(full_rect.top()),
                                           int(full_rect.left()), int(full_rect.bottom()))
                        elif edge_type == 'right':
                            # 右边缘高亮
                            painter.drawLine(int(full_rect.right()), int(full_rect.top()),
                                           int(full_rect.right()), int(full_rect.bottom()))

                    # 2. 拖拽中的任务高亮
                    if self.dragging and self.drag_task_index == i:
                        # 绘制半透明金色覆盖层
                        overlay_color = QColor("#FFD700")
                        overlay_color.setAlpha(50)
                        painter.fillRect(full_rect, overlay_color)

                        # 绘制拖拽边缘的粗线
                        painter.setPen(QPen(QColor("#FFD700"), 4))
                        if self.drag_edge == 'left':
                            painter.drawLine(int(full_rect.left()), int(full_rect.top()),
                                           int(full_rect.left()), int(full_rect.bottom()))
                        elif self.drag_edge == 'right':
                            painter.drawLine(int(full_rect.right()), int(full_rect.top()),
                                           int(full_rect.right()), int(full_rect.bottom()))

                    # 3. 绘制拖拽手柄图标（⋮⋮）
                    if task_width > 20:  # 宽度足够才绘制
                        painter.setPen(QColor("#FFFFFF"))
                        painter.setFont(QFont("Arial", 12, QFont.Bold))

                        # 左边缘手柄
                        handle_text = "⋮"
                        handle_rect_left = QRectF(full_rect.left() + 2, full_rect.top(),
                                                  10, full_rect.height())
                        painter.drawText(handle_rect_left, Qt.AlignCenter, handle_text)

                        # 右边缘手柄
                        handle_rect_right = QRectF(full_rect.right() - 12, full_rect.top(),
                                                   10, full_rect.height())
                        painter.drawText(handle_rect_right, Qt.AlignCenter, handle_text)

                # Focus state visual feedback (Red Focus Chamber integration)
                task_id = generate_time_block_id(task, i)
                focus_state = self.task_focus_states.get(task_id, 'NORMAL')
                is_focus_active = focus_state == 'FOCUS_ACTIVE'
                is_focus_done = focus_state == 'FOCUS_DONE'

                if is_focus_active:
                    # Active focus: Red overlay + Fire icon
                    focus_overlay = QColor(255, 80, 50, 60)  # Semi-transparent red
                    painter.fillRect(rect, focus_overlay)

                    # Draw fire icon
                    if task_width > 30:  # Only if wide enough
                        painter.setPen(QColor(255, 255, 255))
                        painter.setFont(QFont("Segoe UI Emoji", 11, QFont.Bold))
                        icon_height = rect.height() + 24
                        icon_rect = QRectF(rect.left() + 12, rect.top() - 17, 16, icon_height)
                        painter.drawText(icon_rect, Qt.AlignCenter, "🔥")

                # Note: Completed focus fire icons are now drawn globally after all tasks
                # to prevent being covered by other task blocks

                # 如果是悬停任务,保存信息稍后绘制
                if i == self.hovered_task_index:
                    hover_info = {
                        'task': task,
                        'color': color,
                        'x': x,
                        'task_width': task_width,
                        'bar_y_offset': bar_y_offset
                    }

        # 3. 绘制时间标记(最上层,在进度条区域)
        # 重置pen状态，防止任务循环中的pen设置影响后续绘制
        painter.setPen(Qt.NoPen)

        marker_x = self.current_time_percentage * width
        marker_type = self.config.get('marker_type', 'line')

        # 检查是否应该显示标记图片
        # 配置项：marker_always_visible - 是否始终显示标记图片
        # True: 始终显示（默认，保持当前行为）
        # False: 仅在鼠标悬停时显示
        marker_always_visible = self.config.get('marker_always_visible', True)
        should_show_marker = marker_always_visible or self.is_mouse_over_progress_bar

        if marker_type == 'gif' and should_show_marker:
            # GIF 动画标记 - 优先使用预缓存的帧
            current_pixmap = None
            if hasattr(self, 'marker_cached_frames') and self.marker_cached_frames:
                # 使用预缓存的帧（性能最优）
                frame_index = self.marker_current_frame % len(self.marker_cached_frames)
                current_pixmap = self.marker_cached_frames[frame_index]
            elif self.marker_movie and self.marker_movie.isValid():
                # 回退方案：使用QMovie的currentPixmap
                current_pixmap = self.marker_movie.currentPixmap()

            if current_pixmap and not current_pixmap.isNull():
                # 计算绘制位置(水平居中,底部对齐到进度条底部 + Y轴偏移)
                pixmap_width = current_pixmap.width()
                pixmap_height = current_pixmap.height()

                # 计算居中对齐位置
                draw_x = int(marker_x - pixmap_width / 2)

                # 应用 X 轴偏移(正值向右,负值向左)
                # 注意:偏移在边界限制之后应用,以确保偏移能够生效
                marker_x_offset = self.config.get('marker_x_offset', 0)
                draw_x += marker_x_offset

                # 边界限制:防止图片完全超出屏幕
                # 允许部分溢出以保证偏移效果可见
                draw_x = max(-pixmap_width // 2, min(draw_x, width - pixmap_width // 2))

                # Y 轴位置 = 窗口底部 - 图片高度 - Y轴偏移(正值向上,负值向下)
                marker_y_offset = self.config.get('marker_y_offset', 0)
                draw_y = height - pixmap_height - marker_y_offset

                # 绘制 GIF 当前帧
                painter.drawPixmap(draw_x, draw_y, current_pixmap)

        elif marker_type == 'image' and should_show_marker and self.marker_pixmap and not self.marker_pixmap.isNull():
            # 静态图片标记
            pixmap_width = self.marker_pixmap.width()
            pixmap_height = self.marker_pixmap.height()

            # 计算居中对齐位置
            draw_x = int(marker_x - pixmap_width / 2)

            # 应用 X 轴偏移(正值向右,负值向左)
            # 注意:偏移在边界限制之后应用,以确保偏移能够生效
            marker_x_offset = self.config.get('marker_x_offset', 0)
            draw_x += marker_x_offset

            # 边界限制:防止图片完全超出屏幕
            # 允许部分溢出以保证偏移效果可见
            draw_x = max(-pixmap_width // 2, min(draw_x, width - pixmap_width // 2))

            # Y 轴位置 = 窗口底部 - 图片高度 - Y轴偏移(正值向上,负值向下)
            marker_y_offset = self.config.get('marker_y_offset', 0)
            draw_y = height - pixmap_height - marker_y_offset

            # 绘制图片
            painter.drawPixmap(draw_x, draw_y, self.marker_pixmap)

        else:
            # 默认线条标记
            # 绘制阴影效果(可选)
            if self.config.get('enable_shadow', True):
                shadow_pen = QPen(QColor(0, 0, 0, 100))
                shadow_pen.setWidth(self.config['marker_width'] + 1)
                painter.setPen(shadow_pen)
                painter.drawLine(int(marker_x + 1), bar_y_offset, int(marker_x + 1), height)

            # 绘制主线
            marker_color = QColor(self.config['marker_color'])
            marker_pen = QPen(marker_color)
            marker_pen.setWidth(self.config['marker_width'])
            painter.setPen(marker_pen)
            painter.drawLine(int(marker_x), bar_y_offset, int(marker_x), height)

        # 3.5. 绘制所有完成的专注火焰标记(全局覆盖层,不受任务块限制)
        # TODO: 暂时注释掉火焰标记功能,后续优化后再启用
        # if hasattr(self, 'completed_focus_start_times') and self.completed_focus_start_times:
        #     from datetime import datetime
        #     painter.setPen(QColor(255, 255, 255))
        #     painter.setFont(QFont("Segoe UI Emoji", 11, QFont.Bold))
        #
        #     # Debug: Log once per paint cycle (use frame counter to avoid spam)
        #     if not hasattr(self, '_fire_log_count'):
        #         self._fire_log_count = 0
        #     self._fire_log_count += 1
        #     if self._fire_log_count % 100 == 1:  # Log every 100 frames
        #         self.logger.info(f"🔥 绘制 {len(self.completed_focus_start_times)} 个火焰标记")
        #
        #     for task_id, start_time in self.completed_focus_start_times.items():
        #         # Convert time to minutes since midnight
        #         start_minutes = start_time.hour * 60 + start_time.minute
        #         # Calculate percentage within the day
        #         time_percentage = start_minutes / (24 * 60)
        #         # Calculate X position on the bar
        #         fire_x = time_percentage * width
        #
        #         # Draw fire icon at actual completion time
        #         icon_height = bar_height + 24
        #         icon_rect = QRectF(fire_x - 8, bar_y_offset - 17, 16, icon_height)
        #         painter.drawText(icon_rect, Qt.AlignCenter, "🔥")
        #
        #         # Debug: Log position once
        #         if self._fire_log_count % 100 == 1:
        #             self.logger.info(f"  - 火焰位置: {start_time.strftime('%H:%M')} → X={fire_x:.1f}px ({time_percentage*100:.1f}%)")

        # 4. 最后绘制悬停文字(确保在最上层,不被时间标记遮挡)
        if hover_info:
            task = hover_info['task']
            color = hover_info['color']
            x = hover_info['x']
            task_width = hover_info['task_width']
            bar_y_offset = hover_info['bar_y_offset']

            # 设置文字字体
            font = QFont()
            font.setPointSize(9)
            font.setBold(True)
            painter.setFont(font)

            # 任务信息 - 单行显示
            task_text = f"{task['task']} ({task['start']}-{task['end']})"

            # 计算文字的实际尺寸
            font_metrics = painter.fontMetrics()
            text_width = font_metrics.horizontalAdvance(task_text)
            text_height = font_metrics.height()

            # 添加内边距
            padding_horizontal = 30  # 左右各15像素
            padding_vertical = 14    # 上下各7像素

            # 计算悬停色块的实际尺寸
            hover_width = max(task_width, text_width + padding_horizontal)
            hover_height = text_height + padding_vertical

            # 计算悬停色块的位置(居中对齐任务块)
            hover_x = x + (task_width - hover_width) / 2
            hover_y = bar_y_offset - hover_height - 5  # 向上偏移5像素

            # 确保悬停色块不超出窗口边界
            if hover_x < 0:
                hover_x = 0
            elif hover_x + hover_width > width:
                hover_x = width - hover_width

            # 确保 y 坐标不会超出窗口顶部
            if hover_y < 0:
                hover_y = 0

            hover_rect = QRectF(hover_x, hover_y, hover_width, hover_height)

            # 绘制悬停的扩展色块
            hover_color = QColor(color)
            hover_color.setAlpha(240)  # 稍微透明
            painter.setBrush(hover_color)
            painter.setPen(QPen(QColor(255, 255, 255, 255), 2))  # 白色边框

            if self.config.get('corner_radius', 0) > 0:
                painter.drawRoundedRect(
                    hover_rect,
                    self.config['corner_radius'],
                    self.config['corner_radius']
                )
            else:
                painter.drawRect(hover_rect)

            # 绘制任务文本
            # 悬停提示框的文字始终使用白色，确保在任务色块背景上清晰可见
            # 不使用主题的text_color，因为主题text_color是针对进度条背景的，而这里背景是任务颜色
            text_color = QColor(task.get('text_color', '#FFFFFF'))
            painter.setPen(text_color)
            painter.drawText(hover_rect, Qt.AlignCenter, task_text)

        # 5. 编辑模式的提示框和拖拽时间显示
        if self.edit_mode:
            # 5.1 编辑模式提示框（右下角，进度条上方，参考番茄钟尺寸）
            tip_width = 300  # 比番茄钟稍宽一点
            tip_height = 60
            tip_padding = 10  # 距离边缘的间距

            # 计算提示框位置（右下角，进度条上方，额外向上移动40避免遮挡任务提示）
            tip_x = width - tip_width - tip_padding
            tip_y = bar_y_offset - tip_height - tip_padding - 40

            tip_rect = QRectF(tip_x, tip_y, tip_width, tip_height)

            # 半透明深色背景（带圆角）
            tip_bg = QColor(30, 30, 30, 230)
            painter.setBrush(tip_bg)
            painter.setPen(QPen(QColor("#FFD700"), 2))  # 金色边框
            painter.drawRoundedRect(tip_rect, 8, 8)

            # 提示文字（两行）
            painter.setPen(QColor("#FFD700"))  # 金色
            painter.setFont(QFont("Microsoft YaHei", 9, QFont.Bold))

            # 第一行：标题
            title_rect = QRectF(tip_x, tip_y + 8, tip_width, 20)
            painter.drawText(title_rect, Qt.AlignCenter, "✏️ 编辑模式")

            # 第二行：操作提示
            painter.setFont(QFont("Microsoft YaHei", 8))
            painter.setPen(QColor("#FFFFFF"))  # 白色
            hint_rect = QRectF(tip_x, tip_y + 28, tip_width, 25)
            painter.drawText(hint_rect, Qt.AlignCenter, "拖拽任务边缘调整时间\n完成后请到托盘菜单保存")

            # 5.2 拖拽时的实时时间提示
            if self.dragging and 0 <= self.drag_task_index < len(self.temp_tasks):
                task = self.temp_tasks[self.drag_task_index]
                time_text = f"{task['start']} - {task['end']}"

                # 在拖拽任务的上方显示时间
                pos = self.task_positions[self.drag_task_index]
                start_pct = pos['compact_start_pct']
                end_pct = pos['compact_end_pct']
                task_x = start_pct * width
                task_w = (end_pct - start_pct) * width

                # 计算时间提示框的位置
                time_font = QFont("Arial", 11, QFont.Bold)
                painter.setFont(time_font)
                font_metrics = painter.fontMetrics()
                time_width = font_metrics.horizontalAdvance(time_text)
                time_height = font_metrics.height()

                time_padding = 20
                time_box_width = time_width + time_padding
                time_box_height = time_height + 10

                time_box_x = task_x + (task_w - time_box_width) / 2
                time_box_y = bar_y_offset - time_box_height - 35  # 在悬停提示上方

                # 确保不超出边界
                time_box_x = max(0, min(time_box_x, width - time_box_width))
                time_box_y = max(0, time_box_y)

                time_box_rect = QRectF(time_box_x, time_box_y,
                                      time_box_width, time_box_height)

                # 绘制时间提示框（金色背景）
                time_box_color = QColor("#FFD700")
                time_box_color.setAlpha(220)
                painter.setBrush(time_box_color)
                painter.setPen(QPen(QColor("#FFFFFF"), 2))
                painter.drawRoundedRect(time_box_rect, 5, 5)

                # 绘制时间文字（黑色）
                painter.setPen(QColor("#000000"))
                painter.drawText(time_box_rect, Qt.AlignCenter, time_text)

        # 免费版水印：在进度条最右侧显示
        try:
            user_tier = self.auth_client.get_user_tier()
            if user_tier == "free":
                # 水印文本 (国际化)
                watermark_text = tr('watermark.free_version')

                # 设置字体（稍小一点，避免过于显眼）
                watermark_font = QFont("Microsoft YaHei", 8)
                painter.setFont(watermark_font)

                # 计算文本宽度
                from PySide6.QtGui import QFontMetrics
                metrics = QFontMetrics(watermark_font)
                text_width = metrics.horizontalAdvance(watermark_text)
                text_height = metrics.height()

                # 水印位置：固定在窗口底部右侧
                # X坐标：距离右边缘10px
                watermark_x = width - text_width - 10
                # Y坐标：固定在窗口底部，距离底部2px（不受进度条高度影响）
                watermark_y = height - text_height - 2
                watermark_rect = QRectF(watermark_x, watermark_y, text_width, text_height)

                # 绘制半透明背景（可选）
                bg_color = QColor("#000000")
                bg_color.setAlpha(100)
                painter.fillRect(watermark_rect.adjusted(-4, -2, 4, 2), bg_color)

                # 绘制水印文字（白色半透明）
                text_color = QColor("#FFFFFF")
                text_color.setAlpha(180)
                painter.setPen(text_color)
                painter.drawText(watermark_rect, Qt.AlignCenter, watermark_text)
        except Exception as e:
            self.logger.warning(f"绘制水印失败: {e}")

        # 6. 绘制弹幕（最后绘制，确保在最上层）
        if hasattr(self, 'danmaku_manager'):
            try:
                self.danmaku_manager.render(painter, width, height)
            except Exception as e:
                self.logger.error(f"弹幕渲染失败: {e}", exc_info=True)

        painter.end()
    
    def apply_theme(self):
        """应用当前主题到进度条"""
        try:
            if not hasattr(self, 'theme_manager') or not self.theme_manager:
                return

            theme = self.theme_manager.get_current_theme()
            if not theme:
                return

            # 更新config中的颜色配置（保持向后兼容）
            old_bg_color = self.config.get('background_color', '#505050')
            new_bg_color = theme.get('background_color', old_bg_color)
            old_opacity = self.config.get('background_opacity', 180)
            new_opacity = theme.get('background_opacity', old_opacity)
            old_marker_color = self.config.get('marker_color', '#FF0000')
            new_marker_color = theme.get('marker_color', old_marker_color)

            self.config['background_color'] = new_bg_color
            self.config['background_opacity'] = new_opacity
            self.config['marker_color'] = new_marker_color

            # 应用主题配色到任务(如果主题提供了task_colors且用户启用了自动应用)
            # 检查config中的auto_apply_task_colors设置
            theme_config = self.config.get('theme', {})
            auto_apply = theme_config.get('auto_apply_task_colors', False)

            task_colors = theme.get('task_colors', [])
            if auto_apply and task_colors and len(self.tasks) > 0:
                # 智能分配任务颜色
                for i, task in enumerate(self.tasks):
                    color_index = i % len(task_colors)
                    task['color'] = task_colors[color_index]

                # 保存更新后的任务到文件(使主题持久化)
                try:
                    tasks_file = self.app_dir / 'tasks.json'
                    with open(tasks_file, 'w', encoding='utf-8') as f:
                        json.dump(self.tasks, f, indent=4, ensure_ascii=False)
                    self.logger.info(f"已应用主题配色到 {len(self.tasks)} 个任务")
                except Exception as e:
                    self.logger.error(f"保存任务配色失败: {e}")
            elif task_colors and len(self.tasks) > 0 and not auto_apply:
                self.logger.info(f"主题包含 {len(task_colors)} 种配色，但auto_apply_task_colors=False，保留用户自定义颜色")

            # 保存主题配置到config.json
            try:
                config_file = self.app_dir / 'config.json'
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                # 更新主题相关配置
                config_data['background_color'] = new_bg_color
                config_data['background_opacity'] = new_opacity
                config_data['marker_color'] = new_marker_color

                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=4, ensure_ascii=False)
            except Exception as e:
                self.logger.error(f"保存主题配置失败: {e}")

            # 强制刷新整个窗口（确保变化可见）
            self.update()

            self.logger.info(f"已应用主题: {theme.get('name', 'Unknown')}")
            self.logger.info(f"  背景色: {old_bg_color} -> {new_bg_color}")
            self.logger.info(f"  透明度: {old_opacity} -> {new_opacity}")
            self.logger.info(f"  标记色: {old_marker_color} -> {new_marker_color}")
            if task_colors:
                self.logger.info(f"  任务配色: 已应用 {len(task_colors)} 种颜色")
        except Exception as e:
            self.logger.error(f"应用主题失败: {e}", exc_info=True)

    def closeEvent(self, event):
        """窗口关闭事件，清理所有资源"""
        # 停止主定时器
        if hasattr(self, 'timer') and self.timer:
            if self.timer.isActive():
                self.timer.stop()
            self.timer = None

        # 停止可见性监控定时器
        if hasattr(self, 'visibility_timer') and self.visibility_timer:
            if self.visibility_timer.isActive():
                self.visibility_timer.stop()
            self.visibility_timer = None

        # 停止标记帧切换定时器
        if hasattr(self, 'marker_frame_timer') and self.marker_frame_timer:
            if self.marker_frame_timer.isActive():
                self.marker_frame_timer.stop()
            self.marker_frame_timer = None

        # 清理QMovie对象
        if hasattr(self, 'marker_movie') and self.marker_movie:
            self.marker_movie.stop()
            self.marker_movie.deleteLater()
            self.marker_movie = None

        # 清理缓存帧列表（释放内存）
        if hasattr(self, 'marker_cached_frames'):
            self.marker_cached_frames.clear()
            self.marker_cached_frames = None

        # 断开文件监控信号
        if hasattr(self, 'file_watcher') and self.file_watcher:
            try:
                self.file_watcher.fileChanged.disconnect()
            except RuntimeError:
                # 信号已经断开，忽略
                pass
            except Exception as e:
                self.logger.debug(f"断开file_watcher信号时出错: {e}")

        # 停止行为追踪服务
        self.stop_activity_tracker()

        # 停止任务完成推理调度器
        if hasattr(self, 'task_completion_scheduler') and self.task_completion_scheduler:
            try:
                self.task_completion_scheduler.stop()
                self.logger.info("任务完成推理调度器已停止")
            except Exception as e:
                self.logger.warning(f"停止调度器时出错: {e}")

        # 接受关闭事件
        event.accept()
        self.logger.info("时间进度条已关闭，资源已清理")


def main():
    """主程序入口"""
    # 启用高DPI支持(Windows 10/11)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # ✅ 修复: 移除重复的 logging.basicConfig() 配置
    # MainWindow.__init__() 中的 setup_logging() 会正确配置 FileHandler + StreamHandler
    # 这里只需要获取 logger 对象,不要重复配置 basicConfig
    logger = logging.getLogger(__name__)

    # 创建应用实例
    app = QApplication(sys.argv)

    # ⚠️ 关键修复：强制统一样式引擎，解决打包后QFrame边框渲染差异
    # 开发环境使用 windows11，打包环境默认为空，导致CSS边框渲染效果不同
    from PySide6.QtWidgets import QStyleFactory
    available_styles = QStyleFactory.keys()
    logger.info(f"Available Qt styles: {available_styles}")

    # 优先使用windows11（与开发环境一致），否则使用Fusion（跨平台一致性最好）
    if "windows11" in available_styles:
        app.setStyle("windows11")
        logger.info("Forced Qt style: windows11")
    else:
        app.setStyle("fusion")
        logger.info("Forced Qt style: fusion (windows11 not available)")

    logger.info(f"Final Qt style: {app.style().objectName()}")

    # 应用Qt-Material主题（已禁用，改用自定义浅色主题）
    # if QT_MATERIAL_AVAILABLE:
    #     try:
    #         extra = {
    #             'density_scale': '0',
    #             'font_family': 'Microsoft YaHei',
    #             'font_size': '13px',
    #         }
    #         apply_stylesheet(app, theme='dark_teal.xml', extra=extra)
    #         logger.info("✨ 已应用Qt-Material主题: dark_teal")
    #     except Exception as e:
    #         logger.warning(f"应用Material主题失败: {e}，使用默认样式")

    # 创建并显示主窗口（先创建窗口，再启动后台服务）
    window = TimeProgressBar()
    
    # 在窗口完全创建后再显示（避免初始化时的问题）
    window.show()
    window.raise_()
    
    # Windows 特定:设置窗口始终在最顶层
    if platform.system() == 'Windows':
        window.set_windows_topmost()

    # 已切换到Vercel云服务，无需启动本地后端服务
    # AI功能直接通过 https://jindutiao.vercel.app 提供

    # 进入事件循环
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
