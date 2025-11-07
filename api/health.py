from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime
import sys

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        print("Health check function called", file=sys.stderr)
        
        response_data = {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "service": "GaiYa API Service (Vercel)",
            "message": "Health check successful"
        }
        
        print(f"Returning response: {response_data}", file=sys.stderr)
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode('utf-8'))
    
    def do_OPTIONS(self):
        print("CORS preflight request", file=sys.stderr)
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
