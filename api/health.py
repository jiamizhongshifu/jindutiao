import json
from datetime import datetime
import sys

def handler(req):
    """Vercel Python Serverless Function handler"""
    # 添加调试日志
    print("Health check function called", file=sys.stderr)
    print(f"Request object type: {type(req)}", file=sys.stderr)
    print(f"Request object: {req}", file=sys.stderr)
    
    try:
        # 尝试获取method（如果存在）
        if isinstance(req, dict):
            method = req.get('method', 'GET')
        elif hasattr(req, 'method'):
            method = req.method
        else:
            method = 'GET'
        
        print(f"Method: {method}", file=sys.stderr)
        
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
        
        # 返回健康检查响应
        response = {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "service": "PyDayBar API Proxy (Vercel)",
            "message": "Health check successful"
        }
        
        print(f"Returning response: {response}", file=sys.stderr)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response)
        }
    except Exception as e:
        print(f"Error in handler: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                "error": "Internal server error",
                "details": str(e)
            })
        }
