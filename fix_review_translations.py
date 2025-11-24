"""
Fix translations that need manual review
"""
import json

# Manual high-quality translations for common terms
MANUAL_TRANSLATIONS = {
    # Language and UI
    '简体中文': 'Simplified Chinese',
    'English': 'English',

    # Status
    '启用': 'Enabled',
    '禁用': 'Disabled',

    # Days of week
    '周一': 'Monday',
    '周二': 'Tuesday',
    '周三': 'Wednesday',
    '周四': 'Thursday',
    '周五': 'Friday',
    '周六': 'Saturday',
    '周日': 'Sunday',

    # Common terms
    '冲突': 'Conflict',
    '规则类型': 'Rule Type',
    '该规则与现有规则冲突，请检查': 'This rule conflicts with existing rules, please check',
    '无效的规则索引': 'Invalid rule index',

    # Size and details
    '详细': 'Details',
    '细': 'Fine',
    '标准': 'Standard',
    '粗': 'Thick',
    '很粗': 'Very Thick',
    '小': 'Small',
    '中': 'Medium',
    '大': 'Large',

    # Template auto-apply
    '模板自动应用': 'Template Auto-Apply',

    # Technical terms
    '(line=线条, image=图片, gif=动画)': '(line, image, gif)',
    '(最小值,最大值)': '(min, max)',
    '(100%=原速, 200%=2倍速)': '(100%=normal, 200%=2x speed)',

    # Example text
    '示例: 早上9点开始1小时,然后编写代码到中午5点,休息12点休息1小时,下午6点健身...':
        'Example: Start at 9am for 1 hour, then code until 5pm, lunch break at 12pm for 1 hour, gym at 6pm...',

    # Pro membership features
    '✓ 全部免费功能': '✓ All free features',
    '✓ 无限次 AI智能配色': '✓ Unlimited AI color schemes',
    '✓ 无限次 AI任务生成': '✓ Unlimited AI task generation',
    '✓ 云端数据同步': '✓ Cloud data sync',
    '✓ 优先技术支持': '✓ Priority support',
    '✓ 早期访问新功能': '✓ Early access to new features',

    # Partnership
    '成为 GaiYa 合伙人': 'Become a GaiYa Partner',
    '合伙人专属权益': 'Exclusive Partner Benefits',
    '引荐返现': 'Referral Rewards',

    # Version and updates
    '当前版本': 'Current Version',
    '最新版本': 'Latest Version',
    '检查更新': 'Check for Updates',
    '更新可用': 'Update Available',

    # Stripe payment
    '[STRIPE] 创建Checkout Session': '[STRIPE] Creating Checkout Session',
    '[STRIPE] 用户取消支付': '[STRIPE] Payment cancelled by user',

    # Other common phrases
    '建议': 'Recommended',
    '立即体验': 'Try Now',
    '了解更多': 'Learn More',
    '开始使用': 'Get Started',
    '管理': 'Manage',
}

def fix_review_translations():
    # Load review items
    with open('translation_review_needed.json', 'r', encoding='utf-8') as f:
        review_items = json.load(f)

    # Load current en_US
    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    # Helper function to set nested value
    def set_nested_value(obj, path, value):
        keys = path.split('.')
        for key in keys[:-1]:
            if key not in obj:
                obj[key] = {}
            obj = obj[key]
        obj[keys[-1]] = value

    # Fix each review item
    fixed_count = 0
    still_need_review = []

    for item in review_items:
        key = item['key']
        chinese = item['chinese']

        # Try to find manual translation
        if chinese in MANUAL_TRANSLATIONS:
            english = MANUAL_TRANSLATIONS[chinese]
            set_nested_value(en_us, key, english)
            fixed_count += 1
        else:
            # Keep as needing review
            still_need_review.append(item)

    # Save updated en_US
    with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
        json.dump(en_us, f, ensure_ascii=False, indent=2)

    print(f"Fixed {fixed_count} translations with manual mappings")
    print(f"Still need review: {len(still_need_review)}")

    # Save remaining review items
    if still_need_review:
        with open('translation_still_review.json', 'w', encoding='utf-8') as f:
            json.dump(still_need_review, f, ensure_ascii=False, indent=2)
        print("\nRemaining review items saved to: translation_still_review.json")
        print("\nFirst 10 items still needing review:")
        for i, item in enumerate(still_need_review[:10], 1):
            print(f"  {i}. {item['chinese']}")
    else:
        print("\n[OK] All review items have been fixed!")

if __name__ == '__main__':
    fix_review_translations()
