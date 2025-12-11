"""
PyDayBar 配额管理工具
使用Supabase进行真实配额追踪和管理
"""
import os
from datetime import datetime, timedelta
from supabase import create_client, Client
from typing import Dict, Optional, Any
import sys

# Supabase配置
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")

class QuotaManager:
    """配额管理器"""

    def __init__(self):
        """初始化Supabase客户端"""
        if not SUPABASE_URL or not SUPABASE_KEY:
            print("WARNING: Supabase credentials not configured", file=sys.stderr)
            self.client = None
        else:
            try:
                self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
                print("Supabase client initialized successfully", file=sys.stderr)
            except Exception as e:
                print(f"Failed to initialize Supabase client: {e}", file=sys.stderr)
                self.client = None

    def get_or_create_user(self, user_id: str, user_tier: str = "free") -> Optional[Dict]:
        """获取或创建用户配额记录"""
        if not self.client:
            return self._get_fallback_quota(user_tier)

        try:
            # 查询用户
            response = self.client.table("user_quotas").select("*").eq("user_id", user_id).execute()

            if response.data and len(response.data) > 0:
                # 用户存在，检查是否需要更新tier和重置配额
                user_quota = response.data[0]
                # ⚠️ 关键修复: 如果tier发生变化,需要更新数据库
                if user_quota.get("user_tier") != user_tier:
                    print(f"User tier changed: {user_quota.get('user_tier')} -> {user_tier}, updating...", file=sys.stderr)
                    self._update_user_tier(user_id, user_tier, user_quota)
                    # 重新获取更新后的数据
                    response = self.client.table("user_quotas").select("*").eq("user_id", user_id).execute()
                    if response.data and len(response.data) > 0:
                        user_quota = response.data[0]
                return self._check_and_reset_quota(user_quota)
            else:
                # 用户不存在，创建新用户
                return self._create_user_quota(user_id, user_tier)

        except Exception as e:
            print(f"Error getting user quota: {e}", file=sys.stderr)
            return self._get_fallback_quota(user_tier)

    def _create_user_quota(self, user_id: str, user_tier: str) -> Dict:
        """创建新用户配额"""
        from datetime import timezone

        # 使用UTC+8时区（中国标准时间）计算重置时间
        china_tz = timezone(timedelta(hours=8))
        now_china = datetime.now(china_tz)

        # 计算明天零点（UTC+8时区）
        tomorrow_midnight = (now_china + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        # 计算下周同一时间的零点
        next_week_midnight = (now_china + timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)

        # 根据用户等级设置配额
        if user_tier == "pro":
            quotas = {
                "daily_plan_total": 20,
                "weekly_report_total": 10,
                "chat_total": 100
            }
        else:
            quotas = {
                "daily_plan_total": 3,
                "weekly_report_total": 1,
                "chat_total": 10
            }

        new_user = {
            "user_id": user_id,
            "user_tier": user_tier,
            **quotas,
            "daily_plan_used": 0,
            "weekly_report_used": 0,
            "chat_used": 0,
            "daily_plan_reset_at": tomorrow_midnight.isoformat(),
            "weekly_report_reset_at": next_week_midnight.isoformat(),
            "chat_reset_at": tomorrow_midnight.isoformat()
        }

        try:
            response = self.client.table("user_quotas").insert(new_user).execute()
            print(f"Created new user quota for {user_id}", file=sys.stderr)
            return response.data[0] if response.data else new_user
        except Exception as e:
            print(f"Error creating user quota: {e}", file=sys.stderr)
            return new_user

    def _check_and_reset_quota(self, user_quota: Dict) -> Dict:
        """检查并重置过期的配额"""
        from datetime import timezone

        # 使用UTC+8时区（中国标准时间）判断是否需要重置
        china_tz = timezone(timedelta(hours=8))
        now_china = datetime.now(china_tz)
        updates: Dict[str, Any] = {}

        # 检查每日配额
        if user_quota.get("daily_plan_reset_at"):
            reset_time = datetime.fromisoformat(user_quota["daily_plan_reset_at"].replace("Z", "+00:00"))
            if now_china >= reset_time:
                updates["daily_plan_used"] = 0
                # 计算明天零点（UTC+8时区）
                next_reset = (now_china + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                updates["daily_plan_reset_at"] = next_reset.isoformat()

        if user_quota.get("chat_reset_at"):
            reset_time = datetime.fromisoformat(user_quota["chat_reset_at"].replace("Z", "+00:00"))
            if now_china >= reset_time:
                updates["chat_used"] = 0
                next_reset = (now_china + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                updates["chat_reset_at"] = next_reset.isoformat()

        # 检查周配额
        if user_quota.get("weekly_report_reset_at"):
            reset_time = datetime.fromisoformat(user_quota["weekly_report_reset_at"].replace("Z", "+00:00"))
            if now_china >= reset_time:
                updates["weekly_report_used"] = 0
                # 计算下周同一时间的零点
                next_reset = (now_china + timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
                updates["weekly_report_reset_at"] = next_reset.isoformat()

        # 如果有更新，写回数据库
        if updates and self.client:
            try:
                response = self.client.table("user_quotas").update(updates).eq("user_id", user_quota["user_id"]).execute()
                print(f"Reset quota for user {user_quota['user_id']}: {list(updates.keys())}", file=sys.stderr)
                return response.data[0] if response.data else {**user_quota, **updates}
            except Exception as e:
                print(f"Error resetting quota: {e}", file=sys.stderr)
                return {**user_quota, **updates}

        return user_quota

    def use_quota(self, user_id: str, quota_type: str, amount: int = 1) -> Dict:
        """
        使用配额

        Args:
            user_id: 用户ID
            quota_type: 配额类型 (daily_plan, weekly_report, chat, theme_recommend, theme_generate)
            amount: 使用数量

        Returns:
            更新后的配额信息
        """
        if not self.client:
            return {"success": False, "error": "Supabase not configured"}

        try:
            # 获取当前配额
            user_quota = self.get_or_create_user(user_id)
            if not user_quota:
                return {"success": False, "error": "Failed to get user quota"}

            # 检查配额是否足够
            used_key = f"{quota_type}_used"
            total_key = f"{quota_type}_total"

            current_used = user_quota.get(used_key, 0)
            total_quota = user_quota.get(total_key, 0)

            if current_used + amount > total_quota:
                return {
                    "success": False,
                    "error": "Quota exceeded",
                    "remaining": total_quota - current_used,
                    "requested": amount
                }

            # 扣除配额
            new_used = current_used + amount
            response = self.client.table("user_quotas").update({
                used_key: new_used
            }).eq("user_id", user_id).execute()

            print(f"Used {amount} {quota_type} quota for {user_id}, remaining: {total_quota - new_used}", file=sys.stderr)

            return {
                "success": True,
                "quota_type": quota_type,
                "used": new_used,
                "total": total_quota,
                "remaining": total_quota - new_used
            }

        except Exception as e:
            print(f"Error using quota: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}

    def _update_user_tier(self, user_id: str, new_tier: str, old_quota: Dict):
        """更新用户等级并调整配额"""
        if not self.client:
            return

        try:
            # 根据新等级设置配额
            if new_tier == "pro":
                new_quotas = {
                    "user_tier": new_tier,
                    "daily_plan_total": 20,
                    "weekly_report_total": 10,
                    "chat_total": 100
                }
            else:
                new_quotas = {
                    "user_tier": new_tier,
                    "daily_plan_total": 3,
                    "weekly_report_total": 1,
                    "chat_total": 10
                }

            # 更新数据库
            self.client.table("user_quotas").update(new_quotas).eq("user_id", user_id).execute()
            print(f"Updated user tier from {old_quota.get('user_tier')} to {new_tier}", file=sys.stderr)

        except Exception as e:
            print(f"Error updating user tier: {e}", file=sys.stderr)

    def get_quota_status(self, user_id: str, user_tier: str = "free") -> Dict:
        """获取配额状态"""
        user_quota = self.get_or_create_user(user_id, user_tier)

        if not user_quota:
            return self._get_fallback_quota(user_tier)

        return {
            "remaining": {
                "daily_plan": user_quota.get("daily_plan_total", 3) - user_quota.get("daily_plan_used", 0),
                "weekly_report": user_quota.get("weekly_report_total", 1) - user_quota.get("weekly_report_used", 0),
                "chat": user_quota.get("chat_total", 10) - user_quota.get("chat_used", 0)
            },
            "user_tier": user_quota.get("user_tier", user_tier)
        }

    def _get_fallback_quota(self, user_tier: str) -> Dict:
        """返回降级配额（当Supabase不可用时）"""
        if user_tier == "pro":
            return {
                "daily_plan_total": 20,
                "daily_plan_used": 0,
                "weekly_report_total": 10,
                "weekly_report_used": 0,
                "chat_total": 100,
                "chat_used": 0,
                "user_tier": user_tier
            }
        else:
            return {
                "daily_plan_total": 3,
                "daily_plan_used": 0,
                "weekly_report_total": 1,
                "weekly_report_used": 0,
                "chat_total": 10,
                "chat_used": 0,
                "user_tier": user_tier
            }
