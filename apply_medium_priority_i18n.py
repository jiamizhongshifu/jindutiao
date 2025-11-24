#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply medium priority i18n translations to config_gui.py"""

import sys
import io
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Replacement mappings
REPLACEMENTS = [
    # Error messages
    {
        'line': 5555,
        'old': 'f"无法保存模板:\\n{str(e)}"',
        'new': 'self.i18n.t("config.errors.template_save_failed", error=str(e))',
        'description': 'Template save error'
    },
    {
        'line': 5622,
        'old': 'f"模板文件格式错误:\\n{str(e)}"',
        'new': 'self.i18n.t("config.errors.template_format_error", error=str(e))',
        'description': 'Template format error'
    },
    {
        'line': 5624,
        'old': 'f"加载模板失败:\\n{str(e)}"',
        'new': 'self.i18n.t("config.errors.template_load_failed", error=str(e))',
        'description': 'Template load error'
    },

    # Success messages
    {
        'line': 5545,
        'old': 'f"模板已更新:\\n{template_filename}\\n\\n包含 {len(tasks)} 个任务。"',
        'new': 'self.i18n.t("config.messages.template_updated", template_filename=template_filename, task_count=len(tasks))',
        'description': 'Template updated message'
    },
    {
        'line': 5547,
        'old': 'f"模板已创建:\\n{template_filename}\\n\\n已添加到【我的模板】列表中,包含 {len(tasks)} 个任务。"',
        'new': 'self.i18n.t("config.messages.template_created", template_filename=template_filename, task_count=len(tasks))',
        'description': 'Template created message'
    },

    # Confirmation prompt
    {
        'line': 5599,
        'old': 'f\'即将加载自定义模板: {template_name}\\n\\n包含 {len(template_tasks)} 个任务\\n\\n当前表格中的任务将被替换,是否继续?\'',
        'new': 'self.i18n.t("config.prompts.confirm_load_template", template_name=template_name, task_count=len(template_tasks))',
        'description': 'Confirm load template'
    },

    # Test date display
    {
        'line': 1095,
        'old': 'f"测试日期: {selected_date.strftime(\'%Y-%m-%d %A\')}"',
        'new': 'self.i18n.t("config.schedule.test_date_display", test_date=selected_date.strftime(\'%Y-%m-%d %A\'))',
        'description': 'Test date display'
    }
]

def apply_replacements():
    """Apply i18n replacements to config_gui.py"""

    config_path = Path('config_gui.py')

    # Read file
    with open(config_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print("=" * 80)
    print("应用中优先级 i18n 翻译到 config_gui.py")
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

        idx = line_num - 1

        if idx >= len(lines):
            print(f"❌ 第 {line_num} 行: 超出文件范围")
            failed_replacements.append(replacement)
            continue

        line = lines[idx]

        if old_text in line:
            lines[idx] = line.replace(old_text, new_text)
            replaced_count += 1
            print(f"✓ 第 {line_num} 行: {description}")
        else:
            # Try to find partial match
            if '无法保存模板' in line and line_num == 5555:
                # Line may have changed slightly
                print(f"⚠️  第 {line_num} 行: 需要手动检查")
                print(f"   实际: {line.strip()[:80]}...")
                failed_replacements.append(replacement)
            elif '模板文件格式错误' in line and line_num == 5622:
                print(f"⚠️  第 {line_num} 行: 需要手动检查")
                failed_replacements.append(replacement)
            elif '加载模板失败' in line and line_num == 5624:
                print(f"⚠️  第 {line_num} 行: 需要手动检查")
                failed_replacements.append(replacement)
            elif '模板已更新' in line and line_num == 5545:
                print(f"⚠️  第 {line_num} 行: 需要手动检查")
                failed_replacements.append(replacement)
            elif '模板已创建' in line and line_num == 5547:
                print(f"⚠️  第 {line_num} 行: 需要手动检查")
                failed_replacements.append(replacement)
            elif '即将加载自定义模板' in line and line_num == 5599:
                print(f"⚠️  第 {line_num} 行: 需要手动检查")
                failed_replacements.append(replacement)
            elif '测试日期' in line and line_num == 1095:
                print(f"⚠️  第 {line_num} 行: 需要手动检查")
                failed_replacements.append(replacement)
            else:
                print(f"❌ 第 {line_num} 行: 未找到匹配")
                print(f"   期望: {old_text[:60]}...")
                print(f"   实际: {line.strip()[:60]}...")
                failed_replacements.append(replacement)

    print()
    print("=" * 80)
    print(f"替换完成: {replaced_count}/{len(REPLACEMENTS)}")
    print("=" * 80)

    if failed_replacements:
        print()
        print(f"⚠️  {len(failed_replacements)} 处替换需要手动处理:")
        for r in failed_replacements:
            print(f"  - 第 {r['line']} 行: {r['description']}")

    # Save the file
    if replaced_count > 0:
        backup_path = config_path.with_suffix('.py.backup_i18n_medium')

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
    print("提示: 请测试模板保存/加载功能以验证翻译")
    print("=" * 80)

if __name__ == '__main__':
    apply_replacements()
