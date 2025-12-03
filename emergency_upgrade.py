# -*- coding: utf-8 -*-
"""
紧急升级脚本 - 直接通过HTTP API升级会员
适用于支付成功但回调未触发的情况
"""
import sys
import io
import requests
import json
from datetime import datetime, timedelta

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("="*60)
print("紧急会员升级脚本")
print("="*60)
print()

try:
    from gaiya.core.auth_client import AuthClient
    import os

    # 1. 获取当前用户
    auth = AuthClient()
    user_id = auth.get_user_id()

    if not user_id:
        print("❌ 未登录")
        sys.exit(1)

    print(f"✓ 用户ID: {user_id}")
    print()

    # 2. 准备升级数据
    plan_type = "pro_yearly"  # 年度会员

    # 计算到期时间
    expires_at = (datetime.now() + timedelta(days=365)).isoformat()

    print(f"准备升级为: Pro年度会员")
    print(f"到期时间: {expires_at}")
    print()

    # 3. 使用Supabase REST API直接更新
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "") or os.getenv("SUPABASE_ANON_KEY", "")

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ 缺少Supabase环境变量")
        print()
        print("请设置:")
        print("  export SUPABASE_URL='https://your-project.supabase.co'")
        print("  export SUPABASE_SERVICE_KEY='your-service-key'")
        sys.exit(1)

    # 4. 更新用户表
    api_url = f"{SUPABASE_URL}/rest/v1/users"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    update_data = {
        "tier": "pro",
        "is_active": True,
        "subscription_expires_at": expires_at,
        "updated_at": datetime.now().isoformat()
    }

    print("正在更新数据库...")
    response = requests.patch(
        f"{api_url}?id=eq.{user_id}",
        headers=headers,
        json=update_data,
        timeout=10
    )

    print(f"响应状态: {response.status_code}")
    print()

    if response.status_code == 200:
        result = response.json()
        if result:
            print("✅ 升级成功!")
            print(f"\n新的会员状态:")
            print(f"  等级: {result[0].get('tier')}")
            print(f"  是否激活: {result[0].get('is_active')}")
            print(f"  到期时间: {result[0].get('subscription_expires_at')}")
            print()
            print("📝 请在应用中:")
            print("  1. 点击 '🔄 刷新' 按钮")
            print("  2. 查看会员状态是否已更新为PRO")
        else:
            print("❌ 更新失败: 未返回数据")
            print(f"响应: {response.text}")
    else:
        print(f"❌ 更新失败: HTTP {response.status_code}")
        print(f"响应: {response.text}")

except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*60)
