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


class SceneCard(QFrame):
    """场景卡片组件"""

    clicked = Signal(str)  # 发出场景ID

    def __init__(self, scene_id: str, name: str, icon: str, description: str, parent=None):
        super().__init__(parent)
        self.scene_id = scene_id
        self.setup_ui(name, icon, description)

    def setup_ui(self, name: str, icon: str, description: str):
        """设置UI"""
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
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

    def mousePressEvent(self, event):
        """点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.scene_id)
            # 视觉反馈
            self.setStyleSheet("""
                SceneCard {
                    background-color: #E3F2FD;
                    border: 2px solid #2196F3;
                    border-radius: 10px;
                    padding: 15px;
                }
            """)
        super().mousePressEvent(event)


class AiSceneSelector(QWidget):
    """AI场景选择器"""

    scene_selected = Signal(str, str)  # scene_id, prompt
    custom_mode_selected = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scenes_data = []
        self.selected_scene_id = None
        self.load_presets()
        self.setup_ui()

    def load_presets(self):
        """加载场景预设"""
        try:
            # 尝试从打包后的路径加载
            if hasattr(os.sys, '_MEIPASS'):
                presets_path = os.path.join(os.sys._MEIPASS, 'gaiya', 'data', 'ai_scene_presets.json')
            else:
                presets_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'data', 'ai_scene_presets.json'
                )

            with open(presets_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.scenes_data = data.get('presets', [])
        except Exception as e:
            print(f"加载AI场景预设失败: {e}")
            self.scenes_data = []

    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # 快速生成区域
        quick_label = QLabel("━━━ 快速生成 ━━━  (推荐)")
        quick_font = QFont()
        quick_font.setPointSize(11)
        quick_font.setBold(True)
        quick_label.setFont(quick_font)
        quick_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        quick_label.setStyleSheet("color: #2196F3;")
        layout.addWidget(quick_label)

        # 场景选择提示
        hint_label = QLabel("选择你的场景:")
        hint_label.setStyleSheet("color: #666666; font-size: 11pt;")
        layout.addWidget(hint_label)

        # 场景卡片网格
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)
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

        layout.addLayout(cards_layout)

        # 分隔线
        layout.addSpacing(10)
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        layout.addSpacing(10)

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

        layout.addStretch()

    def on_scene_clicked(self, scene_id: str):
        """场景卡片被点击"""
        self.selected_scene_id = scene_id

        # 查找对应的prompt
        for scene in self.scenes_data:
            if scene['id'] == scene_id:
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
