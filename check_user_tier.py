"""
检查用户会员等级脚本
用于验证users表的user_tier字段是否正确更新
"""
from api.supabase_client import get_supabase_client
from dotenv import load_dotenv
from pathlib import Path
import json

# 加载环境变量
load_dotenv(Path(__file__).parent / '.env')

def check_user_tier(user_id: str):
    """查询用户的会员等级和配额信息"""
    supabase = get_supabase_client()

    print("=" * 60)
    print("User Tier Check")
    print("=" * 60)
    print(f"User ID: {user_id}")
    print()

    # 1. 查询users表
    print("1. Checking users table...")
    user_response = supabase.table("users").select("*").eq("id", user_id).execute()

    if user_response.data:
        user = user_response.data[0]
        print(f"   Username: {user.get('username', 'N/A')}")
        print(f"   Email: {user.get('email', 'N/A')}")
        print(f"   User Tier: {user.get('user_tier', 'N/A')}")
        print(f"   Created At: {user.get('created_at', 'N/A')}")
    else:
        print("   [ERROR] User not found!")
        return

    print()

    # 2. 查询user_quotas表
    print("2. Checking user_quotas table...")
    quota_response = supabase.table("user_quotas").select("*").eq("user_id", user_id).execute()

    if quota_response.data:
        quota = quota_response.data[0]
        print(f"   User Tier: {quota.get('user_tier', 'N/A')}")
        print(f"   Daily Plan Total: {quota.get('daily_plan_total', 'N/A')}")
        print(f"   Weekly Report Total: {quota.get('weekly_report_total', 'N/A')}")
        print(f"   Chat Total: {quota.get('chat_total', 'N/A')}")
    else:
        print("   [WARN] No quota record found!")

    print()

    # 3. 查询active订阅
    print("3. Checking active subscriptions...")
    sub_response = supabase.table("subscriptions").select("*").eq(
        "user_id", user_id
    ).eq("status", "active").order("created_at", desc=True).execute()

    if sub_response.data:
        print(f"   Found {len(sub_response.data)} active subscription(s):")
        for idx, sub in enumerate(sub_response.data, 1):
            print(f"\n   Subscription #{idx}:")
            print(f"     ID: {sub.get('id')}")
            print(f"     Plan Type: {sub.get('plan_type')}")
            print(f"     Status: {sub.get('status')}")
            print(f"     Started At: {sub.get('started_at')}")
            print(f"     Expires At: {sub.get('expires_at', 'Lifetime')}")
            print(f"     Payment Provider: {sub.get('payment_provider')}")
    else:
        print("   [WARN] No active subscriptions found!")

    print()
    print("=" * 60)

    # 诊断
    print("\nDiagnosis:")
    if user_response.data:
        current_tier = user.get('user_tier', 'free')
        has_active_sub = bool(sub_response.data)

        if has_active_sub and current_tier == 'free':
            print("  [ISSUE] User has active subscription but tier is still 'free'")
            print("  [ACTION] Need to update users.user_tier field")
            return False
        elif has_active_sub and current_tier in ['pro', 'lifetime']:
            print(f"  [OK] User tier ({current_tier}) matches active subscription")
            return True
        elif not has_active_sub and current_tier == 'free':
            print("  [OK] User is free tier with no active subscription")
            return True
        else:
            print(f"  [WARN] Unexpected state: tier={current_tier}, has_sub={has_active_sub}")
            return False

if __name__ == "__main__":
    import sys
    # 支持命令行参数指定user_id
    if len(sys.argv) > 1:
        test_user_id = sys.argv[1]
    else:
        # 默认用户ID (drmrzhong+10)
        test_user_id = "df15202c-2ff0-4b12-9fc0-a1029d6000a7"

    check_user_tier(test_user_id)
