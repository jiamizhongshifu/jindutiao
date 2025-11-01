from http.server import BaseHTTPRequestHandler
import json
import sys

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        print("Quota status function called", file=sys.stderr)
        
        # 解析查询参数
        from urllib.parse import urlparse, parse_qs
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        user_tier = query_params.get('user_tier', ['free'])[0]
        
        print(f"User tier: {user_tier}", file=sys.stderr)
        
        # 根据用户等级返回不同配额
        if user_tier == 'pro':
            quota = {
                "remaining": {
                    "daily_plan": 50,
                    "weekly_report": 10,
                    "chat": 100,
                    "theme_recommend": 50,
                    "theme_generate": 50
                },
                "user_tier": "pro"
            }
        else:
            quota = {
                "remaining": {
                    "daily_plan": 3,
                    "weekly_report": 1,
                    "chat": 10,
                    "theme_recommend": 5,
                    "theme_generate": 3
                },
                "user_tier": "free"
            }
        
        print(f"Returning quota: {quota}", file=sys.stderr)
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(quota).encode('utf-8'))
    
    def do_OPTIONS(self):
        print("CORS preflight request", file=sys.stderr)
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
