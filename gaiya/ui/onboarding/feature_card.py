"""功能卡片组件 - 用于新手引导界面展示核心功能"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property, QRect
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor
import sys
import os

# 添加父目录到路径以导入i18n模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class FeatureCard(QWidget):
    """功能卡片组件

    展示单个功能的图标、标题和描述,支持悬停动画效果。

    Args:
        emoji: emoji图标字符，如 '🎯'
        title: 功能标题
        description: 功能描述
        parent: 父级widget
    """

    def __init__(self, emoji: str, title: str, description: str, parent=None):
        super().__init__(parent)
        self._emoji = emoji
        self._title = title
        self._description = description

        # 悬停状态
        self._is_hovered = False
        self._elevation = 0  # 阴影高度(用于动画)

        self.setup_ui()
        self.setup_animations()

    def setup_ui(self):
        """设置UI界面"""
        self.setFixedSize(400, 80)
        self.setStyleSheet("""
            FeatureCard {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }
            FeatureCard:hover {
                border: 1px solid #3B82F6;
                background-color: #F9FAFB;
            }
        """)

        # 主布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Emoji图标区域
        self.icon_widget = QLabel(self._emoji)
        icon_font = QFont()
        icon_font.setPointSize(32)  # emoji字号
        icon_font.setFamilies(["Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji"])
        self.icon_widget.setFont(icon_font)
        self.icon_widget.setFixedSize(48, 48)
        self.icon_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_widget.setStyleSheet("background: transparent;")
        layout.addWidget(self.icon_widget)

        # 文字区域
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        # 标题
        title_label = QLabel(self._title)
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #111827;")
        text_layout.addWidget(title_label)

        # 描述
        desc_label = QLabel(self._description)
        desc_font = QFont()
        desc_font.setPointSize(11)
        desc_label.setFont(desc_font)
        desc_label.setStyleSheet("color: #6B7280;")
        desc_label.setWordWrap(True)
        text_layout.addWidget(desc_label)

        layout.addLayout(text_layout, 1)

    def setup_animations(self):
        """设置悬停动画"""
        self.elevation_animation = QPropertyAnimation(self, b"elevation")
        self.elevation_animation.setDuration(200)
        self.elevation_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def enterEvent(self, event):
        """鼠标进入时的动画效果"""
        super().enterEvent(event)
        self._is_hovered = True
        self.elevation_animation.setStartValue(self._elevation)
        self.elevation_animation.setEndValue(4)
        self.elevation_animation.start()

    def leaveEvent(self, event):
        """鼠标离开时的动画效果"""
        super().leaveEvent(event)
        self._is_hovered = False
        self.elevation_animation.setStartValue(self._elevation)
        self.elevation_animation.setEndValue(0)
        self.elevation_animation.start()

    def get_elevation(self) -> int:
        """获取当前阴影高度(用于Property动画)"""
        return self._elevation

    def set_elevation(self, value: int):
        """设置阴影高度并触发重绘"""
        self._elevation = value
        self.update()

    # Qt Property用于动画
    elevation = Property(int, get_elevation, set_elevation)

    def paintEvent(self, event):
        """自定义绘制 - 添加阴影效果"""
        super().paintEvent(event)

        # 如果有elevation,绘制阴影效果
        if self._elevation > 0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # 绘制阴影(简化版,真实项目可使用QGraphicsDropShadowEffect)
            shadow_color = QColor(0, 0, 0, 20 + self._elevation * 5)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(shadow_color)

            shadow_rect = self.rect().adjusted(
                self._elevation,
                self._elevation,
                -self._elevation,
                -self._elevation
            )
            painter.drawRoundedRect(shadow_rect, 8, 8)


class FeatureCardList(QWidget):
    """功能卡片列表容器

    用于在WelcomeDialog中垂直排列多个FeatureCard。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(12)
        self.layout.setContentsMargins(0, 0, 0, 0)

    def add_feature(self, emoji: str, title: str, description: str):
        """添加一个功能卡片

        Args:
            emoji: emoji图标字符
            title: 功能标题
            description: 功能描述
        """
        card = FeatureCard(emoji, title, description, self)
        self.layout.addWidget(card)

    def clear_features(self):
        """清空所有功能卡片"""
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


if __name__ == '__main__':
    """测试代码 - 可以单独运行此文件预览效果"""
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # 测试单个卡片
    card = FeatureCard(
        emoji='🎯',
        title='一眼掌握全天任务进度',
        description='实时追踪每日进度,让时间流逝清晰可见'
    )
    card.show()

    sys.exit(app.exec())
