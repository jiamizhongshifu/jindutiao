"""
GaiYa每日进度条 - 用户认证管理器
使用Supabase Auth进行用户认证和会话管理
"""
import os
from datetime import datetime, timedelta
from typing import Dict, Optional
from supabase import create_client, Client
import sys

# Supabase配置
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")


class AuthManager:
    """用户认证管理器"""

    def __init__(self):
        """初始化Supabase客户端"""
        if not SUPABASE_URL or not SUPABASE_KEY:
            print("WARNING: Supabase credentials not configured", file=sys.stderr)
            self.client = None
        else:
            try:
                self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
                print("AuthManager initialized successfully", file=sys.stderr)
            except Exception as e:
                print(f"Failed to initialize Supabase client: {e}", file=sys.stderr)
                self.client = None

    def sign_up_with_email(self, email: str, password: str, username: Optional[str] = None) -> Dict:
        """
        邮箱注册（使用Supabase内置邮箱验证）

        Args:
            email: 邮箱地址
            password: 密码
            username: 用户名（可选）

        Returns:
            注册结果，包含user_id但不包含session（需要邮箱验证后才能登录）
        """
        if not self.client:
            return {"success": False, "error": "Supabase not configured"}

        try:
            # 1. 创建Supabase Auth用户（会自动发送验证邮件）
            # Supabase会发送包含验证链接的邮件到用户邮箱
            auth_response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "email_redirect_to": "https://jindutiao.vercel.app/email-verified",  # 验证后跳转到成功页面
                    "data": {
                        "username": username or email.split("@")[0]
                    }
                }
            })

            if not auth_response.user:
                return {
                    "success": False,
                    "error": "Failed to create auth user"
                }

            print(f"[AUTH-SIGNUP] User registered: {email}, verification email sent by Supabase", file=sys.stderr)
            print(f"[AUTH-SIGNUP] User ID: {auth_response.user.id}, Email confirmed: {auth_response.user.email_confirmed_at}", file=sys.stderr)

            # 2. 创建用户记录（暂时不创建，等验证后通过webhook创建）
            # 或者立即创建但标记为未验证
            user_data = {
                "id": auth_response.user.id,
                "email": email,
                "username": username or email.split("@")[0],
                "user_tier": "free",
                "auth_provider": "email",
                "email_verified": False,  # 待邮箱验证
                "status": "pending_verification"  # 待验证状态
            }

            try:
                db_response = self.client.table("users").insert(user_data).execute()
                print(f"[AUTH-SIGNUP] User record created in database", file=sys.stderr)
            except Exception as db_error:
                print(f"[AUTH-SIGNUP] Warning: Failed to create user record (will retry after verification): {db_error}", file=sys.stderr)
                # 继续，因为Auth用户已创建成功

            # 3. 返回成功（但没有session，需要邮箱验证）
            return {
                "success": True,
                "user_id": auth_response.user.id,
                "email": email,
                "email_verified": False,
                "message": "注册成功！我们已向您的邮箱发送了验证邮件，请查收并点击验证链接。"
            }

        except Exception as e:
            error_msg = str(e)
            print(f"[AUTH-SIGNUP] Error during sign up: {error_msg}", file=sys.stderr)

            # 友好的错误提示
            if "already registered" in error_msg.lower() or "already exists" in error_msg.lower():
                return {"success": False, "error": "该邮箱已被注册"}
            elif "invalid email" in error_msg.lower():
                return {"success": False, "error": "邮箱格式不正确"}
            else:
                return {"success": False, "error": f"注册失败: {error_msg}"}

    def sign_in_with_email(self, email: str, password: str) -> Dict:
        """
        邮箱登录

        Args:
            email: 邮箱地址
            password: 密码

        Returns:
            登录结果
        """
        if not self.client:
            return {"success": False, "error": "Supabase not configured"}

        try:
            # 1. 使用Supabase Auth登录
            auth_response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if not auth_response.user:
                return {
                    "success": False,
                    "error": "Invalid credentials"
                }

            # 2. 更新最后登录时间
            self.client.table("users").update({
                "last_login_at": datetime.now().isoformat()
            }).eq("id", auth_response.user.id).execute()

            # 3. 获取用户信息
            user_response = self.client.table("users").select("*").eq("id", auth_response.user.id).execute()

            user_data = user_response.data[0] if user_response.data else {}

            print(f"User signed in: {email}", file=sys.stderr)

            return {
                "success": True,
                "user_id": auth_response.user.id,
                "email": email,
                "user_tier": user_data.get("user_tier", "free"),
                "access_token": auth_response.session.access_token if auth_response.session else None,
                "refresh_token": auth_response.session.refresh_token if auth_response.session else None
            }

        except Exception as e:
            print(f"Error during sign in: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}

    def sign_out(self, access_token: str) -> Dict:
        """
        登出

        Args:
            access_token: 访问令牌

        Returns:
            登出结果
        """
        if not self.client:
            return {"success": False, "error": "Supabase not configured"}

        try:
            self.client.auth.sign_out()
            print("User signed out", file=sys.stderr)
            return {"success": True}

        except Exception as e:
            print(f"Error during sign out: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}

    def check_email_verification(self, user_id: Optional[str] = None, email: Optional[str] = None) -> Dict:
        """
        检查邮箱验证状态（用于前端轮询）

        Args:
            user_id: 用户ID（可选）
            email: 邮箱地址（可选）

        Returns:
            验证状态结果
        """
        if not self.client:
            return {"success": False, "error": "Supabase not configured"}

        try:
            # 1. 从Supabase Auth查询用户
            if user_id:
                # 通过user_id查询（需要admin权限，这里用直接查询users表代替）
                user_response = self.client.table("users").select("*").eq("id", user_id).execute()
                if not user_response.data:
                    return {
                        "success": False,
                        "error": "User not found",
                        "verified": False
                    }
                user_data = user_response.data[0]
                email = user_data.get("email")

            # 2. 从auth.users表查询验证状态
            # 注意：Supabase Auth的email_confirmed_at字段存储在auth.users表中
            # 我们需要通过RPC或直接查询来获取
            # 临时方案：通过尝试登录来检测是否已验证（Supabase会拒绝未验证的登录）

            # 方案：查询users表的email_verified字段（需要通过webhook或触发器更新）
            if email:
                user_response = self.client.table("users").select("email_verified, id").eq("email", email).execute()

                if not user_response.data:
                    print(f"[CHECK-VERIFICATION] User not found in users table: {email}", file=sys.stderr)
                    return {
                        "success": True,
                        "verified": False,
                        "message": "等待邮箱验证..."
                    }

                user_data = user_response.data[0]
                is_verified = user_data.get("email_verified", False)

                print(f"[CHECK-VERIFICATION] Email: {email}, Verified: {is_verified}", file=sys.stderr)

                if is_verified:
                    # 验证成功
                    return {
                        "success": True,
                        "verified": True,
                        "user_id": user_data.get("id"),
                        "email": email,
                        "message": "邮箱验证成功！"
                    }
                else:
                    # 尚未验证
                    return {
                        "success": True,
                        "verified": False,
                        "message": "等待邮箱验证..."
                    }
            else:
                return {
                    "success": False,
                    "error": "Email is required"
                }

        except Exception as e:
            print(f"[CHECK-VERIFICATION] Error: {e}", file=sys.stderr)
            return {
                "success": False,
                "error": str(e),
                "verified": False
            }

    def get_user_by_token(self, access_token: str) -> Optional[Dict]:
        """
        通过访问令牌获取用户信息

        Args:
            access_token: 访问令牌

        Returns:
            用户信息
        """
        if not self.client:
            return None

        try:
            # 1. 验证token并获取用户
            user_response = self.client.auth.get_user(access_token)

            if not user_response.user:
                return None

            # 2. 从数据库获取完整用户信息
            db_response = self.client.table("users").select("*").eq("id", user_response.user.id).execute()

            if not db_response.data:
                return None

            return db_response.data[0]

        except Exception as e:
            print(f"Error getting user by token: {e}", file=sys.stderr)
            return None

    def refresh_access_token(self, refresh_token: str) -> Dict:
        """
        刷新访问令牌

        Args:
            refresh_token: 刷新令牌

        Returns:
            新的访问令牌
        """
        if not self.client:
            return {"success": False, "error": "Supabase not configured"}

        try:
            auth_response = self.client.auth.refresh_session(refresh_token)

            if not auth_response.session:
                return {
                    "success": False,
                    "error": "Failed to refresh token"
                }

            return {
                "success": True,
                "access_token": auth_response.session.access_token,
                "refresh_token": auth_response.session.refresh_token
            }

        except Exception as e:
            print(f"Error refreshing token: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}

    def update_user_profile(self, user_id: str, updates: Dict) -> Dict:
        """
        更新用户资料

        Args:
            user_id: 用户ID
            updates: 要更新的字段

        Returns:
            更新结果
        """
        if not self.client:
            return {"success": False, "error": "Supabase not configured"}

        try:
            # 允许更新的字段白名单
            allowed_fields = {"username", "display_name", "avatar_url"}
            filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}

            if not filtered_updates:
                return {
                    "success": False,
                    "error": "No valid fields to update"
                }

            response = self.client.table("users").update(filtered_updates).eq("id", user_id).execute()

            print(f"User profile updated: {user_id}", file=sys.stderr)

            return {
                "success": True,
                "user": response.data[0] if response.data else None
            }

        except Exception as e:
            print(f"Error updating user profile: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}

    def verify_email(self, token: str) -> Dict:
        """
        验证邮箱

        Args:
            token: 验证令牌

        Returns:
            验证结果
        """
        if not self.client:
            return {"success": False, "error": "Supabase not configured"}

        try:
            # Supabase会自动处理邮箱验证
            # 这里只需更新数据库中的email_verified字段

            # 从token中提取用户ID（实际应该从Supabase Auth获取）
            # 这里简化处理
            auth_response = self.client.auth.verify_otp({
                "type": "email",
                "token": token
            })

            if not auth_response.user:
                return {
                    "success": False,
                    "error": "Invalid verification token"
                }

            # 更新邮箱验证状态
            self.client.table("users").update({
                "email_verified": True
            }).eq("id", auth_response.user.id).execute()

            print(f"Email verified for user: {auth_response.user.id}", file=sys.stderr)

            return {"success": True}

        except Exception as e:
            print(f"Error verifying email: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}

    def request_password_reset(self, email: str) -> Dict:
        """
        请求重置密码

        Args:
            email: 邮箱地址

        Returns:
            请求结果
        """
        if not self.client:
            return {"success": False, "error": "Supabase not configured"}

        try:
            self.client.auth.reset_password_for_email(email)

            print(f"Password reset requested for: {email}", file=sys.stderr)

            return {
                "success": True,
                "message": "Password reset email sent"
            }

        except Exception as e:
            print(f"Error requesting password reset: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}

    def update_password(self, access_token: str, new_password: str) -> Dict:
        """
        更新密码

        Args:
            access_token: 访问令牌
            new_password: 新密码

        Returns:
            更新结果
        """
        if not self.client:
            return {"success": False, "error": "Supabase not configured"}

        try:
            # 使用access_token更新密码
            self.client.auth.update_user({
                "password": new_password
            })

            print("Password updated successfully", file=sys.stderr)

            return {"success": True}

        except Exception as e:
            print(f"Error updating password: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}

    def delete_user(self, user_id: str) -> Dict:
        """
        删除用户账号

        Args:
            user_id: 用户ID

        Returns:
            删除结果
        """
        if not self.client:
            return {"success": False, "error": "Supabase not configured"}

        try:
            # 1. 软删除（标记为deleted状态）
            self.client.table("users").update({
                "status": "deleted"
            }).eq("id", user_id).execute()

            # 2. 删除Auth用户（可选，根据业务需求）
            # self.client.auth.admin.delete_user(user_id)

            print(f"User deleted: {user_id}", file=sys.stderr)

            return {"success": True}

        except Exception as e:
            print(f"Error deleting user: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}

    def send_otp_email(self, email: str, otp_code: str, purpose: str) -> Dict:
        """
        发送OTP验证码邮件（使用Resend邮件服务）

        Args:
            email: 邮箱地址
            otp_code: 6位数字验证码
            purpose: 用途（signup, password_reset）

        Returns:
            发送结果
        """
        try:
            # 尝试使用Resend邮件服务
            resend_api_key = os.getenv("RESEND_API_KEY")

            # 诊断日志：检查环境变量
            if resend_api_key:
                print(f"[AUTH-OTP-DEBUG] RESEND_API_KEY found, length: {len(resend_api_key)}", file=sys.stderr)
            else:
                print(f"[AUTH-OTP-DEBUG] RESEND_API_KEY not found, using dev mode", file=sys.stderr)

            if resend_api_key:
                # 生产环境：使用Resend发送邮件
                try:
                    import resend
                    resend.api_key = resend_api_key
                    print(f"[RESEND] Attempting to send OTP email to: {email}", file=sys.stderr)

                    # 根据用途定制邮件内容
                    if purpose == "signup":
                        subject = "欢迎注册GaiYa - 验证您的邮箱"
                        html_content = f"""
                        <html>
                        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                            <h2 style="color: #333;">欢迎使用 GaiYa 每日进度条！</h2>
                            <p style="font-size: 16px; color: #666;">感谢您注册GaiYa。请使用以下验证码完成邮箱验证：</p>

                            <div style="background: #f5f5f5; border-radius: 8px; padding: 20px; text-align: center; margin: 30px 0;">
                                <p style="font-size: 14px; color: #999; margin: 0 0 10px 0;">您的验证码</p>
                                <p style="font-size: 32px; font-weight: bold; color: #4CAF50; letter-spacing: 8px; margin: 0;">
                                    {otp_code}
                                </p>
                            </div>

                            <p style="font-size: 14px; color: #999;">
                                • 此验证码将在 <strong>10分钟</strong> 后失效<br>
                                • 如果这不是您的操作，请忽略此邮件<br>
                                • 请勿将验证码分享给他人
                            </p>

                            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                            <p style="font-size: 12px; color: #999; text-align: center;">
                                GaiYa 每日进度条 - 让每一天都看得见进度
                            </p>
                        </body>
                        </html>
                        """
                    else:  # password_reset
                        subject = "GaiYa - 重置您的密码"
                        html_content = f"""
                        <html>
                        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                            <h2 style="color: #333;">重置密码请求</h2>
                            <p style="font-size: 16px; color: #666;">您正在重置GaiYa账号密码。请使用以下验证码：</p>

                            <div style="background: #f5f5f5; border-radius: 8px; padding: 20px; text-align: center; margin: 30px 0;">
                                <p style="font-size: 14px; color: #999; margin: 0 0 10px 0;">验证码</p>
                                <p style="font-size: 32px; font-weight: bold; color: #FF9800; letter-spacing: 8px; margin: 0;">
                                    {otp_code}
                                </p>
                            </div>

                            <p style="font-size: 14px; color: #999;">
                                • 此验证码将在 <strong>10分钟</strong> 后失效<br>
                                • 如果这不是您的操作，请立即修改密码<br>
                                • 请勿将验证码分享给他人
                            </p>
                        </body>
                        </html>
                        """

                    # 发送邮件
                    params = {
                        "from": "onboarding@resend.dev",
                        "to": [email],
                        "subject": subject,
                        "html": html_content
                    }

                    response = resend.Emails.send(params)
                    print(f"[RESEND] ✅ OTP email sent successfully!", file=sys.stderr)
                    print(f"[RESEND] Email ID: {response.get('id')}", file=sys.stderr)
                    print(f"[RESEND] To: {email}", file=sys.stderr)
                    print(f"[RESEND] From: {params['from']}", file=sys.stderr)
                    print(f"[RESEND] Full response: {response}", file=sys.stderr)

                    # ✅ 只有真正发送成功才返回成功
                    return {
                        "success": True,
                        "message": "验证码已发送到您的邮箱"
                    }

                except ImportError as e:
                    error_msg = f"Resend module not installed: {e}"
                    print(f"[ERROR] {error_msg}", file=sys.stderr)
                    print(f"[ERROR] Run: pip install resend", file=sys.stderr)
                    # ❌ 返回失败而不是继续执行
                    return {
                        "success": False,
                        "error": "邮件服务未配置，请联系管理员"
                    }
                except Exception as e:
                    error_msg = f"Resend send failed: {e}"
                    print(f"[ERROR] {error_msg}", file=sys.stderr)
                    print(f"[ERROR] Type: {type(e).__name__}", file=sys.stderr)
                    # ❌ 返回失败而不是继续执行
                    return {
                        "success": False,
                        "error": f"发送验证码失败: {str(e)}"
                    }
            else:
                # 开发模式：RESEND_API_KEY未配置
                print(f"[DEV MODE] ⚠️ RESEND_API_KEY not configured", file=sys.stderr)
                print(f"[DEV MODE] OTP Code for {email}: {otp_code} (purpose: {purpose})", file=sys.stderr)
                print(f"[DEV MODE] Email will NOT be sent. Configure RESEND_API_KEY to enable email sending", file=sys.stderr)

                return {
                    "success": False,
                    "error": "邮件服务未配置，验证码未发送"
                }

        except Exception as e:
            print(f"Error sending OTP email: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}

    def store_otp(self, email: str, otp_code: str, purpose: str, expires_at: str) -> Dict:
        """
        存储OTP到数据库

        Args:
            email: 邮箱地址
            otp_code: 验证码
            purpose: 用途（signup, password_reset）
            expires_at: 过期时间（ISO格式字符串）

        Returns:
            存储结果
        """
        if not self.client:
            return {"success": False, "error": "Supabase not configured"}

        try:
            # 先删除该邮箱的旧验证码
            self.client.table("otp_codes").delete().eq("email", email).execute()

            # 插入新验证码
            self.client.table("otp_codes").insert({
                "email": email,
                "code": otp_code,
                "purpose": purpose,
                "expires_at": expires_at,
                "attempts": 0
            }).execute()

            print(f"[OTP-STORE] OTP stored for: {email}", file=sys.stderr)
            return {"success": True}

        except Exception as e:
            print(f"[OTP-STORE] Error: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}

    def verify_otp(self, email: str, otp_code: str) -> Dict:
        """
        验证OTP

        Args:
            email: 邮箱地址
            otp_code: 用户输入的验证码

        Returns:
            验证结果
        """
        if not self.client:
            return {"success": False, "error": "Supabase not configured"}

        try:
            from datetime import datetime, timezone

            # 从数据库获取OTP
            response = self.client.table("otp_codes").select("*").eq("email", email).execute()

            if not response.data:
                return {"success": False, "error": "验证码不存在或已过期"}

            stored_otp = response.data[0]

            # 检查过期时间（统一使用UTC时区）
            expires_at_str = stored_otp["expires_at"].replace('Z', '+00:00')
            expires_at = datetime.fromisoformat(expires_at_str)
            now_utc = datetime.now(timezone.utc)

            print(f"[OTP-VERIFY] Checking expiry: now={now_utc.isoformat()}, expires={expires_at.isoformat()}", file=sys.stderr)

            if now_utc > expires_at:
                self.client.table("otp_codes").delete().eq("email", email).execute()
                return {"success": False, "error": "验证码已过期"}

            # 检查尝试次数
            if stored_otp["attempts"] >= 5:
                self.client.table("otp_codes").delete().eq("email", email).execute()
                return {"success": False, "error": "验证尝试次数过多，请重新获取验证码"}

            # 验证OTP
            if stored_otp["code"] != otp_code:
                # 增加尝试次数
                self.client.table("otp_codes").update({
                    "attempts": stored_otp["attempts"] + 1
                }).eq("email", email).execute()

                remaining = 5 - stored_otp["attempts"] - 1
                return {"success": False, "error": f"验证码错误，还剩{remaining}次机会"}

            # 验证成功，删除OTP
            self.client.table("otp_codes").delete().eq("email", email).execute()

            print(f"[OTP-VERIFY] OTP verified for: {email}", file=sys.stderr)
            return {"success": True, "purpose": stored_otp["purpose"]}

        except Exception as e:
            print(f"[OTP-VERIFY] Error: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}

    def mark_email_verified(self, email: str) -> Dict:
        """
        标记邮箱为已验证

        Args:
            email: 邮箱地址

        Returns:
            更新结果
        """
        if not self.client:
            return {"success": False, "error": "Supabase not configured"}

        try:
            # 更新数据库中的email_verified字段
            response = self.client.table("users").update({
                "email_verified": True
            }).eq("email", email).execute()

            print(f"Email marked as verified: {email}", file=sys.stderr)

            return {"success": True}

        except Exception as e:
            print(f"Error marking email as verified: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}
