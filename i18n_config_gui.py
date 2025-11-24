"""
Internationalize config_gui.py - Phase 1
Focus on most visible UI elements first
"""
import json
import re


# Extended translation mappings for config_gui.py
CONFIG_GUI_TRANSLATIONS = {
    # Tab titles
    '外观设置': 'config.appearance',
    '任务管理': 'config.tasks',
    'AI功能': 'config.ai',
    '账号管理': 'config.account',
    '场景设置': 'config.scene',
    '关于': 'config.about',

    # Common labels (already in i18n)
    '语言': 'config.language',
    '语言设置': 'config.language_setting',
    '跟随系统': 'config.language_auto',
    '进度条高度': 'config.bar_height',
    '进度条位置': 'config.bar_position',
    '顶部': 'config.position_top',
    '底部': 'config.position_bottom',
    '透明度': 'config.transparency',
    '背景颜色': 'config.background_color',
    '圆角大小': 'config.corner_radius',
    '阴影效果': 'config.shadow',
    '开机自启动': 'config.auto_start',
    '显示器': 'config.monitor',

    # Buttons (already in i18n)
    '确定': 'button.ok',
    '取消': 'button.cancel',
    '保存': 'button.save',
    '应用': 'button.apply',
    '重置': 'button.reset',
    '关闭': 'button.close',
    '删除': 'button.delete',
    '添加': 'button.add',
    '刷新': 'button.refresh',
    '预览': 'button.preview',
    '生成': 'button.generate',
    '登录': 'account.login',
    '退出登录': 'account.logout',
    '注册': 'account.register',
    '升级会员': 'button.upgrade',

    # Messages (already in i18n)
    '保存成功': 'message.save_success',
    '保存失败': 'message.save_failed',
    '提示': 'message.info',
    '警告': 'message.warning',
    '错误': 'message.error',
    '成功': 'message.success',

    # Task related
    '任务名称': 'tasks.name',
    '开始时间': 'tasks.start_time',
    '结束时间': 'tasks.end_time',
    '颜色': 'tasks.color',
    '添加任务': 'tasks.add_task',
    '编辑任务': 'tasks.edit_task',
    '删除任务': 'tasks.delete_task',
    '模板': 'tasks.template',
    '加载模板': 'tasks.load_template',
    '保存为模板': 'tasks.save_as_template',
    '主题配色': 'tasks.theme',
    '应用主题': 'tasks.apply_theme',

    # Account
    '未登录': 'account.not_logged_in',
    '已登录': 'account.logged_in_as',
    '邮箱': 'account.email',
    '密码': 'account.password',
    '验证码': 'account.verification_code',
    '发送验证码': 'account.send_code',

    # AI
    'AI生成任务': 'ai.generate_tasks',
    'AI配色推荐': 'ai.generate_theme',
    'AI正在生成中...': 'ai.generating',
    '剩余配额': 'ai.quota_remaining',
    '今日配额已用完': 'ai.quota_exhausted',

    # Membership
    '会员中心': 'membership.title',
    '免费版': 'membership.free',
    '月度会员': 'membership.pro_monthly',
    '年度会员': 'membership.pro_yearly',
    '终身会员': 'membership.lifetime',
    '当前套餐': 'membership.current_plan',
}


