"""
查询支付订单状态API
GET /api/payment-query?out_trade_no=xxx
"""
from http.server import BaseHTTPRequestHandler
import json
import sys
from urllib.parse import parse_qs, urlparse

try:
    from zpay_manager import ZPayManager
except ImportError:
    import os
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from zpay_manager import ZPayManager


class handler(BaseHTTPRequestHandler):
    """查询订单处理器"""

    def do_GET(self):
        """处理查询请求"""
        try:
            # 1. 解析查询参数
            parsed_url = urlparse(self.path)
            params = parse_qs(parsed_url.query)

            out_trade_no = params.get("out_trade_no", [None])[0]

            if not out_trade_no:
                self._send_error(400, "Missing out_trade_no parameter")
                return

            print(f"[PAYMENT-QUERY] Querying order: {out_trade_no}", file=sys.stderr)

            # 2. 查询订单
            zpay = ZPayManager()
            result = zpay.query_order(out_trade_no=out_trade_no)

            if result["success"]:
                order = result["order"]

                # 3. 返回订单信息
                self._send_success({
                    "success": True,
                    "order": {
                        "out_trade_no": order.get("out_trade_no"),
                        "trade_no": order.get("trade_no"),
                        "name": order.get("name"),
                        "money": order.get("money"),
                        "status": "paid" if order.get("status") == 1 else "unpaid",
                        "type": order.get("type"),
                        "addtime": order.get("addtime"),
                        "endtime": order.get("endtime")
                    }
                })

                print(f"[PAYMENT-QUERY] Order status: {'paid' if order.get('status') == 1 else 'unpaid'}", file=sys.stderr)
            else:
                self._send_error(404, result.get("error", "Order not found"))

        except Exception as e:
            print(f"[PAYMENT-QUERY] Error: {e}", file=sys.stderr)
            self._send_error(500, f"Internal server error: {str(e)}")

    def _send_success(self, data: dict):
        """发送成功响应"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def _send_error(self, code: int, message: str):
        """发送错误响应"""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        error_response = {
            "success": False,
            "error": message
        }
        self.wfile.write(json.dumps(error_response).encode('utf-8'))
