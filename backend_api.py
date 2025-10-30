# -*- coding: utf-8 -*-
"""
PyDayBar AI Backend API Server
提供任务规划、周报生成、对话查询等AI功能
"""
import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

# 设置Windows控制台编码为UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 加载环境变量
load_dotenv()
TUZI_API_KEY = os.getenv("TUZI_API_KEY")
TUZI_BASE_URL = "https://api.tu-zi.com/v1"

if not TUZI_API_KEY:
    raise ValueError("未找到TUZI_API_KEY环境变量,请在.env文件中配置")

# 初始化Flask应用
app = Flask(__name__)
CORS(app)

# 初始化兔子API客户端
tuzi_client = OpenAI(
    api_key=TUZI_API_KEY,
    base_url=TUZI_BASE_URL
)

# 用户配额管理(简化版)
USER_QUOTAS = {
    "free": {
        "daily_plan": 3,
        "weekly_report": 1,
        "chat": 10
    },
    "pro": {
        "daily_plan": 50,
        "weekly_report": 10,
        "chat": 100
    }
}

# 内存存储用户使用情况(生产环境应使用数据库)
user_usage = {}

def check_quota(user_id: str, feature: str, user_tier: str = "free") -> tuple[bool, dict]:
    """检查用户配额"""
    today = datetime.now().strftime("%Y-%m-%d")

    if user_id not in user_usage:
        user_usage[user_id] = {}

    if today not in user_usage[user_id]:
        user_usage[user_id][today] = {"daily_plan": 0, "weekly_report": 0, "chat": 0}

    usage = user_usage[user_id][today]
    quota = USER_QUOTAS[user_tier][feature]

    if usage[feature] >= quota:
        return False, {
            "quota_exceeded": True,
            "feature": feature,
            "used": usage[feature],
            "quota": quota,
            "user_tier": user_tier
        }

    usage[feature] += 1
    return True, {"used": usage[feature], "quota": quota}


