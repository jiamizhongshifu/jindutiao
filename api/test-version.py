"""
版本测试API - 检查Vercel部署状态
"""
from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        response = {
            "success": True,
            "version": "v1.0.3-user_tier_fixed",
            "timestamp": "2025-12-04T02:15:00Z",
            "field_used": "user_tier"
        }
        self.wfile.write(json.dumps(response).encode('utf-8'))
