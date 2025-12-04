# -*- coding: utf-8 -*-
"""
测试手动升级完整流程
验证:
1. 创建订单(获取二维码)
2. 手动触发升级
"""
import sys
import io

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("="*60)
print("测试手动升级完整流程")
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

    # 2. 创建测试订单
    print("步骤1: 创建测试订单...")
    api_url = "https://jindutiao.vercel.app/api/payment-create-order"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    data = {
        "user_id": user_id,
        "plan_type": "pro_monthly",
        "pay_type": "wxpay"
    }

    response = requests.post(api_url, headers=headers, json=data, timeout=15)

    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            out_trade_no = result.get('out_trade_no')
            print(f"✅ 订单创建成功!")
            print(f"   订单号: {out_trade_no}")
            print(f"   二维码URL: {result.get('qrcode_url', '无')[:60]}...")
            print()

            # 3. 测试手动升级API
            print("步骤2: 测试手动升级...")
            print("⚠️  注意: 这将直接升级账户(用于测试)")

            upgrade_result = auth.trigger_manual_upgrade(
                out_trade_no=out_trade_no,
                user_id=user_id,
                plan_type="pro_monthly"
            )

            if upgrade_result.get("success"):
                print("✅ 手动升级成功!")
                print(f"   会员等级: {upgrade_result.get('membership_tier')}")
                print(f"   到期时间: {upgrade_result.get('membership_expire_at')}")
            else:
                print(f"❌ 手动升级失败: {upgrade_result.get('error')}")
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
