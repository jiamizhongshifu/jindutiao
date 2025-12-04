"""
简化测试API - 不依赖任何外部模块
"""
from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        response = {
            "success": True,
            "message": "简化测试成功"
        }
        self.wfile.write(json.dumps(response).encode('utf-8'))
