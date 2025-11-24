#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加 quota_exhausted_dialog.py 的翻译键到 i18n 文件
"""

import json

def add_quota_dialog_keys():
    """添加quota_exhausted_dialog的翻译键"""

    # 定义所有翻译键（中文和英文）
    quota_keys_zh = {
        "quota_dialog": {
            "title": {
                "window": "AI配额已用完",
                "dialog": "🤖 今日AI配额已用完"
            },
            "info": {
                "message": "免费用户每天有 3 次AI任务规划配额。\n你今天的配额已经用完了。\n\n升级会员即可享受："
            },
            "benefits": {
                "unlimited_ai": "✅ 无限AI任务生成配额",
                "remove_watermark": "✅ 去除进度条水印",
                "full_statistics": "✅ 完整数据统计报告",
                "more_features": "✅ 更多高级功能..."
            },
            "price": {
                "pricing": "💰 月度会员仅需 ¥29/月，年度会员 ¥199/年"
            },
            "button": {
                "later": "明天再说",
                "upgrade": "升级会员"
            }
        }
    }

    quota_keys_en = {
        "quota_dialog": {
            "title": {
                "window": "AI Quota Exhausted",
                "dialog": "🤖 Today's AI Quota Exhausted"
            },
            "info": {
                "message": "Free users have 3 AI task planning quotas per day.\nYou have used up today's quota.\n\nUpgrade to membership to enjoy:"
            },
            "benefits": {
                "unlimited_ai": "✅ Unlimited AI task generation quota",
                "remove_watermark": "✅ Remove progress bar watermark",
                "full_statistics": "✅ Complete data statistics report",
                "more_features": "✅ More advanced features..."
            },
            "price": {
                "pricing": "💰 Monthly membership only ¥29/month, annual membership ¥199/year"
            },
            "button": {
                "later": "Maybe Tomorrow",
                "upgrade": "Upgrade Membership"
            }
        }
    }

    # 读取现有的i18n文件
    with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
        zh_cn = json.load(f)

    with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
        en_us = json.load(f)

    # 添加quota_dialog命名空间
    zh_cn['quota_dialog'] = quota_keys_zh['quota_dialog']
    en_us['quota_dialog'] = quota_keys_en['quota_dialog']

    # 写回文件
    with open('i18n/zh_CN.json', 'w', encoding='utf-8') as f:
        json.dump(zh_cn, f, ensure_ascii=False, indent=2)

    with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
        json.dump(en_us, f, ensure_ascii=False, indent=2)

    print("翻译键添加完成！")
    print(f"zh_CN.json: {len(zh_cn)} 个顶级命名空间")
    print(f"en_US.json: {len(en_us)} 个顶级命名空间")

    # 统计quota_dialog命名空间的键数量
    def count_keys(d):
        count = 0
        for k, v in d.items():
            if isinstance(v, dict):
                count += count_keys(v)
            else:
                count += 1
        return count

    key_count = count_keys(quota_keys_zh['quota_dialog'])
    print(f"新增 quota_dialog 命名空间翻译键: {key_count} 个")

if __name__ == '__main__':
    add_quota_dialog_keys()
