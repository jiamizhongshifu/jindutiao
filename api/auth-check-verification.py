"""
检查邮箱验证状态
POST /api/auth-check-verification

用于前端轮询检查用户是否已经点击了Supabase发送的验证邮件链接
"""
from http.server import BaseHTTPRequestHandler
import json
import sys
import os

try:
    from auth_manager import AuthManager
except ImportError:
    sys.path.insert(0, os.path.dirname(__file__))
    from auth_manager import AuthManager


class handler(BaseHTTPRequestHandler):
    """邮箱验证状态检查处理器"""

    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        """检查邮箱验证状态"""
        try:
            # 1. 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self._send_error(400, "Empty request body")
                return

            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)

            # 2. 验证参数
            user_id = data.get("user_id")
            email = data.get("email")

            if not user_id and not email:
                self._send_error(400, "Missing user_id or email")
                return

            print(f"[AUTH-CHECK-VERIFICATION] Checking verification status for: {email or user_id}", file=sys.stderr)

            # 3. 使用 auth_manager 检查验证状态
            auth_manager = AuthManager()
            result = auth_manager.check_email_verification(user_id=user_id, email=email)

            if result.get("success"):
                self._send_success(result)
            else:
                self._send_error(400, result.get("error", "Check failed"))

        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
        except Exception as e:
            print(f"[AUTH-CHECK-VERIFICATION] Error: {e}", file=sys.stderr)
            self._send_error(500, f"Internal server error: {str(e)}")

    def _send_success(self, data: dict):
        """发送成功响应"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        response = {"success": True, **data}
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def _send_error(self, code: int, message: str):
        """发送错误响应"""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        error_response = {
            "success": False,
            "error": message
        }
        self.wfile.write(json.dumps(error_response).encode('utf-8'))
