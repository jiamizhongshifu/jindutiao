"""
成就弹窗 UI 测试脚本
直接显示各稀有度的成就弹窗，用于测试视觉效果
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import QGraphicsDropShadowEffect

# 模拟成就数据
class MockAchievement:
    def __init__(self, name, description, emoji, rarity):
        self.name = name
        self.description = description
        self.emoji = emoji
        self.rarity = rarity

# 测试用成就
TEST_ACHIEVEMENTS = {
    'common': MockAchievement("初来乍到", "首次使用GaiYa", "👋", "common"),
    'rare': MockAchievement("专注能手", "累计专注50小时", "🎯", "rare"),
    'epic': MockAchievement("时间大师", "连续30天使用", "⏰", "epic"),
    'legendary': MockAchievement("传说觉醒", "达成所有成就", "🏆", "legendary"),
}

# 主题色
class LightTheme:
    BG_PRIMARY = "#FFFFFF"
    TEXT_PRIMARY = "#333333"
    TEXT_SECONDARY = "#666666"

def show_achievement_popup(achievement, parent=None):
    """显示成就弹窗 - 升级版"""

    rarity_cn_map = {
        'common': '普通',
        'rare': '稀有',
        'epic': '史诗',
        'legendary': '传说'
    }
    rarity_cn = rarity_cn_map.get(achievement.rarity, achievement.rarity)

    # 稀有度颜色映射 - 升级版
    rarity_styles = {
        'common': {
            'color': '#78909C',
            'bg_light': '#F5F5F5',
            'bg_dark': '#E0E0E0',
            'border': '#BDBDBD',
            'glow': False
        },
        'rare': {
            'color': '#2196F3',
            'bg_light': '#E3F2FD',
            'bg_dark': '#BBDEFB',
            'border': '#64B5F6',
            'glow': False
        },
        'epic': {
            'color': '#9C27B0',
            'bg_light': '#F3E5F5',
            'bg_dark': '#E1BEE7',
            'border': '#BA68C8',
            'glow': True
        },
        'legendary': {
            'color': '#FF9800',
            'bg_light': '#FFF8E1',
            'bg_dark': '#FFE082',
            'border': '#FFB74D',
            'glow': True
        }
    }

    style = rarity_styles.get(achievement.rarity, rarity_styles['common'])
    color = style['color']
    bg_light = style['bg_light']
    bg_dark = style['bg_dark']
    border_color = style['border']
    has_glow = style['glow']

    # 创建对话框
    dialog = QDialog(parent)
    dialog.setWindowTitle("成就解锁!")
    dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
    dialog.setFixedWidth(340)
    dialog.setModal(True)

    # 设置窗口图标
    trophy_icon_path = Path(__file__).parent / "assets" / "icons" / "trophy.svg"
    if trophy_icon_path.exists():
        dialog.setWindowIcon(QIcon(str(trophy_icon_path)))

    # 主布局
    main_layout = QVBoxLayout(dialog)
    main_layout.setSpacing(16)
    main_layout.setContentsMargins(24, 20, 24, 20)

    # 成就图标区域 - 外层渐变容器
    icon_container = QFrame()
    icon_container.setStyleSheet(f"""
        QFrame {{
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 {bg_light},
                stop:1 {bg_dark}
            );
            border-radius: 16px;
            border: 2px solid {border_color};
        }}
    """)
    icon_container.setFixedHeight(120)

    # 高稀有度添加光晕效果
    if has_glow:
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(color))
        shadow.setOffset(0, 0)
        icon_container.setGraphicsEffect(shadow)

    icon_layout = QVBoxLayout(icon_container)
    icon_layout.setAlignment(Qt.AlignCenter)

    # 内层圆形图标容器 - 带高光效果
    icon_circle = QFrame()
    icon_circle.setFixedSize(80, 80)
    icon_circle.setStyleSheet(f"""
        QFrame {{
            background: qradialgradient(
                cx:0.5, cy:0.3, radius:0.8,
                fx:0.5, fy:0.3,
                stop:0 white,
                stop:0.5 {bg_light},
                stop:1 {bg_dark}
            );
            border-radius: 40px;
            border: 1px solid {border_color};
        }}
    """)
    circle_layout = QVBoxLayout(icon_circle)
    circle_layout.setAlignment(Qt.AlignCenter)
    circle_layout.setContentsMargins(0, 0, 0, 0)

    icon_label = QLabel(achievement.emoji)
    icon_label.setStyleSheet("""
        QLabel {
            font-size: 42px;
            font-family: "Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji";
            background: transparent;
            border: none;
        }
    """)
    icon_label.setAlignment(Qt.AlignCenter)
    circle_layout.addWidget(icon_label)

    icon_layout.addWidget(icon_circle, alignment=Qt.AlignCenter)
    main_layout.addWidget(icon_container)

    # 成就名称
    name_label = QLabel(achievement.name)
    name_label.setStyleSheet(f"""
        QLabel {{
            font-size: 18px;
            font-weight: bold;
            color: {LightTheme.TEXT_PRIMARY};
        }}
    """)
    name_label.setAlignment(Qt.AlignCenter)
    main_layout.addWidget(name_label)

    # 成就描述
    desc_label = QLabel(achievement.description)
    desc_label.setStyleSheet(f"""
        QLabel {{
            font-size: 14px;
            color: {LightTheme.TEXT_SECONDARY};
        }}
    """)
    desc_label.setAlignment(Qt.AlignCenter)
    desc_label.setWordWrap(True)
    main_layout.addWidget(desc_label)

    # 稀有度徽章 - 升级版
    rarity_badge = QLabel(f"⭐ 稀有度: {rarity_cn}")
    rarity_badge.setStyleSheet(f"""
        QLabel {{
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {bg_light},
                stop:1 {bg_dark}
            );
            color: {color};
            font-size: 13px;
            font-weight: 600;
            padding: 8px 20px;
            border-radius: 14px;
            border: 1px solid {border_color};
        }}
    """)
    rarity_badge.setAlignment(Qt.AlignCenter)

    badge_container = QHBoxLayout()
    badge_container.addStretch()
    badge_container.addWidget(rarity_badge)
    badge_container.addStretch()
    main_layout.addLayout(badge_container)

    # 确定按钮
    main_layout.addSpacing(8)
    btn_layout = QHBoxLayout()
    btn_layout.addStretch()

    ok_btn = QPushButton("太棒了!")
    ok_btn.setFixedWidth(100)
    ok_btn.setCursor(Qt.PointingHandCursor)
    ok_btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {color};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 10px 24px;
            font-size: 14px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            opacity: 0.9;
        }}
    """)
    ok_btn.clicked.connect(dialog.accept)
    btn_layout.addWidget(ok_btn)
    btn_layout.addStretch()
    main_layout.addLayout(btn_layout)

    # 对话框样式
    dialog.setStyleSheet(f"""
        QDialog {{
            background-color: {LightTheme.BG_PRIMARY};
        }}
    """)

    return dialog

def main():
    app = QApplication(sys.argv)

    print("=" * 50)
    print("成就弹窗 UI 测试")
    print("=" * 50)
    print("\n将依次显示四种稀有度的成就弹窗：")
    print("1. 普通 (Common) - 灰色")
    print("2. 稀有 (Rare) - 蓝色")
    print("3. 史诗 (Epic) - 紫色 + 光晕")
    print("4. 传说 (Legendary) - 金色 + 光晕")
    print("\n点击按钮关闭后显示下一个...\n")

    for rarity in ['common', 'rare', 'epic', 'legendary']:
        achievement = TEST_ACHIEVEMENTS[rarity]
        print(f"显示: {achievement.name} ({rarity})")
        dialog = show_achievement_popup(achievement)
        dialog.exec()

    print("\n测试完成!")

if __name__ == "__main__":
    main()
