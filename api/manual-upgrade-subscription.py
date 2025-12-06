"""
手动升级订阅API - 方案A主动查询机制
POST /api/manual-upgrade-subscription
Body: {
    "user_id": "xxx",
    "plan_type": "pro_monthly" | "pro_yearly" | "lifetime",
    "out_trade_no": "GAIYA123456"
}

当客户端检测到支付成功时,主动调用此API更新会员状态,不依赖Z-Pay回调
"""
from http.server import BaseHTTPRequestHandler
import json
import sys
import os
from datetime import datetime, timedelta

try:
    from subscription_manager import SubscriptionManager
    from validators_enhanced import validate_user_id, validate_plan_type
    from cors_config import get_cors_origin
    from supabase import create_client, Client
except ImportError:
    sys.path.insert(0, os.path.dirname(__file__))
    from subscription_manager import SubscriptionManager
    from validators_enhanced import validate_user_id, validate_plan_type
    from cors_config import get_cors_origin
    from supabase import create_client, Client

# Supabase配置
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")


class handler(BaseHTTPRequestHandler):
    """手动升级订阅处理器"""

    def do_OPTIONS(self):
        """处理CORS预检请求"""
        request_origin = self.headers.get('Origin', '')
        allowed_origin = get_cors_origin(request_origin)

        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', allowed_origin)
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '3600')
        self.end_headers()

    def do_POST(self):
        """处理手动升级请求"""
        try:
            # CORS配置
            request_origin = self.headers.get('Origin', '')
            self.allowed_origin = get_cors_origin(request_origin)

            # 1. 验证Authorization
            auth_header = self.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                self._send_error(401, "Unauthorized")
                return

            # 2. 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self._send_error(400, "Empty request body")
                return

            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)

            # 3. 验证参数
            user_id = data.get("user_id")
            plan_type = data.get("plan_type")
            out_trade_no = data.get("out_trade_no", "")

            # 验证user_id
            is_valid, error_msg = validate_user_id(user_id, require_uuid=True)
            if not is_valid:
                self._send_error(400, error_msg)
                return

            # 验证plan_type
            is_valid, error_msg, correct_price = validate_plan_type(plan_type)
            if not is_valid:
                self._send_error(400, error_msg)
                return

            print(f"[MANUAL-UPGRADE] Processing: user={user_id}, plan={plan_type}, order={out_trade_no}", file=sys.stderr)

            # 4. ✅ 核心修复: 必须验证订单真的已支付!
            if not out_trade_no:
                self._send_error(400, "Missing out_trade_no parameter")
                return

            # 4.1 先查询 payment_cache 表(webhook 回调写入的缓存)
            cache_result = self._query_payment_cache(out_trade_no)
            if cache_result and cache_result.get("status") == "paid":
                print(f"[MANUAL-UPGRADE] ✅ Cache confirms payment is PAID", file=sys.stderr)
                is_paid = True
            else:
                # 4.2 缓存未命中,主动查询 Z-Pay API
                print(f"[MANUAL-UPGRADE] Cache miss, querying Z-Pay API...", file=sys.stderr)
                from zpay_manager import ZPayManager
                zpay = ZPayManager()

                result = zpay.query_order(out_trade_no=out_trade_no)

                if not result.get("success"):
                    error_msg = result.get("error", "Order not found")
                    print(f"[MANUAL-UPGRADE] ❌ Z-Pay query failed: {error_msg}", file=sys.stderr)
                    self._send_error(400, f"Order not paid: {error_msg}")
                    return

                order = result.get("order", {})
                order_status = order.get("status")

                # 验证支付状态
                is_paid = self._is_paid_status(order_status)

                if not is_paid:
                    print(f"[MANUAL-UPGRADE] ❌ Order not paid yet: status={order_status}", file=sys.stderr)
                    self._send_error(400, f"Order not paid yet (status: {order_status})")
                    return

                print(f"[MANUAL-UPGRADE] ✅ Z-Pay confirms payment is PAID", file=sys.stderr)

            # 5. 连接Supabase
            if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
                self._send_error(500, "Supabase configuration missing")
                return

            supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

            # 6. 获取订阅计划详情
            sm = SubscriptionManager()
            plan_data = sm.PLANS.get(plan_type)

            if not plan_data:
                self._send_error(400, "Invalid plan_type")
                return

            # 6. 计算到期时间
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
                self._send_error(400, f"Unsupported plan_type: {plan_type}")
                return

            # 7. 更新用户表
            print(f"[MANUAL-UPGRADE] Updating user: tier={tier}, expires={expires_at}", file=sys.stderr)

            # ✅ 修复: 使用 RPC 调用绕过 PostgREST schema cache 问题
            try:
                # 方法1: 尝试使用 RPC (如果存在)
                result = supabase.rpc('upgrade_user_subscription', {
                    'p_user_id': user_id,
                    'p_tier': tier,
                    'p_expires_at': expires_at
                }).execute()

                print(f"[MANUAL-UPGRADE] RPC upgrade successful", file=sys.stderr)
                updated_user = {"tier": tier, "subscription_expires_at": expires_at}

            except Exception as rpc_error:
                print(f"[MANUAL-UPGRADE] RPC not available, using direct update: {rpc_error}", file=sys.stderr)

                # 方法2: 直接更新,显式指定字段
                update_data = {
                    "tier": tier,
                    "updated_at": datetime.now().isoformat()
                }

                # 只有非终身会员才设置过期时间
                if expires_at is not None:
                    update_data["subscription_expires_at"] = expires_at

                print(f"[MANUAL-UPGRADE] Update data: {update_data}", file=sys.stderr)

                result = supabase.table("users").update(update_data).eq("id", user_id).execute()

                if not result.data:
                    self._send_error(500, "Failed to update user")
                    return

                updated_user = result.data[0]

            # 8. 记录支付记录(如果订单号提供)
            if out_trade_no:
                try:
                    payment_data = {
                        "user_id": user_id,
                        "order_id": out_trade_no,
                        "amount": plan_data["price"],
                        "plan_type": plan_type,
                        "status": "completed",
                        "payment_method": "zpay",
                        "created_at": datetime.now().isoformat()
                    }
                    supabase.table("payments").insert(payment_data).execute()
                    print(f"[MANUAL-UPGRADE] Payment record created: {out_trade_no}", file=sys.stderr)
                except Exception as e:
                    # 支付记录失败不影响升级
                    print(f"[MANUAL-UPGRADE] Warning: Failed to create payment record: {e}", file=sys.stderr)

            # 9. 返回成功
            print(f"[MANUAL-UPGRADE] ✓ Success: user={user_id} upgraded to {tier}", file=sys.stderr)

            self._send_success({
                "success": True,
                "user_tier": updated_user.get("tier"),
                "subscription_expires_at": updated_user.get("subscription_expires_at"),
                "message": "Subscription upgraded successfully"
            })

        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
        except Exception as e:
            print(f"[MANUAL-UPGRADE] Error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            self._send_error(500, f"Internal server error: {str(e)}")

    def _send_success(self, data: dict):
        """发送成功响应"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', self.allowed_origin)
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def _send_error(self, code: int, message: str):
        """发送错误响应"""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', getattr(self, 'allowed_origin', '*'))
        self.end_headers()

        error_response = {
            "success": False,
            "error": message
        }
        self.wfile.write(json.dumps(error_response).encode('utf-8'))

    def _query_payment_cache(self, out_trade_no: str) -> dict:
        """
        从 payment_cache 表查询支付状态

        这个表由 webhook 回调写入,当支付成功时 Z-Pay 会主动通知我们。

        Returns:
            dict: 缓存记录,如果未找到返回 None
        """
        try:
            from supabase_client import get_supabase_client

            print(f"[MANUAL-UPGRADE] Querying payment_cache for: {out_trade_no}", file=sys.stderr)
            sys.stderr.flush()

            supabase = get_supabase_client()
            response = supabase.table('payment_cache').select('*').eq(
                'out_trade_no', out_trade_no
            ).execute()

            if response.data and len(response.data) > 0:
                cache_record = response.data[0]
                print(f"[MANUAL-UPGRADE] Cache found: status={cache_record.get('status')}", file=sys.stderr)
                sys.stderr.flush()
                return cache_record

            print(f"[MANUAL-UPGRADE] No cache record found", file=sys.stderr)
            sys.stderr.flush()
            return None

        except Exception as e:
            print(f"[MANUAL-UPGRADE] Cache query error: {type(e).__name__}: {str(e)}", file=sys.stderr)
            sys.stderr.flush()
            return None

    @staticmethod
    def _is_paid_status(status_value) -> bool:
        """
        将ZPAY返回的status值统一转换为布尔标记。
        ZPAY会把status序列化为"1"/"0",这里同时兼容字符串和数值。
        """
        if status_value is None:
            return False

        if isinstance(status_value, str):
            normalized = status_value.strip().lower()
            if normalized in {"paid", "unpaid"}:
                return normalized == "paid"
            if normalized == "":
                return False
            status_value = normalized

        try:
            numeric_status = int(float(status_value))
            return numeric_status == 1
        except (ValueError, TypeError):
            return False
