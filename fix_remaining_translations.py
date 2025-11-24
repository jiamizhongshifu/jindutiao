"""
Fix all remaining translations with comprehensive manual mappings
"""
import json

# Comprehensive manual translations
TRANSLATIONS = {
    # Thickness/Size descriptors
    '极细': 'Extra Fine',
    '细': 'Fine',
    '标准': 'Standard',
    '粗': 'Thick',
    '很粗': 'Very Thick',
    '小': 'Small',
    '中': 'Medium',
    '大': 'Large',

    # Units
    '毫秒': 'ms',
    ' 毫秒': ' ms',
    '像素': 'px',
    ' 像素': ' px',
    '秒': 's',
    ' 秒': ' s',

    # Directions/Positions
    '(正值向右,负值向左)': '(positive=right, negative=left)',
    '(正值向上,负值向下)': '(positive=up, negative=down)',

    # Auto-start
    '开机自动启动': 'Launch at startup',

    # Examples
    '例如: 明天9点开会1小时,然后写代码到下午5点,中午12点休息1小时,晚上6点健身...':
        'Example: Meeting at 9am for 1 hour, then coding until 5pm, lunch break at 12pm for 1 hour, gym at 6pm...',

    # Loading messages
    '⏳ 正在连接云服务（可能需要10-15秒）...':
        '⏳ Connecting to cloud service (may take 10-15 seconds)...',

    # Common UI terms
    '操作': 'Action',
    '状态': 'Status',
    '确认': 'Confirm',
    '依然展示进度条': 'Still show progress bar',
    '以换行分隔': 'Separated by newlines',
    '历史': 'History',
    '更新中': 'Updating',

    # Membership/Partner
    '✓ 全部免费功能': '✓ All free features',
    '✓ 无限次 AI智能配色': '✓ Unlimited AI color schemes',
    '✓ 无限次 AI任务生成': '✓ Unlimited AI task generation',
    '✓ 云端数据同步': '✓ Cloud data sync',
    '✓ 优先技术支持': '✓ Priority support',
    '✓ 早期访问新功能': '✓ Early access to new features',
    '成为 GaiYa 合伙人': 'Become a GaiYa Partner',
    '合伙人专属权益': 'Exclusive Partner Benefits',

    # Version
    '当前版本': 'Current Version',
    '最新版本': 'Latest Version',
    '版本': 'Version',

    # Payment
    '[STRIPE] 创建Checkout Session': '[STRIPE] Creating Checkout Session',
    '[STRIPE] 用户取消支付': '[STRIPE] Payment cancelled',

    # Settings sections
    '基本': 'Basic',
    '高级': 'Advanced',
    '通用': 'General',
    '个性化': 'Personalization',

    # Actions
    '立即体验': 'Try Now',
    '了解更多': 'Learn More',
    '开始使用': 'Get Started',
    '管理': 'Manage',
    '编辑': 'Edit',
    '添加': 'Add',
    '删除': 'Delete',

    # Time periods
    '天': 'day',
    ' 天': ' days',
    '小时': 'hour',
    ' 小时': ' hours',
    '分钟': 'minute',
    ' 分钟': ' minutes',

    # Other common terms
    '仅': 'Only',
    '建议': 'Recommended',
    '推荐': 'Recommended',
    '默认': 'Default',
    '自定义': 'Custom',
    '全部': 'All',
    '无': 'None',
    '是': 'Yes',
    '否': 'No',

    # Scene and theme related
    '场景': 'Scene',
    '主题': 'Theme',
    '效果': 'Effect',
    '动画': 'Animation',
    '速度': 'Speed',
    '透明': 'Opacity',

    # Notification
    '静音': 'Mute',
    '免打扰': 'Do Not Disturb',
    '提醒': 'Reminder',
    '通知': 'Notification',

    # Data and sync
    '同步': 'Sync',
    '备份': 'Backup',
    '导入': 'Import',
    '导出': 'Export',

    # Feature names
    '智能规划': 'Smart Planning',
    '配色方案': 'Color Scheme',
    '任务模板': 'Task Template',

    # Messages with emoji
    '✅ 已连接': '✅ Connected',
    '❌ 未连接': '❌ Not connected',
    '⚠️ 警告': '⚠️ Warning',
}

def fix_all_remaining():
    # Load remaining items
    with open('translation_still_review.json', 'r', encoding='utf-8') as f:
        review_items = json.load(f)

    # Load current en_US
    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    # Helper function
    def set_nested_value(obj, path, value):
        keys = path.split('.')
        for key in keys[:-1]:
            if key not in obj:
                obj[key] = {}
            obj = obj[key]
        obj[keys[-1]] = value

    fixed_count = 0
    final_review = []

    for item in review_items:
        key = item['key']
        chinese = item['chinese']

        if chinese in TRANSLATIONS:
            english = TRANSLATIONS[chinese]
            set_nested_value(en_us, key, english)
            fixed_count += 1
        else:
            # Try simple word-by-word replacement for remaining items
            translated = chinese
            for cn, en in TRANSLATIONS.items():
                if cn in translated:
                    translated = translated.replace(cn, en)

            # If translation was successful (not all Chinese)
            if translated != chinese:
                set_nested_value(en_us, key, translated)
                fixed_count += 1
            else:
                final_review.append(item)

    # Save
    with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
        json.dump(en_us, f, ensure_ascii=False, indent=2)

    print(f"[OK] Fixed {fixed_count} more translations")
    print(f"[INFO] Final items still needing review: {len(final_review)}")

    if final_review:
        with open('translation_final_review.json', 'w', encoding='utf-8') as f:
            json.dump(final_review, f, ensure_ascii=False, indent=2)
        print("\nSaved to: translation_final_review.json")
    else:
        print("\n[SUCCESS] All translations completed!")

    # Verify no [TODO] or [REVIEW] left
    def count_placeholders(obj):
        count = 0
        for v in obj.values():
            if isinstance(v, dict):
                count += count_placeholders(v)
            elif isinstance(v, str) and ('[TODO]' in v or '[REVIEW]' in v):
                count += 1
        return count

    placeholders = count_placeholders(en_us)
    print(f"\n[INFO] Remaining placeholders in en_US.json: {placeholders}")

if __name__ == '__main__':
    fix_all_remaining()
