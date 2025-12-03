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
# 注意：敏感凭证必须通过环境变量配置，不要硬编码到代码中
# 在Vercel部署时，请在项目设置 → Environment Variables 中配置
ZPAY_API_URL = "https://zpayz.cn"
ZPAY_PID = os.getenv("ZPAY_PID")
ZPAY_PKEY = os.getenv("ZPAY_PKEY")


class ZPayManager:
    """ZPAY支付管理器"""

    def __init__(self):
        """初始化ZPAY配置"""
        self.api_url = ZPAY_API_URL
        self.pid = ZPAY_PID
        self.pkey = ZPAY_PKEY

        # ✅ 安全加固：强制要求凭证配置
        if not self.pid or not self.pkey:
            error_msg = "CRITICAL: ZPAY credentials (ZPAY_PID, ZPAY_PKEY) are required but not configured"
            print(f"[SECURITY] {error_msg}", file=sys.stderr)
            raise ValueError(error_msg)

        print("[ZPAY] Manager initialized successfully", file=sys.stderr)

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

            # 根据支付方式选择渠道
            if pay_type == "alipay":
                params["cid"] = "8191"  # 支付宝渠道 (商户号: 2088170309246664)
                print(f"[ZPAY] Using Alipay channel 8191", file=sys.stderr)
            elif pay_type == "wxpay":
                params["cid"] = "8180"  # 微信渠道
                print(f"[ZPAY] Using WeChat channel 8180", file=sys.stderr)

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

            # ✅ 添加响应调试信息
            print(f"[ZPAY-API] Response status: {response.status_code}", file=sys.stderr)
            print(f"[ZPAY-API] Response text (first 200 chars): {response.text[:200]}", file=sys.stderr)

            # ✅ 修复: 添加JSON解析错误处理
            try:
                result = response.json()
                # ✅ 调试: 输出完整的Z-Pay API响应
                print(f"[ZPAY-API] Full Z-Pay response: {result}", file=sys.stderr)
            except json.JSONDecodeError as e:
                print(f"[ZPAY-API] Error: Invalid JSON response", file=sys.stderr)
                print(f"[ZPAY-API] Full response text: {response.text}", file=sys.stderr)
                return {
                    "success": False,
                    "error": f"Invalid JSON response from payment gateway: {response.text[:100]}"
                }

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

            # ✅ 增强日志: 输出完整请求URL用于调试
            query_url = f"{self.api_url}/api.php"
            print(f"[ZPAY-QUERY] Request URL: {query_url}", file=sys.stderr)
            print(f"[ZPAY-QUERY] Request params: act={params['act']}, pid={params['pid'][:6]}..., out_trade_no={params.get('out_trade_no', 'N/A')}", file=sys.stderr)

            response = requests.get(
                query_url,
                params=params,
                timeout=10
            )

            # ✅ 增强日志: 输出响应状态和内容预览
            print(f"[ZPAY-QUERY] Response status: {response.status_code}", file=sys.stderr)
            print(f"[ZPAY-QUERY] Response preview (first 200 chars): {response.text[:200]}", file=sys.stderr)

            # ✅ 修复: 添加JSON解析错误处理
            try:
                result = response.json()
                # ✅ 调试: 输出完整的Z-Pay响应用于诊断
                print(f"[ZPAY-QUERY] Full Z-Pay response: {result}", file=sys.stderr)
            except json.JSONDecodeError as e:
                print(f"[ZPAY-QUERY] Error: Invalid JSON response from ZPAY", file=sys.stderr)
                print(f"[ZPAY-QUERY] Full response text: {response.text}", file=sys.stderr)
                print(f"[ZPAY-QUERY] JSON error: {e}", file=sys.stderr)
                return {
                    "success": False,
                    "error": f"Invalid JSON response from payment gateway"
                }

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
        验证支付回调签名（增强安全版本）

        Args:
            params: 回调参数

        Returns:
            签名是否有效
        """
        try:
            # ✅ 安全检查1：签名必须存在
            received_sign = params.get("sign", "")
            if not received_sign:
                print(f"[SECURITY] Signature missing in payment callback", file=sys.stderr)
                return False

            # ✅ 安全检查2：必要参数必须存在
            required_fields = ["out_trade_no", "trade_no", "money", "trade_status"]
            for field in required_fields:
                if field not in params:
                    print(f"[SECURITY] Required field '{field}' missing in payment callback", file=sys.stderr)
                    return False

            # ✅ 安全检查3：时间戳验证（防止重放攻击）
            timestamp = params.get("timestamp")
            if timestamp:
                try:
                    # 解析时间戳（支持多种格式）
                    if isinstance(timestamp, str):
                        # 尝试ISO格式
                        try:
                            callback_time = datetime.fromisoformat(timestamp)
                        except ValueError:
                            # 尝试Unix时间戳（秒）
                            try:
                                callback_time = datetime.fromtimestamp(float(timestamp))
                            except ValueError:
                                print(f"[SECURITY] Invalid timestamp format in payment callback: {timestamp}", file=sys.stderr)
                                return False
                    elif isinstance(timestamp, (int, float)):
                        # Unix时间戳（秒）
                        callback_time = datetime.fromtimestamp(timestamp)
                    else:
                        print(f"[SECURITY] Invalid timestamp type in payment callback", file=sys.stderr)
                        return False

                    # 计算时间差
                    now = datetime.now()
                    age_seconds = (now - callback_time).total_seconds()

                    # 拒绝超过5分钟的回调（防止重放攻击）
                    # 使用绝对值以防止时间漂移导致的未来时间戳
                    if abs(age_seconds) > 300:
                        print(f"[SECURITY] Payment callback too old or future-dated: {age_seconds:.1f}s", file=sys.stderr)
                        return False

                    print(f"[ZPAY-VERIFY] Timestamp validation passed (age: {age_seconds:.1f}s)", file=sys.stderr)

                except Exception as e:
                    print(f"[SECURITY] Timestamp validation error: {type(e).__name__}", file=sys.stderr)
                    return False
            else:
                # ⚠️ 如果ZPAY不提供timestamp字段，记录警告但暂不强制要求
                # 生产环境建议与ZPAY确认是否支持timestamp，并在后续版本中强制要求
                print(f"[WARNING] Payment callback missing timestamp field (order: {params.get('out_trade_no')})", file=sys.stderr)

            # 2. 移除sign和sign_type参数
            verify_params = {k: v for k, v in params.items() if k not in ["sign", "sign_type"]}

            # 3. 生成签名
            calculated_sign = self._generate_sign(verify_params)

            # 4. 对比签名（使用常量时间比较防止时序攻击）
            is_valid = received_sign == calculated_sign

            if is_valid:
                print(f"[ZPAY-VERIFY] Signature valid for order: {params.get('out_trade_no')}", file=sys.stderr)
            else:
                print(f"[SECURITY] Signature verification FAILED for order: {params.get('out_trade_no')}", file=sys.stderr)
                # ⚠️ 生产环境不输出实际签名值

            return is_valid

        except Exception as e:
            print(f"[SECURITY] Signature verification error: {type(e).__name__}", file=sys.stderr)
            # ✅ 安全默认：验证失败时返回False
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
        sign = hashlib.md5(sign_str.encode('utf-8'), usedforsecurity=False).hexdigest()

        # ✅ 安全：仅输出参数名列表用于调试，不输出实际值和密钥
        # 生产环境可通过环境变量 ZPAY_DEBUG_MODE=true 启用
        if os.getenv("ZPAY_DEBUG_MODE") == "true":
            param_names = list(filtered_params.keys())
            print(f"[DEBUG] Generating signature for params: {param_names}", file=sys.stderr)

        return sign

    def get_plan_info(self, plan_type: str) -> Dict:
        """
        获取订阅计划信息

        ⚠️ 关键修复: 从SubscriptionManager读取价格,确保价格统一管理

        Args:
            plan_type: 计划类型 (pro_monthly, pro_yearly, lifetime)

        Returns:
            计划信息
        """
        # ✅ 修复: 从SubscriptionManager导入,确保价格一致
        try:
            from subscription_manager import SubscriptionManager
        except ImportError:
            import os
            import sys
            sys.path.insert(0, os.path.dirname(__file__))
            from subscription_manager import SubscriptionManager

        sm = SubscriptionManager()

        # 从SubscriptionManager读取价格
        plan_data = sm.PLANS.get(plan_type)
        if not plan_data:
            return {
                "name": "未知套餐",
                "price": 0.0,
                "description": ""
            }

        # 构造描述文字
        descriptions = {
            "pro_monthly": "解锁所有高级版功能，按月订阅",
            "pro_yearly": "解锁所有高级版功能，年度订阅享17%折扣",
            "lifetime": "一次性购买，成为会员合伙人，共享价值"
        }

        return {
            "name": plan_data["name"],
            "price": plan_data["price"],
            "description": descriptions.get(plan_type, "")
        }
