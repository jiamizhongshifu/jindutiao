"""配额用尽对话框 - 引导用户升级会员"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class QuotaExhaustedDialog(QDialog):
    """配额用尽对话框

    当免费用户AI配额用尽时显示，引导用户前往个人中心升级会员。
    提供"升级会员"和"明天再说"两个选项。
    """

    # 自定义信号
    upgrade_requested = Signal()  # 用户请求升级会员

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """设置UI界面"""
        # 窗口基本设置
        self.setWindowTitle("AI配额已用完")
        self.setFixedSize(400, 280)
        self.setModal(True)

        # 主布局
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        # 图标和标题
        title = QLabel("🤖 今日AI配额已用完")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 说明文字
        info = QLabel(
            "免费用户每天有 3 次AI任务规划配额。\n"
            "你今天的配额已经用完了。\n\n"
            "升级会员即可享受："
        )
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("color: #666666; line-height: 1.5;")
        layout.addWidget(info)

        # 会员权益
        benefits = [
            "✅ 无限AI任务生成配额",
            "✅ 去除进度条水印",
            "✅ 完整数据统计报告",
            "✅ 更多高级功能..."
        ]

        for benefit in benefits:
            benefit_label = QLabel(benefit)
            benefit_label.setStyleSheet("padding: 2px 0; color: #333333;")
            layout.addWidget(benefit_label)

        layout.addSpacing(10)

        # 价格提示
        price_label = QLabel("💰 月度会员仅需 ¥29/月，年度会员 ¥199/年")
        price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        price_label.setStyleSheet("color: #2196F3; font-weight: bold;")
        layout.addWidget(price_label)

        layout.addStretch()

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # 明天再说按钮
        later_btn = QPushButton("明天再说")
        later_btn.setFixedHeight(36)
        later_btn.clicked.connect(self.reject)
        button_layout.addWidget(later_btn)

        # 升级会员按钮
        upgrade_btn = QPushButton("升级会员")
        upgrade_btn.setFixedHeight(36)
        upgrade_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
        """)
        upgrade_btn.clicked.connect(self.on_upgrade_clicked)
        button_layout.addWidget(upgrade_btn)

        layout.addLayout(button_layout)

    def on_upgrade_clicked(self):
        """升级会员按钮点击"""
        # 关闭对话框
        self.accept()
        # 发出升级信号
        self.upgrade_requested.emit()
