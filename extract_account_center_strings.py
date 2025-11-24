#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取个人中心的所有需要翻译的字符串
"""

import re
from pathlib import Path

def extract_strings_from_range(file_path, start_line, end_line):
    """从指定行范围提取中文字符串"""
    strings = []

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 只处理指定范围
    target_lines = lines[start_line-1:end_line]

    pattern = r'["\']([^"\']*[\u4e00-\u9fff]+[^"\']*)["\']'

    for i, line in enumerate(target_lines, start=start_line):
        # 跳过注释
        if line.strip().startswith('#'):
            continue

        matches = re.finditer(pattern, line)
        for match in matches:
            text = match.group(1)
            # 过滤路径、URL等
            if '/' not in text and '\\' not in text and 'http' not in text.lower():
                strings.append({
                    'line': i,
                    'text': text,
                    'context': line.strip()[:100]
                })

    return strings

def main():
    # 个人中心范围：3016-6835行
    config_gui_path = Path('config_gui.py')

    print("Extracting Chinese strings from account center...")
    strings = extract_strings_from_range(config_gui_path, 3016, 6835)

    # 去重
    unique_strings = {}
    for item in strings:
        if item['text'] not in unique_strings:
            unique_strings[item['text']] = []
        unique_strings[item['text']].append(item['line'])

    print(f"Found {len(unique_strings)} unique Chinese strings")

    # 分类
    categories = {
        'membership': [],  # 会员相关
        'plan': [],  # 套餐相关
        'feature': [],  # 功能特性
        'payment': [],  # 支付相关
        'ui': [],  # UI文本
        'message': [],  # 提示消息
        'other': []  # 其他
    }

    keywords = {
        'membership': ['会员', '用户', '登录', '退出', '账号'],
        'plan': ['月', '年', '终身', '套餐', '价格', '节省', '有效期'],
        'feature': ['功能', '特性', '进度条', '统计', '番茄', '云同步', '场景', '水印', '返现', '咨询'],
        'payment': ['支付', '微信', '支付宝', '订单', '等待', '渠道'],
        'ui': ['确认', '取消', '选择', '点击', '显示', '关闭'],
        'message': ['成功', '失败', '错误', '提示', '警告']
    }

    for text, lines in unique_strings.items():
        categorized = False
        for category, words in keywords.items():
            if any(word in text for word in words):
                categories[category].append({'text': text, 'lines': lines})
                categorized = True
                break
        if not categorized:
            categories['other'].append({'text': text, 'lines': lines})

    # 输出
    output = []
    output.append("=" * 80)
    output.append("个人中心未翻译字符串详细清单")
    output.append("=" * 80)
    output.append("")

    for category, items in categories.items():
        if items:
            category_names = {
                'membership': '会员账号相关',
                'plan': '套餐价格相关',
                'feature': '功能特性描述',
                'payment': '支付流程相关',
                'ui': 'UI界面文本',
                'message': '提示消息',
                'other': '其他'
            }
            output.append(f"\n【{category_names[category]}】({len(items)} 项)")
            output.append("-" * 60)
            for item in items:
                lines_str = ', '.join(map(str, item['lines'][:3]))
                if len(item['lines']) > 3:
                    lines_str += f" (+{len(item['lines'])-3})"
                output.append(f"  行 {lines_str:15s} | {item['text']}")

    report = '\n'.join(output)

    # 保存
    output_file = Path('account_center_strings_detail.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"Report saved to: {output_file}")

    # 保存为JSON供后续处理
    import json
    json_output = {
        'total': len(unique_strings),
        'categories': categories
    }
    json_file = Path('account_center_strings.json')
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_output, f, ensure_ascii=False, indent=2)

    print(f"JSON data saved to: {json_file}")

if __name__ == '__main__':
    main()
