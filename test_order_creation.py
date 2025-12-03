# -*- coding: utf-8 -*-
"""
测试订单创建详细错误
"""
import sys
import io

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("="*60)
print("测试订单创建详细错误")
print("="*60)
print()

try:
    # 1. 测试本地zpay_manager
    print("1. 测试本地zpay_manager.get_plan_info()...")
    sys.path.insert(0, 'api')
    from zpay_manager import ZPayManager

    zpay = ZPayManager()

    for plan_type in ['pro_monthly', 'pro_yearly', 'lifetime']:
        info = zpay.get_plan_info(plan_type)
        print(f"  {plan_type}: 名称={info['name']}, 价格=¥{info['price']}")

    print("  ✓ 本地zpay_manager工作正常")
    print()

    # 2. 测试线上API
    print("2. 测试线上创建订单API...")
    import requests
    import json
    from gaiya.core.auth_client import AuthClient

    auth = AuthClient()
    user_id = auth.get_user_id()
    token = auth.access_token

    if not user_id or not token:
        print("  ❌ 未登录")
        sys.exit(1)

    print(f"  用户ID: {user_id}")

    api_url = "https://jindutiao.vercel.app/api/payment-create-order"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    data = {
        "user_id": user_id,
        "plan_type": "pro_monthly",
        "pay_type": "alipay"
    }

    print(f"  请求: POST {api_url}")
    print(f"  数据: {json.dumps(data, ensure_ascii=False)}")
    print()

    response = requests.post(api_url, headers=headers, json=data, timeout=15)

    print(f"  响应状态码: {response.status_code}")
    print(f"  响应头: {dict(response.headers)}")
    print()
    print(f"  响应内容:")
    print(f"  {response.text}")
    print()

    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print(f"  ✓ 订单创建成功!")
            print(f"    订单金额: ¥{result.get('amount')}")
            print(f"    支付链接: {result.get('pay_url', '')[:50]}...")
        else:
            print(f"  ❌ 订单创建失败: {result.get('error')}")
    else:
        print(f"  ❌ HTTP错误: {response.status_code}")
        if response.text:
            print(f"     可能的错误: {response.text[:200]}")

except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    print()
    print("完整错误:")
    traceback.print_exc()

print()
print("="*60)
