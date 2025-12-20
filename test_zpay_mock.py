"""
Zpay Mock 支付测试脚本
用于快速测试订阅升级逻辑，无需真实支付

使用前提:
1. 启动本地Vercel服务: vercel dev
2. 确保环境变量设置: ENVIRONMENT=development
3. 确保Supabase配置正确

用法:
    python test_zpay_mock.py                           # 默认测试Pro月度订阅
    python test_zpay_mock.py --plan pro_yearly        # 测试Pro年度订阅
    python test_zpay_mock.py --plan lifetime          # 测试终身会员
    python test_zpay_mock.py --scenario failed        # 测试支付失败场景
    python test_zpay_mock.py --user YOUR_USER_ID      # 指定用户ID
"""
import requests
import json
import argparse
import sys
from typing import Dict, Any


# 默认配置
DEFAULT_CONFIG = {
    "api_url": "http://localhost:3000/api/test-zpay-mock-callback",
    "user_id": "df15202c-2ff0-4b12-9fc0-a1029d6000a7",  # 默认测试用户
    "plan_type": "pro_monthly",
    "scenario": "success"
}


def test_mock_payment(
    api_url: str,
    user_id: str,
    plan_type: str,
    scenario: str = "success"
) -> Dict[str, Any]:
    """
    发送Mock支付回调请求

    Args:
        api_url: Mock回调API地址
        user_id: 用户ID
        plan_type: 订阅类型 (pro_monthly/pro_yearly/lifetime)
        scenario: 测试场景 (success/failed)

    Returns:
        API响应数据
    """
    print("=" * 60)
    print("Zpay Mock Payment Test")
    print("=" * 60)

    # 构造请求参数
    payload = {
        "user_id": user_id,
        "plan_type": plan_type,
        "scenario": scenario
    }

    print(f"Sending request to: {api_url}")
    print(f"Request params:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print()

    try:
        # 发送POST请求
        response = requests.post(
            api_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        print(f"Response status: {response.status_code}")
        print()

        # 解析响应
        if response.status_code == 200:
            result = response.json()
            print("[OK] Mock payment callback succeeded!")
            print()
            print("Response data:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print()

            # 提取关键信息
            if result.get("status") == "success":
                print("=" * 60)
                print("Subscription Creation Success!")
                print("=" * 60)

                # 新格式：subscription_result包含success和subscription对象
                sub_result = result.get("subscription_result", {})
                subscription = sub_result.get("subscription", {})

                print(f"User ID: {subscription.get('user_id', 'N/A')}")
                print(f"Plan Type: {subscription.get('plan_type', 'N/A')}")
                print(f"Status: {subscription.get('status', 'N/A')}")
                print(f"Payment Provider: {subscription.get('payment_provider', 'N/A')}")
                print(f"Payment ID: {subscription.get('payment_id', 'N/A')}")
                print(f"Price: {subscription.get('currency', 'CNY')} {subscription.get('price', 'N/A')}")

                if subscription.get('expires_at'):
                    print(f"Expires at: {subscription['expires_at']}")
                else:
                    print("Expires at: Lifetime (no expiration)")

                print()
                print("[PASS] Test passed! Verify member status in GaiYa client.")

            elif result.get("status") == "failed":
                print("=" * 60)
                print("[WARN] Mock payment failure scenario")
                print("=" * 60)
                print("This is expected failure test for error handling validation.")

            return result

        elif response.status_code == 403:
            print("[ERROR] Mock callback endpoint not available in production")
            print("[TIP] Make sure ENVIRONMENT=development")
            return {"error": "Forbidden"}

        else:
            print(f"[ERROR] Request failed: HTTP {response.status_code}")
            print("Response content:")
            print(response.text)
            return {"error": response.text}

    except requests.exceptions.ConnectionError:
        print("[ERROR] Connection failed: Cannot connect to local server")
        print()
        print("[TIP] Start local server first:")
        print("   python local_test_server.py")
        print()
        print("   Then visit: http://localhost:3000")
        return {"error": "Connection failed"}

    except Exception as e:
        print(f"[ERROR] Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


def main():
    """主函数 - 处理命令行参数"""
    parser = argparse.ArgumentParser(
        description="测试Zpay Mock支付回调",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python test_zpay_mock.py
  python test_zpay_mock.py --plan pro_yearly
  python test_zpay_mock.py --plan lifetime
  python test_zpay_mock.py --scenario failed
  python test_zpay_mock.py --user YOUR_USER_ID --plan pro_monthly

支持的订阅类型:
  pro_monthly    Pro月度会员 (29元/月)
  pro_yearly     Pro年度会员 (199元/年)
  lifetime       终身会员 (1200元，买断)

测试场景:
  success        支付成功 (默认)
  failed         支付失败
        """
    )

    parser.add_argument(
        "--api-url",
        default=DEFAULT_CONFIG["api_url"],
        help="Mock回调API地址 (默认: %(default)s)"
    )

    parser.add_argument(
        "--user",
        "--user-id",
        dest="user_id",
        default=DEFAULT_CONFIG["user_id"],
        help="用户ID (默认: %(default)s)"
    )

    parser.add_argument(
        "--plan",
        "--plan-type",
        dest="plan_type",
        choices=["pro_monthly", "pro_yearly", "lifetime"],
        default=DEFAULT_CONFIG["plan_type"],
        help="订阅类型 (默认: %(default)s)"
    )

    parser.add_argument(
        "--scenario",
        choices=["success", "failed"],
        default=DEFAULT_CONFIG["scenario"],
        help="测试场景 (默认: %(default)s)"
    )

    args = parser.parse_args()

    # 执行测试
    result = test_mock_payment(
        api_url=args.api_url,
        user_id=args.user_id,
        plan_type=args.plan_type,
        scenario=args.scenario
    )

    # 根据结果返回退出码
    if result.get("status") == "success":
        sys.exit(0)  # 成功
    else:
        sys.exit(1)  # 失败


if __name__ == "__main__":
    main()
