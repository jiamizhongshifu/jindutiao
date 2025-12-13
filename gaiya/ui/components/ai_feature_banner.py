"""配置管理器顶部AI功能横幅"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QLinearGradient, QGradient, QPalette, QBrush, QColor


class AiFeatureBanner(QFrame):
    """AI功能推广横幅"""

    ai_generate_clicked = Signal()
    learn_more_clicked = Signal()
    close_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setFixedHeight(70)

        # 设置渐变背景
        self.setStyleSheet("""
            AiFeatureBanner {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #E3F2FD,
                    stop:1 #BBDEFB
                );
                border: 1px solid #90CAF9;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)  # ✅ P1-1.6.11: 恢复正常margin,使用AlignVCenter对齐
        layout.setSpacing(15)

        # 图标
        icon_label = QLabel("🤖")
        icon_font = QFont()
        icon_font.setPointSize(28)
        icon_label.setFont(icon_font)
        icon_label.setFixedSize(60, 60)  # ✅ P1-1.6.17: 扩大容器避免截断
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # ✅ P1-1.6.16: 继续向上移动20px,使emoji与文字完美对齐
        icon_label.setStyleSheet("margin-top: -30px;")
        layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignVCenter)  # ✅ P1-1.6: 垂直居中

        # 引导文案
        text_label = QLabel("让AI帮你规划一天吧!")
        text_font = QFont()
        text_font.setPointSize(13)
        text_font.setBold(True)
        text_label.setFont(text_font)
        text_label.setStyleSheet("color: #1565C0;")
        layout.addWidget(text_label, alignment=Qt.AlignmentFlag.AlignVCenter)  # ✅ P1-1.6: 垂直居中

        layout.addStretch()

        # CTA按钮
        self.generate_btn = QPushButton("AI生成任务方案")
        self.generate_btn.setFixedHeight(35)
        self.generate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        self.generate_btn.clicked.connect(self.ai_generate_clicked.emit)
        layout.addWidget(self.generate_btn, alignment=Qt.AlignmentFlag.AlignVCenter)  # ✅ P1-1.6: 垂直居中

        # 了解更多链接
        learn_more_label = QLabel('<a href="#" style="color: #1976D2; text-decoration: none;">了解更多 ></a>')
        learn_more_label.setOpenExternalLinks(False)
        learn_more_label.linkActivated.connect(lambda: self.learn_more_clicked.emit())
        learn_more_label.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(learn_more_label, alignment=Qt.AlignmentFlag.AlignVCenter)  # ✅ P1-1.6: 垂直居中

        # 关闭按钮
        close_btn = QPushButton("×")
        close_btn.setFixedSize(25, 25)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #1565C0;
                border: none;
                font-size: 18pt;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #D32F2F;
            }
        """)
        close_btn.clicked.connect(self.on_close_clicked)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignVCenter)  # ✅ P1-1.6: 垂直居中

    def on_close_clicked(self):
        """关闭按钮被点击"""
        self.close_clicked.emit()
        self.hide()
