"""
GaiYa每日进度条 - API速率限制器
基于Supabase实现跨Serverless函数的速率限制保护
"""
import os
import sys
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict
from supabase import create_client, Client
import hashlib

# Supabase配置
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")


class RateLimiter:
    """
    速率限制器 - 防止API滥用和暴力破解攻击

    特性：
    - 基于IP地址、用户ID或邮箱的限制
    - 灵活的时间窗口配置
    - 跨Serverless函数实例的持久化存储
    - 自动清理过期记录
    """

    # 速率限制规则配置
    RATE_LIMITS = {
        # 认证端点 - 防止暴力破解
        "auth_signin": {
            "max_requests": 5,
            "window_seconds": 60,
            "key_type": "ip"
        },
        "auth_signup": {
            "max_requests": 3,
            "window_seconds": 300,  # 5分钟
            "key_type": "ip"
        },

        # OTP端点 - 防止短信/邮件轰炸
        "auth_send_otp": {
            "max_requests": 3,
            "window_seconds": 3600,  # 1小时
            "key_type": "email"
        },
        "auth_verify_otp": {
            "max_requests": 5,
            "window_seconds": 300,  # 5分钟
            "key_type": "email"
        },

        # 密码重置 - 防止滥用
        "auth_reset_password": {
            "max_requests": 3,
            "window_seconds": 3600,  # 1小时
            "key_type": "ip"
        },

        # 支付端点 - 防止订单创建滥用
        "payment_create_order": {
            "max_requests": 10,
            "window_seconds": 3600,  # 1小时
            "key_type": "user_id"
        },

        # AI功能端点 - 防止资源滥用
        "plan_tasks": {
            "max_requests": 20,
            "window_seconds": 86400,  # 24小时
            "key_type": "user_id"
        },
        "generate_weekly_report": {
            "max_requests": 10,
            "window_seconds": 86400,  # 24小时
            "key_type": "user_id"
        },
        "chat_query": {
            "max_requests": 50,
            "window_seconds": 3600,  # 1小时
            "key_type": "user_id"
        }
    }

    def __init__(self):
        """初始化速率限制器"""
        if not SUPABASE_URL or not SUPABASE_KEY:
            print("[RATE_LIMITER] WARNING: Supabase未配置，速率限制功能禁用", file=sys.stderr)
            self.client = None
        else:
            try:
                self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
                print("[RATE_LIMITER] 初始化成功", file=sys.stderr)
            except Exception as e:
                print(f"[RATE_LIMITER] 初始化失败: {e}", file=sys.stderr)
                self.client = None

    def check_rate_limit(
        self,
        endpoint: str,
        identifier: str,
        identifier_type: Optional[str] = None
    ) -> Tuple[bool, Dict]:
        """
        检查速率限制

        Args:
            endpoint: API端点标识符（如 "auth_signin"）
            identifier: 限制键值（IP地址、用户ID或邮箱）
            identifier_type: 限制类型（"ip", "user_id", "email"），如果为None则使用默认配置

        Returns:
            (is_allowed, info):
                - is_allowed: 是否允许请求
                - info: 包含 remaining（剩余请求数）、reset_at（重置时间）等信息
        """
        # ✅ 安全降级：如果Supabase未配置，允许请求但记录警告
        if not self.client:
            print(f"[RATE_LIMITER] WARNING: 速率限制未启用，允许请求: {endpoint}", file=sys.stderr)
            return True, {"remaining": 999, "total": 999}

        # 获取速率限制规则
        rule = self.RATE_LIMITS.get(endpoint)
        if not rule:
            print(f"[RATE_LIMITER] WARNING: 未配置速率限制规则: {endpoint}，允许请求", file=sys.stderr)
            return True, {"remaining": 999, "total": 999}

        # 生成限制键
        key_type = identifier_type or rule["key_type"]
        limit_key = self._generate_key(endpoint, identifier, key_type)

        max_requests = rule["max_requests"]
        window_seconds = rule["window_seconds"]

        try:
            # 计算时间窗口
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=window_seconds)

            # 查询当前时间窗口内的请求数
            response = self.client.table("rate_limits").select("*").eq(
                "limit_key", limit_key
            ).gte("created_at", window_start.isoformat()).execute()

            current_count = len(response.data) if response.data else 0

            # 检查是否超过限制
            if current_count >= max_requests:
                # 计算重置时间
                if response.data:
                    oldest_request = min(response.data, key=lambda x: x["created_at"])
                    reset_at = datetime.fromisoformat(oldest_request["created_at"].replace("Z", "+00:00")) + timedelta(seconds=window_seconds)
                else:
                    reset_at = now + timedelta(seconds=window_seconds)

                print(f"[RATE_LIMITER] 🚫 速率限制触发: {endpoint}, key={limit_key}, {current_count}/{max_requests}", file=sys.stderr)

                return False, {
                    "remaining": 0,
                    "total": max_requests,
                    "reset_at": reset_at.isoformat(),
                    "retry_after": int((reset_at - now).total_seconds())
                }

            # 记录本次请求
            self.client.table("rate_limits").insert({
                "limit_key": limit_key,
                "endpoint": endpoint,
                "identifier": identifier,
                "identifier_type": key_type,
                "created_at": now.isoformat()
            }).execute()

            remaining = max_requests - current_count - 1

            print(f"[RATE_LIMITER] ✅ 允许请求: {endpoint}, key={limit_key}, {current_count + 1}/{max_requests}", file=sys.stderr)

            return True, {
                "remaining": remaining,
                "total": max_requests,
                "reset_at": (now + timedelta(seconds=window_seconds)).isoformat()
            }

        except Exception as e:
            print(f"[RATE_LIMITER] 检查速率限制失败: {e}", file=sys.stderr)
            # ✅ 安全降级：出错时允许请求，避免阻塞正常用户
            return True, {"remaining": 999, "total": 999}

    def _generate_key(self, endpoint: str, identifier: str, key_type: str) -> str:
        """
        生成限制键

        为了保护隐私，对标识符进行哈希处理
        """
        # 使用SHA256哈希，保护原始标识符（尤其是邮箱）
        identifier_hash = hashlib.sha256(identifier.encode()).hexdigest()[:16]
        return f"{endpoint}:{key_type}:{identifier_hash}"

    def cleanup_expired_records(self, hours: int = 24):
        """
        清理过期的速率限制记录

        Args:
            hours: 清理多少小时之前的记录

        Note:
            建议通过定时任务（如Vercel Cron Jobs）定期调用此方法
        """
        if not self.client:
            return

        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            result = self.client.table("rate_limits").delete().lt(
                "created_at", cutoff_time.isoformat()
            ).execute()

            deleted_count = len(result.data) if result.data else 0
            print(f"[RATE_LIMITER] 清理过期记录: {deleted_count}条 (>{hours}小时)", file=sys.stderr)

        except Exception as e:
            print(f"[RATE_LIMITER] 清理过期记录失败: {e}", file=sys.stderr)


