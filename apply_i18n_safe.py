#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全地应用i18n翻译到config_gui.py
分阶段处理，避免语法错误
"""

import re
import sys

def apply_phase1_simple_replacements(content):
    """
    阶段1: 处理简单的字符串替换（不在f-string中）
    """
    replacements = [
        # 标签名
        ('"👤 个人中心"', 'tr("account.tab_title")'),

        # Feature列表中的字符串（需要特别小心处理数组）
        ('"所有免费功能 +"', 'tr("account.feature.all_free_features_plus")'),
        ('"20次/天 AI智能规划"', 'tr("account.feature.ai_quota_20_per_day")'),
        ('"50次/天 AI智能规划"', 'tr("account.feature.ai_quota_50_per_day")'),
        ('"统计报告分析"', 'tr("account.feature.statistics_reports")'),
        ('"去除进度条水印"', 'tr("account.feature.no_watermark")'),
        ('"番茄时钟"', 'tr("account.feature.pomodoro_timer")'),
        ('"数据云同步"', 'tr("account.feature.cloud_sync")'),
        ('"场景系统"', 'tr("account.feature.scene_system")'),
        ('"抢先体验新功能"', 'tr("account.feature.early_access")'),
        ('"加入VIP会员群"', 'tr("account.feature.vip_group")'),
        ('"33%引荐返现比例"', 'tr("account.feature.referral_cashback")'),
        ('"专属合伙人社群"', 'tr("account.feature.partner_community")'),
        ('"优先体验所有新功能"', 'tr("account.feature.priority_updates")'),
        ('"专属1v1咨询服务"', 'tr("account.feature.one_on_one_consulting")'),
        ('"共同成长,分享价值"', 'tr("account.feature.grow_together")'),

        # 标题和标签
        ('"个人中心"', 'tr("account.title")'),
    ]

    for old, new in replacements:
        # 只替换不在注释中的内容
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            # 跳过注释行
            stripped = line.strip()
            if stripped.startswith('#'):
                new_lines.append(line)
                continue

            # 检查是否在f-string中（简单检测：行中有f"或f'）
            if 'f"' in line or "f'" in line:
                # 暂时跳过f-string，留给阶段2处理
                new_lines.append(line)
                continue

            # 执行替换
            line = line.replace(old, new)
            new_lines.append(line)

        content = '\n'.join(new_lines)

    return content

def apply_phase2_fstring_replacements(content):
    """
    阶段2: 处理f-string中的字符串
    使用单引号包裹tr()调用来避免引号冲突
    """
    replacements = [
        # f-string中的替换，使用单引号
        ('f"• Pro会员：20次/天 AI智能规划\\n"',
         'f"• {tr(\'account.membership.pro\')}: {tr(\'account.feature.ai_quota_20_per_day\')}\\n"'),
    ]

    for old, new in replacements:
        content = content.replace(old, new)

    return content

def verify_syntax(file_path):
    """验证Python文件语法是否正确"""
    import py_compile
    try:
        py_compile.compile(file_path, doraise=True)
        return True, "Syntax OK"
    except py_compile.PyCompileError as e:
        return False, str(e)

def main():
    file_path = 'config_gui.py'

    # 读取原始内容
    print(f"Reading {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        original_content = f.read()

    # 阶段1: 简单替换
    print("\n=== Phase 1: Simple replacements ===")
    content = apply_phase1_simple_replacements(original_content)

    # 写入临时文件并验证
    temp_file = 'config_gui_temp.py'
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(content)

    success, msg = verify_syntax(temp_file)
    if not success:
        print(f"[FAIL] Phase 1 failed syntax check:")
        print(msg)
        return 1

    print("[OK] Phase 1 syntax OK")

    # 阶段2: f-string替换
    print("\n=== Phase 2: F-string replacements ===")
    content = apply_phase2_fstring_replacements(content)

    # 再次验证
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(content)

    success, msg = verify_syntax(temp_file)
    if not success:
        print(f"[FAIL] Phase 2 failed syntax check:")
        print(msg)
        return 1

    print("[OK] Phase 2 syntax OK")

    # 所有阶段都成功，写入最终文件
    print(f"\n[SUCCESS] All phases completed successfully!")
    print(f"Writing to {file_path}...")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # 统计替换数量
    import difflib
    diff = difflib.unified_diff(
        original_content.splitlines(keepends=True),
        content.splitlines(keepends=True),
        lineterm=''
    )
    changes = sum(1 for line in diff if line.startswith('+') or line.startswith('-'))
    print(f"\n[STATS] Made {changes//2} replacements")

    return 0

if __name__ == '__main__':
    sys.exit(main())
