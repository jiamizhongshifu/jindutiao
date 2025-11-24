"""
Apply i18n to create_tasks_tab() method
Replaces all hardcoded Chinese strings with tr() function calls
"""

def apply_i18n():
    with open('config_gui.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Open log file for detailed output
    log = open('tasks_i18n_apply_log.txt', 'w', encoding='utf-8')

    # Replacements: (line_number (1-based), old_text, new_text)
    replacements = [
        # Group titles
        (1932, '        ai_group = QGroupBox("🤖 AI智能规划")',
               '        ai_group = QGroupBox(tr("tasks.ai_planning_title"))'),

        (2026, '        theme_group = QGroupBox("🎨 预设主题配色")',
               '        theme_group = QGroupBox(tr("tasks.preset_themes_title"))'),

        (2060, '        preset_group = QGroupBox("📋 预设模板")',
               '        preset_group = QGroupBox(tr("tasks.preset_templates_title"))'),

        (2090, '        custom_group = QGroupBox("💾 我的模板")',
               '        custom_group = QGroupBox(tr("tasks.my_templates_title"))'),

        (2129, '        timeline_group = QGroupBox("🎨 可视化时间轴编辑器")',
               '        timeline_group = QGroupBox(tr("tasks.visual_timeline_editor_title"))'),

        (2199, '        schedule_group = QGroupBox("📅 模板自动应用管理")',
               '        schedule_group = QGroupBox(tr("tasks.template_auto_apply_title"))'),

        (2238, '        test_group = QGroupBox("🔍 测试日期")',
               '        test_group = QGroupBox(tr("tasks.test_date_title"))'),

        # Hint/help text
        (1937, '        ai_hint = QLabel("💡 用自然语言描述您的计划,AI将自动生成任务时间表")',
               '        ai_hint = QLabel(tr("tasks.ai_planning_hint"))'),

        (2021, '        table_hint = QLabel("双击表格单元格可以编辑任务内容")',
               '        table_hint = QLabel(tr("tasks.double_click_to_edit_hint"))'),

        (2133, '        timeline_hint = QLabel("💡 提示：拖动色块边缘可调整任务时长")',
               '        timeline_hint = QLabel(tr("tasks.drag_to_adjust_hint"))'),

        (2204, '        schedule_hint = QLabel("💡 为每个模板设置自动应用的日期规则，到了指定时间会自动加载对应模板")',
               '        schedule_hint = QLabel(tr("tasks.auto_apply_hint"))'),

        (2239, '        test_hint = QLabel("测试指定日期会匹配到哪个模板")',
               '        test_hint = QLabel(tr("tasks.test_date_hint"))'),

        # Labels
        (1943, '        input_label = QLabel("描述您的计划:")',
               '        input_label = QLabel(tr("tasks.describe_plan_label"))'),

        (2030, '        theme_label = QLabel("选择主题:")',
               '        theme_label = QLabel(tr("tasks.select_theme_label"))'),

        (2045, '        preview_label = QLabel("配色预览:")',
               '        preview_label = QLabel(tr("tasks.color_preview_label"))'),

        (2064, '        quick_label = QLabel("快速加载:")',
               '        quick_label = QLabel(tr("tasks.quick_load_label"))'),

        (2094, '        custom_label = QLabel("选择模板:")',
               '        custom_label = QLabel(tr("tasks.select_template_label"))'),

        (1983, '        self.quota_label = QLabel("配额状态: 加载中...")',
               '        self.quota_label = QLabel(tr("tasks.quota_status_loading"))'),

        (2079, '        self.template_status_label.setText("模板加载中...")',
               '        self.template_status_label.setText(tr("tasks.template_loading"))'),

        # Placeholder text
        (1949, '        self.ai_input.setPlaceholderText("例如: 明天9点开会1小时,然后写代码到下午5点,中午12点休息1小时,晚上6点健身...")',
               '        self.ai_input.setPlaceholderText(tr("tasks.plan_placeholder"))'),

        # Button text
        (1960, '        self.generate_btn = QPushButton("✨ 智能生成任务")',
               '        self.generate_btn = QPushButton(tr("tasks.btn_generate_tasks"))'),

        (1988, '        refresh_btn = QPushButton("🔄 刷新配额")',
               '        refresh_btn = QPushButton(tr("tasks.btn_refresh_quota"))'),

        (2104, '        load_btn = QPushButton("📂 加载")',
               '        load_btn = QPushButton(tr("tasks.btn_load"))'),

        (2112, '        delete_btn = QPushButton("🗑️ 删除")',
               '        delete_btn = QPushButton(tr("tasks.btn_delete"))'),

        (2170, '        add_task_btn = QPushButton("➕ 添加任务")',
               '        add_task_btn = QPushButton(tr("tasks.btn_add_task"))'),

        (2175, '        save_template_btn = QPushButton("💾 保存为模板")',
               '        save_template_btn = QPushButton(tr("tasks.btn_save_as_template"))'),

        (2180, '        load_template_btn = QPushButton("📂 加载自定义模板")',
               '        load_template_btn = QPushButton(tr("tasks.btn_load_custom_template"))'),

        (2185, '        clear_btn = QPushButton("🗑️ 清空所有任务")',
               '        clear_btn = QPushButton(tr("tasks.btn_clear_all_tasks"))'),

        (2232, '        add_rule_btn = QPushButton("➕ 添加规则")',
               '        add_rule_btn = QPushButton(tr("tasks.btn_add_rule"))'),

        # Button tooltips
        (2105, '        load_btn.setToolTip("加载选中的自定义模板")',
               '        load_btn.setToolTip(tr("tasks.load_template_tooltip"))'),

        (2113, '        delete_btn.setToolTip("删除选中的自定义模板")',
               '        delete_btn.setToolTip(tr("tasks.delete_template_tooltip"))'),

        # Status messages
        (2015, '        self.quota_label.setText("⏳ 正在连接云服务（可能需要10-15秒）...")',
               '        self.quota_label.setText(tr("tasks.connecting_cloud_service"))'),

        # Table column headers (line 2155 - single line)
        (2155, '        self.tasks_table.setHorizontalHeaderLabels(["开始时间", "结束时间", "任务名称", "背景颜色", "文字颜色", "操作"])',
               '        self.tasks_table.setHorizontalHeaderLabels([tr("tasks.column_start_time"), tr("tasks.column_end_time"), tr("tasks.column_task_name"), tr("tasks.column_bg_color"), tr("tasks.column_text_color"), tr("tasks.column_actions")])'),
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
                log.write(f'[OK] Line {line_num}\n')
                print(f'[OK] Line {line_num}')
            else:
                log.write(f'[SKIP] Line {line_num}: Content mismatch\n')
                log.write(f'  Expected: {old_text}\n')
                log.write(f'  Found:    {current_line}\n\n')
                print(f'[SKIP] Line {line_num}')

    # Write back
    with open('config_gui.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)

    log.write(f'\n[SUCCESS] Made {changes_made} changes\n')
    log.close()

    print(f'\n[SUCCESS] Made {changes_made} changes')
    print('Details written to tasks_i18n_apply_log.txt')
    return changes_made

if __name__ == '__main__':
    count = apply_i18n()
    print(f'\nTotal changes: {count}')
