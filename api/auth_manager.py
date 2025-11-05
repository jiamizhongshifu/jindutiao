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
        邮箱注册

        Args:
            email: 邮箱地址
            password: 密码
            username: 用户名（可选）

        Returns:
            注册结果
        """
        if not self.client:
            return {"success": False, "error": "Supabase not configured"}

        try:
            # 1. 创建Supabase Auth用户
            auth_response = self.client.auth.sign_up({
                "email": email,
                "password": password
            })

            if not auth_response.user:
                return {
                    "success": False,
                    "error": "Failed to create auth user"
                }

            # 2. 创建用户记录
            user_data = {
                "id": auth_response.user.id,
                "email": email,
                "username": username or email.split("@")[0],
                "user_tier": "free",
                "auth_provider": "email",
                "email_verified": False,
                "status": "active"
            }

            db_response = self.client.table("users").insert(user_data).execute()

            print(f"User registered: {email}", file=sys.stderr)

            return {
                "success": True,
                "user_id": auth_response.user.id,
                "email": email,
                "access_token": auth_response.session.access_token if auth_response.session else None,
                "refresh_token": auth_response.session.refresh_token if auth_response.session else None
            }

        except Exception as e:
            print(f"Error during sign up: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}

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
