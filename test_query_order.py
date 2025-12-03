# -*- coding: utf-8 -*-
"""
查询订单状态
"""
import sys
import io

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("="*60)
print("查询订单状态")
print("="*60)
print()

order_id = "7d2368"  # 从你的截图中获取的订单ID

try:
    # 1. 查询Supabase中的订单记录
    print(f"1. 查询订单 {order_id} 的Supabase记录...")
    import os
    from supabase import create_client

    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("  ⚠️ Supabase凭证未配置,无法查询")
    else:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        # 查询支付记录
        result = supabase.table("payments").select("*").eq("order_id", order_id).execute()

        if result.data:
            print(f"  ✓ 找到支付记录:")
            for record in result.data:
                print(f"    - ID: {record.get('id')}")
                print(f"    - 用户: {record.get('user_id')}")
                print(f"    - 金额: ¥{record.get('amount')}")
                print(f"    - 状态: {record.get('status')}")
                print(f"    - 创建时间: {record.get('created_at')}")
        else:
            print(f"  ❌ 未找到订单记录 (可能回调未触发)")

    print()

    # 2. 通过API查询订单
    print(f"2. 通过API查询订单状态...")
    import requests
    import json
    from gaiya.core.auth_client import AuthClient

    auth = AuthClient()
    token = auth.access_token

    api_url = f"https://jindutiao.vercel.app/api/payment-query"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    data = {
        "out_trade_no": order_id
    }

    response = requests.post(api_url, headers=headers, json=data, timeout=10)

    print(f"  响应状态: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"  响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    else:
        print(f"  错误: {response.text}")

except Exception as e:
    print(f"❌ 查询失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*60)
