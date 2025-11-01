from http.server import BaseHTTPRequestHandler
import os
import json
import requests
from datetime import datetime

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
            
            description = user_data.get("description", "")
            
            prompt = f"""你是一个专业的UI设计师。根据用户的描述生成完整的主题配色方案。

用户描述："{description}"

请生成包含以下字段的主题配置：
- background_color: 背景色（十六进制）
- background_opacity: 背景透明度（0-255）
- task_colors: 任务配色数组（4-6种颜色）
- marker_color: 时间标记颜色
- text_color: 文字颜色
- accent_color: 强调色

返回JSON格式，包含：
- theme_id: 主题ID（格式：ai_generated_YYYYMMDD_HHMMSS）
- name: 主题名称（基于描述生成）
- config: 主题配置对象
- description: 主题描述

输出必须是纯JSON格式，不要包含任何markdown标记或额外文本。"""
            
            api_url = f"{TUZI_BASE_URL}/chat/completions"
            api_request_body = {
                "model": "gpt-5",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的UI设计师，擅长根据自然语言描述生成配色方案。输出必须是纯JSON格式，不要包含任何markdown标记或额外文本。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7
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
                content = api_response['choices'][0]['message']['content'].strip()
                
                # 尝试从markdown代码块中提取JSON
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                try:
                    result = json.loads(content)
                    
                    # 确保有theme_id
                    if 'theme_id' not in result:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        result['theme_id'] = f"ai_generated_{timestamp}"
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "success": True,
                        "theme": result,
                        "quota_info": {
                            "remaining": {"theme_generate": 2},
                            "user_tier": user_data.get("user_tier", "free")
                        }
                    }).encode('utf-8'))
                    return
                except json.JSONDecodeError as e:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'success': False,
                        'error': f'JSON解析失败: {str(e)}',
                        'raw_response': content[:200]
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
