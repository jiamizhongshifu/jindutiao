# -*- coding: utf-8 -*-
"""
完整支付流程测试脚本
测试三种套餐的完整流程
"""
import requests
import json
import sys
import time

# 配置
API_BASE = "https://api.gaiyatime.com"
TEST_USER_ID = "577fba91-90cc-4a79-be47-fa32cd66a14c"  # 从日志获取

def test_subscription_status():
    """测试订阅状态查询"""
    print("\n=== 测试订阅状态查询 ===")
    url = f"{API_BASE}/api/subscription-status"
    params = {"user_id": TEST_USER_ID}

    response = requests.get(url, params=params, timeout=10)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    return response.json()

def test_manual_upgrade(plan_type, plan_name):
    """测试手动升级API"""
    print(f"\n=== 测试手动升级: {plan_name} ===")

    # 需要真实的Bearer token (从本地keyring获取)
    print("⚠️  此测试需要真实的Authorization token")
    print(f"套餐类型: {plan_type}")
    print(f"预期结果: user_tier = {'lifetime' if plan_type == 'team_partner' else 'pro'}")

    return {
        "plan_type": plan_type,
        "plan_name": plan_name,
        "needs_manual_test": True
    }

if __name__ == "__main__":
    print("=" * 60)
    print("GaiYa 支付流程完整测试")
    print("=" * 60)

    # 1. 查询当前状态
    current_status = test_subscription_status()
    current_tier = current_status.get("user_tier", "unknown")
    print(f"\n当前会员等级: {current_tier}")

    # 2. 测试计划
    test_plans = [
        ("pro_monthly", "Pro月度订阅"),
        ("pro_yearly", "Pro年度订阅"),
        ("team_partner", "会员合伙人(终身)")
    ]

    print("\n" + "=" * 60)
    print("测试套餐列表:")
    for i, (plan_type, plan_name) in enumerate(test_plans, 1):
        print(f"{i}. {plan_name} (plan_type={plan_type})")

    print("\n" + "=" * 60)
    print("📝 手动测试步骤:")
    print("1. 在应用中选择套餐并生成二维码")
    print("2. 扫码支付0.1元")
    print("3. 点击'已完成支付'按钮")
    print("4. 查看是否自动刷新为对应会员等级")
    print("5. 重启应用验证会员状态持久化")

    print("\n预期结果:")
    print("- pro_monthly → user_tier: pro")
    print("- pro_yearly → user_tier: pro")
    print("- team_partner → user_tier: lifetime")
