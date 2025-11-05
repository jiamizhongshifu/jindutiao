"""
用户登出API
POST /api/auth-signout
Authorization: Bearer <access_token>
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
    """登出API处理器"""

    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_POST(self):
        """处理登出请求"""
        try:
            # 1. 读取Authorization Header
            auth_header = self.headers.get('Authorization', '')

            if not auth_header.startswith('Bearer '):
                self._send_error(401, "Missing or invalid Authorization header")
                return

            access_token = auth_header.replace('Bearer ', '')

            print(f"[AUTH-SIGNOUT] Signout request received", file=sys.stderr)

            # 2. 调用认证管理器
            auth_manager = AuthManager()
            result = auth_manager.sign_out(access_token)

            # 3. 返回响应
            if result["success"]:
                self._send_success({
                    "success": True,
                    "message": "Signed out successfully"
                })
                print(f"[AUTH-SIGNOUT] Signout successful", file=sys.stderr)
            else:
                self._send_error(400, result.get("error", "Signout failed"))

        except Exception as e:
            print(f"[AUTH-SIGNOUT] Error: {e}", file=sys.stderr)
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
