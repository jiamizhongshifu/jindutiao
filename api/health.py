from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime
import sys
import os

# 添加api目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from cors_config import get_cors_origin

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        print("Health check function called", file=sys.stderr)

        # ✅ 安全修复: CORS源白名单验证
        request_origin = self.headers.get('Origin', '')
        self.allowed_origin = get_cors_origin(request_origin)

        response_data = {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "service": "GaiYa API Service (Vercel)",
            "message": "Health check successful"
        }
        
        print(f"Returning response: {response_data}", file=sys.stderr)
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', getattr(self, 'allowed_origin', '*'))
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode('utf-8'))
    
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
