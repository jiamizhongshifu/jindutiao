from http.server import BaseHTTPRequestHandler
import json
import os
import requests
import sys
import traceback

TUZI_API_KEY = os.getenv("TUZI_API_KEY")
TUZI_BASE_URL = os.getenv("TUZI_BASE_URL", "https://api.tu-zi.com/v1")


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """处理CORS预检请求"""
        print("CORS preflight request for recommend-theme", file=sys.stderr)
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        """处理POST请求 - 主题推荐"""
        print("Recommend theme function called", file=sys.stderr)

        if not TUZI_API_KEY:
            print("API key not configured", file=sys.stderr)
            self._send_json_response(500, {"error": "API密钥未配置"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8") if content_length else ""
            print(f"Request body: {body[:200]}", file=sys.stderr)

            user_data = json.loads(body) if body else {}
            tasks = user_data.get("tasks", [])
            task_analysis = user_data.get("task_analysis", {})

            task_types = task_analysis.get("task_types", {})
            keywords = task_analysis.get("keywords", [])

            prompt = (
                "你是一个专业的UI配色专家。根据以下任务数据，推荐3-5种适合的配色方案。\n\n"
                f"任务列表: {json.dumps(tasks, ensure_ascii=False)}\n"
                f"任务类型分布: {json.dumps(task_types, ensure_ascii=False)}\n"
                f"任务关键词: {', '.join(keywords[:10])}\n\n"
                "请根据任务名称的语义特点，为每种推荐方案提供:\n"
                "1. 主题名称（如\"商务专业\"）\n"
                "2. 背景色、任务配色（4-6种颜色，需考虑任务语义）\n"
                "   - 工作类任务：蓝色、绿色等专业色\n"
                "   - 休息类任务：橙色、黄色等温暖色\n"
                "   - 学习类任务：紫色、靛蓝等专注色\n"
                "   - 运动类任务：红色、橙色等活力色\n"
                "3. 推荐理由，2-3句话说明适用场景\n\n"
                "返回JSON格式，包含recommendations数组，每个推荐包含:\n"
                "- name: 主题名称\n"
                "- theme_id: 主题ID（格式：recommended_1, recommended_2...）\n"
                "- config: 主题配置对象\n"
                "  - background_color: 背景色（十六进制）\n"
                "  - background_opacity: 背景透明度（0-255）\n"
                "  - task_colors: 任务配色数组（4-6种颜色）\n"
                "  - marker_color: 时间标记颜色\n"
                "  - text_color: 文字颜色\n"
                "  - accent_color: 强调色\n"
                "- reason: 推荐理由，2-3句话\n\n"
                "输出必须是纯JSON格式，不要包含任何markdown标记或额外文本。"
            )

            api_url = f"{TUZI_BASE_URL}/chat/completions"
            api_request_body = {
                "model": "gpt-5",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的UI配色专家，擅长根据任务类型推荐合适的配色方案。输出必须是纯JSON格式，不要包含任何markdown标记或额外文本。",
                    },
                    {
                        "role": "user",
                        "content": prompt,
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
                content = api_response["choices"][0]["message"]["content"].strip()

                if "```" in content:
                    parts = content.split("```")
                    if len(parts) >= 3:
                        content = parts[1].replace("json", "").strip()

                try:
                    result = json.loads(content)
                    recommendations = result.get("recommendations", [])

                    for idx, rec in enumerate(recommendations, start=1):
                        rec.setdefault("theme_id", f"recommended_{idx}")
                        rec.setdefault("config", {})

                    print(f"Generated {len(recommendations)} recommendations", file=sys.stderr)

                    self._send_json_response(
                        200,
                        {
                            "success": True,
                            "recommendations": recommendations,
                            "quota_info": {
                                "remaining": {"theme_recommend": 4},
                                "user_tier": user_data.get("user_tier", "free"),
                            },
                        },
                    )
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {str(e)}", file=sys.stderr)
                    self._send_json_response(
                        500,
                        {
                            "success": False,
                            "error": f"JSON解析失败: {str(e)}",
                            "raw_response": content[:200],
                        },
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

    def _send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))
