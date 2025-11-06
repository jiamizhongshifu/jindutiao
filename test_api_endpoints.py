#!/usr/bin/env python3
"""
测试Vercel部署的API端点
"""
import requests
import json

BASE_URL = "https://jindutiao.vercel.app"

def test_health():
    """测试健康检查"""
    print("\n=== 测试 /api/health ===")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_signin():
    """测试登录"""
    print("\n=== 测试 /api/auth-signin ===")
    try:
        data = {
            "email": "test@example.com",
            "password": "test123456"
        }
        response = requests.post(
            f"{BASE_URL}/api/auth-signin",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code in [200, 401]  # 401也算正常（用户不存在）
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_signup():
    """测试注册"""
    print("\n=== 测试 /api/auth-signup ===")
    try:
        data = {
            "email": f"test_{__import__('time').time()}@example.com",  # 使用时间戳避免重复
            "password": "test123456",
            "username": "testuser"
        }
        response = requests.post(
            f"{BASE_URL}/api/auth-signup",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_subscription_status():
    """测试订阅状态"""
    print("\n=== 测试 /api/subscription-status ===")
    try:
        response = requests.get(
            f"{BASE_URL}/api/subscription-status?user_id=test_user",
            timeout=10
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_styles_list():
    """测试样式列表"""
    print("\n=== 测试 /api/styles-list ===")
    try:
        response = requests.get(
            f"{BASE_URL}/api/styles-list?user_id=test_user&user_tier=free",
            timeout=10
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("开始测试API端点")
    print("=" * 60)

    results = {}
    results['health'] = test_health()
    results['signin'] = test_signin()
    results['signup'] = test_signup()
    results['subscription'] = test_subscription_status()
    results['styles'] = test_styles_list()

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    for name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{name:20s}: {status}")

    total = len(results)
    passed = sum(results.values())
    print(f"\n总计: {passed}/{total} 通过")
