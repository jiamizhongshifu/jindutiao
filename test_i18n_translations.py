#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test i18n translations for config_gui.py"""

import sys
import io
import json
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def load_i18n_file(filepath):
    """Load i18n JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_nested_value(data, key_path):
    """Get value from nested dict using dot notation"""
    parts = key_path.split('.')
    current = data

    for part in parts:
        if part not in current:
            return None
        current = current[part]

    return current

def verify_translation_key(zh_data, en_data, key, description):
    """Verify a translation key exists in both languages"""
    zh_value = get_nested_value(zh_data, key)
    en_value = get_nested_value(en_data, key)

    status = "✅" if (zh_value and en_value) else "❌"

    print(f"{status} {description}")
    print(f"   Key: {key}")

    if zh_value:
        print(f"   中文: {zh_value}")
    else:
        print(f"   中文: [缺失]")

    if en_value:
        print(f"   英文: {en_value}")
    else:
        print(f"   英文: [缺失]")

    print()

    return zh_value is not None and en_value is not None

def check_code_usage(key):
    """Check if the key is used in config_gui.py"""
    config_path = Path('config_gui.py')

    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for self.i18n.t("key")
    search_pattern = f'self.i18n.t("{key}"'

    if search_pattern in content:
        return True, "在代码中使用"
    else:
        return False, "未在代码中找到"

def main():
    print("=" * 80)
    print("i18n 翻译验证测试")
    print("=" * 80)
    print()

    # Load i18n files
    zh_path = Path('i18n/zh_CN.json')
    en_path = Path('i18n/en_US.json')

    if not zh_path.exists():
        print(f"❌ 文件不存在: {zh_path}")
        return

    if not en_path.exists():
        print(f"❌ 文件不存在: {en_path}")
        return

    zh_data = load_i18n_file(zh_path)
    en_data = load_i18n_file(en_path)

    print(f"✅ 已加载翻译文件")
    print(f"   - {zh_path}")
    print(f"   - {en_path}")
    print()

    # Test cases for high priority translations
    test_cases = [
        # Tooltips
        ("config.tooltips.load_custom_template", "工具提示: 加载自定义模板"),
        ("config.tooltips.delete_custom_template", "工具提示: 删除自定义模板"),
        ("config.tooltips.test_date_match", "工具提示: 测试日期匹配"),

        # Dialogs
        ("config.dialogs.theme_applied", "对话框: 主题已应用"),
        ("config.dialogs.confirm_delete_template", "对话框: 确认删除模板"),
        ("config.dialogs.template_deleted", "对话框: 模板已删除"),
        ("config.dialogs.overwrite_template_warning", "对话框: 覆盖模板警告"),

        # Membership
        ("config.membership.partner_recruitment", "会员: 合伙人招募"),
        ("config.membership.selected_plan", "会员: 选择的套餐"),
        ("config.membership.plan_type", "会员: 套餐类型"),
        ("config.membership.payment_success_restart", "会员: 支付成功消息"),
        ("config.membership.welcome_back", "会员: 欢迎回来"),
        ("config.membership.read_partner_invitation", "会员: 阅读邀请函"),

        # Templates/Schedule
        ("config.templates.template_name", "模板: 模板名"),
        ("config.templates.task_count", "模板: 任务数量"),
        ("config.schedule.date_will_load_template", "时间表: 日期加载模板"),
        ("config.schedule.date_conflict_warning", "时间表: 冲突警告"),
    ]

    print("=" * 80)
    print("测试翻译键完整性")
    print("=" * 80)
    print()

    passed = 0
    failed = 0

    for key, description in test_cases:
        if verify_translation_key(zh_data, en_data, key, description):
            passed += 1
        else:
            failed += 1

    print("=" * 80)
    print(f"翻译键测试结果: {passed} 通过, {failed} 失败")
    print("=" * 80)
    print()

    # Check code usage
    print("=" * 80)
    print("检查代码中的使用情况")
    print("=" * 80)
    print()

    used_count = 0
    not_used_count = 0

    for key, description in test_cases:
        is_used, status = check_code_usage(key)
        symbol = "✅" if is_used else "⚠️"

        print(f"{symbol} {description}")
        print(f"   Key: {key}")
        print(f"   状态: {status}")
        print()

        if is_used:
            used_count += 1
        else:
            not_used_count += 1

    print("=" * 80)
    print(f"代码使用情况: {used_count} 已使用, {not_used_count} 未使用")
    print("=" * 80)
    print()

    # Check for variable substitution
    print("=" * 80)
    print("检查变量替换")
    print("=" * 80)
    print()

    substitution_keys = {
        "config.dialogs.theme_applied": ["theme_name"],
        "config.dialogs.confirm_delete_template": ["template_name"],
        "config.dialogs.template_deleted": ["template_name"],
        "config.membership.selected_plan": ["plan_name", "plan_price", "plan_period"],
        "config.membership.plan_type": ["plan_id"],
        "config.membership.payment_success_restart": [],
        "config.membership.welcome_back": ["user_email"],
        "config.templates.task_count": ["template_name", "task_count"],
        "config.schedule.date_will_load_template": ["template_name"],
        "config.schedule.date_conflict_warning": ["conflict_count"],
    }

    for key, expected_vars in substitution_keys.items():
        zh_value = get_nested_value(zh_data, key)
        en_value = get_nested_value(en_data, key)

        if not zh_value or not en_value:
            continue

        print(f"🔍 {key}")

        all_found = True
        for var in expected_vars:
            var_pattern = f"{{{var}}}"
            zh_has = var_pattern in zh_value
            en_has = var_pattern in en_value

            symbol = "✅" if (zh_has and en_has) else "❌"
            print(f"   {symbol} 变量 '{var}': 中文={zh_has}, 英文={en_has}")

            if not (zh_has and en_has):
                all_found = False

        if not expected_vars:
            print(f"   ✅ 无需变量替换")

        print()

    # Final summary
    print("=" * 80)
    print("测试总结")
    print("=" * 80)
    print()
    print(f"✅ 翻译键完整性: {passed}/{len(test_cases)} 通过")
    print(f"✅ 代码使用情况: {used_count}/{len(test_cases)} 已使用")
    print()

    if failed > 0:
        print(f"⚠️  有 {failed} 个翻译键缺失，请检查")

    if not_used_count > 0:
        print(f"⚠️  有 {not_used_count} 个翻译键未在代码中使用")

    if failed == 0 and not_used_count == 0:
        print("🎉 所有测试通过！翻译已正确配置。")

    print()
    print("=" * 80)
    print("下一步建议:")
    print("=" * 80)
    print()
    print("1. 运行应用程序测试实际显示效果")
    print("2. 在设置中切换语言，验证英文翻译")
    print("3. 测试包含变量的消息（如删除模板确认）")
    print("4. 检查工具提示是否正确显示")

if __name__ == '__main__':
    main()
