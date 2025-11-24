"""
Complete all remaining translations - Final round
"""
import json

# Final comprehensive translations
FINAL_TRANSLATIONS = {
    # Common
    '未知': 'Unknown',
    '用户': 'User',
    '此功能': 'This feature',
    '下班': 'Off work',
    '选色': 'Pick Color',
    '任意': 'Any',
    '输入为空': 'Input is empty',

    # Pricing
    '/月': '/month',
    '/年': '/year',
    '节省 40%': 'Save 40%',
    '所有免费功能 +': 'All free features +',
    '永久有效': 'Lifetime Access',
    '永久': 'Lifetime',
    '终身可用': 'Lifetime Access',
    '一次购买,终身可用': 'One-time purchase, lifetime access',
    '一次付费': 'One-time payment',
    '到期后不会自动扣费': 'No automatic renewal after expiration',
    '有效期': 'Validity Period',
    '支持 Visa/Mastercard/Amex': 'Supports Visa/Mastercard/Amex',
    '渠道': 'Channel',

    # Features
    '统计报告分析': 'Statistical Report Analysis',
    '去除进度条水印': 'Remove Progress Bar Watermark',
    '番茄时钟': 'Pomodoro Timer',
    '抢先体验新功能': 'Early Access to New Features',
    '功能特性': 'Features',
    '【核心功能】': '[Core Features]',

    # Partnership
    '成为合伙人': 'Become a Partner',
    '限量1000名': 'Limited to 1000 partners',
    '33%引荐返现比例': '33% referral cashback',
    '引荐返现比例': 'Referral Cashback Rate',
    '专属合伙人社群': 'Exclusive Partner Community',
    '优先体验所有新功能': 'Priority Access to All New Features',
    '专属1v1咨询服务': 'Exclusive 1-on-1 Consulting',
    '1v1咨询服务': '1-on-1 Consulting',
    '共同成长,分享价值': 'Grow together, share value',
    '邀请您共同成长，共享价值': 'Inviting you to grow together and share value',
    '<a href="#" style="color: #666666; text-decoration: none;">📜 阅读合伙人邀请函</a>':
        '<a href="#" style="color: #666666; text-decoration: none;">📜 Read Partner Invitation</a>',

    # Messages
    '感谢您的支持！': 'Thank you for your support!',
    '可能的原因：\\n': 'Possible reasons:\\n',
    '调试信息：\\n': 'Debug info:\\n',
    '网络请求超时，请检查网络连接': 'Network request timeout, please check your connection',

    # Examples
    '示例: 22:00 - 08:00 表示晚上10点到早上8点不打扰':
        'Example: 22:00 - 08:00 means do not disturb from 10pm to 8am',

    # Templates
    '  - weekday: 工作日': '  - weekday: Weekday',
    '  - weekend: 周末': '  - weekend: Weekend',
    '  - holiday: 节假日': '  - holiday: Holiday',
    'custom_template_combo未找到': 'custom_template_combo not found',

    # Status
    '(将在开机时自动启动)': '(will launch automatically at startup)',
    '(未启用)': '(not enabled)',

    # File types
    '图片文件 (*.jpg *.jpeg *.png *.gif *.webp)': 'Image Files (*.jpg *.jpeg *.png *.gif *.webp)',

    # Cloud
    '⏳ 正在连接云服务...': '⏳ Connecting to cloud service...',

    # Feedback
    '扫描二维码，直接反馈问题': 'Scan QR code to report issues directly',
    '扫一扫上面的二维码图案，加我为朋友。': 'Scan the QR code above to add me as a friend.',
    '<a href="#" style="color: #2196F3; text-decoration: none;">直接向创始人反馈问题</a>':
        '<a href="#" style="color: #2196F3; text-decoration: none;">Report issues directly to founder</a>',

    # API/Technical
    '[STRIPE] 调用API: /api/stripe-create-checkout':
        '[STRIPE] Calling API: /api/stripe-create-checkout',
}

def complete_all_translations():
    # Load final review items
    with open('translation_final_review.json', 'r', encoding='utf-8') as f:
        review_items = json.load(f)

    # Load current en_US
    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    # Helper
    def set_nested_value(obj, path, value):
        keys = path.split('.')
        for key in keys[:-1]:
            if key not in obj:
                obj[key] = {}
            obj = obj[key]
        obj[keys[-1]] = value

    completed = 0
    still_missing = []

    for item in review_items:
        key = item['key']
        chinese = item['chinese']

        if chinese in FINAL_TRANSLATIONS:
            set_nested_value(en_us, key, FINAL_TRANSLATIONS[chinese])
            completed += 1
        else:
            still_missing.append(item)

    # Save
    with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
        json.dump(en_us, f, ensure_ascii=False, indent=2)

    print(f"[OK] Completed {completed} final translations")
    print(f"[INFO] Still missing: {len(still_missing)}")

    if still_missing:
        with open('translation_still_missing.json', 'w', encoding='utf-8') as f:
            json.dump(still_missing, f, ensure_ascii=False, indent=2)
        print("\nSaved to: translation_still_missing.json")

    # Final verification
    def count_review_markers(obj):
        count = 0
        for v in obj.values():
            if isinstance(v, dict):
                count += count_review_markers(v)
            elif isinstance(v, str) and ('[TODO]' in v or '[REVIEW]' in v):
                count += 1
        return count

    markers = count_review_markers(en_us)
    total_keys = sum(1 for line in json.dumps(en_us).split('\n') if '":' in line)

    print(f"\n=== Translation Status ===")
    print(f"Total translation keys: ~{total_keys}")
    print(f"Remaining markers: {markers}")
    print(f"Completion rate: {((total_keys - markers) / total_keys * 100):.1f}%")

    if markers == 0:
        print("\n[SUCCESS] All translations completed! 🎉")
    else:
        print(f"\n[INFO] {markers} items still need manual review")

if __name__ == '__main__':
    complete_all_translations()
