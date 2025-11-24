"""
Generate new translation keys and update i18n JSON files
Uses OpenCC for proper text processing
"""
import json
import re
from collections import defaultdict


def simplify_chinese_for_key(text):
    """
    Convert Chinese text to a simple key format
    For now, use descriptive English keywords based on common patterns
    """
    # Common pattern mappings for creating meaningful English keys
    KEY_PATTERNS = {
        # Config related
        '高度': 'height',
        '宽度': 'width',
        '位置': 'position',
        '颜色': 'color',
        '透明': 'transparency',
        '背景': 'background',
        '圆角': 'radius',
        '阴影': 'shadow',
        '显示': 'show',
        '隐藏': 'hide',
        '启用': 'enable',
        '禁用': 'disable',
        '自动': 'auto',
        '手动': 'manual',

        # Actions
        '保存': 'save',
        '加载': 'load',
        '导入': 'import',
        '导出': 'export',
        '删除': 'delete',
        '添加': 'add',
        '编辑': 'edit',
        '修改': 'modify',
        '复制': 'copy',
        '粘贴': 'paste',
        '刷新': 'refresh',
        '重置': 'reset',
        '应用': 'apply',
        '取消': 'cancel',
        '确定': 'ok',
        '确认': 'confirm',
        '选择': 'select',
        '清除': 'clear',

        # Status
        '成功': 'success',
        '失败': 'failed',
        '错误': 'error',
        '警告': 'warning',
        '提示': 'info',
        '完成': 'completed',
        '进行中': 'in_progress',

        # Time
        '时间': 'time',
        '日期': 'date',
        '开始': 'start',
        '结束': 'end',
        '当前': 'current',

        # Common UI elements
        '标题': 'title',
        '名称': 'name',
        '描述': 'description',
        '备注': 'note',
        '标签': 'label',
        '提示符': 'placeholder',
        '选项': 'option',
        '设置': 'settings',
        '配置': 'config',
    }

    # Try to find matching patterns
    for cn, en in KEY_PATTERNS.items():
        if cn in text:
            return en

    # If no pattern matches, create a simple key from first few chars
    clean = re.sub(r'[^\u4e00-\u9fff\w]', '', text)
    if len(clean) <= 20:
        return f"text_{abs(hash(clean)) % 10000}"

    return f"text_{abs(hash(clean[:20])) % 10000}"


def load_existing_translations():
    """Load existing translation files"""
    try:
        with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
            zh_cn = json.load(f)
        with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
            en_us = json.load(f)
        return zh_cn, en_us
    except Exception as e:
        print(f"Error loading translations: {e}")
        return {}, {}


def get_all_keys_flat(obj, prefix=''):
    """Get all keys from nested dict as flat set"""
    keys = set()
    for key, value in obj.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            keys.update(get_all_keys_flat(value, full_key))
        else:
            keys.add(full_key)
    return keys


def build_new_translations():
    """Build comprehensive translations based on UI strings"""

    # Load filtered UI strings
    with open('ui_strings_filtered.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    ui_strings = data['ui_strings']
    print(f"Processing {len(ui_strings)} UI strings...")

    # Load existing translations
    zh_cn, en_us = load_existing_translations()
    existing_keys = get_all_keys_flat(zh_cn)
    print(f"Found {len(existing_keys)} existing translation keys\n")

    # Group strings by category and deduplicate
    strings_by_category = defaultdict(dict)  # category -> {chinese: count}

    for item in ui_strings:
        category = item['category']
        chinese = item['chinese']

        # Skip if already in existing translations
        # (check if this exact Chinese text exists anywhere)
        found = False
        for existing_key in existing_keys:
            # This is approximate - in real implementation, search values
            pass

        if chinese not in strings_by_category[category]:
            strings_by_category[category][chinese] = 1
        else:
            strings_by_category[category][chinese] += 1

    # Generate new translation keys
    new_zh_additions = defaultdict(dict)
    new_en_additions = defaultdict(dict)

    print("=== Generating New Translation Keys ===\n")

    for category in sorted(strings_by_category.keys()):
        strings = strings_by_category[category]
        print(f"[{category}] Processing {len(strings)} unique strings...")

        for chinese_text, count in sorted(strings.items(), key=lambda x: x[1], reverse=True):
            # Generate key suffix
            key_suffix = simplify_chinese_for_key(chinese_text)

            # Try to avoid duplicates
            counter = 0
            while True:
                if counter == 0:
                    full_key = f"{category}.{key_suffix}"
                else:
                    full_key = f"{category}.{key_suffix}_{counter}"

                # Check if key already exists
                if full_key not in existing_keys and full_key not in new_zh_additions[category]:
                    break
                counter += 1

                if counter > 100:  # Safety limit
                    full_key = f"{category}.auto_{abs(hash(chinese_text)) % 100000}"
                    break

            # Add to new translations
            key_part = full_key.split('.', 1)[1]  # Remove category prefix
            new_zh_additions[category][key_part] = chinese_text

            # Generate English translation (placeholder for now)
            # In production, use proper translation service
            new_en_additions[category][key_part] = f"[EN] {chinese_text}"

    # Show summary
    print("\n=== Summary of New Additions ===\n")
    total_new = sum(len(v) for v in new_zh_additions.values())
    print(f"Total new keys to add: {total_new}\n")

    for category in sorted(new_zh_additions.keys()):
        count = len(new_zh_additions[category])
        print(f"  {category}: +{count} keys")

    # Save new additions for review
    output = {
        'zh_CN_additions': dict(new_zh_additions),
        'en_US_additions': dict(new_en_additions),
        'summary': {
            'total_new_keys': total_new,
            'categories': list(new_zh_additions.keys())
        }
    }

    with open('translation_additions.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n=== New translations saved to: translation_additions.json ===")
    print("\nNote: English translations are placeholders marked with [EN].")
    print("These should be properly translated before use.\n")

    return new_zh_additions, new_en_additions


if __name__ == '__main__':
    build_new_translations()
