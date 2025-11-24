"""
Filter hardcoded strings to identify UI text that needs internationalization
Excludes: logger messages, docstrings, comments
"""
import json
import re
from collections import defaultdict


def is_ui_string(item):
    """
    Determine if a string is UI text that needs internationalization
    Returns: (is_ui, reason)
    """
    full_line = item['full_line']
    chinese = item['chinese']

    # Exclude logger messages
    if any(x in full_line for x in ['logger.', 'logging.', 'print(', 'self.logger']):
        return False, 'logger'

    # Exclude docstrings
    if '"""' in full_line or "'''" in full_line:
        return False, 'docstring'

    # Exclude comments
    if full_line.strip().startswith('#'):
        return False, 'comment'

    # Exclude very long strings (likely descriptions/docs, not UI labels)
    if len(chinese) > 100:
        return False, 'too_long'

    # Include common UI patterns
    ui_patterns = [
        'QLabel',
        'QPushButton',
        'QAction',
        'setText',
        'setWindowTitle',
        'setToolTip',
        'QMessageBox',
        'addItem',
        'addRow',
        'setPlaceholderText',
        'setTitle',
        'QCheckBox',
        'QRadioButton',
        'QGroupBox',
    ]

    for pattern in ui_patterns:
        if pattern in full_line:
            return True, pattern

    # Default: assume it's UI if not explicitly excluded
    return True, 'default'


def generate_translation_key(chinese_str, category, counter_dict):
    """Generate a meaningful translation key"""

    # Common direct mappings (high priority)
    DIRECT_MAP = {
        # Buttons
        '确定': 'button.ok',
        '取消': 'button.cancel',
        '保存': 'button.save',
        '应用': 'button.apply',
        '重置': 'button.reset',
        '关闭': 'button.close',
        '删除': 'button.delete',
        '添加': 'button.add',
        '编辑': 'button.edit',
        '刷新': 'button.refresh',
        '确认': 'button.confirm',
        '导入': 'button.import',
        '导出': 'button.export',
        '预览': 'button.preview',
        '生成': 'button.generate',
        '登录': 'button.login',
        '退出登录': 'button.logout',
        '注册': 'button.register',
        '下一步': 'button.next',
        '上一步': 'button.back',
        '完成': 'button.finish',
        '跳过': 'button.skip',
        '选择': 'button.select',
        '清除': 'button.clear',
        '重试': 'button.retry',
        '复制': 'button.copy',
        '粘贴': 'button.paste',
        '升级会员': 'button.upgrade',

        # Messages
        '提示': 'message.info',
        '警告': 'message.warning',
        '错误': 'message.error',
        '成功': 'message.success',
        '保存成功': 'message.save_success',
        '保存失败': 'message.save_failed',
        '加载成功': 'message.load_success',
        '加载失败': 'message.load_failed',
        '删除成功': 'message.delete_success',
        '删除失败': 'message.delete_failed',
        '操作成功': 'message.operation_success',
        '操作失败': 'message.operation_failed',
        '请稍候...': 'message.please_wait',
        '加载中...': 'message.loading',

        # Config
        '配置': 'config.title',
        '设置': 'config.title',
        '外观设置': 'config.appearance',
        '语言': 'config.language',
        '进度条高度': 'config.bar_height',
        '进度条位置': 'config.bar_position',
        '顶部': 'config.position_top',
        '底部': 'config.position_bottom',
        '透明度': 'config.transparency',
        '背景颜色': 'config.background_color',
        '圆角大小': 'config.corner_radius',
        '阴影效果': 'config.shadow',
        '开机自启动': 'config.auto_start',

        # Tasks
        '任务管理': 'tasks.title',
        '任务名称': 'tasks.name',
        '开始时间': 'tasks.start_time',
        '结束时间': 'tasks.end_time',
        '颜色': 'tasks.color',
        '添加任务': 'tasks.add_task',
        '编辑任务': 'tasks.edit_task',
        '删除任务': 'tasks.delete_task',
        '模板': 'tasks.template',
        '主题配色': 'tasks.theme',

        # Account
        '账号管理': 'account.title',
        '未登录': 'account.not_logged_in',
        '邮箱': 'account.email',
        '密码': 'account.password',
        '确认密码': 'account.confirm_password',
        '验证码': 'account.verification_code',
        '发送验证码': 'account.send_code',
        '验证码已发送': 'account.code_sent',

        # Membership
        '会员中心': 'membership.title',
        '免费版': 'membership.free',
        '月度会员': 'membership.pro_monthly',
        '年度会员': 'membership.pro_yearly',
        '终身会员': 'membership.lifetime',
        '当前套餐': 'membership.current_plan',
        '升级': 'membership.upgrade',
        '价格': 'membership.price',

        # AI
        'AI功能': 'ai.title',
        'AI生成任务': 'ai.generate_tasks',
        'AI配色推荐': 'ai.generate_theme',
        'AI正在生成中...': 'ai.generating',
        '生成成功': 'ai.generate_success',
        '生成失败': 'ai.generate_failed',
    }

    # Check direct mapping first
    if chinese_str in DIRECT_MAP:
        return DIRECT_MAP[chinese_str]

    # Generate key from content
    # Remove punctuation and special characters
    clean = re.sub(r'[^\u4e00-\u9fff\w\s]', '', chinese_str)
    clean = clean.strip()

    if not clean or len(clean) > 50:
        return None

    # Create snake_case key from Chinese
    # This is a simplified version - use pinyin for better keys in production
    key_suffix = clean.replace(' ', '_')[:30]

    # Use category prefix
    base_key = f"{category}.{key_suffix}"

    # Ensure uniqueness
    if base_key not in counter_dict:
        counter_dict[base_key] = 0
        return base_key
    else:
        counter_dict[base_key] += 1
        return f"{base_key}_{counter_dict[base_key]}"


