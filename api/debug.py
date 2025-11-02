from http.server import BaseHTTPRequestHandler
import json
import sys
import os
import traceback

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """诊断端点"""
        debug_info = {
            "python_version": sys.version,
            "sys_path": sys.path[:5],
            "env_vars": {
                "SUPABASE_URL": os.getenv("SUPABASE_URL", "NOT SET"),
                "SUPABASE_ANON_KEY": "SET" if os.getenv("SUPABASE_ANON_KEY") else "NOT SET"
            },
            "errors": []
        }

        # 测试导入
        try:
            import supabase
            debug_info["supabase_version"] = supabase.__version__ if hasattr(supabase, '__version__') else "unknown"
            debug_info["supabase_import"] = "SUCCESS"
        except Exception as e:
            debug_info["supabase_import"] = f"FAILED: {str(e)}"
            debug_info["errors"].append(traceback.format_exc())

        # 测试quota_manager导入
        try:
            sys.path.insert(0, os.path.dirname(__file__))
            from quota_manager import QuotaManager
            debug_info["quota_manager_import"] = "SUCCESS"
        except Exception as e:
            debug_info["quota_manager_import"] = f"FAILED: {str(e)}"
            debug_info["errors"].append(traceback.format_exc())

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(debug_info, indent=2).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
