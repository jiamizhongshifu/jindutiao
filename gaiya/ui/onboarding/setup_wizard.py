"""配置向导 - 2步快速设置"""

from PySide6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QLabel,
    QRadioButton, QPushButton, QButtonGroup,
    QHBoxLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


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
        self.setWindowTitle("快速配置")
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
        self.setTitle("选择任务模板")
        self.setSubTitle("为你推荐3个热门模板，选择最适合的一个即可快速开始")

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 模板选项组
        self.button_group = QButtonGroup(self)

        # 模板1：工作日模板
        work_radio = QRadioButton("📊 工作日模板")
        work_radio.setProperty("template_id", "work_weekday")
        radio_font = QFont()
        radio_font.setPointSize(13)  # 设置单选按钮字号为13pt
        work_radio.setFont(radio_font)
        work_description = QLabel(
            "适合上班族。包含：通勤、会议、工作、午休、晚餐、学习等典型工作日任务。"
        )
        work_description.setWordWrap(True)
        work_description.setStyleSheet("color: #666666; font-size: 12px; margin-left: 25px; margin-bottom: 15px;")  # 字号11→12px, 间距10→15px

        # 模板2：学生模板
        student_radio = QRadioButton("🎓 学生模板")
        student_radio.setProperty("template_id", "student")
        student_radio.setFont(radio_font)  # 使用相同字体
        student_description = QLabel(
            "适合学生党。包含：早读、上课、自习、运动、社团活动等校园生活任务。"
        )
        student_description.setWordWrap(True)
        student_description.setStyleSheet("color: #666666; font-size: 12px; margin-left: 25px; margin-bottom: 15px;")  # 字号11→12px, 间距10→15px

        # 模板3：自由职业模板
        freelancer_radio = QRadioButton("💼 自由职业模板")
        freelancer_radio.setProperty("template_id", "freelancer")
        freelancer_radio.setFont(radio_font)  # 使用相同字体
        freelancer_description = QLabel(
            "适合自由工作者。包含：客户沟通、项目开发、创作时间、休息等灵活时间安排。"
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
        ai_label = QLabel("或者，让AI根据你的需求智能生成任务：")
        ai_label_font = QFont()
        ai_label_font.setPointSize(13)  # 设置AI标签字号为13pt
        ai_label_font.setBold(True)
        ai_label.setFont(ai_label_font)
        layout.addWidget(ai_label)

        ai_btn = QPushButton("🤖 AI智能生成任务")
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

        ai_note = QLabel("💡 点击后将关闭向导，打开配置界面使用AI生成")
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
    """完成页面（第2步）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """设置页面UI"""
        # 页面标题
        self.setTitle("配置完成！🎉")
        self.setSubTitle("你已成功完成基础配置，现在可以开始使用 GaiYa 了")

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 配置摘要
        summary_label = QLabel("✅ 已完成的配置：")
        summary_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(summary_label)

        layout.addSpacing(10)

        # 模板选择信息（动态更新）
        self.template_label = QLabel()
        template_font = QFont()
        template_font.setPointSize(13)
        self.template_label.setFont(template_font)
        self.template_label.setStyleSheet("color: #333333; padding: 5px 0;")  # 使用主色 #333333
        layout.addWidget(self.template_label)

        # 进度条位置信息
        position_label = QLabel("进度条位置: 屏幕底部（固定）")
        position_font = QFont()
        position_font.setPointSize(13)
        position_label.setFont(position_font)
        position_label.setStyleSheet("color: #333333; padding: 5px 0;")  # 使用主色 #333333
        layout.addWidget(position_label)

        layout.addSpacing(15)

        # 下一步建议标题
        suggestions_title = QLabel("下一步建议:")
        suggestions_font = QFont()
        suggestions_font.setPointSize(13)
        suggestions_font.setBold(True)
        suggestions_title.setFont(suggestions_font)
        suggestions_title.setStyleSheet("color: #333333; padding: 5px 0;")  # 使用主色 #333333
        layout.addWidget(suggestions_title)

        # 建议列表
        suggestions = [
            "• 打开配置界面自定义任务时间和颜色",
            "• 设置任务提醒时间",
            "• 选择喜欢的主题配色"
        ]

        for suggestion in suggestions:
            suggestion_label = QLabel(suggestion)
            suggestion_font = QFont()
            suggestion_font.setPointSize(12)
            suggestion_label.setFont(suggestion_font)
            suggestion_label.setStyleSheet("color: #999999; padding: 3px 0; margin-left: 15px;")  # 使用浅灰色 #999999
            layout.addWidget(suggestion_label)

        # 快速上手提示
        tips_label = QLabel("💡 快速上手提示：")
        tips_label.setStyleSheet("font-weight: bold; font-size: 14px;")  # 字号12→14px
        layout.addWidget(tips_label)

        tips = [
            "• 右键点击进度条可以打开配置界面",
            "• 系统托盘图标右键菜单提供快捷操作",
            "• 支持快捷键：双击隐藏/显示进度条",
            "• 免费用户每天有3次AI任务规划配额"
        ]

        for tip in tips:
            tip_label = QLabel(tip)
            tip_font = QFont()
            tip_font.setPointSize(12)  # 设置提示条目字号为12pt
            tip_label.setFont(tip_font)
            tip_label.setStyleSheet("color: #666666; padding: 3px 0;")  # 使用辅助色 #666666
            layout.addWidget(tip_label)

        layout.addStretch()

    def initializePage(self):
        """页面初始化时更新摘要"""
        wizard = self.wizard()
        template_id = wizard.get_selected_template()

        template_names = {
            "work_weekday": "工作日模板 📊",
            "student": "学生模板 🎓",
            "freelancer": "自由职业模板 💼"
        }

        template_name = template_names.get(template_id, template_id)
        self.template_label.setText(f"已选择任务模板: {template_name}")
