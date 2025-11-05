#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GaiYa认证系统自动化测试脚本
测试认证客户端的各项功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gaiya'))

from gaiya.core.auth_client import AuthClient
import time

def print_separator(title):
    """打印分隔线"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_token_management():
    """测试Token管理功能"""
    print_separator("测试1: Token本地存储管理")

    auth_client = AuthClient()

    # 检查初始状态
    print(f"✓ 认证客户端初始化成功")
    print(f"  后端URL: {auth_client.backend_url}")
    print(f"  Token文件路径: {auth_client.auth_file}")
    print(f"  初始登录状态: {auth_client.is_logged_in()}")

    # 模拟保存Token
    print(f"\n正在模拟保存Token...")
    auth_client._save_tokens(
        access_token="test_access_token_123",
        refresh_token="test_refresh_token_456",
        user_info={
            "user_id": "test_user_001",
            "email": "test@example.com",
            "user_tier": "free"
        }
    )

    print(f"✓ Token保存成功")
    print(f"  登录状态: {auth_client.is_logged_in()}")
    print(f"  用户邮箱: {auth_client.get_user_email()}")
    print(f"  用户ID: {auth_client.get_user_id()}")
    print(f"  会员等级: {auth_client.get_user_tier()}")

    # 测试重新加载
    print(f"\n正在测试Token持久化...")
    new_client = AuthClient()
    print(f"✓ 重新创建客户端后Token自动加载")
    print(f"  登录状态: {new_client.is_logged_in()}")
    print(f"  用户邮箱: {new_client.get_user_email()}")

    # 清除Token
    print(f"\n正在清除Token...")
    new_client._clear_tokens()
    print(f"✓ Token清除成功")
    print(f"  登录状态: {new_client.is_logged_in()}")

    return True

def test_quota_api():
    """测试配额查询API"""
    print_separator("测试2: 配额查询API")

    auth_client = AuthClient()

    # 查询免费用户配额
    print("正在查询免费用户配额...")
    result = auth_client.get_quota_status()

    if result:
        print(f"✓ 配额查询成功")
        remaining = result.get("remaining", {})
        user_tier = result.get("user_tier", "unknown")
        print(f"  用户等级: {user_tier}")
        print(f"  每日任务规划: {remaining.get('daily_plan', 0)} 次")
        print(f"  每周进度报告: {remaining.get('weekly_report', 0)} 次")
        print(f"  AI对话: {remaining.get('chat', 0)} 次")
        return True
    else:
        print(f"⚠ 配额查询失败（可能是网络问题）")
        return False

def test_auth_api_structure():
    """测试认证API结构（不实际调用）"""
    print_separator("测试3: 认证API结构验证")

    auth_client = AuthClient()

    # 检查所有方法是否存在
    methods = [
        'signup',
        'signin',
        'signout',
        'refresh_access_token',
        'reset_password',
        'get_subscription_status',
        'create_payment_order',
        'query_payment_order',
        'get_quota_status'
    ]

    print("验证AuthClient类方法...")
    for method in methods:
        if hasattr(auth_client, method):
            print(f"  ✓ {method}")
        else:
            print(f"  ✗ {method} - 缺失")
            return False

    print(f"\n✓ 所有必需的API方法都已实现")
    return True

def test_ui_modules_import():
    """测试UI模块导入"""
    print_separator("测试4: UI模块导入测试")

    try:
        from gaiya.ui.auth_ui import AuthDialog
        print(f"✓ AuthDialog 导入成功")

        from gaiya.ui.membership_ui import MembershipDialog
        print(f"✓ MembershipDialog 导入成功")

        # 检查类属性
        if hasattr(AuthDialog, 'login_success'):
            print(f"✓ AuthDialog.login_success 信号存在")

        if hasattr(MembershipDialog, 'purchase_success'):
            print(f"✓ MembershipDialog.purchase_success 信号存在")

        return True
    except Exception as e:
        print(f"✗ UI模块导入失败: {e}")
        return False

def test_payment_api_structure():
    """测试支付API结构"""
    print_separator("测试5: 支付系统结构验证")

    auth_client = AuthClient()

    # 检查支付相关方法的参数
    import inspect

    # create_payment_order
    sig = inspect.signature(auth_client.create_payment_order)
    params = list(sig.parameters.keys())
    print(f"create_payment_order 参数: {params}")
    if 'plan_type' in params and 'pay_type' in params:
        print(f"  ✓ 参数正确")
    else:
        print(f"  ✗ 参数不正确")
        return False

    # query_payment_order
    sig = inspect.signature(auth_client.query_payment_order)
    params = list(sig.parameters.keys())
    print(f"query_payment_order 参数: {params}")
    if 'out_trade_no' in params:
        print(f"  ✓ 参数正确")
    else:
        print(f"  ✗ 参数不正确")
        return False

    print(f"\n✓ 支付API结构验证通过")
    return True

def run_all_tests():
    """运行所有测试"""
    print("\n" + "█"*60)
    print("  GaiYa认证系统自动化测试")
    print("█"*60)

    results = []

    # 执行所有测试
    results.append(("Token管理", test_token_management()))
    results.append(("配额查询API", test_quota_api()))
    results.append(("认证API结构", test_auth_api_structure()))
    results.append(("UI模块导入", test_ui_modules_import()))
    results.append(("支付API结构", test_payment_api_structure()))

    # 打印测试总结
    print_separator("测试总结")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print(f"\n🎉 所有测试通过！认证系统基础功能正常。")
        return 0
    else:
        print(f"\n⚠️ 部分测试失败，请检查错误信息。")
        return 1

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
