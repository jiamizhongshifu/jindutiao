from http.server import BaseHTTPRequestHandler
import os
import json
import requests
import sys
import traceback

# 添加api目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from quota_manager import QuotaManager
from cors_config import get_cors_origin

TUZI_API_KEY = os.getenv("TUZI_API_KEY")
TUZI_BASE_URL = os.getenv("TUZI_BASE_URL", "https://api.tu-zi.com/v1")

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """处理CORS预检请求"""
        print("CORS preflight request for plan-tasks", file=sys.stderr)
        # ✅ 安全修复: CORS源白名单验证
        request_origin = self.headers.get('Origin', '')
        allowed_origin = get_cors_origin(request_origin)

        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', allowed_origin)
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '3600')
        self.end_headers()

    def do_POST(self):
        """处理POST请求 - 任务规划"""
        print("Plan tasks function called", file=sys.stderr)

        # ✅ 安全修复: CORS源白名单验证
        request_origin = self.headers.get('Origin', '')
        self.allowed_origin = get_cors_origin(request_origin)

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

            # ✅ P1-1.6.4: 移除速率限制器,统一使用配额管理器
            # 原因: 速率限制(20次)和配额系统(free:3次, pro:无限)重复,导致混淆
            # 现在: 所有用户(免费/付费)都只受配额系统约束

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

⚠️ **关键规则 - 任务排序与跨天处理**:
6. 任务必须按照用户**一天的实际执行顺序**排列,从早晨到深夜:
   - 第一个任务: 早上起床/早餐 (如07:00开始)
   - 中间任务: 白天的工作/学习/活动
   - 最后一个任务: 睡眠 (如23:00-07:00)

7. **睡眠任务的正确写法** (跨天任务):
   ✅ 正确: {"start": "23:00", "end": "07:00", "task": "睡眠", "category": "break"}  // 晚上23点睡到次日07点
   ✅ 正确: {"start": "22:00", "end": "06:00", "task": "睡眠", "category": "break"}  // 晚上22点睡到次日06点
   ❌ 错误: {"start": "00:00", "end": "24:00", ...}  // 不要用这种格式!
   ❌ 错误: {"start": "00:00", "end": "07:00", ...}  // 不要把睡眠任务拆成两段!

8. 完整示例(注意睡眠在最后,且是跨天格式):
{"tasks": [{"start": "07:00", "end": "08:00", "task": "起床早餐", "category": "break"}, {"start": "08:00", "end": "12:00", "task": "上午工作", "category": "work"}, {"start": "12:00", "end": "13:00", "task": "午餐", "category": "break"}, {"start": "13:00", "end": "18:00", "task": "下午工作", "category": "work"}, {"start": "18:00", "end": "19:00", "task": "晚餐", "category": "break"}, {"start": "19:00", "end": "23:00", "task": "休闲娱乐", "category": "other"}, {"start": "23:00", "end": "07:00", "task": "睡眠", "category": "break"}]}"""
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
            # ✅ P1-1.6: 延长AI API请求超时时间到4分钟 (Vercel maxDuration=5分钟,留1分钟缓冲)
            response = requests.post(
                api_url,
                headers={
                    "Authorization": f"Bearer {TUZI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=api_request_body,
                timeout=240  # 4分钟 (Vercel执行限制5分钟,留1分钟缓冲处理响应)
            )

            print(f"API response status: {response.status_code}", file=sys.stderr)

            if response.status_code == 200:
                api_response = response.json()
                content = api_response['choices'][0]['message']['content'].strip()

                # ✅ P1-1.5: 提取token使用量
                token_usage = 0
                if 'usage' in api_response:
                    usage = api_response['usage']
                    # OpenAI格式: total_tokens = prompt_tokens + completion_tokens
                    token_usage = usage.get('total_tokens', 0)
                    print(f"Token usage: prompt={usage.get('prompt_tokens', 0)}, completion={usage.get('completion_tokens', 0)}, total={token_usage}", file=sys.stderr)

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
                        "quota_info": quota_info,
                        "token_usage": token_usage  # ✅ P1-1.5: 添加token使用量到响应
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
        self.send_header('Access-Control-Allow-Origin', getattr(self, 'allowed_origin', '*'))
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
