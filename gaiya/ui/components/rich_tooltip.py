"""Rich Tooltip Component for Task Hover Display"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QPainter, QColor, QPainterPath
from datetime import datetime


class RichToolTip(QWidget):
    """富文本任务悬停卡片

    Features:
    - Emoji + task name display
    - Time range and duration
    - Task description
    - Optional progress bar
    - Fade-in/fade-out animation
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Window setup
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(280)  # 固定宽度,高度自适应内容

        # Animation
        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_animation.setDuration(200)
        self.opacity_animation.setEasingCurve(QEasingCurve.OutCubic)

        # Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(8)

        # Title label (emoji + task name)
        self.title_label = QLabel()
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #333;
            }
        """)
        self.title_label.setWordWrap(True)

        # Time label
        self.time_label = QLabel()
        self.time_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #666;
            }
        """)

        # Description label
        self.desc_label = QLabel()
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #888;
                line-height: 1.4;
            }
        """)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 3px;
                background-color: #E0E0E0;
            }
            QProgressBar::chunk {
                border-radius: 3px;
                background-color: #4CAF50;
            }
        """)

        # Add widgets to layout
        self.main_layout.addWidget(self.title_label)
        self.main_layout.addWidget(self.time_label)
        self.main_layout.addWidget(self.desc_label)
        self.main_layout.addWidget(self.progress_bar)

        # Hide initially
        self.hide()

    def set_task(self, task: dict):
        """更新显示的任务信息

        Args:
            task: Task dictionary with keys:
                - task: Task name
                - emoji: Optional emoji icon
                - start: Start time (HH:MM)
                - end: End time (HH:MM)
                - description: Optional task description
                - progress: Optional progress value (0-100)
                - color: Task color for progress bar
        """
        # Title: emoji + task name
        emoji = task.get('emoji', '')
        task_name = task.get('task', '')
        title_text = f"{emoji} {task_name}" if emoji else task_name
        self.title_label.setText(title_text)

        # Time: start - end (duration)
        start = task.get('start', '')
        end = task.get('end', '')
        duration_minutes = self._calculate_duration(start, end)
        time_text = f"⏰ {start} - {end} ({duration_minutes}分钟)"
        self.time_label.setText(time_text)

        # Description
        description = task.get('description', '')
        if description:
            self.desc_label.setText(description)
            self.desc_label.show()
        else:
            self.desc_label.hide()

        # Progress bar
        progress = task.get('progress', None)
        if progress is not None:
            self.progress_bar.setValue(progress)
            # Update progress bar color based on task color
            task_color = task.get('color', '#4CAF50')
            self.progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: none;
                    border-radius: 3px;
                    background-color: #E0E0E0;
                }}
                QProgressBar::chunk {{
                    border-radius: 3px;
                    background-color: {task_color};
                }}
            """)
            self.progress_bar.show()
        else:
            self.progress_bar.hide()

        # Adjust size to content
        self.adjustSize()

    def _calculate_duration(self, start: str, end: str) -> int:
        """计算任务时长(分钟)

        Args:
            start: Start time (HH:MM)
            end: End time (HH:MM)

        Returns:
            Duration in minutes
        """
        try:
            # Handle 23:59 as end of day
            if end == "23:59":
                end = "24:00"

            start_parts = start.split(':')
            end_parts = end.split(':')

            start_minutes = int(start_parts[0]) * 60 + int(start_parts[1])
            end_minutes = int(end_parts[0]) * 60 + int(end_parts[1])

            # Handle overnight tasks
            if end_minutes < start_minutes:
                end_minutes += 24 * 60

            return end_minutes - start_minutes
        except (ValueError, IndexError):
            return 0

    def show_animated(self, position=None):
        """带淡入动画显示

        Args:
            position: Optional QPoint for tooltip position
        """
        if position:
            self.move(position)

        self.setWindowOpacity(0.0)
        self.show()

        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(1.0)
        self.opacity_animation.start()

    def hide_animated(self):
        """带淡出动画隐藏"""
        self.opacity_animation.setStartValue(1.0)
        self.opacity_animation.setEndValue(0.0)

        # Hide widget after animation completes
        self.opacity_animation.finished.connect(self.hide)
        self.opacity_animation.start()

    def paintEvent(self, event):
        """绘制带圆角和阴影的背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw shadow
        shadow_rect = self.rect().adjusted(2, 2, -2, -2)
        shadow_path = QPainterPath()
        shadow_path.addRoundedRect(shadow_rect.x(), shadow_rect.y(),
                                   shadow_rect.width(), shadow_rect.height(), 8, 8)
        painter.fillPath(shadow_path, QColor(0, 0, 0, 30))

        # Draw background
        bg_rect = self.rect().adjusted(0, 0, -4, -4)
        bg_path = QPainterPath()
        bg_path.addRoundedRect(bg_rect.x(), bg_rect.y(),
                              bg_rect.width(), bg_rect.height(), 8, 8)
        painter.fillPath(bg_path, QColor(255, 255, 255, 250))

        # Draw border
        painter.setPen(QColor(200, 200, 200, 100))
        painter.drawPath(bg_path)
