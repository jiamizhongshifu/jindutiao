"""
Batch Translation Generator
Generates high-quality English translations for remaining TODO items
"""
import json
import re

def translate_chinese_to_english(chinese_text):
    """
    Intelligent translation based on patterns and context
    """
    # Common translation mappings
    translations = {
        # Account related
        '邮箱': 'Email',
        '密码': 'Password',
        '登录': 'Login',
        '注册': 'Register',
        '退出登录': 'Logout',
        '需要登录': 'Login Required',
        '登录成功': 'Login Successful',
        '登录失败': 'Login Failed',
        '用户信息': 'User Information',
        '账号': 'Account',
        '会员等级': 'Membership Level',
        '会员': 'Member',
        '免费用户': 'Free User',
        '游客': 'Guest',

        # AI related
        'AI智能规划': 'AI Smart Planning',
        'AI生成': 'AI Generation',
        'AI服务': 'AI Service',
        'AI正在生成': 'AI is generating',
        'AI正在处理': 'AI is processing',
        '配额': 'Quota',
        '次/天': ' times/day',
        '生成成功': 'Generated successfully',
        '生成失败': 'Generation failed',
        '初始化': 'Initialization',
        '初始化失败': 'Initialization failed',

        # Config related
        '配置': 'Configuration',
        '设置': 'Settings',
        '外观': 'Appearance',
        '场景': 'Scene',
        '通知': 'Notifications',
        '基础设置': 'Basic Settings',
        '高级设置': 'Advanced Settings',
        '保存': 'Save',
        '加载': 'Load',
        '保存成功': 'Saved successfully',
        '保存失败': 'Failed to save',
        '加载成功': 'Loaded successfully',
        '加载失败': 'Failed to load',
        '应用': 'Apply',
        '重置': 'Reset',
        '清空': 'Clear',
        '删除': 'Delete',
        '确定': 'OK',
        '取消': 'Cancel',

        # Colors and appearance
        '颜色': 'Color',
        '背景颜色': 'Background Color',
        '文字颜色': 'Text Color',
        '透明度': 'Opacity',
        '圆角': 'Corner Radius',
        '阴影': 'Shadow',
        '高度': 'Height',
        '宽度': 'Width',
        '大小': 'Size',
        '位置': 'Position',
        '偏移': 'Offset',

        # Tasks and templates
        '任务': 'Task',
        '模板': 'Template',
        '主题': 'Theme',
        '配色': 'Color Scheme',
        '时间': 'Time',
        '开始时间': 'Start Time',
        '结束时间': 'End Time',

        # Messages
        '提示': 'Info',
        '警告': 'Warning',
        '错误': 'Error',
        '成功': 'Success',
        '失败': 'Failed',
        '请稍候': 'Please wait',
        '加载中': 'Loading',
        '处理中': 'Processing',

        # Common actions
        '选择': 'Select',
        '打开': 'Open',
        '关闭': 'Close',
        '刷新': 'Refresh',
        '更新': 'Update',
        '升级': 'Upgrade',
        '下载': 'Download',
        '安装': 'Install',

        # Days
        '星期': 'Day of week',
        '日期': 'Date',
        '每月': 'Monthly',
        '每日': 'Daily',

        # Payment
        '支付': 'Payment',
        '套餐': 'Plan',
        '价格': 'Price',
        '月度': 'Monthly',
        '年度': 'Yearly',

        # Common phrases
        '确定要': 'Are you sure you want to',
        '是否': 'Do you want to',
        '请输入': 'Please enter',
        '请选择': 'Please select',
        '请至少': 'Please at least',
    }

    # Handle complex patterns
    text = chinese_text.strip()

    # Pattern 1: Bullet points
    if text.startswith('•'):
        translated = text[1:].strip()
        for cn, en in translations.items():
            translated = translated.replace(cn, en)
        return f"• {translated}"

    # Pattern 2: Emoji at start
    emoji_match = re.match(r'^([\U0001F300-\U0001F9FF]|[\u2600-\u26FF]|[\u2700-\u27BF])\s*(.+)$', text)
    if emoji_match:
        emoji, rest = emoji_match.groups()
        translated = rest
        for cn, en in translations.items():
            translated = translated.replace(cn, en)
        return f"{emoji} {translated}"

    # Pattern 3: Questions (确定要...吗?)
    if '确定要' in text and '吗' in text:
        content = text.replace('确定要', '').replace('吗', '').replace('?', '').strip()
        for cn, en in translations.items():
            content = content.replace(cn, en)
        return f"Are you sure you want to {content.lower()}?"

    # Pattern 4: Format strings with placeholders
    if '{' in text and '}' in text:
        translated = text
        for cn, en in translations.items():
            translated = translated.replace(cn, en)
        return translated

    # Pattern 5: Colon-based labels (颜色:, 设置:)
    if text.endswith(':') or text.endswith('：'):
        content = text[:-1]
        for cn, en in translations.items():
            content = content.replace(cn, en)
        return f"{content}:"

    # Default: word-by-word replacement
    translated = text
    for cn, en in translations.items():
        translated = translated.replace(cn, en)

    # If no translation occurred, mark as needing manual review
    if translated == text and any('\u4e00' <= c <= '\u9fff' for c in text):
        return f"[REVIEW] {text}"

    return translated


def generate_batch_translations():
    """Generate translations for all TODO items"""
    # Load current state
    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    # Find TODO items
    def find_and_translate_todos(obj, path=''):
        changes = []
        for k, v in obj.items():
            current_path = f'{path}.{k}' if path else k
            if isinstance(v, dict):
                changes.extend(find_and_translate_todos(v, current_path))
            elif isinstance(v, str) and '[TODO]' in v:
                chinese = v.replace('[TODO] ', '')
                english = translate_chinese_to_english(chinese)
                changes.append((current_path, chinese, english))
        return changes

    changes = find_and_translate_todos(en_us)

    print(f"Found {len(changes)} TODO items to translate")

    # Apply translations
    def set_nested_value(obj, path, value):
        keys = path.split('.')
        for key in keys[:-1]:
            obj = obj[key]
        obj[keys[-1]] = value

    for path, chinese, english in changes:
        set_nested_value(en_us, path, english)

    # Save updated file
    with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
        json.dump(en_us, f, ensure_ascii=False, indent=2)

    # Count items needing manual review
    needs_review = [c for c in changes if '[REVIEW]' in c[2]]

    print(f"\n[OK] Translated {len(changes)} items")
    print(f"[INFO] Items needing manual review: {len(needs_review)}")

    if needs_review:
        print("\nFirst 10 items needing review:")
        for path, chinese, english in needs_review[:10]:
            print(f"  {path}: {chinese}")

    # Save review list
    if needs_review:
        with open('translation_review_needed.json', 'w', encoding='utf-8') as f:
            json.dump([
                {'key': path, 'chinese': chinese, 'auto_translation': english}
                for path, chinese, english in needs_review
            ], f, ensure_ascii=False, indent=2)
        print(f"\nReview list saved to: translation_review_needed.json")


if __name__ == '__main__':
    generate_batch_translations()
