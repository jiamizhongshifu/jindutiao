# -*- coding: utf-8 -*-
"""
调试支付宝支付崩溃问题
"""
import sys
import traceback

try:
    # 模拟membership_ui中的支付流程
    sys.path.insert(0, '.')
    from gaiya.core.auth_client import AuthClient

    auth = AuthClient()
    user_id = auth.get_user_id()
    token = auth.access_token

    print(f"User ID: {user_id}")
    print(f"Token: {token[:20] if token else None}...")

    # 模拟创建订单
    print("\n测试创建订单...")
    result = auth.create_payment_order(
        user_id=user_id,
        plan_type="pro_monthly",
        pay_type="alipay"
    )

    print(f"Result: {result}")

    if result.get("success"):
        out_trade_no = result.get("out_trade_no")
        print(f"\n订单号: {out_trade_no}")

        # 模拟查询订单
        print("\n测试查询订单...")
        query_result = auth.query_payment_order(out_trade_no)
        print(f"Query result: {query_result}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    traceback.print_exc()
