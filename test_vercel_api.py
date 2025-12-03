# -*- coding: utf-8 -*-
"""
测试Vercel线上API的Z-Pay配置
通过调用线上API来测试环境变量是否正确
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
print("测试Vercel线上Z-Pay配置")
print("="*60)
print()

try:
    from gaiya.core.auth_client import AuthClient

    # 1. 获取用户信息
    auth = AuthClient()
    user_id = auth.get_user_id()
    token = auth.access_token

    if not user_id or not token:
        print("❌ 未登录,无法测试")
        sys.exit(1)

    print(f"✓ 用户ID: {user_id}")
    print()

    # 2. 测试创建订单 (会使用Vercel环境变量中的Z-Pay凭证)
    print("测试创建订单...")
    print("(此测试会调用Vercel API,使用Vercel环境变量中的凭证)")
    print()

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

    print(f"响应状态码: {response.status_code}")
    print()

    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print("✅ 订单创建成功!")
            print()
            print(f"  订单号: {result.get('out_trade_no')}")
            print(f"  订单金额: ¥{result.get('amount')}")
            print(f"  支付链接: {result.get('payment_url', '')[:60]}...")
            print()
            print("✓ Vercel环境变量中的Z-Pay凭证配置正确!")
            print()
            print("接下来:")
            print("  1. 打开支付链接完成支付")
            print("  2. 立即查看Vercel日志: https://vercel.com/jindutiao → Functions → Logs")
            print("  3. 查找 [PAYMENT-NOTIFY] 日志")
            print("  4. 如果看到回调日志,说明回调成功!")
        else:
            error = result.get("error", "Unknown error")
            print(f"❌ 订单创建失败: {error}")
            print()

            # 分析错误类型
            if "pid不存在" in error or "key错误" in error:
                print("问题原因: Vercel环境变量中的Z-Pay凭证配置错误")
                print()
                print("解决方法:")
                print("  1. 访问: https://vercel.com/jindutiao")
                print("  2. Settings → Environment Variables")
                print("  3. 检查 ZPAY_PID 和 ZPAY_PKEY 的值")
                print("  4. 确认不是占位符 'your_merchant_id_here'")
                print("  5. 使用从 https://z-pay.cn/ 获取的真实凭证")
                print("  6. 保存后重新部署")
            else:
                print(f"其他错误: {error}")
    else:
        print(f"❌ HTTP错误: {response.status_code}")
        print(f"   响应: {response.text[:200]}")

except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*60)
