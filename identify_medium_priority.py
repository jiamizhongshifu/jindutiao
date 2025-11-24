#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Identify medium priority translations from untranslated strings"""

import json
import sys
import io

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def is_docstring(code):
    """Check if it's a docstring"""
    return code.strip().startswith('"""') and code.strip().endswith('"""')

def is_logging(code):
    """Check if it's a logging statement"""
    return 'logging.' in code

def is_user_facing(item):
    """Determine if string is user-facing (not docstring or log)"""
    code = item['code']
    text = item['text']

    # Skip docstrings
    if is_docstring(code):
        return False

    # Skip logging
    if is_logging(code):
        return False

    # User-facing indicators
    user_facing_patterns = [
        'QMessageBox',
        'QLabel',
        'setToolTip',
        'setWindowTitle',
        'setText',
        'setPlaceholderText',
        'addItem',
        'result_lines.append',  # Test results shown to user
        'success_msg',  # Success messages
        'error_msg',  # Error messages
    ]

    return any(pattern in code for pattern in user_facing_patterns)

def main():
    # Load untranslated data
    with open('config_i18n_audit_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    untranslated = data['untranslated_details']

    print("=" * 80)
    print("中优先级翻译项目识别")
    print("=" * 80)
    print()
    print(f"总未翻译项: {len(untranslated)}")
    print()

    # Categorize
    user_facing = []
    docstrings = []
    logging_msgs = []
    others = []

    for item in untranslated:
        if is_docstring(item['code']):
            docstrings.append(item)
        elif is_logging(item['code']):
            logging_msgs.append(item)
        elif is_user_facing(item):
            user_facing.append(item)
        else:
            others.append(item)

    print(f"分类结果:")
    print(f"  - 用户可见UI: {len(user_facing)}")
    print(f"  - Docstrings: {len(docstrings)}")
    print(f"  - 日志消息: {len(logging_msgs)}")
    print(f"  - 其他: {len(others)}")
    print()

    # Show user-facing items
    print("=" * 80)
    print(f"用户可见UI文本 ({len(user_facing)} 项)")
    print("=" * 80)
    print()

    # Group by type
    messages = []
    errors = []
    prompts = []
    test_results = []

    for item in user_facing:
        text = item['text']
        code = item['code']

        if 'QMessageBox.critical' in code or '失败' in text or '错误' in text:
            errors.append(item)
        elif 'QMessageBox' in code or 'success_msg' in code:
            messages.append(item)
        elif 'result_lines.append' in code or '测试' in text:
            test_results.append(item)
        else:
            prompts.append(item)

    # Print by priority
    print("## 🔴 高优先级 - 错误消息")
    print(f"共 {len(errors)} 项\n")
    for i, item in enumerate(errors[:10], 1):
        print(f"{i}. 行 {item['line']}: {item['text'][:60]}...")

    print("\n## 🟡 中优先级 - 成功/提示消息")
    print(f"共 {len(messages)} 项\n")
    for i, item in enumerate(messages[:10], 1):
        print(f"{i}. 行 {item['line']}: {item['text'][:60]}...")

    print("\n## 🟢 低优先级 - 测试结果")
    print(f"共 {len(test_results)} 项\n")
    for i, item in enumerate(test_results[:5], 1):
        print(f"{i}. 行 {item['line']}: {item['text'][:60]}...")

    print("\n## 📝 其他UI文本")
    print(f"共 {len(prompts)} 项\n")
    for i, item in enumerate(prompts[:5], 1):
        print(f"{i}. 行 {item['line']}: {item['text'][:60]}...")

    # Generate medium priority list
    medium_priority = errors + messages + test_results[:3]

    print()
    print("=" * 80)
    print(f"建议翻译: {len(medium_priority)} 项")
    print("=" * 80)
    print()

    # Save to file
    output = {
        'summary': {
            'total': len(medium_priority),
            'errors': len(errors),
            'messages': len(messages),
            'test_results': min(3, len(test_results))
        },
        'items': medium_priority,
        'docstrings': len(docstrings),
        'logging': len(logging_msgs)
    }

    with open('medium_priority_translations.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"✓ 中优先级翻译清单已保存: medium_priority_translations.json")
    print()
    print("建议:")
    print(f"  1. 翻译 {len(errors)} 个错误消息（用户遇到问题时会看到）")
    print(f"  2. 翻译 {len(messages)} 个成功/提示消息（操作反馈）")
    print(f"  3. 可选翻译 {len(test_results)} 个测试结果消息")
    print(f"  4. 将 {len(docstrings)} 个Docstrings改为英文注释")
    print(f"  5. 保留 {len(logging_msgs)} 个日志消息（开发用）")

if __name__ == '__main__':
    main()
