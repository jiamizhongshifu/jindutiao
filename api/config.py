"""
统一配置管理模块

✅ 安全修复 (Priority 12): 配置管理
- 移除硬编码配置
- 统一使用环境变量
- 集中管理配置项
- 提供默认值和验证
"""
import os
from typing import Dict, List, Optional
from decimal import Decimal


class Config:
    """应用配置管理类"""

    # ========================================
    # 应用基础配置
    # ========================================

    @staticmethod
    def get_app_name() -> str:
        """获取应用名称"""
        return os.getenv("APP_NAME", "GaiYa")

    @staticmethod
    def get_app_version() -> str:
        """获取应用版本"""
        return os.getenv("APP_VERSION", "1.0.0")

    @staticmethod
    def get_environment() -> str:
        """获取运行环境（development/staging/production）"""
        return os.getenv("ENVIRONMENT", "production")

    @staticmethod
    def is_production() -> bool:
        """判断是否为生产环境"""
        return Config.get_environment().lower() == "production"

    @staticmethod
    def is_development() -> bool:
        """判断是否为开发环境"""
        return Config.get_environment().lower() in ("development", "dev")

    # ========================================
    # 前端域名配置
    # ========================================

    @staticmethod
    def get_frontend_url() -> str:
        """获取前端基础URL（用于支付回调等）"""
        return os.getenv("FRONTEND_URL", "https://jindutiao.vercel.app")

    @staticmethod
    def get_cors_allowed_origins() -> List[str]:
        """
        获取CORS允许的源列表

        环境变量:
            CORS_ALLOWED_ORIGINS: 逗号分隔的域名列表
            例如: "https://gaiya.app,https://www.gaiya.app,http://localhost:3000"

        Returns:
            允许的源列表
        """
        # 从环境变量读取（逗号分隔）
        env_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")

        if env_origins:
            origins = [origin.strip() for origin in env_origins.split(",")]
        else:
            # 默认值
            origins = [
                "https://jindutiao.vercel.app",
                "https://gaiya.app",
                "https://www.gaiya.app",
            ]

        # 开发环境自动添加本地域名
        if Config.is_development():
            local_origins = [
                "http://localhost:3000",
                "http://localhost:5000",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5000",
            ]
            origins.extend(local_origins)

        return list(set(origins))  # 去重

    # ========================================
    # 第三方服务配置
    # ========================================

    # 兔子AI API
    @staticmethod
    def get_tuzi_base_url() -> str:
        """获取兔子AI API基础URL"""
        return os.getenv("TUZI_BASE_URL", "https://api.tu-zi.com/v1")

    @staticmethod
    def get_tuzi_api_key() -> Optional[str]:
        """获取兔子AI API密钥"""
        return os.getenv("TUZI_API_KEY")

    # Zpay支付网关
    @staticmethod
    def get_zpay_api_url() -> str:
        """获取Zpay API基础URL"""
        return os.getenv("ZPAY_API_URL", "https://zpayz.cn")

    @staticmethod
    def get_zpay_pid() -> Optional[str]:
        """获取Zpay商户ID"""
        return os.getenv("ZPAY_PID")

    @staticmethod
    def get_zpay_pkey() -> Optional[str]:
        """获取Zpay商户密钥"""
        return os.getenv("ZPAY_PKEY")

    @staticmethod
    def is_zpay_configured() -> bool:
        """检查Zpay是否已配置"""
        return bool(Config.get_zpay_pid() and Config.get_zpay_pkey())

    # 邮箱服务
    @staticmethod
    def get_email_redirect_url() -> str:
        """获取邮箱验证后重定向URL"""
        return os.getenv("EMAIL_REDIRECT_URL", "https://api.gaiyatime.com/email-verified")

    # ========================================
    # 订阅计划和价格配置
    # ========================================

    @staticmethod
    def get_plan_prices() -> Dict[str, Decimal]:
        """
        获取订阅计划价格

        环境变量（可选）:
            PLAN_PRICE_PRO_MONTHLY: 月度会员价格（默认29.0）
            PLAN_PRICE_PRO_YEARLY: 年度会员价格（默认199.0）
            PLAN_PRICE_LIFETIME: 终身会员价格（默认1200.0）

        Returns:
            计划类型 -> 价格的映射字典
        """
        return {
            "pro_monthly": Decimal(os.getenv("PLAN_PRICE_PRO_MONTHLY", "29.0")),
            "pro_yearly": Decimal(os.getenv("PLAN_PRICE_PRO_YEARLY", "199.0")),
            "lifetime": Decimal(os.getenv("PLAN_PRICE_LIFETIME", "1200.0")),
        }

    @staticmethod
    def get_plan_price(plan_type: str) -> Optional[Decimal]:
        """
        获取指定计划的价格

        Args:
            plan_type: 计划类型（pro_monthly/pro_yearly/lifetime）

        Returns:
            价格（Decimal），如果计划不存在返回None
        """
        prices = Config.get_plan_prices()
        return prices.get(plan_type)

    @staticmethod
    def is_valid_plan(plan_type: str) -> bool:
        """检查计划类型是否有效"""
        return plan_type in Config.get_plan_prices()

    # ========================================
    # 日志配置
    # ========================================

    @staticmethod
    def get_log_level() -> str:
        """获取日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL）"""
        return os.getenv("LOG_LEVEL", "INFO").upper()

    @staticmethod
    def is_log_verbose() -> bool:
        """是否启用详细日志（不脱敏）"""
        return os.getenv("LOG_VERBOSE", "false").lower() == "true"

    # ========================================
    # 安全配置
    # ========================================

    @staticmethod
    def is_ssl_verify_disabled() -> bool:
        """是否禁用SSL验证（仅用于开发/测试）"""
        return os.getenv("DISABLE_SSL_VERIFY", "false").lower() == "true"

    @staticmethod
    def is_zpay_debug_mode() -> bool:
        """是否启用Zpay调试模式"""
        return os.getenv("ZPAY_DEBUG_MODE", "false").lower() == "true"

    # ========================================
    # 数据库配置
    # ========================================

    @staticmethod
    def get_supabase_url() -> Optional[str]:
        """获取Supabase项目URL"""
        return os.getenv("SUPABASE_URL")

    @staticmethod
    def get_supabase_key() -> Optional[str]:
        """获取Supabase匿名密钥"""
        return os.getenv("SUPABASE_KEY")

    @staticmethod
    def get_supabase_service_key() -> Optional[str]:
        """获取Supabase服务角色密钥（管理员权限）"""
        return os.getenv("SUPABASE_SERVICE_KEY")

    # ========================================
    # 速率限制配置
    # ========================================

    @staticmethod
    def get_rate_limit_default() -> int:
        """获取默认速率限制（次数/分钟）"""
        return int(os.getenv("RATE_LIMIT_DEFAULT", "10"))

    @staticmethod
    def get_rate_limit_auth() -> int:
        """获取认证相关API的速率限制"""
        return int(os.getenv("RATE_LIMIT_AUTH", "5"))

    @staticmethod
    def get_rate_limit_payment() -> int:
        """获取支付相关API的速率限制"""
        return int(os.getenv("RATE_LIMIT_PAYMENT", "3"))

    # ========================================
    # 配置验证
    # ========================================

    @staticmethod
    def validate_required_configs() -> tuple[bool, List[str]]:
        """
        验证所有必需的配置是否已设置

        Returns:
            (是否全部配置, 缺少的配置项列表)
        """
        missing = []

        # 检查数据库配置
        if not Config.get_supabase_url():
            missing.append("SUPABASE_URL")
        if not Config.get_supabase_key():
            missing.append("SUPABASE_KEY")

        # 检查支付配置（可选，仅在需要支付功能时）
        # if not Config.is_zpay_configured():
        #     missing.append("ZPAY_PID and ZPAY_PKEY")

        return len(missing) == 0, missing

    @staticmethod
    def print_config_summary():
        """打印配置摘要（仅开发环境，不输出敏感信息）"""
        if not Config.is_development():
            return

        print("=" * 60)
        print("Configuration Summary")
        print("=" * 60)
        print(f"Environment: {Config.get_environment()}")
        print(f"App Name: {Config.get_app_name()}")
        print(f"App Version: {Config.get_app_version()}")
        print(f"Frontend URL: {Config.get_frontend_url()}")
        print(f"CORS Origins: {len(Config.get_cors_allowed_origins())} allowed")
        print(f"Tuzi API: {Config.get_tuzi_base_url()}")
        print(f"Zpay API: {Config.get_zpay_api_url()}")
        print(f"Zpay Configured: {Config.is_zpay_configured()}")
        print(f"Log Level: {Config.get_log_level()}")
        print(f"SSL Verify: {not Config.is_ssl_verify_disabled()}")

        # 验证必需配置
        is_valid, missing = Config.validate_required_configs()
        if not is_valid:
            print(f"⚠️ Missing required configs: {', '.join(missing)}")
        else:
            print("✅ All required configs are set")

        print("=" * 60)


# ========================================
# 便捷函数
# ========================================

# 创建全局配置实例
config = Config()

# 导出便捷函数
get_frontend_url = Config.get_frontend_url
get_cors_allowed_origins = Config.get_cors_allowed_origins
get_plan_prices = Config.get_plan_prices
get_plan_price = Config.get_plan_price
is_valid_plan = Config.is_valid_plan
get_zpay_api_url = Config.get_zpay_api_url
get_tuzi_base_url = Config.get_tuzi_base_url
