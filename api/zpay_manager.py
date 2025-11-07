"""
GaiYa每日进度条 - ZPAY支付管理器
基于 ZPAY（易支付）接口实现支付功能
"""
import os
import hashlib
import json
import requests
from datetime import datetime
from typing import Dict, Optional
import sys

# ZPAY配置
ZPAY_API_URL = "https://zpayz.cn"
ZPAY_PID = os.getenv("ZPAY_PID", "2025040215385823")
ZPAY_PKEY = os.getenv("ZPAY_PKEY", "Ltb8ZL7kuFg7ZgtnIbuIpJ350FoTXdqu")


class ZPayManager:
    """ZPAY支付管理器"""

    def __init__(self):
        """初始化ZPAY配置"""
        self.api_url = ZPAY_API_URL
        self.pid = ZPAY_PID
        self.pkey = ZPAY_PKEY

        if not self.pid or not self.pkey:
            print("WARNING: ZPAY credentials not configured", file=sys.stderr)

        print("ZPayManager initialized successfully", file=sys.stderr)

    def create_order(
        self,
        out_trade_no: str,
        name: str,
        money: float,
        pay_type: str,
        notify_url: str,
        return_url: str,
        param: str = ""
    ) -> Dict:
        """
        创建支付订单（页面跳转方式）

        Args:
            out_trade_no: 商户订单号（唯一）
            name: 商品名称
            money: 订单金额（元）
            pay_type: 支付方式（alipay/wxpay）
            notify_url: 异步通知地址
            return_url: 同步跳转地址
            param: 附加参数（可选）

        Returns:
            支付链接信息
        """
        try:
            # 1. 构建参数
            params = {
                "pid": self.pid,
                "type": pay_type,
                "out_trade_no": out_trade_no,
                "notify_url": notify_url,
                "return_url": return_url,
                "name": name,
                "money": f"{money:.2f}",
                "sign_type": "MD5"
            }

            # 添加可选参数
            if param:
                params["param"] = param

            # 临时方案：明确指定使用渠道8180（已确认可用的渠道）
            # 渠道8191可能需要完成支付宝官方签约，暂时使用8180
            params["cid"] = "8180"
            print(f"[ZPAY] Using channel 8180 to avoid channel 8191 issue", file=sys.stderr)

            # 2. 生成签名
            sign = self._generate_sign(params)
            params["sign"] = sign

            # 3. 构建支付URL
            payment_url = f"{self.api_url}/submit.php"

            print(f"[ZPAY] Created order: {out_trade_no}, amount: ¥{money:.2f}, type: {pay_type}", file=sys.stderr)

            return {
                "success": True,
                "payment_url": payment_url,
                "params": params,
                "out_trade_no": out_trade_no
            }

        except Exception as e:
            print(f"[ZPAY] Error creating order: {e}", file=sys.stderr)
            return {
                "success": False,
                "error": str(e)
            }

    def create_api_order(
        self,
        out_trade_no: str,
        name: str,
        money: float,
        pay_type: str,
        notify_url: str,
        clientip: str,
        param: str = ""
    ) -> Dict:
        """
        创建支付订单（API方式）

        Args:
            out_trade_no: 商户订单号
            name: 商品名称
            money: 订单金额
            pay_type: 支付方式（alipay/wxpay）
            notify_url: 异步通知地址
            clientip: 用户IP地址
            param: 附加参数（可选）

        Returns:
            支付信息（包含payurl/qrcode/img）
        """
        try:
            # 1. 构建参数
            params = {
                "pid": self.pid,
                "type": pay_type,
                "out_trade_no": out_trade_no,
                "notify_url": notify_url,
                "name": name,
                "money": f"{money:.2f}",
                "clientip": clientip,
                "sign_type": "MD5"
            }

            if param:
                params["param"] = param

            # 2. 生成签名
            sign = self._generate_sign(params)
            params["sign"] = sign

            # 3. 发起API请求
            response = requests.post(
                f"{self.api_url}/mapi.php",
                data=params,
                timeout=10
            )

            result = response.json()

            if result.get("code") == 1:
                print(f"[ZPAY-API] Order created: {out_trade_no}", file=sys.stderr)
                return {
                    "success": True,
                    "trade_no": result.get("trade_no"),
                    "O_id": result.get("O_id"),
                    "payurl": result.get("payurl"),
                    "qrcode": result.get("qrcode"),
                    "img": result.get("img")
                }
            else:
                print(f"[ZPAY-API] Order creation failed: {result.get('msg')}", file=sys.stderr)
                return {
                    "success": False,
                    "error": result.get("msg", "Unknown error")
                }

        except Exception as e:
            print(f"[ZPAY-API] Error: {e}", file=sys.stderr)
            return {
                "success": False,
                "error": str(e)
            }

    def query_order(self, out_trade_no: Optional[str] = None, trade_no: Optional[str] = None) -> Dict:
        """
        查询订单状态

        Args:
            out_trade_no: 商户订单号
            trade_no: ZPAY订单号

        Returns:
            订单信息
        """
        if not out_trade_no and not trade_no:
            return {
                "success": False,
                "error": "out_trade_no or trade_no is required"
            }

        try:
            # 构建查询URL
            params = {
                "act": "order",
                "pid": self.pid,
                "key": self.pkey
            }

            if out_trade_no:
                params["out_trade_no"] = out_trade_no
            if trade_no:
                params["trade_no"] = trade_no

            response = requests.get(
                f"{self.api_url}/api.php",
                params=params,
                timeout=10
            )

            result = response.json()

            if result.get("code") == 1:
                print(f"[ZPAY-QUERY] Order found: {out_trade_no or trade_no}, status: {result.get('status')}", file=sys.stderr)
                return {
                    "success": True,
                    "order": result
                }
            else:
                print(f"[ZPAY-QUERY] Order not found or error: {result.get('msg')}", file=sys.stderr)
                return {
                    "success": False,
                    "error": result.get("msg", "Order not found")
                }

        except Exception as e:
            print(f"[ZPAY-QUERY] Error: {e}", file=sys.stderr)
            return {
                "success": False,
                "error": str(e)
            }

    def verify_notify(self, params: Dict) -> bool:
        """
        验证支付回调签名

        Args:
            params: 回调参数

        Returns:
            签名是否有效
        """
        try:
            # 1. 获取传入的签名
            received_sign = params.get("sign", "")

            # 2. 移除sign和sign_type参数
            verify_params = {k: v for k, v in params.items() if k not in ["sign", "sign_type"]}

            # 3. 生成签名
            calculated_sign = self._generate_sign(verify_params)

            # 4. 对比签名
            is_valid = received_sign == calculated_sign

            if is_valid:
                print(f"[ZPAY-VERIFY] Signature valid for order: {params.get('out_trade_no')}", file=sys.stderr)
            else:
                print(f"[ZPAY-VERIFY] Signature invalid! Received: {received_sign}, Calculated: {calculated_sign}", file=sys.stderr)

            return is_valid

        except Exception as e:
            print(f"[ZPAY-VERIFY] Error: {e}", file=sys.stderr)
            return False

    def request_refund(self, out_trade_no: str, money: float, trade_no: Optional[str] = None) -> Dict:
        """
        申请退款

        Args:
            out_trade_no: 商户订单号
            money: 退款金额
            trade_no: ZPAY订单号（可选）

        Returns:
            退款结果
        """
        try:
            params = {
                "pid": self.pid,
                "key": self.pkey,
                "out_trade_no": out_trade_no,
                "money": f"{money:.2f}"
            }

            if trade_no:
                params["trade_no"] = trade_no

            response = requests.post(
                f"{self.api_url}/api.php?act=refund",
                data=params,
                timeout=10
            )

            result = response.json()

            if result.get("code") == 1:
                print(f"[ZPAY-REFUND] Refund successful: {out_trade_no}", file=sys.stderr)
                return {
                    "success": True,
                    "message": result.get("msg")
                }
            else:
                print(f"[ZPAY-REFUND] Refund failed: {result.get('msg')}", file=sys.stderr)
                return {
                    "success": False,
                    "error": result.get("msg", "Refund failed")
                }

        except Exception as e:
            print(f"[ZPAY-REFUND] Error: {e}", file=sys.stderr)
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_sign(self, params: Dict) -> str:
        """
        生成MD5签名

        签名算法：
        1. 参数按ASCII码排序
        2. 拼接成 a=b&c=d 格式
        3. 加上商户密钥：md5(a=b&c=d + KEY)

        Args:
            params: 参数字典

        Returns:
            MD5签名（小写）
        """
        # 1. 移除sign和sign_type，并过滤空值
        filtered_params = {
            k: v for k, v in params.items()
            if k not in ["sign", "sign_type"] and v is not None and v != ""
        }

        # 2. 按键名ASCII码排序
        sorted_params = sorted(filtered_params.items())

        # 3. 拼接成 key=value 格式
        sign_str = "&".join([f"{k}={v}" for k, v in sorted_params])

        # 4. 加上商户密钥
        sign_str += self.pkey

        # 5. MD5加密（小写）
        sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest()

        print(f"[ZPAY-SIGN] Sign string: {sign_str[:100]}...", file=sys.stderr)
        print(f"[ZPAY-SIGN] Generated sign: {sign}", file=sys.stderr)

        return sign

    def get_plan_info(self, plan_type: str) -> Dict:
        """
        获取订阅计划信息

        Args:
            plan_type: 计划类型 (pro_monthly, pro_yearly, lifetime)

        Returns:
            计划信息
        """
        plans = {
            "pro_monthly": {
                "name": "GaiYa Pro 月度会员",
                "price": 9.9,
                "description": "解锁所有Pro功能，按月订阅"
            },
            "pro_yearly": {
                "name": "GaiYa Pro 年度会员",
                "price": 59.0,
                "description": "解锁所有Pro功能，年度订阅享17%折扣"
            },
            "lifetime": {
                "name": "GaiYa 终身会员",
                "price": 199.0,
                "description": "一次性购买，终身享受Pro功能"
            }
        }

        return plans.get(plan_type, {
            "name": "未知套餐",
            "price": 0.0,
            "description": ""
        })
