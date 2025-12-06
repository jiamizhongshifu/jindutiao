"""
查询支付订单状态API
GET /api/payment-query?out_trade_no=xxx

Version: 2.0 - Fixed api.php query
"""
from http.server import BaseHTTPRequestHandler
import json
import sys
from urllib.parse import parse_qs, urlparse

try:
    from zpay_manager import ZPayManager
    from cors_config import get_cors_origin
except ImportError:
    import os
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from zpay_manager import ZPayManager
    from cors_config import get_cors_origin


class handler(BaseHTTPRequestHandler):
    """查询订单处理器"""

    def do_GET(self):
        """处理查询请求"""
        try:
            # ✅ 安全修复: CORS源白名单验证
            request_origin = self.headers.get('Origin', '')
            self.allowed_origin = get_cors_origin(request_origin)

            # 1. 解析查询参数
            parsed_url = urlparse(self.path)
            params = parse_qs(parsed_url.query)

            out_trade_no = params.get("out_trade_no", [None])[0]
            trade_no = params.get("trade_no", [None])[0]

            if not out_trade_no:
                self._send_error(400, "Missing out_trade_no parameter")
                return

            print(f"[PAYMENT-QUERY] Querying order: out_trade_no={out_trade_no}, trade_no={trade_no}", file=sys.stderr)

            # 2. 查询订单
            zpay = ZPayManager()

            # ✅ 修复: mapi.php 不支持查询操作,统一使用 api.php 查询
            # mapi.php 创建的订单可以通过 api.php 查询(已验证)
            print(f"[PAYMENT-QUERY] Querying order via api.php: out_trade_no={out_trade_no}, trade_no={trade_no}", file=sys.stderr)
            result = zpay.query_order(out_trade_no=out_trade_no, trade_no=trade_no)

            if result["success"]:
                order = result["order"]
                is_paid = self._is_paid_status(order.get("status"))

                # 3. 返回订单信息
                self._send_success({
                    "success": True,
                    "order": {
                        "out_trade_no": order.get("out_trade_no"),
                        "trade_no": order.get("trade_no"),
                        "name": order.get("name"),
                        "money": order.get("money"),
                        "status": "paid" if is_paid else "unpaid",
                        "type": order.get("type"),
                        "addtime": order.get("addtime"),
                        "endtime": order.get("endtime"),
                        "param": order.get("param", "")  # ✅ 关键修复: 必须包含param字段,客户端需要从中提取user_id和plan_type
                    }
                })

                print(f"[PAYMENT-QUERY] Order status: {'paid' if is_paid else 'unpaid'}", file=sys.stderr)
            else:
                # 兜底: 不再返回404，避免客户端轮询中断；标记未支付/未找到
                self._send_success({
                    "success": True,
                    "order": {
                        "out_trade_no": out_trade_no,
                        "status": "unpaid",
                        "error": result.get("error", "Order not found")
                    }
                })
                print(f"[PAYMENT-QUERY] Order not found yet, return unpaid", file=sys.stderr)

        except Exception as e:
            print(f"[PAYMENT-QUERY] Error: {e}", file=sys.stderr)
            self._send_error(500, f"Internal server error: {str(e)}")

    def _send_success(self, data: dict):
        """发送成功响应"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', getattr(self, 'allowed_origin', '*'))
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def _send_error(self, code: int, message: str):
        """发送错误响应"""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', getattr(self, 'allowed_origin', '*'))
        self.end_headers()

        error_response = {
            "success": False,
            "error": message
        }
        self.wfile.write(json.dumps(error_response).encode('utf-8'))

    @staticmethod
    def _is_paid_status(status_value) -> bool:
        """
        将ZPAY返回的status值统一转换为布尔标记。
        ZPAY会把status序列化为"1"/"0"，这里同时兼容字符串和数值。
        """
        if status_value is None:
            return False

        if isinstance(status_value, str):
            normalized = status_value.strip().lower()
            if normalized in {"paid", "unpaid"}:
                return normalized == "paid"
            if normalized == "":
                return False
            status_value = normalized

        try:
            numeric_status = int(float(status_value))
            return numeric_status == 1
        except (ValueError, TypeError):
            return False
