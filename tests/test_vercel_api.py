"""
Vercel API端到端测试脚本
测试配额查询、任务生成和配额扣除的完整流程
"""
import requests
import json
import time

BASE_URL = "https://jindutiao.vercel.app"
USER_ID = "user_demo"
USER_TIER = "free"

def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_health():
    """测试健康检查"""
    print_section("1. 健康检查")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=15)
        print(f"✅ 状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False

def get_quota():
    """获取当前配额"""
    print_section("2. 查询当前配额")
    try:
        response = requests.get(
            f"{BASE_URL}/api/quota-status",
            params={"user_id": USER_ID, "user_tier": USER_TIER},
            timeout=20
        )
        print(f"✅ 状态码: {response.status_code}")
        data = response.json()
        print(f"配额信息: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return data['remaining']['daily_plan']
    except Exception as e:
        print(f"❌ 配额查询失败: {e}")
        return None

def generate_tasks():
    """生成任务（会扣除配额）"""
    print_section("3. 生成任务（扣除1次配额）")

    payload = {
        "user_id": USER_ID,
        "user_tier": USER_TIER,
        "time_blocks": [
            {"start": "09:00", "end": "12:00", "type": "work", "description": "工作时间"},
            {"start": "12:00", "end": "13:00", "type": "break", "description": "午休"},
            {"start": "13:00", "end": "18:00", "type": "work", "description": "下午工作"}
        ]
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/plan-tasks",
            json=payload,
            timeout=30  # AI调用可能需要更长时间
        )
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ 任务生成成功！")
                if 'tasks' in data:
                    print(f"生成了 {len(data['tasks'])} 个任务")
                if 'quota_info' in data:
                    print(f"配额信息: {json.dumps(data['quota_info'], indent=2, ensure_ascii=False)}")
                return True
            else:
                print(f"❌ 任务生成失败: {data.get('error')}")
                return False
        elif response.status_code == 429:
            print("⚠️ 配额已用尽（这是预期行为）")
            return False
        else:
            print(f"❌ 请求失败: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 任务生成失败: {e}")
        return False

def main():
    """主测试流程"""
    print("\n" + "🚀 " * 20)
    print("   Vercel API 端到端测试")
    print("🚀 " * 20)

    # 1. 健康检查
    if not test_health():
        print("\n❌ 健康检查失败，终止测试")
        return

    time.sleep(1)

    # 2. 查询初始配额
    initial_quota = get_quota()
    if initial_quota is None:
        print("\n❌ 无法获取配额，终止测试")
        return

    print(f"\n📊 初始配额: {initial_quota} 次")

    if initial_quota <= 0:
        print("\n⚠️ 配额已用完，无法测试任务生成")
        print("💡 提示：等待明天自动重置，或在Supabase中手动重置配额")
        return

    time.sleep(1)

    # 3. 生成任务（扣除配额）
    print(f"\n🎯 准备生成任务（将扣除1次配额）...")
    time.sleep(2)  # 给用户时间看到提示

    if generate_tasks():
        time.sleep(2)

        # 4. 再次查询配额验证扣除
        print_section("4. 验证配额扣除")
        final_quota = get_quota()

        if final_quota is not None:
            expected_quota = initial_quota - 1
            if final_quota == expected_quota:
                print(f"\n🎉 配额扣除验证成功！")
                print(f"   {initial_quota} → {final_quota}")
            else:
                print(f"\n⚠️ 配额数值异常")
                print(f"   期望: {expected_quota}, 实际: {final_quota}")

    print("\n" + "=" * 60)
    print("  测试完成")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
