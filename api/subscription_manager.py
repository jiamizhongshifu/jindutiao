"""
GaiYa每日进度条 - 订阅管理器
处理用户订阅、续费、取消等业务逻辑
"""
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any, cast
from supabase import create_client, Client
import sys

# Supabase配置
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
# 优先使用Service Key（绕过RLS），否则使用Anon Key
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY", "")


class SubscriptionManager:
    """订阅管理器"""

    # 订阅计划定价
    PLANS = {
        "pro_monthly": {
            "name": "Pro月度订阅",
            "price": 0.1,  # ⚠️ 测试价格 (原价: 29.0)
            "currency": "CNY",
            "duration_days": 30
        },
        "pro_yearly": {
            "name": "Pro年度订阅",
            "price": 0.1,  # ⚠️ 测试价格 (原价: 199.0)
            "currency": "CNY",
            "duration_days": 365
        },
        "lifetime": {
            "name": "终身会员",
            "price": 0.1,  # ⚠️ 测试价格 (原价: 599.0)
            "currency": "CNY",
            "duration_days": None  # 永久
        }
    }

    def __init__(self):
        """初始化Supabase客户端"""
        if not SUPABASE_URL or not SUPABASE_KEY:
            print("WARNING: Supabase credentials not configured", file=sys.stderr)
            self.client = None
        else:
            try:
                self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
                print("SubscriptionManager initialized successfully", file=sys.stderr)
            except Exception as e:
                print(f"Failed to initialize Supabase client: {e}", file=sys.stderr)
                self.client = None

    def create_subscription(
        self,
        user_id: str,
        plan_type: str,
        payment_id: str,
        stripe_subscription_id: str = "",
        stripe_customer_id: str = "",
        payment_provider: str = "zpay"
    ) -> Dict:
        """
        创建订阅

        Args:
            user_id: 用户ID
            plan_type: 订阅类型 (pro_monthly, pro_yearly, lifetime)
            payment_id: 支付记录ID
            stripe_subscription_id: Stripe订阅ID（可选）
            stripe_customer_id: Stripe客户ID（可选）
            payment_provider: 支付提供商（zpay/stripe）

        Returns:
            订阅信息
        """
        if not self.client:
            return {"success": False, "error": "Supabase not configured"}

        if plan_type not in self.PLANS:
            return {"success": False, "error": "Invalid plan type"}

        try:
            plan = self.PLANS[plan_type]
            now = datetime.now()

            # 计算过期时间
            if plan["duration_days"]:
                expires_at = now + timedelta(days=cast(int, plan["duration_days"]))
            else:
                expires_at = None  # 终身会员

            # 1. 创建订阅记录
            subscription_data = {
                "user_id": user_id,
                "plan_type": plan_type,
                "price": plan["price"],
                "currency": plan["currency"],
                "status": "active",
                "started_at": now.isoformat(),
                "expires_at": expires_at.isoformat() if expires_at else None,
                "payment_id": payment_id,
                "payment_provider": payment_provider,
                "auto_renew": True if plan["duration_days"] else False
            }

            # 添加Stripe特有字段
            if stripe_subscription_id:
                subscription_data["stripe_subscription_id"] = stripe_subscription_id
            if stripe_customer_id:
                subscription_data["stripe_customer_id"] = stripe_customer_id

            sub_response = self.client.table("subscriptions").insert(subscription_data).execute()

            # 2. 更新用户等级和Stripe客户ID
            user_tier = "lifetime" if plan_type == "lifetime" else "pro"
            user_update_data = {"user_tier": user_tier}
            if stripe_customer_id:
                user_update_data["stripe_customer_id"] = stripe_customer_id

            self.client.table("users").update(user_update_data).eq("id", user_id).execute()

            # 3. 更新配额
            if user_tier in ["pro", "lifetime"]:
                self.client.table("user_quotas").update({
                    "user_tier": user_tier,
                    "daily_plan_total": 20,
                    "weekly_report_total": 10,
                    "chat_total": 100
                }).eq("user_id", user_id).execute()

            print(f"Subscription created for user {user_id}: {plan_type}", file=sys.stderr)

            return {
                "success": True,
                "subscription": sub_response.data[0] if sub_response.data else None
            }

        except Exception as e:
            print(f"Error creating subscription: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}

    def get_user_subscription(self, user_id: str) -> Optional[Dict]:
        """
        获取用户当前订阅

        Args:
            user_id: 用户ID

        Returns:
            订阅信息
        """
        if not self.client:
            return None

        try:
            # 查询活跃的订阅（按开始时间倒序，取最新的）
            response = self.client.table("subscriptions").select("*").eq(
                "user_id", user_id
            ).eq("status", "active").order("started_at", desc=True).limit(1).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]

            return None

        except Exception as e:
            print(f"Error getting user subscription: {e}", file=sys.stderr)
            return None

    def check_subscription_status(self, user_id: str) -> Dict:
        """
        检查订阅状态（过期自动处理）

        Args:
            user_id: 用户ID

        Returns:
            订阅状态
        """
        subscription = self.get_user_subscription(user_id)

        if not subscription:
            return {
                "is_active": False,
                "user_tier": "free"
            }

        # 检查是否过期
        if subscription["expires_at"]:
            expires_at = datetime.fromisoformat(subscription["expires_at"].replace("Z", "+00:00"))
            now = datetime.now(expires_at.tzinfo)

            if now >= expires_at:
                # 订阅已过期，更新状态
                self._expire_subscription(user_id, subscription["id"])
                return {
                    "is_active": False,
                    "user_tier": "free",
                    "expired_at": expires_at.isoformat()
                }

        # 订阅有效
        user_tier = "lifetime" if subscription["plan_type"] == "lifetime" else "pro"
        return {
            "is_active": True,
            "user_tier": user_tier,
            "plan_type": subscription["plan_type"],
            "expires_at": subscription["expires_at"],
            "auto_renew": subscription.get("auto_renew", False)
        }

    def _expire_subscription(self, user_id: str, subscription_id: str):
        """
        处理订阅过期

        Args:
            user_id: 用户ID
            subscription_id: 订阅ID
        """
        if not self.client:
            return

        try:
            # 1. 更新订阅状态为过期
            self.client.table("subscriptions").update({
                "status": "expired"
            }).eq("id", subscription_id).execute()

            # 2. 降级用户等级为免费
            self.client.table("users").update({
                "user_tier": "free"
            }).eq("id", user_id).execute()

            # 3. 重置配额为免费等级
            self.client.table("user_quotas").update({
                "user_tier": "free",
                "daily_plan_total": 3,
                "weekly_report_total": 1,
                "chat_total": 10
            }).eq("user_id", user_id).execute()

            print(f"Subscription expired for user {user_id}", file=sys.stderr)

        except Exception as e:
            print(f"Error expiring subscription: {e}", file=sys.stderr)

    def cancel_subscription(self, user_id: str, reason: Optional[str] = None) -> Dict:
        """
        取消订阅（立即生效）

        Args:
            user_id: 用户ID
            reason: 取消原因

        Returns:
            取消结果
        """
        if not self.client:
            return {"success": False, "error": "Supabase not configured"}

        try:
            subscription = self.get_user_subscription(user_id)

            if not subscription:
                return {
                    "success": False,
                    "error": "No active subscription found"
                }

            # 1. 更新订阅状态
            self.client.table("subscriptions").update({
                "status": "cancelled",
                "cancelled_at": datetime.now().isoformat(),
                "auto_renew": False
            }).eq("id", subscription["id"]).execute()

            # 2. 降级用户等级
            self.client.table("users").update({
                "user_tier": "free"
            }).eq("id", user_id).execute()

            # 3. 重置配额
            self.client.table("user_quotas").update({
                "user_tier": "free",
                "daily_plan_total": 3,
                "weekly_report_total": 1,
                "chat_total": 10
            }).eq("user_id", user_id).execute()

            print(f"Subscription cancelled for user {user_id}", file=sys.stderr)

            return {"success": True}

        except Exception as e:
            print(f"Error cancelling subscription: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}

    def toggle_auto_renew(self, user_id: str, auto_renew: bool) -> Dict:
        """
        开启/关闭自动续订

        Args:
            user_id: 用户ID
            auto_renew: 是否自动续订

        Returns:
            更新结果
        """
        if not self.client:
            return {"success": False, "error": "Supabase not configured"}

        try:
            subscription = self.get_user_subscription(user_id)

            if not subscription:
                return {
                    "success": False,
                    "error": "No active subscription found"
                }

            # 终身会员不需要自动续订
            if subscription["plan_type"] == "lifetime":
                return {
                    "success": False,
                    "error": "Lifetime members don't need auto-renew"
                }

            self.client.table("subscriptions").update({
                "auto_renew": auto_renew
            }).eq("id", subscription["id"]).execute()

            print(f"Auto-renew {'enabled' if auto_renew else 'disabled'} for user {user_id}", file=sys.stderr)

            return {"success": True, "auto_renew": auto_renew}

        except Exception as e:
            print(f"Error toggling auto-renew: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}

    def get_subscription_history(self, user_id: str) -> List[Dict]:
        """
        获取用户订阅历史

        Args:
            user_id: 用户ID

        Returns:
            订阅历史列表
        """
        if not self.client:
            return []

        try:
            response = self.client.table("subscriptions").select("*").eq(
                "user_id", user_id
            ).order("started_at", desc=True).execute()

            return response.data if response.data else []

        except Exception as e:
            print(f"Error getting subscription history: {e}", file=sys.stderr)
            return []

    def process_renewal(self, subscription_id: str, payment_id: str) -> Dict:
        """
        处理订阅续费

        Args:
            subscription_id: 订阅ID
            payment_id: 新的支付记录ID

        Returns:
            续费结果
        """
        if not self.client:
            return {"success": False, "error": "Supabase not configured"}

        try:
            # 1. 获取现有订阅
            sub_response = self.client.table("subscriptions").select("*").eq("id", subscription_id).execute()

            if not sub_response.data:
                return {
                    "success": False,
                    "error": "Subscription not found"
                }

            old_sub = sub_response.data[0]
            plan = self.PLANS.get(old_sub["plan_type"])

            if not plan or not plan["duration_days"]:
                return {
                    "success": False,
                    "error": "Cannot renew this subscription type"
                }

            # 2. 计算新的过期时间（从当前过期时间延长，或从现在开始）
            if old_sub["expires_at"]:
                old_expires = datetime.fromisoformat(old_sub["expires_at"].replace("Z", "+00:00"))
                now = datetime.now(old_expires.tzinfo)

                if old_expires > now:
                    # 还未过期，从过期时间延长
                    new_expires = old_expires + timedelta(days=cast(int, plan["duration_days"]))
                else:
                    # 已过期，从现在开始
                    new_expires = now + timedelta(days=cast(int, plan["duration_days"]))
            else:
                new_expires = datetime.now() + timedelta(days=cast(int, plan["duration_days"]))

            # 3. 创建新的订阅记录
            new_subscription_data = {
                "user_id": old_sub["user_id"],
                "plan_type": old_sub["plan_type"],
                "price": plan["price"],
                "currency": plan["currency"],
                "status": "active",
                "started_at": datetime.now().isoformat(),
                "expires_at": new_expires.isoformat(),
                "payment_id": payment_id,
                "auto_renew": old_sub.get("auto_renew", True)
            }

            new_sub_response = self.client.table("subscriptions").insert(new_subscription_data).execute()

            # 4. 标记旧订阅为已续费
            self.client.table("subscriptions").update({
                "status": "renewed"
            }).eq("id", subscription_id).execute()

            print(f"Subscription renewed for user {old_sub['user_id']}", file=sys.stderr)

            return {
                "success": True,
                "subscription": new_sub_response.data[0] if new_sub_response.data else None
            }

        except Exception as e:
            print(f"Error processing renewal: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}

    def get_pricing_info(self) -> List[Dict]:
        """
        获取所有定价方案信息

        Returns:
            定价方案列表
        """
        return [
            {
                "plan_type": plan_type,
                "name": plan_data["name"],
                "price": plan_data["price"],
                "currency": plan_data["currency"],
                "duration_days": plan_data["duration_days"],
                "features": self._get_plan_features(plan_type)
            }
            for plan_type, plan_data in self.PLANS.items()
        ]

    def _get_plan_features(self, plan_type: str) -> List[str]:
        """获取计划功能列表"""
        if plan_type in ["pro_monthly", "pro_yearly"]:
            return [
                "20次/天 AI智能规划",
                "去除进度条水印",
                "抢先体验后续更新的新功能",
                "加入VIP会员群，参与后续功能规划"
            ]
        elif plan_type == "lifetime":
            return [
                "所有高级版功能",
                "终身免费更新",
                "优先客服支持",
                "未来新功能抢先体验",
                "专属终身会员徽章"
            ]
        else:
            return []
