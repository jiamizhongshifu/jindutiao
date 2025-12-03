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

            # 4. 连接Supabase
            if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
                self._send_error(500, "Supabase configuration missing")
                return

            supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

            # 5. 获取订阅计划详情
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

            update_data = {
                "tier": tier,
                "is_active": True,
                "subscription_expires_at": expires_at,
                "updated_at": datetime.now().isoformat()
            }

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
                "is_active": updated_user.get("is_active"),
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
