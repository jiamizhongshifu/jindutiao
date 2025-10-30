# -*- coding: utf-8 -*-
"""
可视化时间轴编辑器
允许通过拖拽色块边缘来调整任务时长
"""

from PySide6.QtWidgets import QWidget, QToolTip
from PySide6.QtCore import Qt, QRectF, Signal, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QCursor


class TimelineEditor(QWidget):
    """可视化时间轴编辑器组件"""

    # 信号：任务时间被修改 (task_index, new_start_minutes, new_end_minutes)
    task_time_changed = Signal(int, int, int)

    # 最小任务时长（分钟）
    MIN_TASK_DURATION = 15

    # 边缘检测宽度（像素）
    EDGE_DETECT_WIDTH = 8

    def __init__(self, parent=None):
        super().__init__(parent)

        self.tasks = []  # 任务列表: [{"start": "HH:MM", "end": "HH:MM", "task": "name", "color": "#RRGGBB"}]
        self.task_rects = []  # 任务矩形位置缓存

        # 拖拽状态
        self.dragging = False
        self.drag_task_index = -1  # 正在拖拽的任务索引
        self.drag_edge = None  # 'left' or 'right'
        self.drag_start_x = 0
        self.drag_start_minutes = 0  # 拖拽开始时的分钟数

        # 悬停状态
        self.hover_task_index = -1
        self.hover_edge = None

        # 设置最小高度
        self.setMinimumHeight(100)
        self.setMaximumHeight(100)

        # 启用鼠标跟踪
        self.setMouseTracking(True)

        # 设置样式
        self.setStyleSheet("background-color: #2C2C2C; border: 2px solid #444; border-radius: 5px;")

    def set_tasks(self, tasks):
        """设置任务列表"""
        self.tasks = tasks.copy() if tasks else []
        self.calculate_task_rects()
        self.update()

    def calculate_task_rects(self):
        """计算所有任务的矩形位置（紧凑模式）"""
        self.task_rects = []

        if not self.tasks:
            return

        # 计算总时长
        total_minutes = 0
        for task in self.tasks:
            start_min = self.time_to_minutes(task['start'])
            end_min = self.time_to_minutes(task['end'])
            duration = end_min - start_min
            if duration < 0:  # 跨午夜
                duration += 1440
            total_minutes += duration

        if total_minutes == 0:
            return

        # 可用宽度（留出边距）
        margin = 10
        available_width = self.width() - 2 * margin
        height = self.height()

        # 计算每个任务的矩形
        current_x = margin
        bar_top = 20  # 顶部留空间显示时间文字
        bar_height = height - bar_top - 10

        for task in self.tasks:
            start_min = self.time_to_minutes(task['start'])
            end_min = self.time_to_minutes(task['end'])
            duration = end_min - start_min
            if duration < 0:
                duration += 1440

            # 按比例计算宽度
            width = (duration / total_minutes) * available_width

            rect = QRectF(current_x, bar_top, width, bar_height)
            self.task_rects.append({
                'rect': rect,
                'task': task,
                'duration': duration
            })

            current_x += width

    def time_to_minutes(self, time_str):
        """将 HH:MM 转换为分钟数"""
        try:
            hours, minutes = map(int, time_str.split(':'))
            if hours == 24 and minutes == 0:
                return 1440
            return hours * 60 + minutes
        except:
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
        """绘制时间轴"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self.task_rects:
            # 显示提示文字
            painter.setPen(QColor("#999"))
            painter.setFont(QFont("Arial", 12))
            painter.drawText(self.rect(), Qt.AlignCenter, "暂无任务，请在下方添加")
            return

        # 绘制任务色块
        for i, item in enumerate(self.task_rects):
            rect = item['rect']
            task = item['task']
            color = QColor(task['color'])

            # 如果正在拖拽或悬停，高亮显示
            if i == self.hover_task_index or i == self.drag_task_index:
                painter.fillRect(rect, color.lighter(120))

                # 高亮边缘
                if self.hover_edge == 'left' or (self.dragging and self.drag_edge == 'left'):
                    edge_rect = QRectF(rect.left(), rect.top(), 3, rect.height())
                    painter.fillRect(edge_rect, QColor("#FFD700"))  # 金色
                elif self.hover_edge == 'right' or (self.dragging and self.drag_edge == 'right'):
                    edge_rect = QRectF(rect.right() - 3, rect.top(), 3, rect.height())
                    painter.fillRect(edge_rect, QColor("#FFD700"))
            else:
                painter.fillRect(rect, color)

            # 绘制任务名（如果宽度足够）
            if rect.width() > 60:
                painter.setPen(QColor("#FFF"))
                painter.setFont(QFont("Microsoft YaHei", 9, QFont.Bold))
                text_rect = rect.adjusted(5, 0, -5, 0)
                painter.drawText(text_rect, Qt.AlignCenter, task['task'])

            # 绘制边框
            painter.setPen(QPen(QColor("#333"), 1))
            painter.drawRect(rect)

        # 如果正在拖拽，显示时间提示
        if self.dragging and 0 <= self.drag_task_index < len(self.tasks):
            task = self.tasks[self.drag_task_index]
            start_time = task['start']
            end_time = task['end']

            # 在色块上方显示时间
            rect = self.task_rects[self.drag_task_index]['rect']
            painter.setPen(QColor("#FFD700"))
            painter.setFont(QFont("Arial", 10, QFont.Bold))
            time_text = f"{start_time} - {end_time}"
            text_rect = QRectF(rect.left(), 2, rect.width(), 18)
            painter.drawText(text_rect, Qt.AlignCenter, time_text)

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            pos = event.position()

            # 检查是否点击在任务边缘
            for i, item in enumerate(self.task_rects):
                rect = item['rect']

                # 检测左边缘
                if abs(pos.x() - rect.left()) <= self.EDGE_DETECT_WIDTH and rect.top() <= pos.y() <= rect.bottom():
                    self.dragging = True
                    self.drag_task_index = i
                    self.drag_edge = 'left'
                    self.drag_start_x = pos.x()
                    self.drag_start_minutes = self.time_to_minutes(self.tasks[i]['start'])
                    return

                # 检测右边缘
                if abs(pos.x() - rect.right()) <= self.EDGE_DETECT_WIDTH and rect.top() <= pos.y() <= rect.bottom():
                    self.dragging = True
                    self.drag_task_index = i
                    self.drag_edge = 'right'
                    self.drag_start_x = pos.x()
                    self.drag_start_minutes = self.time_to_minutes(self.tasks[i]['end'])
                    return

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        pos = event.position()

        if self.dragging:
            # 正在拖拽
            self.handle_drag(pos)
        else:
            # 更新悬停状态
            self.update_hover_state(pos)

    def handle_drag(self, pos):
        """处理拖拽"""
        if self.drag_task_index < 0 or self.drag_task_index >= len(self.tasks):
            return

        # 计算拖拽的像素差
        delta_x = pos.x() - self.drag_start_x

        # 计算总宽度和总时长
        total_minutes = sum(item['duration'] for item in self.task_rects)
        available_width = self.width() - 20

        if available_width <= 0 or total_minutes <= 0:
            return

        # 将像素转换为分钟
        minutes_per_pixel = total_minutes / available_width
        delta_minutes = int(delta_x * minutes_per_pixel)

        if self.drag_edge == 'right':
            # 拖动右边缘：调整当前任务的结束时间
            current_task = self.tasks[self.drag_task_index]
            start_min = self.time_to_minutes(current_task['start'])
            new_end_min = self.drag_start_minutes + delta_minutes

            # 限制最小时长
            if new_end_min - start_min < self.MIN_TASK_DURATION:
                new_end_min = start_min + self.MIN_TASK_DURATION

            # 如果有下一个任务，确保不会让下一个任务小于最小时长
            if self.drag_task_index < len(self.tasks) - 1:
                next_task = self.tasks[self.drag_task_index + 1]
                next_end_min = self.time_to_minutes(next_task['end'])

                # 下一个任务的最小开始时间 = 结束时间 - 最小时长
                min_next_start = next_end_min - self.MIN_TASK_DURATION

                if new_end_min > min_next_start:
                    new_end_min = min_next_start

            # 更新当前任务和下一个任务
            current_task['end'] = self.minutes_to_time(new_end_min)

            if self.drag_task_index < len(self.tasks) - 1:
                next_task = self.tasks[self.drag_task_index + 1]
                next_task['start'] = self.minutes_to_time(new_end_min)

        elif self.drag_edge == 'left':
            # 拖动左边缘：调整当前任务的开始时间
            current_task = self.tasks[self.drag_task_index]
            end_min = self.time_to_minutes(current_task['end'])
            new_start_min = self.drag_start_minutes + delta_minutes

            # 限制最小时长
            if end_min - new_start_min < self.MIN_TASK_DURATION:
                new_start_min = end_min - self.MIN_TASK_DURATION

            # 如果有上一个任务，确保不会让上一个任务小于最小时长
            if self.drag_task_index > 0:
                prev_task = self.tasks[self.drag_task_index - 1]
                prev_start_min = self.time_to_minutes(prev_task['start'])

                # 上一个任务的最大结束时间 = 开始时间 + 最小时长
                max_prev_end = prev_start_min + self.MIN_TASK_DURATION

                if new_start_min < max_prev_end:
                    new_start_min = max_prev_end

            # 更新当前任务和上一个任务
            current_task['start'] = self.minutes_to_time(new_start_min)

            if self.drag_task_index > 0:
                prev_task = self.tasks[self.drag_task_index - 1]
                prev_task['end'] = self.minutes_to_time(new_start_min)

        # 重新计算矩形并刷新
        self.calculate_task_rects()
        self.update()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton and self.dragging:
            # 发送信号通知任务时间已改变
            if 0 <= self.drag_task_index < len(self.tasks):
                task = self.tasks[self.drag_task_index]
                start_min = self.time_to_minutes(task['start'])
                end_min = self.time_to_minutes(task['end'])
                self.task_time_changed.emit(self.drag_task_index, start_min, end_min)

            self.dragging = False
            self.drag_task_index = -1
            self.drag_edge = None
            self.update()

    def update_hover_state(self, pos):
        """更新悬停状态"""
        old_hover_task = self.hover_task_index
        old_hover_edge = self.hover_edge

        self.hover_task_index = -1
        self.hover_edge = None

        # 检查是否悬停在任务上
        for i, item in enumerate(self.task_rects):
            rect = item['rect']

            if rect.contains(pos):
                self.hover_task_index = i

                # 检测是否在边缘
                if abs(pos.x() - rect.left()) <= self.EDGE_DETECT_WIDTH:
                    self.hover_edge = 'left'
                    self.setCursor(Qt.SizeHorCursor)
                elif abs(pos.x() - rect.right()) <= self.EDGE_DETECT_WIDTH:
                    self.hover_edge = 'right'
                    self.setCursor(Qt.SizeHorCursor)
                else:
                    self.setCursor(Qt.ArrowCursor)

                # 显示工具提示
                task = item['task']
                tooltip = f"{task['task']}\n{task['start']} - {task['end']}"
                QToolTip.showText(self.mapToGlobal(pos.toPoint()), tooltip, self)
                break
        else:
            self.setCursor(Qt.ArrowCursor)

        # 如果悬停状态改变，刷新
        if old_hover_task != self.hover_task_index or old_hover_edge != self.hover_edge:
            self.update()

    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.hover_task_index = -1
        self.hover_edge = None
        self.setCursor(Qt.ArrowCursor)
        self.update()

    def resizeEvent(self, event):
        """窗口大小改变事件"""
        self.calculate_task_rects()
        self.update()
