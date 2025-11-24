"""
Patch ConfigManager main UI with i18n
国际化 ConfigManager 的主窗口标题和标签页
"""

def patch_config_manager_main_ui():
    # Read the file
    with open('config_gui.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Replacements to make (line_num is 1-based)
    replacements = [
        # Line 1315: Window title
        (1315, "        self.setWindowTitle(f'{VERSION_STRING_ZH} - 配置管理器')",
               "        self.setWindowTitle(tr('config.config_2', VERSION_STRING_ZH=VERSION_STRING_ZH))"),

        # Line 1358: Tab 1 - Appearance
        (1358, '        tabs.addTab(self.create_config_tab(), "🎨 外观配置")',
               '        tabs.addTab(self.create_config_tab(), "🎨 " + tr(\'config.appearance\'))'),

        # Line 1359: Tab 2 - Tasks
        (1359, '        tabs.addTab(self.create_tasks_tab(), "📋 任务管理")',
               '        tabs.addTab(self.create_tasks_tab(), "📋 " + tr(\'config.tasks\'))'),

        # Line 1363: Tab 3 - Scene (placeholder)
        (1363, '        tabs.addTab(QWidget(), "🎬 场景设置")  # 占位widget',
               '        tabs.addTab(QWidget(), "🎬 " + tr(\'config.scene\'))  # 占位widget'),

        # Line 1367: Tab 4 - Notification (placeholder)
        (1367, '        tabs.addTab(QWidget(), "🔔 通知设置")  # 占位widget',
               '        tabs.addTab(QWidget(), "🔔 " + tr(\'config.notification_settings\'))  # 占位widget'),

        # Line 1371: Tab 5 - Account (placeholder)
        (1371, '        tabs.addTab(QWidget(), "👤 个人中心")  # 占位widget',
               '        tabs.addTab(QWidget(), "👤 " + tr(\'config.account\'))  # 占位widget'),
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
                print(f'[OK] Line {line_num}: Window title' if line_num == 1315 else f'[OK] Line {line_num}: Tab {changes_made-1 if line_num > 1315 else "title"}')
            else:
                print(f'[SKIP] Line {line_num}: Content mismatch')
                print(f'  Expected: {old_text[:60]}...')
                print(f'  Found:    {current_line[:60]}...')

    # Write back
    with open('config_gui.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print(f'\n[SUCCESS] Made {changes_made} changes to config_gui.py')
    print('ConfigManager main UI (window title + tabs) is now internationalized!')

    return changes_made

if __name__ == '__main__':
    count = patch_config_manager_main_ui()
    if count == 6:
        print('\n[OK] All expected changes completed successfully')
    else:
        print(f'\n[WARNING] Expected 6 changes, but made {count}')
