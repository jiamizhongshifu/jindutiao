from http.server import BaseHTTPRequestHandler
import json
import os
import requests
import sys
import traceback

# 添加api目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from rate_limiter import RateLimiter
from cors_config import get_cors_origin

TUZI_API_KEY = os.getenv("TUZI_API_KEY")
TUZI_BASE_URL = os.getenv("TUZI_BASE_URL", "https://api.tu-zi.com/v1")


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """处理CORS预检请求"""
        print("CORS preflight request for generate-weekly-report", file=sys.stderr)
        # ✅ 安全修复: CORS源白名单验证
        request_origin = self.headers.get('Origin', '')
        allowed_origin = get_cors_origin(request_origin)

        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", allowed_origin)
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "3600")
        self.end_headers()

    def do_POST(self):
        """处理POST请求 - 周报生成"""
        print("Generate weekly report function called", file=sys.stderr)

        # ✅ 安全修复: CORS源白名单验证
        request_origin = self.headers.get('Origin', '')
        self.allowed_origin = get_cors_origin(request_origin)

        if not TUZI_API_KEY:
            print("API key not configured", file=sys.stderr)
            self._send_json_response(500, {"error": "API密钥未配置"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8") if content_length else ""
            print(f"Request body: {body[:200]}", file=sys.stderr)

            user_data = json.loads(body) if body else {}
            user_id = user_data.get("user_id", "user_demo")
            statistics = user_data.get("statistics", {})

            # ✅ 安全修复: 速率限制检查（防止AI资源滥用）
            limiter = RateLimiter()

            # 检查速率限制 (10次/24小时，基于user_id)
            is_allowed, rate_info = limiter.check_rate_limit("generate_weekly_report", user_id)

            if not is_allowed:
                # 返回429 Too Many Requests
                print(f"[WEEKLY-REPORT] 🚫 Rate limit exceeded for user: {user_id}", file=sys.stderr)
                self._send_json_response(429, {
                    "success": False,
                    "error": "Daily report generation quota exceeded. Please try again tomorrow.",
                    "retry_after": rate_info.get("retry_after", 60)
                }, rate_info)
                return

            stats_summary = (
                "本周统计数据:\n"
                f"- 总任务数: {statistics.get('total_tasks', 0)}\n"
                f"- 工作时长: {statistics.get('work_hours', 0)}小时\n"
                f"- 学习时长: {statistics.get('learning_hours', 0)}小时\n"
                f"- 会议时长: {statistics.get('meeting_hours', 0)}小时\n"
                f"- 休息时长: {statistics.get('break_hours', 0)}小时\n"
                f"- 完成率: {statistics.get('completion_rate', 0)}%\n"
            )

            api_url = f"{TUZI_BASE_URL}/chat/completions"
            api_request_body = {
                "model": "gpt-5",
                "messages": [
                    {
                        "role": "system",
                        "content": """你是一个专业的效率分析师。根据用户的周统计数据生成一份专业的周报。

周报应包含:
1. **本周概览** - 用一段话总结本周表现
2. **时间分配分析** - 分析各类任务的时间占比
3. **亮点与成就** - 指出做得好的地方
4. **改进建议** - 提供2-3条具体可行的建议
5. **下周目标** - 建议下周的优化方向

使用Markdown格式,语气专业但友好。如果数据中有异常,如工作时间过长,请特别提醒。""",
                    },
                    {
                        "role": "user",
                        "content": stats_summary,
                    },
                ],
                "temperature": 0.7,
            }

            response = requests.post(
                api_url,
                headers={
                    "Authorization": f"Bearer {TUZI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=api_request_body,
                timeout=60,
            )

            print(f"API response status: {response.status_code}", file=sys.stderr)

            if response.status_code == 200:
                api_response = response.json()
                report = api_response["choices"][0]["message"]["content"]

                self._send_json_response(
                    200,
                    {
                        "report": report,
                        "quota_info": {
                            "remaining": {"weekly_report": 0},
                            "user_tier": user_data.get("user_tier", "free"),
                        },
                    },
                    rate_info
                )
            else:
                print(f"API request failed: {response.text[:200]}", file=sys.stderr)
                self._send_json_response(
                    response.status_code,
                    {
                        "error": "API请求失败",
                        "details": response.text[:200],
                    },
                )

        except json.JSONDecodeError as e:
            print(f"JSON decode error: {str(e)}", file=sys.stderr)
            self._send_json_response(400, {"error": f"请求数据格式错误: {str(e)}"})
        except requests.exceptions.Timeout:
            print("Request timeout", file=sys.stderr)
            self._send_json_response(504, {"error": "请求超时,请稍后再试"})
        except Exception as e:
            print(f"Error in handler: {str(e)}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            self._send_json_response(
                500,
                {
                    "error": "服务器内部错误",
                    "details": str(e),
                },
            )

    def _send_json_response(self, status_code, data, rate_info: dict = None):
        """发送JSON响应（包含速率限制响应头）"""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", getattr(self, 'allowed_origin', '*'))

        # ✅ 添加速率限制响应头
        if rate_info:
            self.send_header('X-RateLimit-Limit', str(rate_info.get("total", 0)))
            self.send_header('X-RateLimit-Remaining', str(rate_info.get("remaining", 0)))
            self.send_header('X-RateLimit-Reset', rate_info.get("reset_at", ""))
            if status_code == 429:
                self.send_header('Retry-After', str(rate_info.get("retry_after", 60)))

        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))
