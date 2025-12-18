"""AI场景快速选择器组件"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QButtonGroup, QRadioButton,
    QTextEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import json
import os
import sys


class SceneCard(QFrame):
    """场景卡片组件"""

    clicked = Signal(str)  # 发出场景ID

    def __init__(self, scene_id: str, name: str, icon: str, description: str, parent=None):
        super().__init__(parent)
        self.scene_id = scene_id
        self.is_selected = False
        self.setup_ui(name, icon, description)

    def setup_ui(self, name: str, icon: str, description: str):
        """设置UI"""
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.update_style()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(140, 140)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 图标
        icon_label = QLabel(icon)
        icon_font = QFont()
        icon_font.setPointSize(32)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # 名称
        name_label = QLabel(name)
        name_font = QFont()
        name_font.setPointSize(12)
        name_font.setBold(True)
        name_label.setFont(name_font)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)

        # 描述
        desc_label = QLabel(description)
        desc_font = QFont()
        desc_font.setPointSize(9)
        desc_label.setFont(desc_font)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666666;")
        layout.addWidget(desc_label)

    def update_style(self):
        """更新样式状态"""
        if self.is_selected:
            self.setStyleSheet("""
                SceneCard {
                    background-color: #E3F2FD;
                    border: 2px solid #2196F3;
                    border-radius: 10px;
                    padding: 15px;
                }
            """)
        else:
            self.setStyleSheet("""
                SceneCard {
                    background-color: #FFFFFF;
                    border: 2px solid #E0E0E0;
                    border-radius: 10px;
                    padding: 15px;
                }
                SceneCard:hover {
                    border-color: #2196F3;
                    background-color: #F5F9FF;
                }
            """)

    def set_selected(self, selected: bool):
        """设置选中状态"""
        self.is_selected = selected
        self.update_style()

    def mousePressEvent(self, event):
        """点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.scene_id)
        super().mousePressEvent(event)


class AiSceneSelector(QWidget):
    """AI场景选择器"""

    scene_selected = Signal(str, str)  # scene_id, prompt
    custom_mode_selected = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scenes_data = []
        self.selected_scene_id = None
        self.scene_cards = {}  # 存储场景卡片引用
        self.load_presets()
        self.setup_ui()

    def load_presets(self):
        """加载场景预设"""
        import logging
        try:
            # 尝试从打包后的路径加载
            if hasattr(sys, '_MEIPASS'):
                presets_path = os.path.join(sys._MEIPASS, 'gaiya', 'data', 'ai_scene_presets.json')
                logging.info(f"[场景预��] 打包模式,路径: {presets_path}")
            else:
                presets_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'data', 'ai_scene_presets.json'
                )
                logging.info(f"[场景预设] 开发模式,路径: {presets_path}")

            logging.info(f"[场景预设] 文件是否存在: {os.path.exists(presets_path)}")

            with open(presets_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.scenes_data = data.get('presets', [])
                logging.info(f"[场景预设] 成功加载 {len(self.scenes_data)} 个预设场景")
        except Exception as e:
            logging.error(f"[场景预设] 加载失败: {type(e).__name__}: {e}", exc_info=True)
            self.scenes_data = []

    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)  # 基础间距
        layout.setContentsMargins(24, 20, 24, 10)  # 增加左右边距

        # 快速生成区域
        quick_label = QLabel("━━━ 快速生成 ━━━  (推荐)")
        quick_font = QFont()
        quick_font.setPointSize(11)
        quick_font.setBold(True)
        quick_label.setFont(quick_font)
        quick_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        quick_label.setStyleSheet("color: #2196F3;")
        layout.addWidget(quick_label)

        layout.addSpacing(4)  # 标题与提示间距

        # 场景选择提示
        hint_label = QLabel("选择你的场景:")
        hint_label.setStyleSheet("color: #666666; font-size: 11pt;")
        layout.addWidget(hint_label)

        layout.addSpacing(4)  # 提示与卡片间距

        # 场景卡片网格
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)  # 卡片间距
        cards_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        for scene in self.scenes_data:
            card = SceneCard(
                scene['id'],
                scene['name'],
                scene['icon'],
                scene['description']
            )
            card.clicked.connect(self.on_scene_clicked)
            cards_layout.addWidget(card)
            self.scene_cards[scene['id']] = card  # 保存卡片引用

        layout.addLayout(cards_layout)

        layout.addSpacing(16)  # 场景卡片与自定义区域间距

        # ✅ P1-1.6: 删除多余的 HLine 分隔符,保留文字装饰即可
        # layout.addSpacing(10)
        # separator = QFrame()
        # separator.setFrameShape(QFrame.Shape.HLine)
        # separator.setFrameShadow(QFrame.Shadow.Sunken)
        # layout.addWidget(separator)
        # layout.addSpacing(10)

        # 自定义描述区域
        custom_label = QLabel("━━━ 自定义描述 ━━━")
        custom_font = QFont()
        custom_font.setPointSize(11)
        custom_font.setBold(True)
        custom_label.setFont(custom_font)
        custom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(custom_label)

        # 自定义输入框
        self.custom_input = QTextEdit()
        self.custom_input.setPlaceholderText("或者详细描述你的计划...")
        self.custom_input.setMinimumHeight(60)
        self.custom_input.setMaximumHeight(80)
        self.custom_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                padding: 8px;
                font-size: 10pt;
            }
            QTextEdit:focus {
                border-color: #2196F3;
            }
        """)
        layout.addWidget(self.custom_input)

        # 底部留白（由父容器 ImprovedAIGenerationDialog 的按钮区域提供）

    def on_scene_clicked(self, scene_id: str):
        """场景卡片被点击"""
        import logging
        logging.info(f"[场景选择器] 场景卡片被点击: {scene_id}")

        # 取消之前选中的卡片
        if self.selected_scene_id and self.selected_scene_id in self.scene_cards:
            logging.info(f"[场景选择器] 取消之前选中的卡片: {self.selected_scene_id}")
            self.scene_cards[self.selected_scene_id].set_selected(False)

        # 设置新选中的卡片
        self.selected_scene_id = scene_id
        if scene_id in self.scene_cards:
            logging.info(f"[场景选择器] 设置新选中的卡片: {scene_id}")
            self.scene_cards[scene_id].set_selected(True)

        # 查找对应的prompt
        for scene in self.scenes_data:
            if scene['id'] == scene_id:
                logging.info(f"[场景选择器] 找到场景prompt,长度: {len(scene['prompt'])}")
                self.scene_selected.emit(scene_id, scene['prompt'])
                break

    def get_custom_prompt(self) -> str:
        """获取自定义输入的prompt"""
        return self.custom_input.toPlainText().strip()

    def get_selected_prompt(self) -> str:
        """获取当前选中的prompt(场景或自定义)"""
        custom = self.get_custom_prompt()
        if custom:
            return custom

        if self.selected_scene_id:
            for scene in self.scenes_data:
                if scene['id'] == self.selected_scene_id:
                    return scene['prompt']

        return ""
