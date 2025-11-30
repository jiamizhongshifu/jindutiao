"""
时间回放窗口
展示计划vs专注vs行为的综合时间分析
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QScrollArea, QWidget,
    QGroupBox, QProgressBar, QTextEdit, QSplitter,
    QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPainter, QColor, QPen

from gaiya.data.db_manager import db
from gaiya.services.app_category_manager import app_category_manager

logger = logging.getLogger("gaiya.ui.time_review_window")

class TimeReviewWindow(QDialog):
    """时间回放窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logger

        # 窗口设置
        self.setWindowTitle("⏰ 今日时间回放")
        self.setModal(True)
        self.resize(900, 700)
        self.setMinimumSize(800, 600)

        # 数据缓存
        self.review_data: Optional[Dict] = None
        self.activity_data: Optional[Dict] = None

        # 初始化UI
        self.init_ui()
        self.load_today_data()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title_label = QLabel(f"⏰ {datetime.now().strftime('%Y年%m月%d日')} 时间回放")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        # 左侧：计划vs专注
        left_widget = self.create_focus_review_panel()
        splitter.addWidget(left_widget)

        # 右侧：行为统计
        right_widget = self.create_activity_review_panel()
        splitter.addWidget(right_widget)

        # 设置分割器比例
        splitter.setSizes([450, 450])

        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        refresh_button = QPushButton("🔄 刷新数据")
        refresh_button.clicked.connect(self.load_today_data)
        button_layout.addWidget(refresh_button)

        export_button = QPushButton("📊 导出报告")
        export_button.clicked.connect(self.export_report)
        button_layout.addWidget(export_button)

        close_button = QPushButton("✖️ 关闭")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def create_focus_review_panel(self) -> QWidget:
        """创建专注回放面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        # 计划vs专注概览
        overview_group = QGroupBox("📋 今日专注概览")
        overview_layout = QFormLayout(overview_group)

        # 计划时间
        self.total_plan_time_label = QLabel("0小时0分钟")
        overview_layout.addRow("计划时间:", self.total_plan_time_label)

        # 专注时间
        self.total_focus_time_label = QLabel("0小时0分钟")
        overview_layout.addRow("红温专注:", self.total_focus_time_label)

        # 专注执行率
        self.focus_execution_rate_label = QLabel("0%")
        overview_layout.addRow("专注执行率:", self.focus_execution_rate_label)

        # 执行率进度条
        self.focus_rate_progress = QProgressBar()
        self.focus_rate_progress.setRange(0, 100)
        self.focus_rate_progress.setValue(0)
        self.focus_rate_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #e74c3c;
                border-radius: 3px;
            }
        """)
        overview_layout.addRow("执行进度:", self.focus_rate_progress)

        layout.addWidget(overview_group)

        # 时间块详细列表
        time_blocks_group = QGroupBox("📅 时间块详情")
        time_blocks_layout = QVBoxLayout(time_blocks_group)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.time_blocks_widget = QWidget()
        self.time_blocks_layout = QVBoxLayout(self.time_blocks_widget)
        self.time_blocks_layout.setSpacing(5)

        scroll_area.setWidget(self.time_blocks_widget)
        time_blocks_layout.addWidget(scroll_area)

        layout.addWidget(time_blocks_group)

        return widget

    def create_activity_review_panel(self) -> QWidget:
        """创建行为回放面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        # 活跃用机统计
        active_time_group = QGroupBox("💻 今日用机统计")
        active_time_layout = QFormLayout(active_time_group)

        # 总活跃时间
        self.total_active_time_label = QLabel("0小时0分钟")
        active_time_layout.addRow("活跃用机:", self.total_active_time_label)

        # 生产力时间
        self.productive_time_label = QLabel("0小时0分钟")
        active_time_layout.addRow("🎯 生产力:", self.productive_time_label)

        # 摸鱼时间
        self.leisure_time_label = QLabel("0小时0分钟")
        active_time_layout.addRow("🎮 摸鱼:", self.leisure_time_label)

        # 其他时间
        self.neutral_time_label = QLabel("0小时0分钟")
        active_time_layout.addRow("⚙️ 中性:", self.neutral_time_label)

        # 未分类时间
        self.unknown_time_label = QLabel("0小时0分钟")
        active_time_layout.addRow("❓ 未分类:", self.unknown_time_label)

        layout.addWidget(active_time_group)

        # Top App排行榜
        top_apps_group = QGroupBox("🏆 Top应用排行")
        top_apps_layout = QVBoxLayout(top_apps_group)

        # 创建应用排行榜
        self.top_apps_widget = QWidget()
        self.top_apps_layout = QVBoxLayout(self.top_apps_widget)
        self.top_apps_layout.setSpacing(3)

        top_apps_scroll = QScrollArea()
        top_apps_scroll.setWidget(self.top_apps_widget)
        top_apps_scroll.setWidgetResizable(True)
        top_apps_scroll.setMaximumHeight(200)

        top_apps_layout.addWidget(top_apps_scroll)
        layout.addWidget(top_apps_group)

        return widget

    def load_today_data(self):
        """加载今日数据"""
        try:
            start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)

            # 加载专注统计数据
            self.load_focus_data(start_of_day, end_of_day)

            # 加载行为统计数据
            self.load_activity_data(start_of_day, end_of_day)

            # 更新UI显示
            self.update_focus_review()
            self.update_activity_review()

            self.logger.info("已加载今日时间回放数据")

        except Exception as e:
            self.logger.error(f"加载今日数据失败: {e}")

    def load_focus_data(self, start_time: datetime, end_time: datetime):
        """加载专注数据"""
        try:
            # 这里需要从数据库获取时间块和专注会话数据
            # 暂时使用模拟数据
            self.review_data = {
                'total_plan_minutes': 480,  # 8小时
                'total_focus_minutes': 180,  # 3小时
                'focus_execution_rate': 37.5,
                'time_blocks': [
                    {
                        'name': '写方案',
                        'plan_minutes': 120,
                        'focus_minutes': 80,
                        'focus_sessions': 2
                    },
                    {
                        'name': '开会',
                        'plan_minutes': 90,
                        'focus_minutes': 60,
                        'focus_sessions': 1
                    },
                    {
                        'name': '写副业项目',
                        'plan_minutes': 150,
                        'focus_minutes': 0,
                        'focus_sessions': 0
                    },
                    {
                        'name': '学习',
                        'plan_minutes': 120,
                        'focus_minutes': 40,
                        'focus_sessions': 1
                    }
                ]
            }
        except Exception as e:
            self.logger.error(f"加载专注数据失败: {e}")
            self.review_data = {
                'total_plan_minutes': 0,
                'total_focus_minutes': 0,
                'focus_execution_rate': 0,
                'time_blocks': []
            }

    def load_activity_data(self, start_time: datetime, end_time: datetime):
        """加载行为数据"""
        try:
            # 从数据库获取今日行为统计
            self.activity_data = db.get_today_activity_stats()

            # 如果没有数据，使用默认值
            if not self.activity_data:
                self.activity_data = {
                    'total_seconds': 0,
                    'categories': {
                        'PRODUCTIVE': 0,
                        'LEISURE': 0,
                        'NEUTRAL': 0,
                        'UNKNOWN': 0
                    },
                    'top_apps': []
                }

        except Exception as e:
            self.logger.error(f"加载行为数据失败: {e}")
            self.activity_data = {
                'total_seconds': 0,
                'categories': {
                    'PRODUCTIVE': 0,
                    'LEISURE': 0,
                    'NEUTRAL': 0,
                    'UNKNOWN': 0
                },
                'top_apps': []
            }

    def update_focus_review(self):
        """更新专注回放显示"""
        if not self.review_data:
            return

        # 更新概览数据
        total_plan = self.review_data['total_plan_minutes']
        total_focus = self.review_data['total_focus_minutes']
        execution_rate = self.review_data['focus_execution_rate']

        self.total_plan_time_label.setText(f"{total_plan // 60}小时{total_plan % 60}分钟")
        self.total_focus_time_label.setText(f"{total_focus // 60}小时{total_focus % 60}分钟")
        self.focus_execution_rate_label.setText(f"{execution_rate:.1f}%")
        self.focus_rate_progress.setValue(int(execution_rate))

        # 清空并重建时间块列表
        self.clear_layout(self.time_blocks_layout)

        for block in self.review_data['time_blocks']:
            block_widget = self.create_time_block_widget(block)
            self.time_blocks_layout.addWidget(block_widget)

        self.time_blocks_layout.addStretch()

    def update_activity_review(self):
        """更新行为回放显示"""
        if not self.activity_data:
            return

        # 计算各类时间
        total_seconds = self.activity_data['total_seconds']
        categories = self.activity_data['categories']

        productive_seconds = categories.get('PRODUCTIVE', 0)
        leisure_seconds = categories.get('LEISURE', 0)
        neutral_seconds = categories.get('NEUTRAL', 0)
        unknown_seconds = categories.get('UNKNOWN', 0)

        # 更新时间显示
        self.total_active_time_label.setText(self.format_duration(total_seconds))
        self.productive_time_label.setText(self.format_duration(productive_seconds))
        self.leisure_time_label.setText(self.format_duration(leisure_seconds))
        self.neutral_time_label.setText(self.format_duration(neutral_seconds))
        self.unknown_time_label.setText(self.format_duration(unknown_seconds))

        # 更新Top应用列表
        self.update_top_apps(self.activity_data['top_apps'])

    def create_time_block_widget(self, block_data: Dict) -> QWidget:
        """创建时间块显示组件"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Box)
        widget.setStyleSheet("""
            QFrame {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                background-color: #f8f9fa;
                padding: 5px;
            }
        """)

        layout = QHBoxLayout(widget)
        layout.setSpacing(10)

        # 时间块名称
        name_label = QLabel(block_data['name'])
        name_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        name_label.setMinimumWidth(100)
        layout.addWidget(name_label)

        # 计划时间
        plan_label = QLabel(f"计划: {block_data['plan_minutes']}分钟")
        plan_label.setStyleSheet("color: #6c757d;")
        layout.addWidget(plan_label)

        # 专注时间
        focus_minutes = block_data['focus_minutes']
        focus_sessions = block_data['focus_sessions']

        if focus_minutes > 0:
            focus_label = QLabel(f"专注: {focus_minutes}分钟 ({focus_sessions}次)")
            focus_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        else:
            focus_label = QLabel("专注: 无记录")
            focus_label.setStyleSheet("color: #6c757d;")

        layout.addWidget(focus_label)

        # 专注完成度
        if block_data['plan_minutes'] > 0:
            completion_rate = (focus_minutes / block_data['plan_minutes']) * 100
            progress_bar = QProgressBar()
            progress_bar.setRange(0, 100)
            progress_bar.setValue(int(completion_rate))
            progress_bar.setMaximumWidth(100)
            progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    text-align: center;
                    font-size: 10px;
                }
                QProgressBar::chunk {
                    background-color: #e74c3c;
                    border-radius: 2px;
                }
            """)
            layout.addWidget(progress_bar)

        layout.addStretch()
        return widget

    def update_top_apps(self, top_apps: List[Dict]):
        """更新Top应用列表"""
        self.clear_layout(self.top_apps_layout)

        if not top_apps:
            no_data_label = QLabel("暂无应用数据")
            no_data_label.setAlignment(Qt.AlignCenter)
            no_data_label.setStyleSheet("color: #6c757d; padding: 20px;")
            self.top_apps_layout.addWidget(no_data_label)
            return

        for i, app in enumerate(top_apps[:10]):  # 显示前10个
            app_widget = self.create_top_app_widget(i + 1, app)
            self.top_apps_layout.addWidget(app_widget)

        self.top_apps_layout.addStretch()

    def create_top_app_widget(self, rank: int, app_data: Dict) -> QWidget:
        """创建Top应用显示组件"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.NoFrame)

        layout = QHBoxLayout(widget)
        layout.setSpacing(10)

        # 排名
        rank_label = QLabel(f"#{rank}")
        rank_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        rank_label.setStyleSheet("""
            QLabel {
                background-color: #e74c3c;
                color: white;
                border-radius: 10px;
                padding: 2px 6px;
                min-width: 30px;
                text-align: center;
            }
        """)
        rank_label.setAlignment(Qt.AlignCenter)
        rank_label.setMaximumWidth(40)
        layout.addWidget(rank_label)

        # 应用名称
        app_name = app_data.get('name', 'Unknown')
        if len(app_name) > 20:
            app_name = app_name[:17] + "..."

        name_label = QLabel(app_name)
        name_label.setMinimumWidth(150)
        layout.addWidget(name_label)

        # 分类标签
        category = app_data.get('category', 'UNKNOWN')
        category_colors = {
            'PRODUCTIVE': '#28a745',
            'LEISURE': '#dc3545',
            'NEUTRAL': '#6c757d',
            'UNKNOWN': '#ffc107'
        }
        category_names = {
            'PRODUCTIVE': '生产力',
            'LEISURE': '摸鱼',
            'NEUTRAL': '中性',
            'UNKNOWN': '未分类'
        }

        category_label = QLabel(category_names.get(category, '未分类'))
        category_color = category_colors.get(category, '#6c757d')
        category_label.setStyleSheet(f"""
            QLabel {{
                background-color: {category_color};
                color: white;
                border-radius: 3px;
                padding: 2px 8px;
                font-size: 10px;
            }}
        """)
        category_label.setAlignment(Qt.AlignCenter)
        category_label.setMaximumWidth(60)
        layout.addWidget(category_label)

        # 使用时长
        duration = app_data.get('duration', 0)
        duration_label = QLabel(self.format_duration(duration))
        duration_label.setStyleSheet("color: #2c3e50; font-weight: bold;")
        layout.addWidget(duration_label)

        layout.addStretch()
        return widget

    def format_duration(self, seconds: int) -> str:
        """格式化时长显示"""
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}分{secs}秒"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}小时{minutes}分钟"

    def clear_layout(self, layout):
        """清空布局"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def export_report(self):
        """导出时间报告"""
        try:
            # 这里可以实现导出为PDF、图片等功能
            QMessageBox.information(self, "提示", "报告导出功能开发中...")
        except Exception as e:
            self.logger.error(f"导出报告失败: {e}")