import json

def handler(req):
    """Vercel Python Serverless Function handler"""
    # 处理CORS预检请求
    if hasattr(req, 'method') and req.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': ''
        }
    
    if hasattr(req, 'method') and req.method != 'GET':
        return {
            'statusCode': 405,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    # 解析查询参数
    query_params = {}
    if hasattr(req, 'queryStringParameters') and req.queryStringParameters:
        query_params = req.queryStringParameters
    elif hasattr(req, 'args') and req.args:
        query_params = req.args
    
    user_tier = query_params.get('user_tier', 'free') if isinstance(query_params, dict) else 'free'
    
    # 根据用户等级返回不同配额
    if user_tier == 'pro':
        quota = {
            "remaining": {
                "daily_plan": 50,
                "weekly_report": 10,
                "chat": 100,
                "theme_recommend": 50,
                "theme_generate": 50
            },
            "user_tier": "pro"
        }
    else:
        quota = {
            "remaining": {
                "daily_plan": 3,
                "weekly_report": 1,
                "chat": 10,
                "theme_recommend": 5,
                "theme_generate": 3
            },
            "user_tier": "free"
        }
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(quota)
    }
