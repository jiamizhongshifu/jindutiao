#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply high priority i18n translations to config_gui.py"""

import re
import sys
import io
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Replacement mappings (line number -> replacement)
REPLACEMENTS = [
    # Tooltips
    {
        'line': 2082,
        'old': '"加载选中的自定义模板"',
        'new': 'self.i18n.t("config.tooltips.load_custom_template")',
        'description': 'Tooltip: Load custom template'
    },
    {
        'line': 2090,
        'old': '"删除选中的自定义模板"',
        'new': 'self.i18n.t("config.tooltips.delete_custom_template")',
        'description': 'Tooltip: Delete custom template'
    },
    {
        'line': 2216,
        'old': '"测试指定日期会匹配到哪个模板"',
        'new': 'self.i18n.t("config.tooltips.test_date_match")',
        'description': 'Tooltip: Test date match'
    },

    # Template task count display
    {
        'line': 87,
        'old': 'f"{template_name} ({task_count}个任务)"',
        'new': 'self.i18n.t("config.templates.task_count", template_name=template_name, task_count=task_count)',
        'description': 'Template task count display'
    },

    # Overwrite warning
    {
        'line': 104,
        'old': '"• 选择历史模板将直接覆盖该模板\\n"',
        'new': 'self.i18n.t("config.dialogs.overwrite_template_warning")',
        'description': 'Overwrite template warning'
    },

    # Date match result
    {
        'line': 1106,
        'old': 'f"✅ 该日期会自动加载模板: {template_name}"',
        'new': 'self.i18n.t("config.schedule.date_will_load_template", template_name=template_name)',
        'description': 'Date will load template message'
    },

    # Conflict warning
    {
        'line': 1110,
        'old': 'f"⚠️ 警告：该日期有 {len(all_matched)} 个模板规则冲突！"',
        'new': 'self.i18n.t("config.schedule.date_conflict_warning", conflict_count=len(all_matched))',
        'description': 'Date conflict warning'
    },

    # Theme applied
    {
        'line': 2301,
        'old': 'f"已应用主题: {self.theme_manager.get_current_theme().get(\'name\', \'Unknown\')}"',
        'new': 'self.i18n.t("config.dialogs.theme_applied", theme_name=self.theme_manager.get_current_theme().get(\'name\', \'Unknown\'))',
        'description': 'Theme applied message'
    },

    # Welcome back
    {
        'line': 3255,
        'old': 'f"欢迎回来，{user_info.get(\'email\', \'用户\')}！\\n\\n"',
        'new': 'self.i18n.t("config.membership.welcome_back", user_email=user_info.get(\'email\', \'User\')) + "\\n"',
        'description': 'Welcome back message'
    },

    # Payment success
    {
        'line': 5033,
        'old': '"支付已完成！\\n您的会员权益已激活。\\n\\n请重新启动应用以生效。"',
        'new': 'self.i18n.t("config.membership.payment_success_restart")',
        'description': 'Payment success message'
    },

    # Delete template confirmation
    {
        'line': 5814,
        'old': 'f\'确定要删除模板 "{template["name"]}" 吗?\\n\\n此操作不可撤销!\'',
        'new': 'self.i18n.t("config.dialogs.confirm_delete_template", template_name=template["name"])',
        'description': 'Delete template confirmation'
    },

    # Template deleted
    {
        'line': 5834,
        'old': 'f"模板 \\"{template[\'name\']}\\" 已删除"',
        'new': 'self.i18n.t("config.dialogs.template_deleted", template_name=template[\'name\'])',
        'description': 'Template deleted message'
    }
]

def apply_replacements():
    """Apply i18n replacements to config_gui.py"""

    config_path = Path('config_gui.py')

    # Read file
    with open(config_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print("=" * 80)
    print("应用高优先级 i18n 翻译到 config_gui.py")
    print("=" * 80)
    print()
    print(f"文件总行数: {len(lines)}")
    print(f"计划替换: {len(REPLACEMENTS)} 处")
    print()

    replaced_count = 0
    failed_replacements = []

    for replacement in REPLACEMENTS:
        line_num = replacement['line']
        old_text = replacement['old']
        new_text = replacement['new']
        description = replacement['description']

        # Line numbers in list are 0-indexed
        idx = line_num - 1

        if idx >= len(lines):
            print(f"❌ 第 {line_num} 行: 超出文件范围")
            failed_replacements.append(replacement)
            continue

        line = lines[idx]

        # Try to find and replace
        if old_text in line:
            lines[idx] = line.replace(old_text, new_text)
            replaced_count += 1
            print(f"✓ 第 {line_num} 行: {description}")
        else:
            # Try fuzzy match (in case line changed slightly)
            # Extract the Chinese text from old_text
            chinese_match = re.search(r'[\u4e00-\u9fa5]+', old_text)
            if chinese_match and chinese_match.group() in line:
                print(f"⚠️  第 {line_num} 行: 找到部分匹配，需要手动检查")
                print(f"   期望: {old_text[:50]}...")
                print(f"   实际: {line.strip()[:50]}...")
                failed_replacements.append(replacement)
            else:
                print(f"❌ 第 {line_num} 行: 未找到匹配")
                print(f"   期望: {old_text[:50]}...")
                print(f"   实际: {line.strip()[:50]}...")
                failed_replacements.append(replacement)

    print()
    print("=" * 80)
    print(f"替换完成: {replaced_count}/{len(REPLACEMENTS)}")
    print("=" * 80)

    if failed_replacements:
        print()
        print(f"⚠️  {len(failed_replacements)} 处替换失败，需要手动处理:")
        for r in failed_replacements:
            print(f"  - 第 {r['line']} 行: {r['description']}")

    # Save the file
    backup_path = config_path.with_suffix('.py.backup_i18n')

    # Create backup
    with open(backup_path, 'w', encoding='utf-8') as f:
        with open(config_path, 'r', encoding='utf-8') as original:
            f.write(original.read())

    print()
    print(f"✓ 备份已创建: {backup_path}")

    # Write updated file
    with open(config_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print(f"✓ 文件已更新: {config_path}")
    print()
    print("=" * 80)
    print("提示: 请测试应用以确保翻译正常工作")
    print("如有问题，可以从备份恢复: config_gui.py.backup_i18n")
    print("=" * 80)

if __name__ == '__main__':
    apply_replacements()
