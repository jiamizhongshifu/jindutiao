# -*- coding: utf-8 -*-
"""
详细测试手动升级API,查看完整错误信息
"""
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from gaiya.core.auth_client import AuthClient
import requests
import json

auth = AuthClient()
user_id = auth.get_user_id()
token = auth.access_token

print(f"用户ID: {user_id}")
print(f"Token: {token[:30]}...")
print()

# 测试API
url = f"{auth.backend_url}/api/payment-manual-upgrade"
print(f"API URL: {url}")
print()

data = {
    "out_trade_no": "TEST_ORDER_123",
    "user_id": user_id,
    "plan_type": "pro_monthly"
}

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print("发送请求...")
print(f"数据: {json.dumps(data, indent=2)}")
print()

try:
    response = requests.post(url, headers=headers, json=data, timeout=15)
    print(f"状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    print()
    print(f"响应内容:")
    print(response.text)
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
