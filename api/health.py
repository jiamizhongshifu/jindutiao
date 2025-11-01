import json
from datetime import datetime

def handler(req):
    """Vercel Python Serverless Function handler"""
    # Vercel Python函数中，req是一个类似字典的对象
    # 但也可以有属性访问方式
    try:
        method = req.method if hasattr(req, 'method') else req.get('method', 'GET')
    except:
        method = 'GET'
    
    # 处理CORS预检请求
    if method == 'OPTIONS':
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
