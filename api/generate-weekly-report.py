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
        
        statistics = user_data.get("statistics", {})
        stats_summary = f"""
本周统计数据:
- 总任务数: {statistics.get('total_tasks', 0)}
- 工作时长: {statistics.get('work_hours', 0)}小时
- 学习时长: {statistics.get('learning_hours', 0)}小时
- 会议时长: {statistics.get('meeting_hours', 0)}小时
- 休息时长: {statistics.get('break_hours', 0)}小时
- 完成率: {statistics.get('completion_rate', 0)}%
"""
        
        api_url = f"{TUZI_BASE_URL}/chat/completions"
        api_request_body = {
            "model": "gpt-5",
            "messages": [
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
            "temperature": 0.7
        }
        
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
            report = api_response['choices'][0]['message']['content']
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    "report": report,
                    "quota_info": {
                        "remaining": {"weekly_report": 0},
                        "user_tier": user_data.get("user_tier", "free")
                    }
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
