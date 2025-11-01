import json
from datetime import datetime

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
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "service": "PyDayBar API Proxy (Vercel)"
        })
    }