# Additional translations needed for config_gui.py
ADDITIONAL_TRANSLATIONS_ZH = {
    'config': {
        # More specific config items that aren't in the current i18n
        'theme_light': '浅色主题',
        'theme_dark': '深色主题',
        'marker_settings': '时间标记设置',
        'marker_type': '标记类型',
        'marker_line': '线条',
        'marker_image': '图片',
        'marker_gif': 'GIF动画',
        'marker_size': '标记大小',
        'marker_speed': '动画速度',
        'marker_offset': '标记偏移',
        'x_offset': 'X轴偏移',
        'y_offset': 'Y轴偏移',
        'update_interval': '更新间隔',
        'milliseconds': '毫秒',
        'pixels': '像素',
        'percent': '百分比',
    },
    'tasks': {
        'time_format': '时间格式',
        'color_theme': '配色主题',
        'task_list': '任务列表',
        'no_tasks': '暂无任务',
        'task_editor': '任务编辑器',
    },
    'ai': {
        'input_placeholder': '请描述你的日程安排，例如：我是程序员，朝九晚六工作，中午休息1小时...',
        'quota_info': '剩余配额: {count}次',
        'upgrade_hint': '升级会员获取更多配额',
    },
    'dialog': {
        'confirm_delete': '确定要删除吗？',
        'confirm_reset': '确定要重置吗？',
        'unsaved_changes': '有未保存的更改',
        'save_before_exit': '是否在退出前保存更改？',
    }
}

ADDITIONAL_TRANSLATIONS_EN = {
    'config': {
        'theme_light': 'Light Theme',
        'theme_dark': 'Dark Theme',
        'marker_settings': 'Time Marker Settings',
        'marker_type': 'Marker Type',
        'marker_line': 'Line',
        'marker_image': 'Image',
        'marker_gif': 'GIF Animation',
        'marker_size': 'Marker Size',
        'marker_speed': 'Animation Speed',
        'marker_offset': 'Marker Offset',
        'x_offset': 'X Offset',
        'y_offset': 'Y Offset',
        'update_interval': 'Update Interval',
        'milliseconds': 'milliseconds',
        'pixels': 'pixels',
        'percent': 'percent',
    },
    'tasks': {
        'time_format': 'Time Format',
        'color_theme': 'Color Theme',
        'task_list': 'Task List',
        'no_tasks': 'No tasks',
        'task_editor': 'Task Editor',
    },
    'ai': {
        'input_placeholder': 'Describe your daily schedule, e.g., I\'m a programmer working 9 to 6, with 1 hour lunch break...',
        'quota_info': 'Remaining quota: {count}',
        'upgrade_hint': 'Upgrade for more quota',
    },
    'dialog': {
        'confirm_delete': 'Are you sure you want to delete?',
        'confirm_reset': 'Are you sure you want to reset?',
        'unsaved_changes': 'There are unsaved changes',
        'save_before_exit': 'Save changes before exit?',
    }
}


def merge_translations(base, additions):
    """Deep merge two dictionaries"""
    result = base.copy()
    for key, value in additions.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_translations(result[key], value)
        else:
            result[key] = value
    return result


def update_translation_files():
    """Update i18n JSON files with additional translations"""
    print("=== Updating Translation Files ===\n")

    # Load existing
    with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
        zh_cn = json.load(f)
    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    print(f"Loaded zh_CN: {sum(len(v) if isinstance(v, dict) else 1 for v in zh_cn.values())} keys")
    print(f"Loaded en_US: {sum(len(v) if isinstance(v, dict) else 1 for v in en_us.values())} keys\n")

    # Merge new translations
    zh_cn = merge_translations(zh_cn, ADDITIONAL_TRANSLATIONS_ZH)
    en_us = merge_translations(en_us, ADDITIONAL_TRANSLATIONS_EN)

    # Save updated files
    with open('i18n/zh_CN.json', 'w', encoding='utf-8') as f:
        json.dump(zh_cn, f, ensure_ascii=False, indent=2)
    with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
        json.dump(en_us, f, ensure_ascii=False, indent=2)

    print("Translation files updated!\n")
    print(f"New zh_CN: {sum(len(v) if isinstance(v, dict) else 1 for v in zh_cn.values())} keys")
    print(f"New en_US: {sum(len(v) if isinstance(v, dict) else 1 for v in en_us.values())} keys\n")


