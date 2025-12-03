# -*- coding: utf-8 -*-
"""
手动升级用户会员等级(用于支付回调失败时)
"""
import sys
import io

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("="*60)
print("手动升级用户会员等级")
print("="*60)
print()

try:
    from gaiya.core.auth_client import AuthClient
    import os
    from supabase import create_client
    from datetime import datetime, timedelta

    # 1. 获取当前登录用户
    auth = AuthClient()
    user_id = auth.get_user_id()

    if not user_id:
        print("❌ 未登录")
        sys.exit(1)

    print(f"✓ 当前用户: {user_id}")
    print()

    # 2. 连接Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "") or os.getenv("SUPABASE_ANON_KEY", "")

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Supabase凭证未配置")
        print("   请确保设置了 SUPABASE_URL 和 SUPABASE_SERVICE_KEY 环境变量")
        sys.exit(1)

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✓ 已连接Supabase")
    print()

    # 3. 查询当前会员状态
    print("查询当前会员状态...")
    result = supabase.table("users").select("*").eq("id", user_id).execute()

    if not result.data:
        print("❌ 未找到用户记录")
        sys.exit(1)

    user = result.data[0]
    print(f"  当前等级: {user.get('tier', 'free')}")
    print(f"  是否激活: {user.get('is_active', False)}")
    print(f"  到期时间: {user.get('subscription_expires_at', 'N/A')}")
    print()

    # 4. 升级为Pro会员
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

    confirm = input("确认升级? (yes/no) [默认: no]: ").strip().lower()
    if confirm != "yes":
        print("已取消")
        sys.exit(0)

    # 5. 更新数据库
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

except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*60)
