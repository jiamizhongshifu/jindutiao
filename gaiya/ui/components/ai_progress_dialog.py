"""AI任务生成进度对话框"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class AiProgressDialog(QDialog):
    """AI生成进度对话框

    显示AI任务生成的进度,提供取消功能
    """

    # 信号
    cancel_requested = Signal()  # 用户请求取消

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("AI任务生成中")
        self.setFixedSize(400, 200)
        self.setModal(True)

        # 禁用关闭按钮(必须通过取消按钮关闭)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        title = QLabel("🤖 AI正在为你生成任务计划...")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 进度条(不确定模式)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # 不确定模式
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(8)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                background-color: #F5F5F5;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress)

        # 提示文字
        hint = QLabel("这通常需要10-30秒,请耐心等待...")
        hint.setStyleSheet("color: #666666;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        layout.addStretch()

        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedHeight(36)
        cancel_btn.clicked.connect(self.on_cancel_clicked)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F5;
                color: #666666;
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #EEEEEE;
            }
        """)
        layout.addWidget(cancel_btn)

    def on_cancel_clicked(self):
        """取消按钮点击"""
        self.cancel_requested.emit()
        self.reject()

    def closeEvent(self, event):
        """阻止用户通过ESC键关闭"""
        # 只能通过取消按钮关闭
        self.on_cancel_clicked()
        event.ignore()
