"""
GaiYa每日进度条 - Stripe支付管理器
基于Stripe API实现海外支付功能
"""
import os
import stripe
import sys
from datetime import datetime
from typing import Dict, Optional


# Stripe配置
# 注意：敏感凭证必须通过环境变量配置，不要硬编码到代码中
# 在Vercel部署时，请在项目设置 → Environment Variables 中配置
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# 产品价格ID
STRIPE_PRICE_MONTHLY = os.getenv("STRIPE_PRICE_MONTHLY")
STRIPE_PRICE_YEARLY = os.getenv("STRIPE_PRICE_YEARLY")
STRIPE_PRICE_LIFETIME = os.getenv("STRIPE_PRICE_LIFETIME")


class StripeManager:
    """Stripe支付管理器"""

    def __init__(self):
        """初始化Stripe配置"""
        self.secret_key = STRIPE_SECRET_KEY
        self.webhook_secret = STRIPE_WEBHOOK_SECRET

        # 价格ID映射
        self.price_ids = {
            "pro_monthly": STRIPE_PRICE_MONTHLY,
            "pro_yearly": STRIPE_PRICE_YEARLY,
            "lifetime": STRIPE_PRICE_LIFETIME
        }

        # 安全加固：强制要求凭证配置
        if not self.secret_key:
            error_msg = "CRITICAL: Stripe credentials (STRIPE_SECRET_KEY) are required but not configured"
            print(f"[SECURITY] {error_msg}", file=sys.stderr)
            raise ValueError(error_msg)

        # 初始化Stripe
        stripe.api_key = self.secret_key

        print("[Stripe] Manager initialized successfully", file=sys.stderr)

    def create_checkout_session(
        self,
        plan_type: str,
        user_email: str,
        user_id: str,
        success_url: str,
        cancel_url: str,
        client_reference_id: Optional[str] = None
    ) -> Dict:
        """
        创建Stripe Checkout Session

        Args:
            plan_type: 计划类型（pro_monthly/pro_yearly/lifetime）
            user_email: 用户邮箱
            user_id: 用户ID
            success_url: 支付成功后跳转URL
            cancel_url: 支付取消后跳转URL
            client_reference_id: 客户端参考ID（可选）

        Returns:
            Checkout Session信息
        """
        try:
            # 获取价格ID
            price_id = self.price_ids.get(plan_type)
            if not price_id:
                return {
                    "success": False,
                    "error": f"Invalid plan type: {plan_type}",
                    "error_code": "INVALID_PLAN"
                }

            # 确定支付模式
            if plan_type == "lifetime":
                mode = "payment"  # 一次性支付
            else:
                mode = "subscription"  # 订阅

            # 创建Checkout Session
            session_params = {
                "payment_method_types": ["card"],
                "line_items": [{
                    "price": price_id,
                    "quantity": 1
                }],
                "mode": mode,
                "success_url": success_url,
                "cancel_url": cancel_url,
                "customer_email": user_email,
                "metadata": {
                    "user_id": user_id,
                    "plan_type": plan_type
                },
                "allow_promotion_codes": True,  # 允许优惠码
            }

            # 添加客户端参考ID
            if client_reference_id:
                session_params["client_reference_id"] = client_reference_id

            # 订阅模式额外配置
            if mode == "subscription":
                session_params["subscription_data"] = {
                    "metadata": {
                        "user_id": user_id,
                        "plan_type": plan_type
                    }
                }

            session = stripe.checkout.Session.create(**session_params)

            print(f"[Stripe] Created checkout session: {session.id}, plan: {plan_type}, user: {user_email}", file=sys.stderr)

            return {
                "success": True,
                "session_id": session.id,
                "checkout_url": session.url,
                "plan_type": plan_type
            }

        except stripe.error.StripeError as e:
            error_msg = str(e)
            print(f"[Stripe] Error creating checkout session: {error_msg}", file=sys.stderr)
            return {
                "success": False,
                "error": error_msg,
                "error_code": "STRIPE_ERROR"
            }
        except Exception as e:
            error_msg = str(e)
            print(f"[Stripe] Unexpected error: {error_msg}", file=sys.stderr)
            return {
                "success": False,
                "error": error_msg,
                "error_code": "UNEXPECTED_ERROR"
            }

    def verify_webhook_signature(self, payload: bytes, sig_header: str) -> Dict:
        """
        验证Webhook签名

        Args:
            payload: 请求体原始数据
            sig_header: Stripe-Signature头

        Returns:
            验证结果和事件对象
        """
        try:
            if not self.webhook_secret:
                return {
                    "success": False,
                    "error": "Webhook secret not configured",
                    "error_code": "NO_WEBHOOK_SECRET"
                }

            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )

            return {
                "success": True,
                "event": event
            }

        except stripe.error.SignatureVerificationError as e:
            print(f"[Stripe] Webhook signature verification failed: {e}", file=sys.stderr)
            return {
                "success": False,
                "error": "Invalid signature",
                "error_code": "INVALID_SIGNATURE"
            }
        except Exception as e:
            print(f"[Stripe] Webhook verification error: {e}", file=sys.stderr)
            return {
                "success": False,
                "error": str(e),
                "error_code": "VERIFICATION_ERROR"
            }

    def get_subscription(self, subscription_id: str) -> Dict:
        """
        获取订阅信息

        Args:
            subscription_id: Stripe订阅ID

        Returns:
            订阅信息
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)

            return {
                "success": True,
                "subscription": {
                    "id": subscription.id,
                    "status": subscription.status,
                    "current_period_start": subscription.current_period_start,
                    "current_period_end": subscription.current_period_end,
                    "cancel_at_period_end": subscription.cancel_at_period_end,
                    "plan_type": subscription.metadata.get("plan_type", "unknown")
                }
            }

        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e),
                "error_code": "STRIPE_ERROR"
            }

    def cancel_subscription(self, subscription_id: str, at_period_end: bool = True) -> Dict:
        """
        取消订阅

        Args:
            subscription_id: Stripe订阅ID
            at_period_end: 是否在当前周期结束时取消

        Returns:
            取消结果
        """
        try:
            if at_period_end:
                # 在当前周期结束时取消
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                # 立即取消
                subscription = stripe.Subscription.delete(subscription_id)

            print(f"[Stripe] Cancelled subscription: {subscription_id}", file=sys.stderr)

            return {
                "success": True,
                "subscription_id": subscription_id,
                "cancel_at_period_end": at_period_end
            }

        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e),
                "error_code": "STRIPE_ERROR"
            }

    def create_customer_portal_session(self, customer_id: str, return_url: str) -> Dict:
        """
        创建客户门户会话（用户自助管理订阅）

        Args:
            customer_id: Stripe客户ID
            return_url: 返回URL

        Returns:
            门户会话信息
        """
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )

            return {
                "success": True,
                "portal_url": session.url
            }

        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e),
                "error_code": "STRIPE_ERROR"
            }

    def get_plan_info(self, plan_type: str) -> Dict:
        """
        获取计划信息

        Args:
            plan_type: 计划类型

        Returns:
            计划信息
        """
        plans = {
            "pro_monthly": {
                "name": "GaiYa Pro - Monthly",
                "price": 4.99,
                "currency": "USD",
                "interval": "month",
                "description": "Monthly subscription with full access"
            },
            "pro_yearly": {
                "name": "GaiYa Pro - Yearly",
                "price": 39.99,
                "currency": "USD",
                "interval": "year",
                "description": "Annual subscription - Save 33%"
            },
            "lifetime": {
                "name": "GaiYa Lifetime",
                "price": 89.99,
                "currency": "USD",
                "interval": "one_time",
                "description": "One-time purchase, lifetime access"
            }
        }

        if plan_type not in plans:
            return {
                "success": False,
                "error": f"Invalid plan type: {plan_type}"
            }

        return {
            "success": True,
            "plan": plans[plan_type]
        }


# 单例模式
_stripe_manager = None

def get_stripe_manager() -> StripeManager:
    """获取Stripe管理器单例"""
    global _stripe_manager
    if _stripe_manager is None:
        _stripe_manager = StripeManager()
    return _stripe_manager
