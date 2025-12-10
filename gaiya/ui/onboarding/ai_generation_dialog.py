"""AI生成任务动画对话框 - 展示AI生成进度"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QFont, QPainter, QColor, QTransform
from PySide6.QtSvgWidgets import QSvgWidget
import sys
import os

# 添加父目录到路径以导入i18n模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 尝试导入tr函数,如果失败则使用虚拟函数(用于测试)
try:
    from i18n.translator import tr
except ImportError:
    def tr(key):
        return key


class RotatingSvgWidget(QSvgWidget):
    """支持旋转动画的SVG图标组件"""

    def __init__(self, svg_path: str, parent=None):
        super().__init__(svg_path, parent)
        self._rotation = 0

    def get_rotation(self) -> float:
        """获取当前旋转角度"""
        return self._rotation

    def set_rotation(self, angle: float):
        """设置旋转角度并触发重绘"""
        self._rotation = angle
        self.update()

    rotation = Property(float, get_rotation, set_rotation)

    def paintEvent(self, event):
        """自定义绘制 - 添加旋转效果"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # 移动到中心点
        center_x = self.width() / 2
        center_y = self.height() / 2

        # 应用旋转
        transform = QTransform()
        transform.translate(center_x, center_y)
        transform.rotate(self._rotation)
        transform.translate(-center_x, -center_y)

        painter.setTransform(transform)

        # 调用父类绘制SVG
        super().paintEvent(event)


class AIGenerationDialog(QDialog):
    """AI生成任务对话框

    在用户请求AI生成任务时显示,展示生成进度和动画效果。
    包含旋转的AI图标、状态文字和进度条。

    Args:
        parent: 父级widget
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_status = 0
        self._status_messages = []
        self.setup_ui()
        self.setup_animations()

    def setup_ui(self):
        """设置UI界面"""
        # 窗口基本设置
        self.setWindowTitle(tr("ai_generation.window.title"))
        self.setFixedSize(400, 320)
        self.setModal(True)

        # 移除窗口边框按钮
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)

        # 主布局
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # AI图标 (旋转动画)
        icon_path = self.get_ai_icon_path()
        self.icon_widget = RotatingSvgWidget(icon_path)
        self.icon_widget.setFixedSize(80, 80)
        icon_container = QVBoxLayout()
        icon_container.addWidget(self.icon_widget, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(icon_container)

        layout.addSpacing(10)

        # 标题
        title = QLabel(tr("ai_generation.title.main"))
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 状态文字
        self.status_label = QLabel(tr("ai_generation.status.initializing"))
        status_font = QFont()
        status_font.setPointSize(12)
        self.status_label.setFont(status_font)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #6B7280;")
        layout.addWidget(self.status_label)

        layout.addSpacing(10)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #E5E7EB;
            }
            QProgressBar::chunk {
                border-radius: 4px;
                background-color: #A78BFA;
            }
        """)
        layout.addWidget(self.progress_bar)

        # 提示文字
        tip = QLabel(tr("ai_generation.tip.message"))
        tip.setWordWrap(True)
        tip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tip.setStyleSheet("color: #9CA3AF; font-size: 10px;")
        layout.addWidget(tip)

        layout.addStretch()

        # 初始化状态消息列表
        self._status_messages = [
            tr("ai_generation.status.initializing"),
            tr("ai_generation.status.analyzing"),
            tr("ai_generation.status.generating"),
            tr("ai_generation.status.optimizing"),
            tr("ai_generation.status.finalizing")
        ]

    def setup_animations(self):
        """设置动画"""
        # 图标旋转动画
        self.rotation_animation = QPropertyAnimation(self.icon_widget, b"rotation")
        self.rotation_animation.setStartValue(0)
        self.rotation_animation.setEndValue(360)
        self.rotation_animation.setDuration(2000)  # 2秒一圈
        self.rotation_animation.setLoopCount(-1)  # 无限循环
        self.rotation_animation.setEasingCurve(QEasingCurve.Type.Linear)

        # 状态更新定时器
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.setInterval(1500)  # 每1.5秒切换状态

        # 进度更新定时器
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.setInterval(100)  # 每100ms更新进度

    def get_ai_icon_path(self) -> str:
        """获取AI图标路径"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        return os.path.join(project_root, 'assets', 'icons', 'ai_brain.svg')

    def start_generation(self):
        """开始生成动画"""
        self._current_status = 0
        self.progress_bar.setValue(0)

        # 启动动画和定时器
        self.rotation_animation.start()
        self.status_timer.start()
        self.progress_timer.start()

    def stop_generation(self):
        """停止生成动画"""
        self.rotation_animation.stop()
        self.status_timer.stop()
        self.progress_timer.stop()

    def update_status(self):
        """更新状态文字"""
        self._current_status = (self._current_status + 1) % len(self._status_messages)
        self.status_label.setText(self._status_messages[self._current_status])

    def update_progress(self):
        """更新进度条"""
        current_value = self.progress_bar.value()

        # 模拟进度增长(快速增长到80%,然后缓慢增长)
        if current_value < 80:
            increment = 2
        elif current_value < 95:
            increment = 0.5
        else:
            increment = 0.1

        new_value = min(current_value + increment, 99)
        self.progress_bar.setValue(int(new_value))

    def set_complete(self):
        """设置为完成状态"""
        self.stop_generation()
        self.progress_bar.setValue(100)
        self.status_label.setText(tr("ai_generation.status.complete"))
        self.status_label.setStyleSheet("color: #10B981;")  # 绿色

        # 1秒后自动关闭
        QTimer.singleShot(1000, self.accept)

    def set_error(self, error_message: str):
        """设置为错误状态"""
        self.stop_generation()
        self.status_label.setText(error_message)
        self.status_label.setStyleSheet("color: #EF4444;")  # 红色

    def showEvent(self, event):
        """窗口显示时自动居中并启动动画"""
        super().showEvent(event)
        self.center_on_screen()
        self.start_generation()

    def closeEvent(self, event):
        """窗口关闭时停止动画"""
        self.stop_generation()
        super().closeEvent(event)

    def center_on_screen(self):
        """将窗口移动到屏幕中央"""
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().geometry()
        window_rect = self.frameGeometry()
        center_point = screen.center()
        window_rect.moveCenter(center_point)
        self.move(window_rect.topLeft())


if __name__ == '__main__':
    """测试代码"""
    from PySide6.QtWidgets import QApplication, QPushButton

    # 测试模式不加载i18n
    def tr(key):
        translations = {
            "ai_generation.window.title": "AI 智能生成",
            "ai_generation.title.main": "AI 正在为你规划...",
            "ai_generation.status.initializing": "正在初始化 AI 引擎...",
            "ai_generation.status.analyzing": "分析你的时间偏好...",
            "ai_generation.status.generating": "生成个性化任务列表...",
            "ai_generation.status.optimizing": "优化任务时间分配...",
            "ai_generation.status.finalizing": "完成最后的调整...",
            "ai_generation.status.complete": "✓ 生成完成!",
            "ai_generation.tip.message": "AI 正在根据你的习惯生成专属时间规划"
        }
        return translations.get(key, key)

    # 覆盖全局tr函数
    import builtins
    builtins.tr = tr

    app = QApplication(sys.argv)

    # 测试按钮
    test_btn = QPushButton("测试AI生成对话框")

    def show_dialog():
        dialog = AIGenerationDialog()
        # 模拟3秒后完成
        QTimer.singleShot(3000, dialog.set_complete)
        dialog.exec()

    test_btn.clicked.connect(show_dialog)
    test_btn.show()

    sys.exit(app.exec())
