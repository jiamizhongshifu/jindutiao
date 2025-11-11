"""
GaiYa每日进度条 - 认证客户端
封装所有认证和支付相关的API调用
"""
import os
import json
import requests
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime


class AuthClient:
    """认证客户端"""

    def __init__(self):
        """初始化客户端"""
        self.backend_url = os.getenv("GAIYA_API_URL", "https://jindutiao.vercel.app")
        self.auth_file = Path.home() / ".gaiya" / "auth.json"
        self.auth_file.parent.mkdir(parents=True, exist_ok=True)

        # 创建 Session 对象，自动使用系统代理（支持科学上网）
        self.session = requests.Session()
        # Session 默认会读取环境变量 HTTP_PROXY 和 HTTPS_PROXY

        # 加载已保存的Token
        self.access_token = None
        self.refresh_token = None
        self.user_info = None
        self._load_tokens()

    def _load_tokens(self):
        """从本地加载Token"""
        try:
            if self.auth_file.exists():
                with open(self.auth_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.access_token = data.get("access_token")
                    self.refresh_token = data.get("refresh_token")
                    self.user_info = data.get("user_info")
        except Exception as e:
            print(f"加载Token失败: {e}")

    def _save_tokens(self, access_token: str, refresh_token: str, user_info: Dict = None):
        """保存Token到本地"""
        try:
            data = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user_info": user_info,
                "saved_at": datetime.now().isoformat()
            }

            with open(self.auth_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self.access_token = access_token
            self.refresh_token = refresh_token
            self.user_info = user_info

        except Exception as e:
            print(f"保存Token失败: {e}")

    def _clear_tokens(self):
        """清除本地Token"""
        try:
            if self.auth_file.exists():
                self.auth_file.unlink()

            self.access_token = None
            self.refresh_token = None
            self.user_info = None

        except Exception as e:
            print(f"清除Token失败: {e}")

    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        return self.access_token is not None

    def get_user_id(self) -> Optional[str]:
        """获取当前用户ID"""
        if self.user_info:
            return self.user_info.get("user_id")
        return None

    def get_user_email(self) -> Optional[str]:
        """获取当前用户邮箱"""
        if self.user_info:
            return self.user_info.get("email")
        return None

    def get_user_tier(self) -> str:
        """获取当前用户等级"""
        if self.user_info:
            return self.user_info.get("user_tier", "free")
        return "free"

    # ==================== 认证API ====================

    def signup(self, email: str, password: str, username: str = None) -> Dict:
        """
        用户注册

        Args:
            email: 邮箱
            password: 密码
            username: 用户名（可选）

        Returns:
            {"success": True/False, "error": "...", "access_token": "...", ...}
        """
        try:
            response = self.session.post(
                f"{self.backend_url}/api/auth-signup",
                json={
                    "email": email,
                    "password": password,
                    "username": username
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                if data.get("success"):
                    # 检查是否包含access_token（新的Supabase邮箱验证流程不会立即返回token）
                    if "access_token" in data and "refresh_token" in data:
                        # 保存Token（仅当包含时）
                        self._save_tokens(
                            data["access_token"],
                            data["refresh_token"],
                            {
                                "user_id": data["user_id"],
                                "email": data["email"]
                            }
                        )
                    # 否则：等待邮箱验证后再登录

                return data
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except requests.exceptions.Timeout:
            return {"success": False, "error": "请求超时"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "无法连接到服务器"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def signin(self, email: str, password: str) -> Dict:
        """
        用户登录

        Args:
            email: 邮箱
            password: 密码

        Returns:
            {"success": True/False, "error": "...", "access_token": "...", ...}
        """
        try:
            response = self.session.post(
                f"{self.backend_url}/api/auth-signin",
                json={
                    "email": email,
                    "password": password
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                if data.get("success"):
                    # 保存Token
                    self._save_tokens(
                        data["access_token"],
                        data["refresh_token"],
                        {
                            "user_id": data["user_id"],
                            "email": data["email"],
                            "user_tier": data.get("user_tier", "free")
                        }
                    )

                return data
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except requests.exceptions.Timeout:
            return {"success": False, "error": "请求超时"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "无法连接到服务器"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def signout(self) -> Dict:
        """
        用户登出

        Returns:
            {"success": True/False, "error": "..."}
        """
        try:
            if not self.access_token:
                return {"success": False, "error": "未登录"}

            response = self.session.post(
                f"{self.backend_url}/api/auth-signout",
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=10
            )

            # 无论成功与否，都清除本地Token
            self._clear_tokens()

            if response.status_code == 200:
                return {"success": True}
            else:
                return {"success": True}  # 即使失败也返回成功

        except Exception as e:
            # 出错也清除本地Token
            self._clear_tokens()
            return {"success": True}

    def refresh_access_token(self) -> Dict:
        """
        刷新访问令牌

        Returns:
            {"success": True/False, "error": "...", "access_token": "...", ...}
        """
        try:
            if not self.refresh_token:
                return {"success": False, "error": "无刷新令牌"}

            response = self.session.post(
                f"{self.backend_url}/api/auth-refresh",
                json={"refresh_token": self.refresh_token},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                if data.get("success"):
                    # 更新Token
                    self._save_tokens(
                        data["access_token"],
                        data["refresh_token"],
                        self.user_info
                    )

                return data
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def reset_password(self, email: str) -> Dict:
        """
        请求重置密码

        Args:
            email: 邮箱

        Returns:
            {"success": True/False, "error": "...", "message": "..."}
        """
        try:
            response = self.session.post(
                f"{self.backend_url}/api/auth-reset-password",
                json={"email": email},
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== 订阅API ====================

    def get_subscription_status(self) -> Dict:
        """
        获取当前用户的订阅状态

        Returns:
            {"success": True/False, "is_active": True/False, "user_tier": "...", ...}
        """
        try:
            if not self.get_user_id():
                return {"success": False, "error": "未登录"}

            response = self.session.get(
                f"{self.backend_url}/api/subscription-status",
                params={"user_id": self.get_user_id()},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                # 更新本地用户信息
                if data.get("success") and self.user_info:
                    self.user_info["user_tier"] = data.get("user_tier", "free")
                    self._save_tokens(self.access_token, self.refresh_token, self.user_info)

                return data
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== 支付API ====================

    def create_payment_order(self, plan_type: str, pay_type: str = "alipay") -> Dict:
        """
        创建支付订单

        Args:
            plan_type: 订阅类型（pro_monthly, pro_yearly, lifetime）
            pay_type: 支付方式（alipay, wxpay）

        Returns:
            {"success": True/False, "payment_url": "...", "params": {...}, ...}
        """
        try:
            if not self.get_user_id():
                return {"success": False, "error": "未登录"}

            response = self.session.post(
                f"{self.backend_url}/api/payment-create-order",
                json={
                    "user_id": self.get_user_id(),
                    "plan_type": plan_type,
                    "pay_type": pay_type
                },
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def query_payment_order(self, out_trade_no: str) -> Dict:
        """
        查询支付订单状态

        Args:
            out_trade_no: 商户订单号

        Returns:
            {"success": True/False, "order": {...}}
        """
        try:
            response = self.session.get(
                f"{self.backend_url}/api/payment-query",
                params={"out_trade_no": out_trade_no},
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== 配额API ====================

    def get_quota_status(self) -> Dict:
        """
        获取AI功能配额状态

        Returns:
            {"remaining": {...}, "user_tier": "..."}
        """
        try:
            user_tier = self.get_user_tier()

            response = self.session.get(
                f"{self.backend_url}/api/quota-status",
                params={"user_tier": user_tier},
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                # 返回默认配额
                return {
                    "remaining": {
                        "daily_plan": 3 if user_tier == "free" else 50,
                        "weekly_report": 1 if user_tier == "free" else 10,
                        "chat": 10 if user_tier == "free" else 100
                    },
                    "user_tier": user_tier
                }

        except Exception as e:
            # 返回默认配额
            user_tier = self.get_user_tier()
            return {
                "remaining": {
                    "daily_plan": 3 if user_tier == "free" else 50,
                    "weekly_report": 1 if user_tier == "free" else 10,
                    "chat": 10 if user_tier == "free" else 100
                },
                "user_tier": user_tier
            }

    # ==================== 微信登录API ====================

    def wechat_get_qr_code(self) -> Dict:
        """
        获取微信登录二维码URL

        Returns:
            {"success": True/False, "qr_url": "...", "state": "...", "error": "..."}
        """
        try:
            response = self.session.get(
                f"{self.backend_url}/api/auth-wechat-qrcode",
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except requests.exceptions.Timeout:
            return {"success": False, "error": "请求超时"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "无法连接到服务器"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def wechat_check_scan_status(self, state: str) -> Dict:
        """
        检查微信扫码登录状态

        Args:
            state: 登录state参数

        Returns:
            {
                "status": "pending" | "scanned" | "success" | "expired" | "error",
                "user_info": {...},  # 仅当status为success时返回
                "error": "..."       # 仅当status为error时返回
            }
        """
        try:
            response = self.session.get(
                f"{self.backend_url}/api/auth-wechat-status",
                params={"state": state},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                # 如果登录成功，保存Token
                if data.get("status") == "success":
                    user_info = data.get("user_info", {})
                    access_token = data.get("access_token")
                    refresh_token = data.get("refresh_token")

                    if access_token and refresh_token:
                        self._save_tokens(
                            access_token,
                            refresh_token,
                            {
                                "user_id": user_info.get("user_id"),
                                "email": user_info.get("email"),
                                "username": user_info.get("username"),
                                "user_tier": user_info.get("user_tier", "free")
                            }
                        )

                return data
            else:
                return {"status": "error", "error": f"HTTP {response.status_code}"}

        except requests.exceptions.Timeout:
            return {"status": "error", "error": "请求超时"}
        except requests.exceptions.ConnectionError:
            return {"status": "error", "error": "无法连接到服务器"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ==================== OTP验证API ====================

    def send_otp(self, email: str, purpose: str = "signup") -> Dict:
        """
        发送OTP验证码到邮箱

        Args:
            email: 邮箱地址
            purpose: 用途（signup, password_reset）

        Returns:
            {"success": True/False, "error": "...", "message": "..."}
        """
        try:
            url = f"{self.backend_url}/api/auth-send-otp"
            print(f"[OTP] 正在发送验证码到: {email}")
            print(f"[OTP] 请求URL: {url}")

            response = self.session.post(
                url,
                json={
                    "email": email,
                    "purpose": purpose
                },
                timeout=10
            )

            print(f"[OTP] 响应状态码: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"[OTP] 发送成功: {result.get('message', '验证码已发送')}")
                return result
            else:
                error_msg = f"HTTP {response.status_code}"
                print(f"[OTP] 发送失败: {error_msg}")
                try:
                    error_detail = response.json()
                    print(f"[OTP] 错误详情: {error_detail}")
                except:
                    pass
                return {"success": False, "error": error_msg}

        except requests.exceptions.Timeout:
            print(f"[OTP] 错误: 请求超时（10秒）")
            return {"success": False, "error": "请求超时"}
        except requests.exceptions.ConnectionError as e:
            print(f"[OTP] 错误: 无法连接到服务器 - {e}")
            return {"success": False, "error": "无法连接到服务器"}
        except Exception as e:
            print(f"[OTP] 未知错误: {type(e).__name__}: {e}")
            return {"success": False, "error": str(e)}

    def verify_otp(self, email: str, otp_code: str) -> Dict:
        """
        验证OTP验证码

        Args:
            email: 邮箱地址
            otp_code: 6位数字验证码

        Returns:
            {"success": True/False, "error": "...", "message": "..."}
        """
        try:
            response = self.session.post(
                f"{self.backend_url}/api/auth-verify-otp",
                json={
                    "email": email,
                    "otp_code": otp_code
                },
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except requests.exceptions.Timeout:
            return {"success": False, "error": "请求超时"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "无法连接到服务器"}
        except Exception as e:
            return {"success": False, "error": str(e)}
