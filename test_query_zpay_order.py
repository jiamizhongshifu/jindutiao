# -*- coding: utf-8 -*-
"""
查询Z-Pay订单详情,验证notify_url配置
"""
import sys
import io

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("="*60)
print("查询Z-Pay订单详情")
print("="*60)
print()

# 从命令行获取订单号,如果没有则使用最近的订单
order_id = sys.argv[1] if len(sys.argv) > 1 else "GAIYA1764727660522308748"

try:
    sys.path.insert(0, 'api')
    from zpay_manager import ZPayManager
    import json

    zpay = ZPayManager()

    print(f"查询订单: {order_id}")
    print(f"Z-Pay API: {zpay.api_url}")
    print()

    # 查询订单
    result = zpay.query_order(out_trade_no=order_id)

    print("查询结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print()

    if result.get("success"):
        print("✅ 订单查询成功")
        print()
        print("订单信息:")
        print(f"  商户订单号: {result.get('out_trade_no', 'N/A')}")
        print(f"  Z-Pay订单号: {result.get('trade_no', 'N/A')}")
        print(f"  订单金额: ¥{result.get('money', 'N/A')}")
        print(f"  支付状态: {result.get('status', 'N/A')} (1=已支付, 0=未支付)")
        print(f"  支付方式: {result.get('type', 'N/A')}")
        print(f"  商品名称: {result.get('name', 'N/A')}")
        print(f"  创建时间: {result.get('addtime', 'N/A')}")
        print(f"  完成时间: {result.get('endtime', 'N/A')}")
        print(f"  业务参数: {result.get('param', 'N/A')}")
        print()

        # 检查支付状态
        status = result.get('status', 0)
        if status == 1:
            print("✅ 订单已支付!")
            print()
            print("⚠️ 但是会员状态未更新,说明回调未触发。")
            print()
            print("可能原因:")
            print("  1. Z-Pay商户后台未配置全局异步通知地址")
            print("  2. Z-Pay回调被防火墙拦截")
            print("  3. 商户账户处于测试模式")
            print()
            print("建议:")
            print("  1. 登录Z-Pay商户后台检查'异步通知地址'配置")
            print("  2. 设置为: https://jindutiao.vercel.app/api/payment-notify")
            print("  3. 或使用 manual_upgrade.py 手动升级账户")
        else:
            print("⚠️ 订单未支付")
    else:
        print(f"❌ 查询失败: {result.get('error', 'Unknown error')}")
        print()
        print("可能原因:")
        print("  1. 订单号不存在")
        print("  2. Z-Pay API密钥配置错误")
        print("  3. 网络连接问题")

except Exception as e:
    print(f"❌ 查询失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*60)
