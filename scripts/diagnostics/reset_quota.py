"""
重置用户配额脚本
用于手动重置测试用户的配额
"""
import os
import sys
from datetime import datetime, timezone, timedelta

# 设置环境变量
os.environ["SUPABASE_URL"] = "https://qpgypaxwjgcirssydgqh.supabase.co"
os.environ["SUPABASE_ANON_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFwZ3lwYXh3amdjaXJzc3lkZ3FoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjIwNzcwNDksImV4cCI6MjA3NzY1MzA0OX0.19xAKHuvJtOl3Jca-O7z3dOhsIyiIfPBo2IJHRvA9U8"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))
from quota_manager import QuotaManager

def reset_user_quota(user_id="user_demo"):
    """重置指定用户的配额"""
    print("\n" + "=" * 60)
    print(f"  重置配额工具 - 用户: {user_id}")
    print("=" * 60)

    qm = QuotaManager()

    if not qm.client:
        print("[ERROR] 无法连接到Supabase")
        return False

    try:
        # 获取当前配额状态
        print("\n[当前配额状态]")
        quota_status = qm.get_quota_status(user_id, "free")
        print(f"  daily_plan 剩余: {quota_status['remaining']['daily_plan']}")
        print(f"  weekly_report 剩余: {quota_status['remaining']['weekly_report']}")
        print(f"  chat 剩余: {quota_status['remaining']['chat']}")

        # 重置配额
        print("\n[正在重置配额...]")
        now = datetime.now(timezone.utc)
        tomorrow = now + timedelta(days=1)
        next_week = now + timedelta(days=7)

        updates = {
            "daily_plan_used": 0,
            "chat_used": 0,
            "theme_recommend_used": 0,
            "theme_generate_used": 0,
            "weekly_report_used": 0,
            "daily_plan_reset_at": tomorrow.isoformat(),
            "chat_reset_at": tomorrow.isoformat(),
            "theme_recommend_reset_at": tomorrow.isoformat(),
            "theme_generate_reset_at": tomorrow.isoformat(),
            "weekly_report_reset_at": next_week.isoformat()
        }

        response = qm.client.table("user_quotas").update(updates).eq("user_id", user_id).execute()

        if response.data:
            print("[SUCCESS] 配额重置成功！")

            # 验证重置结果
            print("\n[重置后配额状态]")
            quota_status = qm.get_quota_status(user_id, "free")
            print(f"  daily_plan 剩余: {quota_status['remaining']['daily_plan']}")
            print(f"  weekly_report 剩余: {quota_status['remaining']['weekly_report']}")
            print(f"  chat 剩余: {quota_status['remaining']['chat']}")
            print(f"  theme_recommend 剩余: {quota_status['remaining']['theme_recommend']}")
            print(f"  theme_generate 剩余: {quota_status['remaining']['theme_generate']}")

            print("\n" + "=" * 60)
            print("  配额重置完成！现在可以继续测试了")
            print("=" * 60 + "\n")
            return True
        else:
            print("[ERROR] 配额重置失败：没有返回数据")
            return False

    except Exception as e:
        print(f"[ERROR] 重置配额时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    reset_user_quota()
