"""配置向导 - 2步快速设置"""

from PySide6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QLabel,
    QRadioButton, QPushButton, QButtonGroup,
    QHBoxLayout, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

import sys
import os
# 添加父目录到路径以导入i18n模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from i18n.translator import tr


class SetupWizard(QWizard):
    """配置向导

    帮助新用户快速完成基本配置的2步向导：
    1. 模板选择页面
    2. 完成页面
    """

    # 页面ID
    PAGE_TEMPLATE = 0
    PAGE_COMPLETE = 1

    # 自定义信号
    ai_generate_requested = Signal()  # 用户请求AI生成

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """设置向导界面"""
        # 向导基本设置
        self.setWindowTitle(tr("wizard.window.title"))
        self.setFixedSize(550, 700)  # 增加高度 650→700，确保完成页无需滚动
        self.setModal(True)

        # 设置向导样式
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOption(QWizard.WizardOption.NoBackButtonOnLastPage, True)

        # 添加页面
        self.setPage(self.PAGE_TEMPLATE, TemplateSelectionPage(self))
        self.setPage(self.PAGE_COMPLETE, CompletionPage(self))

        # 连接AI生成信号
        template_page = self.page(self.PAGE_TEMPLATE)
        template_page.ai_generate_clicked.connect(self.on_ai_generate_clicked)

    def on_ai_generate_clicked(self):
        """用户点击AI生成按钮"""
        # 关闭向导
        self.reject()
        # 发出信号通知主窗口打开配置界面
        self.ai_generate_requested.emit()

    def get_selected_template(self):
        """获取用户选择的模板ID"""
        template_page = self.page(self.PAGE_TEMPLATE)
        return template_page.get_selected_template()

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


class TemplateSelectionPage(QWizardPage):
    """模板选择页面（第1步）"""

    # 自定义信号
    ai_generate_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """设置页面UI"""
        # 页面标题和说明
        self.setTitle(tr("wizard.template_page.title"))
        self.setSubTitle(tr("wizard.template_page.subtitle"))

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 模板选项组
        self.button_group = QButtonGroup(self)

        # 模板1：工作日模板
        work_radio = QRadioButton(tr("wizard.templates.work_weekday.name"))
        work_radio.setProperty("template_id", "work_weekday")
        radio_font = QFont()
        radio_font.setPointSize(13)  # 设置单选按钮字号为13pt
        work_radio.setFont(radio_font)
        work_description = QLabel(
            tr("wizard.templates.work_weekday.description")
        )
        work_description.setWordWrap(True)
        work_description.setStyleSheet("color: #666666; font-size: 12px; margin-left: 25px; margin-bottom: 15px;")  # 字号11→12px, 间距10→15px

        # 模板2：学生模板
        student_radio = QRadioButton(tr("wizard.templates.student.name"))
        student_radio.setProperty("template_id", "student")
        student_radio.setFont(radio_font)  # 使用相同字体
        student_description = QLabel(
            tr("wizard.templates.student.description")
        )
        student_description.setWordWrap(True)
        student_description.setStyleSheet("color: #666666; font-size: 12px; margin-left: 25px; margin-bottom: 15px;")  # 字号11→12px, 间距10→15px

        # 模板3：自由职业模板
        freelancer_radio = QRadioButton(tr("wizard.templates.freelancer.name"))
        freelancer_radio.setProperty("template_id", "freelancer")
        freelancer_radio.setFont(radio_font)  # 使用相同字体
        freelancer_description = QLabel(
            tr("wizard.templates.freelancer.description")
        )
        freelancer_description.setWordWrap(True)
        freelancer_description.setStyleSheet("color: #666666; font-size: 12px; margin-left: 25px; margin-bottom: 15px;")  # 字号11→12px, 间距10→15px

        # 添加单选按钮到按钮组
        self.button_group.addButton(work_radio, 0)
        self.button_group.addButton(student_radio, 1)
        self.button_group.addButton(freelancer_radio, 2)

        # 默认选中工作日模板
        work_radio.setChecked(True)

        # 添加到布局
        layout.addWidget(work_radio)
        layout.addWidget(work_description)
        layout.addWidget(student_radio)
        layout.addWidget(student_description)
        layout.addWidget(freelancer_radio)
        layout.addWidget(freelancer_description)

        layout.addSpacing(25)  # 增加间距 20→25px

        # 分隔线
        separator = QLabel()
        separator.setFrameStyle(QLabel.Shape.HLine | QLabel.Shadow.Sunken)
        layout.addWidget(separator)

        layout.addSpacing(15)  # 增加间距 10→15px

        # AI生成选项
        ai_label = QLabel(tr("wizard.template_page.ai_option_label"))
        ai_label_font = QFont()
        ai_label_font.setPointSize(13)  # 设置AI标签字号为13pt
        ai_label_font.setBold(True)
        ai_label.setFont(ai_label_font)
        layout.addWidget(ai_label)

        ai_btn = QPushButton(tr("wizard.template_page.ai_button"))
        ai_btn.setFixedHeight(45)  # 增加按钮高度 40→45px
        ai_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)  # 字号13→14px
        ai_btn.clicked.connect(self.on_ai_button_clicked)
        layout.addWidget(ai_btn)

        layout.addSpacing(10)  # AI按钮与提示文字之间的间距

        ai_note = QLabel(tr("wizard.template_page.ai_note"))
        ai_note.setStyleSheet("color: #888888; font-size: 11px;")  # 字号10→11px
        layout.addWidget(ai_note)

        layout.addStretch()

    def get_selected_template(self):
        """获取选中的模板ID"""
        checked_button = self.button_group.checkedButton()
        if checked_button:
            return checked_button.property("template_id")
        return "work_weekday"  # 默认

    def on_ai_button_clicked(self):
        """AI生成按钮点击"""
        self.ai_generate_clicked.emit()


