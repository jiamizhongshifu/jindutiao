"""
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
        import_pattern = r'(""".*?"""|'''.*?''')?\n(import.*?\n)+)'
        match = re.search(import_pattern, content, re.DOTALL)
        if match:
            insert_pos = match.end()
            content = content[:insert_pos] + 'from i18n import tr\n' + content[insert_pos:]
        else:
            # Insert at beginning after any initial comments
            lines = content.split('\n')
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('"""'):
                    insert_idx = i
                    break
            lines.insert(insert_idx, 'from i18n import tr')
            content = '\n'.join(lines)

    original = content
    changes = 0

    # Sort replacements by length (longest first) to avoid partial matches
    sorted_replacements = sorted(replacements.items(), key=lambda x: len(x[0]), reverse=True)

    for chinese, key in sorted_replacements:
        # Patterns to match various string formats
        patterns = [
            # QLabel("text")
            (f'QLabel\("{re.escape(chinese)}"\)', f'QLabel(tr("{key}"))'),
            (f"QLabel\('{re.escape(chinese)}'\)", f"QLabel(tr('{key}'))"),

            # QPushButton("text")
            (f'QPushButton\("{re.escape(chinese)}"\)', f'QPushButton(tr("{key}"))'),
            (f"QPushButton\('{re.escape(chinese)}'\)", f"QPushButton(tr('{key}'))"),

            # setText("text")
            (f'\.setText\("{re.escape(chinese)}"\)', f'.setText(tr("{key}"))'),
            (f"\.setText\('{re.escape(chinese)}'\)", f".setText(tr('{key}'))"),

            # setWindowTitle("text")
            (f'\.setWindowTitle\("{re.escape(chinese)}"\)', f'.setWindowTitle(tr("{key}"))'),

            # addItem("text")
            (f'\.addItem\("{re.escape(chinese)}"', f'.addItem(tr("{key}")'),

            # addRow("label:", widget)
            (f'\.addRow\("{re.escape(chinese)}:', f'.addRow(tr("{key}") + ":'),

            # QMessageBox
            (f'QMessageBox\.information\([^,]+,\s*"{re.escape(chinese)}"', f'QMessageBox.information(self, tr("{key}")'),
            (f'QMessageBox\.warning\([^,]+,\s*"{re.escape(chinese)}"', f'QMessageBox.warning(self, tr("{key}")'),

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
    replacements = {'外观设置': 'config.appearance', '任务管理': 'config.tasks', 'AI功能': 'config.ai', '账号管理': 'config.account', '场景设置': 'config.scene', '关于': 'config.about', '语言': 'config.language', '语言设置': 'config.language_setting', '跟随系统': 'config.language_auto', '进度条高度': 'config.bar_height', '进度条位置': 'config.bar_position', '顶部': 'config.position_top', '底部': 'config.position_bottom', '透明度': 'config.transparency', '背景颜色': 'config.background_color', '圆角大小': 'config.corner_radius', '阴影效果': 'config.shadow', '开机自启动': 'config.auto_start', '显示器': 'config.monitor', '确定': 'button.ok', '取消': 'button.cancel', '保存': 'button.save', '应用': 'button.apply', '重置': 'button.reset', '关闭': 'button.close', '删除': 'button.delete', '添加': 'button.add', '刷新': 'button.refresh', '预览': 'button.preview', '生成': 'button.generate', '登录': 'account.login', '退出登录': 'account.logout', '注册': 'account.register', '升级会员': 'button.upgrade', '保存成功': 'message.save_success', '保存失败': 'message.save_failed', '提示': 'message.info', '警告': 'message.warning', '错误': 'message.error', '成功': 'message.success', '任务名称': 'tasks.name', '开始时间': 'tasks.start_time', '结束时间': 'tasks.end_time', '颜色': 'tasks.color', '添加任务': 'tasks.add_task', '编辑任务': 'tasks.edit_task', '删除任务': 'tasks.delete_task', '模板': 'tasks.template', '加载模板': 'tasks.load_template', '保存为模板': 'tasks.save_as_template', '主题配色': 'tasks.theme', '应用主题': 'tasks.apply_theme', '未登录': 'account.not_logged_in', '已登录': 'account.logged_in_as', '邮箱': 'account.email', '密码': 'account.password', '验证码': 'account.verification_code', '发送验证码': 'account.send_code', 'AI生成任务': 'ai.generate_tasks', 'AI配色推荐': 'ai.generate_theme', 'AI正在生成中...': 'ai.generating', '剩余配额': 'ai.quota_remaining', '今日配额已用完': 'ai.quota_exhausted', '会员中心': 'membership.title', '免费版': 'membership.free', '月度会员': 'membership.pro_monthly', '年度会员': 'membership.pro_yearly', '终身会员': 'membership.lifetime', '当前套餐': 'membership.current_plan'}

    print("=== Internationalizing config_gui.py ===\n")
    replace_in_file('config_gui.py', replacements)
    print("\nDone! Review config_gui.py.i18n before replacing the original file.")
