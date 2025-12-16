"""
任务统计报告GUI窗口
显示任务完成情况的可视化统计
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QTabWidget, QTableWidget, QTableWidgetItem,
                               QPushButton, QGroupBox, QScrollArea, QHeaderView,
                               QMessageBox, QFileDialog, QProgressBar, QDialog,
                               QSpinBox, QComboBox, QDialogButtonBox, QFormLayout,
                               QGridLayout)
from PySide6.QtCore import Qt, Signal, Q_ARG, Slot, QDateTime, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis, QPieSeries, QPieSlice
from statistics_manager import StatisticsManager
from gaiya.core.theme_manager import ThemeManager
from gaiya.ui.theme_light import LightTheme
from gaiya.ui.style_manager import StyleManager
from i18n.translator import tr
from gaiya.data.db_manager import db
from gaiya.core.insights_generator import InsightsGenerator
from gaiya.core.goal_manager import GoalManager, Goal
from gaiya.core.achievement_manager import AchievementManager, Achievement
from gaiya.core.motivation_engine import MotivationEngine
from pathlib import Path
import logging
import sys
import json
from datetime import date
from version import VERSION_STRING


class CircularProgressWidget(QWidget):
    """圆形进度条小部件"""

    def __init__(self, percentage: float, color: str = "#4CAF50", parent=None):
        super().__init__(parent)
        self.percentage = percentage
        self.color = QColor(color)
        self.setFixedSize(100, 100)

    def set_percentage(self, percentage: float):
        """设置百分比并刷新"""
        self.percentage = percentage
        self.update()

    def paintEvent(self, event):
        """绘制圆形进度条"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制背景圆环
        pen = QPen(QColor(220, 220, 220))
        pen.setWidth(8)
        painter.setPen(pen)
        painter.drawEllipse(10, 10, 80, 80)

        # 绘制进度圆弧
        pen.setColor(self.color)
        painter.setPen(pen)
        span_angle = int(self.percentage * 360 / 100 * 16)  # Qt使用16分之一度
        painter.drawArc(10, 10, 80, 80, 90 * 16, -span_angle)

        # 绘制中心文字
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(50, 50, 50))
        painter.drawText(0, 0, 100, 100, Qt.AlignCenter, f"{int(self.percentage)}%")

        painter.end()


class StatCard(QWidget):
    """统计卡片小部件"""

    def __init__(self, title: str, value: str, icon: str = "", color: str = "#2196F3", parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.icon = icon
        self.color = color
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        # 设置背景颜色
        self.setStyleSheet(f"""
            StatCard {{
                background-color: {LightTheme.BG_PRIMARY};
                border: 1px solid {LightTheme.BORDER_LIGHT};
                border-radius: {LightTheme.RADIUS_LARGE}px;
            }}
        """)

        # 图标和标题行
        title_layout = QHBoxLayout()
        if self.icon:
            icon_label = QLabel(self.icon)
            icon_label.setStyleSheet("font-size: 24px;")
            title_layout.addWidget(icon_label)

        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"font-size: {LightTheme.FONT_SMALL}px; color: {LightTheme.TEXT_HINT};")
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        layout.addLayout(title_layout)

        # 数值
        value_label = QLabel(self.value)
        value_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: bold;
            color: {self.color};
        """)
        layout.addWidget(value_label)

    def update_value(self, new_value: str):
        """更新数值"""
        # 查找并更新value_label
        layout = self.layout()
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if isinstance(widget, QLabel) and widget.text() == self.value:
                widget.setText(new_value)
                self.value = new_value
                break


class AIGuideDialog(QWidget):
    """AI推理功能引导对话框

    首次使用统计报告时显示,介绍AI任务完成推理功能并引导用户配置。
    参考 welcome_dialog.py 的设计风格,使用MacOS极简风格。
    """

    # Signal emitted when user clicks "立即配置" button
    config_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """设置UI界面"""
        # 窗口基本设置
        # ✅ P1-1.6.20: 移除WindowStaysOnTopHint,避免阻止其他窗口交互
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setFixedSize(500, 520)

        # 浅色主题背景和圆角
        self.setStyleSheet(f"""
            AIGuideDialog {{
                background-color: {LightTheme.BG_PRIMARY};
                border: 2px solid {LightTheme.BORDER_NORMAL};
                border-radius: {LightTheme.RADIUS_XLARGE}px;
            }}
        """)

        # 主布局
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(30, 30, 30, 30)

        # 顶部图标和标题行
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        # 图标
        icon_label = QLabel("🤖")
        icon_label.setStyleSheet(f"font-size: 40px;")
        header_layout.addWidget(icon_label)

        # 标题
        title_label = QLabel("AI任务完成推理")
        title_font = QFont()
        title_font.setPointSize(LightTheme.FONT_TITLE)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {LightTheme.TEXT_PRIMARY};")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # 副标题
        subtitle = QLabel("让AI帮你分析每日任务完成情况")
        subtitle.setStyleSheet(f"""
            font-size: {LightTheme.FONT_SUBTITLE}px;
            color: {LightTheme.TEXT_SECONDARY};
            padding: 0 0 8px 0;
        """)
        layout.addWidget(subtitle)

        # 功能介绍卡片
        features_card = QLabel(
            "✨ <b>核心功能</b><br><br>"
            "• <b>智能分析</b>: 根据活动日志自动推理任务完成情况<br>"
            "• <b>活动追踪</b>: 实时记录应用使用情况<br>"
            "• <b>精准匹配</b>: 将应用活动与任务时间段关联<br>"
            "• <b>批量处理</b>: 一键推理全天所有任务"
        )
        features_card.setWordWrap(True)
        features_card.setStyleSheet(f"""
            QLabel {{
                background-color: {LightTheme.BG_SECONDARY};
                border-left: 4px solid {LightTheme.ACCENT_GREEN};
                border-radius: {LightTheme.RADIUS_SMALL}px;
                padding: 16px;
                color: {LightTheme.TEXT_PRIMARY};
                font-size: {LightTheme.FONT_BODY}px;
                line-height: 1.6;
            }}
        """)
        layout.addWidget(features_card)

        # 使用说明
        usage_info = QLabel(
            "📋 <b>使用步骤</b><br><br>"
            "1. 开启「活动追踪」功能<br>"
            "2. 正常使用电脑工作<br>"
            "3. 点击「手动生成推理」按钮<br>"
            "4. 在弹出窗口中确认或修正完成度"
        )
        usage_info.setWordWrap(True)
        usage_info.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(33, 150, 243, 0.1);
                border-left: 4px solid {LightTheme.ACCENT_BLUE};
                border-radius: {LightTheme.RADIUS_SMALL}px;
                padding: 16px;
                color: {LightTheme.TEXT_PRIMARY};
                font-size: {LightTheme.FONT_BODY}px;
                line-height: 1.6;
            }}
        """)
        layout.addWidget(usage_info)

        # 提示信息
        hint_label = QLabel(
            "💡 提示: 如需配置应用分类规则,请前往「配置界面 → 行为识别」"
        )
        hint_label.setWordWrap(True)
        hint_label.setStyleSheet(f"""
            color: {LightTheme.TEXT_HINT};
            font-size: {LightTheme.FONT_SMALL}px;
            padding: 8px 0;
        """)
        layout.addWidget(hint_label)

        layout.addStretch()

        # 底部按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        # 稍后再说按钮
        later_btn = QPushButton("稍后再说")
        later_btn.setFixedHeight(40)
        later_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {LightTheme.BG_SECONDARY};
                color: {LightTheme.TEXT_PRIMARY};
                border: 1px solid {LightTheme.BORDER_NORMAL};
                border-radius: {LightTheme.RADIUS_MEDIUM}px;
                font-size: {LightTheme.FONT_BODY}px;
                font-weight: normal;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background-color: {LightTheme.BG_HOVER};
                border-color: {LightTheme.BORDER_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {LightTheme.BG_PRESSED};
            }}
        """)
        later_btn.clicked.connect(self.close)
        button_layout.addWidget(later_btn)

        # 立即配置按钮
        config_btn = QPushButton("立即配置 →")
        config_btn.setFixedHeight(40)
        config_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {LightTheme.ACCENT_GREEN};
                color: white;
                border: none;
                border-radius: {LightTheme.RADIUS_MEDIUM}px;
                font-size: {LightTheme.FONT_BODY}px;
                font-weight: bold;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background-color: {LightTheme.ACCENT_GREEN_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {LightTheme.ACCENT_GREEN_PRESSED};
            }}
        """)
        config_btn.clicked.connect(self._on_config_clicked)
        button_layout.addWidget(config_btn)

        layout.addLayout(button_layout)

    def _on_config_clicked(self):
        """立即配置按钮点击处理"""
        self.config_requested.emit()
        self.close()

    def showEvent(self, event):
        """窗口显示时自动居中"""
        super().showEvent(event)
        self.center_on_screen()

    def center_on_screen(self):
        """将窗口移动到屏幕中央"""
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().geometry()
        window_rect = self.frameGeometry()
        center_point = screen.center()
        window_rect.moveCenter(center_point)
        self.move(window_rect.topLeft())


