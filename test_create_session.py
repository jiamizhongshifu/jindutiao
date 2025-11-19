#!/usr/bin/env python3
"""
测试Stripe创建Checkout Session API
"""
import requests
import json

# API端点
API_URL = "https://jindutiao.vercel.app/api/stripe-create-checkout"

# 测试数据
test_data = {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_email": "test@example.com",
    "plan_type": "lifetime"  # 或 "pro_monthly", "pro_yearly"
}

print("=" * 60)
print("Testing Stripe Checkout Session Creation")
print("=" * 60)
print(f"\nAPI Endpoint: {API_URL}")
print(f"Request Data: {json.dumps(test_data, indent=2)}")
print("\n" + "=" * 60)

try:
    # 发送POST请求
    response = requests.post(
        API_URL,
        json=test_data,
        headers={
            "Content-Type": "application/json"
        },
        timeout=30
    )

    print(f"\n[OK] HTTP Status Code: {response.status_code}")
    print(f"Response Headers:")
    for key, value in response.headers.items():
        if key.lower() in ['content-type', 'x-ratelimit-limit', 'x-ratelimit-remaining', 'access-control-allow-origin']:
            print(f"  {key}: {value}")

    print(f"\nResponse Body:")
    response_data = response.json()
    print(json.dumps(response_data, indent=2))

    # 如果成功，打印Checkout URL
    if response_data.get("success"):
        print("\n" + "=" * 60)
        print("[SUCCESS] Session Created Successfully!")
        print("=" * 60)
        print(f"\nCheckout URL:")
        print(f"   {response_data['checkout_url']}")
        print(f"\nSession ID: {response_data['session_id']}")

        if 'plan_name' in response_data:
            print(f"Plan: {response_data['plan_name']}")
            print(f"Amount: ${response_data['amount']} {response_data['currency']}")

        print("\n[TIP] Copy the Checkout URL above and open it in your browser to test payment")

        # 提供测试卡号信息
        print("\n" + "=" * 60)
        print("Stripe Test Card Numbers")
        print("=" * 60)
        print("  Card Number: 4242 4242 4242 4242")
        print("  Expiry Date: Any future date (e.g., 12/34)")
        print("  CVC: Any 3 digits (e.g., 123)")
        print("  ZIP: Any 5 digits (e.g., 12345)")

    else:
        print("\n" + "=" * 60)
        print("[ERROR] Session Creation Failed!")
        print("=" * 60)
        print(f"\nError Message: {response_data.get('error', 'Unknown error')}")
        if 'error_code' in response_data:
            print(f"Error Code: {response_data['error_code']}")

except requests.exceptions.Timeout:
    print("\n[ERROR] Request timeout (30 seconds)")
except requests.exceptions.ConnectionError:
    print("\n[ERROR] Connection failed, please check network or API address")
except json.JSONDecodeError:
    print(f"\n[ERROR] Response is not valid JSON:")
    print(response.text)
except Exception as e:
    print(f"\n[ERROR] Exception occurred: {e}")

print("\n" + "=" * 60)
