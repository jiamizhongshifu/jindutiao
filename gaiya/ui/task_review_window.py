"""
任务完成回顾窗口

在每日推理完成后显示,允许用户快速确认或修正任务完成度
"""
import logging
from datetime import datetime
from typing import List, Dict, Optional, Callable
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QFrame, QSlider, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

logger = logging.getLogger("gaiya.ui.task_review_window")


class TaskReviewCard(QFrame):
    """单个任务回顾卡片"""

    # 信号:当用户修改完成度时发出
    completion_changed = Signal(str, int)  # (completion_id, new_completion)

    def __init__(self, task_data: Dict, parent=None):
        """
        初始化任务卡片

        Args:
            task_data: 任务完成数据
                {
                    'id': str,
                    'task_name': str,
                    'planned_start_time': str,
                    'planned_end_time': str,
                    'planned_duration_minutes': int,
                    'actual_duration_minutes': int,
                    'completion_percentage': int,
                    'confidence_level': str,
                    'inference_data': str (JSON)
                }
        """
        super().__init__(parent)
        self.task_data = task_data
        self.completion_id = task_data['id']
        self.original_completion = task_data['completion_percentage']
        self.current_completion = self.original_completion

        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(1)

        # 根据置信度设置边框颜色
        confidence = self.task_data['confidence_level']
        if confidence == 'high':
            border_color = '#4CAF50'  # 绿色
        elif confidence == 'medium':
            border_color = '#FFC107'  # 黄色
        elif confidence == 'low':
            border_color = '#FF9800'  # 橙色
        else:
            border_color = '#9E9E9E'  # 灰色

        self.setStyleSheet(f"""
            TaskReviewCard {{
                border: 2px solid {border_color};
                border-radius: 8px;
                background-color: #FFFFFF;
                margin: 4px;
                padding: 8px;
            }}
        """)

        layout = QVBoxLayout(self)

        # 任务标题行
        title_layout = QHBoxLayout()

        # 任务名称
        task_name_label = QLabel(self.task_data['task_name'])
        task_name_font = QFont()
        task_name_font.setPointSize(12)
        task_name_font.setBold(True)
        task_name_label.setFont(task_name_font)
        title_layout.addWidget(task_name_label)

        title_layout.addStretch()

        # 置信度标签
        confidence_label = QLabel(self._get_confidence_text(confidence))
        confidence_label.setStyleSheet(f"""
            QLabel {{
                background-color: {border_color};
                color: white;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 10px;
            }}
        """)
        title_layout.addWidget(confidence_label)

        layout.addLayout(title_layout)

        # 时间信息行
        time_info = QLabel(
            f"计划: {self.task_data['planned_start_time']} - {self.task_data['planned_end_time']} "
            f"({self.task_data['planned_duration_minutes']}分钟) | "
            f"实际: {self.task_data['actual_duration_minutes']}分钟"
        )
        time_info.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(time_info)

        # 完成度调整区域
        completion_layout = QVBoxLayout()

        # 完成度标签和百分比显示
        completion_header = QHBoxLayout()
        completion_header.addWidget(QLabel("完成度:"))

        self.completion_value_label = QLabel(f"{self.current_completion}%")
        completion_value_font = QFont()
        completion_value_font.setPointSize(14)
        completion_value_font.setBold(True)
        self.completion_value_label.setFont(completion_value_font)
        self.completion_value_label.setStyleSheet("color: #2196F3;")
        completion_header.addWidget(self.completion_value_label)

        completion_header.addStretch()
        completion_layout.addLayout(completion_header)

        # 完成度滑块
        self.completion_slider = QSlider(Qt.Horizontal)
        self.completion_slider.setMinimum(0)
        self.completion_slider.setMaximum(100)
        self.completion_slider.setValue(self.current_completion)
        self.completion_slider.setTickPosition(QSlider.TicksBelow)
        self.completion_slider.setTickInterval(10)
        self.completion_slider.valueChanged.connect(self._on_completion_changed)
        completion_layout.addWidget(self.completion_slider)

        # 快捷按钮
        quick_buttons = QHBoxLayout()
        for value in [0, 25, 50, 75, 100]:
            btn = QPushButton(f"{value}%")
            btn.setFixedWidth(50)
            btn.clicked.connect(lambda checked, v=value: self.set_completion(v))
            quick_buttons.addWidget(btn)
        quick_buttons.addStretch()
        completion_layout.addLayout(quick_buttons)

        layout.addLayout(completion_layout)

        # 推理详情(可折叠)
        self.details_visible = False
        self.details_widget = QTextEdit()
        self.details_widget.setReadOnly(True)
        self.details_widget.setMaximumHeight(80)
        self.details_widget.setVisible(False)
        self.details_widget.setPlainText(self._format_inference_details())
        layout.addWidget(self.details_widget)

        # 显示详情按钮
        self.toggle_details_btn = QPushButton("显示详情 ▼")
        self.toggle_details_btn.clicked.connect(self._toggle_details)
        self.toggle_details_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #2196F3;
                text-align: left;
                padding: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                text-decoration: underline;
            }
        """)
        layout.addWidget(self.toggle_details_btn)

    def _get_confidence_text(self, confidence: str) -> str:
        """获取置信度显示文本"""
        mapping = {
            'high': '高置信度',
            'medium': '中等置信度',
            'low': '低置信度',
            'unknown': '未知'
        }
        return mapping.get(confidence, confidence)

    def _format_inference_details(self) -> str:
        """格式化推理详情"""
        try:
            import json
            inference_data = json.loads(self.task_data['inference_data'])

            details = []
            details.append(f"信号数量: {inference_data.get('signal_count', 0)}")
            details.append(f"总权重: {inference_data.get('total_weight', 0):.2f}")

            # 详细信号信息
            signal_details = inference_data.get('details', {})
            if signal_details:
                details.append("\n信号详情:")
                if signal_details.get('focus_duration', 0) > 0:
                    details.append(f"  - 专注时长: {signal_details['focus_duration']}分钟")
                if signal_details.get('primary_apps'):
                    details.append(f"  - 主要应用: {', '.join(signal_details['primary_apps'])}")
                if signal_details.get('time_match_score', 0) > 0:
                    details.append(f"  - 时间匹配: {signal_details['time_match_score']:.0%}")

            return '\n'.join(details)
        except Exception as e:
            logger.warning(f"解析推理数据失败: {e}")
            return "推理详情不可用"

    def _toggle_details(self):
        """切换详情显示"""
        self.details_visible = not self.details_visible
        self.details_widget.setVisible(self.details_visible)

        if self.details_visible:
            self.toggle_details_btn.setText("隐藏详情 ▲")
        else:
            self.toggle_details_btn.setText("显示详情 ▼")

    def _on_completion_changed(self, value: int):
        """完成度滑块变化"""
        self.current_completion = value
        self.completion_value_label.setText(f"{value}%")

        # 高亮显示已修改
        if value != self.original_completion:
            self.completion_value_label.setStyleSheet("color: #FF5722; font-weight: bold;")
        else:
            self.completion_value_label.setStyleSheet("color: #2196F3;")

        # 发出信号
        self.completion_changed.emit(self.completion_id, value)

    def set_completion(self, value: int):
        """设置完成度"""
        self.completion_slider.setValue(value)

    def get_completion(self) -> int:
        """获取当前完成度"""
        return self.current_completion

    def is_modified(self) -> bool:
        """是否已修改"""
        return self.current_completion != self.original_completion


class TaskReviewWindow(QDialog):
    """任务完成回顾窗口"""

    # 信号:当用户完成审查时发出
    review_completed = Signal(list)  # [(completion_id, new_completion, note), ...]

    def __init__(self, date: str, task_completions: List[Dict],
                 on_confirm: Optional[Callable] = None,
                 parent=None):
        """
        初始化回顾窗口

        Args:
            date: 日期 (YYYY-MM-DD)
            task_completions: 任务完成数据列表
            on_confirm: 确认回调函数
            parent: 父窗口
        """
        super().__init__(parent)
        self.date = date
        self.task_completions = task_completions
        self.on_confirm_callback = on_confirm

        # 任务卡片映射
        self.task_cards: Dict[str, TaskReviewCard] = {}

        # 修改记录
        self.modifications: Dict[str, int] = {}  # {completion_id: new_completion}

        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        # 设置窗口标志 - 使用非模态窗口避免事件循环阻塞导致的渲染冲突
        # 添加 Qt.Dialog 标志确保窗口独立显示
        self.setWindowFlags(
            Qt.Dialog |
            Qt.WindowCloseButtonHint |
            Qt.WindowTitleHint |
            Qt.WindowStaysOnTopHint
        )
        # 不使用 ApplicationModal,避免阻塞主窗口事件循环
        # 使用非模态窗口，允许主线程继续处理事件

        self.setWindowTitle(f"任务完成回顾 - {self.date}")
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout(self)

        # 标题区域
        header_layout = QVBoxLayout()

        title = QLabel(f"📊 {self.date} 任务完成情况")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)

        subtitle = QLabel(
            f"共 {len(self.task_completions)} 个任务 | "
            f"请确认或调整AI推理的完成度"
        )
        subtitle.setStyleSheet("color: #666; font-size: 12px;")
        header_layout.addWidget(subtitle)

        layout.addLayout(header_layout)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)

        # 任务列表(可滚动)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # 添加任务卡片
        for task_data in self.task_completions:
            card = TaskReviewCard(task_data)
            card.completion_changed.connect(self._on_task_modified)
            self.task_cards[task_data['id']] = card
            scroll_layout.addWidget(card)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

        # 底部按钮区域
        button_layout = QHBoxLayout()

        # 统计信息
        self.stats_label = QLabel(self._get_stats_text())
        self.stats_label.setStyleSheet("color: #666; font-size: 11px;")
        button_layout.addWidget(self.stats_label)

        button_layout.addStretch()

        # 全部确认按钮
        confirm_all_btn = QPushButton("全部确认")
        confirm_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 24px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        confirm_all_btn.clicked.connect(self.confirm_all)
        button_layout.addWidget(confirm_all_btn)

        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
                color: white;
                border: none;
                padding: 8px 24px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #757575;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _get_stats_text(self) -> str:
        """获取统计信息文本"""
        total = len(self.task_completions)
        modified = len(self.modifications)

        if modified == 0:
            return f"未修改任何任务"
        else:
            return f"已修改 {modified}/{total} 个任务"

    def _on_task_modified(self, completion_id: str, new_completion: int):
        """任务被修改"""
        # 查找原始完成度
        original_completion = None
        for task_data in self.task_completions:
            if task_data['id'] == completion_id:
                original_completion = task_data['completion_percentage']
                break

        # 更新修改记录
        if original_completion is not None:
            if new_completion != original_completion:
                self.modifications[completion_id] = new_completion
            else:
                # 改回原值,移除修改记录
                if completion_id in self.modifications:
                    del self.modifications[completion_id]

        # 更新统计信息
        self.stats_label.setText(self._get_stats_text())

    def confirm_all(self):
        """确认所有任务"""
        # 收集所有修改
        results = []

        for completion_id, card in self.task_cards.items():
            new_completion = card.get_completion()
            original_completion = None

            # 查找原始数据
            for task_data in self.task_completions:
                if task_data['id'] == completion_id:
                    original_completion = task_data['completion_percentage']
                    break

            # 记录所有任务(无论是否修改)
            results.append({
                'completion_id': completion_id,
                'new_completion': new_completion,
                'original_completion': original_completion,
                'is_modified': card.is_modified(),
                'note': ''  # 暂不支持备注
            })

        # 发出信号
        self.review_completed.emit(results)

        # 调用回调
        if self.on_confirm_callback:
            try:
                self.on_confirm_callback(results)
            except Exception as e:
                logger.error(f"确认回调执行失败: {e}", exc_info=True)

        # 关闭窗口
        self.accept()

    @staticmethod
    def show_review(date: str, task_completions: List[Dict],
                    on_confirm: Optional[Callable] = None,
                    parent=None) -> 'TaskReviewWindow':
        """
        显示任务回顾窗口(便捷方法)

        Args:
            date: 日期
            task_completions: 任务完成数据列表
            on_confirm: 确认回调函数
            parent: 父窗口

        Returns:
            TaskReviewWindow实例
        """
        window = TaskReviewWindow(date, task_completions, on_confirm, parent)
        window.show()
        return window
