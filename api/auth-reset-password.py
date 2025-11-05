"""
请求重置密码API
POST /api/auth-reset-password
Body: {"email": "user@example.com"}
"""
from http.server import BaseHTTPRequestHandler
import json
import sys

try:
    from auth_manager import AuthManager
except ImportError:
    import os
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from auth_manager import AuthManager


class handler(BaseHTTPRequestHandler):
    """重置密码处理器"""

    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        """处理重置密码请求"""
        try:
            # 1. 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self._send_error(400, "Empty request body")
                return

            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)

            # 2. 验证参数
            email = data.get("email")

            if not email:
                self._send_error(400, "Missing email")
                return

            print(f"[AUTH-RESET-PASSWORD] Password reset requested for: {email}", file=sys.stderr)

            # 3. 调用认证管理器
            auth_manager = AuthManager()
            result = auth_manager.request_password_reset(email)

            # 4. 返回响应（为了安全，即使邮箱不存在也返回成功）
            self._send_success({
                "success": True,
                "message": "If the email exists, a password reset link has been sent"
            })

            print(f"[AUTH-RESET-PASSWORD] Password reset email sent to: {email}", file=sys.stderr)

        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
        except Exception as e:
            print(f"[AUTH-RESET-PASSWORD] Error: {e}", file=sys.stderr)
            self._send_error(500, f"Internal server error: {str(e)}")

    def _send_success(self, data: dict):
        """发送成功响应"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

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
