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
from gaiya.core.focus_tracker import calculate_focus_from_activity_log
from gaiya.services.app_category_manager import app_category_manager
from gaiya.utils import data_loader, path_utils, time_utils
from gaiya.utils.time_block_utils import generate_time_block_id

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
        layout.setSpacing(8)  # 减小间距
        layout.setContentsMargins(10, 10, 10, 10)  # 减小边距

        # 将日期信息移到窗口标题
        date_str = datetime.now().strftime('%Y年%m月%d日')
        self.setWindowTitle(f"⏰ 今日时间回放 - {date_str}")

        # 创建分割器(移除大标题,直接使用分割器)
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

        # 左侧按钮：行为识别设置
        activity_settings_button = QPushButton("🔍 行为识别设置")
        activity_settings_button.clicked.connect(self.show_activity_settings)
        button_layout.addWidget(activity_settings_button)

        button_layout.addStretch()

        refresh_button = QPushButton("🔄 刷新数据")
        refresh_button.clicked.connect(self.load_today_data)
        button_layout.addWidget(refresh_button)

        export_button = QPushButton("📊 导出报告")
        export_button.clicked.connect(self.export_report)
        button_layout.addWidget(export_button)

        # 添加"查看详细报告"按钮
        detail_report_button = QPushButton("📈 查看详细报告")
        detail_report_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        detail_report_button.clicked.connect(self.open_statistics_report)
        button_layout.addWidget(detail_report_button)

        close_button = QPushButton("✖️ 关闭")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def create_focus_review_panel(self) -> QWidget:
        """创建专注回放面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        # 红温专注概览 - 简洁版
        overview_group = QGroupBox("🔥 红温专注概览")
        overview_layout = QVBoxLayout(overview_group)
        overview_layout.setSpacing(8)
        overview_layout.setContentsMargins(10, 10, 10, 10)

        # 总专注时间 (大字号显示)
        focus_time_container = QWidget()
        focus_time_layout = QHBoxLayout(focus_time_container)
        focus_time_layout.setContentsMargins(0, 0, 0, 0)

        focus_time_label = QLabel("今日专注:")
        focus_time_label.setStyleSheet("font-size: 14px; font-weight: bold;")

        self.total_focus_time_label = QLabel("0小时0分钟")
        self.total_focus_time_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #e74c3c;")

        focus_time_layout.addWidget(focus_time_label)
        focus_time_layout.addWidget(self.total_focus_time_label)
        focus_time_layout.addStretch()

        overview_layout.addWidget(focus_time_container)

        layout.addWidget(overview_group)

        # 专注任务列表
        tasks_group = QGroupBox("📝 专注任务")
        tasks_layout = QVBoxLayout(tasks_group)
        tasks_layout.setSpacing(3)
        tasks_layout.setContentsMargins(5, 5, 5, 5)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setMinimumHeight(400)

        self.focus_tasks_widget = QWidget()
        self.focus_tasks_layout = QVBoxLayout(self.focus_tasks_widget)
        self.focus_tasks_layout.setSpacing(4)
        self.focus_tasks_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area.setWidget(self.focus_tasks_widget)
        tasks_layout.addWidget(scroll_area)

        layout.addWidget(tasks_group)

        return widget

    def create_activity_review_panel(self) -> QWidget:
        """创建行为回放面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(5)  # 减小间距
        layout.setContentsMargins(0, 0, 0, 0)  # 移除边距

        # 行为识别摘要
        summary_group = QGroupBox("⚡ 行为摘要")  # 简化标题
        summary_layout = QVBoxLayout(summary_group)
        summary_layout.setSpacing(5)  # 减小间距

        self.behavior_summary_label = QLabel("行为识别未启用或暂无数据")
        self.behavior_summary_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        summary_layout.addWidget(self.behavior_summary_label)

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
        summary_layout.addWidget(self.behavior_ratio_bar)

        self.behavior_ratio_detail_label = QLabel("🎯 生产力 0% | 🎮 摸鱼 0% | ⚙️ 中性 0% | ❓ 未分类 0%")
        self.behavior_ratio_detail_label.setStyleSheet("color: #6c757d;")
        summary_layout.addWidget(self.behavior_ratio_detail_label)

        self.behavior_top_label = QLabel("🏆 Top 应用：暂无数据")
        summary_layout.addWidget(self.behavior_top_label)

        layout.addWidget(summary_group)

        # 活跃用机统计
        active_time_group = QGroupBox("💻 用机统计")  # 简化标题
        active_time_layout = QFormLayout(active_time_group)
        active_time_layout.setSpacing(4)  # 减小间距

        # 总活跃时间
        self.total_active_time_label = QLabel("0小时0分钟")
        active_time_layout.addRow("活跃用机:", self.total_active_time_label)

        # 生产力时间
        self.productive_time_label = QLabel("0小时0分钟")
        active_time_layout.addRow("🎯 生产力:", self.productive_time_label)

        # 专注时长 (新增)
        self.focus_time_label = QLabel("0小时0分钟")
        self.focus_time_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        active_time_layout.addRow("🔥 专注时长:", self.focus_time_label)

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

        # 数据说明卡片 (新增)
        info_card = QLabel(
            "💡 <b>数据说明</b><br>"
            "• <b>生产力时长</b>: 使用生产力应用的总时长(可以碎片化)<br>"
            "• <b>专注时长</b>: 连续使用同一应用 ≥25分钟 的时长(深度工作)"
        )
        info_card.setStyleSheet("""
            QLabel {
                background-color: rgba(33, 150, 243, 0.1);
                border-left: 4px solid #2196F3;
                border-radius: 4px;
                padding: 12px;
                color: #2c3e50;
                font-size: 10pt;
            }
        """)
        info_card.setWordWrap(True)
        layout.addWidget(info_card)

        # Top App排行榜 (增加高度)
        top_apps_group = QGroupBox("🏆 应用排行")  # 简化标题
        top_apps_layout = QVBoxLayout(top_apps_group)
        top_apps_layout.setSpacing(3)  # 减小间距
        top_apps_layout.setContentsMargins(5, 5, 5, 5)  # 减小边距

        # 创建应用排行榜
        self.top_apps_widget = QWidget()
        self.top_apps_layout = QVBoxLayout(self.top_apps_widget)
        self.top_apps_layout.setSpacing(3)
        self.top_apps_layout.setContentsMargins(0, 0, 0, 0)

        top_apps_scroll = QScrollArea()
        top_apps_scroll.setWidget(self.top_apps_widget)
        top_apps_scroll.setWidgetResizable(True)
        top_apps_scroll.setMinimumHeight(250)  # 增加最小高度
        # 移除最大高度限制,让它自动扩展

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

    def _get_tasks(self):
        """获取用于统计的时间块列表。"""
        parent = self.parent()
        if parent and hasattr(parent, 'tasks'):
            tasks = getattr(parent, 'tasks', [])
            if tasks:
                return tasks

        try:
            app_dir = path_utils.get_app_dir()
            return data_loader.load_tasks(app_dir, self.logger)
        except Exception as e:
            self.logger.error(f"加载任务数据失败: {e}")
            return []

    def _calculate_plan_minutes(self, task: Dict) -> int:
        """根据任务开始结束时间计算计划分钟数。"""
        try:
            start_seconds = time_utils.time_str_to_seconds(task.get('start', '00:00'))
            end_seconds = time_utils.time_str_to_seconds(task.get('end', '00:00'))
            duration = max(0, end_seconds - start_seconds)
            return duration // 60
        except Exception as e:
            self.logger.warning(f"计算任务时长失败: {e}")
            return 0

    def _resolve_time_block_id(self, task: Dict, index: int) -> str:
        """生成与主窗口相同的时间块ID。"""
        try:
            return generate_time_block_id(task, index)
        except Exception as e:
            self.logger.warning(f"生成时间块ID失败: {e}")
            return f"time-block-{index}"

    def load_focus_data(self, start_time: datetime, end_time: datetime):
        """加载专注数据"""
        try:
            tasks = self._get_tasks()
            focus_stats = db.get_today_focus_stats() or {}
            focus_by_block = focus_stats.get('by_block', {})
            total_focus_minutes = focus_stats.get('total_minutes', 0) or 0

            time_blocks = []
            total_plan_minutes = 0
            matched_block_ids = set()

            for idx, task in enumerate(tasks):
                plan_minutes = self._calculate_plan_minutes(task)
                total_plan_minutes += plan_minutes
                block_id = self._resolve_time_block_id(task, idx)
                matched_block_ids.add(block_id)

                focus_info = focus_by_block.get(block_id, {})
                focus_minutes = focus_info.get('duration', 0) or 0
                focus_sessions = focus_info.get('count', 0) or 0

                time_blocks.append({
                    'name': task.get('task') or task.get('name') or f'任务 {idx + 1}',
                    'plan_minutes': plan_minutes,
                    'focus_minutes': focus_minutes,
                    'focus_sessions': focus_sessions
                })

            unmatched_blocks = [
                (block_id, info) for block_id, info in focus_by_block.items()
                if block_id not in matched_block_ids
            ]
            for extra_idx, (block_id, info) in enumerate(unmatched_blocks, start=1):
                time_blocks.append({
                    'name': f'未匹配时间块 #{extra_idx}',
                    'plan_minutes': 0,
                    'focus_minutes': info.get('duration', 0) or 0,
                    'focus_sessions': info.get('count', 0) or 0
                })

            focus_execution_rate = (
                (total_focus_minutes / total_plan_minutes) * 100
                if total_plan_minutes > 0 else 0
            )

            self.review_data = {
                'total_plan_minutes': total_plan_minutes,
                'total_focus_minutes': total_focus_minutes,
                'focus_execution_rate': focus_execution_rate,
                'time_blocks': time_blocks
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

        # 更新总专注时间
        total_focus = self.review_data['total_focus_minutes']
        hours = total_focus // 60
        minutes = total_focus % 60

        if hours > 0:
            self.total_focus_time_label.setText(f"{hours}小时{minutes}分钟")
        else:
            self.total_focus_time_label.setText(f"{minutes}分钟")

        # 清空并重建专注任务列表 (只显示有专注记录的任务)
        self.clear_layout(self.focus_tasks_layout)

        # 筛选有专注记录的任务
        focused_tasks = [
            block for block in self.review_data['time_blocks']
            if block['focus_minutes'] > 0
        ]

        if focused_tasks:
            for block in focused_tasks:
                task_widget = self.create_focus_task_item(block)
                self.focus_tasks_layout.addWidget(task_widget)
        else:
            # 无专注记录时显示提示
            no_data_label = QLabel("今日尚无专注记录")
            no_data_label.setStyleSheet("color: gray; font-style: italic; padding: 10px;")
            no_data_label.setAlignment(Qt.AlignCenter)
            self.focus_tasks_layout.addWidget(no_data_label)

        self.focus_tasks_layout.addStretch()

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

        # 行为识别摘要
        if total_seconds > 0:
            self.behavior_summary_label.setText(f"今日活跃用机：{self.format_duration(total_seconds)}")
            productive_pct = (productive_seconds / total_seconds) * 100 if total_seconds else 0
            leisure_pct = (leisure_seconds / total_seconds) * 100 if total_seconds else 0
            neutral_pct = (neutral_seconds / total_seconds) * 100 if total_seconds else 0
            unknown_pct = max(0.0, 100 - productive_pct - leisure_pct - neutral_pct)

            self.behavior_ratio_bar.setValue(int(round(productive_pct)))
            self.behavior_ratio_bar.setFormat(f"🎯 生产力 {productive_pct:.1f}%")
            self.behavior_ratio_detail_label.setText(
                f"🎯 生产力 {productive_pct:.1f}% | "
                f"🎮 摸鱼 {leisure_pct:.1f}% | "
                f"⚙️ 中性 {neutral_pct:.1f}% | "
                f"❓ 未分类 {unknown_pct:.1f}%"
            )

            # 获取top_apps数据
            top_apps = self.activity_data.get('top_apps', [])
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
                    f"{self.format_duration(top.get('duration', 0))}（{category_cn}）"
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

        # 更新时间显示
        self.total_active_time_label.setText(self.format_duration(total_seconds))
        self.productive_time_label.setText(self.format_duration(productive_seconds))
        self.leisure_time_label.setText(self.format_duration(leisure_seconds))
        self.neutral_time_label.setText(self.format_duration(neutral_seconds))
        self.unknown_time_label.setText(self.format_duration(unknown_seconds))

        # 计算并更新专注时长 (新增)
        try:
            # 从数据库获取今日活动记录
            activity_records = db.get_today_activity_records()
            if activity_records:
                focus_stats = calculate_focus_from_activity_log(activity_records)
                focus_seconds = focus_stats['productive_focus_time']
                self.focus_time_label.setText(self.format_duration(focus_seconds))

                # 如果有专注时段,显示绿色,否则显示灰色
                if focus_seconds > 0:
                    self.focus_time_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
                else:
                    self.focus_time_label.setStyleSheet("color: #999999;")
            else:
                self.focus_time_label.setText("0分钟")
                self.focus_time_label.setStyleSheet("color: #999999;")
        except Exception as e:
            self.logger.warning(f"计算专注时长失败: {e}")
            self.focus_time_label.setText("--")
            self.focus_time_label.setStyleSheet("color: #999999;")

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

    def create_focus_task_item(self, block_data: Dict) -> QWidget:
        """创建专注任务条目 (简洁版)"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Box)
        widget.setStyleSheet("""
            QFrame {
                border: 1px solid #ffcccb;
                border-radius: 5px;
                background-color: #fff5f5;
                padding: 8px;
            }
        """)

        layout = QHBoxLayout(widget)
        layout.setSpacing(12)
        layout.setContentsMargins(8, 5, 8, 5)

        # 火焰图标
        icon_label = QLabel("🔥")
        icon_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(icon_label)

        # 任务名称
        name_label = QLabel(block_data['name'])
        name_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        name_label.setMinimumWidth(120)
        layout.addWidget(name_label)

        # 专注时长
        focus_minutes = block_data['focus_minutes']
        hours = focus_minutes // 60
        minutes = focus_minutes % 60

        if hours > 0:
            time_text = f"{hours}小时{minutes}分钟"
        else:
            time_text = f"{minutes}分钟"

        time_label = QLabel(time_text)
        time_label.setStyleSheet("color: #e74c3c; font-size: 12px; font-weight: bold;")
        time_label.setMinimumWidth(80)
        layout.addWidget(time_label)

        # 专注次数
        sessions = block_data['focus_sessions']
        sessions_label = QLabel(f"共 {sessions} 次")
        sessions_label.setStyleSheet("color: #6c757d; font-size: 11px;")
        layout.addWidget(sessions_label)

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

    def show_activity_settings(self):
        """显示行为识别设置窗口"""
        try:
            from gaiya.ui.activity_settings_window import ActivitySettingsWindow

            # Get main window reference (parent of this dialog)
            main_window = self.parent()
            if main_window:
                activity_settings_window = ActivitySettingsWindow(main_window)
                activity_settings_window.settings_changed.connect(self.on_activity_settings_changed)
                activity_settings_window.exec_()
            else:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "错误", "无法打开行为识别设置窗口")
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            self.logger.error(f"打开行为识别设置窗口失败: {e}", exc_info=True)
            QMessageBox.warning(self, "错误", f"无法打开行为识别设置窗口: {e}")

    def on_activity_settings_changed(self):
        """行为识别设置更改后的回调"""
        self.logger.info("行为识别设置已更改，刷新数据")
        self.load_today_data()

    def export_report(self):
        """导出时间报告"""
        try:
            from PySide6.QtWidgets import QMessageBox
            # 这里可以实现导出为PDF、图片等功能
            QMessageBox.information(self, "提示", "报告导出功能开发中...")
        except Exception as e:
            self.logger.error(f"导出报告失败: {e}")

    def open_statistics_report(self):
        """打开统计报告窗口"""
        try:
            # Get config window (parent of this dialog)
            config_window = self.parent()
            if config_window and hasattr(config_window, 'main_window'):
                # Get main window from config's main_window reference
                main_window = config_window.main_window
                if main_window and hasattr(main_window, 'show_statistics'):
                    # 关闭当前回放窗口和配置窗口
                    self.close()
                    config_window.close()
                    # 打开统计报告窗口 (正确的方法名是 show_statistics)
                    main_window.show_statistics()
                else:
                    from PySide6.QtWidgets import QMessageBox
                    QMessageBox.warning(self, "提示", "无法打开统计报告窗口,请从主界面访问")
            else:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "提示", "无法打开统计报告窗口")
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            self.logger.error(f"打开统计报告窗口失败: {e}", exc_info=True)
            QMessageBox.warning(self, "错误", f"无法打开统计报告窗口: {e}")
