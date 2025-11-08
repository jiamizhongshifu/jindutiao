"""
测试配额系统

使用前请设置环境变量：
export SUPABASE_URL="your_supabase_url"
export SUPABASE_ANON_KEY="your_supabase_anon_key"

或使用 .env 文件（需要先安装 python-dotenv）
"""
import os
import sys

# 检查环境变量是否已设置
if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_ANON_KEY"):
    print("❌ 错误: 请先设置 SUPABASE_URL 和 SUPABASE_ANON_KEY 环境变量")
    print("\n设置方法:")
    print("  export SUPABASE_URL='your_supabase_url'")
    print("  export SUPABASE_ANON_KEY='your_supabase_anon_key'")
    sys.exit(1)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))
from quota_manager import QuotaManager

def test_quota_system():
    """测试配额系统"""
    print("=" * 60)
    print("配额系统测试")
    print("=" * 60)

    qm = QuotaManager()
    user_id = "user_demo"
    user_tier = "free"

    # 测试1：获取初始配额
    print("\n【测试1】获取初始配额")
    quota = qm.get_quota_status(user_id, user_tier)
    print(f"初始配额: {quota}")
    initial_daily_plan = quota['remaining']['daily_plan']
    print(f"✅ daily_plan剩余: {initial_daily_plan} 次")

    # 测试2：使用1次配额
    print("\n【测试2】使用1次daily_plan配额")
    result = qm.use_quota(user_id, 'daily_plan', 1)
    print(f"扣除结果: {result}")

    if result.get('success'):
        print(f"✅ 配额扣除成功!")
        print(f"   已用: {result['used']}")
        print(f"   总数: {result['total']}")
        print(f"   剩余: {result['remaining']}")
    else:
        print(f"❌ 配额扣除失败: {result.get('error')}")
        return

    # 测试3：再次查询配额，验证是否被扣除
    print("\n【测试3】验证配额是否被扣除")
    quota_after = qm.get_quota_status(user_id, user_tier)
    print(f"扣除后配额: {quota_after}")
    final_daily_plan = quota_after['remaining']['daily_plan']
    print(f"剩余: {final_daily_plan} 次")

    if final_daily_plan == initial_daily_plan - 1:
        print(f"✅ 配额扣除验证成功! ({initial_daily_plan} → {final_daily_plan})")
    else:
        print(f"❌ 配额未正确扣除! 期望: {initial_daily_plan - 1}, 实际: {final_daily_plan}")

    # 测试4：尝试超额使用
    print("\n【测试4】测试配额用尽情况")
    # 先用完剩余配额
    for i in range(final_daily_plan):
        print(f"  使用第 {i+1} 次配额...")
        qm.use_quota(user_id, 'daily_plan', 1)

    # 尝试再次使用
    print("  尝试超额使用...")
    result = qm.use_quota(user_id, 'daily_plan', 1)
    if not result.get('success'):
        print(f"✅ 正确阻止了超额使用: {result.get('error')}")
    else:
        print(f"❌ 未能阻止超额使用!")

    # 最终状态
    print("\n【最终状态】")
    final_quota = qm.get_quota_status(user_id, user_tier)
    print(f"最终配额: {final_quota}")

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    test_quota_system()
