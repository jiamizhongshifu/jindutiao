# -*- coding: utf-8 -*-
"""测试版本API确认Vercel部署状态"""
import requests

url = "https://api.gaiyatime.com/api/test-version"
print(f"测试版本API: {url}")
print()

try:
    response = requests.get(url, timeout=10)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")
except Exception as e:
    print(f"错误: {e}")
