"""改进版AI任务生成对话框 - 集成场景快速选择"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from gaiya.ui.components.ai_scene_selector import AiSceneSelector


class ImprovedAIGenerationDialog(QDialog):
    """改进版AI生成对话框

    集成场景快速选择功能,简化用户输入流程
    """

    # ✅ P1-1.6: 修改信号定义,添加 scene_name 参数
    generation_requested = Signal(str, str)  # (prompt, scene_name)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_prompt = ""
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("AI任务生成助手")  # ✅ P1-1.6.19: 恢复文字标题
        self.setFixedSize(550, 440)  # ✅ P1-1.6.19: 移除60px标题栏后调整总高度
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # ✅ P1-1.6.19: 移除标题栏,直接显示场景选择器
        # title_widget = self.create_title_bar()
        # layout.addWidget(title_widget)

        # 场景选择器
        self.scene_selector = AiSceneSelector(self)
        self.scene_selector.scene_selected.connect(self.on_scene_selected)
        layout.addWidget(self.scene_selector)

        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(20, 10, 20, 20)
        button_layout.setSpacing(10)

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedHeight(40)
        cancel_btn.clicked.connect(self.reject)
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
        button_layout.addWidget(cancel_btn)

        self.next_btn = QPushButton("下一步")
        self.next_btn.setFixedHeight(40)
        self.next_btn.clicked.connect(self.on_next_clicked)
        self.next_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
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
        button_layout.addWidget(self.next_btn)

        layout.addLayout(button_layout)

    def create_title_bar(self):
        """创建标题栏"""
        title_widget = QLabel()
        title_widget.setFixedHeight(60)
        title_widget.setStyleSheet("""
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #2196F3,
                stop:1 #42A5F5
            );
        """)

        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(20, 0, 20, 0)

        # 标题文字 - ✅ P1-1.6.18: 只保留机器人图标,移除文字
        title_label = QLabel("🤖")
        title_font = QFont()
        title_font.setPointSize(24)  # 增大图标字号
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: white;")
        title_layout.addWidget(title_label)

        title_layout.addStretch()

        return title_widget

    def on_scene_selected(self, scene_id: str, prompt: str):
        """场景被选中"""
        self.selected_prompt = prompt

    def on_next_clicked(self):
        """下一步按钮点击"""
        import logging
        logging.info("[AI对话框] 下一步按钮被点击")

        # 获取最终的prompt
        final_prompt = self.scene_selector.get_selected_prompt()
        logging.info(f"[AI对话框] 获取到的prompt长度: {len(final_prompt) if final_prompt else 0}")
        logging.info(f"[AI对话框] 当前选中场景ID: {self.scene_selector.selected_scene_id}")
        logging.info(f"[AI对话框] 自定义输入内容: {self.scene_selector.get_custom_prompt()[:50] if self.scene_selector.get_custom_prompt() else '(空)'}")

        if not final_prompt:
            logging.warning("[AI对话框] prompt为空,弹出警告对话框")
            QMessageBox.warning(
                self,
                "请选择场景",
                "请选择一个预设场景或输入自定义描述!"
            )
            return

        # ✅ P1-1.6: 获取场景名称以传递给信号
        scene_name = "未命名"
        if self.scene_selector and self.scene_selector.selected_scene_id:
            # 从场景数据中查找名称
            for scene in self.scene_selector.scenes_data:
                if scene.get('id') == self.scene_selector.selected_scene_id:
                    scene_name = scene.get('name', scene_name)
                    logging.info(f"[AI对话框] 找到场景名称: {scene_name} (ID: {self.scene_selector.selected_scene_id})")
                    break

        # 发出信号并关闭对话框(现在包含场景名称)
        logging.info(f"[AI对话框] 发出generation_requested信号,场景:{scene_name}, prompt前50字符: {final_prompt[:50]}")
        self.generation_requested.emit(final_prompt, scene_name)
        logging.info("[AI对话框] 调用accept()关闭对话框")
        self.accept()

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