def main():
    print("=== Filtering UI Strings ===\n")

    # Load scan results
    with open('hardcoded_strings_report.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Re-scan to get full data (report only has first 100)
    from scan_hardcoded_strings import extract_chinese_strings, categorize_string, SCAN_FILES
    import os

    all_strings = []
    for file_path in SCAN_FILES:
        if os.path.exists(file_path):
            strings = extract_chinese_strings(file_path)
            all_strings.extend(strings)

    # Categorize
    for item in all_strings:
        item['category'] = categorize_string(item['chinese'])

    print(f"Total strings scanned: {len(all_strings)}")

    # Filter UI strings
    ui_strings = []
    non_ui_strings = defaultdict(list)

    for item in all_strings:
        is_ui, reason = is_ui_string(item)
        if is_ui:
            ui_strings.append(item)
        else:
            non_ui_strings[reason].append(item)

    print(f"UI strings to internationalize: {len(ui_strings)}")
    print(f"Non-UI strings (can stay Chinese): {len(all_strings) - len(ui_strings)}\n")

    # Show breakdown
    print("=== Non-UI Strings Breakdown ===")
    for reason, items in sorted(non_ui_strings.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {reason}: {len(items)}")

    # Generate translation keys
    print("\n=== Generating Translation Keys ===\n")

    counter_dict = {}
    translation_map = {}
    stats_by_category = defaultdict(int)

    for item in ui_strings:
        chinese = item['chinese']
        category = item['category']

        key = generate_translation_key(chinese, category, counter_dict)
        if key:
            if key not in translation_map:
                translation_map[key] = chinese
                stats_by_category[category] += 1

    print(f"Unique translation keys generated: {len(translation_map)}\n")

    print("=== Keys by Category ===")
    for cat in sorted(stats_by_category.keys()):
        print(f"  {cat}: {stats_by_category[cat]} keys")

    # Save translation mapping
    output = {
        'total_ui_strings': len(ui_strings),
        'unique_keys': len(translation_map),
        'ui_strings': ui_strings,
        'translation_map': translation_map,
        'stats_by_category': dict(stats_by_category)
    }

    with open('ui_strings_filtered.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n=== Results saved to: ui_strings_filtered.json ===")

    # Show samples
    print("\n=== Sample Translation Keys (first 20) ===\n")
    for i, (key, chinese) in enumerate(list(translation_map.items())[:20], 1):
        print(f"{i:2d}. {key}")
        print(f"    ZH: {chinese}")
        print()


if __name__ == '__main__':
    main()
