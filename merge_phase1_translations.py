"""
Merge Phase 1 Critical Translations into i18n JSON files
"""
import json

def merge_translations():
    # Load Phase 1 translations
    with open('phase1_critical_translations.json', 'r', encoding='utf-8') as f:
        phase1 = json.load(f)

    # Load existing i18n files
    with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
        zh_cn = json.load(f)
    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    # Merge function
    def deep_merge(target, source):
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                deep_merge(target[key], value)
            else:
                target[key] = value

    # Merge Phase 1 translations
    deep_merge(zh_cn, phase1['translations_zh'])
    deep_merge(en_us, phase1['translations_en'])

    # Count updates
    def count_keys(obj):
        count = 0
        for v in obj.values():
            if isinstance(v, dict):
                count += count_keys(v)
            else:
                count += 1
        return count

    zh_keys = count_keys(phase1['translations_zh'])
    en_keys = count_keys(phase1['translations_en'])

    print(f"Merging {zh_keys} Chinese translations...")
    print(f"Merging {en_keys} English translations...")

    # Save updated files
    with open('i18n/zh_CN.json', 'w', encoding='utf-8') as f:
        json.dump(zh_cn, f, ensure_ascii=False, indent=2)
    with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
        json.dump(en_us, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Successfully merged Phase 1 translations")
    print(f"Updated files:")
    print(f"  - i18n/zh_CN.json")
    print(f"  - i18n/en_US.json")

    # Verify no [TODO] in merged keys
    def find_todos(obj, path=''):
        todos = []
        for k, v in obj.items():
            current_path = f"{path}.{k}" if path else k
            if isinstance(v, dict):
                todos.extend(find_todos(v, current_path))
            elif isinstance(v, str) and '[TODO]' in v:
                todos.append(current_path)
        return todos

    todos = find_todos(en_us)
    print(f"\n[INFO] Remaining [TODO] placeholders: {len(todos)}")

    if todos:
        print(f"Next batch of keys to translate: {min(10, len(todos))}")
        for todo in todos[:10]:
            print(f"  - {todo}")

if __name__ == '__main__':
    merge_translations()
