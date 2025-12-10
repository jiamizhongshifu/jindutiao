"""迷你进度条预览组件 - 用于模板预览"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, QTime
from PySide6.QtGui import QPainter, QColor, QFont, QPen
import json
from pathlib import Path
from datetime import datetime


class MiniProgressBarPreview(QWidget):
    """迷你进度条预览组件

    用于在SetupWizard的模板选择页面实时预览模板效果。
    显示简化版本的进度条,包含任务块和时间标记。

    Args:
        template_id: 模板ID(如 'work_weekday', 'student', 'freelancer')
        parent: 父级widget
    """

    def __init__(self, template_id: str = None, parent=None):
        super().__init__(parent)
        self._template_id = template_id
        self._tasks = []
        self._current_time_percent = 0.0

        # 模拟当前时间(用于演示)
        self._demo_time = QTime.currentTime()

        self.setFixedSize(400, 80)
        self.setup_ui()

        # 启动时间更新定时器
        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)  # 每秒更新

        # 加载模板(如果提供)
        if template_id:
            self.load_template(template_id)

    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # 标题标签
        self.title_label = QLabel("模板预览")
        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        layout.addStretch()

    def load_template(self, template_id: str):
        """加载指定模板的任务数据

        Args:
            template_id: 模板ID
        """
        self._template_id = template_id

        # 获取模板文件路径
        template_path = self.get_template_path(template_id)

        if not template_path.exists():
            print(f"模板文件不存在: {template_path}")
            return

        # 读取模板数据
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)

            # 模板文件是一个任务数组,不是对象
            if isinstance(template_data, list):
                self._tasks = template_data
            else:
                # 如果是对象,尝试获取tasks字段
                self._tasks = template_data.get('tasks', [])

            self.update()

        except Exception as e:
            print(f"加载模板失败: {e}")

    def get_template_path(self, template_id: str) -> Path:
        """获取模板文件路径

        Args:
            template_id: 模板ID(如 'work_weekday' 或 'template_workday')

        Returns:
            模板文件的Path对象
        """
        # ID映射表:SetupWizard使用的简化ID → templates_config.json中的ID
        id_mapping = {
            'work_weekday': 'template_workday',
            'student': 'template_student',
            'freelancer': 'template_freelancer'
        }

        # 转换为标准ID
        standard_id = id_mapping.get(template_id, template_id)

        # 文件名格式: tasks_template_{name}.json
        # 从 template_workday → workday
        if standard_id.startswith('template_'):
            template_name = standard_id[9:]  # 移除 'template_' 前缀
        else:
            template_name = standard_id

        # 获取项目根目录
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent.parent

        return project_root / f'tasks_template_{template_name}.json'

    def update_time(self):
        """更新当前时间百分比"""
        now = QTime.currentTime()
        seconds_since_midnight = now.hour() * 3600 + now.minute() * 60 + now.second()
        total_seconds_in_day = 24 * 3600
        self._current_time_percent = seconds_since_midnight / total_seconds_in_day
        self.update()

    def paintEvent(self, event):
        """绘制预览进度条"""
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 进度条绘制区域(留出上下边距)
        bar_rect = self.rect().adjusted(10, 30, -10, -10)
        bar_height = 20

        # 绘制背景
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#F3F4F6"))
        painter.drawRoundedRect(bar_rect.x(), bar_rect.y(), bar_rect.width(), bar_height, 4, 4)

        # 绘制任务块
        if self._tasks:
            for task in self._tasks:
                # 兼容两种字段名格式
                start_time = self.parse_time(task.get('start', task.get('start_time', '00:00')))
                end_time = self.parse_time(task.get('end', task.get('end_time', '23:59')))

                start_percent = self.time_to_percent(start_time)
                end_percent = self.time_to_percent(end_time)

                # 计算任务块的x坐标和宽度
                task_x = bar_rect.x() + int(bar_rect.width() * start_percent)
                task_width = int(bar_rect.width() * (end_percent - start_percent))

                # 任务颜色
                color_str = task.get('color', '#3B82F6')
                task_color = QColor(color_str)

                painter.setBrush(task_color)
                painter.drawRoundedRect(task_x, bar_rect.y(), task_width, bar_height, 4, 4)

                # 绘制任务名称(如果空间足够)
                if task_width > 40:
                    painter.setPen(QColor("#FFFFFF"))
                    # 兼容两种字段名格式
                    task_name = task.get('task', task.get('name', ''))
                    task_rect = painter.boundingRect(
                        task_x, bar_rect.y(), task_width, bar_height,
                        Qt.AlignmentFlag.AlignCenter, task_name
                    )

                    # 简化名称以适应空间
                    if task_rect.width() > task_width - 10:
                        task_name = task_name[:3] + '...' if len(task_name) > 3 else task_name

                    painter.drawText(
                        task_x, bar_rect.y(), task_width, bar_height,
                        Qt.AlignmentFlag.AlignCenter, task_name
                    )

        # 绘制当前时间标记(红色线条)
        painter.setPen(QPen(QColor("#EF4444"), 2))
        time_x = bar_rect.x() + int(bar_rect.width() * self._current_time_percent)
        painter.drawLine(time_x, bar_rect.y() - 5, time_x, bar_rect.y() + bar_height + 5)

        # 绘制时间文字
        painter.setPen(QColor("#6B7280"))
        time_font = QFont()
        time_font.setPointSize(8)
        painter.setFont(time_font)

        # 起始时间
        painter.drawText(bar_rect.x(), bar_rect.y() + bar_height + 15, "00:00")

        # 结束时间
        end_time_text = "24:00"
        end_text_rect = painter.fontMetrics().boundingRect(end_time_text)
        painter.drawText(
            bar_rect.x() + bar_rect.width() - end_text_rect.width(),
            bar_rect.y() + bar_height + 15,
            end_time_text
        )

    def parse_time(self, time_str: str) -> QTime:
        """解析时间字符串

        Args:
            time_str: 时间字符串,格式为 'HH:MM' 或 'HH:MM:SS'

        Returns:
            QTime对象
        """
        parts = time_str.split(':')
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        second = int(parts[2]) if len(parts) > 2 else 0

        return QTime(hour, minute, second)

    def time_to_percent(self, time: QTime) -> float:
        """将时间转换为百分比

        Args:
            time: QTime对象

        Returns:
            0.0-1.0之间的百分比
        """
        seconds = time.hour() * 3600 + time.minute() * 60 + time.second()
        return seconds / (24 * 3600)

    def set_template(self, template_id: str):
        """设置要预览的模板

        Args:
            template_id: 模板ID
        """
        self.load_template(template_id)


if __name__ == '__main__':
    """测试代码"""
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # 测试预览组件
    preview = MiniProgressBarPreview(template_id='work_weekday')
    preview.show()

    sys.exit(app.exec())
