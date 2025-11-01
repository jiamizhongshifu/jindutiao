from http.server import BaseHTTPRequestHandler
import os
import json
import requests

TUZI_API_KEY = os.getenv("TUZI_API_KEY")
TUZI_BASE_URL = os.getenv("TUZI_BASE_URL", "https://api.tu-zi.com/v1")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if not TUZI_API_KEY:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "API密钥未配置"}).encode('utf-8'))
            return
        
        try:
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            user_data = json.loads(post_data.decode('utf-8'))
            
            query = user_data.get("query", "")
            context = user_data.get("context", {})
            
            api_url = f"{TUZI_BASE_URL}/chat/completions"
            api_request_body = {
                "model": "gpt-5",
                "messages": [
                    {
                        "role": "system",
                        "content": """你是PyDayBar的智能助手,帮助用户分析他们的时间使用情况。

用户可能会问:
- 统计查询: "我本周最忙的一天是?" "我哪天休息最多?"
- 趋势分析: "我的工作时间是否在增加?"
- 建议请求: "如何提高效率?"

回答要:
- 基于提供的数据context
- 简洁明了,1-3句话
- 如果数据不足,说明需要更多数据"""
                    },
                    {
                        "role": "user",
                        "content": f"统计数据: {json.dumps(context, ensure_ascii=False)}\n\n问题: {query}"
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            response = requests.post(
                api_url,
                headers={
                    "Authorization": f"Bearer {TUZI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=api_request_body,
                timeout=60
            )
            
            if response.status_code == 200:
                api_response = response.json()
                answer = api_response['choices'][0]['message']['content']
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "response": answer,
                    "quota_info": {
                        "remaining": {"chat": 9},
                        "user_tier": user_data.get("user_tier", "free")
                    }
                }).encode('utf-8'))
                return
            else:
                self.send_response(response.status_code)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'API请求失败',
                    'details': response.text[:200]
                }).encode('utf-8'))
                return
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': '服务器内部错误',
                'details': str(e)
            }).encode('utf-8'))
            return
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        return
