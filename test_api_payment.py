# -*- coding: utf-8 -*-
"""
测试新的API方式支付订单创建
验证从submit.php切换到mapi.php后订单创建是否正常
"""
import sys
import io

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("="*60)
print("测试API方式支付订单创建")
print("="*60)
print()

try:
    from gaiya.core.auth_client import AuthClient
    import requests
    import json

    # 1. 获取当前登录用户
    auth = AuthClient()
    user_id = auth.get_user_id()
    token = auth.access_token

    if not user_id or not token:
        print("❌ 未登录")
        sys.exit(1)

    print(f"✓ 当前用户: {user_id}")
    print()

    # 2. 测试创建订单 (使用新的API方式)
    print("测试创建订单 (API方式: mapi.php)...")
    api_url = "https://jindutiao.vercel.app/api/payment-create-order"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    data = {
        "user_id": user_id,
        "plan_type": "pro_monthly",
        "pay_type": "wxpay"  # 使用微信支付测试
    }

    print(f"  请求: POST {api_url}")
    print(f"  数据: {json.dumps(data, ensure_ascii=False)}")
    print()

    response = requests.post(api_url, headers=headers, json=data, timeout=15)

    print(f"  响应状态码: {response.status_code}")
    print()

    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print("✅ 订单创建成功!")
            print(f"  订单号: {result.get('out_trade_no')}")
            print(f"  订单金额: ¥{result.get('amount')}")
            print(f"  套餐名称: {result.get('plan_name')}")
            print()
            print(f"  支付链接: {result.get('payment_url', '')[:80]}...")

            # 检查是否有qrcode字段 (API方式特有)
            if result.get('qrcode'):
                print(f"  二维码链接: {result.get('qrcode', '')[:80]}...")
                print()
                print("✓ API方式特征: 包含qrcode字段")

            print()
            print("⚠️ 注意事项:")
            print("  1. 此订单使用API方式(mapi.php)创建")
            print("  2. 回调通知应该更可靠")
            print("  3. 完成支付后观察Vercel日志是否出现 [PAYMENT-NOTIFY]")
            print("  4. 检查会员状态是否正常更新")
        else:
            print(f"❌ 订单创建失败: {result.get('error')}")
    else:
        print(f"❌ HTTP错误: {response.status_code}")
        print(f"   响应: {response.text[:200]}")

except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*60)