class StatisticsWindow(QWidget):
    """统计报告主窗口"""

    closed = Signal()  # 关闭信号
    inference_completed = Signal(bool, str)  # 推理完成信号 (success, error_msg)

    def __init__(self, stats_manager: StatisticsManager, logger: logging.Logger, parent=None):
        super().__init__(parent)
        self.stats_manager = stats_manager
        self.logger = logger
        self._engine_connected = False  # 标记是否已连接自动推理引擎

        # 初始化洞察生成器
        self.insights_generator = InsightsGenerator(stats_manager, logger)

        # 初始化目标管理器和成就管理器
        if getattr(sys, 'frozen', False):
            app_dir = Path(sys.executable).parent
        else:
            app_dir = Path(__file__).parent
        data_dir = app_dir / 'gaiya' / 'data'
        self.goal_manager = GoalManager(data_dir, logger)
        self.achievement_manager = AchievementManager(data_dir, logger)

        # 初始化激励引擎 (自动更新目标和成就)
        self.motivation_engine = MotivationEngine(
            goal_manager=self.goal_manager,
            achievement_manager=self.achievement_manager,
            stats_manager=stats_manager,
            logger=logger
        )

        # 设置激励引擎的回调
        self.motivation_engine.on_goal_completed = self._on_goal_completed
        self.motivation_engine.on_achievement_unlocked = self._on_achievement_unlocked

        # 成就通知队列 (防止连续弹窗)
        self.pending_achievements = []
        self.achievement_notification_timer = QTimer(self)
        self.achievement_notification_timer.timeout.connect(self._show_batched_achievements)
        self.achievement_notification_timer.setSingleShot(True)

        # 初始化主题管理器
        self.theme_manager = ThemeManager(app_dir)
        self.theme_manager.register_ui_component(self)
        self.theme_manager.theme_changed.connect(self.apply_theme)

        self.init_ui()
        self.load_statistics()

        # 连接推理完成信号
        self.inference_completed.connect(self._on_inference_completed)

        # 注: 自动推理引擎连接延迟到 showEvent 中进行
        # 因为 main_window 属性在 __init__ 之后才会被设置

        # 应用初始主题
        self.apply_theme()

        # ✅ P1-1.6.20: 延迟显示AI引导对话框,避免与统计窗口冲突
        # self._show_ai_guide_if_needed()  # 移到showEvent中处理

        # 启动定时器: 每5分钟自动更新目标和成就
        self.motivation_timer = QTimer(self)
        self.motivation_timer.timeout.connect(self._update_motivation_system)
        self.motivation_timer.start(300000)  # 5分钟 = 300000毫秒

        # 首次启动时立即更新一次
        QTimer.singleShot(2000, self._update_motivation_system)  # 延迟2秒执行

    def _show_ai_guide_if_needed(self):
        """首次使用时显示AI功能引导对话框"""
        try:
            # 从config.json读取配置
            config_path = Path("config.json")
            config = {}
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

            # 检查是否已显示过引导对话框
            ai_guide_shown = config.get('ai_guide_shown', False)

            if not ai_guide_shown:
                # 创建并显示引导对话框
                guide_dialog = AIGuideDialog(self)

                # 连接"立即配置"信号
                guide_dialog.config_requested.connect(self._open_config_window)

                # 显示对话框
                guide_dialog.show()

                # 标记为已显示,保存到配置
                config['ai_guide_shown'] = True
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)

                self.logger.info("AI功能引导对话框已显示")
        except Exception as e:
            self.logger.warning(f"显示AI引导对话框失败: {e}")

    def _open_config_window(self):
        """打开配置窗口到行为识别页签"""
        try:
            # 获取主窗口引用 (在main.py的show_statistics中设置)
            main_window = getattr(self, 'main_window', None)
            if main_window is None:
                # 如果没有main_window引用,尝试从parent获取
                main_window = self.parent()

            if main_window is None:
                self.logger.warning("无法获取主窗口引用")
                QMessageBox.warning(
                    self,
                    "提示",
                    "无法打开配置窗口,请从主界面打开"
                )
                return

            # 调用主窗口的open_config_gui方法,传递行为识别页签的索引(4)
            if hasattr(main_window, 'open_config_gui'):
                main_window.open_config_gui(initial_tab=4)
                self.logger.info("已打开配置窗口到行为识别页签")
            else:
                self.logger.error("主窗口没有open_config_gui方法")
                QMessageBox.warning(
                    self,
                    "错误",
                    "无法打开配置窗口"
                )
        except Exception as e:
            self.logger.error(f"打开配置窗口失败: {e}")
            QMessageBox.warning(
                self,
                "错误",
                f"无法打开配置窗口:\n{str(e)}"
            )

    def init_ui(self):
        """初始化用户界面"""
        # 设置为独立的顶层窗口,而不是子窗口
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        self.setWindowTitle(f'任务统计报告 - GaiYa每日进度条 {VERSION_STRING}')

        # 设置窗口大小
        self.resize(900, 700)

        # 窗口居中显示 (避免出现在左上角)
        self.center_window()

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 顶部标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel("任务统计报告")
        self.title_label = title_label  # 保存引用以便主题更新
        title_label.setStyleSheet(f"font-size: {LightTheme.FONT_TITLE}px; font-weight: bold; color: {LightTheme.TEXT_PRIMARY};")
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        # 刷新按钮
        refresh_button = QPushButton(tr("statistics.btn_refresh"))
        refresh_button.setFixedHeight(36)
        refresh_button.setStyleSheet(StyleManager.button_minimal())
        refresh_button.clicked.connect(self.load_statistics)
        title_layout.addWidget(refresh_button)

        # 导出按钮
        export_button = QPushButton(tr("statistics.btn_export_csv"))
        export_button.setFixedHeight(36)
        export_button.setStyleSheet(StyleManager.button_primary())
        export_button.clicked.connect(self.export_statistics)
        title_layout.addWidget(export_button)

        main_layout.addLayout(title_layout)

        # 标签页
        self.tab_widget = QTabWidget()
        # 样式将在 apply_theme 中设置

        # 创建各个标签页
        self.create_today_tab()
        self.create_weekly_tab()
        self.create_monthly_tab()
        self.create_tasks_tab()
        self.create_goals_tab()  # 添加目标管理页签
        self.create_achievements_tab()  # 添加成就展示页签

        main_layout.addWidget(self.tab_widget)

    def create_behavior_shortcut(self):
        """创建行为摘要快捷跳转卡片"""
        shortcut_card = QWidget()
        shortcut_card.setStyleSheet(f"""
            QWidget {{
                background-color: {LightTheme.BG_TERTIARY};
                border: none;
                border-radius: {LightTheme.RADIUS_LARGE}px;
                padding: 16px;
            }}
            QWidget:hover {{
                background-color: {LightTheme.BG_HOVER};
            }}
        """)

        layout = QVBoxLayout(shortcut_card)

        # 图标 + 标题
        title_layout = QHBoxLayout()
        icon_label = QLabel("⚡")
        icon_label.setStyleSheet("font-size: 32px;")
        title_layout.addWidget(icon_label)

        title_label = QLabel("行为识别摘要")
        title_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {LightTheme.TEXT_PRIMARY};")
        title_layout.addWidget(title_label, 1)

        arrow_label = QLabel("→")
        arrow_label.setStyleSheet(f"font-size: 20px; color: {LightTheme.TEXT_HINT};")
        title_layout.addWidget(arrow_label)

        layout.addLayout(title_layout)

        # 描述文字
        desc_label = QLabel("查看完整的应用使用情况、行为分类分析和Top应用排行")
        desc_label.setStyleSheet(f"color: {LightTheme.TEXT_SECONDARY}; font-size: {LightTheme.FONT_BODY}px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # 点击跳转
        shortcut_card.mousePressEvent = lambda e: self.open_time_review_window()
        shortcut_card.setCursor(Qt.CursorShape.PointingHandCursor)

        return shortcut_card

    def create_today_overview_card(self) -> QWidget:
        """创建今日概览卡片"""
        card = QGroupBox("📊 今日概览")
        card.setStyleSheet(f"""
            QGroupBox {{
                background-color: {LightTheme.BG_SECONDARY};
                border: 1px solid {LightTheme.BORDER_LIGHT};
                border-radius: {LightTheme.RADIUS_LARGE}px;
                font-weight: bold;
                font-size: 14px;
                padding-top: 20px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                color: {LightTheme.TEXT_PRIMARY};
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 24, 16, 16)
        layout.setSpacing(12)

        # 统计数据行
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)

        # 获取推理任务数据
        tasks = self._get_inferred_tasks()
        total_minutes = sum(t.get('duration_minutes', 0) for t in tasks)
        hours = total_minutes // 60
        mins = total_minutes % 60
        time_str = f"{hours}小时{mins}分" if hours > 0 else f"{mins}分钟"

        # 总工作时长
        time_widget = self._create_stat_item("⏱️", "总工作时长", time_str)
        stats_layout.addWidget(time_widget)
        self.overview_time_widget = time_widget  # 保存引用

        # 完成任务数
        task_count = len(tasks)
        count_widget = self._create_stat_item("📋", "完成任务", f"{task_count}个")
        stats_layout.addWidget(count_widget)
        self.overview_count_widget = count_widget  # 保存引用

        # 最活跃时段
        active_period = self._get_most_active_period(tasks)
        period_widget = self._create_stat_item("🔥", "最活跃时段", active_period)
        stats_layout.addWidget(period_widget)
        self.overview_period_widget = period_widget  # 保存引用

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # 快捷操作按钮
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 8, 0, 0)

        timeline_btn = QPushButton("⏱️ 时间轴回放")
        timeline_btn.setStyleSheet(StyleManager.button_minimal())
        timeline_btn.setFixedHeight(32)
        timeline_btn.clicked.connect(self.open_time_review_window)
        buttons_layout.addWidget(timeline_btn)

        apps_btn = QPushButton("📊 应用统计")
        apps_btn.setStyleSheet(StyleManager.button_minimal())
        apps_btn.setFixedHeight(32)
        apps_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(3))
        buttons_layout.addWidget(apps_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        return card

    def _create_stat_item(self, icon: str, label: str, value: str) -> QWidget:
        """创建统计数据项"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # 图标和标签
        header = QLabel(f"{icon} {label}")
        header.setStyleSheet(f"color: {LightTheme.TEXT_SECONDARY}; font-size: {LightTheme.FONT_SMALL}px;")
        layout.addWidget(header)

        # 数值
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {LightTheme.TEXT_PRIMARY}; font-size: 18px; font-weight: bold;")
        layout.addWidget(value_label)

        # 保存引用以便后续更新
        widget.value_label = value_label

        return widget

    def create_task_timeline_card(self) -> QWidget:
        """创建任务时间线卡片"""
        card = QGroupBox("📋 今日任务时间线")
        card.setStyleSheet(f"""
            QGroupBox {{
                background-color: {LightTheme.BG_SECONDARY};
                border: 1px solid {LightTheme.BORDER_LIGHT};
                border-radius: {LightTheme.RADIUS_LARGE}px;
                font-weight: bold;
                font-size: 14px;
                padding-top: 20px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                color: {LightTheme.TEXT_PRIMARY};
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 24, 16, 16)
        layout.setSpacing(8)

        # 任务时间线列表容器
        self.timeline_task_list_widget = QWidget()
        self.timeline_task_list_layout = QVBoxLayout(self.timeline_task_list_widget)
        self.timeline_task_list_layout.setContentsMargins(0, 0, 0, 0)
        self.timeline_task_list_layout.setSpacing(8)

        # 初始加载任务
        tasks = self._get_inferred_tasks()
        if tasks:
            # 按开始时间排序
            sorted_tasks = sorted(tasks, key=lambda t: t.get('start_time', '00:00'))
            for task in sorted_tasks:
                task_widget = self._create_timeline_task_item(task)
                self.timeline_task_list_layout.addWidget(task_widget)
        else:
            empty_label = QLabel("暂无任务记录")
            empty_label.setStyleSheet(f"color: {LightTheme.TEXT_HINT}; font-size: {LightTheme.FONT_BODY}px; padding: 20px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.timeline_task_list_layout.addWidget(empty_label)

        layout.addWidget(self.timeline_task_list_widget)

        return card

    def _create_timeline_task_item(self, task: dict) -> QWidget:
        """创建时间线任务项"""
        widget = QWidget()
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {LightTheme.BG_TERTIARY};
                border-radius: {LightTheme.RADIUS_MEDIUM}px;
                padding: 8px;
            }}
        """)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(16)

        # 时间列
        start_time = task.get('start_time', '--:--')
        end_time = task.get('end_time', '--:--')
        time_label = QLabel(f"{start_time}-{end_time}")
        time_label.setStyleSheet(f"color: {LightTheme.ACCENT_BLUE}; font-size: {LightTheme.FONT_BODY}px; font-weight: bold; min-width: 90px;")
        layout.addWidget(time_label)

        # 任务名称
        task_name = task.get('name', '未知任务')
        name_label = QLabel(task_name)
        name_label.setStyleSheet(f"color: {LightTheme.TEXT_PRIMARY}; font-size: {LightTheme.FONT_BODY}px;")
        layout.addWidget(name_label, 1)

        # 时长
        duration = task.get('duration_minutes', 0)
        if duration >= 60:
            duration_str = f"{duration // 60}h{duration % 60}m"
        else:
            duration_str = f"{duration}min"
        duration_label = QLabel(duration_str)
        duration_label.setStyleSheet(f"color: {LightTheme.TEXT_SECONDARY}; font-size: {LightTheme.FONT_SMALL}px;")
        layout.addWidget(duration_label)

        # 应用列表
        apps = task.get('apps', [])
        if apps:
            apps_text = ", ".join(apps[:2])
            if len(apps) > 2:
                apps_text += f" +{len(apps) - 2}"
            apps_label = QLabel(f"💻 {apps_text}")
            apps_label.setStyleSheet(f"color: {LightTheme.TEXT_HINT}; font-size: {LightTheme.FONT_SMALL}px;")
            layout.addWidget(apps_label)

        return widget

    def create_daily_summary_card(self) -> QWidget:
        """创建今日总结分析卡片"""
        card = QGroupBox("📝 今日总结")
        card.setStyleSheet(f"""
            QGroupBox {{
                background-color: {LightTheme.BG_SECONDARY};
                border: 1px solid {LightTheme.BORDER_LIGHT};
                border-radius: {LightTheme.RADIUS_LARGE}px;
                font-weight: bold;
                font-size: 14px;
                padding-top: 20px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                color: {LightTheme.TEXT_PRIMARY};
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 24, 16, 16)
        layout.setSpacing(16)

        # 创建可刷新的内容容器
        self.summary_content_widget = QWidget()
        self.summary_content_layout = QVBoxLayout(self.summary_content_widget)
        self.summary_content_layout.setContentsMargins(0, 0, 0, 0)
        self.summary_content_layout.setSpacing(8)

        # 填充初始内容
        self._populate_daily_summary_content(self._get_inferred_tasks())

        layout.addWidget(self.summary_content_widget)

        return card

    def _populate_daily_summary_content(self, tasks: list):
        """填充今日总结内容"""
        layout = self.summary_content_layout

        # 主要工作 (Top 3)
        main_work_label = QLabel("🏆 主要工作")
        main_work_label.setStyleSheet(f"color: {LightTheme.TEXT_PRIMARY}; font-size: {LightTheme.FONT_BODY}px; font-weight: bold;")
        layout.addWidget(main_work_label)

        top_tasks = self._get_top_tasks_by_duration(tasks, 3)
        if top_tasks:
            for i, task in enumerate(top_tasks, 1):
                name = task.get('name', '未知任务')
                duration = task.get('duration_minutes', 0)
                if duration >= 60:
                    duration_str = f"{duration // 60}小时{duration % 60}分"
                else:
                    duration_str = f"{duration}分钟"
                item_label = QLabel(f"  {i}. {name} - {duration_str}")
                item_label.setStyleSheet(f"color: {LightTheme.TEXT_SECONDARY}; font-size: {LightTheme.FONT_BODY}px;")
                layout.addWidget(item_label)
        else:
            empty_label = QLabel("  暂无数据")
            empty_label.setStyleSheet(f"color: {LightTheme.TEXT_HINT}; font-size: {LightTheme.FONT_BODY}px;")
            layout.addWidget(empty_label)

        # 应用使用分布
        app_usage_label = QLabel("💻 应用使用")
        app_usage_label.setStyleSheet(f"color: {LightTheme.TEXT_PRIMARY}; font-size: {LightTheme.FONT_BODY}px; font-weight: bold; margin-top: 8px;")
        layout.addWidget(app_usage_label)

        app_summary = self._get_app_usage_summary(tasks)
        if app_summary:
            usage_text = " | ".join([f"{app} {pct}%" for app, pct in app_summary[:4]])
            usage_label = QLabel(f"  {usage_text}")
            usage_label.setStyleSheet(f"color: {LightTheme.TEXT_SECONDARY}; font-size: {LightTheme.FONT_BODY}px;")
            layout.addWidget(usage_label)
        else:
            empty_label = QLabel("  暂无数据")
            empty_label.setStyleSheet(f"color: {LightTheme.TEXT_HINT}; font-size: {LightTheme.FONT_BODY}px;")
            layout.addWidget(empty_label)

        # 专注度评估
        focus_label = QLabel("🎯 专注度评估")
        focus_label.setStyleSheet(f"color: {LightTheme.TEXT_PRIMARY}; font-size: {LightTheme.FONT_BODY}px; font-weight: bold; margin-top: 8px;")
        layout.addWidget(focus_label)

        focus_score, focus_text, switch_count, avg_duration = self._calculate_focus_metrics(tasks)
        stars = "⭐" * focus_score + "☆" * (5 - focus_score)
        focus_detail = QLabel(f"  {stars} ({focus_text})")
        focus_detail.setStyleSheet(f"color: {LightTheme.TEXT_SECONDARY}; font-size: {LightTheme.FONT_BODY}px;")
        layout.addWidget(focus_detail)

        if switch_count > 0:
            focus_stats = QLabel(f"  任务切换{switch_count}次，平均专注时长{avg_duration}分钟")
            focus_stats.setStyleSheet(f"color: {LightTheme.TEXT_HINT}; font-size: {LightTheme.FONT_SMALL}px;")
            layout.addWidget(focus_stats)

    def _refresh_today_overview(self, tasks: list):
        """刷新今日概览卡片"""
        if not hasattr(self, 'overview_time_widget'):
            return

        # 计算统计数据
        total_minutes = sum(t.get('duration_minutes', 0) for t in tasks)
        hours = total_minutes // 60
        mins = total_minutes % 60
        time_str = f"{hours}小时{mins}分" if hours > 0 else f"{mins}分钟"
        task_count = len(tasks)
        active_period = self._get_most_active_period(tasks)

        # 更新标签
        if hasattr(self.overview_time_widget, 'value_label'):
            self.overview_time_widget.value_label.setText(time_str)
        if hasattr(self.overview_count_widget, 'value_label'):
            self.overview_count_widget.value_label.setText(f"{task_count}个")
        if hasattr(self.overview_period_widget, 'value_label'):
            self.overview_period_widget.value_label.setText(active_period)

    def _refresh_task_timeline(self, tasks: list):
        """刷新任务时间线"""
        if not hasattr(self, 'timeline_task_list_layout'):
            return

        # 清空现有内容
        while self.timeline_task_list_layout.count():
            item = self.timeline_task_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 重新填充
        if tasks:
            sorted_tasks = sorted(tasks, key=lambda t: t.get('start_time', '00:00'))
            for task in sorted_tasks:
                task_widget = self._create_timeline_task_item(task)
                self.timeline_task_list_layout.addWidget(task_widget)
        else:
            empty_label = QLabel("暂无任务记录")
            empty_label.setStyleSheet(f"color: {LightTheme.TEXT_HINT}; font-size: {LightTheme.FONT_BODY}px; padding: 20px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.timeline_task_list_layout.addWidget(empty_label)

    def _refresh_daily_summary(self, tasks: list):
        """刷新今日总结"""
        if not hasattr(self, 'summary_content_layout'):
            return

        # 清空现有内容
        while self.summary_content_layout.count():
            item = self.summary_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 重新填充内容
        self._populate_daily_summary_content(tasks)

    def _get_inferred_tasks(self) -> list:
        """获取推理任务列表"""
        if hasattr(self, 'auto_inference_engine') and self.auto_inference_engine:
            return self.auto_inference_engine.inferred_tasks or []
        return []

    def _get_most_active_period(self, tasks: list) -> str:
        """获取最活跃时段"""
        if not tasks:
            return "--"

        # 按小时统计时长
        hour_duration = {}
        for task in tasks:
            start_time = task.get('start_time', '00:00')
            duration = task.get('duration_minutes', 0)
            try:
                hour = int(start_time.split(':')[0])
                hour_duration[hour] = hour_duration.get(hour, 0) + duration
            except (ValueError, IndexError):
                continue

        if not hour_duration:
            return "--"

        # 找到最活跃的小时
        max_hour = max(hour_duration, key=hour_duration.get)
        return f"{max_hour:02d}:00-{max_hour+1:02d}:00"

    def _get_top_tasks_by_duration(self, tasks: list, limit: int) -> list:
        """获取按时长排序的Top N任务"""
        if not tasks:
            return []
        return sorted(tasks, key=lambda t: t.get('duration_minutes', 0), reverse=True)[:limit]

    def _get_app_usage_summary(self, tasks: list) -> list:
        """获取应用使用分布"""
        if not tasks:
            return []

        # 统计每个应用的总时长
        app_duration = {}
        total_duration = 0
        for task in tasks:
            duration = task.get('duration_minutes', 0)
            apps = task.get('apps', [])
            # 将任务时长平均分配给使用的应用
            if apps:
                per_app_duration = duration / len(apps)
                for app in apps:
                    app_duration[app] = app_duration.get(app, 0) + per_app_duration
                    total_duration += per_app_duration

        if total_duration == 0:
            return []

        # 计算百分比并排序
        result = []
        for app, duration in sorted(app_duration.items(), key=lambda x: x[1], reverse=True):
            pct = int(duration / total_duration * 100)
            if pct > 0:
                result.append((app, pct))

        return result

    def _calculate_focus_metrics(self, tasks: list) -> tuple:
        """计算专注度指标"""
        if not tasks:
            return (3, "一般", 0, 0)

        task_count = len(tasks)
        total_minutes = sum(t.get('duration_minutes', 0) for t in tasks)

        if total_minutes == 0:
            return (3, "一般", 0, 0)

        avg_duration = total_minutes // task_count if task_count > 0 else 0
        switch_count = max(0, task_count - 1)

        # 根据平均专注时长评分
        if avg_duration >= 60:
            score = 5
            text = "非常专注"
        elif avg_duration >= 45:
            score = 4
            text = "较专注"
        elif avg_duration >= 30:
            score = 3
            text = "一般"
        elif avg_duration >= 15:
            score = 2
            text = "较分散"
        else:
            score = 1
            text = "需改进"

        return (score, text, switch_count, avg_duration)

    def create_auto_inference_summary(self):
        """创建自动推理摘要卡片 (方案A: 全自动推理模式)"""
        summary_group = QGroupBox("🎯 今日工作任务 (AI自动识别)")
        summary_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        layout = QVBoxLayout(summary_group)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 状态指示行
        status_layout = QHBoxLayout()

        # 状态图标
        status_icon = QLabel("🟢")
        status_icon.setStyleSheet("font-size: 16px;")
        status_layout.addWidget(status_icon)

        # 状态文字
        status_label = QLabel("AI运行中 (每5分钟自动分析)")
        status_label.setStyleSheet(f"color: {LightTheme.TEXT_SECONDARY}; font-size: {LightTheme.FONT_SMALL}px;")
        status_layout.addWidget(status_label)

        status_layout.addStretch()

        # 最后更新时间
        self.last_inference_time_label = QLabel("最后更新: --")
        self.last_inference_time_label.setStyleSheet(f"color: {LightTheme.TEXT_HINT}; font-size: {LightTheme.FONT_SMALL}px;")
        status_layout.addWidget(self.last_inference_time_label)

        layout.addLayout(status_layout)

        # 推理结果摘要
        self.inference_summary_label = QLabel("今日已识别 <b>0</b> 个工作任务 · 总计工作时长: <b>0分钟</b>")
        self.inference_summary_label.setStyleSheet(f"font-size: {LightTheme.FONT_BODY}px; color: {LightTheme.TEXT_PRIMARY};")
        layout.addWidget(self.inference_summary_label)

        # 推理任务列表容器
        self.inference_task_list_widget = QWidget()
        self.inference_task_list_layout = QVBoxLayout(self.inference_task_list_widget)
        self.inference_task_list_layout.setContentsMargins(0, 8, 0, 0)
        self.inference_task_list_layout.setSpacing(8)

        layout.addWidget(self.inference_task_list_widget)

        # 快捷操作按钮区域
        quick_actions_layout = QHBoxLayout()
        quick_actions_layout.setContentsMargins(0, 12, 0, 0)

        # 时间轴回放按钮
        timeline_btn = QPushButton("⏱️ 时间轴回放")
        timeline_btn.setStyleSheet(StyleManager.button_minimal())
        timeline_btn.setFixedHeight(32)
        timeline_btn.clicked.connect(self.open_time_review_window)
        timeline_btn.setToolTip("查看今日详细的时间使用情况")
        quick_actions_layout.addWidget(timeline_btn)

        # 应用统计按钮
        apps_btn = QPushButton("📊 应用统计")
        apps_btn.setStyleSheet(StyleManager.button_minimal())
        apps_btn.setFixedHeight(32)
        apps_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(3))  # 跳转到任务分类tab
        apps_btn.setToolTip("查看应用使用统计分析")
        quick_actions_layout.addWidget(apps_btn)

        quick_actions_layout.addStretch()

        layout.addLayout(quick_actions_layout)

        return summary_group

    def create_inferred_task_card(self, task: dict) -> QWidget:
        """
        创建推理任务卡片

        Args:
            task: {
                'name': '代码开发',
                'confidence': 0.9,
                'start_time': '14:30',
                'end_time': '15:00',
                'duration_minutes': 30,
                'apps': ['vscode', 'chrome']
            }
        """
        card = QWidget()
        card.setStyleSheet(f"""
            QWidget {{
                background-color: {LightTheme.BG_SECONDARY};
                border-radius: {LightTheme.RADIUS_MEDIUM}px;
                padding: 12px;
            }}
            QWidget:hover {{
                background-color: {LightTheme.BG_TERTIARY};
            }}
        """)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)

        # 左侧: 任务信息
        info_layout = QVBoxLayout()

        # 任务名称
        task_name = task.get('name', '未知任务')
        name_label = QLabel(f"📋 {task_name}")
        name_label.setStyleSheet(f"font-weight: bold; color: {LightTheme.TEXT_PRIMARY}; font-size: {LightTheme.FONT_BODY}px;")
        info_layout.addWidget(name_label)

        # 时间范围 + 时长
        start_time = task.get('start_time', '--:--')
        end_time = task.get('end_time', '--:--')
        duration = task.get('duration_minutes', 0)
        time_label = QLabel(f"⏰ {start_time} - {end_time} ({duration}分钟)")
        time_label.setStyleSheet(f"color: {LightTheme.TEXT_SECONDARY}; font-size: {LightTheme.FONT_SMALL}px;")
        info_layout.addWidget(time_label)

        # 相关应用
        apps = task.get('apps', [])
        apps_text = ", ".join(apps[:3]) if apps else "无"
        apps_label = QLabel(f"💻 应用: {apps_text}")
        apps_label.setStyleSheet(f"color: {LightTheme.TEXT_HINT}; font-size: {LightTheme.FONT_SMALL}px;")
        info_layout.addWidget(apps_label)

        layout.addLayout(info_layout, 1)

        # 右侧: 置信度标签 (友好化显示)
        confidence = task.get('confidence', 0.0)

        # 根据置信度设置不同的文案和颜色
        if confidence >= 0.9:
            confidence_text = "✨ 非常确定"
            confidence_color = LightTheme.ACCENT_GREEN
            tooltip_text = f"AI非常确信您在做这个任务\n准确度: {confidence:.0%}"
        elif confidence >= 0.8:
            confidence_text = "✓ 比较确定"
            confidence_color = LightTheme.ACCENT_GREEN
            tooltip_text = f"AI比较确信,建议检查一下\n准确度: {confidence:.0%}"
        else:
            confidence_text = "? 需要确认"
            confidence_color = LightTheme.ACCENT_ORANGE
            tooltip_text = f"AI不太确定,请您确认\n准确度: {confidence:.0%}"

        confidence_badge = QLabel(confidence_text)
        confidence_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        confidence_badge.setFixedHeight(24)
        confidence_badge.setToolTip(tooltip_text)
        confidence_badge.setStyleSheet(f"""
            QLabel {{
                background-color: {confidence_color};
                color: white;
                border-radius: 12px;
                font-size: {LightTheme.FONT_SMALL}px;
                font-weight: bold;
                padding: 0 12px;
            }}
        """)
        layout.addWidget(confidence_badge)

        return card

    def update_inference_ui(self, inferred_tasks: list):
        """
        更新推理UI (方案A)

        Args:
            inferred_tasks: 推理任务列表
        """
        try:
            # 新版工作日志Tab - 刷新三个卡片
            if not hasattr(self, 'inference_summary_label') or self.inference_summary_label is None:
                self.logger.debug(f"推理数据已更新: {len(inferred_tasks)} 个任务")
                # 刷新今日概览卡片
                self._refresh_today_overview(inferred_tasks)
                # 刷新任务时间线
                self._refresh_task_timeline(inferred_tasks)
                # 刷新今日总结
                self._refresh_daily_summary(inferred_tasks)
                self.logger.info(f"工作日志已刷新: {len(inferred_tasks)} 个任务")
                return

            # 旧版UI更新逻辑（兼容）
            # 计算总工作时长
            total_minutes = sum(t.get('duration_minutes', 0) for t in inferred_tasks)

            # 更新摘要 - 不再显示置信度,改为显示总时长
            self.inference_summary_label.setText(
                f"今日已识别 <b>{len(inferred_tasks)}</b> 个工作任务 · "
                f"总计工作时长: <b>{total_minutes}分钟</b>"
            )

            # 更新时间
            from datetime import datetime
            if hasattr(self, 'last_inference_time_label') and self.last_inference_time_label:
                self.last_inference_time_label.setText(f"最后更新: {datetime.now().strftime('%H:%M')}")

            # 清空现有任务列表
            if hasattr(self, 'inference_task_list_layout') and self.inference_task_list_layout:
                while self.inference_task_list_layout.count():
                    child = self.inference_task_list_layout.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()

                # 添加新任务卡片 (只显示最近5个)
                for task in inferred_tasks[-5:]:
                    card = self.create_inferred_task_card(task)
                    self.inference_task_list_layout.addWidget(card)

            self.logger.info(f"推理UI已更新: {len(inferred_tasks)} 个任务")

        except Exception as e:
            self.logger.error(f"更新推理UI失败: {e}", exc_info=True)

    def open_time_review_window(self):
        """打开今日回放窗口"""
        try:
            from gaiya.ui.time_review_window import TimeReviewWindow
            self.time_review_window = TimeReviewWindow()
            self.time_review_window.show()
        except Exception as e:
            logging.error(f"打开今日回放窗口失败: {e}")
            QMessageBox.warning(self, "错误", f"无法打开今日回放窗口: {str(e)}")

    def create_today_tab(self):
        """创建今日统计标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)

        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        # 样式将在 apply_theme 中设置

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)  # 设置组件之间的间距
        content_layout.setContentsMargins(15, 15, 15, 15)  # 设置内容边距

        # 今日概览卡片
        overview_card = self.create_today_overview_card()
        content_layout.addWidget(overview_card)

        # 任务时间线
        timeline_card = self.create_task_timeline_card()
        content_layout.addWidget(timeline_card)

        # 今日总结分析
        summary_card = self.create_daily_summary_card()
        content_layout.addWidget(summary_card)

        # 导出按钮区域
        export_layout = QHBoxLayout()
        export_layout.addStretch()

        export_log_btn = QPushButton("📤 导出工作日志")
        export_log_btn.setStyleSheet(StyleManager.button_primary())
        export_log_btn.setFixedHeight(36)
        export_log_btn.clicked.connect(self.export_work_log)
        export_log_btn.setToolTip("将今日工作任务导出为Markdown格式")
        export_layout.addWidget(export_log_btn)

        export_layout.addStretch()
        content_layout.addLayout(export_layout)

        # 保留confirm_button和ai_analysis_button的引用,避免其他代码报错
        self.confirm_button = QPushButton()  # 占位按钮,不添加到界面
        self.ai_analysis_button = QPushButton()  # 占位按钮,不添加到界面

        content_layout.addStretch()

        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        self.tab_widget.addTab(tab, tr("statistics.tab.today"))

    def create_weekly_tab(self):
        """创建本周统计标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)

        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        # 样式将在 apply_theme 中设置

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)  # 设置组件之间的间距
        content_layout.setContentsMargins(15, 15, 15, 15)  # 设置内容边距

        # 本周统计摘要 (卡片式设计)
        weekly_summary_group = QGroupBox("📊 本周统计摘要")
        weekly_summary_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        weekly_summary_layout = QVBoxLayout(weekly_summary_group)

        # 统计卡片布局
        cards_layout = QHBoxLayout()

        # 总任务数卡片
        total_card = QWidget()
        total_card_layout = QVBoxLayout(total_card)
        total_card_layout.setContentsMargins(10, 10, 10, 10)
        total_card_layout.setSpacing(5)
        self.weekly_total_label = QLabel("0")
        self.weekly_total_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {LightTheme.ACCENT_BLUE};")
        self.weekly_total_label.setAlignment(Qt.AlignCenter)
        total_card_layout.addWidget(self.weekly_total_label)
        total_card_name = QLabel("📝 总任务")
        total_card_name.setStyleSheet(f"font-size: {LightTheme.FONT_SMALL}px; color: {LightTheme.TEXT_HINT};")
        total_card_name.setAlignment(Qt.AlignCenter)
        total_card_layout.addWidget(total_card_name)
        total_card.setStyleSheet(f"""
            QWidget {{
                background-color: {LightTheme.BG_TERTIARY};
                border: none;
                border-radius: {LightTheme.RADIUS_LARGE}px;
            }}
        """)
        cards_layout.addWidget(total_card)

        # 已完成卡片
        completed_card = QWidget()
        completed_card_layout = QVBoxLayout(completed_card)
        completed_card_layout.setContentsMargins(10, 10, 10, 10)
        completed_card_layout.setSpacing(5)
        self.weekly_completed_label = QLabel("0")
        self.weekly_completed_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {LightTheme.ACCENT_GREEN};")
        self.weekly_completed_label.setAlignment(Qt.AlignCenter)
        completed_card_layout.addWidget(self.weekly_completed_label)
        completed_card_name = QLabel("✅ 已完成")
        completed_card_name.setStyleSheet(f"font-size: {LightTheme.FONT_SMALL}px; color: {LightTheme.TEXT_HINT};")
        completed_card_name.setAlignment(Qt.AlignCenter)
        completed_card_layout.addWidget(completed_card_name)
        completed_card.setStyleSheet(f"""
            QWidget {{
                background-color: {LightTheme.BG_TERTIARY};
                border: none;
                border-radius: {LightTheme.RADIUS_LARGE}px;
            }}
        """)
        cards_layout.addWidget(completed_card)

        # 平均完成率卡片
        avg_card = QWidget()
        avg_card_layout = QVBoxLayout(avg_card)
        avg_card_layout.setContentsMargins(10, 10, 10, 10)
        avg_card_layout.setSpacing(5)
        self.weekly_avg_label = QLabel("0%")
        self.weekly_avg_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {LightTheme.ACCENT_ORANGE};")
        self.weekly_avg_label.setAlignment(Qt.AlignCenter)
        avg_card_layout.addWidget(self.weekly_avg_label)
        avg_card_name = QLabel("📈 平均完成率")
        avg_card_name.setStyleSheet(f"font-size: {LightTheme.FONT_SMALL}px; color: {LightTheme.TEXT_HINT};")
        avg_card_name.setAlignment(Qt.AlignCenter)
        avg_card_layout.addWidget(avg_card_name)
        avg_card.setStyleSheet(f"""
            QWidget {{
                background-color: {LightTheme.BG_TERTIARY};
                border: none;
                border-radius: {LightTheme.RADIUS_LARGE}px;
            }}
        """)
        cards_layout.addWidget(avg_card)

        # 总时长卡片
        hours_card = QWidget()
        hours_card_layout = QVBoxLayout(hours_card)
        hours_card_layout.setContentsMargins(10, 10, 10, 10)
        hours_card_layout.setSpacing(5)
        self.weekly_hours_label = QLabel("0h")
        self.weekly_hours_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {LightTheme.ACCENT_BLUE};")
        self.weekly_hours_label.setAlignment(Qt.AlignCenter)
        hours_card_layout.addWidget(self.weekly_hours_label)
        hours_card_name = QLabel("⏱️ 总时长")
        hours_card_name.setStyleSheet(f"font-size: {LightTheme.FONT_SMALL}px; color: {LightTheme.TEXT_HINT};")
        hours_card_name.setAlignment(Qt.AlignCenter)
        hours_card_layout.addWidget(hours_card_name)
        hours_card.setStyleSheet(f"""
            QWidget {{
                background-color: {LightTheme.BG_TERTIARY};
                border: none;
                border-radius: {LightTheme.RADIUS_LARGE}px;
            }}
        """)
        cards_layout.addWidget(hours_card)

        weekly_summary_layout.addLayout(cards_layout)
        content_layout.addWidget(weekly_summary_group)

        # 任务完成率趋势图
        chart_group = QGroupBox("📈 完成率趋势")
        chart_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        chart_layout = QVBoxLayout(chart_group)
        chart_layout.setContentsMargins(10, 10, 10, 10)

        # 创建并添加折线图
        trend_chart = self.create_completion_trend_chart()
        chart_layout.addWidget(trend_chart)

        content_layout.addWidget(chart_group)

        # 任务分类饼图
        pie_chart_group = QGroupBox("📊 任务分类分布")
        pie_chart_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        pie_chart_layout = QVBoxLayout(pie_chart_group)
        pie_chart_layout.setContentsMargins(10, 10, 10, 10)

        # 创建并添加饼图
        category_pie_chart = self.create_category_pie_chart()
        pie_chart_layout.addWidget(category_pie_chart)

        content_layout.addWidget(pie_chart_group)

        # 智能洞察报告 (Sprint 3 - Task 3.2)
        insights_group = QGroupBox("💡 本周智能洞察")
        insights_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        insights_layout = QVBoxLayout(insights_group)
        insights_layout.setContentsMargins(10, 10, 10, 10)

        # 创建并添加洞察报告
        insights_widget = self.create_insights_widget()
        insights_layout.addWidget(insights_widget)

        content_layout.addWidget(insights_group)

        # 每日趋势表格
        trend_group = QGroupBox(tr("statistics.table.daily_completion"))
        trend_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        trend_layout = QVBoxLayout(trend_group)

        self.weekly_table = QTableWidget()
        self.weekly_table.setColumnCount(6)
        self.weekly_table.setHorizontalHeaderLabels([
            tr("statistics.table.date"),
            tr("statistics.table.weekday"),
            tr("statistics.table.task_count"),
            tr("statistics.table.completed_count"),
            tr("statistics.table.planned_hours"),
            tr("statistics.table.completion_rate")
        ])
        self.weekly_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.weekly_table.setAlternatingRowColors(True)
        self.weekly_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {LightTheme.BG_PRIMARY};
                border: 1px solid {LightTheme.BORDER_LIGHT};
                border-radius: {LightTheme.RADIUS_MEDIUM}px;
                gridline-color: {LightTheme.BORDER_LIGHT};
                color: {LightTheme.TEXT_PRIMARY};
            }}
            QTableWidget::item {{
                padding: 8px;
                color: {LightTheme.TEXT_PRIMARY};
            }}
            QHeaderView::section {{
                background-color: {LightTheme.BG_SECONDARY};
                color: {LightTheme.TEXT_PRIMARY};
                padding: 8px;
                border: none;
                font-weight: bold;
                font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
            }}
            QHeaderView:horizontal::section {{
                border-bottom: 2px solid {LightTheme.ACCENT_BLUE};
            }}
            QHeaderView:vertical::section {{
                border-right: 1px solid {LightTheme.BORDER_LIGHT};
                text-align: center;
            }}
        """)

        trend_layout.addWidget(self.weekly_table)
        content_layout.addWidget(trend_group)

        content_layout.addStretch()

        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        self.tab_widget.addTab(tab, tr("statistics.tab.weekly"))

    def create_monthly_tab(self):
        """创建本月统计标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)

        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {LightTheme.BG_PRIMARY};
                border: none;
            }}
        """)

        content_widget = QWidget()
        content_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {LightTheme.BG_PRIMARY};
            }}
        """)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)  # 设置组件之间的间距
        content_layout.setContentsMargins(15, 15, 15, 15)  # 设置内容边距

        # 本月统计摘要 (卡片式设计)
        monthly_summary_group = QGroupBox("📊 本月统计摘要")
        monthly_summary_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        monthly_summary_layout = QVBoxLayout(monthly_summary_group)

        # 统计卡片布局
        cards_layout = QHBoxLayout()

        # 总任务数卡片
        total_card = QWidget()
        total_card_layout = QVBoxLayout(total_card)
        total_card_layout.setContentsMargins(10, 10, 10, 10)
        total_card_layout.setSpacing(5)
        self.monthly_total_label = QLabel("0")
        self.monthly_total_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {LightTheme.ACCENT_BLUE};")
        self.monthly_total_label.setAlignment(Qt.AlignCenter)
        total_card_layout.addWidget(self.monthly_total_label)
        total_card_name = QLabel("📝 总任务")
        total_card_name.setStyleSheet(f"font-size: {LightTheme.FONT_SMALL}px; color: {LightTheme.TEXT_HINT};")
        total_card_name.setAlignment(Qt.AlignCenter)
        total_card_layout.addWidget(total_card_name)
        total_card.setStyleSheet(f"""
            QWidget {{
                background-color: {LightTheme.BG_TERTIARY};
                border: none;
                border-radius: {LightTheme.RADIUS_LARGE}px;
            }}
        """)
        cards_layout.addWidget(total_card)

        # 已完成卡片
        completed_card = QWidget()
        completed_card_layout = QVBoxLayout(completed_card)
        completed_card_layout.setContentsMargins(10, 10, 10, 10)
        completed_card_layout.setSpacing(5)
        self.monthly_completed_label = QLabel("0")
        self.monthly_completed_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {LightTheme.ACCENT_GREEN};")
        self.monthly_completed_label.setAlignment(Qt.AlignCenter)
        completed_card_layout.addWidget(self.monthly_completed_label)
        completed_card_name = QLabel("✅ 已完成")
        completed_card_name.setStyleSheet(f"font-size: {LightTheme.FONT_SMALL}px; color: {LightTheme.TEXT_HINT};")
        completed_card_name.setAlignment(Qt.AlignCenter)
        completed_card_layout.addWidget(completed_card_name)
        completed_card.setStyleSheet(f"""
            QWidget {{
                background-color: {LightTheme.BG_TERTIARY};
                border: none;
                border-radius: {LightTheme.RADIUS_LARGE}px;
            }}
        """)
        cards_layout.addWidget(completed_card)

        # 平均完成率卡片
        avg_card = QWidget()
        avg_card_layout = QVBoxLayout(avg_card)
        avg_card_layout.setContentsMargins(10, 10, 10, 10)
        avg_card_layout.setSpacing(5)
        self.monthly_avg_label = QLabel("0%")
        self.monthly_avg_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {LightTheme.ACCENT_ORANGE};")
        self.monthly_avg_label.setAlignment(Qt.AlignCenter)
        avg_card_layout.addWidget(self.monthly_avg_label)
        avg_card_name = QLabel("📈 平均完成率")
        avg_card_name.setStyleSheet(f"font-size: {LightTheme.FONT_SMALL}px; color: {LightTheme.TEXT_HINT};")
        avg_card_name.setAlignment(Qt.AlignCenter)
        avg_card_layout.addWidget(avg_card_name)
        avg_card.setStyleSheet(f"""
            QWidget {{
                background-color: {LightTheme.BG_TERTIARY};
                border: none;
                border-radius: {LightTheme.RADIUS_LARGE}px;
            }}
        """)
        cards_layout.addWidget(avg_card)

        # 总时长卡片
        hours_card = QWidget()
        hours_card_layout = QVBoxLayout(hours_card)
        hours_card_layout.setContentsMargins(10, 10, 10, 10)
        hours_card_layout.setSpacing(5)
        self.monthly_hours_label = QLabel("0h")
        self.monthly_hours_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {LightTheme.ACCENT_BLUE};")
        self.monthly_hours_label.setAlignment(Qt.AlignCenter)
        hours_card_layout.addWidget(self.monthly_hours_label)
        hours_card_name = QLabel("⏱️ 总时长")
        hours_card_name.setStyleSheet(f"font-size: {LightTheme.FONT_SMALL}px; color: {LightTheme.TEXT_HINT};")
        hours_card_name.setAlignment(Qt.AlignCenter)
        hours_card_layout.addWidget(hours_card_name)
        hours_card.setStyleSheet(f"""
            QWidget {{
                background-color: {LightTheme.BG_TERTIARY};
                border: none;
                border-radius: {LightTheme.RADIUS_LARGE}px;
            }}
        """)
        cards_layout.addWidget(hours_card)

        monthly_summary_layout.addLayout(cards_layout)
        content_layout.addWidget(monthly_summary_group)

        # 每日统计表格
        daily_group = QGroupBox(tr("statistics.table.daily_stats"))
        daily_group.setStyleSheet("QGroupBox::title { color: #666666; font-weight: bold; font-size: 14px; }")
        daily_layout = QVBoxLayout(daily_group)

        self.monthly_table = QTableWidget()
        self.monthly_table.setColumnCount(5)
        self.monthly_table.setHorizontalHeaderLabels([
            tr("statistics.table.date"),
            tr("statistics.table.task_count"),
            tr("statistics.table.completed_count"),
            tr("statistics.table.planned_hours"),
            tr("statistics.table.completion_rate")
        ])
        self.monthly_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.monthly_table.setAlternatingRowColors(True)
        self.monthly_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {LightTheme.BG_PRIMARY};
                border: 1px solid {LightTheme.BORDER_LIGHT};
                border-radius: {LightTheme.RADIUS_MEDIUM}px;
                gridline-color: {LightTheme.BORDER_LIGHT};
                color: {LightTheme.TEXT_PRIMARY};
            }}
            QTableWidget::item {{
                padding: 8px;
                color: {LightTheme.TEXT_PRIMARY};
            }}
            QHeaderView::section {{
                background-color: {LightTheme.BG_SECONDARY};
                color: {LightTheme.TEXT_PRIMARY};
                padding: 8px;
                border: none;
                font-weight: bold;
                font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
            }}
            QHeaderView:horizontal::section {{
                border-bottom: 2px solid {LightTheme.ACCENT_BLUE};
            }}
            QHeaderView:vertical::section {{
                border-right: 1px solid {LightTheme.BORDER_LIGHT};
                text-align: center;
            }}
        """)

        daily_layout.addWidget(self.monthly_table)
        content_layout.addWidget(daily_group)

        content_layout.addStretch()

        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        self.tab_widget.addTab(tab, tr("statistics.tab.monthly"))

    def create_tasks_tab(self):
        """创建任务分类统计标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)  # 设置组件之间的间距

        # 标题
        title_label = QLabel(tr("statistics.tab.category_history"))
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(title_label)

        # 任务统计表格
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(4)
        self.tasks_table.setHorizontalHeaderLabels([
            tr("statistics.table.task_name"),
            tr("statistics.table.completion_times"),
            tr("statistics.table.total_hours"),
            tr("statistics.table.color")
        ])
        self.tasks_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tasks_table.setAlternatingRowColors(True)
        self.tasks_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {LightTheme.BG_PRIMARY};
                border: 1px solid {LightTheme.BORDER_LIGHT};
                border-radius: {LightTheme.RADIUS_MEDIUM}px;
                gridline-color: {LightTheme.BORDER_LIGHT};
                color: {LightTheme.TEXT_PRIMARY};
            }}
            QTableWidget::item {{
                padding: 8px;
                color: {LightTheme.TEXT_PRIMARY};
            }}
            QHeaderView::section {{
                background-color: {LightTheme.BG_SECONDARY};
                color: {LightTheme.TEXT_PRIMARY};
                padding: 8px;
                border: none;
                font-weight: bold;
                font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
            }}
            QHeaderView:horizontal::section {{
                border-bottom: 2px solid {LightTheme.ACCENT_BLUE};
            }}
            QHeaderView:vertical::section {{
                border-right: 1px solid {LightTheme.BORDER_LIGHT};
                text-align: center;
            }}
        """)

        layout.addWidget(self.tasks_table)

        self.tab_widget.addTab(tab, tr("statistics.tab.category"))

    def load_statistics(self):
        """加载统计数据"""
        try:
            self.logger.info(tr("statistics.message.loading_start"))

            # 加载今日统计
            self.load_today_statistics()

            # 加载本周统计
            self.load_weekly_statistics()

            # 加载本月统计
            self.load_monthly_statistics()

            # 加载任务分类统计
            self.load_task_statistics()

            self.logger.info(tr("statistics.message.loading_complete"))

        except Exception as e:
            self.logger.error(tr("statistics.error.loading_failed_log", e=e), exc_info=True)
            QMessageBox.warning(self, tr("statistics.error.error_title"), tr("statistics.error.loading_failed_message", error=str(e)))

    def load_today_statistics(self):
        """加载今日统计 - 从数据库获取实际活动数据"""
        try:
            # 新版工作日志Tab不再使用旧组件,数据在打开窗口时通过 _get_inferred_tasks() 获取
            if not hasattr(self, 'inference_summary_label') or self.inference_summary_label is None:
                self.logger.debug("今日统计已加载 (新版UI在创建时获取数据)")
                return

            # ✅ P1-1.6.21: 直接从数据库加载今日活动数据,与时间回放保持一致
            activity_stats = db.get_today_activity_stats()

            if activity_stats:
                total_seconds = activity_stats.get('total_seconds', 0)
                total_minutes = total_seconds // 60
                top_apps = activity_stats.get('top_apps', [])

                # 计算工作任务数量(使用PRODUCTIVE类别的应用数量)
                productive_apps = [app for app in top_apps if app.get('category') == 'PRODUCTIVE']
                task_count = len(productive_apps)

                # 计算工作时长(PRODUCTIVE类别的总时长)
                categories = activity_stats.get('categories', {})
                work_seconds = categories.get('PRODUCTIVE', 0)
                work_minutes = work_seconds // 60

                # 更新UI显示
                self.inference_summary_label.setText(
                    f"今日已识别 <b>{task_count}</b> 个工作任务 · "
                    f"总计工作时长: <b>{work_minutes}分钟</b>"
                )

                # 更新最后更新时间
                from datetime import datetime
                if hasattr(self, 'last_inference_time_label') and self.last_inference_time_label:
                    self.last_inference_time_label.setText(f"最后更新: {datetime.now().strftime('%H:%M')}")

                # 清空现有任务列表
                if hasattr(self, 'inference_task_list_layout') and self.inference_task_list_layout:
                    while self.inference_task_list_layout.count():
                        child = self.inference_task_list_layout.takeAt(0)
                        if child.widget():
                            child.widget().deleteLater()

                    # 添加TOP应用卡片(只显示PRODUCTIVE类别的前5个)
                    for app in productive_apps[:5]:
                        app_minutes = app.get('duration', 0) // 60
                        task_data = {
                            'name': app.get('name', '未知应用'),
                            'duration_minutes': app_minutes,
                            'confidence': 1.0,  # 实际数据,置信度100%
                            'apps': [app.get('name', '')]
                        }
                        card = self.create_inferred_task_card(task_data)
                        self.inference_task_list_layout.addWidget(card)

                self.logger.info(f"今日统计已加载: {task_count} 个工作任务, {work_minutes}分钟")
            else:
                self.logger.info("今日统计: 暂无活动数据")

        except Exception as e:
            self.logger.error(f"加载今日统计失败: {e}", exc_info=True)

    def update_ai_summary(self, summary: dict):
        """更新AI推理数据摘要 (已废弃,保留用于兼容性)

        注: 今日统计页签已完全重构为自动推理模式(方案A)
        AI推理数据通过 update_inference_ui() 方法实时更新
        此方法保留仅为避免调用处报错

        Args:
            summary: 统计摘要数据
        """
        # 不再更新UI,自动推理引擎会通过信号槽实时更新
        pass

    # update_behavior_summary() 方法已移除
    # 行为摘要数据统一在今日回放窗口中查看,不再在统计报告中显示

    def _format_duration(self, seconds: int) -> str:
        if seconds < 60:
            return f"{seconds}秒"
        if seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}分{secs}秒"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}小时{minutes}分"

    def load_weekly_statistics(self):
        """加载本周统计"""
        summary = self.stats_manager.get_weekly_summary()

        # 更新卡片数据
        self.weekly_total_label.setText(str(summary['total_tasks']))
        self.weekly_completed_label.setText(str(summary['completed_tasks']))
        self.weekly_avg_label.setText(f"{summary['completion_rate']:.1f}%")
        self.weekly_hours_label.setText(f"{summary['total_completed_minutes'] / 60:.1f}h")

        # 加载每日趋势
        daily_breakdown = summary.get('daily_breakdown', [])
        self.weekly_table.setRowCount(len(daily_breakdown))

        for row, day_data in enumerate(daily_breakdown):
            day_summary = day_data['summary']

            self.weekly_table.setItem(row, 0, QTableWidgetItem(day_data['date']))
            self.weekly_table.setItem(row, 1, QTableWidgetItem(day_data['weekday']))
            self.weekly_table.setItem(row, 2, QTableWidgetItem(str(day_summary['total_tasks'])))
            self.weekly_table.setItem(row, 3, QTableWidgetItem(str(day_summary['completed_tasks'])))
            self.weekly_table.setItem(row, 4, QTableWidgetItem(
                f"{day_summary['total_planned_minutes'] / 60:.1f}"
            ))
            self.weekly_table.setItem(row, 5, QTableWidgetItem(
                f"{day_summary['completion_rate']:.1f}"
            ))

    def load_monthly_statistics(self):
        """加载本月统计"""
        summary = self.stats_manager.get_monthly_summary()

        # 更新卡片数据
        self.monthly_total_label.setText(str(summary['total_tasks']))
        self.monthly_completed_label.setText(str(summary['completed_tasks']))
        self.monthly_avg_label.setText(f"{summary['completion_rate']:.1f}%")
        self.monthly_hours_label.setText(f"{summary['total_completed_minutes'] / 60:.1f}h")

        # 加载每日统计
        daily_breakdown = summary.get('daily_breakdown', [])
        self.monthly_table.setRowCount(len(daily_breakdown))

        for row, day_data in enumerate(daily_breakdown):
            day_summary = day_data['summary']

            self.monthly_table.setItem(row, 0, QTableWidgetItem(day_data['date']))
            self.monthly_table.setItem(row, 1, QTableWidgetItem(str(day_summary['total_tasks'])))
            self.monthly_table.setItem(row, 2, QTableWidgetItem(str(day_summary['completed_tasks'])))
            self.monthly_table.setItem(row, 3, QTableWidgetItem(
                f"{day_summary['total_planned_minutes'] / 60:.1f}"
            ))
            self.monthly_table.setItem(row, 4, QTableWidgetItem(
                f"{day_summary['completion_rate']:.1f}"
            ))

    def load_task_statistics(self):
        """加载任务分类统计"""
        task_stats = self.stats_manager.get_task_statistics()

        self.tasks_table.setRowCount(len(task_stats))
        row = 0

        for task_name, stats in sorted(
            task_stats.items(),
            key=lambda x: x[1]['total_minutes'],
            reverse=True
        ):
            # 任务名称(带颜色标记)
            name_item = QTableWidgetItem(f"● {task_name}")
            name_item.setForeground(QColor(stats['color']))
            self.tasks_table.setItem(row, 0, name_item)

            # 统计数据
            self.tasks_table.setItem(row, 1, QTableWidgetItem(str(stats['total_completions'])))
            self.tasks_table.setItem(row, 2, QTableWidgetItem(f"{stats['total_hours']:.2f}"))

            # 颜色块
            color_item = QTableWidgetItem("")
            color_item.setBackground(QColor(stats['color']))
            self.tasks_table.setItem(row, 3, color_item)

            row += 1

    def clear_layout(self, layout):
        """清空布局中的所有部件"""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def export_statistics(self):
        """导出统计数据到CSV"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                tr("statistics.message.export_dialog_title"),
                "statistics_export.csv",
                tr("statistics.message.csv_file_filter")
            )

            if file_path:
                success = self.stats_manager.export_to_csv(Path(file_path))
                if success:
                    QMessageBox.information(
                        self,
                        tr("statistics.message.export_success_title"),
                        tr("statistics.message.export_success_message", file_path=file_path)
                    )
                else:
                    QMessageBox.warning(
                        self,
                        tr("statistics.error.export_failed_title"),
                        tr("statistics.error.export_failed_simple")
                    )

        except Exception as e:
            self.logger.error(tr("statistics.error.export_failed_log", e=e), exc_info=True)
            QMessageBox.critical(
                self,
                tr("statistics.error.error_title"),
                tr("statistics.error.export_failed_message", error=str(e))
            )

    def apply_theme(self):
        """应用当前主题到统计窗口 - 与配置界面风格统一"""
        theme = self.theme_manager.get_current_theme()
        if not theme:
            return

        # 使用浅色系主题,与配置界面保持一致
        bg_color = theme.get('background_color', LightTheme.BG_SECONDARY)
        text_color = theme.get('text_color', LightTheme.TEXT_PRIMARY)
        accent_color = theme.get('accent_color', LightTheme.ACCENT_BLUE)

        # 移除全局样式覆盖,与其他界面保持一致
        # QGroupBox将使用默认的白色背景,仅在需要时使用内联样式

        # 更新标题颜色
        if hasattr(self, 'title_label'):
            self.title_label.setStyleSheet(f"font-size: {LightTheme.FONT_TITLE}px; font-weight: bold; color: {LightTheme.TEXT_PRIMARY};")

        # 优化标签页样式 - 与配置界面一致
        if hasattr(self, 'tab_widget'):
            self.tab_widget.setStyleSheet(f"""
                QTabWidget::pane {{
                    border: 1px solid {LightTheme.BORDER_LIGHT};
                    background: {LightTheme.BG_PRIMARY};
                    border-radius: {LightTheme.RADIUS_SMALL}px;
                }}
                QTabBar::tab {{
                    padding: 10px 20px;
                    margin-right: 2px;
                    background: {LightTheme.BG_SECONDARY};
                    color: {LightTheme.TEXT_SECONDARY};
                    border: 1px solid {LightTheme.BORDER_LIGHT};
                    border-bottom: none;
                    border-top-left-radius: {LightTheme.RADIUS_SMALL}px;
                    border-top-right-radius: {LightTheme.RADIUS_SMALL}px;
                    font-size: 11pt;
                    font-weight: 500;
                }}
                QTabBar::tab:hover {{
                    background: {LightTheme.BG_HOVER};
                    color: {LightTheme.TEXT_PRIMARY};
                }}
                QTabBar::tab:selected {{
                    background: {LightTheme.BG_PRIMARY};
                    color: {accent_color};
                    border-bottom: 2px solid {accent_color};
                    font-weight: bold;
                }}
            """)

        # 更新滚动区域背景 - 白色内容区
        for scroll in self.findChildren(QScrollArea):
            scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {LightTheme.BG_PRIMARY}; }}")

        # 优化表格样式 - MacOS极简风格
        # 注意: 统计界面始终使用浅色背景,所以文字颜色固定使用 LightTheme.TEXT_PRIMARY
        for table in self.findChildren(QTableWidget):
            table.setStyleSheet(f"""
                QTableWidget {{
                    border: 1px solid {LightTheme.BORDER_LIGHT};
                    border-radius: {LightTheme.RADIUS_SMALL}px;
                    gridline-color: {LightTheme.BORDER_LIGHT};
                    background-color: {LightTheme.BG_PRIMARY};
                    color: {LightTheme.TEXT_PRIMARY};
                    selection-background-color: {LightTheme.with_opacity(LightTheme.ACCENT_BLUE, 0.1)};
                    selection-color: {LightTheme.TEXT_PRIMARY};
                }}
                QTableWidget::item {{
                    padding: 8px;
                    border-bottom: 1px solid {LightTheme.BORDER_LIGHT};
                    color: {LightTheme.TEXT_PRIMARY};
                }}
                QTableWidget::item:hover {{
                    background-color: {LightTheme.BG_HOVER};
                }}
                QHeaderView::section {{
                    background-color: {LightTheme.BG_TERTIARY};
                    color: {LightTheme.TEXT_PRIMARY};
                    padding: 10px;
                    border: none;
                    font-weight: bold;
                    font-size: {LightTheme.FONT_SMALL}pt;
                    font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
                }}
                QHeaderView:horizontal::section {{
                    border-bottom: 2px solid {LightTheme.BORDER_LIGHT};
                }}
                QHeaderView:vertical::section {{
                    border-right: 1px solid {LightTheme.BORDER_LIGHT};
                    text-align: center;
                }}
            """)

        # 移除 QMessageBox 的全局样式设置
        # QMessageBox 将使用系统默认样式,与其他界面保持一致

        # 更新统计卡片样式 - 添加悬停效果
        for card in self.findChildren(StatCard):
            card.setStyleSheet(f"""
                StatCard {{
                    background-color: {LightTheme.BG_PRIMARY};
                    border: 1px solid {LightTheme.BORDER_LIGHT};
                    border-radius: {LightTheme.RADIUS_LARGE}px;
                }}
                StatCard:hover {{
                    border-color: {accent_color};
                }}
            """)

        self.logger.info(f"已应用统一主题到统计窗口: {theme.get('name', 'Unknown')}")

    def open_task_review_window(self):
        """打开任务完成回顾窗口（显示所有任务，包括已确认的）"""
        from gaiya.ui.task_review_window import TaskReviewWindow
        from datetime import date

        today = date.today().isoformat()

        try:
            # 获取今日所有任务（包括已确认和未确认的）
            all_tasks = db.get_today_task_completions(today)

            if not all_tasks:
                QMessageBox.information(
                    self,
                    "提示",
                    "今天还没有任务完成记录。\n\n"
                    "可能原因:\n"
                    "1. 今天尚未生成任务完成推理\n"
                    "2. 任务完成推理系统未启用\n\n"
                    "💡 请点击上方「🔄 手动生成推理」按钮生成今日任务完成情况。"
                )
                return

            # 统计已确认和未确认的任务数
            confirmed_count = sum(1 for t in all_tasks if t.get('user_confirmed', False))
            unconfirmed_count = len(all_tasks) - confirmed_count

            self.logger.info(f"打开任务回顾窗口: 总任务={len(all_tasks)}, 已确认={confirmed_count}, 未确认={unconfirmed_count}")

            # 打开任务回顾窗口
            # 注意: parent=None 避免与主窗口的渲染冲突,防止 QPainter 错误
            self.review_window = TaskReviewWindow(
                date=today,
                task_completions=all_tasks,  # 显示所有任务
                on_confirm=None,  # 使用信号连接,不使用回调
                parent=None  # 独立窗口,避免渲染冲突
            )
            self.review_window.review_completed.connect(self.on_review_completed)

            # 窗口关闭后清理引用
            self.review_window.finished.connect(lambda: setattr(self, 'review_window', None))

            # 延迟显示,确保当前事件循环完成
            # 使用 show() 而不是 exec(),非模态显示避免事件循环阻塞
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, lambda: self.review_window.show() if hasattr(self, 'review_window') and self.review_window else None)

        except Exception as e:
            self.logger.error(f"打开任务回顾窗口失败: {e}", exc_info=True)
            QMessageBox.warning(
                self,
                "错误",
                f"打开任务回顾窗口失败:\n{str(e)}"
            )

    def on_review_completed(self, results: list):
        """任务回顾完成回调

        Args:
            results: [{'completion_id': str, 'new_completion': int, 'note': str, ...}, ...]
        """
        try:
            # 更新数据库
            for result in results:
                completion_id = result['completion_id']
                new_completion = result['new_completion']
                note = result.get('note', '')
                db.confirm_task_completion(completion_id, new_completion, note)

            self.logger.info(f"用户确认 {len(results)} 个任务完成记录")

            # 刷新统计显示
            self.load_today_statistics()

            QMessageBox.information(
                self,
                "完成",
                f"已成功确认 {len(results)} 个任务!"
            )

        except Exception as e:
            self.logger.error(f"保存任务确认失败: {e}", exc_info=True)
            QMessageBox.warning(
                self,
                "错误",
                f"保存任务确认失败:\n{str(e)}"
            )

    def trigger_manual_inference(self):
        """手动触发今日任务完成推理"""
        from datetime import date
        import threading
        import time

        today = date.today().isoformat()

        try:
            # 禁用按钮,防止重复点击
            self.trigger_inference_button.setEnabled(False)
            self.trigger_inference_button.setText("🔄 准备中...")

            # 检查是否今天已有推理数据
            existing_completions = db.get_today_task_completions(today)

            if existing_completions:
                reply = QMessageBox.question(
                    self,
                    "确认",
                    f"今天已有 {len(existing_completions)} 条推理记录。\n\n"
                    "重新生成推理会覆盖现有数据(已确认的记录除外)。\n"
                    "是否继续?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )

                if reply != QMessageBox.Yes:
                    self.trigger_inference_button.setEnabled(True)
                    self.trigger_inference_button.setText("🔄 手动生成推理")
                    return

                # 删除未确认的推理记录
                conn = db._get_connection()
                try:
                    for completion in existing_completions:
                        if not completion.get('user_confirmed', False):
                            conn.execute(
                                "DELETE FROM task_completions WHERE id = ?",
                                (completion['id'],)
                            )
                    conn.commit()
                    self.logger.info(f"已删除今日未确认的推理记录")
                finally:
                    conn.close()

            # 显示进度提示
            self.trigger_inference_button.setText("🔄 正在执行推理...")

            # 在后台线程执行推理
            def run_inference():
                try:
                    start_time = time.time()
                    self.logger.info(f"[手动推理] 开始执行: {today}")

                    # 获取调度器实例 (从 main window)
                    main_window = self.parent()
                    self.logger.info(f"[手动推理] parent类型: {type(main_window).__name__}")

                    # 详细诊断
                    if not hasattr(main_window, 'task_completion_scheduler'):
                        self.logger.error("[手动推理] 未找到任务完成推理调度器")
                        self.logger.error(f"[手动推理] parent属性列表: {dir(main_window)[:10]}...")

                        # 生成详细错误信息
                        error_msg = (
                            "AI推理功能暂时不可用\n\n"
                            "可能原因:\n"
                            "1. 任务追踪系统初始化失败\n"
                            "2. 应用刚启动,系统组件正在加载中\n"
                            "3. 配置文件缺少必要参数\n\n"
                            "建议操作:\n"
                            "• 重启应用再试\n"
                            "• 检查系统日志(gaiya.log)\n"
                            "• 如问题持续,请联系技术支持"
                        )

                        # 发射信号通知推理失败
                        self.inference_completed.emit(False, error_msg)
                        return

                    scheduler = main_window.task_completion_scheduler

                    # 检查调度器是否正常初始化
                    if not scheduler or not hasattr(scheduler, '_run_daily_inference'):
                        self.logger.error("[手动推理] 调度器未正确初始化")
                        error_msg = (
                            "AI推理功能未正确初始化\n\n"
                            "请检查:\n"
                            "1. 应用是否完全启动\n"
                            "2. 系统日志中是否有错误信息\n"
                            "3. 数据库文件是否正常"
                        )
                        self.inference_completed.emit(False, error_msg)
                        return

                    # 直接调用内部方法执行推理
                    self.logger.info(f"[手动推理] 调用调度器执行推理")
                    scheduler._run_daily_inference(today)

                    elapsed_time = time.time() - start_time
                    self.logger.info(f"[手动推理] 推理完成,耗时: {elapsed_time:.1f}秒")

                    # 发射信号通知推理成功
                    self.inference_completed.emit(True, "")

                except Exception as e:
                    self.logger.error(f"[手动推理] 执行失败: {e}", exc_info=True)
                    # 发射信号通知推理失败
                    self.inference_completed.emit(False, str(e))

            # 启动后台线程
            self.logger.info(f"[手动推理] 启动推理线程")
            threading.Thread(target=run_inference, daemon=True).start()

        except Exception as e:
            self.logger.error(f"触发手动推理失败: {e}", exc_info=True)
            QMessageBox.warning(
                self,
                "错误",
                f"触发手动推理失败:\n{str(e)}"
            )
            self.trigger_inference_button.setEnabled(True)
            self.trigger_inference_button.setText("🔄 手动生成推理")

    def trigger_ai_analysis(self):
        """触发AI深度分析"""
        from datetime import date
        import threading

        today = date.today().isoformat()

        try:
            # 获取今日任务完成数据
            task_completions = db.get_today_task_completions(today)

            if not task_completions:
                QMessageBox.information(
                    self,
                    "提示",
                    "今天还没有任务完成记录。\n\n"
                    "请先点击「🔄 手动生成推理」按钮生成今日任务完成情况。"
                )
                return

            # 禁用按钮
            self.ai_analysis_button.setEnabled(False)
            self.ai_analysis_button.setText("🤖 分析中...")

            # 在后台线程调用AI
            def run_analysis():
                try:
                    from ai_client import GaiyaAIClient

                    self.logger.info(f"[AI分析] 开始分析: {today}, {len(task_completions)}个任务")

                    # 获取或创建AI客户端
                    ai_client = None

                    # 尝试从主窗口获取
                    main_window = self.parent()
                    if hasattr(main_window, 'ai_client') and main_window.ai_client:
                        ai_client = main_window.ai_client
                        self.logger.info("[AI分析] 使用主窗口的AI客户端")
                    else:
                        # 创建新的AI客户端实例
                        self.logger.info("[AI分析] 创建新的AI客户端")
                        ai_client = GaiyaAIClient()

                    if not ai_client:
                        QMessageBox.warning(
                            self,
                            "错误",
                            "AI客户端初始化失败"
                        )
                        self.ai_analysis_button.setEnabled(True)
                        self.ai_analysis_button.setText("🤖 AI深度分析")
                        return

                    # 调用AI分析
                    analysis_text = ai_client.analyze_task_completion(
                        date=today,
                        task_completions=task_completions,
                        parent_widget=self
                    )

                    if analysis_text:
                        self.logger.info(f"[AI分析] 分析成功")
                        # 在主线程显示分析结果
                        from PySide6.QtCore import QMetaObject, Q_ARG
                        QMetaObject.invokeMethod(
                            self,
                            "_show_ai_analysis_result",
                            Qt.QueuedConnection,
                            Q_ARG(str, today),
                            Q_ARG(str, analysis_text)
                        )
                    else:
                        self.logger.warning(f"[AI分析] 分析失败或被取消")

                    # 恢复按钮状态
                    self.ai_analysis_button.setEnabled(True)
                    self.ai_analysis_button.setText("🤖 AI深度分析")

                except Exception as e:
                    self.logger.error(f"[AI分析] 执行失败: {e}", exc_info=True)
                    QMessageBox.warning(
                        self,
                        "错误",
                        f"AI分析失败:\n{str(e)}"
                    )
                    self.ai_analysis_button.setEnabled(True)
                    self.ai_analysis_button.setText("🤖 AI深度分析")

            # 启动后台线程
            threading.Thread(target=run_analysis, daemon=True).start()

        except Exception as e:
            self.logger.error(f"触发AI分析失败: {e}", exc_info=True)
            QMessageBox.warning(
                self,
                "错误",
                f"触发AI分析失败:\n{str(e)}"
            )
            self.ai_analysis_button.setEnabled(True)
            self.ai_analysis_button.setText("🤖 AI深度分析")

    @Slot(str, str)
    def _show_ai_analysis_result(self, date: str, analysis_text: str):
        """显示AI分析结果（在主线程中调用）"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel

        dialog = QDialog(self)
        dialog.setWindowTitle(f"AI深度分析 - {date}")
        dialog.setMinimumSize(700, 500)

        # 添加浅色模式样式
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {LightTheme.BG_PRIMARY};
            }}
            QLabel {{
                color: {LightTheme.TEXT_PRIMARY};
            }}
        """)

        layout = QVBoxLayout(dialog)

        # 标题
        title_label = QLabel(f"📊 {date} 任务完成度深度分析")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title_label)

        # 分析内容
        text_edit = QTextEdit()
        text_edit.setPlainText(analysis_text)
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {LightTheme.BG_SECONDARY};
                border: 1px solid {LightTheme.BORDER_LIGHT};
                border-radius: {LightTheme.RADIUS_SMALL}px;
                padding: 15px;
                font-size: {LightTheme.FONT_SUBTITLE}px;
                line-height: 1.6;
            }}
        """)
        layout.addWidget(text_edit)

        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.setFixedHeight(36)
        close_button.setStyleSheet(StyleManager.button_primary())
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)

        dialog.exec()

    def _on_inference_completed(self, success: bool, error_msg: str):
        """推理完成回调 (在主线程执行)"""
        # 恢复按钮状态
        self.trigger_inference_button.setEnabled(True)
        self.trigger_inference_button.setText("🔄 手动生成推理")

        if success:
            # 刷新统计显示
            self.load_today_statistics()

            # 检查是否有待确认的任务
            from datetime import date
            today = date.today().isoformat()
            unconfirmed_tasks = db.get_unconfirmed_task_completions(today)

            if unconfirmed_tasks:
                # 显示完成提示,说明批量确认窗口即将弹出
                QMessageBox.information(
                    self,
                    "✅ 推理完成",
                    f"任务完成推理已生成!\n\n"
                    f"📊 共推理 {len(unconfirmed_tasks)} 个任务\n"
                    f"💡 批量确认窗口即将自动打开,请确认或修正任务完成度。\n\n"
                    f"提示: 如果窗口未弹出,请点击下方\"确认/修正任务完成度\"按钮。"
                )
            else:
                QMessageBox.information(
                    self,
                    "✅ 推理完成",
                    "任务完成推理已生成!\n\n"
                    "所有任务都已自动确认(高置信度任务)。"
                )
        else:
            QMessageBox.warning(
                self,
                "❌ 推理失败",
                f"任务完成推理生成失败:\n\n{error_msg}\n\n"
                f"请检查日志文件获取详细错误信息。"
            )

    def create_completion_trend_chart(self) -> QChartView:
        """创建任务完成率趋势折线图(最近7天)

        Returns:
            QChartView: 图表视图组件
        """
        # 获取最近7天的趋势数据
        trend_data = self.stats_manager.get_weekly_trend(days=7)

        # 创建折线系列
        series = QLineSeries()
        series.setName("任务完成率")

        # 添加数据点
        for day_stat in trend_data:
            # 将日期字符串转换为 QDateTime
            date_time = QDateTime.fromString(day_stat['date'], "yyyy-MM-dd")
            timestamp = date_time.toMSecsSinceEpoch()
            completion_rate = day_stat['completion_rate']

            series.append(timestamp, completion_rate)

        # 创建图表
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("📈 任务完成率趋势 (最近7天)")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

        # 设置图表样式
        chart.setBackgroundBrush(QColor(LightTheme.BG_PRIMARY))
        chart.setTitleFont(QFont("Microsoft YaHei", LightTheme.FONT_SUBTITLE, QFont.Weight.Bold))

        # X轴: 日期
        axis_x = QDateTimeAxis()
        axis_x.setFormat("MM-dd")
        axis_x.setTitleText("日期")
        axis_x.setLabelsFont(QFont("Microsoft YaHei", LightTheme.FONT_SMALL))
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        # Y轴: 百分比
        axis_y = QValueAxis()
        axis_y.setRange(0, 100)
        axis_y.setTitleText("完成率 (%)")
        axis_y.setLabelsFont(QFont("Microsoft YaHei", LightTheme.FONT_SMALL))
        axis_y.setTickCount(6)  # 0, 20, 40, 60, 80, 100
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        # 设置系列颜色
        pen = QPen(QColor(LightTheme.ACCENT_GREEN))
        pen.setWidth(3)
        series.setPen(pen)

        # 创建视图
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view.setMinimumHeight(300)
        chart_view.setStyleSheet(f"""
            QChartView {{
                background-color: {LightTheme.BG_PRIMARY};
                border: 1px solid {LightTheme.BORDER_LIGHT};
                border-radius: {LightTheme.RADIUS_MEDIUM}px;
            }}
        """)

        return chart_view

    def create_category_pie_chart(self) -> QChartView:
        """创建任务颜色分布饼图(本周)

        Returns:
            QChartView: 饼图视图组件
        """
        # 获取本周任务颜色分布数据
        color_distribution = self.stats_manager.get_task_color_distribution(date_range="week")

        # 如果没有数据,显示空图表
        if not color_distribution or len(color_distribution) == 0:
            series = QPieSeries()
            series.append("暂无数据", 1)
            slice = series.slices()[0]
            slice.setBrush(QColor(LightTheme.TEXT_TERTIARY))
            slice.setLabelVisible(True)
            slice.setLabelFont(QFont("Microsoft YaHei", LightTheme.FONT_SMALL))
        else:
            # 创建饼图系列
            series = QPieSeries()

            # 定义颜色标签对应的emoji
            label_emoji = {
                '工作': '💼',
                '学习': '📚',
                '生活': '🏠',
                '娱乐': '🎮',
                '运动': '🏃',
                '重要': '⭐',
                '社交': '👥',
                '休闲': '☕',
                '其他': '📌'
            }

            # 添加数据到饼图
            total_tasks = sum(item['count'] for item in color_distribution)

            for item in color_distribution:
                label = item['label']
                count = item['count']
                percentage = item['percentage']
                color = item['color']

                # 只显示占比超过3%的分类
                if percentage < 3.0:
                    continue

                # 设置标签：emoji + 分类名 + 任务数 + 百分比
                emoji = label_emoji.get(label, '📌')
                slice_label = f"{emoji} {label} ({count}个, {percentage:.1f}%)"

                slice = series.append(slice_label, count)
                slice.setLabelVisible(True)
                slice.setLabelFont(QFont("Microsoft YaHei", LightTheme.FONT_SMALL))

                # 设置扇形颜色(使用任务实际颜色)
                slice.setBrush(QColor(color))

                # 高亮最大的分类（爆炸效果）
                if item == color_distribution[0]:  # 第一个是最大的(已排序)
                    slice.setExploded(True)
                    slice.setExplodeDistanceFactor(0.1)

        # 创建图表
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("📊 任务分类分布 (最近7天)")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

        # 设置图表样式
        chart.setBackgroundBrush(QColor(LightTheme.BG_PRIMARY))
        chart.setTitleFont(QFont("Microsoft YaHei", LightTheme.FONT_SUBTITLE, QFont.Weight.Bold))

        # 隐藏图例（因为饼图上已有标签）
        chart.legend().setVisible(False)

        # 创建视图
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view.setMinimumHeight(300)
        chart_view.setStyleSheet(f"""
            QChartView {{
                background-color: {LightTheme.BG_PRIMARY};
                border: 1px solid {LightTheme.BORDER_LIGHT};
                border-radius: {LightTheme.RADIUS_MEDIUM}px;
            }}
        """)

        return chart_view

    def center_window(self):
        """将窗口居中显示在屏幕上"""
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().geometry()
        window_rect = self.frameGeometry()
        center_point = screen.center()
        window_rect.moveCenter(center_point)
        self.move(window_rect.topLeft())

    def create_insights_widget(self) -> QWidget:
        """创建智能洞察组件 (Sprint 3 - Task 3.2)"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        try:
            # 生成洞察报告
            insights = self.insights_generator.generate_weekly_insights(days=7)

            # 1. 总体摘要卡片
            summary_card = self._create_insights_summary_card(insights)
            layout.addWidget(summary_card)

            # 2. 生产力趋势 + Top 3应用 (横向布局)
            stats_row = QHBoxLayout()
            stats_row.setSpacing(12)

            # 生产力趋势卡片
            trend_card = self._create_insights_trend_card(insights['productivity_trend'])
            stats_row.addWidget(trend_card, 1)

            # Top 3应用卡片
            top_apps_card = self._create_insights_top_apps_card(insights['top_apps'])
            stats_row.addWidget(top_apps_card, 1)

            layout.addLayout(stats_row)

            # 3. 改进建议列表
            if insights['suggestions']:
                suggestions_card = self._create_insights_suggestions_card(insights['suggestions'])
                layout.addWidget(suggestions_card)

        except Exception as e:
            self.logger.error(f"生成洞察报告失败: {e}")
            # 显示错误提示
            error_label = QLabel("⚠️ 暂无足够数据生成洞察报告")
            error_label.setStyleSheet(f"""
                color: {LightTheme.TEXT_SECONDARY};
                font-size: {LightTheme.FONT_BODY}px;
                padding: 20px;
            """)
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(error_label)

        return container

    def _create_insights_summary_card(self, insights: dict) -> QWidget:
        """创建洞察摘要卡片"""
        card = QWidget()
        card.setStyleSheet(f"""
            QWidget {{
                background-color: {LightTheme.with_opacity(LightTheme.ACCENT_BLUE, 0.05)};
                border: none;
                border-radius: {LightTheme.RADIUS_MEDIUM}px;
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(8)

        # 摘要文字
        summary_text = insights['summary']
        summary_label = QLabel(summary_text)
        summary_label.setWordWrap(True)
        summary_label.setStyleSheet(f"""
            color: {LightTheme.TEXT_PRIMARY};
            font-size: {LightTheme.FONT_BODY}px;
            line-height: 1.6;
        """)
        layout.addWidget(summary_label)

        return card

    def _create_insights_trend_card(self, trend_data: dict) -> QWidget:
        """创建生产力趋势卡片"""
        card = QWidget()
        card.setStyleSheet(f"""
            QWidget {{
                background-color: {LightTheme.BG_TERTIARY};
                border: none;
                border-radius: {LightTheme.RADIUS_MEDIUM}px;
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(8)

        # 标题
        title_layout = QHBoxLayout()
        emoji_label = QLabel(trend_data['emoji'])
        emoji_label.setStyleSheet("font-size: 28px;")
        title_layout.addWidget(emoji_label)

        title_label = QLabel("生产力趋势")
        title_label.setStyleSheet(f"""
            color: {LightTheme.TEXT_PRIMARY};
            font-size: {LightTheme.FONT_SUBTITLE}px;
            font-weight: bold;
        """)
        title_layout.addWidget(title_label, 1)
        layout.addLayout(title_layout)

        # 趋势描述
        desc_label = QLabel(trend_data['description'])
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"""
            color: {LightTheme.TEXT_SECONDARY};
            font-size: {LightTheme.FONT_BODY}px;
        """)
        layout.addWidget(desc_label)

        # 变化值
        if 'change' in trend_data:
            change_val = trend_data['change']
            change_text = f"+{change_val:.1f}%" if change_val > 0 else f"{change_val:.1f}%"
            change_color = LightTheme.ACCENT_GREEN if change_val > 0 else LightTheme.ACCENT_RED

            change_label = QLabel(change_text)
            change_label.setStyleSheet(f"""
                color: {change_color};
                font-size: {LightTheme.FONT_TITLE}px;
                font-weight: bold;
            """)
            layout.addWidget(change_label)

        return card

    def _create_insights_top_apps_card(self, top_apps: list) -> QWidget:
        """创建Top 3应用卡片"""
        card = QWidget()
        card.setStyleSheet(f"""
            QWidget {{
                background-color: {LightTheme.BG_TERTIARY};
                border: none;
                border-radius: {LightTheme.RADIUS_MEDIUM}px;
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(8)

        # 标题
        title_label = QLabel("⏱️ 时间投入TOP 3")
        title_label.setStyleSheet(f"""
            color: {LightTheme.TEXT_PRIMARY};
            font-size: {LightTheme.FONT_SUBTITLE}px;
            font-weight: bold;
        """)
        layout.addWidget(title_label)

        # 应用列表
        if top_apps:
            for app in top_apps[:3]:
                app_row = QHBoxLayout()

                # 排名 + Emoji
                rank_label = QLabel(f"{app['rank']}. {app['emoji']}")
                rank_label.setStyleSheet(f"font-size: {LightTheme.FONT_BODY}px;")
                app_row.addWidget(rank_label)

                # 分类名称
                name_label = QLabel(app['category'])
                name_label.setStyleSheet(f"""
                    color: {LightTheme.TEXT_PRIMARY};
                    font-size: {LightTheme.FONT_BODY}px;
                """)
                app_row.addWidget(name_label, 1)

                # 时长
                hours_label = QLabel(f"{app['hours']}h")
                hours_label.setStyleSheet(f"""
                    color: {LightTheme.ACCENT_BLUE};
                    font-size: {LightTheme.FONT_BODY}px;
                    font-weight: bold;
                """)
                app_row.addWidget(hours_label)

                layout.addLayout(app_row)
        else:
            empty_label = QLabel("暂无数据")
            empty_label.setStyleSheet(f"color: {LightTheme.TEXT_HINT};")
            layout.addWidget(empty_label)

        return card

    def _create_insights_suggestions_card(self, suggestions: list) -> QWidget:
        """创建改进建议卡片"""
        card = QWidget()
        card.setStyleSheet(f"""
            QWidget {{
                border-left: 3px solid {LightTheme.ACCENT_GREEN};
                padding: 12px 16px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标题
        title_label = QLabel("💡 改进建议")
        title_label.setStyleSheet(f"""
            color: {LightTheme.TEXT_PRIMARY};
            font-size: {LightTheme.FONT_SUBTITLE}px;
            font-weight: bold;
        """)
        layout.addWidget(title_label)

        # 建议列表
        for suggestion in suggestions:
            suggestion_label = QLabel(f"• {suggestion}")
            suggestion_label.setWordWrap(True)
            suggestion_label.setStyleSheet(f"""
                color: {LightTheme.TEXT_SECONDARY};
                font-size: {LightTheme.FONT_BODY}px;
                line-height: 1.6;
            """)
            layout.addWidget(suggestion_label)

        return card

    def create_goals_tab(self):
        """创建目标管理页签 (Sprint 4 - Task 4.1)"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)

        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)

        # 标题和创建按钮
        header_layout = QHBoxLayout()
        title_label = QLabel("🎯 我的目标")
        title_label.setStyleSheet(f"font-size: {LightTheme.FONT_TITLE}px; font-weight: bold; color: {LightTheme.TEXT_PRIMARY};")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        create_goal_btn = QPushButton("➕ 创建新目标")
        create_goal_btn.setFixedHeight(36)
        create_goal_btn.setStyleSheet(StyleManager.button_primary())
        create_goal_btn.clicked.connect(self._create_new_goal)
        header_layout.addWidget(create_goal_btn)

        content_layout.addLayout(header_layout)

        # 目标统计卡片
        stats = self.goal_manager.get_statistics()
        stats_card = QGroupBox("📊 目标统计")
        stats_card.setStyleSheet(f"QGroupBox::title {{ color: {LightTheme.TEXT_PRIMARY}; font-weight: bold; font-size: {LightTheme.FONT_SUBTITLE}px; }}")
        stats_layout = QHBoxLayout(stats_card)

        self._add_stat_item(stats_layout, "活跃目标", str(stats['active_goals']), LightTheme.ACCENT_BLUE)
        self._add_stat_item(stats_layout, "已完成", str(stats['completed_goals']), LightTheme.ACCENT_GREEN)
        self._add_stat_item(stats_layout, "完成率", f"{stats['completion_rate']:.0f}%", LightTheme.ACCENT_ORANGE)

        content_layout.addWidget(stats_card)

        # 活跃目标列表
        active_goals = self.goal_manager.get_active_goals()
        if active_goals:
            goals_group = QGroupBox(f"📋 活跃目标 ({len(active_goals)}个)")
            goals_group.setStyleSheet(f"QGroupBox::title {{ color: {LightTheme.TEXT_PRIMARY}; font-weight: bold; font-size: {LightTheme.FONT_SUBTITLE}px; }}")
            goals_layout = QVBoxLayout(goals_group)
            goals_layout.setSpacing(10)

            for goal in active_goals:
                goal_card = self._create_goal_card(goal)
                goals_layout.addWidget(goal_card)

            content_layout.addWidget(goals_group)
        else:
            # 空状态提示
            empty_label = QLabel("暂无活跃目标\n点击上方「创建新目标」按钮开始设定你的第一个目标!")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet(f"""
                color: {LightTheme.TEXT_HINT};
                font-size: {LightTheme.FONT_BODY}px;
                padding: 40px;
            """)
            content_layout.addWidget(empty_label)

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        self.tab_widget.addTab(tab, "🎯 目标")

    def _add_stat_item(self, layout: QHBoxLayout, label: str, value: str, color: str):
        """添加统计项"""
        item_widget = QWidget()
        item_layout = QVBoxLayout(item_widget)
        item_layout.setSpacing(5)

        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
        value_label.setAlignment(Qt.AlignCenter)
        item_layout.addWidget(value_label)

        label_label = QLabel(label)
        label_label.setStyleSheet(f"color: {LightTheme.TEXT_SECONDARY}; font-size: {LightTheme.FONT_SMALL}px;")
        label_label.setAlignment(Qt.AlignCenter)
        item_layout.addWidget(label_label)

        layout.addWidget(item_widget)

    def _create_goal_card(self, goal: Goal) -> QWidget:
        """创建目标卡片"""
        card = QWidget()
        card.setStyleSheet(f"""
            QWidget {{
                background-color: {LightTheme.BG_PRIMARY};
                border: 1px solid {LightTheme.BORDER_LIGHT};
                border-radius: {LightTheme.RADIUS_MEDIUM}px;
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(10)

        # 目标信息
        info = goal.get_info()

        # 标题行
        title_layout = QHBoxLayout()
        title_label = QLabel(f"{info['emoji']} {info['name']}")
        title_label.setStyleSheet(f"font-size: {LightTheme.FONT_SUBTITLE}px; font-weight: bold; color: {LightTheme.TEXT_PRIMARY};")
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        # 删除按钮
        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(32, 32)
        delete_btn.setStyleSheet(StyleManager.button_minimal())
        delete_btn.clicked.connect(lambda: self._delete_goal(goal.goal_id))
        title_layout.addWidget(delete_btn)

        layout.addLayout(title_layout)

        # 进度信息
        progress_text = QLabel(f"目标: {info['target_value']}{info['unit']}  |  当前: {info['current_value']:.1f}{info['unit']}")
        progress_text.setStyleSheet(f"color: {LightTheme.TEXT_SECONDARY}; font-size: {LightTheme.FONT_BODY}px;")
        layout.addWidget(progress_text)

        # 进度条
        progress_bar = QProgressBar()
        progress_bar.setValue(int(info['progress_percentage']))
        progress_bar.setTextVisible(True)
        progress_bar.setFormat(f"{info['progress_percentage']:.1f}%")
        progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {LightTheme.BORDER_LIGHT};
                border-radius: {LightTheme.RADIUS_SMALL}px;
                text-align: center;
                height: 24px;
                background-color: {LightTheme.BG_SECONDARY};
            }}
            QProgressBar::chunk {{
                background-color: {LightTheme.ACCENT_GREEN};
                border-radius: {LightTheme.RADIUS_SMALL}px;
            }}
        """)
        layout.addWidget(progress_bar)

        return card

    def _create_new_goal(self):
        """创建新目标对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("创建新目标")
        dialog.setFixedWidth(400)

        layout = QFormLayout(dialog)

        # 目标类型
        type_combo = QComboBox()
        type_combo.addItem("📋 每日任务目标", "daily_tasks")
        type_combo.addItem("⏱️ 每周专注时长", "weekly_focus_hours")
        type_combo.addItem("🎯 每周完成率", "weekly_completion_rate")
        layout.addRow("目标类型:", type_combo)

        # 目标值
        value_spin = QSpinBox()
        value_spin.setMinimum(1)
        value_spin.setMaximum(1000)
        value_spin.setValue(5)

        def update_value_range(index):
            goal_type = type_combo.itemData(index)
            if goal_type == "daily_tasks":
                value_spin.setValue(5)
                value_spin.setSuffix(" 个任务")
            elif goal_type == "weekly_focus_hours":
                value_spin.setValue(20)
                value_spin.setSuffix(" 小时")
            else:  # weekly_completion_rate
                value_spin.setMaximum(100)
                value_spin.setValue(80)
                value_spin.setSuffix(" %")

        type_combo.currentIndexChanged.connect(update_value_range)
        update_value_range(0)  # 初始化

        layout.addRow("目标值:", value_spin)

        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)

        if dialog.exec() == QDialog.Accepted:
            goal_type = type_combo.currentData()
            target_value = value_spin.value()

            try:
                self.goal_manager.create_goal(goal_type, target_value)
                QMessageBox.information(self, "成功", "目标创建成功!")
                self._refresh_goals_tab()
            except Exception as e:
                QMessageBox.warning(self, "错误", f"创建目标失败:\n{str(e)}")

    def _delete_goal(self, goal_id: str):
        """删除目标"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除这个目标吗?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.goal_manager.delete_goal(goal_id)
            self._refresh_goals_tab()

    def _refresh_goals_tab(self):
        """刷新目标页签"""
        # 删除旧的tab
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == "🎯 目标":
                self.tab_widget.removeTab(i)
                break

        # 重新创建
        self.create_goals_tab()

    def create_achievements_tab(self):
        """创建成就展示页签 (Sprint 4 - Task 4.2)"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)

        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)

        # 标题
        title_label = QLabel("🏆 成就系统")
        title_label.setStyleSheet(f"font-size: {LightTheme.FONT_TITLE}px; font-weight: bold; color: {LightTheme.TEXT_PRIMARY};")
        content_layout.addWidget(title_label)

        # 成就统计卡片
        stats = self.achievement_manager.get_statistics()
        stats_card = QGroupBox("📊 成就统计")
        stats_card.setStyleSheet(f"QGroupBox::title {{ color: {LightTheme.TEXT_PRIMARY}; font-weight: bold; font-size: {LightTheme.FONT_SUBTITLE}px; }}")
        stats_layout = QGridLayout(stats_card)

        # 总体统计
        total_card = self._create_achievement_stat_card(
            "总成就数",
            str(stats['total_achievements']),
            LightTheme.ACCENT_BLUE
        )
        stats_layout.addWidget(total_card, 0, 0)

        unlocked_card = self._create_achievement_stat_card(
            "已解锁",
            str(stats['unlocked_count']),
            LightTheme.ACCENT_GREEN
        )
        stats_layout.addWidget(unlocked_card, 0, 1)

        percentage_card = self._create_achievement_stat_card(
            "完成度",
            f"{stats['unlock_percentage']:.0f}%",
            LightTheme.ACCENT_ORANGE
        )
        stats_layout.addWidget(percentage_card, 0, 2)

        # 稀有度统计
        rarity_layout = QHBoxLayout()
        rarity_counts = stats['rarity_counts']
        rarity_info = [
            ('普通', rarity_counts.get('common', 0), LightTheme.TEXT_SECONDARY),
            ('稀有', rarity_counts.get('rare', 0), LightTheme.ACCENT_BLUE),
            ('史诗', rarity_counts.get('epic', 0), LightTheme.ACCENT_PURPLE),
            ('传说', rarity_counts.get('legendary', 0), LightTheme.ACCENT_ORANGE)
        ]

        for rarity_name, count, color in rarity_info:
            rarity_label = QLabel(f"{rarity_name}: {count}")
            rarity_label.setStyleSheet(f"color: {color}; font-size: {LightTheme.FONT_SMALL}px; font-weight: bold;")
            rarity_layout.addWidget(rarity_label)

        rarity_widget = QWidget()
        rarity_widget.setLayout(rarity_layout)
        stats_layout.addWidget(rarity_widget, 1, 0, 1, 3)

        content_layout.addWidget(stats_card)

        # 已解锁成就
        unlocked_achievements = self.achievement_manager.get_unlocked_achievements()
        if unlocked_achievements:
            unlocked_group = QGroupBox(f"✅ 已解锁成就 ({len(unlocked_achievements)}个)")
            unlocked_group.setStyleSheet(f"QGroupBox::title {{ color: {LightTheme.TEXT_PRIMARY}; font-weight: bold; font-size: {LightTheme.FONT_SUBTITLE}px; }}")
            unlocked_layout = QVBoxLayout(unlocked_group)
            unlocked_layout.setSpacing(10)

            for achievement in unlocked_achievements:
                achievement_card = self._create_achievement_card(achievement, unlocked=True)
                unlocked_layout.addWidget(achievement_card)

            content_layout.addWidget(unlocked_group)

        # 未解锁成就 (始终显示,即使为空)
        locked_achievements = self.achievement_manager.get_locked_achievements()

        # Debug logging
        all_achievements = self.achievement_manager.get_all_achievements()
        unlocked_count = len(unlocked_achievements)
        locked_count = len(locked_achievements)
        total_count = len(all_achievements)
        self.logger.info(f"成就统计: 总数={total_count}, 已解锁={unlocked_count}, 未解锁={locked_count}")

        locked_group = QGroupBox(f"🔒 未解锁成就 ({len(locked_achievements)}个)")
        locked_group.setStyleSheet(f"QGroupBox::title {{ color: {LightTheme.TEXT_PRIMARY}; font-weight: bold; font-size: {LightTheme.FONT_SUBTITLE}px; }}")
        locked_layout = QVBoxLayout(locked_group)
        locked_layout.setSpacing(10)

        if locked_achievements:
            for achievement in locked_achievements:
                achievement_card = self._create_achievement_card(achievement, unlocked=False)
                locked_layout.addWidget(achievement_card)
        else:
            # 如果所有成就都解锁了,显示祝贺信息
            congrats_label = QLabel("🎉 恭喜!你已解锁所有成就!")
            congrats_label.setStyleSheet(f"color: {LightTheme.TEXT_SECONDARY}; font-size: {LightTheme.FONT_BODY}px; padding: 20px;")
            congrats_label.setAlignment(Qt.AlignCenter)
            locked_layout.addWidget(congrats_label)

        content_layout.addWidget(locked_group)

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        self.tab_widget.addTab(tab, "🏆 成就")

    def _create_achievement_stat_card(self, label: str, value: str, color: str) -> QWidget:
        """创建成就统计卡片"""
        card = QWidget()
        card.setStyleSheet(f"""
            QWidget {{
                border-left: 3px solid {color};
                padding: 12px 16px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(5)

        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {color};")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)

        label_label = QLabel(label)
        label_label.setStyleSheet(f"color: {LightTheme.TEXT_SECONDARY}; font-size: {LightTheme.FONT_SMALL}px;")
        label_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_label)

        return card

    def _create_achievement_card(self, achievement: Achievement, unlocked: bool) -> QWidget:
        """创建成就卡片"""
        card = QWidget()

        # 根据稀有度选择颜色
        rarity_colors = {
            'common': LightTheme.TEXT_SECONDARY,
            'rare': LightTheme.ACCENT_BLUE,
            'epic': LightTheme.ACCENT_PURPLE,
            'legendary': LightTheme.ACCENT_ORANGE
        }
        border_color = rarity_colors.get(achievement.rarity, LightTheme.BORDER_LIGHT)

        # 简化样式: 只使用 border-left 进行视觉区分
        if not unlocked:
            card.setStyleSheet(f"""
                QWidget {{
                    border-left: 3px solid {LightTheme.BORDER_LIGHT};
                    padding: 12px 16px;
                }}
            """)
        else:
            card.setStyleSheet(f"""
                QWidget {{
                    border-left: 3px solid {border_color};
                    padding: 12px 16px;
                }}
            """)

        layout = QHBoxLayout(card)
        layout.setSpacing(12)

        # 图标 (添加emoji字体支持)
        icon_label = QLabel(achievement.emoji if unlocked else "🔒")

        # 使用QFont设置emoji字体 (更可靠的方式)
        emoji_font = QFont()
        emoji_font.setPointSize(28)  # 增大字体
        emoji_font.setFamilies(["Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji"])
        icon_label.setFont(emoji_font)

        # 设置固定宽度但允许高度自适应,并添加内边距
        icon_label.setMinimumSize(60, 60)  # 增大最小尺寸
        icon_label.setMaximumSize(60, 60)  # 设置最大尺寸
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("padding: 5px;")  # 添加内边距防止裁剪
        layout.addWidget(icon_label)

        # 信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        # 名称和稀有度
        name_layout = QHBoxLayout()
        name_label = QLabel(achievement.name)  # 始终显示成就名称
        name_label.setStyleSheet(f"font-size: {LightTheme.FONT_SUBTITLE}px; font-weight: bold; color: {LightTheme.TEXT_PRIMARY if unlocked else LightTheme.TEXT_SECONDARY};")
        name_layout.addWidget(name_label)

        # 稀有度标签: 移除背景色,使用彩色文本
        rarity_text = {
            'common': '普通',
            'rare': '稀有',
            'epic': '史诗',
            'legendary': '传说'
        }.get(achievement.rarity, achievement.rarity)

        rarity_badge = QLabel(f"[{rarity_text}]")
        rarity_badge.setStyleSheet(f"""
            color: {border_color};
            font-size: {LightTheme.FONT_TINY}px;
            font-weight: bold;
        """)
        name_layout.addWidget(rarity_badge)
        name_layout.addStretch()

        info_layout.addLayout(name_layout)

        # 描述
        desc_label = QLabel(achievement.description)  # 始终显示成就描述
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"color: {LightTheme.TEXT_PRIMARY if unlocked else LightTheme.TEXT_SECONDARY}; font-size: {LightTheme.FONT_SMALL}px;")
        info_layout.addWidget(desc_label)

        # 解锁时间 (仅已解锁)
        if unlocked and achievement.unlocked_at:
            from datetime import datetime
            unlock_time = datetime.fromisoformat(achievement.unlocked_at)
            time_label = QLabel(f"解锁于: {unlock_time.strftime('%Y-%m-%d %H:%M')}")
            time_label.setStyleSheet(f"color: {LightTheme.TEXT_HINT}; font-size: {LightTheme.FONT_TINY}px;")
            info_layout.addWidget(time_label)

        layout.addLayout(info_layout, 1)

        return card

    # ============================================================
    # 激励系统回调和自动更新 (Sprint 4 - 后续拓展功能)
    # ============================================================

    def _update_motivation_system(self):
        """自动更新激励系统 (目标进度 + 成就检测) - 线程安全版本"""
        try:
            self.logger.info("🚀 Updating motivation system...")

            # 检查窗口是否还存在
            if not self.isVisible():
                self.logger.info("Window closed, skipping motivation update")
                return

            result = self.motivation_engine.update_all()

            completed_goals = result['completed_goals']
            unlocked_achievements = result['unlocked_achievements']

            # 刷新UI (如果有更新) - 确保在主线程
            if completed_goals or unlocked_achievements:
                # 使用QTimer.singleShot确保UI更新在主线程
                QTimer.singleShot(0, self._refresh_goals_tab)
                QTimer.singleShot(0, self._refresh_achievements_tab)

            self.logger.info(
                f"✅ Motivation update complete: "
                f"{len(completed_goals)} goals, {len(unlocked_achievements)} achievements"
            )

        except Exception as e:
            self.logger.error(f"Failed to update motivation system: {e}", exc_info=True)

    def _on_goal_completed(self, goal: Goal):
        """目标完成回调 - 显示庆祝动画"""
        self.logger.info(f"🎉 Goal completed callback: {goal.goal_type}")

        # 显示庆祝对话框
        self._show_goal_celebration(goal)

    def _on_achievement_unlocked(self, achievement: Achievement):
        """成就解锁回调 - 加入队列批量显示"""
        self.logger.info(f"🏆 Achievement unlocked callback: {achievement.name}")

        # 添加到待显示队列
        self.pending_achievements.append(achievement)

        # 重置定时器 (500ms后批量显示,避免连续弹窗)
        self.achievement_notification_timer.stop()
        self.achievement_notification_timer.start(500)

    def _show_batched_achievements(self):
        """批量显示成就解锁通知 (合并多个成就在一个对话框)"""
        if not self.pending_achievements:
            return

        try:
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
            from PySide6.QtCore import Qt

            # 取出所有待显示的成就
            achievements = self.pending_achievements[:]
            self.pending_achievements.clear()

            # 创建自定义对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("成就解锁!")
            dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
            dialog.setFixedWidth(340)
            dialog.setModal(True)

            # 主布局
            main_layout = QVBoxLayout(dialog)
            main_layout.setSpacing(16)
            main_layout.setContentsMargins(24, 20, 24, 20)

            if len(achievements) == 1:
                achievement = achievements[0]
                rarity_cn = self._get_rarity_cn(achievement.rarity)

                # 稀有度颜色映射
                rarity_colors = {
                    'common': '#78909C',
                    'rare': '#2196F3',
                    'epic': '#9C27B0',
                    'legendary': '#FF9800'
                }
                rarity_bg_colors = {
                    'common': '#ECEFF1',
                    'rare': '#E3F2FD',
                    'epic': '#F3E5F5',
                    'legendary': '#FFF3E0'
                }
                color = rarity_colors.get(achievement.rarity, '#4CAF50')
                bg_color = rarity_bg_colors.get(achievement.rarity, '#E8F5E9')

                # 成就图标区域
                icon_container = QFrame()
                icon_container.setStyleSheet(f"""
                    QFrame {{
                        background-color: {bg_color};
                        border-radius: 12px;
                        padding: 16px;
                    }}
                """)
                icon_layout = QVBoxLayout(icon_container)
                icon_layout.setAlignment(Qt.AlignCenter)

                icon_label = QLabel(achievement.emoji)
                icon_label.setStyleSheet("""
                    QLabel {
                        font-size: 48px;
                        font-family: "Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji";
                    }
                """)
                icon_label.setAlignment(Qt.AlignCenter)
                icon_layout.addWidget(icon_label)
                main_layout.addWidget(icon_container)

                # 成就名称
                name_label = QLabel(achievement.name)
                name_label.setStyleSheet(f"""
                    QLabel {{
                        font-size: 18px;
                        font-weight: bold;
                        color: {LightTheme.TEXT_PRIMARY};
                    }}
                """)
                name_label.setAlignment(Qt.AlignCenter)
                main_layout.addWidget(name_label)

                # 成就描述
                desc_label = QLabel(achievement.description)
                desc_label.setStyleSheet(f"""
                    QLabel {{
                        font-size: 14px;
                        color: {LightTheme.TEXT_SECONDARY};
                    }}
                """)
                desc_label.setAlignment(Qt.AlignCenter)
                desc_label.setWordWrap(True)
                main_layout.addWidget(desc_label)

                # 稀有度徽章
                rarity_badge = QLabel(f"⭐ 稀有度: {rarity_cn}")
                rarity_badge.setStyleSheet(f"""
                    QLabel {{
                        background-color: {bg_color};
                        color: {color};
                        font-size: 13px;
                        font-weight: 500;
                        padding: 6px 16px;
                        border-radius: 12px;
                    }}
                """)
                rarity_badge.setAlignment(Qt.AlignCenter)

                badge_container = QHBoxLayout()
                badge_container.addStretch()
                badge_container.addWidget(rarity_badge)
                badge_container.addStretch()
                main_layout.addLayout(badge_container)

            else:
                # 多个成就
                title_label = QLabel(f"🎉 恭喜!同时解锁 {len(achievements)} 个成就")
                title_label.setStyleSheet(f"""
                    QLabel {{
                        font-size: 16px;
                        font-weight: bold;
                        color: {LightTheme.TEXT_PRIMARY};
                    }}
                """)
                title_label.setAlignment(Qt.AlignCenter)
                main_layout.addWidget(title_label)

                # 成就列表
                for ach in achievements:
                    rarity_cn = self._get_rarity_cn(ach.rarity)

                    item_frame = QFrame()
                    item_frame.setStyleSheet(f"""
                        QFrame {{
                            background-color: {LightTheme.BG_SECONDARY};
                            border-radius: 8px;
                            padding: 8px;
                        }}
                    """)
                    item_layout = QHBoxLayout(item_frame)
                    item_layout.setContentsMargins(12, 8, 12, 8)

                    emoji_label = QLabel(ach.emoji)
                    emoji_label.setStyleSheet("""
                        QLabel {
                            font-size: 24px;
                            font-family: "Segoe UI Emoji", "Apple Color Emoji";
                        }
                    """)
                    item_layout.addWidget(emoji_label)

                    text_layout = QVBoxLayout()
                    text_layout.setSpacing(2)

                    name_lbl = QLabel(ach.name)
                    name_lbl.setStyleSheet(f"""
                        QLabel {{
                            font-size: 14px;
                            font-weight: bold;
                            color: {LightTheme.TEXT_PRIMARY};
                        }}
                    """)
                    text_layout.addWidget(name_lbl)

                    desc_lbl = QLabel(f"{ach.description} ({rarity_cn})")
                    desc_lbl.setStyleSheet(f"""
                        QLabel {{
                            font-size: 12px;
                            color: {LightTheme.TEXT_SECONDARY};
                        }}
                    """)
                    text_layout.addWidget(desc_lbl)

                    item_layout.addLayout(text_layout, 1)
                    main_layout.addWidget(item_frame)

                color = '#9C27B0'  # 多个成就使用紫色

            # 确定按钮
            main_layout.addSpacing(8)
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()

            ok_btn = QPushButton("确定")
            ok_btn.setFixedWidth(100)
            ok_btn.setCursor(Qt.PointingHandCursor)
            ok_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color if len(achievements) == 1 else '#9C27B0'};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 24px;
                    font-size: 14px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    opacity: 0.9;
                }}
            """)
            ok_btn.clicked.connect(dialog.accept)
            btn_layout.addWidget(ok_btn)
            btn_layout.addStretch()
            main_layout.addLayout(btn_layout)

            # 对话框样式
            dialog.setStyleSheet(f"""
                QDialog {{
                    background-color: {LightTheme.BG_PRIMARY};
                }}
            """)

            dialog.exec()

        except Exception as e:
            self.logger.error(f"Failed to show batched achievements: {e}", exc_info=True)

    def _get_rarity_cn(self, rarity: str) -> str:
        """获取稀有度中文名称"""
        rarity_map = {
            'common': '普通',
            'rare': '稀有',
            'epic': '史诗',
            'legendary': '传说'
        }
        return rarity_map.get(rarity, rarity)

    def _show_goal_celebration(self, goal: Goal):
        """显示目标完成庆祝动画"""
        try:
            from PySide6.QtWidgets import QMessageBox

            goal_info = goal.get_info()
            goal_name = goal_info['name']
            emoji = goal_info['emoji']

            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("🎉 目标达成!")
            msg_box.setText(f"恭喜!你已完成目标:")
            msg_box.setInformativeText(f"\n{emoji} {goal_name}\n\n继续保持,创造更多成就!")
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setStandardButtons(QMessageBox.Ok)

            # 应用样式 - 添加emoji字体支持
            msg_box.setStyleSheet(f"""
                QMessageBox {{
                    background-color: {LightTheme.BG_PRIMARY};
                }}
                QLabel {{
                    color: {LightTheme.TEXT_PRIMARY};
                    font-size: {LightTheme.FONT_BODY}px;
                    font-family: "Microsoft YaHei UI", "Segoe UI Emoji", "Apple Color Emoji";
                }}
                QPushButton {{
                    background-color: {LightTheme.ACCENT_GREEN};
                    color: white;
                    border: none;
                    border-radius: {LightTheme.RADIUS_SMALL}px;
                    padding: 8px 16px;
                    font-size: {LightTheme.FONT_BODY}px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {LightTheme.ACCENT_GREEN_HOVER};
                }}
            """)

            # 为所有QLabel设置emoji字体 (更可靠的方式)
            emoji_font = QFont()
            emoji_font.setPointSize(LightTheme.FONT_BODY)
            emoji_font.setFamilies(["Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji"])

            for label in msg_box.findChildren(QLabel):
                label.setFont(emoji_font)

            # 显示对话框
            msg_box.exec()

        except Exception as e:
            self.logger.error(f"Failed to show goal celebration: {e}", exc_info=True)

    def _refresh_goals_tab(self):
        """刷新目标页签"""
        try:
            # 查找目标页签的索引
            for i in range(self.tab_widget.count()):
                if "目标" in self.tab_widget.tabText(i):
                    # 移除旧的页签
                    self.tab_widget.removeTab(i)
                    # 重新创建
                    self.create_goals_tab()
                    break
        except Exception as e:
            self.logger.error(f"Failed to refresh goals tab: {e}", exc_info=True)

    def _refresh_achievements_tab(self):
        """刷新成就页签"""
        try:
            # 查找成就页签的索引
            for i in range(self.tab_widget.count()):
                if "成就" in self.tab_widget.tabText(i):
                    # 移除旧的页签
                    self.tab_widget.removeTab(i)
                    # 重新创建
                    self.create_achievements_tab()
                    break
        except Exception as e:
            self.logger.error(f"Failed to refresh achievements tab: {e}", exc_info=True)

    def _connect_inference_engine(self):
        """连接自动推理引擎 (延迟初始化)

        此方法在 showEvent 中调用,确保 main_window 属性已被设置
        """
        if self._engine_connected:
            return  # 已经连接过了

        # 尝试通过 main_window 属性访问主窗口
        main_window = getattr(self, 'main_window', None) or self.parent()

        if main_window and hasattr(main_window, 'auto_inference_engine'):
            engine = main_window.auto_inference_engine

            # 保存引擎引用,供导出功能使用
            self.auto_inference_engine = engine

            engine.inference_completed.connect(self.update_inference_ui)
            self.logger.info("已连接自动推理引擎信号")

            # 立即获取已有的推理数据并显示
            if hasattr(engine, 'inferred_tasks') and engine.inferred_tasks:
                self.logger.info(f"加载已有推理数据: {len(engine.inferred_tasks)} 个任务")
                self.update_inference_ui(engine.inferred_tasks)
            else:
                self.logger.info("暂无已有推理数据")

            self._engine_connected = True
        else:
            self.logger.warning("未找到自动推理引擎,自动推理功能将不可用")
            self.auto_inference_engine = None

    def showEvent(self, event):
        """窗口显示事件 - 延迟连接自动推理引擎"""
        super().showEvent(event)
        # 首次显示时连接自动推理引擎
        if not self._engine_connected:
            self._connect_inference_engine()

        # AI引导对话框已移除 - 用户无需手动确认，系统自动处理

    def closeEvent(self, event):
        """窗口关闭事件 - 清理资源"""
        try:
            # 停止激励系统定时器
            if hasattr(self, 'motivation_timer') and self.motivation_timer:
                self.motivation_timer.stop()
                self.logger.info("Motivation timer stopped")

            # 停止成就通知定时器
            if hasattr(self, 'achievement_notification_timer') and self.achievement_notification_timer:
                self.achievement_notification_timer.stop()
                self.logger.info("Achievement notification timer stopped")

            # 清空待显示队列
            if hasattr(self, 'pending_achievements'):
                self.pending_achievements.clear()

            self.closed.emit()
            super().closeEvent(event)

        except Exception as e:
            self.logger.error(f"Error in closeEvent: {e}", exc_info=True)
            super().closeEvent(event)

    def export_work_log(self):
        """导出工作日志为Markdown格式"""
        from datetime import date, datetime

        today = date.today()

        try:
            # 获取推理引擎的数据
            if not hasattr(self, 'auto_inference_engine') or not self.auto_inference_engine:
                QMessageBox.information(
                    self,
                    "提示",
                    "推理引擎未启动,无法导出工作日志"
                )
                return

            inferred_tasks = self.auto_inference_engine.inferred_tasks

            if not inferred_tasks:
                QMessageBox.information(
                    self,
                    "暂无数据",
                    "今天还没有识别到工作任务。\n\n"
                    "• AI推理每5分钟运行一次\n"
                    "• 请确保有足够的应用使用时间(建议15分钟以上)\n\n"
                    "💡 您也可以手动添加任务完成记录"
                )
                return

            # 生成文件名
            default_filename = f"工作日志_{today.strftime('%Y%m%d')}.md"

            # 打开文件保存对话框
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "导出工作日志",
                default_filename,
                "Markdown文件 (*.md);;所有文件 (*.*)"
            )

            if not file_path:
                return  # 用户取消

            # 生成Markdown内容
            md_content = self._generate_work_log_markdown(inferred_tasks, today)

            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(md_content)

            # 显示成功消息
            QMessageBox.information(
                self,
                "导出成功",
                f"工作日志已导出到:\n{file_path}\n\n"
                "💡 您可以将这个文件发送给客户或领导"
            )

            self.logger.info(f"工作日志已导出: {file_path}")

        except Exception as e:
            self.logger.error(f"导出工作日志失败: {e}", exc_info=True)
            QMessageBox.warning(
                self,
                "导出失败",
                f"导出失败:\n{str(e)}"
            )

    def _generate_work_log_markdown(self, inferred_tasks: list, date_obj: date) -> str:
        """生成工作日志的Markdown内容"""
        from datetime import datetime

        # 计算统计数据
        total_minutes = sum(t.get('duration_minutes', 0) for t in inferred_tasks)
        total_hours = total_minutes / 60

        # 开始生成Markdown
        md = f"# {date_obj.strftime('%Y年%m月%d日')} 工作日志\n\n"
        md += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        md += "---\n\n"

        # 工作任务总结
        md += "## 📊 工作任务总结\n\n"

        # 按任务名称分组统计
        task_summary = {}
        for task in inferred_tasks:
            task_name = task.get('name', '未知任务')
            duration = task.get('duration_minutes', 0)

            if task_name in task_summary:
                task_summary[task_name] += duration
            else:
                task_summary[task_name] = duration

        for task_name, duration in sorted(task_summary.items(), key=lambda x: x[1], reverse=True):
            md += f"- **{task_name}**: {duration}分钟\n"

        md += f"\n**总计**: {len(inferred_tasks)}个任务 · {total_minutes}分钟 ({total_hours:.1f}小时)\n\n"
        md += "---\n\n"

        # 详细时间线
        md += "## ⏰ 详细时间线\n\n"

        for task in inferred_tasks:
            task_name = task.get('name', '未知任务')
            start_time = task.get('start_time', '--')
            end_time = task.get('end_time', '--')
            duration = task.get('duration_minutes', 0)
            apps = task.get('apps', [])
            confidence = task.get('confidence', 0)

            md += f"### {start_time} - {end_time} | {task_name}\n\n"
            md += f"**时长**: {duration}分钟  \n"
            md += f"**使用工具**: {', '.join(apps[:5]) if apps else '无'}  \n"
            md += f"**AI置信度**: {confidence:.0%}  \n"
            md += "\n"

        md += "---\n\n"

        # 效率分析
        md += "## 📈 效率分析\n\n"

        # 计算平均置信度
        avg_confidence = sum(t.get('confidence', 0) for t in inferred_tasks) / len(inferred_tasks) if inferred_tasks else 0

        # 专注度评级
        if avg_confidence >= 0.9:
            focus_rating = "⭐⭐⭐⭐⭐"
            focus_comment = "非常专注"
        elif avg_confidence >= 0.8:
            focus_rating = "⭐⭐⭐⭐"
            focus_comment = "比较专注"
        else:
            focus_rating = "⭐⭐⭐"
            focus_comment = "需要改进"

        md += f"**专注度**: {focus_rating} ({focus_comment})  \n"
        md += f"**平均AI置信度**: {avg_confidence:.0%}  \n"
        md += f"**任务切换次数**: {len(inferred_tasks)}次  \n"

        md += "\n---\n\n"
        md += "*本报告由 GaiYa每日进度条 自动生成 | [https://www.gaiyatime.com](https://www.gaiyatime.com)*\n"

        return md
