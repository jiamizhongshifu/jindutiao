"""
番茄钟面板和设置对话框
"""
import sys
import json
from pathlib import Path
from PySide6.QtWidgets import (QWidget, QDialog, QSystemTrayIcon, QMessageBox,
                                QFormLayout, QSpinBox, QPushButton, QHBoxLayout, QVBoxLayout)
from PySide6.QtCore import Qt, QRectF, QTimer, QPoint, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QCursor
from pydaybar.core.pomodoro_state import PomodoroState
from pydaybar.core.theme_manager import ThemeManager


class PomodoroSettingsDialog(QDialog):
    """番茄钟设置对话框"""

    settings_saved = Signal(dict)  # 设置保存信号,传递新配置

    def __init__(self, config, logger, parent=None):
        super().__init__(parent)
        self.config = config.copy()  # 复制配置,避免直接修改
        self.logger = logger
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle('番茄钟设置')
        self.setFixedSize(350, 250)

        # 主布局
        layout = QVBoxLayout(self)

        # 表单布局
        form_layout = QFormLayout()

        # 获取当前番茄钟配置
        pomodoro_config = self.config.get('pomodoro', {})

        # 工作时长(分钟)
        self.work_duration_input = QSpinBox()
        self.work_duration_input.setRange(1, 120)
        self.work_duration_input.setValue(pomodoro_config.get('work_duration', 1500) // 60)
        self.work_duration_input.setSuffix(' 分钟')
        form_layout.addRow('工作时长:', self.work_duration_input)

        # 短休息时长(分钟)
        self.short_break_input = QSpinBox()
        self.short_break_input.setRange(1, 60)
        self.short_break_input.setValue(pomodoro_config.get('short_break', 300) // 60)
        self.short_break_input.setSuffix(' 分钟')
        form_layout.addRow('短休息时长:', self.short_break_input)

        # 长休息时长(分钟)
        self.long_break_input = QSpinBox()
        self.long_break_input.setRange(1, 120)
        self.long_break_input.setValue(pomodoro_config.get('long_break', 900) // 60)
        self.long_break_input.setSuffix(' 分钟')
        form_layout.addRow('长休息时长:', self.long_break_input)

        # 长休息间隔(番茄钟数量)
        self.long_break_interval_input = QSpinBox()
        self.long_break_interval_input.setRange(1, 10)
        self.long_break_interval_input.setValue(pomodoro_config.get('long_break_interval', 4))
        self.long_break_interval_input.setSuffix(' 个番茄钟')
        form_layout.addRow('长休息间隔:', self.long_break_interval_input)

        layout.addLayout(form_layout)

        # 按钮布局
        button_layout = QHBoxLayout()

        # 保存按钮
        save_button = QPushButton('保存')
        save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(save_button)

        # 取消按钮
        cancel_button = QPushButton('取消')
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

    def save_settings(self):
        """保存设置到配置文件"""
        try:
            # 更新配置对象
            if 'pomodoro' not in self.config:
                self.config['pomodoro'] = {}

            self.config['pomodoro']['work_duration'] = self.work_duration_input.value() * 60
            self.config['pomodoro']['short_break'] = self.short_break_input.value() * 60
            self.config['pomodoro']['long_break'] = self.long_break_input.value() * 60
            self.config['pomodoro']['long_break_interval'] = self.long_break_interval_input.value()

            # 保存到文件
            if getattr(sys, 'frozen', False):
                # 打包后的 exe
                config_file = Path(sys.executable).parent / 'config.json'
            else:
                # 开发环境
                config_file = Path(__file__).parent.parent.parent / 'config.json'

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)

            self.logger.info("番茄钟设置已保存")

            # 发送信号通知配置已更新
            self.settings_saved.emit(self.config)

            # 关闭对话框
            self.accept()

        except Exception as e:
            self.logger.error(f"保存番茄钟设置失败: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "错误",
                f"保存设置失败:\n{str(e)}"
            )


class PomodoroPanel(QWidget):
    """番茄钟面板窗口"""

    closed = Signal()  # 关闭信号

    def __init__(self, config, tray_icon, logger, parent=None):
        super().__init__(parent)
        self.config = config
        self.tray_icon = tray_icon
        self.logger = logger

        # 番茄钟配置
        pomodoro_config = self.config.get('pomodoro', {})
        self.work_duration = pomodoro_config.get('work_duration', 1500)  # 25分钟
        self.short_break = pomodoro_config.get('short_break', 300)       # 5分钟
        self.long_break = pomodoro_config.get('long_break', 900)         # 15分钟
        self.long_break_interval = pomodoro_config.get('long_break_interval', 4)  # 每4个番茄钟

        # 状态变量
        self.state = PomodoroState.IDLE
        self.time_remaining = self.work_duration  # 剩余秒数
        self.pomodoro_count = 0  # 完成的番茄钟数量

        # 悬停状态(用于按钮高亮)
        self.hovered_button = None  # 'play_pause', 'settings' 或 'close'

        # 拖拽相关变量
        self.dragging = False
        self.drag_position = QPoint()

        # 初始化UI(先初始化UI组件)
        self.init_ui()

        # 倒计时定时器
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)

        # 初始化主题管理器(UI初始化完成后再注册)
        try:
            if getattr(sys, 'frozen', False):
                app_dir = Path(sys.executable).parent
            else:
                app_dir = Path(__file__).parent.parent.parent
            self.theme_manager = ThemeManager(app_dir)
            # 注册时不立即应用主题(避免UI未就绪时调用)
            self.theme_manager.register_ui_component(self, apply_immediately=False)
            self.theme_manager.theme_changed.connect(self.apply_theme)
            # 使用QTimer延迟应用主题,确保UI完全就绪
            QTimer.singleShot(100, self.apply_theme)
        except Exception as e:
            self.logger.warning(f"主题管理器初始化失败: {e}")
            self.theme_manager = None

        self.logger.info("番茄钟面板创建成功")

    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口属性
        self.setWindowTitle('番茄钟')

        # 窗口标志:无边框,始终置顶,不接受焦点
        flags = (
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool  # 不在任务栏显示
        )
        self.setWindowFlags(flags)

        # 设置背景透明
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 启用鼠标追踪(用于按钮悬停效果)
        self.setMouseTracking(True)

        # 设置固定大小
        self.setFixedSize(280, 50)

    def position_above_progress_bar(self, progress_bar_widget):
        """将番茄钟面板定位在进度条上方

        Args:
            progress_bar_widget: TimeProgressBar 实例
        """
        # 获取进度条的几何信息
        bar_geometry = progress_bar_widget.geometry()

        # 计算面板位置(居中,在进度条上方10像素)
        panel_x = bar_geometry.x() + (bar_geometry.width() - self.width()) // 2
        panel_y = bar_geometry.y() - self.height() - 10

        self.move(panel_x, panel_y)
        self.logger.info(f"番茄钟面板定位: x={panel_x}, y={panel_y}")

    def start_work(self):
        """开始工作番茄钟"""
        self.state = PomodoroState.WORK
        self.time_remaining = self.work_duration
        self.countdown_timer.start(1000)  # 每秒更新一次
        self.update()
        self.logger.info("番茄钟开始:工作模式")

    def start_short_break(self):
        """开始短休息"""
        self.state = PomodoroState.SHORT_BREAK
        self.time_remaining = self.short_break
        self.countdown_timer.start(1000)
        self.update()
        self.logger.info("番茄钟开始:短休息")

    def start_long_break(self):
        """开始长休息"""
        self.state = PomodoroState.LONG_BREAK
        self.time_remaining = self.long_break
        self.countdown_timer.start(1000)
        self.update()
        self.logger.info("番茄钟开始:长休息")

    def toggle_pause(self):
        """切换暂停/继续"""
        if self.state == PomodoroState.IDLE:
            # 如果是空闲状态,开始工作
            self.start_work()
        elif self.state == PomodoroState.PAUSED:
            # 恢复之前的状态
            self.countdown_timer.start(1000)
            # 恢复到工作或休息状态(根据剩余时间判断)
            if self.time_remaining <= self.long_break and self.pomodoro_count % self.long_break_interval == 0:
                self.state = PomodoroState.LONG_BREAK
            elif self.time_remaining <= self.short_break:
                self.state = PomodoroState.SHORT_BREAK
            else:
                self.state = PomodoroState.WORK
            self.logger.info("番茄钟继续")
        else:
            # 暂停当前状态
            self.countdown_timer.stop()
            self.state = PomodoroState.PAUSED
            self.logger.info("番茄钟暂停")

        self.update()

    def stop(self):
        """停止番茄钟"""
        self.countdown_timer.stop()
        self.state = PomodoroState.IDLE
        self.time_remaining = self.work_duration
        self.logger.info("番茄钟停止")
        self.close()
        self.closed.emit()

    def open_settings(self):
        """打开番茄钟设置窗口"""
        try:
            # 如果设置窗口已经打开,则激活它
            if hasattr(self, 'settings_window') and self.settings_window.isVisible():
                self.settings_window.activateWindow()
                self.settings_window.raise_()
                return

            # 创建设置窗口
            self.settings_window = PomodoroSettingsDialog(self.config, self.logger, parent=self)
            self.settings_window.settings_saved.connect(self.on_settings_saved)
            self.settings_window.show()
            self.logger.info("番茄钟设置窗口已打开")

        except Exception as e:
            self.logger.error(f"打开番茄钟设置窗口失败: {e}", exc_info=True)
            self.tray_icon.showMessage(
                "错误",
                f"打开设置失败: {str(e)}",
                QSystemTrayIcon.Critical,
                3000
            )

    def on_settings_saved(self, new_config):
        """设置保存后的回调"""
        try:
            # 更新配置
            self.config = new_config
            pomodoro_config = self.config.get('pomodoro', {})
            self.work_duration = pomodoro_config.get('work_duration', 1500)
            self.short_break = pomodoro_config.get('short_break', 300)
            self.long_break = pomodoro_config.get('long_break', 900)
            self.long_break_interval = pomodoro_config.get('long_break_interval', 4)

            self.logger.info("番茄钟配置已更新")
            self.tray_icon.showMessage(
                "设置已保存",
                "番茄钟配置已更新",
                QSystemTrayIcon.Information,
                2000
            )

        except Exception as e:
            self.logger.error(f"更新番茄钟配置失败: {e}", exc_info=True)

    def update_countdown(self):
        """更新倒计时"""
        self.time_remaining -= 1

        if self.time_remaining <= 0:
            # 倒计时结束
            self.on_countdown_finished()

        self.update()  # 触发重绘

    def on_countdown_finished(self):
        """倒计时完成"""
        self.countdown_timer.stop()

        if self.state == PomodoroState.WORK:
            # 工作完成
            self.pomodoro_count += 1
            self.logger.info(f"番茄钟完成:第{self.pomodoro_count}个")

            # 发送通知
            self.tray_icon.showMessage(
                "🍅 番茄钟完成!",
                f"恭喜完成第{self.pomodoro_count}个番茄钟!\n休息一下吧~",
                QSystemTrayIcon.Information,
                5000
            )

            # 自动进入休息模式
            if self.pomodoro_count % self.long_break_interval == 0:
                self.start_long_break()
            else:
                self.start_short_break()

        elif self.state in [PomodoroState.SHORT_BREAK, PomodoroState.LONG_BREAK]:
            # 休息完成
            rest_type = "长休息" if self.state == PomodoroState.LONG_BREAK else "短休息"
            self.logger.info(f"{rest_type}完成")

            # 发送通知,询问是否开始下一个番茄钟
            self.tray_icon.showMessage(
                "⏰ 休息时间结束",
                f"{rest_type}结束啦!准备好开始下一个番茄钟了吗?\n点击番茄钟面板的开始按钮继续~",
                QSystemTrayIcon.Information,
                5000
            )

            # 停止计时,等待用户手动开始
            self.state = PomodoroState.IDLE
            self.time_remaining = self.work_duration
            self.update()

    def format_time(self, seconds):
        """格式化时间显示

        Args:
            seconds: 秒数

        Returns:
            str: 格式化的时间字符串 "MM:SS"
        """
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"

    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 支持拖拽和按钮悬停"""
        mouse_pos = event.position()

        # 如果正在拖拽,移动窗口
        if self.dragging:
            # 计算新位置
            new_pos = event.globalPosition().toPoint() - self.drag_position
            self.move(new_pos)
            return

        # 计算按钮区域
        play_pause_rect = self.get_play_pause_button_rect()
        settings_rect = self.get_settings_button_rect()
        close_rect = self.get_close_button_rect()

        old_hovered = self.hovered_button

        if play_pause_rect.contains(mouse_pos.toPoint()):
            self.hovered_button = 'play_pause'
            self.setCursor(QCursor(Qt.PointingHandCursor))
        elif settings_rect.contains(mouse_pos.toPoint()):
            self.hovered_button = 'settings'
            self.setCursor(QCursor(Qt.PointingHandCursor))
        elif close_rect.contains(mouse_pos.toPoint()):
            self.hovered_button = 'close'
            self.setCursor(QCursor(Qt.PointingHandCursor))
        else:
            self.hovered_button = None
            self.setCursor(QCursor(Qt.ArrowCursor))

        # 如果悬停状态改变,触发重绘
        if old_hovered != self.hovered_button:
            self.update()

        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        """鼠标离开事件"""
        if self.hovered_button is not None:
            self.hovered_button = None
            self.setCursor(QCursor(Qt.ArrowCursor))
            self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            mouse_pos = event.position()

            # 检查点击位置
            play_pause_rect = self.get_play_pause_button_rect()
            settings_rect = self.get_settings_button_rect()
            close_rect = self.get_close_button_rect()

            if play_pause_rect.contains(mouse_pos.toPoint()):
                self.toggle_pause()
            elif settings_rect.contains(mouse_pos.toPoint()):
                self.open_settings()
            elif close_rect.contains(mouse_pos.toPoint()):
                self.stop()
            else:
                # 点击在其他区域,开始拖拽
                self.dragging = True
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                self.setCursor(QCursor(Qt.ClosedHandCursor))

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton and self.dragging:
            self.dragging = False
            self.setCursor(QCursor(Qt.ArrowCursor))

        super().mouseReleaseEvent(event)

    def get_play_pause_button_rect(self):
        """获取开始/暂停按钮的矩形区域"""
        # 按钮位置:倒计时文字右侧
        return QRectF(150, 12, 30, 26)

    def get_settings_button_rect(self):
        """获取设置按钮的矩形区域"""
        # 按钮位置:播放/暂停按钮和关闭按钮之间
        return QRectF(190, 12, 30, 26)

    def get_close_button_rect(self):
        """获取关闭按钮的矩形区域"""
        # 按钮位置:右上角
        return QRectF(250, 8, 20, 20)

    def paintEvent(self, event):
        """绘制番茄钟面板"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        # 1. 绘制半透明背景(深色,带圆角)
        if hasattr(self, 'theme_bg_color'):
            bg_color = self.theme_bg_color
        else:
            bg_color = QColor(50, 50, 50, 230)  # 深灰色,半透明
        painter.setBrush(bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, width, height, 10, 10)  # 圆角半径10px

        # 2. 绘制番茄图标(emoji)
        font = QFont()
        font.setPointSize(20)
        painter.setFont(font)
        icon_color = QColor(self.theme_text_color) if hasattr(self, 'theme_text_color') else QColor(255, 255, 255)
        painter.setPen(icon_color)
        painter.drawText(QRectF(10, 0, 40, height), Qt.AlignCenter, "🍅")

        # 3. 绘制倒计时文字
        time_text = self.format_time(self.time_remaining)
        font.setPointSize(18)
        font.setBold(True)
        painter.setFont(font)

        # 根据状态选择颜色
        if self.state == PomodoroState.WORK:
            text_color = QColor(255, 99, 71)  # 番茄红
        elif self.state in [PomodoroState.SHORT_BREAK, PomodoroState.LONG_BREAK]:
            text_color = QColor(76, 175, 80)  # 绿色
        elif self.state == PomodoroState.PAUSED:
            text_color = QColor(158, 158, 158)  # 灰色
        else:
            text_color = QColor(255, 255, 255)  # 白色

        painter.setPen(text_color)
        painter.drawText(QRectF(50, 0, 100, height), Qt.AlignCenter, time_text)

        # 4. 绘制开始/暂停按钮
        play_pause_rect = self.get_play_pause_button_rect()

        # 按钮背景(悬停时高亮)
        if self.hovered_button == 'play_pause':
            button_bg = QColor(255, 255, 255, 50)  # 半透明白色
            painter.setBrush(button_bg)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(play_pause_rect, 5, 5)

        # 按钮图标
        font.setPointSize(16)
        painter.setFont(font)
        btn_text_color = QColor(self.theme_text_color) if hasattr(self, 'theme_text_color') else QColor(255, 255, 255)
        painter.setPen(btn_text_color)

        if self.state in [PomodoroState.WORK, PomodoroState.SHORT_BREAK, PomodoroState.LONG_BREAK]:
            # 显示暂停图标
            painter.drawText(play_pause_rect, Qt.AlignCenter, "⏸")
        else:
            # 显示播放图标
            painter.drawText(play_pause_rect, Qt.AlignCenter, "▶")

        # 5. 绘制设置按钮
        settings_rect = self.get_settings_button_rect()

        # 按钮背景(悬停时高亮)
        if self.hovered_button == 'settings':
            button_bg = QColor(255, 255, 255, 50)  # 半透明白色
            painter.setBrush(button_bg)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(settings_rect, 5, 5)

        # 按钮图标
        font.setPointSize(14)
        painter.setFont(font)
        btn_text_color = QColor(self.theme_text_color) if hasattr(self, 'theme_text_color') else QColor(255, 255, 255)
        painter.setPen(btn_text_color)
        painter.drawText(settings_rect, Qt.AlignCenter, "⚙")

        # 6. 绘制关闭按钮
        close_rect = self.get_close_button_rect()

        # 按钮背景(悬停时高亮)
        if self.hovered_button == 'close':
            button_bg = QColor(255, 99, 71, 100)  # 半透明红色
            painter.setBrush(button_bg)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(close_rect, 3, 3)

        # 按钮图标
        font.setPointSize(12)
        painter.setFont(font)
        btn_text_color = QColor(self.theme_text_color) if hasattr(self, 'theme_text_color') else QColor(255, 255, 255)
        painter.setPen(btn_text_color)
        painter.drawText(close_rect, Qt.AlignCenter, "✕")

        painter.end()

    def apply_theme(self):
        """应用当前主题到番茄钟面板"""
        if not self.theme_manager:
            return

        theme = self.theme_manager.get_current_theme()
        if not theme:
            return

        # 保存主题颜色以便绘制时使用
        bg_color = theme.get('background_color', '#323232')
        text_color = theme.get('text_color', '#FFFFFF')
        accent_color = theme.get('accent_color', '#2196F3')

        # 转换背景色为RGB（用于半透明背景）
        bg_rgb = QColor(bg_color)
        bg_rgb.setAlpha(230)  # 保持半透明

        # 保存主题颜色
        self.theme_bg_color = bg_rgb
        self.theme_text_color = text_color
        self.theme_accent_color = accent_color

        self.update()
