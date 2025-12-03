# -*- coding: utf-8 -*-
"""
通过API手动升级用户会员等级
"""
import sys
import io

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("="*60)
print("通过API手动升级用户会员等级")
print("="*60)
print()

try:
    from gaiya.core.auth_client import AuthClient
    import requests
    import json

    # 1. 获取当前登录用户
    auth = AuthClient()
    user_id = auth.get_user_id()
    token = auth.access_token

    if not user_id or not token:
        print("❌ 未登录")
        sys.exit(1)

    print(f"✓ 当前用户: {user_id}")
    print()

    # 2. 查询当前状态
    print("查询当前会员状态...")
    api_url = "https://jindutiao.vercel.app/api/subscription-status"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {"user_id": user_id}

    response = requests.post(api_url, headers=headers, json=data, timeout=10)
    if response.status_code == 200:
        result = response.json()
        print(f"  当前等级: {result.get('user_tier', 'unknown')}")
        print(f"  是否激活: {result.get('is_active', False)}")
    print()

    # 3. 显示说明
    print("⚠️ 注意:")
    print("  由于支付回调可能延迟,我们可以通过以下方式手动触发升级:")
    print()
    print("方案1: 等待Z-Pay回调自动到达 (可能需要1-5分钟)")
    print("方案2: 联系管理员在Supabase后台手动更新")
    print("方案3: 重新发起支付(如果金额较小)")
    print()

    # 4. 检查是否有环境变量可以直接升级
    import os
    service_key = os.getenv("SUPABASE_SERVICE_KEY")

    if service_key:
        print("✓ 检测到SUPABASE_SERVICE_KEY环境变量")
        print()
        confirm = input("是否使用Service Key直接升级? (yes/no) [默认: no]: ").strip().lower()

        if confirm == "yes":
            from supabase import create_client
            from datetime import datetime, timedelta

            supabase_url = os.getenv("SUPABASE_URL", "")
            supabase = create_client(supabase_url, service_key)

            plan_type = input("请选择升级套餐 (pro_monthly/pro_yearly/lifetime) [默认: pro_monthly]: ").strip() or "pro_monthly"

            # 计算到期时间
            if plan_type == "pro_monthly":
                expires_at = (datetime.now() + timedelta(days=30)).isoformat()
                tier = "pro"
            elif plan_type == "pro_yearly":
                expires_at = (datetime.now() + timedelta(days=365)).isoformat()
                tier = "pro"
            elif plan_type == "lifetime":
                expires_at = None
                tier = "lifetime"
            else:
                print(f"❌ 无效的套餐类型: {plan_type}")
                sys.exit(1)

            print(f"\n准备升级:")
            print(f"  套餐: {plan_type}")
            print(f"  等级: {tier}")
            print(f"  到期: {expires_at or '永久'}")
            print()

            confirm2 = input("最后确认升级? (yes/no) [默认: no]: ").strip().lower()
            if confirm2 != "yes":
                print("已取消")
                sys.exit(0)

            print("\n正在更新...")
            update_data = {
                "tier": tier,
                "is_active": True,
                "subscription_expires_at": expires_at,
                "updated_at": datetime.now().isoformat()
            }

            result = supabase.table("users").update(update_data).eq("id", user_id).execute()

            if result.data:
                print("✅ 升级成功!")
                print(f"\n新的会员状态:")
                updated_user = result.data[0]
                print(f"  等级: {updated_user.get('tier')}")
                print(f"  是否激活: {updated_user.get('is_active')}")
                print(f"  到期时间: {updated_user.get('subscription_expires_at', 'N/A')}")
                print()
                print("请在应用中点击 '🔄 刷新' 按钮更新状态")
            else:
                print("❌ 升级失败")
    else:
        print("❌ 未检测到SUPABASE_SERVICE_KEY环境变量")
        print()
        print("建议:")
        print("  1. 等待1-5分钟让Z-Pay回调自动到达")
        print("  2. 在应用中点击 '🔄 刷新' 按钮检查状态")
        print("  3. 如果仍未更新,联系管理员")

except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*60)
