# -*- coding: utf-8 -*-
"""
测试Stripe API端点
"""
import requests
import json

# 配置
API_BASE_URL = "https://jindutiao.vercel.app"

# 测试数据
TEST_USER_ID = "550e8400-e29b-41d4-a716-446655440000"  # 示例UUID
TEST_EMAIL = "test@example.com"

def test_create_checkout_session(plan_type="pro_monthly"):
    """测试创建Checkout Session"""
    print('\n' + '='*60)
    print('Testing Stripe Checkout Session Creation')
    print('='*60)

    url = f"{API_BASE_URL}/api/stripe-create-checkout"
    payload = {
        "user_id": TEST_USER_ID,
        "user_email": TEST_EMAIL,
        "plan_type": plan_type
    }

    print('\nRequest:')
    print('  URL:', url)
    print('  Payload:', json.dumps(payload, indent=2))

    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        print('\nResponse:')
        print('  Status Code:', response.status_code)

        if response.status_code == 200:
            data = response.json()
            print('  Response Data:')
            print(json.dumps(data, indent=2))

            if data.get("success"):
                print('\n' + '='*60)
                print('SUCCESS: Checkout Session Created!')
                print('='*60)
                print('\nCheckout URL:')
                print(data.get('checkout_url'))
                print('\nSession Details:')
                print('  - Plan:', data.get('plan_name'))
                print('  - Amount: ${} {}'.format(data.get('amount'), data.get('currency')))
                print('  - Session ID:', data.get('session_id'))
                print('\nNext Steps:')
                print('1. Open the Checkout URL in your browser')
                print('2. Use Stripe test card:')
                print('   Card Number: 4242 4242 4242 4242')
                print('   Expiry: Any future date (e.g., 12/34)')
                print('   CVC: Any 3 digits (e.g., 123)')
                print('   ZIP: Any 5 digits (e.g., 12345)')
                return True
            else:
                print('\nERROR:', data.get('error'))
                return False
        else:
            print('  Error Response:', response.text)
            return False

    except requests.exceptions.Timeout:
        print('\nERROR: Request timeout')
        return False
    except requests.exceptions.ConnectionError as e:
        print('\nERROR: Connection failed')
        print('Details:', str(e))
        return False
    except Exception as e:
        print('\nERROR:', str(e))
        return False

def test_all_plans():
    """测试所有计划类型"""
    plans = [
        ("pro_monthly", "Monthly Plan - $4.99/month"),
        ("pro_yearly", "Yearly Plan - $39.99/year"),
        ("lifetime", "Lifetime Plan - $89.99 one-time")
    ]

    print('\n' + '='*60)
    print('Testing All Plan Types')
    print('='*60)

    results = []
    for plan_type, description in plans:
        print('\n[{}] {}'.format(plan_type, description))
        print('-' * 60)
        result = test_create_checkout_session(plan_type)
        results.append((plan_type, result))
        print('')

    print('\n' + '='*60)
    print('Test Summary')
    print('='*60)
    for plan_type, result in results:
        status = 'PASS' if result else 'FAIL'
        print('[{}] {}'.format(status, plan_type))

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Test specific plan
        plan = sys.argv[1]
        test_create_checkout_session(plan)
    else:
        # Test all plans
        test_all_plans()
