#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply remaining i18n translations to config_gui.py"""

import sys
import io
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Additional replacements for the 5 missing translations
ADDITIONAL_REPLACEMENTS = [
    # Partner recruitment (line 4017) - In HTML content
    {
        'line': 4017,
        'old': '此次会员合伙人招募，<b style="color: #FF9800;">首批仅开放1000个名额</b>',
        'new': f'{{self.i18n.t("config.membership.partner_recruitment")}}<b style="color: #FF9800;"></b>',
        'skip': True,  # Skip - complex HTML context, keep original
        'reason': 'HTML内容太复杂，保留原文'
    },

    # Selected plan (line 4529)
    {
        'line': 4529,
        'old': 'f"您选择的套餐：{plan[\'name\']} - {plan[\'price_cny\']}{plan[\'period\']}"',
        'new': 'self.i18n.t("config.membership.selected_plan", plan_name=plan[\'name\'], plan_price=plan[\'price_cny\'], plan_period=plan[\'period\'])',
        'description': 'Selected plan display'
    },

    # Read partner invitation (line 3808) - In HTML link
    {
        'line': 3808,
        'old': '\'<a href="#" style="color: #666666; text-decoration: none;">📜 阅读合伙人邀请函</a>\'',
        'new': 'f\'<a href="#" style="color: #666666; text-decoration: none;">{self.i18n.t("config.membership.read_partner_invitation")}</a>\'',
        'description': 'Partner invitation link'
    }
]

def apply_replacements():
    """Apply remaining i18n replacements"""

    config_path = Path('config_gui.py')

    # Read file
    with open(config_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print("=" * 80)
    print("应用剩余的 i18n 翻译")
    print("=" * 80)
    print()

    replaced_count = 0
    skipped_count = 0

    for replacement in ADDITIONAL_REPLACEMENTS:
        line_num = replacement['line']
        old_text = replacement['old']
        new_text = replacement['new']

        # Check if should skip
        if replacement.get('skip', False):
            print(f"⏭️  第 {line_num} 行: 跳过")
            print(f"   原因: {replacement.get('reason', '复杂上下文')}")
            print(f"   保持原文: {old_text[:60]}...")
            print()
            skipped_count += 1
            continue

        description = replacement.get('description', 'Translation')
        idx = line_num - 1

        if idx >= len(lines):
            print(f"❌ 第 {line_num} 行: 超出文件范围")
            continue

        line = lines[idx]

        # Try to replace
        if old_text in line:
            lines[idx] = line.replace(old_text, new_text)
            replaced_count += 1
            print(f"✅ 第 {line_num} 行: {description}")
            print(f"   替换为: self.i18n.t(...)")
            print()
        else:
            print(f"⚠️  第 {line_num} 行: 未找到完全匹配")
            print(f"   期望: {old_text[:60]}...")
            print(f"   实际: {line.strip()[:60]}...")
            print()

    print("=" * 80)
    print(f"替换结果: {replaced_count} 成功, {skipped_count} 跳过")
    print("=" * 80)
    print()

    if replaced_count > 0:
        # Create backup
        backup_path = config_path.with_suffix('.py.backup_i18n2')

        with open(backup_path, 'w', encoding='utf-8') as f:
            with open(config_path, 'r', encoding='utf-8') as original:
                f.write(original.read())

        print(f"✅ 备份已创建: {backup_path}")

        # Write updated file
        with open(config_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ 文件已更新: {config_path}")
        print()

    # Summary of what's not translated and why
    print("=" * 80)
    print("未翻译字段说明")
    print("=" * 80)
    print()
    print("以下字段因特殊原因保留中文:")
    print()
    print("1. 会员合伙人招募文本 (行 4017)")
    print("   - 原因: 嵌入在复杂HTML模板中")
    print("   - 建议: 整个HTML块使用模板引擎")
    print()
    print("2. 套餐类型显示 (多处)")
    print("   - 原因: Debug日志消息")
    print("   - 建议: 保留中文用于调试")
    print()
    print("3. 模板名标签 (行 53)")
    print("   - 原因: 代码注释/文档")
    print("   - 建议: 改为英文注释")

if __name__ == '__main__':
    apply_replacements()
