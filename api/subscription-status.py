"""
订阅状态查询API
GET /api/subscription-status?user_id=xxx
"""
from http.server import BaseHTTPRequestHandler
import json
import sys
from urllib.parse import parse_qs, urlparse

try:
    from subscription_manager import SubscriptionManager
except ImportError:
    import os
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from subscription_manager import SubscriptionManager


class handler(BaseHTTPRequestHandler):
    """订阅状态查询处理器"""

    def do_GET(self):
        """处理GET请求"""
        try:
            # 1. 解析查询参数
            parsed_url = urlparse(self.path)
            params = parse_qs(parsed_url.query)

            user_id = params.get("user_id", [None])[0]

            if not user_id:
                self._send_error(400, "Missing user_id parameter")
                return

            print(f"[SUBSCRIPTION-STATUS] Checking status for user: {user_id}", file=sys.stderr)

            # 2. 调用订阅管理器
            sub_manager = SubscriptionManager()
            status = sub_manager.check_subscription_status(user_id)

            # 3. 返回响应
            self._send_success({
                "success": True,
                **status
            })

        except Exception as e:
            print(f"[SUBSCRIPTION-STATUS] Error: {e}", file=sys.stderr)
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
