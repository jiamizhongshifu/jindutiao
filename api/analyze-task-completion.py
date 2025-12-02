from http.server import BaseHTTPRequestHandler
import os
import json
import requests
import sys
import traceback

# 添加api目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from quota_manager import QuotaManager
from rate_limiter import RateLimiter
from cors_config import get_cors_origin

TUZI_API_KEY = os.getenv("TUZI_API_KEY")
TUZI_BASE_URL = os.getenv("TUZI_BASE_URL", "https://api.tu-zi.com/v1")

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """处理CORS预检请求"""
        print("CORS preflight request for analyze-task-completion", file=sys.stderr)
        request_origin = self.headers.get('Origin', '')
        allowed_origin = get_cors_origin(request_origin)

        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', allowed_origin)
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '3600')
        self.end_headers()

    def do_POST(self):
        """处理POST请求 - 任务完成度深度分析"""
        print("Analyze task completion function called", file=sys.stderr)

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

            request_data = json.loads(body)
            user_id = request_data.get('user_id', 'user_demo')
            user_tier = request_data.get('user_tier', 'free')
            date = request_data.get('date')
            task_completions = request_data.get('task_completions', [])

            if not date or not task_completions:
                self._send_json_response(400, {'error': '缺少必要参数: date 或 task_completions'})
                return

            # 速率限制检查 (10次/24小时)
            limiter = RateLimiter()
            is_allowed, rate_info = limiter.check_rate_limit("analyze_completion", user_id)

            if not is_allowed:
                print(f"[ANALYZE-COMPLETION] 🚫 Rate limit exceeded for user: {user_id}", file=sys.stderr)
                self._send_json_response(429, {
                    'success': False,
                    'error': 'Daily AI analysis quota exceeded. Please try again tomorrow.',
                    'retry_after': rate_info.get("retry_after", 60)
                }, rate_info)
                return

            # 检查配额
            quota_manager = QuotaManager()
            quota_status = quota_manager.get_quota_status(user_id, user_tier)

            # 使用 daily_plan 配额（与任务规划共享）
            if quota_status['remaining']['daily_plan'] <= 0:
                print(f"Quota exceeded for user {user_id}", file=sys.stderr)
                self._send_json_response(429, {
                    'success': False,
                    'error': '今日AI配额已用尽',
                    'quota_info': quota_status
                })
                return

            # 构造分析提示词
            task_summary = self._format_task_completions(task_completions)

            api_url = f"{TUZI_BASE_URL}/chat/completions"
            api_request_body = {
                "model": "gpt-5",
                "messages": [
                    {
                        "role": "system",
                        "content": """你是一个时间管理和生产力分析专家。你将收到用户一天的任务完成情况数据,包括任务名称、计划时间、实际完成度、置信度等信息。

请分析这些数据并提供:
1. **完成度总结**: 简明扼要地总结今日任务完成情况
2. **亮点发现**: 识别做得好的地方(如高完成度任务、专注时段)
3. **改进建议**: 针对性的建议(如时间分配、专注度提升、任务优先级)
4. **时间模式**: 分析用户的高效时段和低效时段
5. **明日计划提示**: 基于今日表现给出明日规划建议

要求:
- 语气友好、鼓励性,避免批评
- 建议具体可执行
- 关注用户的进步和成长
- 使用emoji增强可读性
- 回复控制在300字以内,分段清晰"""
                    },
                    {
                        "role": "user",
                        "content": f"""日期: {date}

任务完成情况:
{task_summary}

请为我分析今日任务完成情况,提供具体的改进建议。"""
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }

            # 调用AI API (带重试和更长超时)
            print(f"Calling AI API for task completion analysis", file=sys.stderr)

            max_retries = 2
            last_error = None

            for attempt in range(max_retries):
                try:
                    api_response = requests.post(
                        api_url,
                        headers={
                            "Authorization": f"Bearer {TUZI_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        json=api_request_body,
                        timeout=60  # 增加到60秒
                    )

                    if api_response.status_code != 200:
                        error_message = api_response.text
                        print(f"AI API error (attempt {attempt+1}): {error_message}", file=sys.stderr)
                        last_error = f"API返回错误状态码: {api_response.status_code}"

                        if attempt < max_retries - 1:
                            continue  # 重试
                        else:
                            self._send_json_response(500, {
                                'success': False,
                                'error': 'AI服务暂时不可用',
                                'details': error_message[:200]
                            })
                            return

                    # 成功
                    api_result = api_response.json()
                    analysis_text = api_result['choices'][0]['message']['content']
                    break  # 成功,跳出循环

                except requests.exceptions.Timeout:
                    print(f"[ANALYZE-COMPLETION] API timeout (attempt {attempt+1}/{max_retries})", file=sys.stderr)
                    last_error = "AI服务响应超时"
                    if attempt < max_retries - 1:
                        continue  # 重试
                except requests.exceptions.RequestException as e:
                    print(f"[ANALYZE-COMPLETION] API request failed: {e}", file=sys.stderr)
                    last_error = f"网络请求失败: {str(e)}"
                    if attempt < max_retries - 1:
                        continue  # 重试
            else:
                # 所有重试都失败 - 返回降级响应
                print(f"[ANALYZE-COMPLETION] All retries failed, returning fallback response", file=sys.stderr)

                # 不扣配额,返回降级分析
                fallback_analysis = self._generate_fallback_analysis(task_completions, date)

                self._send_json_response(200, {
                    'success': True,
                    'analysis': fallback_analysis,
                    'date': date,
                    'task_count': len(task_completions),
                    'fallback': True,
                    'quota_info': quota_status,  # 不扣配额,返回原状态
                    'note': 'AI服务暂时不可用,这是基于规则的简化分析'
                })
                return

            # 扣除配额
            quota_manager.use_quota(user_id, user_tier, 'daily_plan', 1)
            updated_quota = quota_manager.get_quota_status(user_id, user_tier)

            print(f"Analysis completed successfully", file=sys.stderr)

            # 返回成功响应
            self._send_json_response(200, {
                'success': True,
                'analysis': analysis_text,
                'date': date,
                'task_count': len(task_completions),
                'quota_info': updated_quota
            })

        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}", file=sys.stderr)
            self._send_json_response(400, {
                'success': False,
                'error': '无效的JSON格式'
            })
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            self._send_json_response(500, {
                'success': False,
                'error': f'服务器内部错误: {str(e)}'
            })

    def _format_task_completions(self, tasks):
        """格式化任务完成数据为可读文本"""
        lines = []

        for i, task in enumerate(tasks, 1):
            name = task.get('task_name', '未命名任务')
            start = task.get('planned_start_time', '??:??')
            end = task.get('planned_end_time', '??:??')
            completion = task.get('completion_percentage', 0)
            confidence = task.get('confidence_level', 'unknown')

            # 置信度emoji
            confidence_emoji = {
                'high': '🟢',
                'medium': '🟡',
                'low': '🟠',
                'unknown': '⚪'
            }.get(confidence, '⚪')

            # 完成度状态
            if completion >= 80:
                status = '✅'
            elif completion >= 50:
                status = '⏳'
            else:
                status = '❌'

            lines.append(
                f"{i}. {status} {name} ({start}-{end}): {completion}% {confidence_emoji}"
            )

        return '\n'.join(lines)

    def _generate_fallback_analysis(self, tasks, date):
        """生成基于规则的降级分析(当AI服务不可用时)"""
        if not tasks:
            return "📊 今日暂无任务完成记录"

        # 统计数据
        total_tasks = len(tasks)
        high_completion = sum(1 for t in tasks if t.get('completion_percentage', 0) >= 80)
        medium_completion = sum(1 for t in tasks if 50 <= t.get('completion_percentage', 0) < 80)
        low_completion = sum(1 for t in tasks if t.get('completion_percentage', 0) < 50)

        avg_completion = sum(t.get('completion_percentage', 0) for t in tasks) / total_tasks

        # 生成分析文本
        analysis_parts = []

        # 1. 完成度总结
        analysis_parts.append(f"📊 **完成度总结** ({date})")
        analysis_parts.append(f"共完成 {total_tasks} 项任务,平均完成度 {avg_completion:.0f}%")
        analysis_parts.append(f"✅ 高完成度: {high_completion}项 | ⏳ 中等: {medium_completion}项 | ❌ 待改进: {low_completion}项")
        analysis_parts.append("")

        # 2. 亮点发现
        analysis_parts.append("✨ **亮点发现**")
        if high_completion > 0:
            analysis_parts.append(f"- 有 {high_completion} 项任务完成度超过80%,执行力不错!")
        if avg_completion >= 70:
            analysis_parts.append(f"- 整体完成度达到 {avg_completion:.0f}%,保持这个节奏!")
        else:
            analysis_parts.append("- 今天有些任务未能充分完成,不要气馁,明天再接再厉!")
        analysis_parts.append("")

        # 3. 改进建议
        analysis_parts.append("💡 **改进建议**")
        if low_completion > 0:
            analysis_parts.append(f"- 有 {low_completion} 项任务完成度较低,考虑调整任务难度或时间分配")
        if avg_completion < 50:
            analysis_parts.append("- 建议减少任务数量,专注于完成质量")
        else:
            analysis_parts.append("- 继续保持当前节奏,适当休息避免疲劳")
        analysis_parts.append("")

        # 4. 明日计划
        analysis_parts.append("🎯 **明日建议**")
        analysis_parts.append("- 基于今日经验调整任务时长")
        analysis_parts.append("- 优先处理重要且紧急的任务")
        analysis_parts.append("")

        analysis_parts.append("ℹ️ _注: AI深度分析暂时不可用,以上为基于规则的简化分析_")

        return '\n'.join(analysis_parts)

    def _send_json_response(self, status_code, data, rate_info=None):
        """发送JSON响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', self.allowed_origin)

        if rate_info:
            self.send_header('X-RateLimit-Remaining', str(rate_info.get('remaining', 0)))
            self.send_header('X-RateLimit-Reset', str(rate_info.get('reset_time', 0)))

        self.end_headers()

        response_json = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(response_json.encode('utf-8'))
