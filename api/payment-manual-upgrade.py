"""
手动触发会员升级API
POST /api/payment-manual-upgrade
用于支付完成后手动确认并升级会员
"""
from http.server import BaseHTTPRequestHandler
import json
import sys
from datetime import datetime, timedelta

try:
    from auth_manager import AuthManager
    from cors_config import get_cors_origin
except ImportError:
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from auth_manager import AuthManager
    from cors_config import get_cors_origin


class handler(BaseHTTPRequestHandler):
    """手动升级处理器"""

    def do_OPTIONS(self):
        """处理OPTIONS请求"""
        self.send_response(200)
        request_origin = self.headers.get('Origin', '')
        allowed_origin = get_cors_origin(request_origin)
        self.send_header('Access-Control-Allow-Origin', allowed_origin)
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()

    def do_POST(self):
        """处理手动升级请求"""
        try:
            # CORS处理
            request_origin = self.headers.get('Origin', '')
            self.allowed_origin = get_cors_origin(request_origin)

            # 1. 验证Authorization
            auth_header = self.headers.get('Authorization', '')
            if not auth_header or not auth_header.startswith('Bearer '):
                self._send_error(401, "未授权")
                return

            # 2. 解析请求数据
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            out_trade_no = data.get("out_trade_no")
            user_id = data.get("user_id")
            plan_type = data.get("plan_type")

            if not all([out_trade_no, user_id, plan_type]):
                self._send_error(400, "缺少必需参数")
                return

            print(f"[MANUAL-UPGRADE] Processing manual upgrade: {out_trade_no}, user: {user_id}, plan: {plan_type}", file=sys.stderr)

            # 3. 获取AuthManager客户端
            auth_manager = AuthManager()
            if not auth_manager.client:
                self._send_error(500, "数据库连接失败")
                return

            # 4. 计算会员到期时间
            plan_durations = {
                "pro_monthly": 30,
                "pro_yearly": 365,
                "team_partner": 36500  # 100年,相当于永久
            }
            days = plan_durations.get(plan_type, 30)

            now = datetime.utcnow()
            expire_at = now + timedelta(days=days)

            # 5. 更新用户会员状态
            update_data = {
                "membership_tier": "pro" if plan_type != "team_partner" else "team_partner",
                "membership_expire_at": expire_at.isoformat(),
                "updated_at": now.isoformat()
            }

            result = auth_manager.client.table("users").update(update_data).eq("id", user_id).execute()

            if result.data:
                print(f"[MANUAL-UPGRADE] ✓ User upgraded successfully: {user_id}", file=sys.stderr)

                # 6. 返回成功响应
                self._send_success({
                    "success": True,
                    "message": "会员升级成功",
                    "membership_tier": update_data["membership_tier"],
                    "membership_expire_at": update_data["membership_expire_at"]
                })
            else:
                print(f"[MANUAL-UPGRADE] ✗ Failed to upgrade user: {user_id}", file=sys.stderr)
                self._send_error(500, "升级失败")

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
        self.send_header('Access-Control-Allow-Origin', getattr(self, 'allowed_origin', '*'))
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
