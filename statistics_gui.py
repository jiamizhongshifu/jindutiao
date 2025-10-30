"""
任务统计报告GUI窗口
显示任务完成情况的可视化统计
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QTabWidget, QTableWidget, QTableWidgetItem,
                               QPushButton, QGroupBox, QScrollArea, QHeaderView,
                               QMessageBox, QFileDialog, QProgressBar)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from statistics_manager import StatisticsManager
from pathlib import Path
import logging


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

    def __init__(self, stats_manager: StatisticsManager, logger: logging.Logger, parent=None):
        super().__init__(parent)
        self.stats_manager = stats_manager
        self.logger = logger
        self.init_ui()
        self.load_statistics()

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle('📊 任务统计报告 - PyDayBar')
        self.setGeometry(100, 100, 900, 700)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 顶部标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel("📊 任务统计报告")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #2196F3;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        # 刷新按钮
        refresh_button = QPushButton("🔄 刷新")
        refresh_button.clicked.connect(self.load_statistics)
        title_layout.addWidget(refresh_button)

        # 导出按钮
        export_button = QPushButton("📥 导出CSV")
        export_button.clicked.connect(self.export_statistics)
        title_layout.addWidget(export_button)

        main_layout.addLayout(title_layout)

        # 标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #E0E0E0;
                background: white;
            }
            QTabBar::tab {
                padding: 10px 20px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #2196F3;
                color: white;
            }
        """)

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
        scroll.setStyleSheet("QScrollArea { border: none; background: #F5F5F5; }")

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # 统计卡片容器
        self.today_cards_layout = QHBoxLayout()
        content_layout.addLayout(self.today_cards_layout)

        # 圆形进度条
        progress_group = QGroupBox("今日完成率")
        progress_layout = QHBoxLayout(progress_group)
        progress_layout.setAlignment(Qt.AlignCenter)

        self.today_circular_progress = CircularProgressWidget(0)
        progress_layout.addWidget(self.today_circular_progress)

        content_layout.addWidget(progress_group)

        # 任务详情表格
        details_group = QGroupBox("今日任务详情")
        details_layout = QVBoxLayout(details_group)

        self.today_table = QTableWidget()
        self.today_table.setColumnCount(5)
        self.today_table.setHorizontalHeaderLabels(['任务名称', '开始时间', '结束时间', '时长(分钟)', '状态'])
        self.today_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.today_table.setAlternatingRowColors(True)
        self.today_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E0E0E0;
                gridline-color: #E0E0E0;
            }
            QTableWidget::item {
                padding: 8px;
            }
        """)

        details_layout.addWidget(self.today_table)
        content_layout.addWidget(details_group)

        content_layout.addStretch()

        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        self.tab_widget.addTab(tab, "📅 今日统计")

    def create_weekly_tab(self):
        """创建本周统计标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)

        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: #F5F5F5; }")

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # 统计卡片
        self.weekly_cards_layout = QHBoxLayout()
        content_layout.addLayout(self.weekly_cards_layout)

        # 周进度条
        progress_group = QGroupBox("本周完成率")
        progress_layout = QHBoxLayout(progress_group)
        progress_layout.setAlignment(Qt.AlignCenter)

        self.weekly_circular_progress = CircularProgressWidget(0, "#FF9800")
        progress_layout.addWidget(self.weekly_circular_progress)

        content_layout.addWidget(progress_group)

        # 每日趋势表格
        trend_group = QGroupBox("每日完成情况")
        trend_layout = QVBoxLayout(trend_group)

        self.weekly_table = QTableWidget()
        self.weekly_table.setColumnCount(6)
        self.weekly_table.setHorizontalHeaderLabels([
            '日期', '星期', '任务数', '完成数', '计划时长(h)', '完成率(%)'
        ])
        self.weekly_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.weekly_table.setAlternatingRowColors(True)

        trend_layout.addWidget(self.weekly_table)
        content_layout.addWidget(trend_group)

        content_layout.addStretch()

        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        self.tab_widget.addTab(tab, "📊 本周统计")

    def create_monthly_tab(self):
        """创建本月统计标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)

        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: #F5F5F5; }")

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # 统计卡片
        self.monthly_cards_layout = QHBoxLayout()
        content_layout.addLayout(self.monthly_cards_layout)

        # 月进度条
        progress_group = QGroupBox("本月完成率")
        progress_layout = QHBoxLayout(progress_group)
        progress_layout.setAlignment(Qt.AlignCenter)

        self.monthly_circular_progress = CircularProgressWidget(0, "#9C27B0")
        progress_layout.addWidget(self.monthly_circular_progress)

        content_layout.addWidget(progress_group)

        # 每日统计表格
        daily_group = QGroupBox("每日统计")
        daily_layout = QVBoxLayout(daily_group)

        self.monthly_table = QTableWidget()
        self.monthly_table.setColumnCount(5)
        self.monthly_table.setHorizontalHeaderLabels([
            '日期', '任务数', '完成数', '计划时长(h)', '完成率(%)'
        ])
        self.monthly_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.monthly_table.setAlternatingRowColors(True)

        daily_layout.addWidget(self.monthly_table)
        content_layout.addWidget(daily_group)

        content_layout.addStretch()

        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        self.tab_widget.addTab(tab, "📈 本月统计")

    def create_tasks_tab(self):
        """创建任务分类统计标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title_label = QLabel("📋 任务分类统计(历史累计)")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # 任务统计表格
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(4)
        self.tasks_table.setHorizontalHeaderLabels([
            '任务名称', '完成次数', '总时长(小时)', '颜色'
        ])
        self.tasks_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tasks_table.setAlternatingRowColors(True)

        layout.addWidget(self.tasks_table)

        self.tab_widget.addTab(tab, "📋 任务分类")

    def load_statistics(self):
        """加载统计数据"""
        try:
            self.logger.info("开始加载统计数据...")

            # 加载今日统计
            self.load_today_statistics()

            # 加载本周统计
            self.load_weekly_statistics()

            # 加载本月统计
            self.load_monthly_statistics()

            # 加载任务分类统计
            self.load_task_statistics()

            self.logger.info("统计数据加载完成")

        except Exception as e:
            self.logger.error(f"加载统计数据失败: {e}", exc_info=True)
            QMessageBox.warning(self, "错误", f"加载统计数据失败:\n{str(e)}")

    def load_today_statistics(self):
        """加载今日统计"""
        summary = self.stats_manager.get_today_summary()

        # 清空旧卡片
        self.clear_layout(self.today_cards_layout)

        # 创建统计卡片
        total_card = StatCard("总任务数", str(summary['total_tasks']), "📝", "#2196F3")
        self.today_cards_layout.addWidget(total_card)

        completed_card = StatCard("已完成", str(summary['completed_tasks']), "✅", "#4CAF50")
        self.today_cards_layout.addWidget(completed_card)

        in_progress_card = StatCard("进行中", str(summary['in_progress_tasks']), "⏳", "#FF9800")
        self.today_cards_layout.addWidget(in_progress_card)

        not_started_card = StatCard("未开始", str(summary['not_started_tasks']), "⏰", "#9E9E9E")
        self.today_cards_layout.addWidget(not_started_card)

        # 更新圆形进度条
        self.today_circular_progress.set_percentage(summary['completion_rate'])

        # 加载今日任务详情
        today_record = self.stats_manager.statistics["daily_records"].get(
            self.stats_manager.current_date, {}
        )
        tasks = today_record.get("tasks", {})

        self.today_table.setRowCount(len(tasks))
        for row, (task_name, task_info) in enumerate(tasks.items()):
            duration = self.stats_manager._calculate_duration(task_info['start'], task_info['end'])

            # 任务名称(带颜色标记)
            name_item = QTableWidgetItem(f"● {task_name}")
            name_item.setForeground(QColor(task_info['color']))
            self.today_table.setItem(row, 0, name_item)

            # 时间信息
            self.today_table.setItem(row, 1, QTableWidgetItem(task_info['start']))
            self.today_table.setItem(row, 2, QTableWidgetItem(task_info['end']))
            self.today_table.setItem(row, 3, QTableWidgetItem(str(duration)))

            # 状态
            status_text = {
                "completed": "✅ 已完成",
                "in_progress": "⏳ 进行中",
                "not_started": "⏰ 未开始"
            }.get(task_info['status'], task_info['status'])
            self.today_table.setItem(row, 4, QTableWidgetItem(status_text))

    def load_weekly_statistics(self):
        """加载本周统计"""
        summary = self.stats_manager.get_weekly_summary()

        # 清空旧卡片
        self.clear_layout(self.weekly_cards_layout)

        # 创建统计卡片
        total_card = StatCard("总任务数", str(summary['total_tasks']), "📝", "#2196F3")
        self.weekly_cards_layout.addWidget(total_card)

        completed_card = StatCard("已完成", str(summary['completed_tasks']), "✅", "#4CAF50")
        self.weekly_cards_layout.addWidget(completed_card)

        hours_card = StatCard(
            "完成时长",
            f"{summary['total_completed_minutes'] / 60:.1f}h",
            "⏱️",
            "#FF9800"
        )
        self.weekly_cards_layout.addWidget(hours_card)

        # 更新圆形进度条
        self.weekly_circular_progress.set_percentage(summary['completion_rate'])

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

        # 清空旧卡片
        self.clear_layout(self.monthly_cards_layout)

        # 创建统计卡片
        total_card = StatCard("总任务数", str(summary['total_tasks']), "📝", "#2196F3")
        self.monthly_cards_layout.addWidget(total_card)

        completed_card = StatCard("已完成", str(summary['completed_tasks']), "✅", "#4CAF50")
        self.monthly_cards_layout.addWidget(completed_card)

        hours_card = StatCard(
            "完成时长",
            f"{summary['total_completed_minutes'] / 60:.1f}h",
            "⏱️",
            "#9C27B0"
        )
        self.monthly_cards_layout.addWidget(hours_card)

        # 更新圆形进度条
        self.monthly_circular_progress.set_percentage(summary['completion_rate'])

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
                "导出统计数据",
                "statistics_export.csv",
                "CSV文件 (*.csv)"
            )

            if file_path:
                success = self.stats_manager.export_to_csv(Path(file_path))
                if success:
                    QMessageBox.information(
                        self,
                        "导出成功",
                        f"统计数据已导出到:\n{file_path}"
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "导出失败",
                        "导出统计数据失败,请查看日志了解详情"
                    )

        except Exception as e:
            self.logger.error(f"导出统计数据失败: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "错误",
                f"导出失败:\n{str(e)}"
            )

    def closeEvent(self, event):
        """窗口关闭事件"""
        self.closed.emit()
        super().closeEvent(event)
