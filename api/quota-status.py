from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# 添加api目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from quota_manager import QuotaManager
from cors_config import get_cors_origin

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        print("Quota status function called", file=sys.stderr)

        # ✅ 安全修复: CORS源白名单验证
        request_origin = self.headers.get('Origin', '')
        self.allowed_origin = get_cors_origin(request_origin)

        # 解析查询参数
        from urllib.parse import urlparse, parse_qs
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)

        user_id = query_params.get('user_id', ['user_demo'])[0]
        user_tier = query_params.get('user_tier', ['free'])[0]

        print(f"User: {user_id}, Tier: {user_tier}", file=sys.stderr)

        # 使用QuotaManager获取真实配额
        try:
            quota_manager = QuotaManager()
            quota_data = quota_manager.get_quota_status(user_id, user_tier)

            print(f"Returning quota: {quota_data}", file=sys.stderr)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', getattr(self, 'allowed_origin', '*'))
            self.end_headers()
            self.wfile.write(json.dumps(quota_data).encode('utf-8'))

        except Exception as e:
            print(f"Error getting quota: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)

            # 返回降级配额
            fallback_quota = {
                "remaining": {
                    "daily_plan": 3 if user_tier == "free" else 50,
                    "weekly_report": 1 if user_tier == "free" else 10,
                    "chat": 10 if user_tier == "free" else 100,
                    "theme_recommend": 5 if user_tier == "free" else 50,
                    "theme_generate": 3 if user_tier == "free" else 50
                },
                "user_tier": user_tier,
                "error": "Failed to get quota from database, using fallback"
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', getattr(self, 'allowed_origin', '*'))
            self.end_headers()
            self.wfile.write(json.dumps(fallback_quota).encode('utf-8'))

    def do_OPTIONS(self):
        print("CORS preflight request", file=sys.stderr)
        # ✅ 安全修复: CORS源白名单验证
        request_origin = self.headers.get('Origin', '')
        allowed_origin = get_cors_origin(request_origin)

        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', allowed_origin)
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '3600')
        self.end_headers()
