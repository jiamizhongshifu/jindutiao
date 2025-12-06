"""
Z-Pay 订单查询诊断工具
用于诊断支付订单查询失败的问题
"""
import sys
import os

# 添加 api 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

from zpay_manager import ZPayManager
import json

def debug_order_query(out_trade_no: str):
    """
    诊断订单查询问题

    Args:
        out_trade_no: 商户订单号 (例如: GAIYA17649274325984cc530)
    """
    print("=" * 60)
    print("Z-Pay 订单查询诊断工具")
    print("=" * 60)
    print(f"\n[订单] 订单号: {out_trade_no}\n")

    zpay = ZPayManager()

    # 测试1: 使用 mapi.php 查询 (API订单查询接口)
    print("[测试1] 使用 mapi.php 查询订单")
    print("-" * 60)
    result1 = zpay.query_api_order(out_trade_no=out_trade_no)

    if result1.get("success"):
        print("[成功] mapi.php 查询成功!")
        order = result1.get("order", {})
        print(f"  - 订单状态: {order.get('status')}")
        print(f"  - 支付状态: {'已支付' if order.get('status') == 1 else '未支付'}")
        print(f"  - 订单金额: ¥{order.get('money')}")
        print(f"  - 商品名称: {order.get('name')}")
        print(f"  - 附加参数: {order.get('param')}")
        print(f"  - 完整响应: {json.dumps(order, ensure_ascii=False, indent=2)}")
    else:
        print(f"[失败] mapi.php 查询失败: {result1.get('error')}")

    print("\n")

    # 测试2: 使用 api.php 查询 (标准订单查询接口)
    print("[测试2] 使用 api.php 查询订单")
    print("-" * 60)
    result2 = zpay.query_order(out_trade_no=out_trade_no)

    if result2.get("success"):
        print("[成功] api.php 查询成功!")
        order = result2.get("order", {})
        print(f"  - 订单状态: {order.get('status')}")
        print(f"  - 支付状态: {'已支付' if order.get('status') == 1 else '未支付'}")
        print(f"  - 订单金额: ¥{order.get('money')}")
        print(f"  - 商品名称: {order.get('name')}")
        print(f"  - 附加参数: {order.get('param')}")
        print(f"  - 完整响应: {json.dumps(order, ensure_ascii=False, indent=2)}")
    else:
        print(f"[失败] api.php 查询失败: {result2.get('error')}")

    print("\n" + "=" * 60)
    print("诊断结论:")
    print("=" * 60)

    if result1.get("success") or result2.get("success"):
        print("[结论] 至少有一个接口可以查询到订单")
        if result1.get("success"):
            order = result1.get("order", {})
            if order.get("status") == 1 or str(order.get("status")) == "1":
                print("[成功] 订单已支付!")
                print("\n[警告] 但客户端仍显示未支付，可能的原因:")
                print("   1. 客户端轮询间隔太长")
                print("   2. 查询接口响应格式与预期不符")
                print("   3. param 参数解析失败")
            else:
                print("[警告] 订单存在但未支付")
    else:
        print("[失败] 所有接口都无法查询到订单")
        print("\n可能的原因:")
        print("   1. 订单号错误")
        print("   2. 订单创建失败")
        print("   3. Z-Pay 服务器延迟,订单尚未同步")
        print("   4. Z-Pay 凭证 (PID/PKEY) 配置错误")
        print("\n建议:")
        print("   - 等待 30 秒后重试查询")
        print("   - 检查 Z-Pay 商户后台的订单记录")
        print("   - 确认环境变量 ZPAY_PID 和 ZPAY_PKEY 配置正确")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python debug_zpay_order.py <订单号>")
        print("示例: python debug_zpay_order.py GAIYA17649274325984cc530")
        sys.exit(1)

    order_no = sys.argv[1]
    debug_order_query(order_no)
