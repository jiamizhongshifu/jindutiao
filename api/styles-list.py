"""
样式列表查询API
GET /api/styles-list?user_id=xxx&user_tier=free&category=basic
"""
from http.server import BaseHTTPRequestHandler
import json
import sys
from urllib.parse import parse_qs, urlparse

try:
    from style_manager import StyleManager
except ImportError:
    import os
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from style_manager import StyleManager


class handler(BaseHTTPRequestHandler):
    """样式列表查询处理器"""

    def do_GET(self):
        """处理GET请求"""
        try:
            # 1. 解析查询参数
            parsed_url = urlparse(self.path)
            params = parse_qs(parsed_url.query)

            user_id = params.get("user_id", [None])[0]
            user_tier = params.get("user_tier", ["free"])[0]
            category = params.get("category", [None])[0]
            featured_only = params.get("featured", ["false"])[0].lower() == "true"

            if not user_id:
                self._send_error(400, "Missing user_id parameter")
                return

            print(f"[STYLES-LIST] Fetching styles for user {user_id}, tier: {user_tier}", file=sys.stderr)

            # 2. 调用样式管理器
            style_manager = StyleManager()
            styles = style_manager.get_available_styles(
                user_id=user_id,
                user_tier=user_tier,
                category=category,
                featured_only=featured_only
            )

            # 3. 返回响应
            self._send_success({
                "success": True,
                "styles": styles,
                "count": len(styles),
                "user_tier": user_tier
            })

            print(f"[STYLES-LIST] Returned {len(styles)} styles", file=sys.stderr)

        except Exception as e:
            print(f"[STYLES-LIST] Error: {e}", file=sys.stderr)
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
