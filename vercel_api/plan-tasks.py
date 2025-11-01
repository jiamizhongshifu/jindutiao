# Vercel Serverless Functions for PyDayBar API Proxy

# 注意：Vercel的Python函数需要使用特定的格式
# 每个API端点都是一个独立的Python文件

# api/plan-tasks.py
"""
Vercel Serverless Function: 任务规划代理
路径: /api/plan-tasks
"""
import os
import json
import requests
from datetime import datetime

# API配置（从环境变量读取）
TUZI_API_KEY = os.getenv("TUZI_API_KEY")
TUZI_BASE_URL = os.getenv("TUZI_BASE_URL", "https://api.tu-zi.com/v1")

def handler(req):
    """
    Vercel serverless function handler
    
    请求格式:
    {
        "method": "POST",
        "body": "{\"user_id\": \"xxx\", \"input\": \"...\", \"user_tier\": \"free\"}",
        "headers": {...}
    }
    """
    # 处理CORS预检请求
    if req.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': ''
        }
    
    if req.method != 'POST':
        return {
            'statusCode': 405,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    if not TUZI_API_KEY:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'API密钥未配置'})
        }
    
    try:
        # 获取用户请求数据
        if isinstance(req.body, str):
            user_data = json.loads(req.body)
        else:
            user_data = req.body
        
        if not user_data:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': '请求数据为空'})
            }
        
        # 构造API请求 - 使用OpenAI格式
        api_url = f"{TUZI_BASE_URL}/chat/completions"
        
        # 构造请求体（OpenAI格式）
        api_request_body = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个任务规划助手，帮助用户将自然语言描述转换为结构化的任务列表。"
                },
                {
                    "role": "user",
                    "content": user_data.get("input", "")
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
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
        
        if response.status_code == 200:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(response.json())
            }
        else:
            return {
                'statusCode': response.status_code,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'API请求失败',
                    'details': response.text[:200]
                })
            }
            
    except requests.exceptions.Timeout:
        return {
            'statusCode': 504,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': '请求超时，请稍后再试'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': '服务器内部错误',
                'details': str(e)
            })
        }
