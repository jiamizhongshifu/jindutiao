#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扫描所有UI文件，统计需要国际化的中文字符串数量
"""

import re
import os
from pathlib import Path

def count_chinese_strings(file_path):
    """统计文件中的中文字符串数量"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 匹配包含中文的字符串（单引号或双引号）
        pattern = r'["\']([^"\']*[\u4e00-\u9fff][^"\']*)["\']'
        matches = re.findall(pattern, content)

        # 过滤掉文档字符串（通常很长或包含多行）
        filtered_matches = [m for m in matches if len(m) < 200 and '\n' not in m]

        return len(filtered_matches), filtered_matches
    except Exception as e:
        return 0, []

def scan_ui_files():
    """扫描所有UI文件"""
    ui_files = [
        # 主要UI文件
        'gaiya/ui/auth_ui.py',
        'gaiya/ui/membership_ui.py',
        'scene_editor.py',
        'statistics_gui.py',

        # Onboarding系列
        'gaiya/ui/onboarding/welcome_dialog.py',
        'gaiya/ui/onboarding/setup_wizard.py',
        'gaiya/ui/onboarding/quota_exhausted_dialog.py',

        # 其他对话框
        'gaiya/ui/email_verification_dialog.py',
        'gaiya/ui/otp_dialog.py',

        # 功能面板
        'gaiya/ui/pomodoro_panel.py',
    ]

    results = []
    total_strings = 0

    for file_path in ui_files:
        full_path = os.path.join(os.getcwd(), file_path)
        if os.path.exists(full_path):
            count, strings = count_chinese_strings(full_path)
            total_strings += count

            # 获取文件大小（行数）
            with open(full_path, 'r', encoding='utf-8') as f:
                line_count = len(f.readlines())

            results.append({
                'file': file_path,
                'strings': count,
                'lines': line_count,
                'samples': strings[:5]  # 前5个样本
            })

    # 按字符串数量排序
    results.sort(key=lambda x: x['strings'], reverse=True)

    # 输出到文件
    with open('ui_files_i18n_scan.txt', 'w', encoding='utf-8') as f:
        f.write("=== UI文件国际化工作量评估 ===\n\n")
        f.write(f"扫描文件总数: {len(results)}\n")
        f.write(f"累计中文字符串: {total_strings}\n\n")
        f.write("=" * 80 + "\n\n")

        for i, result in enumerate(results, 1):
            f.write(f"{i}. {result['file']}\n")
            f.write(f"   - 中文字符串数: {result['strings']}\n")
            f.write(f"   - 文件行数: {result['lines']}\n")

            if result['samples']:
                f.write(f"   - 示例字符串:\n")
                for sample in result['samples']:
                    f.write(f"     • {sample}\n")

            f.write("\n")

        # 分组建议
        f.write("=" * 80 + "\n")
        f.write("\n优先级分组建议:\n\n")

        high_priority = [r for r in results if r['strings'] >= 50]
        medium_priority = [r for r in results if 20 <= r['strings'] < 50]
        low_priority = [r for r in results if r['strings'] < 20]

        if high_priority:
            f.write("🔴 高优先级（≥50个字符串）:\n")
            for r in high_priority:
                f.write(f"   • {r['file']} ({r['strings']}个)\n")
            f.write("\n")

        if medium_priority:
            f.write("🟡 中优先级（20-49个字符串）:\n")
            for r in medium_priority:
                f.write(f"   • {r['file']} ({r['strings']}个)\n")
            f.write("\n")

        if low_priority:
            f.write("🟢 低优先级（<20个字符串）:\n")
            for r in low_priority:
                f.write(f"   • {r['file']} ({r['strings']}个)\n")

    print(f"扫描完成！共扫描 {len(results)} 个文件，发现 {total_strings} 个中文字符串")
    print("详细报告已保存到: ui_files_i18n_scan.txt")

    # 返回结果供进一步分析
    return results

if __name__ == '__main__':
    results = scan_ui_files()