@app.route('/api/plan-tasks', methods=['POST'])
def plan_tasks():
    """
    任务规划接口
    输入: {"user_id": "xxx", "input": "明天9点开会...", "user_tier": "free"}
    输出: {"tasks": [...], "quota_info": {...}}
    """
    data = request.json
    user_id = data.get("user_id", "anonymous")
    user_input = data.get("input", "")
    user_tier = data.get("user_tier", "free")

    # 检查配额
    allowed, quota_info = check_quota(user_id, "daily_plan", user_tier)
    if not allowed:
        return jsonify(quota_info), 403

    # 使用JSON输出模式(兔子API的GPT-5)
    try:
        response = tuzi_client.chat.completions.create(
            model="gpt-5",
            messages=[
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
                    "content": user_input
                }
            ],
            temperature=0.3
        )

        content = response.choices[0].message.content.strip()

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
                return jsonify({
                    "success": False,
                    "error": "未生成任何任务",
                    "raw_response": content
                }), 500

            # 添加颜色
            color_palette = [
                "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A",
                "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E2"
            ]
            for i, task in enumerate(tasks):
                task["color"] = color_palette[i % len(color_palette)]

            return jsonify({
                "success": True,
                "tasks": tasks,
                "quota_info": quota_info,
                "token_usage": response.usage.total_tokens
            })

        except json.JSONDecodeError as e:
            return jsonify({
                "success": False,
                "error": f"JSON解析失败: {str(e)}",
                "raw_response": content
            }), 500

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/generate-weekly-report', methods=['POST'])
def generate_weekly_report():
    """
    周报生成接口
    输入: {"user_id": "xxx", "statistics": {...}, "user_tier": "free"}
    输出: {"report": "markdown文本", "insights": [...]}
    """
    data = request.json
    user_id = data.get("user_id", "anonymous")
    statistics = data.get("statistics", {})
    user_tier = data.get("user_tier", "free")

    # 检查配额
    allowed, quota_info = check_quota(user_id, "weekly_report", user_tier)
    if not allowed:
        return jsonify(quota_info), 403

    # 构建统计摘要
    stats_summary = f"""
本周统计数据:
- 总任务数: {statistics.get('total_tasks', 0)}
- 工作时长: {statistics.get('work_hours', 0)}小时
- 学习时长: {statistics.get('learning_hours', 0)}小时
- 会议时长: {statistics.get('meeting_hours', 0)}小时
- 休息时长: {statistics.get('break_hours', 0)}小时
- 完成率: {statistics.get('completion_rate', 0)}%
"""

    try:
        response = tuzi_client.chat.completions.create(
            model="gpt-5",
            messages=[
                {
                    "role": "system",
                    "content": """你是一个专业的效率分析师。根据用户的周统计数据,生成一份专业的周报。

周报应包含:
1. **本周概览** - 用一段话总结本周表现
2. **时间分配分析** - 分析各类任务的时间占比
3. **亮点与成就** - 指出做得好的地方
4. **改进建议** - 提供2-3条具体可行的建议
5. **下周目标** - 建议下周的优化方向

使用Markdown格式,语气专业但友好。如果数据中有异常(如工作时间过长),请特别提醒。"""
                },
                {
                    "role": "user",
                    "content": stats_summary
                }
            ],
            temperature=0.7
        )

        report = response.choices[0].message.content

        return jsonify({
            "success": True,
            "report": report,
            "quota_info": quota_info,
            "token_usage": response.usage.total_tokens
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# 对话历史管理(内存版)
conversation_history = {}

@app.route('/api/chat-query', methods=['POST'])
def chat_query():
    """
    对话查询接口
    输入: {"user_id": "xxx", "query": "我本周最忙的一天是?", "context": {...}, "user_tier": "free"}
    输出: {"response": "...", "quota_info": {...}}
    """
    data = request.json
    user_id = data.get("user_id", "anonymous")
    query = data.get("query", "")
    context = data.get("context", {})
    user_tier = data.get("user_tier", "free")

    # 检查配额
    allowed, quota_info = check_quota(user_id, "chat", user_tier)
    if not allowed:
        return jsonify(quota_info), 403

    # 获取对话历史
    if user_id not in conversation_history:
        conversation_history[user_id] = []

    history = conversation_history[user_id]

    # 限制历史轮数
    max_history = 3 if user_tier == "free" else 10
    if len(history) > max_history * 2:  # *2 because each turn has 2 messages
        history = history[-(max_history * 2):]

    # 构建消息
    messages = [
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
        }
    ]

    # 添加历史对话
    messages.extend(history)

    # 添加当前查询(附带context)
    messages.append({
        "role": "user",
        "content": f"统计数据: {json.dumps(context, ensure_ascii=False)}\n\n问题: {query}"
    })

    try:
        response = tuzi_client.chat.completions.create(
            model="gpt-5",
            messages=messages,
            temperature=0.5,
            max_tokens=300
        )

        answer = response.choices[0].message.content

        # 保存对话历史
        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": answer})
        conversation_history[user_id] = history

        return jsonify({
            "success": True,
            "response": answer,
            "quota_info": quota_info,
            "token_usage": response.usage.total_tokens
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/quota-status', methods=['GET'])
def quota_status():
    """
    查询用户配额状态
    """
    user_id = request.args.get("user_id", "anonymous")
    user_tier = request.args.get("user_tier", "free")
    today = datetime.now().strftime("%Y-%m-%d")

    usage = {}
    if user_id in user_usage and today in user_usage[user_id]:
        usage = user_usage[user_id][today]
    else:
        usage = {"daily_plan": 0, "weekly_report": 0, "chat": 0}

    quotas = USER_QUOTAS[user_tier]

    return jsonify({
        "user_id": user_id,
        "user_tier": user_tier,
        "date": today,
        "usage": usage,
        "quotas": quotas,
        "remaining": {
            "daily_plan": quotas["daily_plan"] - usage["daily_plan"],
            "weekly_report": quotas["weekly_report"] - usage["weekly_report"],
            "chat": quotas["chat"] - usage["chat"]
        }
    })


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})


if __name__ == '__main__':
    print("="*60)
    print("PyDayBar AI Backend API Server")
    print("="*60)
    print(f"API密钥已加载: {'OK' if TUZI_API_KEY else 'FAIL'}")
    print(f"监听地址: http://localhost:5000")
    print("\n可用端点:")
    print("  POST /api/plan-tasks - 任务规划")
    print("  POST /api/generate-weekly-report - 周报生成")
    print("  POST /api/chat-query - 对话查询")
    print("  GET  /api/quota-status - 配额查询")
    print("  GET  /health - 健康检查")
    print("="*60)

    app.run(host='0.0.0.0', port=5000, debug=True)
