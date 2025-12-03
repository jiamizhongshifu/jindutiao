# -*- coding: utf-8 -*-
"""
直接测试Z-Pay API方式创建订单,查看实际返回值
"""
import sys
import io

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("="*60)
print("直接测试Z-Pay API方式")
print("="*60)
print()

try:
    sys.path.insert(0, 'api')
    from zpay_manager import ZPayManager
    from gaiya.core.auth_client import AuthClient
    import json

    # 1. 获取用户信息
    auth = AuthClient()
    user_id = auth.get_user_id()

    if not user_id:
        print("❌ 未登录")
        sys.exit(1)

    print(f"✓ 用户ID: {user_id}")
    print()

    # 2. 创建zpay实例
    zpay = ZPayManager()
    print(f"✓ Z-Pay实例已创建")
    print(f"  API URL: {zpay.api_url}")
    print()

    # 3. 测试API方式创建订单
    print("测试create_api_order()...")
    out_trade_no = f"TEST_API_{int(__import__('time').time())}"

    result = zpay.create_api_order(
        out_trade_no=out_trade_no,
        name="测试订单-API方式",
        money=0.1,
        pay_type="wxpay",
        notify_url="https://jindutiao.vercel.app/api/payment-notify",
        clientip="127.0.0.1",
        param=json.dumps({"user_id": user_id, "plan_type": "pro_monthly"})
    )

    print()
    print("API方式返回结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print()

    if result.get("success"):
        print("✅ API方式订单创建成功")
        print()
        print("返回字段分析:")
        print(f"  payurl: {result.get('payurl', 'N/A')[:80]}...")
        print(f"  qrcode: {result.get('qrcode', 'N/A')[:80]}...")
        print(f"  trade_no: {result.get('trade_no', 'N/A')}")

        # 检查payurl是否包含mapi
        payurl = result.get('payurl', '')
        if 'mapi' in payurl:
            print()
            print("✓ payurl包含'mapi'字样,确认使用API方式")
        elif 'submit' in payurl:
            print()
            print("⚠️ payurl包含'submit'字样,可能仍然是页面跳转方式")
            print("   这可能是Z-Pay返回的固定格式")
    else:
        print(f"❌ 创建失败: {result.get('error')}")

    print()
    print("="*60)
    print()

    # 4. 对比页面跳转方式
    print("对比: 测试create_order()页面跳转方式...")
    out_trade_no2 = f"TEST_SUBMIT_{int(__import__('time').time())}"

    result2 = zpay.create_order(
        out_trade_no=out_trade_no2,
        name="测试订单-页面跳转方式",
        money=0.1,
        pay_type="wxpay",
        notify_url="https://jindutiao.vercel.app/api/payment-notify",
        return_url="gaiya://test",
        param=json.dumps({"user_id": user_id, "plan_type": "pro_monthly"})
    )

    print()
    print("页面跳转方式返回结果:")
    print(json.dumps(result2, indent=2, ensure_ascii=False))

except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*60)
