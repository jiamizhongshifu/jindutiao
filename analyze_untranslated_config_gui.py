#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析config_gui.py中未翻译的中文字符串
对比en_US.json翻译文件，找出缺失的翻译
"""

import re
import json
from pathlib import Path

def extract_chinese_strings_from_file(file_path):
    """从文件中提取所有硬编码的中文字符串"""
    chinese_strings = {}

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 匹配中文字符串的正则表达式
    # 1. 单引号或双引号包裹的纯中文字符串
    # 2. 包含中文的f-string
    pattern = r'["\']([^"\']*[\u4e00-\u9fff]+[^"\']*)["\']'

    for line_num, line in enumerate(lines, 1):
        # 跳过注释行
        if line.strip().startswith('#'):
            continue

        matches = re.finditer(pattern, line)
        for match in matches:
            chinese_text = match.group(1)
            # 过滤掉一些特殊情况（如文件路径、URL等）
            if '/' not in chinese_text and '\\' not in chinese_text:
                if chinese_text not in chinese_strings:
                    chinese_strings[chinese_text] = []
                chinese_strings[chinese_text].append(line_num)

    return chinese_strings

def load_translation_keys(json_path):
    """加载翻译文件中的所有key"""
    with open(json_path, 'r', encoding='utf-8') as f:
        translations = json.load(f)

    def extract_keys(obj, prefix=''):
        """递归提取所有嵌套的key"""
        keys = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                full_key = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    keys.extend(extract_keys(v, full_key))
                else:
                    keys.append((full_key, v))
        return keys

    return extract_keys(translations)

def categorize_strings_by_tab(line_num):
    """根据行号判断字符串属于哪个tab"""
    if 1612 <= line_num < 1985:
        return "外观配置"
    elif 1985 <= line_num < 2517:
        return "任务管理"
    elif 2517 <= line_num < 2818:
        return "场景设置"
    elif 2818 <= line_num < 3016:
        return "通知设置"
    elif 3016 <= line_num < 6835:
        return "个人中心"
    elif 6835 <= line_num < 7500:
        return "关于"
    else:
        return "其他/通用"

def main():
    # 文件路径
    config_gui_path = Path('config_gui.py')
    zh_json_path = Path('i18n/zh_CN.json')
    en_json_path = Path('i18n/en_US.json')

    print("正在分析 config_gui.py 中的硬编码中文字符串...")
    chinese_strings = extract_chinese_strings_from_file(config_gui_path)

    print(f"共找到 {len(chinese_strings)} 个不同的中文字符串\n")

    print("正在加载翻译文件...")
    zh_translations = load_translation_keys(zh_json_path)
    en_translations = load_translation_keys(en_json_path)

    # 创建中文到翻译key的映射
    zh_to_key = {v: k for k, v in zh_translations}

    # 分类统计
    categorized_missing = {}
    has_zh_key_but_no_en = []
    completely_missing = []

    for chinese_text, line_numbers in chinese_strings.items():
        # 判断是否有中文翻译key
        if chinese_text in zh_to_key:
            zh_key = zh_to_key[chinese_text]
            # 检查英文翻译是否存在且不是中文
            en_value = next((v for k, v in en_translations if k == zh_key), None)
            if en_value is None or any('\u4e00' <= c <= '\u9fff' for c in str(en_value)):
                has_zh_key_but_no_en.append({
                    'text': chinese_text,
                    'key': zh_key,
                    'en_value': en_value,
                    'lines': line_numbers
                })
        else:
            # 完全缺失翻译key
            category = categorize_strings_by_tab(line_numbers[0])
            if category not in categorized_missing:
                categorized_missing[category] = []
            categorized_missing[category].append({
                'text': chinese_text,
                'lines': line_numbers
            })
            completely_missing.append({
                'text': chinese_text,
                'lines': line_numbers,
                'category': category
            })

    # 生成报告
    report = []
    report.append("=" * 80)
    report.append("Config GUI 未翻译字符串分析报告")
    report.append("=" * 80)
    report.append("")

    report.append(f"📊 统计摘要")
    report.append(f"  • 总中文字符串数: {len(chinese_strings)}")
    report.append(f"  • 完全缺失翻译key: {len(completely_missing)}")
    report.append(f"  • 有中文key但英文翻译缺失/错误: {len(has_zh_key_but_no_en)}")
    report.append("")

    # 按tab分类显示完全缺失的翻译
    if categorized_missing:
        report.append("=" * 80)
        report.append("📋 按Tab分类的缺失翻译（完全没有i18n key）")
        report.append("=" * 80)
        report.append("")

        for category, items in sorted(categorized_missing.items()):
            report.append(f"\n【{category}】({len(items)} 项)")
            report.append("-" * 60)
            for item in items[:20]:  # 每个分类只显示前20个
                lines_str = ', '.join(map(str, item['lines'][:5]))
                if len(item['lines']) > 5:
                    lines_str += f" ... (+{len(item['lines'])-5}处)"
                report.append(f"  行 {lines_str:20s} | {item['text']}")
            if len(items) > 20:
                report.append(f"  ... 还有 {len(items)-20} 个字符串")

    # 显示有中文key但英文翻译有问题的
    if has_zh_key_but_no_en:
        report.append("\n" + "=" * 80)
        report.append("⚠️ 有中文key但英文翻译缺失或仍为中文")
        report.append("=" * 80)
        report.append("")
        for item in has_zh_key_but_no_en[:30]:  # 只显示前30个
            report.append(f"  Key: {item['key']}")
            report.append(f"  中文: {item['text']}")
            report.append(f"  英文: {item['en_value'] or '(缺失)'}")
            report.append(f"  位置: 行 {', '.join(map(str, item['lines'][:3]))}")
            report.append("")
        if len(has_zh_key_but_no_en) > 30:
            report.append(f"  ... 还有 {len(has_zh_key_but_no_en)-30} 项")

    # 保存到文件
    report_text = '\n'.join(report)
    output_file = Path('config_gui_translation_analysis.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(f"Report saved to: {output_file}")

    # 生成JSON格式的详细数据
    json_report = {
        'summary': {
            'total_chinese_strings': len(chinese_strings),
            'completely_missing': len(completely_missing),
            'has_key_but_no_en': len(has_zh_key_but_no_en)
        },
        'categorized_missing': categorized_missing,
        'has_key_but_no_en': has_zh_key_but_no_en,
        'all_missing': completely_missing
    }

    json_output_file = Path('config_gui_translation_analysis.json')
    with open(json_output_file, 'w', encoding='utf-8') as f:
        json.dump(json_report, f, ensure_ascii=False, indent=2)

    print(f"JSON data saved to: {json_output_file}")

if __name__ == '__main__':
    main()
