"""欢迎对话框 - 首次启动时显示"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QCheckBox,
    QPushButton, QHBoxLayout, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

import sys
import os
# 添加父目录到路径以导入i18n模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from i18n.translator import tr
from .feature_card import FeatureCardList


class WelcomeDialog(QDialog):
    """欢迎对话框

    首次启动应用时显示，介绍核心功能并引导用户进入配置向导。
    用户需要勾选确认复选框后才能点击"开始配置"按钮。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """设置UI界面"""
        # 窗口基本设置
        self.setWindowTitle(tr("welcome_dialog.window.title"))
        self.setFixedSize(450, 680)  # 增加高度以容纳FeatureCard (580→680)
        self.setModal(True)

        # 主布局
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        title = QLabel(tr("welcome_dialog.title.main"))
        title_font = QFont()
        title_font.setPointSize(18)  # 增加字号 16→18
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 副标题
        subtitle = QLabel(tr("welcome_dialog.title.subtitle"))
        subtitle_font = QFont()
        subtitle_font.setPointSize(14)  # 增加字号 12→14
        subtitle.setFont(subtitle_font)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #666666;")
        layout.addWidget(subtitle)

        layout.addSpacing(15)

        # 核心功能介绍 - 使用FeatureCard组件
        feature_list = FeatureCardList(self)

        # 添加4个功能卡片 (使用emoji图标)
        features_data = [
            {
                "emoji": "🎯",
                "title": tr("welcome_dialog.features.task_progress"),
                "desc": tr("welcome_dialog.features.task_progress_desc")
            },
            {
                "emoji": "🤖",
                "title": tr("welcome_dialog.features.ai_planning"),
                "desc": tr("welcome_dialog.features.ai_planning_desc")
            },
            {
                "emoji": "🎨",
                "title": tr("welcome_dialog.features.rich_themes"),
                "desc": tr("welcome_dialog.features.rich_themes_desc")
            },
            {
                "emoji": "⏰",
                "title": tr("welcome_dialog.features.smart_reminder"),
                "desc": tr("welcome_dialog.features.smart_reminder_desc")
            }
        ]

        for feature in features_data:
            feature_list.add_feature(
                emoji=feature["emoji"],
                title=feature["title"],
                description=feature["desc"]
            )

        layout.addWidget(feature_list)

        layout.addSpacing(10)

        # 说明文字
        info = QLabel(tr("welcome_dialog.info.message"))
        info.setWordWrap(True)
        info.setStyleSheet("color: #888888; font-size: 12px;")  # 增加字号 11px→12px
        layout.addWidget(info)

        layout.addStretch()

        # 确认复选框
        self.confirm_checkbox = QCheckBox(tr("welcome_dialog.checkbox.confirm"))
        checkbox_font = QFont()
        checkbox_font.setPointSize(13)  # 设置复选框字号为13pt
        self.confirm_checkbox.setFont(checkbox_font)
        self.confirm_checkbox.stateChanged.connect(self.on_checkbox_changed)
        layout.addWidget(self.confirm_checkbox)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # 跳过按钮
        skip_btn = QPushButton(tr("welcome_dialog.buttons.skip"))
        skip_btn.setFixedHeight(40)  # 增加按钮高度 36→40
        skip_btn.clicked.connect(self.reject)
        button_layout.addWidget(skip_btn)

        # 开始配置按钮
        self.start_btn = QPushButton(tr("welcome_dialog.buttons.start"))
        self.start_btn.setFixedHeight(40)  # 增加按钮高度 36→40
        self.start_btn.setEnabled(False)  # 初始禁用
        self.start_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.start_btn)

        layout.addLayout(button_layout)

    def on_checkbox_changed(self, state):
        """复选框状态改变时启用/禁用开始按钮"""
        self.start_btn.setEnabled(state == Qt.CheckState.Checked.value)

    def showEvent(self, event):
        """窗口显示时自动居中"""
        super().showEvent(event)
        self.center_on_screen()

    def center_on_screen(self):
        """将窗口移动到屏幕中央"""
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().geometry()
        window_rect = self.frameGeometry()
        center_point = screen.center()
        window_rect.moveCenter(center_point)
        self.move(window_rect.topLeft())
