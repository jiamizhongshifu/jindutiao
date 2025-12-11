"""配额用尽对话框 - 引导用户升级会员"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

import sys
import os
# 添加父目录到路径以导入i18n模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from i18n.translator import tr


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
        self.setWindowTitle(tr("quota_dialog.title.window"))
        self.setFixedSize(400, 280)
        self.setModal(True)

        # 主布局
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        # 图标和标题
        title = QLabel(tr("quota_dialog.title.dialog"))
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 说明文字
        info = QLabel(tr("quota_dialog.info.message"))
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("color: #666666; line-height: 1.5;")
        layout.addWidget(info)

        # 会员权益
        benefits = [
            tr("quota_dialog.benefits.unlimited_ai"),
            tr("quota_dialog.benefits.remove_watermark"),
            tr("quota_dialog.benefits.full_statistics"),
            tr("quota_dialog.benefits.more_features")
        ]

        for benefit in benefits:
            benefit_label = QLabel(benefit)
            benefit_label.setStyleSheet("padding: 2px 0; color: #333333;")
            layout.addWidget(benefit_label)

        layout.addSpacing(10)

        # 价格提示
        price_label = QLabel(tr("quota_dialog.price.pricing"))
        price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        price_label.setStyleSheet("color: #2196F3; font-weight: bold;")
        layout.addWidget(price_label)

        layout.addStretch()

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # 明天再说按钮
        later_btn = QPushButton(tr("quota_dialog.button.later"))
        later_btn.setFixedHeight(36)
        later_btn.clicked.connect(self.reject)
        button_layout.addWidget(later_btn)

        # 升级会员按钮
        upgrade_btn = QPushButton(tr("quota_dialog.button.upgrade"))
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
        # 先发出升级信号(在关闭对话框之前)
        self.upgrade_requested.emit()
        # 再关闭对话框
        self.accept()
