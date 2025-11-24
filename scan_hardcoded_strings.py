"""
Comprehensive scan of hardcoded Chinese strings in the codebase
Generates a detailed report and mapping for internationalization
"""
import os
import re
import json
from pathlib import Path
from collections import defaultdict

# Files to scan (main application files)
SCAN_FILES = [
    'main.py',
    'config_gui.py',
    'timeline_editor.py',
    'statistics_gui.py',
    'gaiya/ui/membership_ui.py',
    'gaiya/ui/auth_ui.py',
    'gaiya/ui/pomodoro_panel.py',
    'gaiya/ui/onboarding/setup_wizard.py',
    'gaiya/ui/onboarding/quota_exhausted_dialog.py',
    'gaiya/ui/otp_dialog.py',
    'gaiya/ui/email_verification_dialog.py',
]

# Categories based on context
CATEGORIES = {
    'config': ['配置', '设置', '外观', '透明', '高度', '位置', '颜色', '圆角', '阴影', '自启动', '显示器'],
    'tasks': ['任务', '时间', '开始', '结束', '模板', '主题', '配色', '时间轴'],
    'ai': ['AI', '智能', '生成', '配额', '描述'],
    'membership': ['会员', '套餐', '订阅', '支付', '价格', '升级', '激活'],
    'account': ['账号', '登录', '注册', '邮箱', '密码', '验证码'],
    'dialog': ['确定', '取消', '保存', '应用', '删除', '提示', '警告', '错误'],
    'notification': ['通知', '提醒'],
    'scene': ['场景', '编辑器'],
    'pomodoro': ['番茄钟'],
    'statistics': ['统计', '报告'],
}


def has_chinese(text):
    """Check if text contains Chinese characters"""
    return bool(re.search(r'[\u4e00-\u9fff]', str(text)))


def extract_chinese_strings(file_path):
    """Extract all Chinese strings from a Python file"""
    strings = []

    if not os.path.exists(file_path):
        return strings

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line_num, line in enumerate(lines, 1):
        # Skip comments
        if line.strip().startswith('#'):
            continue

        # Skip if already using tr()
        if 'tr(' in line and line.index('tr(') < line.find('"') if '"' in line else True:
            continue

        # Find all quoted strings
        # Match both single and double quotes
        patterns = [
            r'"([^"]*[\u4e00-\u9fff][^"]*)"',  # Double quotes
            r"'([^']*[\u4e00-\u9fff][^']*)'",  # Single quotes
            r'f"([^"]*[\u4e00-\u9fff][^"]*)"', # f-strings with double quotes
            r"f'([^']*[\u4e00-\u9fff][^']*)'", # f-strings with single quotes
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, line)
            for match in matches:
                chinese_str = match.group(1)

                # Get context (function/class name if possible)
                context = ""
                for prev_line in reversed(lines[max(0, line_num-10):line_num-1]):
                    if 'def ' in prev_line or 'class ' in prev_line:
                        context = prev_line.strip()
                        break

                strings.append({
                    'file': file_path,
                    'line': line_num,
                    'chinese': chinese_str,
                    'full_line': line.strip(),
                    'context': context
                })

    return strings


def categorize_string(chinese_str):
    """Categorize a string based on keywords"""
    for category, keywords in CATEGORIES.items():
        for keyword in keywords:
            if keyword in chinese_str:
                return category
    return 'general'


def suggest_translation_key(chinese_str, category, existing_keys):
    """Suggest a translation key for a Chinese string"""
    # Common mappings
    key_mapping = {
        '确定': 'button.ok',
        '取消': 'button.cancel',
        '保存': 'button.save',
        '应用': 'button.apply',
        '删除': 'button.delete',
        '关闭': 'button.close',
        '添加': 'button.add',
        '编辑': 'button.edit',
        '刷新': 'button.refresh',
        '配置': 'config.title',
        '设置': 'config.title',
        '任务': 'tasks.title',
        '会员': 'membership.title',
        '登录': 'account.login',
        '注册': 'account.register',
    }

    # Check direct mapping
    if chinese_str in key_mapping:
        return key_mapping[chinese_str]

    # Generate key based on category and content
    # Remove special characters and convert to key format
    clean_str = re.sub(r'[^\u4e00-\u9fff\w\s]', '', chinese_str)
    clean_str = clean_str.strip()

    if not clean_str:
        return None

    # Create a base key
    base_key = f"{category}.{clean_str[:20]}"

    # Ensure uniqueness
    key = base_key
    counter = 1
    while key in existing_keys:
        key = f"{base_key}_{counter}"
        counter += 1

    return key


def main():
    print("=== Scanning Hardcoded Chinese Strings ===\n")

    all_strings = []
    stats_by_file = defaultdict(int)
    stats_by_category = defaultdict(int)

    # Scan all files
    for file_path in SCAN_FILES:
        if not os.path.exists(file_path):
            print(f"[SKIP] {file_path} - File not found")
            continue

        strings = extract_chinese_strings(file_path)
        all_strings.extend(strings)
        stats_by_file[file_path] = len(strings)
        print(f"[SCAN] {file_path}: {len(strings)} strings")

    print(f"\nTotal strings found: {len(all_strings)}\n")

    # Categorize strings
    for item in all_strings:
        category = categorize_string(item['chinese'])
        item['category'] = category
        stats_by_category[category] += 1

    # Generate statistics
    print("=== Statistics by File ===\n")
    for file_path, count in sorted(stats_by_file.items(), key=lambda x: x[1], reverse=True):
        print(f"{count:4d}  {file_path}")

    print("\n=== Statistics by Category ===\n")
    for category, count in sorted(stats_by_category.items(), key=lambda x: x[1], reverse=True):
        print(f"{count:4d}  {category}")

    # Save detailed report
    output = {
        'total_strings': len(all_strings),
        'stats_by_file': dict(stats_by_file),
        'stats_by_category': dict(stats_by_category),
        'strings': all_strings[:100]  # Save first 100 for review
    }

    with open('hardcoded_strings_report.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("\n=== Report saved to: hardcoded_strings_report.json ===")

    # Generate sample translation keys
    print("\n=== Sample Translation Keys Needed ===\n")
    existing_keys = set()
    samples_by_category = defaultdict(list)

    for item in all_strings:
        category = item['category']
        chinese = item['chinese']

        # Skip very long strings (likely descriptions)
        if len(chinese) > 50:
            continue

        # Generate key suggestion
        key = suggest_translation_key(chinese, category, existing_keys)
        if key:
            existing_keys.add(key)
            if len(samples_by_category[category]) < 5:  # Show 5 samples per category
                samples_by_category[category].append({
                    'key': key,
                    'zh': chinese,
                    'file': item['file']
                })

    for category in sorted(samples_by_category.keys()):
        print(f"\n[{category}]")
        for sample in samples_by_category[category]:
            print(f"  {sample['key']}: \"{sample['zh']}\"")
            print(f"    (from {sample['file']})")

    print(f"\n=== Scan Complete ===")
    print(f"Estimated new translation keys needed: {len(existing_keys)}")


if __name__ == '__main__':
    main()
