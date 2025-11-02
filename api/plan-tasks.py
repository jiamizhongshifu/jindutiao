from http.server import BaseHTTPRequestHandler
import os
import json
import requests
import sys
import traceback

# 添加api目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from quota_manager import QuotaManager

TUZI_API_KEY = os.getenv("TUZI_API_KEY")
TUZI_BASE_URL = os.getenv("TUZI_BASE_URL", "https://api.tu-zi.com/v1")

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """处理CORS预检请求"""
        print("CORS preflight request for plan-tasks", file=sys.stderr)
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        """处理POST请求 - 任务规划"""
        print("Plan tasks function called", file=sys.stderr)

        if not TUZI_API_KEY:
            print("API key not configured", file=sys.stderr)
            self._send_json_response(500, {'error': 'API密钥未配置'})
            return

        try:
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')

            print(f"Request body: {body[:200]}", file=sys.stderr)

            if not body:
                self._send_json_response(400, {'error': '请求数据为空'})
                return

            user_data = json.loads(body)
            user_id = user_data.get('user_id', 'user_demo')
            user_tier = user_data.get('user_tier', 'free')

            # 检查并扣除配额
            quota_manager = QuotaManager()

            # 先检查配额是否足够
            quota_status = quota_manager.get_quota_status(user_id, user_tier)
            if quota_status['remaining']['daily_plan'] <= 0:
                print(f"Quota exceeded for user {user_id}", file=sys.stderr)
                self._send_json_response(429, {
                    'success': False,
                    'error': '今日配额已用尽',
                    'quota_info': quota_status
                })
                return

            # 构造API请求 - 使用OpenAI格式
            api_url = f"{TUZI_BASE_URL}/chat/completions"

            # 构造请求体(OpenAI格式)
            api_request_body = {
                "model": "gpt-5",
                "messages": [
                    {
                        "role": "system",
                        "content": """你是一个任务规划助手。用户会用自然语言描述他们的计划,你需要将其转换为结构化的任务时间表。

输出要求:
1. 必须输出纯JSON格式,不要包含任何markdown标记或额外文本
2. JSON结构: {"tasks": [{"start": "HH:MM", "end": "HH:MM", "task": "任务名称", "category": "类别"}]}
3. 时间使用24小时制,格式为HH:MM
4. category只能是: work, break, exercise, meeting, learning, other 之一
5. 确保任务时间连续且合理,不重叠

示例输出:
{"tasks": [{"start": "09:00", "end": "12:00", "task": "工作", "category": "work"}, {"start": "12:00", "end": "13:00", "task": "午休", "category": "break"}]}"""
                    },
                    {
                        "role": "user",
                        "content": user_data.get("input", "")
                    }
                ],
                "temperature": 0.3
            }

            print(f"Calling API: {api_url}", file=sys.stderr)

            # 转发请求到真实API
            response = requests.post(
                api_url,
                headers={
                    "Authorization": f"Bearer {TUZI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=api_request_body,
                timeout=60
            )

            print(f"API response status: {response.status_code}", file=sys.stderr)

            if response.status_code == 200:
                api_response = response.json()
                content = api_response['choices'][0]['message']['content'].strip()

                # 尝试从markdown代码块中提取JSON
                if content.startswith("```"):
                    lines = content.split("\n")
                    content = "\n".join(lines[1:-1]) if len(lines) > 2 else content
                    content = content.replace("```json", "").replace("```", "").strip()

                # 解析JSON
                try:
                    result = json.loads(content)
                    tasks = result.get("tasks", [])

                    if not tasks:
                        self._send_json_response(500, {
                            "success": False,
                            "error": "未生成任何任务",
                            "raw_response": content
                        })
                        return

                    # 添加颜色
                    color_palette = [
                        "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A",
                        "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E2"
                    ]
                    for i, task in enumerate(tasks):
                        task["color"] = color_palette[i % len(color_palette)]

                    # 任务生成成功，扣除配额
                    quota_result = quota_manager.use_quota(user_id, 'daily_plan', 1)

                    if quota_result.get('success'):
                        print(f"Successfully used quota for {user_id}, remaining: {quota_result['remaining']}", file=sys.stderr)
                        quota_info = quota_manager.get_quota_status(user_id, user_tier)
                    else:
                        print(f"Failed to use quota: {quota_result}", file=sys.stderr)
                        # 即使配额扣除失败，也返回任务（已经调用了API）
                        quota_info = quota_status

                    print(f"Successfully generated {len(tasks)} tasks", file=sys.stderr)

                    self._send_json_response(200, {
                        "success": True,
                        "tasks": tasks,
                        "quota_info": quota_info
                    })

                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {str(e)}", file=sys.stderr)
                    self._send_json_response(500, {
                        "success": False,
                        "error": f"JSON解析失败: {str(e)}",
                        "raw_response": content
                    })
            else:
                print(f"API request failed: {response.text[:200]}", file=sys.stderr)
                self._send_json_response(response.status_code, {
                    'error': 'API请求失败',
                    'details': response.text[:200]
                })

        except requests.exceptions.Timeout:
            print("Request timeout", file=sys.stderr)
            self._send_json_response(504, {'error': '请求超时,请稍后再试'})
        except Exception as e:
            print(f"Error in handler: {str(e)}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            self._send_json_response(500, {
                'error': '服务器内部错误',
                'details': str(e)
            })

    def _send_json_response(self, status_code, data):
        """发送JSON响应的辅助方法"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
