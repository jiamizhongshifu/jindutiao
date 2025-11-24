import json

# Read translation files
with open('locales/zh_CN.json', 'r', encoding='utf-8') as f:
    zh = json.load(f)

with open('locales/en_US.json', 'r', encoding='utf-8') as f:
    en = json.load(f)

# Check checkout section
zh_checkout = zh.get('checkout', {})
en_checkout = en.get('checkout', {})

print('=== Checkout Section Comparison ===')
print(f'zh_CN has {len(zh_checkout)} keys')
print(f'en_US has {len(en_checkout)} keys')

# Compare all keys
same_count = 0
diff_count = 0

for key in zh_checkout.keys():
    zh_val = zh_checkout.get(key, 'N/A')
    en_val = en_checkout.get(key, 'N/A')
    if zh_val == en_val:
        same_count += 1
    else:
        diff_count += 1

print(f'\nSame values: {same_count}')
print(f'Different values: {diff_count}')

# Check if identical
if zh_checkout == en_checkout:
    print('\n!!! WARNING: zh_CN.checkout is IDENTICAL to en_US.checkout !!!')
    print('This needs to be fixed!')
else:
    print('\nCheckout sections are different (good)')
