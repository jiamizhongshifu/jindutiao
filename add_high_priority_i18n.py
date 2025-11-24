#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Add high priority translations to i18n files"""

import json
import sys
import io
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# High priority translations (user-facing UI)
HIGH_PRIORITY_TRANSLATIONS = {
    # Tooltips (3 items)
    "config.tooltips.load_custom_template": {
        "zh_CN": "加载选中的自定义模板",
        "en_US": "Load selected custom template"
    },
    "config.tooltips.delete_custom_template": {
        "zh_CN": "删除选中的自定义模板",
        "en_US": "Delete selected custom template"
    },
    "config.tooltips.test_date_match": {
        "zh_CN": "测试指定日期会匹配到哪个模板",
        "en_US": "Test which template will match the specified date"
    },

    # Dialogs (4 items)
    "config.dialogs.theme_applied": {
        "zh_CN": "已应用主题: {theme_name}",
        "en_US": "Theme applied: {theme_name}"
    },
    "config.dialogs.confirm_delete_template": {
        "zh_CN": "确定要删除模板 \"{template_name}\" 吗?\n\n此操作不可撤销!",
        "en_US": "Are you sure you want to delete template \"{template_name}\"?\n\nThis action cannot be undone!"
    },
    "config.dialogs.template_deleted": {
        "zh_CN": "模板 \"{template_name}\" 已删除",
        "en_US": "Template \"{template_name}\" has been deleted"
    },
    "config.dialogs.overwrite_template_warning": {
        "zh_CN": "• 选择历史模板将直接覆盖该模板\n",
        "en_US": "• Selecting a historical template will overwrite it\n"
    },

    # Membership/Payment (7 items)
    "config.membership.partner_recruitment": {
        "zh_CN": "此次会员合伙人招募，首批仅开放1000个名额",
        "en_US": "This membership partnership recruitment is limited to 1,000 spots for the first batch"
    },
    "config.membership.selected_plan": {
        "zh_CN": "您选择的套餐：{plan_name} - {plan_price}{plan_period}",
        "en_US": "Selected plan: {plan_name} - {plan_price}{plan_period}"
    },
    "config.membership.plan_type": {
        "zh_CN": "• 套餐类型: {plan_id}\n",
        "en_US": "• Plan type: {plan_id}\n"
    },
    "config.membership.stripe_session_creating": {
        "zh_CN": "[STRIPE] 开始创建Stripe支付会话 - 套餐: {plan_id}",
        "en_US": "[STRIPE] Creating Stripe payment session - Plan: {plan_id}"
    },
    "config.membership.payment_success_restart": {
        "zh_CN": "支付已完成！\n您的会员权益已激活。\n\n请重新启动应用以生效。",
        "en_US": "Payment completed!\nYour membership benefits have been activated.\n\nPlease restart the app for changes to take effect."
    },
    "config.membership.welcome_back": {
        "zh_CN": "欢迎回来，{user_email}！\n\n",
        "en_US": "Welcome back, {user_email}!\n\n"
    },
    "config.membership.read_partner_invitation": {
        "zh_CN": "📜 阅读合伙人邀请函",
        "en_US": "📜 Read Partner Invitation"
    },

    # Template/Schedule (4 items)
    "config.templates.template_name": {
        "zh_CN": "模板名",
        "en_US": "Template Name"
    },
    "config.templates.task_count": {
        "zh_CN": "{template_name} ({task_count}个任务)",
        "en_US": "{template_name} ({task_count} tasks)"
    },
    "config.schedule.date_will_load_template": {
        "zh_CN": "✅ 该日期会自动加载模板: {template_name}",
        "en_US": "✅ This date will automatically load template: {template_name}"
    },
    "config.schedule.date_conflict_warning": {
        "zh_CN": "⚠️ 警告：该日期有 {conflict_count} 个模板规则冲突！",
        "en_US": "⚠️ Warning: This date has {conflict_count} conflicting template rules!"
    }
}

def add_nested_key(data, key_path, value):
    """Add a nested key to a dictionary"""
    parts = key_path.split('.')
    current = data

    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]

    current[parts[-1]] = value

def main():
    print("=" * 80)
    print("添加高优先级翻译到 i18n 文件")
    print("=" * 80)
    print()

    # Load existing i18n files
    zh_path = Path('i18n/zh_CN.json')
    en_path = Path('i18n/en_US.json')

    with open(zh_path, 'r', encoding='utf-8') as f:
        zh_data = json.load(f)

    with open(en_path, 'r', encoding='utf-8') as f:
        en_data = json.load(f)

    print(f"✓ 已加载现有翻译文件")
    print(f"  - zh_CN: {len(json.dumps(zh_data))} 字符")
    print(f"  - en_US: {len(json.dumps(en_data))} 字符")
    print()

    # Add translations
    added_count = 0
    updated_count = 0

    for key, translations in HIGH_PRIORITY_TRANSLATIONS.items():
        # Check if key exists
        parts = key.split('.')

        # Check Chinese
        zh_exists = True
        current = zh_data
        for part in parts:
            if part not in current:
                zh_exists = False
                break
            current = current.get(part, {})

        # Add to zh_CN
        add_nested_key(zh_data, key, translations['zh_CN'])

        # Add to en_US
        add_nested_key(en_data, key, translations['en_US'])

        if zh_exists:
            updated_count += 1
            print(f"⚠️  更新: {key}")
        else:
            added_count += 1
            print(f"✓ 添加: {key}")

    print()
    print(f"总计: 新增 {added_count} 项, 更新 {updated_count} 项")
    print()

    # Save updated files
    with open(zh_path, 'w', encoding='utf-8') as f:
        json.dump(zh_data, f, ensure_ascii=False, indent=2)

    with open(en_path, 'w', encoding='utf-8') as f:
        json.dump(en_data, f, ensure_ascii=False, indent=2)

    print("✓ i18n 文件已更新:")
    print(f"  - {zh_path}")
    print(f"  - {en_path}")
    print()

    # Generate replacement mapping
    replacement_map = []

    for key, translations in HIGH_PRIORITY_TRANSLATIONS.items():
        replacement_map.append({
            'key': key,
            'zh_CN': translations['zh_CN'],
            'en_US': translations['en_US'],
            'replacement': f'self.i18n.t("{key}")'
        })

    with open('high_priority_replacement_map.json', 'w', encoding='utf-8') as f:
        json.dump(replacement_map, f, ensure_ascii=False, indent=2)

    print("✓ 替换映射已生成: high_priority_replacement_map.json")
    print()
    print("=" * 80)
    print("下一步: 在代码中应用这些翻译键")
    print("=" * 80)

if __name__ == '__main__':
    main()
