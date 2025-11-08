"""
Simple quota test

Required environment variables:
- SUPABASE_URL
- SUPABASE_ANON_KEY
"""
import os
import sys

# Check required environment variables
if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_ANON_KEY"):
    print("ERROR: Missing required environment variables")
    print("Please set SUPABASE_URL and SUPABASE_ANON_KEY")
    sys.exit(1)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))
from quota_manager import QuotaManager

def test():
    qm = QuotaManager()
    user_id = "user_demo"

    print("\n=== Test 1: Get initial quota ===")
    quota = qm.get_quota_status(user_id, "free")
    print(f"Initial quota: {quota}")
    initial = quota['remaining']['daily_plan']
    print(f"Daily plan remaining: {initial}")

    print("\n=== Test 2: Use 1 quota ===")
    result = qm.use_quota(user_id, 'daily_plan', 1)
    print(f"Use result: {result}")

    if result.get('success'):
        print(f"SUCCESS! Used: {result['used']}, Remaining: {result['remaining']}")
    else:
        print(f"FAILED: {result.get('error')}")
        return

    print("\n=== Test 3: Verify quota was deducted ===")
    quota_after = qm.get_quota_status(user_id, "free")
    final = quota_after['remaining']['daily_plan']
    print(f"After use: {final}")

    if final == initial - 1:
        print(f"VERIFIED! Quota decreased from {initial} to {final}")
    else:
        print(f"ERROR! Expected {initial - 1}, got {final}")

    print("\n=== Test Complete ===\n")

if __name__ == "__main__":
    test()
