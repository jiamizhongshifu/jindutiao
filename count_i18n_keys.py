import json

def count_keys(d):
    count = 0
    for k, v in d.items():
        if isinstance(v, dict):
            count += count_keys(v)
        else:
            count += 1
    return count

with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total keys: {count_keys(data)}")
