"""
测试 Vercel API 是否已部署最新修复
"""
import requests
import json

def test_vercel_query():
    """测试 Vercel payment-query API"""

    # 使用已支付的订单号
    order_no = "GAIYA17649287338764cc530"

    url = f"https://jindutiao.vercel.app/api/payment-query?out_trade_no={order_no}"

    print("=" * 60)
    print("测试 Vercel API 部署状态")
    print("=" * 60)
    print(f"\n订单号: {order_no}")
    print(f"API URL: {url}\n")

    try:
        response = requests.get(url, timeout=10)

        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")

        if response.status_code == 200:
            data = response.json()

            if data.get("success"):
                order = data.get("order", {})
                status = order.get("status")

                print("=" * 60)
                if status == "paid":
                    print("[成功] Vercel API 已部署最新修复!")
                    print(f"  - 订单状态: {status}")
                    print(f"  - 支付金额: {order.get('money')}")
                    print(f"  - 附加参数: {order.get('param')}")
                    print("\n✓ 修复已生效，客户端应该可以识别支付成功")
                elif status == "unpaid":
                    print("[警告] API 返回未支付")
                    print("  可能原因:")
                    print("  1. 订单尚未支付")
                    print("  2. Vercel 缓存延迟")
                else:
                    print(f"[异常] 未知状态: {status}")
            else:
                print("[失败] API 返回失败")
                print(f"  错误信息: {data.get('error')}")
                print("\n可能原因: Vercel 还未部署最新代码")
        else:
            print(f"[失败] HTTP 错误: {response.status_code}")

    except Exception as e:
        print(f"[错误] 请求失败: {e}")

if __name__ == "__main__":
    test_vercel_query()