def generate_replacement_script():
    """Generate a Python script to replace hardcoded strings in config_gui.py"""

    script = '''"""
Auto-generated script to replace hardcoded Chinese strings with tr() calls in config_gui.py
Run this after backing up the original file
"""
import re


def replace_in_file(filename, replacements):
    """Replace strings in file based on mapping"""
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add import if not exists
    if 'from i18n import tr' not in content:
        # Find the import section (after initial comments/docstring)
        import_pattern = r'(""".*?"""|\'\'\'.*?\'\'\')?\\n(import.*?\\n)+)'
        match = re.search(import_pattern, content, re.DOTALL)
        if match:
            insert_pos = match.end()
            content = content[:insert_pos] + 'from i18n import tr\\n' + content[insert_pos:]
        else:
            # Insert at beginning after any initial comments
            lines = content.split('\\n')
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('"""'):
                    insert_idx = i
                    break
            lines.insert(insert_idx, 'from i18n import tr')
            content = '\\n'.join(lines)

    original = content
    changes = 0

    # Sort replacements by length (longest first) to avoid partial matches
    sorted_replacements = sorted(replacements.items(), key=lambda x: len(x[0]), reverse=True)

    for chinese, key in sorted_replacements:
        # Patterns to match various string formats
        patterns = [
            # QLabel("text")
            (f'QLabel\\("{re.escape(chinese)}"\\)', f'QLabel(tr("{key}"))'),
            (f"QLabel\\('{re.escape(chinese)}'\\)", f"QLabel(tr('{key}'))"),

            # QPushButton("text")
            (f'QPushButton\\("{re.escape(chinese)}"\\)', f'QPushButton(tr("{key}"))'),
            (f"QPushButton\\('{re.escape(chinese)}'\\)", f"QPushButton(tr('{key}'))"),

            # setText("text")
            (f'\\.setText\\("{re.escape(chinese)}"\\)', f'.setText(tr("{key}"))'),
            (f"\\.setText\\('{re.escape(chinese)}'\\)", f".setText(tr('{key}'))"),

            # setWindowTitle("text")
            (f'\\.setWindowTitle\\("{re.escape(chinese)}"\\)', f'.setWindowTitle(tr("{key}"))'),

            # addItem("text")
            (f'\\.addItem\\("{re.escape(chinese)}"', f'.addItem(tr("{key}")'),

            # addRow("label:", widget)
            (f'\\.addRow\\("{re.escape(chinese)}:', f'.addRow(tr("{key}") + ":'),

            # QMessageBox
            (f'QMessageBox\\.information\\([^,]+,\\s*"{re.escape(chinese)}"', f'QMessageBox.information(self, tr("{key}")'),
            (f'QMessageBox\\.warning\\([^,]+,\\s*"{re.escape(chinese)}"', f'QMessageBox.warning(self, tr("{key}")'),

            # Generic string replacement (be careful with this)
            (f'"{re.escape(chinese)}"', f'tr("{key}")'),
        ]

        for pattern, replacement in patterns:
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                changes += 1
                content = new_content

    if content != original:
        with open(filename + '.i18n', 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Created internationalized version: {filename}.i18n")
        print(f"Total replacements: {changes}")
        return True
    else:
        print("No changes needed")
        return False


if __name__ == '__main__':
    replacements = ''' + repr(CONFIG_GUI_TRANSLATIONS) + '''

    print("=== Internationalizing config_gui.py ===\\n")
    replace_in_file('config_gui.py', replacements)
    print("\\nDone! Review config_gui.py.i18n before replacing the original file.")
'''

    with open('auto_i18n_config_gui.py', 'w', encoding='utf-8') as f:
        f.write(script)

    print("Generated replacement script: auto_i18n_config_gui.py\n")


if __name__ == '__main__':
    # Step 1: Update translation files
    update_translation_files()

    # Step 2: Generate replacement script
    generate_replacement_script()

    print("=== Next Steps ===")
    print("1. Review the updated translation files in i18n/")
    print("2. Run: python auto_i18n_config_gui.py")
    print("3. Review the generated config_gui.py.i18n")
    print("4. If it looks good, backup and replace the original")
