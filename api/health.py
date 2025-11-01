import json
from datetime import datetime

def handler(req):
    """Vercel Python Serverless Function handler - 简化版本用于测试"""
    # 直接返回，不检查method（因为GET请求可能没有method属性）
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "service": "PyDayBar API Proxy (Vercel)",
            "message": "Health check successful"
        })
    }
