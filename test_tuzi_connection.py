# -*- coding: utf-8 -*-
"""
兔子API连接测试脚本
测试基本API调用和Function Calling功能
"""
import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

# 设置Windows控制台编码为UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 加载环境变量
load_dotenv()
TUZI_API_KEY = os.getenv("TUZI_API_KEY")

if not TUZI_API_KEY:
    print("[X] 错误: 未在.env文件中找到TUZI_API_KEY")
    print("请在.env文件中添加: TUZI_API_KEY=your-api-key-here")
    exit(1)

print(f"[OK] API密钥已加载 (长度: {len(TUZI_API_KEY)})")

# 初始化客户端
client = OpenAI(
    api_key=TUZI_API_KEY,
    base_url="https://api.tu-zi.com/v1"
)

print("\n" + "="*60)
print("测试 1: 基础文本对话")
print("="*60)
try:
    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "user", "content": "你好,请用一句话介绍你自己"}
        ]
    )
    print(f"[OK] 响应: {response.choices[0].message.content}")
    print(f"  模型: {response.model}")
    print(f"  Token用量: {response.usage.total_tokens}")
except Exception as e:
    print(f"[X] 错误: {e}")
    exit(1)

print("\n" + "="*60)
print("测试 2: Function Calling (任务规划)")
print("="*60)
try:
    tools = [{
        "type": "function",
        "function": {
            "name": "generate_task_schedule",
            "description": "生成结构化的任务时间表",
            "parameters": {
                "type": "object",
                "properties": {
                    "tasks": {
                        "type": "array",
                        "description": "任务列表",
                        "items": {
                            "type": "object",
                            "properties": {
                                "start": {"type": "string", "description": "开始时间,格式HH:MM"},
                                "end": {"type": "string", "description": "结束时间,格式HH:MM"},
                                "task": {"type": "string", "description": "任务名称"},
                                "category": {
                                    "type": "string",
                                    "enum": ["work", "break", "exercise", "meeting", "learning", "other"],
                                    "description": "任务类别"
                                }
                            },
                            "required": ["start", "end", "task", "category"]
                        }
                    }
                },
                "required": ["tasks"]
            }
        }
    }]

    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {
                "role": "system",
                "content": "你是一个任务规划助手,帮助用户将自然语言描述转换为结构化的任务时间表。"
            },
            {
                "role": "user",
                "content": "明天9点开会1小时,然后写代码到下午5点,中午12点休息1小时"
            }
        ],
        tools=tools,
        tool_choice="auto",
        temperature=0.3
    )

    choice = response.choices[0]
    message = choice.message
    print(f"[OK] 模型响应类型: {choice.finish_reason}")

    if message.tool_calls:
        import json
        tool_call = message.tool_calls[0]
        print(f"  调用函数: {tool_call.function.name}")
        args = json.loads(tool_call.function.arguments)
        print(f"  生成的任务:")
        for task in args.get("tasks", []):
            print(f"    - {task['start']}-{task['end']}: {task['task']} ({task['category']})")
    else:
        print(f"  文本响应: {message.content}")

    print(f"  Token用量: {response.usage.total_tokens}")
except Exception as e:
    print(f"[X] 错误: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "="*60)
print("测试 3: 联网搜索功能")
print("="*60)
try:
    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "user", "content": "今天是几号?现在的时间是?"}
        ]
    )
    print(f"[OK] 响应: {response.choices[0].message.content}")
    print(f"  Token用量: {response.usage.total_tokens}")
except Exception as e:
    print(f"[X] 错误: {e}")
    exit(1)

print("\n" + "="*60)
print("[SUCCESS] 所有测试通过!")
print("="*60)
print("\n下一步:")
print("1. 启动Flask后端服务器: python backend_api.py")
print("2. 测试后端API端点: python test_backend_api.py")
print("3. 集成到config_gui.py中测试完整流程")