class CompletionPage(QWizardPage):
    """完成页面（第2步）- 优化版本"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """设置页面UI"""
        # 页面标题
        self.setTitle(tr("wizard.complete_page.title"))
        self.setSubTitle(tr("wizard.complete_page.subtitle"))

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # 成功图标 + 祝贺文字
        success_container = QVBoxLayout()
        success_container.setSpacing(15)

        # 成功图标(使用Unicode字符)
        success_icon = QLabel("✓")
        success_icon_font = QFont()
        success_icon_font.setPointSize(48)
        success_icon_font.setBold(True)
        success_icon.setFont(success_icon_font)
        success_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        success_icon.setStyleSheet("color: #10B981;")  # 绿色
        success_container.addWidget(success_icon)

        # 祝贺文字
        congrats = QLabel(tr("wizard.complete_page.congrats"))
        congrats_font = QFont()
        congrats_font.setPointSize(18)
        congrats_font.setBold(True)
        congrats.setFont(congrats_font)
        congrats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        success_container.addWidget(congrats)

        layout.addLayout(success_container)

        layout.addSpacing(10)

        # 配置摘要卡片
        summary_card = QWidget()
        summary_card.setStyleSheet("""
            QWidget {
                background-color: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }
        """)
        summary_layout = QVBoxLayout(summary_card)
        summary_layout.setContentsMargins(20, 15, 20, 15)
        summary_layout.setSpacing(10)

        # 配置摘要标题
        summary_title = QLabel(tr("wizard.complete_page.summary_title"))
        summary_title_font = QFont()
        summary_title_font.setPointSize(14)
        summary_title_font.setBold(True)
        summary_title.setFont(summary_title_font)
        summary_layout.addWidget(summary_title)

        # 模板选择信息（动态更新）
        self.template_label = QLabel()
        template_font = QFont()
        template_font.setPointSize(13)
        self.template_label.setFont(template_font)
        self.template_label.setStyleSheet("color: #6B7280;")
        summary_layout.addWidget(self.template_label)

        # 进度条位置信息
        position_label = QLabel(tr("wizard.complete_page.position_label"))
        position_font = QFont()
        position_font.setPointSize(13)
        position_label.setFont(position_font)
        position_label.setStyleSheet("color: #6B7280;")
        summary_layout.addWidget(position_label)

        layout.addWidget(summary_card)

        layout.addSpacing(5)

        # 快速上手提示(使用更清晰的布局)
        tips_title = QLabel(tr("wizard.complete_page.tips_title"))
        tips_title_font = QFont()
        tips_title_font.setPointSize(14)
        tips_title_font.setBold(True)
        tips_title.setFont(tips_title_font)
        layout.addWidget(tips_title)

        tips = [
            ("🖱️", tr("wizard.tips.right_click_config")),
            ("📊", tr("wizard.tips.tray_menu")),
            ("⌨️", tr("wizard.tips.double_click_toggle")),
            ("🎁", tr("wizard.tips.free_quota"))
        ]

        for icon, tip_text in tips:
            tip_container = QHBoxLayout()
            tip_container.setSpacing(10)

            # 图标
            icon_label = QLabel(icon)
            icon_label.setFixedWidth(30)
            icon_font = QFont()
            icon_font.setPointSize(16)
            icon_label.setFont(icon_font)
            tip_container.addWidget(icon_label)

            # 提示文字
            tip_label = QLabel(tip_text)
            tip_font = QFont()
            tip_font.setPointSize(12)
            tip_label.setFont(tip_font)
            tip_label.setStyleSheet("color: #4B5563;")
            tip_label.setWordWrap(True)
            tip_container.addWidget(tip_label, 1)

            layout.addLayout(tip_container)

        layout.addStretch()

    def initializePage(self):
        """页面初始化时更新摘要"""
        wizard = self.wizard()
        template_id = wizard.get_selected_template()

        template_names = {
            "work_weekday": tr("wizard.templates.work_weekday.name"),
            "student": tr("wizard.templates.student.name"),
            "freelancer": tr("wizard.templates.freelancer.name")
        }

        template_name = template_names.get(template_id, template_id)
        self.template_label.setText(tr("wizard.complete_page.selected_template", template_name=template_name))
