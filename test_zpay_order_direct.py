# -*- coding: utf-8 -*-
"""
直接调用Z-Pay API查询订单状态
"""
import os
import requests
import json
import sys

# Z-Pay配置
ZPAY_PID = os.getenv("ZPAY_PID", "")
ZPAY_PKEY = os.getenv("ZPAY_PKEY", "")
ZPAY_API_URL = "https://zpayz.cn"

# 订单号(从截图URL中提取)
order_id = "GAIYA1764737631885308748"

print("="*60)
print("直接查询Z-Pay订单状态")
print("="*60)
print()

if not ZPAY_PID or not ZPAY_PKEY:
    print("❌ 环境变量未配置:")
    print(f"   ZPAY_PID: {'✓' if ZPAY_PID else '✗'}")
    print(f"   ZPAY_PKEY: {'✓' if ZPAY_PKEY else '✗'}")
    sys.exit(1)

print(f"PID: {ZPAY_PID}")
print(f"订单号: {order_id}")
print()

try:
    # 构建查询请求
    params = {
        "act": "order",
        "pid": ZPAY_PID,
        "key": ZPAY_PKEY,
        "out_trade_no": order_id
    }

    print(f"请求URL: {ZPAY_API_URL}/api.php")
    print(f"请求参数: {params}")
    print()

    response = requests.get(
        f"{ZPAY_API_URL}/api.php",
        params=params,
        timeout=15
    )

    print(f"响应状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    print()
    print("响应内容:")
    print(response.text)
    print()

    # 尝试解析JSON
    try:
        result = response.json()
        print("解析后的JSON:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print()

        if result.get("code") == 1:
            print("✅ 订单查询成功!")
            print()
            print(f"  订单号: {result.get('out_trade_no')}")
            print(f"  支付状态: {result.get('status')} (1=已支付, 0=未支付)")
            print(f"  金额: ¥{result.get('money')}")
            print(f"  商品名称: {result.get('name')}")
            print(f"  param参数: {result.get('param')}")
        else:
            print(f"❌ 查询失败: {result.get('msg')}")

    except json.JSONDecodeError as e:
        print(f"❌ JSON解析失败: {e}")
        print(f"   这就是Vercel日志中看到的 'Expecting delimiter' 错误的原因")

except Exception as e:
    print(f"❌ 请求失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*60)
