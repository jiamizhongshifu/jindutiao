import os
import json
import requests

TUZI_API_KEY = os.getenv("TUZI_API_KEY")
TUZI_BASE_URL = os.getenv("TUZI_BASE_URL", "https://api.tu-zi.com/v1")

def handler(req):
    """Vercel Python Serverless Function handler"""
    # 处理CORS预检请求
    if hasattr(req, 'method') and req.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': ''
        }
    
    if hasattr(req, 'method') and req.method != 'POST':
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
            user_data = req.body or {}
        
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
                    return {
                        'statusCode': 500,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        },
                        'body': json.dumps({
                            "success": False,
                            "error": "未生成任何任务",
                            "raw_response": content
                        })
                    }
                
                # 添加颜色
                color_palette = [
                    "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A",
                    "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E2"
                ]
                for i, task in enumerate(tasks):
                    task["color"] = color_palette[i % len(color_palette)]
                
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        "success": True,
                        "tasks": tasks,
                        "quota_info": {
                            "remaining": {"daily_plan": 2},
                            "user_tier": user_data.get("user_tier", "free")
                        }
                    })
                }
                
            except json.JSONDecodeError as e:
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        "success": False,
                        "error": f"JSON解析失败: {str(e)}",
                        "raw_response": content
                    })
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
