"""
任务统计报告GUI窗口
显示任务完成情况的可视化统计
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QTabWidget, QTableWidget, QTableWidgetItem,
                               QPushButton, QGroupBox, QScrollArea, QHeaderView,
                               QMessageBox, QFileDialog, QProgressBar)
from PySide6.QtCore import Qt, Signal, Q_ARG, Slot
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from statistics_manager import StatisticsManager
from gaiya.core.theme_manager import ThemeManager
from i18n.translator import tr
from gaiya.data.db_manager import db
from pathlib import Path
import logging
import sys


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
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
            }}
        """)

        # 图标和标题行
        title_layout = QHBoxLayout()
        if self.icon:
            icon_label = QLabel(self.icon)
            icon_label.setStyleSheet("font-size: 24px;")
            title_layout.addWidget(icon_label)

        title_label = QLabel(self.title)
        title_label.setStyleSheet("font-size: 12px; color: #757575;")
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


class StatisticsWindow(QWidget):
    """统计报告主窗口"""

    closed = Signal()  # 关闭信号
    inference_completed = Signal(bool, str)  # 推理完成信号 (success, error_msg)

    def __init__(self, stats_manager: StatisticsManager, logger: logging.Logger, parent=None):
        super().__init__(parent)
        self.stats_manager = stats_manager
        self.logger = logger
        
        # 初始化主题管理器
        if getattr(sys, 'frozen', False):
            app_dir = Path(sys.executable).parent
        else:
            app_dir = Path(__file__).parent
        self.theme_manager = ThemeManager(app_dir)
        self.theme_manager.register_ui_component(self)
        self.theme_manager.theme_changed.connect(self.apply_theme)
        
        self.init_ui()
        self.load_statistics()

        # 连接推理完成信号
        self.inference_completed.connect(self._on_inference_completed)

        # 应用初始主题
        self.apply_theme()

    def init_ui(self):
        """初始化用户界面"""
        # 设置为独立的顶层窗口,而不是子窗口
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        self.setWindowTitle('📊 任务统计报告 - GaiYa每日进度条')
        self.setGeometry(100, 100, 900, 700)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 顶部标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel(tr("statistics.window_title"))
        self.title_label = title_label  # 保存引用以便主题更新
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #2196F3;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        # 刷新按钮
        refresh_button = QPushButton(tr("statistics.btn_refresh"))
        refresh_button.clicked.connect(self.load_statistics)
        title_layout.addWidget(refresh_button)

        # 导出按钮
        export_button = QPushButton(tr("statistics.btn_export_csv"))
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

        main_layout.addWidget(self.tab_widget)

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

        # 行为识别摘要
        behavior_group = QGroupBox("⚡ 今日行为摘要")
        behavior_layout = QVBoxLayout(behavior_group)

        self.behavior_summary_label = QLabel("行为识别未启用或暂无数据")
        self.behavior_summary_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        behavior_layout.addWidget(self.behavior_summary_label)

        self.behavior_ratio_bar = QProgressBar()
        self.behavior_ratio_bar.setRange(0, 100)
        self.behavior_ratio_bar.setValue(0)
        self.behavior_ratio_bar.setFormat("🎯 生产力 0%")
        self.behavior_ratio_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ced4da;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        behavior_layout.addWidget(self.behavior_ratio_bar)

        self.behavior_ratio_detail_label = QLabel("🎯 生产力 0% | 🎮 摸鱼 0% | ⚙️ 中性 0% | ❓ 未分类 0%")
        self.behavior_ratio_detail_label.setStyleSheet("color: #6c757d;")
        behavior_layout.addWidget(self.behavior_ratio_detail_label)

        self.behavior_top_label = QLabel("🏆 Top 应用：暂无数据")
        behavior_layout.addWidget(self.behavior_top_label)

        content_layout.addWidget(behavior_group)

        # AI推理数据摘要区域 (作为主要展示区域)
        ai_summary_group = QGroupBox("🤖 AI推理数据摘要")
        ai_summary_layout = QVBoxLayout(ai_summary_group)

        # 第一行: 推理统计卡片 + 任务统计卡片 (紧凑布局)
        row1_layout = QHBoxLayout()

        # 左侧: AI推理核心指标
        ai_core_layout = QVBoxLayout()

        # 已推理任务数 & 平均完成度 (大字体,突出显示)
        ai_main_layout = QHBoxLayout()

        self.ai_inferred_label = QLabel("已推理: 0 个")
        self.ai_inferred_label.setStyleSheet("font-size: 16px; color: #2196F3; font-weight: bold;")
        ai_main_layout.addWidget(self.ai_inferred_label)

        ai_main_layout.addSpacing(30)

        self.ai_avg_completion_label = QLabel("平均完成度: 0%")
        self.ai_avg_completion_label.setStyleSheet("font-size: 16px; color: #4CAF50; font-weight: bold;")
        ai_main_layout.addWidget(self.ai_avg_completion_label)

        ai_main_layout.addStretch()
        ai_core_layout.addLayout(ai_main_layout)

        # 高置信度 & 待确认 (次要指标)
        ai_sub_layout = QHBoxLayout()

        self.ai_high_confidence_label = QLabel("高置信度: 0 个")
        self.ai_high_confidence_label.setStyleSheet("font-size: 13px; color: #FF9800;")
        ai_sub_layout.addWidget(self.ai_high_confidence_label)

        ai_sub_layout.addSpacing(20)

        self.ai_unconfirmed_label = QLabel("待确认: 0 个")
        self.ai_unconfirmed_label.setStyleSheet("font-size: 13px; color: #F44336;")
        ai_sub_layout.addWidget(self.ai_unconfirmed_label)

        ai_sub_layout.addStretch()
        ai_core_layout.addLayout(ai_sub_layout)

        row1_layout.addLayout(ai_core_layout, 3)

        # 右侧: 简化的任务统计卡片 (紧凑型)
        task_stats_layout = QHBoxLayout()

        # 总任务数卡片
        total_card = QWidget()
        total_card_layout = QVBoxLayout(total_card)
        total_card_layout.setContentsMargins(10, 5, 10, 5)
        total_card_layout.setSpacing(2)
        self.total_tasks_label = QLabel("0")
        self.total_tasks_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #2196F3;")
        self.total_tasks_label.setAlignment(Qt.AlignCenter)
        total_card_layout.addWidget(self.total_tasks_label)
        total_card_name = QLabel("📝 总任务")
        total_card_name.setStyleSheet("font-size: 11px; color: #757575;")
        total_card_name.setAlignment(Qt.AlignCenter)
        total_card_layout.addWidget(total_card_name)
        total_card.setStyleSheet("background-color: #E3F2FD; border-radius: 5px;")
        task_stats_layout.addWidget(total_card)

        # 已完成卡片
        completed_card = QWidget()
        completed_card_layout = QVBoxLayout(completed_card)
        completed_card_layout.setContentsMargins(10, 5, 10, 5)
        completed_card_layout.setSpacing(2)
        self.completed_tasks_label = QLabel("0")
        self.completed_tasks_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #4CAF50;")
        self.completed_tasks_label.setAlignment(Qt.AlignCenter)
        completed_card_layout.addWidget(self.completed_tasks_label)
        completed_card_name = QLabel("✅ 已完成")
        completed_card_name.setStyleSheet("font-size: 11px; color: #757575;")
        completed_card_name.setAlignment(Qt.AlignCenter)
        completed_card_layout.addWidget(completed_card_name)
        completed_card.setStyleSheet("background-color: #E8F5E9; border-radius: 5px;")
        task_stats_layout.addWidget(completed_card)

        # 进行中卡片
        in_progress_card = QWidget()
        in_progress_card_layout = QVBoxLayout(in_progress_card)
        in_progress_card_layout.setContentsMargins(10, 5, 10, 5)
        in_progress_card_layout.setSpacing(2)
        self.in_progress_tasks_label = QLabel("0")
        self.in_progress_tasks_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #FF9800;")
        self.in_progress_tasks_label.setAlignment(Qt.AlignCenter)
        in_progress_card_layout.addWidget(self.in_progress_tasks_label)
        in_progress_card_name = QLabel("⏳ 进行中")
        in_progress_card_name.setStyleSheet("font-size: 11px; color: #757575;")
        in_progress_card_name.setAlignment(Qt.AlignCenter)
        in_progress_card_layout.addWidget(in_progress_card_name)
        in_progress_card.setStyleSheet("background-color: #FFF3E0; border-radius: 5px;")
        task_stats_layout.addWidget(in_progress_card)

        # 未开始卡片
        not_started_card = QWidget()
        not_started_card_layout = QVBoxLayout(not_started_card)
        not_started_card_layout.setContentsMargins(10, 5, 10, 5)
        not_started_card_layout.setSpacing(2)
        self.not_started_tasks_label = QLabel("0")
        self.not_started_tasks_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #F44336;")
        self.not_started_tasks_label.setAlignment(Qt.AlignCenter)
        not_started_card_layout.addWidget(self.not_started_tasks_label)
        not_started_card_name = QLabel("⏰ 未开始")
        not_started_card_name.setStyleSheet("font-size: 11px; color: #757575;")
        not_started_card_name.setAlignment(Qt.AlignCenter)
        not_started_card_layout.addWidget(not_started_card_name)
        not_started_card.setStyleSheet("background-color: #FFEBEE; border-radius: 5px;")
        task_stats_layout.addWidget(not_started_card)

        row1_layout.addLayout(task_stats_layout, 2)
        ai_summary_layout.addLayout(row1_layout)

        # 第二行: 智能提示 + 操作按钮
        row2_layout = QHBoxLayout()

        self.ai_accuracy_hint_label = QLabel("💡 提示: 持续确认任务完成度,可以提高AI推理的准确度")
        self.ai_accuracy_hint_label.setStyleSheet("font-size: 12px; color: #757575;")
        row2_layout.addWidget(self.ai_accuracy_hint_label)

        row2_layout.addStretch()

        # 手动触发推理按钮
        self.trigger_inference_button = QPushButton("🔄 手动生成推理")
        self.trigger_inference_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
            }
        """)
        self.trigger_inference_button.clicked.connect(self.trigger_manual_inference)
        row2_layout.addWidget(self.trigger_inference_button)

        ai_summary_layout.addLayout(row2_layout)

        content_layout.addWidget(ai_summary_group)

        # 操作按钮区域 (移除了任务详情表格,直接提供操作按钮)
        action_group = QGroupBox("📋 操作")
        action_layout = QVBoxLayout(action_group)
        action_layout.setContentsMargins(20, 15, 20, 15)

        # 说明文字
        hint_label = QLabel(
            "💡 点击下方按钮查看和确认今日任务完成度\n"
            "   批量确认窗口会显示所有任务的详细信息"
        )
        hint_label.setStyleSheet("color: #757575; font-size: 13px; padding: 10px;")
        hint_label.setWordWrap(True)
        action_layout.addWidget(hint_label)

        # 按钮容器 (水平居中)
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.confirm_button = QPushButton("✅ 确认/修正任务完成度")
        self.confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.confirm_button.clicked.connect(self.open_task_review_window)
        button_layout.addWidget(self.confirm_button)

        button_layout.addSpacing(20)

        # AI深度分析按钮
        self.ai_analysis_button = QPushButton("🤖 AI深度分析")
        self.ai_analysis_button.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.ai_analysis_button.clicked.connect(self.trigger_ai_analysis)
        button_layout.addWidget(self.ai_analysis_button)

        button_layout.addStretch()
        action_layout.addLayout(button_layout)

        content_layout.addWidget(action_group)

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

        # 本周统计摘要 (卡片式设计)
        weekly_summary_group = QGroupBox("📊 本周统计摘要")
        weekly_summary_layout = QVBoxLayout(weekly_summary_group)

        # 统计卡片布局
        cards_layout = QHBoxLayout()

        # 总任务数卡片
        total_card = QWidget()
        total_card_layout = QVBoxLayout(total_card)
        total_card_layout.setContentsMargins(10, 10, 10, 10)
        total_card_layout.setSpacing(5)
        self.weekly_total_label = QLabel("0")
        self.weekly_total_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2196F3;")
        self.weekly_total_label.setAlignment(Qt.AlignCenter)
        total_card_layout.addWidget(self.weekly_total_label)
        total_card_name = QLabel("📝 总任务")
        total_card_name.setStyleSheet("font-size: 12px; color: #757575;")
        total_card_name.setAlignment(Qt.AlignCenter)
        total_card_layout.addWidget(total_card_name)
        total_card.setStyleSheet("background-color: #E3F2FD; border-radius: 8px;")
        cards_layout.addWidget(total_card)

        # 已完成卡片
        completed_card = QWidget()
        completed_card_layout = QVBoxLayout(completed_card)
        completed_card_layout.setContentsMargins(10, 10, 10, 10)
        completed_card_layout.setSpacing(5)
        self.weekly_completed_label = QLabel("0")
        self.weekly_completed_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4CAF50;")
        self.weekly_completed_label.setAlignment(Qt.AlignCenter)
        completed_card_layout.addWidget(self.weekly_completed_label)
        completed_card_name = QLabel("✅ 已完成")
        completed_card_name.setStyleSheet("font-size: 12px; color: #757575;")
        completed_card_name.setAlignment(Qt.AlignCenter)
        completed_card_layout.addWidget(completed_card_name)
        completed_card.setStyleSheet("background-color: #E8F5E9; border-radius: 8px;")
        cards_layout.addWidget(completed_card)

        # 平均完成率卡片
        avg_card = QWidget()
        avg_card_layout = QVBoxLayout(avg_card)
        avg_card_layout.setContentsMargins(10, 10, 10, 10)
        avg_card_layout.setSpacing(5)
        self.weekly_avg_label = QLabel("0%")
        self.weekly_avg_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #FF9800;")
        self.weekly_avg_label.setAlignment(Qt.AlignCenter)
        avg_card_layout.addWidget(self.weekly_avg_label)
        avg_card_name = QLabel("📈 平均完成率")
        avg_card_name.setStyleSheet("font-size: 12px; color: #757575;")
        avg_card_name.setAlignment(Qt.AlignCenter)
        avg_card_layout.addWidget(avg_card_name)
        avg_card.setStyleSheet("background-color: #FFF3E0; border-radius: 8px;")
        cards_layout.addWidget(avg_card)

        # 总时长卡片
        hours_card = QWidget()
        hours_card_layout = QVBoxLayout(hours_card)
        hours_card_layout.setContentsMargins(10, 10, 10, 10)
        hours_card_layout.setSpacing(5)
        self.weekly_hours_label = QLabel("0h")
        self.weekly_hours_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #9C27B0;")
        self.weekly_hours_label.setAlignment(Qt.AlignCenter)
        hours_card_layout.addWidget(self.weekly_hours_label)
        hours_card_name = QLabel("⏱️ 总时长")
        hours_card_name.setStyleSheet("font-size: 12px; color: #757575;")
        hours_card_name.setAlignment(Qt.AlignCenter)
        hours_card_layout.addWidget(hours_card_name)
        hours_card.setStyleSheet("background-color: #F3E5F5; border-radius: 8px;")
        cards_layout.addWidget(hours_card)

        weekly_summary_layout.addLayout(cards_layout)
        content_layout.addWidget(weekly_summary_group)

        # 每日趋势表格
        trend_group = QGroupBox(tr("statistics.table.daily_completion"))
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
        # 样式将在 apply_theme 中设置

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # 本月统计摘要 (卡片式设计)
        monthly_summary_group = QGroupBox("📊 本月统计摘要")
        monthly_summary_layout = QVBoxLayout(monthly_summary_group)

        # 统计卡片布局
        cards_layout = QHBoxLayout()

        # 总任务数卡片
        total_card = QWidget()
        total_card_layout = QVBoxLayout(total_card)
        total_card_layout.setContentsMargins(10, 10, 10, 10)
        total_card_layout.setSpacing(5)
        self.monthly_total_label = QLabel("0")
        self.monthly_total_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2196F3;")
        self.monthly_total_label.setAlignment(Qt.AlignCenter)
        total_card_layout.addWidget(self.monthly_total_label)
        total_card_name = QLabel("📝 总任务")
        total_card_name.setStyleSheet("font-size: 12px; color: #757575;")
        total_card_name.setAlignment(Qt.AlignCenter)
        total_card_layout.addWidget(total_card_name)
        total_card.setStyleSheet("background-color: #E3F2FD; border-radius: 8px;")
        cards_layout.addWidget(total_card)

        # 已完成卡片
        completed_card = QWidget()
        completed_card_layout = QVBoxLayout(completed_card)
        completed_card_layout.setContentsMargins(10, 10, 10, 10)
        completed_card_layout.setSpacing(5)
        self.monthly_completed_label = QLabel("0")
        self.monthly_completed_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4CAF50;")
        self.monthly_completed_label.setAlignment(Qt.AlignCenter)
        completed_card_layout.addWidget(self.monthly_completed_label)
        completed_card_name = QLabel("✅ 已完成")
        completed_card_name.setStyleSheet("font-size: 12px; color: #757575;")
        completed_card_name.setAlignment(Qt.AlignCenter)
        completed_card_layout.addWidget(completed_card_name)
        completed_card.setStyleSheet("background-color: #E8F5E9; border-radius: 8px;")
        cards_layout.addWidget(completed_card)

        # 平均完成率卡片
        avg_card = QWidget()
        avg_card_layout = QVBoxLayout(avg_card)
        avg_card_layout.setContentsMargins(10, 10, 10, 10)
        avg_card_layout.setSpacing(5)
        self.monthly_avg_label = QLabel("0%")
        self.monthly_avg_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #FF9800;")
        self.monthly_avg_label.setAlignment(Qt.AlignCenter)
        avg_card_layout.addWidget(self.monthly_avg_label)
        avg_card_name = QLabel("📈 平均完成率")
        avg_card_name.setStyleSheet("font-size: 12px; color: #757575;")
        avg_card_name.setAlignment(Qt.AlignCenter)
        avg_card_layout.addWidget(avg_card_name)
        avg_card.setStyleSheet("background-color: #FFF3E0; border-radius: 8px;")
        cards_layout.addWidget(avg_card)

        # 总时长卡片
        hours_card = QWidget()
        hours_card_layout = QVBoxLayout(hours_card)
        hours_card_layout.setContentsMargins(10, 10, 10, 10)
        hours_card_layout.setSpacing(5)
        self.monthly_hours_label = QLabel("0h")
        self.monthly_hours_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #9C27B0;")
        self.monthly_hours_label.setAlignment(Qt.AlignCenter)
        hours_card_layout.addWidget(self.monthly_hours_label)
        hours_card_name = QLabel("⏱️ 总时长")
        hours_card_name.setStyleSheet("font-size: 12px; color: #757575;")
        hours_card_name.setAlignment(Qt.AlignCenter)
        hours_card_layout.addWidget(hours_card_name)
        hours_card.setStyleSheet("background-color: #F3E5F5; border-radius: 8px;")
        cards_layout.addWidget(hours_card)

        monthly_summary_layout.addLayout(cards_layout)
        content_layout.addWidget(monthly_summary_group)

        # 每日统计表格
        daily_group = QGroupBox(tr("statistics.table.daily_stats"))
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

        # 标题
        title_label = QLabel(tr("statistics.tab.category_history"))
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
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
        """加载今日统计"""
        summary = self.stats_manager.get_today_summary()

        # 更新紧凑型统计卡片
        self.total_tasks_label.setText(str(summary['total_tasks']))
        self.completed_tasks_label.setText(str(summary['completed_tasks']))
        self.in_progress_tasks_label.setText(str(summary['in_progress_tasks']))
        self.not_started_tasks_label.setText(str(summary['not_started_tasks']))

        # 更新AI推理数据摘要
        self.update_ai_summary(summary)

        # 任务详情表格已移除,用户通过"确认/修正任务完成度"按钮查看详情

        # 更新行为摘要
        activity_stats = db.get_today_activity_stats() or {}
        self.update_behavior_summary(activity_stats)

    def update_ai_summary(self, summary: dict):
        """更新AI推理数据摘要

        Args:
            summary: 统计摘要数据
        """
        # 检查是否有推理数据
        if summary.get('data_source') == 'task_completions':
            # 有推理数据
            total_tasks = summary.get('total_tasks', 0)
            high_confidence = summary.get('high_confidence_tasks', 0)
            avg_completion = summary.get('avg_completion_percentage', 0)

            # 计算待确认任务数
            try:
                from datetime import date
                today = date.today().isoformat()
                unconfirmed = db.get_unconfirmed_task_completions(today)
                unconfirmed_count = len(unconfirmed) if unconfirmed else 0
            except Exception:
                unconfirmed_count = 0

            # 更新标签
            self.ai_inferred_label.setText(f"已推理: {total_tasks} 个任务")
            self.ai_avg_completion_label.setText(f"平均完成度: {avg_completion}%")
            self.ai_high_confidence_label.setText(f"高置信度: {high_confidence} 个")
            self.ai_unconfirmed_label.setText(f"待确认: {unconfirmed_count} 个")

            # 如果有待确认任务,高亮显示
            if unconfirmed_count > 0:
                self.ai_unconfirmed_label.setStyleSheet(
                    "font-size: 14px; color: #F44336; font-weight: bold; "
                    "background-color: #FFEBEE; padding: 5px; border-radius: 3px;"
                )
            else:
                self.ai_unconfirmed_label.setStyleSheet(
                    "font-size: 14px; color: #4CAF50; font-weight: bold;"
                )

            # 更新提示文字
            if avg_completion >= 80:
                hint = "✨ 太棒了!今天的任务完成度很高!"
            elif avg_completion >= 50:
                hint = "💪 继续加油!完成度还不错!"
            else:
                hint = "📊 今天的完成度较低,确认后帮助AI更准确分析"

            self.ai_accuracy_hint_label.setText(hint)

        else:
            # 无推理数据,显示提示
            self.ai_inferred_label.setText("今日尚未生成推理数据")
            self.ai_avg_completion_label.setText("平均完成度: --")
            self.ai_high_confidence_label.setText("高置信度: --")
            self.ai_unconfirmed_label.setText("待确认: --")
            self.ai_accuracy_hint_label.setText(
                "💡 提示: 每晚21:00自动生成推理,或点击下方按钮手动触发"
            )

    def update_behavior_summary(self, activity_stats: dict):
        """刷新行为识别摘要"""
        total_seconds = activity_stats.get('total_seconds', 0) or 0
        categories = activity_stats.get('categories', {}) or {}

        productive_seconds = categories.get('PRODUCTIVE', 0) or 0
        leisure_seconds = categories.get('LEISURE', 0) or 0
        neutral_seconds = categories.get('NEUTRAL', 0) or 0
        unknown_seconds = categories.get('UNKNOWN', 0) or 0

        if total_seconds > 0:
            self.behavior_summary_label.setText(f"今日活跃用机：{self._format_duration(total_seconds)}")
            productive_pct = (productive_seconds / total_seconds) * 100
            leisure_pct = (leisure_seconds / total_seconds) * 100
            neutral_pct = (neutral_seconds / total_seconds) * 100
            unknown_pct = max(0.0, 100 - productive_pct - leisure_pct - neutral_pct)

            self.behavior_ratio_bar.setValue(int(round(productive_pct)))
            self.behavior_ratio_bar.setFormat(f"🎯 生产力 {productive_pct:.1f}%")
            self.behavior_ratio_detail_label.setText(
                f"🎯 生产力 {productive_pct:.1f}% | "
                f"🎮 摸鱼 {leisure_pct:.1f}% | "
                f"⚙️ 中性 {neutral_pct:.1f}% | "
                f"❓ 未分类 {unknown_pct:.1f}%"
            )

            top_apps = activity_stats.get('top_apps', []) or []
            if top_apps:
                top = top_apps[0]
                category_map = {
                    'PRODUCTIVE': '生产力',
                    'LEISURE': '摸鱼',
                    'NEUTRAL': '中性',
                    'UNKNOWN': '未分类'
                }
                category_cn = category_map.get(top.get('category', 'UNKNOWN'), '未分类')
                self.behavior_top_label.setText(
                    f"🏆 Top 应用：{top.get('name', 'Unknown')} "
                    f"{self._format_duration(top.get('duration', 0))}（{category_cn}）"
                )
            else:
                self.behavior_top_label.setText("🏆 Top 应用：暂无数据")
        else:
            self.behavior_summary_label.setText("行为识别未启用或暂无数据")
            self.behavior_ratio_bar.setValue(0)
            self.behavior_ratio_bar.setFormat("🎯 生产力 0%")
            self.behavior_ratio_detail_label.setText(
                "🎯 生产力 0% | 🎮 摸鱼 0% | ⚙️ 中性 0% | ❓ 未分类 0%"
            )
            self.behavior_top_label.setText("🏆 Top 应用：暂无数据")

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
        """应用当前主题到统计窗口"""
        theme = self.theme_manager.get_current_theme()
        if not theme:
            return
        
        bg_color = theme.get('background_color', '#FFFFFF')
        text_color = theme.get('text_color', '#000000')
        accent_color = theme.get('accent_color', '#2196F3')
        
        # 应用窗口背景色
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                color: {text_color};
            }}
        """)
        
        # 更新标题颜色
        if hasattr(self, 'title_label'):
            self.title_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {accent_color};")
        
        if hasattr(self, 'tab_widget'):
            self.tab_widget.setStyleSheet(f"""
                QTabWidget::pane {{
                    border: 1px solid #E0E0E0;
                    background: {bg_color};
                }}
                QTabBar::tab {{
                    padding: 10px 20px;
                    margin-right: 2px;
                    background: {bg_color};
                    color: {text_color};
                }}
                QTabBar::tab:selected {{
                    background: {accent_color};
                    color: white;
                }}
            """)
        
        # 更新滚动区域背景
        for scroll in self.findChildren(QScrollArea):
            scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {bg_color}; }}")
        
        # 更新表格样式
        for table in self.findChildren(QTableWidget):
            table.setStyleSheet(f"""
                QTableWidget {{
                    border: 1px solid #E0E0E0;
                    gridline-color: #E0E0E0;
                    background-color: {bg_color};
                    color: {text_color};
                }}
                QTableWidget::item {{
                    padding: 8px;
                }}
                QHeaderView::section {{
                    background-color: {accent_color};
                    color: white;
                    padding: 8px;
                }}
            """)
        
        # 更新统计卡片样式
        for card in self.findChildren(StatCard):
            card.setStyleSheet(f"""
                StatCard {{
                    background-color: {bg_color};
                    border: 1px solid #E0E0E0;
                    border-radius: 8px;
                }}
            """)
        
        self.logger.info(f"已应用主题到统计窗口: {theme.get('name', 'Unknown')}")

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
                    self.logger.info(f"[手动推理] parent有task_completion_scheduler属性吗? {hasattr(main_window, 'task_completion_scheduler')}")
                    if not hasattr(main_window, 'task_completion_scheduler'):
                        self.logger.error("[手动推理] 未找到任务完成推理调度器")
                        # 发射信号通知推理失败
                        self.inference_completed.emit(False, "未找到任务完成推理调度器,请检查配置")
                        return

                    scheduler = main_window.task_completion_scheduler

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

        layout = QVBoxLayout(dialog)

        # 标题
        title_label = QLabel(f"📊 {date} 任务完成度深度分析")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title_label)

        # 分析内容
        text_edit = QTextEdit()
        text_edit.setPlainText(analysis_text)
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #F5F5F5;
                border: 1px solid #E0E0E0;
                border-radius: 5px;
                padding: 15px;
                font-size: 14px;
                line-height: 1.6;
            }
        """)
        layout.addWidget(text_edit)

        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 30px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
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

    def closeEvent(self, event):
        """窗口关闭事件"""
        self.closed.emit()
        super().closeEvent(event)
