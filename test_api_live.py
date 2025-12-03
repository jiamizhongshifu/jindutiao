# -*- coding: utf-8 -*-
"""
测试线上API的实际价格
"""
import sys
import io
import requests
import json

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("="*60)
print("测试线上API价格")
print("="*60)
print()

# 从本地auth读取user_id和token
try:
    from gaiya.core.auth_client import AuthClient
    auth = AuthClient()
    user_id = auth.get_user_id()
    token = auth.access_token

    if not user_id or not token:
        print("❌ 未登录,无法测试")
        sys.exit(1)

    print(f"✓ 用户ID: {user_id}")
    print()

    # 测试创建订单API
    print("1. 测试创建Pro月度订单...")
    api_url = "https://jindutiao.vercel.app/api/create-order"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    data = {
        "user_id": user_id,
        "plan_type": "pro_monthly"
    }

    print(f"   请求URL: {api_url}")
    print(f"   请求数据: {json.dumps(data, ensure_ascii=False)}")
    print()

    response = requests.post(api_url, headers=headers, json=data, timeout=10)

    print(f"   响应状态码: {response.status_code}")
    print(f"   响应内容:")

    result = response.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print()

    if result.get("success"):
        amount = result.get("amount")
        print(f"✓ 订单创建成功")
        print(f"  订单金额: ¥{amount}")

        if amount == 0.1:
            print("  ✅ 价格正确! (¥0.1)")
        else:
            print(f"  ❌ 价格错误! 期望¥0.1, 实际¥{amount}")
    else:
        print(f"❌ 订单创建失败: {result.get('error')}")

except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*60)
