"""
Script to check desktop application's English translation quality
"""
import json
import re

# Load translation files
with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
    zh_cn = json.load(f)

with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
    en_us = json.load(f)


def has_chinese(text):
    """Check if text contains Chinese characters"""
    return bool(re.search(r'[\u4e00-\u9fff]', str(text)))


def get_all_keys(obj, prefix=''):
    """Recursively get all keys from nested dict"""
    keys = []
    for key, value in obj.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            keys.extend(get_all_keys(value, full_key))
        else:
            keys.append(full_key)
    return keys


def get_value_by_key(obj, key_path):
    """Get value from nested dict using dot notation"""
    keys = key_path.split('.')
    value = obj
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return None
    return value


# Get all translation keys
zh_keys = set(get_all_keys(zh_cn))
en_keys = set(get_all_keys(en_us))

print("=== Desktop Application English Translation Check ===\n")

# 1. Check for missing keys
missing_in_en = zh_keys - en_keys
missing_in_zh = en_keys - zh_keys

if missing_in_en:
    print(f"[ERROR] Missing keys in en_US.json ({len(missing_in_en)}):")
    for key in sorted(missing_in_en):
        print(f"  - {key}")
    print()
else:
    print("[OK] All Chinese keys exist in English\n")

if missing_in_zh:
    print(f"[WARNING] Extra keys in en_US.json ({len(missing_in_zh)}):")
    for key in sorted(missing_in_zh):
        print(f"  - {key}")
    print()

# 2. Check for Chinese characters in English translations
print("=== Checking for untranslated Chinese in en_US.json ===\n")
chinese_found = []

for key in sorted(zh_keys & en_keys):
    en_value = get_value_by_key(en_us, key)
    if en_value and has_chinese(en_value):
        zh_value = get_value_by_key(zh_cn, key)
        chinese_found.append({
            'key': key,
            'en': en_value,
            'zh': zh_value
        })

if chinese_found:
    print(f"[ERROR] Found {len(chinese_found)} English translations containing Chinese:\n")
    for item in chinese_found:
        print(f"Key: {item['key']}")
        print(f"  EN: {item['en']}")
        print(f"  ZH: {item['zh']}")
        print()
else:
    print("[OK] No Chinese characters found in English translations\n")

# 3. Check for identical translations (possible copy-paste errors)
print("=== Checking for identical translations ===\n")
identical = []

for key in sorted(zh_keys & en_keys):
    zh_value = get_value_by_key(zh_cn, key)
    en_value = get_value_by_key(en_us, key)

    # Skip emoji-only values
    if zh_value and en_value and zh_value == en_value:
        if not re.match(r'^[\U0001F000-\U0001F9FF\s]+$', str(zh_value)):
            identical.append({
                'key': key,
                'value': zh_value
            })

if identical:
    print(f"[WARNING] Found {len(identical)} identical translations (may need review):\n")
    for item in identical[:10]:  # Show first 10
        print(f"  {item['key']}: {item['value']}")
    if len(identical) > 10:
        print(f"  ... and {len(identical) - 10} more")
    print()

# 4. Summary statistics
print("=== Translation Statistics ===\n")
print(f"Total translation keys: {len(zh_keys)}")
print(f"Chinese (zh_CN): {len(zh_keys)} keys")
print(f"English (en_US): {len(en_keys)} keys")
print(f"Sections: {len(zh_cn)} ({', '.join(zh_cn.keys())})")
print()

# 5. Check translation coverage by section
print("=== Coverage by Section ===\n")
for section in sorted(zh_cn.keys()):
    zh_count = len(get_all_keys(zh_cn[section]))
    en_count = len(get_all_keys(en_us.get(section, {})))
    status = "OK" if zh_count == en_count else "MISMATCH"
    print(f"  {section}: {en_count}/{zh_count} [{status}]")

print("\n=== Check Complete ===")