def rate_limit_decorator(endpoint: str):
    """
    速率限制装饰器

    使用方法：
    ```python
    @rate_limit_decorator("auth_signin")
    def do_POST(self):
        # 请求处理逻辑
    ```

    注意：此装饰器需要在handler类的方法中使用，并且需要访问 self.client_address
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            limiter = RateLimiter()

            # 获取客户端IP（从X-Forwarded-For或直接获取）
            ip = self.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            if not ip:
                ip = self.client_address[0] if self.client_address else "unknown"

            # 检查速率限制
            is_allowed, info = limiter.check_rate_limit(endpoint, ip)

            if not is_allowed:
                # 返回429 Too Many Requests
                self.send_response(429)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Retry-After', str(info.get("retry_after", 60)))
                self.send_header('X-RateLimit-Limit', str(info.get("total", 0)))
                self.send_header('X-RateLimit-Remaining', '0')
                self.send_header('X-RateLimit-Reset', info.get("reset_at", ""))
                self.end_headers()

                import json
                error_response = {
                    "success": False,
                    "error": "Too many requests. Please try again later.",
                    "retry_after": info.get("retry_after", 60)
                }
                self.wfile.write(json.dumps(error_response).encode('utf-8'))
                return

            # 添加速率限制响应头
            original_send_response = self.send_response
            def patched_send_response(code, message=None):
                original_send_response(code, message)
                self.send_header('X-RateLimit-Limit', str(info.get("total", 0)))
                self.send_header('X-RateLimit-Remaining', str(info.get("remaining", 0)))
                self.send_header('X-RateLimit-Reset', info.get("reset_at", ""))
            self.send_response = patched_send_response

            # 调用原始方法
            return func(self, *args, **kwargs)

        return wrapper
    return decorator
