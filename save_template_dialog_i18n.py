"""
SaveTemplateDialog - Internationalized version
手动国际化的SaveTemplateDialog类,用于测试和参考
"""

class SaveTemplateDialog(QDialog):
    """保存模板对话框 - 智能适应有无历史模板的情况"""

    def __init__(self, existing_templates, parent=None):
        """
        初始化对话框

        Args:
            existing_templates: 现有模板列表 [{"name": "模板名", ...}, ...]
            parent: 父窗口
        """
        super().__init__(parent)
        self.existing_templates = existing_templates
        self.template_name = None
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(tr('dialog.save_template_title'))
        self.setMinimumWidth(400)

        layout = QVBoxLayout()

        # 提示文本
        if self.existing_templates:
            hint_label = QLabel(tr('dialog.select_or_new'))
        else:
            hint_label = QLabel(tr('dialog.enter_name'))

        layout.addWidget(hint_label)

        # 根据是否有历史模板决定使用下拉框还是输入框
        if self.existing_templates:
            # 有历史模板,使用可编辑的下拉框
            self.input_widget = QComboBox()
            self.input_widget.setEditable(True)
            self.input_widget.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

            # 添加历史模板到下拉框
            for template in self.existing_templates:
                template_name = template.get('name', '')
                task_count = template.get('task_count', 0)
                # Use tr() with parameters for dynamic text
                display_text = tr('tasks.text_3308', template_name=template_name, task_count=task_count)
                self.input_widget.addItem(display_text, template_name)

            # 设置当前文本为空,引导用户选择或输入
            self.input_widget.setCurrentIndex(-1)
            self.input_widget.setPlaceholderText(tr('tasks.template_4'))
        else:
            # 无历史模板,使用普通输入框
            self.input_widget = QLineEdit()
            self.input_widget.setPlaceholderText(tr('tasks.template_5'))

        layout.addWidget(self.input_widget)

        # 提示信息
        if self.existing_templates:
            # Multi-line hint - combine three separate tr() calls
            hint_text = (tr('message.text_8425') + "\n" +
                        tr('tasks.template_6') + "\n" +
                        tr('tasks.template_7'))
            tip_label = QLabel(hint_text)
            tip_label.setStyleSheet(StyleManager.label_hint())
            layout.addWidget(tip_label)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def accept(self):
        """确定按钮点击"""
        # 获取模板名称
        if isinstance(self.input_widget, QComboBox):
            # 下拉框:可能是选择的历史模板,也可能是手动输入的新名称
            current_text = self.input_widget.currentText()

            # 检查是否选择了历史模板(通过匹配显示文本)
            current_data = self.input_widget.currentData()
            if current_data:
                # 选择了历史模板
                self.template_name = current_data
            else:
                # 手动输入的新名称
                # 需要去掉可能的任务数量后缀
                template_name = current_text.strip()
                # 如果输入的恰好和某个显示文本一致,提取实际名称
                for i in range(self.input_widget.count()):
                    if self.input_widget.itemText(i) == template_name:
                        template_name = self.input_widget.itemData(i)
                        break
                self.template_name = template_name
        else:
            # 输入框
            self.template_name = self.input_widget.text().strip()

        # 验证名称不为空
        if not self.template_name:
            QMessageBox.warning(self, tr('message.input_error'), tr('dialog.template_name_empty'))
            return

        super().accept()

    def get_template_name(self):
        """获取用户输入/选择的模板名称"""
        return self.template_name
