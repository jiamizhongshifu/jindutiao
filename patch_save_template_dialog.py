"""
Patch SaveTemplateDialog with i18n
手动精确替换SaveTemplateDialog类中的硬编码字符串
"""

def patch_save_template_dialog():
    # Read the file
    with open('config_gui.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Replacements to make (line_num is 1-based)
    replacements = [
        # Line 76: Window title
        (76, '        self.setWindowTitle("保存为模板")',
             "        self.setWindowTitle(tr('dialog.save_template_title'))"),

        # Line 83: Hint label (with templates)
        (83, '            hint_label = QLabel("选择要覆盖的模板或输入新的模板名称:")',
             "            hint_label = QLabel(tr('dialog.select_or_new'))"),

        # Line 85: Hint label (no templates)
        (85, '            hint_label = QLabel("请输入模板名称:")',
             "            hint_label = QLabel(tr('dialog.enter_name'))"),

        # Line 100: F-string with task count
        (100, '                display_text = f"{template_name} ({task_count}个任务)"',
              '                display_text = tr(\'tasks.text_3308\', template_name=template_name, task_count=task_count)'),

        # Line 105: Placeholder for combobox
        (105, '            self.input_widget.setPlaceholderText("选择历史模板或输入新名称")',
              "            self.input_widget.setPlaceholderText(tr('tasks.template_4'))"),

        # Line 109: Placeholder for line edit
        (109, '            self.input_widget.setPlaceholderText("例如: 工作日模板")',
              "            self.input_widget.setPlaceholderText(tr('tasks.template_5'))"),

        # Line 161: Error message
        (161, '            QMessageBox.warning(self, "输入错误", "模板名称不能为空!")',
              "            QMessageBox.warning(self, tr('message.input_error'), tr('dialog.template_name_empty'))"),
    ]

    # Apply replacements
    changes_made = 0
    for line_num, old_text, new_text in replacements:
        idx = line_num - 1  # Convert to 0-based
        if idx < len(lines):
            current_line = lines[idx].rstrip('\n')
            if current_line == old_text:
                lines[idx] = new_text + '\n'
                changes_made += 1
                print(f'[OK] Line {line_num}: {old_text[:50]}...')
            else:
                print(f'[SKIP] Line {line_num}: Content mismatch')
                print(f'  Expected: {old_text[:60]}')
                print(f'  Found:    {current_line[:60]}')

    # Handle multi-line tip label (lines 115-119)
    # Original:
    #     tip_label = QLabel(
    #         "💡 提示:\n"
    #         "• 选择历史模板将直接覆盖该模板\n"
    #         "• 输入新名称将创建新的模板"
    #     )
    # New: Use + to concatenate tr() calls
    if len(lines) > 118:
        if ('tip_label = QLabel(' in lines[114] and
            '"💡 提示' in lines[115]):
            # Replace lines 115-118
            lines[115] = '                tr(\'message.text_8425\') + "\\n" +\n'
            lines[116] = '                tr(\'tasks.template_6\') + "\\n" +\n'
            lines[117] = '                tr(\'tasks.template_7\')\n'
            lines[118] = '            )\n'
            changes_made += 1
            print('[OK] Lines 115-118: Multi-line tip label')

    # Write back
    with open('config_gui.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print(f'\n[SUCCESS] Made {changes_made} changes to config_gui.py')
    print('SaveTemplateDialog is now internationalized!')

if __name__ == '__main__':
    patch_save_template_dialog()
