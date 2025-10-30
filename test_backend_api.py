# -*- coding: utf-8 -*-
"""
测试Backend API的功能
"""
import sys
import io
import time
import json
import requests

# 设置Windows控制台编码为UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

BASE_URL = "http://localhost:5000"

print("="*60)
print("测试Backend API")
print("="*60)

# 等待服务器启动
print("\n等待服务器启动...")
for i in range(10):
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print("[OK] 服务器已就绪")
            break
    except Exception:
        time.sleep(1)
        print(f"  尝试连接中... ({i+1}/10)")
else:
    print("[X] 服务器启动失败,请手动运行: python backend_api.py")
    exit(1)

# 测试1: 任务规划
print("\n" + "="*60)
print("测试 1: 任务规划API")
print("="*60)
try:
    response = requests.post(
        f"{BASE_URL}/api/plan-tasks",
        json={
            "user_id": "test_user",
            "input": "明天早上8点起床,9点开始工作到12点,中午休息1小时,下午1点到5点继续工作,晚上6点健身1小时",
            "user_tier": "free"
        },
        timeout=30
    )

    if response.status_code == 200:
        data = response.json()
        print("[OK] 任务规划成功")
        print(f"  生成任务数: {len(data.get('tasks', []))}")
        print(f"  Token使用: {data.get('token_usage', 0)}")
        print(f"  配额状态: {data.get('quota_info', {})}")
        print("\n生成的任务:")
        for task in data.get('tasks', []):
            print(f"  {task['start']}-{task['end']}: {task['task']} [{task['category']}]")
    else:
        print(f"[X] 失败: HTTP {response.status_code}")
        print(f"  {response.text}")
except Exception as e:
    print(f"[X] 错误: {e}")

# 测试2: 周报生成
print("\n" + "="*60)
print("测试 2: 周报生成API")
print("="*60)
try:
    statistics = {
        "total_tasks": 35,
        "work_hours": 40,
        "learning_hours": 8,
        "meeting_hours": 10,
        "break_hours": 5,
        "completion_rate": 85
    }

    response = requests.post(
        f"{BASE_URL}/api/generate-weekly-report",
        json={
            "user_id": "test_user",
            "statistics": statistics,
            "user_tier": "free"
        },
        timeout=30
    )

    if response.status_code == 200:
        data = response.json()
        print("[OK] 周报生成成功")
        print(f"  Token使用: {data.get('token_usage', 0)}")
        print("\n周报内容:")
        print(data.get('report', ''))
    else:
        print(f"[X] 失败: HTTP {response.status_code}")
        print(f"  {response.text}")
except Exception as e:
    print(f"[X] 错误: {e}")

# 测试3: 对话查询
print("\n" + "="*60)
print("测试 3: 对话查询API")
print("="*60)
try:
    context = {
        "daily_stats": {
            "2025-10-29": {"work_hours": 8, "tasks": 5},
            "2025-10-30": {"work_hours": 10, "tasks": 7}
        }
    }

    response = requests.post(
        f"{BASE_URL}/api/chat-query",
        json={
            "user_id": "test_user",
            "query": "我哪天工作时间更长?",
            "context": context,
            "user_tier": "free"
        },
        timeout=30
    )

    if response.status_code == 200:
        data = response.json()
        print("[OK] 对话查询成功")
        print(f"  Token使用: {data.get('token_usage', 0)}")
        print(f"\n回答: {data.get('response', '')}")
    else:
        print(f"[X] 失败: HTTP {response.status_code}")
        print(f"  {response.text}")
except Exception as e:
    print(f"[X] 错误: {e}")

# 测试4: 配额查询
print("\n" + "="*60)
print("测试 4: 配额查询API")
print("="*60)
try:
    response = requests.get(
        f"{BASE_URL}/api/quota-status",
        params={
            "user_id": "test_user",
            "user_tier": "free"
        },
        timeout=10
    )

    if response.status_code == 200:
        data = response.json()
        print("[OK] 配额查询成功")
        print(f"  用户: {data.get('user_id')}")
        print(f"  等级: {data.get('user_tier')}")
        print(f"  日期: {data.get('date')}")
        print(f"\n已使用:")
        for key, value in data.get('usage', {}).items():
            print(f"    {key}: {value}")
        print(f"\n剩余配额:")
        for key, value in data.get('remaining', {}).items():
            print(f"    {key}: {value}")
    else:
        print(f"[X] 失败: HTTP {response.status_code}")
        print(f"  {response.text}")
except Exception as e:
    print(f"[X] 错误: {e}")

print("\n" + "="*60)
print("[SUCCESS] 所有测试完成!")
print("="*60)
