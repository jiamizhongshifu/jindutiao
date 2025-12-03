# -*- coding: utf-8 -*-
"""
通过Vercel API查询订单状态
(使用Vercel环境变量中的凭证,而非本地凭证)
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
print("通过Vercel API查询订单状态")
print("="*60)
print()

# 之前支付的订单号
order_id = "GAIYA1764727660522308748"

try:
    from gaiya.core.auth_client import AuthClient

    # 1. 获取用户信息
    auth = AuthClient()
    user_id = auth.get_user_id()
    token = auth.access_token

    if not user_id or not token:
        print("❌ 未登录")
        sys.exit(1)

    print(f"✓ 用户ID: {user_id}")
    print(f"  查询订单: {order_id}")
    print()

    # 2. 调用Vercel API查询订单
    api_url = "https://jindutiao.vercel.app/api/payment-query"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    data = {
        "out_trade_no": order_id
    }

    response = requests.post(api_url, headers=headers, json=data, timeout=15)

    print(f"响应状态码: {response.status_code}")
    print()

    if response.status_code == 200:
        result = response.json()
        print("查询结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print()

        if result.get("success"):
            status = result.get("status", 0)
            if status == 1:
                print("✅ 订单已支付!")
                print()
                print(f"  订单金额: ¥{result.get('money', 'N/A')}")
                print(f"  支付方式: {result.get('type', 'N/A')}")
                print(f"  创建时间: {result.get('addtime', 'N/A')}")
                print(f"  完成时间: {result.get('endtime', 'N/A')}")
                print()
                print("⚠️ 订单已支付,但会员状态未更新")
                print("   → 说明Z-Pay回调确实未到达Vercel")
                print()
                print("可能原因:")
                print("  1. Z-Pay回调被防火墙拦截")
                print("  2. notify_url配置有问题")
                print("  3. Z-Pay服务端问题")
            else:
                print("⚠️ 订单未支付")
        else:
            print(f"❌ 查询失败: {result.get('error', 'Unknown error')}")
    else:
        print(f"❌ HTTP错误: {response.status_code}")
        print(f"   响应: {response.text[:200]}")

except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*60)
