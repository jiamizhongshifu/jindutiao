"""
Stripe Webhook处理API
POST /api/stripe-webhook
接收Stripe的webhook事件通知
"""
from http.server import BaseHTTPRequestHandler
import json
import sys
import os

try:
    from stripe_manager import StripeManager
    from subscription_manager import SubscriptionManager
    from supabase import create_client, Client
except ImportError:
    sys.path.insert(0, os.path.dirname(__file__))
    from stripe_manager import StripeManager
    from subscription_manager import SubscriptionManager
    from supabase import create_client, Client

# Supabase配置
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
# 优先使用Service Key（绕过RLS），否则使用Anon Key
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY", "")


class handler(BaseHTTPRequestHandler):
    """Stripe Webhook处理器"""

    def do_POST(self):
        """处理Stripe Webhook事件"""
        try:
            # 1. 读取原始请求体（用于签名验证）
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self._send_response(400, "Empty request body")
                return

            payload = self.rfile.read(content_length)

            # 2. 获取签名头
            sig_header = self.headers.get('Stripe-Signature')
            if not sig_header:
                print("[STRIPE-WEBHOOK] Missing Stripe-Signature header", file=sys.stderr)
                self._send_response(400, "Missing signature")
                return

            # 3. 验证签名
            stripe_manager = StripeManager()
            verify_result = stripe_manager.verify_webhook_signature(payload, sig_header)

            if not verify_result["success"]:
                print(f"[STRIPE-WEBHOOK] Signature verification failed: {verify_result.get('error')}", file=sys.stderr)
                self._send_response(400, "Invalid signature")
                return

            event = verify_result["event"]
            event_type = event["type"]

            print(f"[STRIPE-WEBHOOK] Received event: {event_type}", file=sys.stderr)

            # 4. 处理不同事件类型
            if event_type == "checkout.session.completed":
                self._handle_checkout_completed(event)
            elif event_type == "customer.subscription.updated":
                self._handle_subscription_updated(event)
            elif event_type == "customer.subscription.deleted":
                self._handle_subscription_deleted(event)
            elif event_type == "invoice.payment_succeeded":
                self._handle_invoice_paid(event)
            elif event_type == "invoice.payment_failed":
                self._handle_payment_failed(event)
            else:
                print(f"[STRIPE-WEBHOOK] Unhandled event type: {event_type}", file=sys.stderr)

            # 5. 返回成功响应
            self._send_response(200, "OK")

        except Exception as e:
            print(f"[STRIPE-WEBHOOK] Error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            self._send_response(500, f"Internal error: {str(e)}")

    def _handle_checkout_completed(self, event):
        """处理Checkout Session完成事件"""
        try:
            session = event["data"]["object"]

            # 提取信息
            session_id = session["id"]
            customer_email = session.get("customer_email", "")
            customer_id = session.get("customer", "")
            payment_status = session.get("payment_status", "")
            mode = session.get("mode", "")  # payment/subscription

            # 从metadata获取用户信息
            metadata = session.get("metadata", {})
            user_id = metadata.get("user_id")
            plan_type = metadata.get("plan_type")

            # 如果metadata中没有信息，尝试从其他地方获取
            if not user_id:
                # 尝试从customer_details获取email，然后查找用户
                customer_details = session.get("customer_details", {})
                customer_email = customer_details.get("email") or session.get("customer_email", "")

                if customer_email:
                    print(f"[STRIPE-WEBHOOK] No user_id in metadata, looking up by email: {customer_email}", file=sys.stderr)
                    user_id = self._get_user_id_by_email(customer_email)

                if not user_id:
                    print(f"[STRIPE-WEBHOOK] Cannot find user_id for email: {customer_email}", file=sys.stderr)
                    return

            # 如果没有plan_type，从金额推断
            if not plan_type:
                amount_total = session.get("amount_total", 0) / 100  # 转换为美元
                plan_type = self._infer_plan_type(amount_total)
                print(f"[STRIPE-WEBHOOK] Inferred plan_type from amount ${amount_total}: {plan_type}", file=sys.stderr)

                if not plan_type:
                    print(f"[STRIPE-WEBHOOK] Cannot infer plan_type from amount: ${amount_total}", file=sys.stderr)
                    return

            print(f"[STRIPE-WEBHOOK] Checkout completed: user={user_id}, plan={plan_type}, mode={mode}", file=sys.stderr)

            # 检查支付状态
            if payment_status != "paid":
                print(f"[STRIPE-WEBHOOK] Payment not completed: {payment_status}", file=sys.stderr)
                return

            # 获取金额（单位：分）
            amount_total = session.get("amount_total", 0) / 100  # 转换为美元

            # 获取订阅ID（如果是订阅模式）
            subscription_id = session.get("subscription", "")

            # 检查是否已处理
            if self._is_session_processed(session_id):
                print(f"[STRIPE-WEBHOOK] Session already processed: {session_id}", file=sys.stderr)
                return

            # 创建支付记录
            payment_id = self._create_payment_record(
                user_id=user_id,
                order_id=session_id,
                trade_no=subscription_id or session_id,
                amount=amount_total,
                plan_type=plan_type,
                payment_method="stripe",
                currency="USD",
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id
            )

            if not payment_id:
                print(f"[STRIPE-WEBHOOK] Failed to create payment record", file=sys.stderr)
                return

            # 创建订阅并激活会员
            sub_manager = SubscriptionManager()
            result = sub_manager.create_subscription(
                user_id=user_id,
                plan_type=plan_type,
                payment_id=payment_id,
                stripe_subscription_id=subscription_id,
                stripe_customer_id=customer_id
            )

            if result["success"]:
                print(f"[STRIPE-WEBHOOK] Subscription activated for user {user_id}", file=sys.stderr)
            else:
                print(f"[STRIPE-WEBHOOK] Failed to create subscription: {result.get('error')}", file=sys.stderr)

        except Exception as e:
            print(f"[STRIPE-WEBHOOK] Error handling checkout completed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)

    def _handle_subscription_updated(self, event):
        """处理订阅更新事件"""
        try:
            subscription = event["data"]["object"]
            subscription_id = subscription["id"]
            status = subscription["status"]

            metadata = subscription.get("metadata", {})
            user_id = metadata.get("user_id")

            print(f"[STRIPE-WEBHOOK] Subscription updated: {subscription_id}, status={status}", file=sys.stderr)

            if user_id:
                # 更新用户订阅状态
                self._update_subscription_status(user_id, subscription_id, status)

        except Exception as e:
            print(f"[STRIPE-WEBHOOK] Error handling subscription update: {e}", file=sys.stderr)

    def _handle_subscription_deleted(self, event):
        """处理订阅取消事件"""
        try:
            subscription = event["data"]["object"]
            subscription_id = subscription["id"]

            metadata = subscription.get("metadata", {})
            user_id = metadata.get("user_id")

            print(f"[STRIPE-WEBHOOK] Subscription deleted: {subscription_id}", file=sys.stderr)

            if user_id:
                # 取消用户订阅
                self._cancel_user_subscription(user_id, subscription_id)

        except Exception as e:
            print(f"[STRIPE-WEBHOOK] Error handling subscription deletion: {e}", file=sys.stderr)

    def _handle_invoice_paid(self, event):
        """处理发票支付成功事件（续费）"""
        try:
            invoice = event["data"]["object"]
            subscription_id = invoice.get("subscription")
            customer_id = invoice.get("customer")
            amount_paid = invoice.get("amount_paid", 0) / 100

            print(f"[STRIPE-WEBHOOK] Invoice paid: subscription={subscription_id}, amount=${amount_paid}", file=sys.stderr)

            # 这里可以记录续费记录或发送通知

        except Exception as e:
            print(f"[STRIPE-WEBHOOK] Error handling invoice paid: {e}", file=sys.stderr)

    def _handle_payment_failed(self, event):
        """处理支付失败事件"""
        try:
            invoice = event["data"]["object"]
            subscription_id = invoice.get("subscription")
            customer_email = invoice.get("customer_email")

            print(f"[STRIPE-WEBHOOK] Payment failed: subscription={subscription_id}, email={customer_email}", file=sys.stderr)

            # 这里可以发送邮件通知用户更新支付方式

        except Exception as e:
            print(f"[STRIPE-WEBHOOK] Error handling payment failed: {e}", file=sys.stderr)

    def _is_session_processed(self, session_id: str) -> bool:
        """检查Session是否已处理"""
        try:
            if not SUPABASE_URL or not SUPABASE_KEY:
                return False

            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

            result = supabase.table("payments").select("id").eq("order_id", session_id).execute()

            return len(result.data) > 0

        except Exception as e:
            print(f"[STRIPE-WEBHOOK] Error checking session: {e}", file=sys.stderr)
            return False

    def _create_payment_record(
        self,
        user_id: str,
        order_id: str,
        trade_no: str,
        amount: float,
        plan_type: str,
        payment_method: str,
        currency: str = "USD",
        stripe_customer_id: str = "",
        stripe_subscription_id: str = ""
    ) -> str:
        """创建支付记录"""
        try:
            if not SUPABASE_URL or not SUPABASE_KEY:
                print("[STRIPE-WEBHOOK] Supabase not configured", file=sys.stderr)
                return ""

            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

            payment_data = {
                "user_id": user_id,
                "order_id": order_id,
                "trade_no": trade_no,
                "amount": amount,
                "currency": currency,
                "plan_type": plan_type,
                "payment_method": payment_method,
                "status": "completed",
                "stripe_customer_id": stripe_customer_id,
                "stripe_subscription_id": stripe_subscription_id
            }

            result = supabase.table("payments").insert(payment_data).execute()

            if result.data and len(result.data) > 0:
                return result.data[0]["id"]

            return ""

        except Exception as e:
            print(f"[STRIPE-WEBHOOK] Error creating payment record: {e}", file=sys.stderr)
            return ""

    def _update_subscription_status(self, user_id: str, subscription_id: str, status: str):
        """更新订阅状态"""
        try:
            if not SUPABASE_URL or not SUPABASE_KEY:
                return

            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

            # 根据Stripe状态映射到我们的状态
            status_map = {
                "active": "active",
                "past_due": "past_due",
                "canceled": "canceled",
                "unpaid": "unpaid",
                "trialing": "active"
            }

            our_status = status_map.get(status, status)

            supabase.table("subscriptions").update({
                "status": our_status,
                "stripe_status": status
            }).eq("stripe_subscription_id", subscription_id).execute()

            print(f"[STRIPE-WEBHOOK] Updated subscription status: {subscription_id} -> {our_status}", file=sys.stderr)

        except Exception as e:
            print(f"[STRIPE-WEBHOOK] Error updating subscription status: {e}", file=sys.stderr)

    def _cancel_user_subscription(self, user_id: str, subscription_id: str):
        """取消用户订阅"""
        try:
            if not SUPABASE_URL or not SUPABASE_KEY:
                return

            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

            # 更新订阅状态为已取消
            supabase.table("subscriptions").update({
                "status": "canceled",
                "stripe_status": "canceled"
            }).eq("stripe_subscription_id", subscription_id).execute()

            # 更新用户等级为免费
            supabase.table("users").update({
                "user_tier": "free"
            }).eq("id", user_id).execute()

            print(f"[STRIPE-WEBHOOK] Cancelled subscription for user {user_id}", file=sys.stderr)

        except Exception as e:
            print(f"[STRIPE-WEBHOOK] Error cancelling subscription: {e}", file=sys.stderr)

    def _get_user_id_by_email(self, email: str) -> str:
        """通过邮箱查找用户ID"""
        try:
            if not SUPABASE_URL or not SUPABASE_KEY:
                return ""

            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

            # 查找用户
            response = supabase.table("users").select("id").eq("email", email).execute()

            if response.data and len(response.data) > 0:
                user_id = response.data[0]["id"]
                print(f"[STRIPE-WEBHOOK] Found user_id {user_id} for email {email}", file=sys.stderr)
                return user_id
            else:
                print(f"[STRIPE-WEBHOOK] No user found for email {email}", file=sys.stderr)
                return ""

        except Exception as e:
            print(f"[STRIPE-WEBHOOK] Error looking up user by email: {e}", file=sys.stderr)
            return ""

    def _infer_plan_type(self, amount: float) -> str:
        """从金额推断计划类型"""
        # Stripe金额精度可能有浮点误差，使用接近判断
        if abs(amount - 4.99) < 0.01:
            return "pro_monthly"
        elif abs(amount - 39.99) < 0.01:
            return "pro_yearly"
        elif abs(amount - 89.99) < 0.01:
            return "lifetime"
        else:
            print(f"[STRIPE-WEBHOOK] Unknown amount: ${amount}", file=sys.stderr)
            return ""

    def _send_response(self, code: int, message: str):
        """发送响应"""
        self.send_response(code)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(message.encode('utf-8'))
