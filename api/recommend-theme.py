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
            
            tasks = user_data.get("tasks", [])
            task_analysis = user_data.get("task_analysis", {})
            
            task_types = task_analysis.get('task_types', {})
            keywords = task_analysis.get('keywords', [])
            
            prompt = f"""你是一个专业的UI配色专家。根据以下任务数据，推荐3-5种适合的配色方案。

任务数据：
- 任务列表: {json.dumps(tasks, ensure_ascii=False)}
- 任务类型分布: {json.dumps(task_types, ensure_ascii=False)}
- 任务关键词: {', '.join(keywords[:10])}

请根据任务名称的语义特点，为每种推荐方案提供：
1. 主题名称（如"商务专业"）
2. 背景色、任务配色（4-6种颜色，需考虑任务语义）
   - 工作类任务：蓝色、绿色等专业色
   - 休息类任务：橙色、黄色等温暖色
   - 学习类任务：紫色、靛蓝等专注色
   - 运动类任务：红色、橙色等活力色
3. 推荐理由（2-3句话，说明为什么适合这些任务类型）

返回JSON格式，包含recommendations数组，每个推荐包含：
- name: 主题名称
- theme_id: 主题ID（格式：recommended_1, recommended_2...）
- config: 主题配置对象
  - background_color: 背景色（十六进制）
  - background_opacity: 背景透明度（0-255）
  - task_colors: 任务配色数组（4-6种颜色）
  - marker_color: 时间标记颜色
  - text_color: 文字颜色
  - accent_color: 强调色
- reason: 推荐理由（2-3句话）

输出必须是纯JSON格式，不要包含任何markdown标记或额外文本。"""
            
            api_url = f"{TUZI_BASE_URL}/chat/completions"
            api_request_body = {
                "model": "gpt-5",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的UI配色专家，擅长根据任务类型推荐合适的配色方案。输出必须是纯JSON格式，不要包含任何markdown标记或额外文本。"
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
                    recommendations = result.get('recommendations', [])
                    
                    # 确保每个推荐都有完整的配置
                    for rec in recommendations:
                        if 'config' not in rec:
                            rec['config'] = {}
                        if 'theme_id' not in rec:
                            rec['theme_id'] = f"recommended_{recommendations.index(rec) + 1}"
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "success": True,
                        "recommendations": recommendations,
                        "quota_info": {
                            "remaining": {"theme_recommend": 4},
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
