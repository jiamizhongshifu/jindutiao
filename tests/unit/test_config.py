"""
测试config模块

验证配置管理功能:
- 环境变量读取
- 默认值处理
- CORS配置
- 价格配置
- 配置验证
"""

import sys
import os
from pathlib import Path
from decimal import Decimal

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "api"))

from config import Config


class TestBasicConfig:
    """测试基础配置"""

    def test_default_app_name(self):
        """测试默认应用名称"""
        # 清除环境变量
        os.environ.pop("APP_NAME", None)
        assert Config.get_app_name() == "GaiYa"

    def test_custom_app_name(self):
        """测试自定义应用名称"""
        os.environ["APP_NAME"] = "TestApp"
        assert Config.get_app_name() == "TestApp"
        os.environ.pop("APP_NAME", None)

    def test_default_environment(self):
        """测试默认环境"""
        os.environ.pop("ENVIRONMENT", None)
        assert Config.get_environment() == "production"
        assert Config.is_production() is True
        assert Config.is_development() is False

    def test_development_environment(self):
        """测试开发环境"""
        os.environ["ENVIRONMENT"] = "development"
        assert Config.is_development() is True
        assert Config.is_production() is False
        os.environ.pop("ENVIRONMENT", None)


class TestURLConfig:
    """测试URL配置"""

    def test_default_frontend_url(self):
        """测试默认前端URL"""
        os.environ.pop("FRONTEND_URL", None)
        assert Config.get_frontend_url() == "https://jindutiao.vercel.app"

    def test_custom_frontend_url(self):
        """测试自定义前端URL"""
        os.environ["FRONTEND_URL"] = "https://custom.app"
        assert Config.get_frontend_url() == "https://custom.app"
        os.environ.pop("FRONTEND_URL", None)

    def test_default_tuzi_url(self):
        """测试默认兔子API URL"""
        os.environ.pop("TUZI_BASE_URL", None)
        assert Config.get_tuzi_base_url() == "https://api.tu-zi.com/v1"

    def test_default_zpay_url(self):
        """测试默认Zpay URL"""
        os.environ.pop("ZPAY_API_URL", None)
        assert Config.get_zpay_api_url() == "https://zpayz.cn"


class TestCORSConfig:
    """测试CORS配置"""

    def test_default_cors_origins(self):
        """测试默认CORS源列表"""
        os.environ.pop("CORS_ALLOWED_ORIGINS", None)
        os.environ["ENVIRONMENT"] = "production"

        origins = Config.get_cors_allowed_origins()

        assert "https://jindutiao.vercel.app" in origins
        assert "https://gaiya.app" in origins
        assert "https://www.gaiya.app" in origins

        os.environ.pop("ENVIRONMENT", None)

    def test_custom_cors_origins(self):
        """测试自定义CORS源列表"""
        os.environ["CORS_ALLOWED_ORIGINS"] = "https://app1.com,https://app2.com"
        os.environ["ENVIRONMENT"] = "production"

        origins = Config.get_cors_allowed_origins()

        assert "https://app1.com" in origins
        assert "https://app2.com" in origins

        os.environ.pop("CORS_ALLOWED_ORIGINS", None)
        os.environ.pop("ENVIRONMENT", None)

    def test_development_cors_includes_localhost(self):
        """测试开发环境自动包含localhost"""
        os.environ.pop("CORS_ALLOWED_ORIGINS", None)
        os.environ["ENVIRONMENT"] = "development"

        origins = Config.get_cors_allowed_origins()

        assert "http://localhost:3000" in origins
        assert "http://localhost:5000" in origins
        assert "http://127.0.0.1:3000" in origins

        os.environ.pop("ENVIRONMENT", None)


class TestPlanPricesConfig:
    """测试订阅计划价格配置"""

    def test_default_plan_prices(self):
        """测试默认价格"""
        os.environ.pop("PLAN_PRICE_PRO_MONTHLY", None)
        os.environ.pop("PLAN_PRICE_PRO_YEARLY", None)
        os.environ.pop("PLAN_PRICE_LIFETIME", None)

        prices = Config.get_plan_prices()

        assert prices["pro_monthly"] == Decimal("29.0")
        assert prices["pro_yearly"] == Decimal("199.0")
        assert prices["lifetime"] == Decimal("1200.0")

    def test_custom_plan_prices(self):
        """测试自定义价格"""
        os.environ["PLAN_PRICE_PRO_MONTHLY"] = "39.0"
        os.environ["PLAN_PRICE_PRO_YEARLY"] = "299.0"

        prices = Config.get_plan_prices()

        assert prices["pro_monthly"] == Decimal("39.0")
        assert prices["pro_yearly"] == Decimal("299.0")

        os.environ.pop("PLAN_PRICE_PRO_MONTHLY", None)
        os.environ.pop("PLAN_PRICE_PRO_YEARLY", None)

    def test_get_plan_price(self):
        """测试获取单个计划价格"""
        os.environ.pop("PLAN_PRICE_PRO_MONTHLY", None)

        price = Config.get_plan_price("pro_monthly")
        assert price == Decimal("29.0")

        # 无效计划
        invalid_price = Config.get_plan_price("invalid_plan")
        assert invalid_price is None

    def test_is_valid_plan(self):
        """测试计划有效性检查"""
        assert Config.is_valid_plan("pro_monthly") is True
        assert Config.is_valid_plan("pro_yearly") is True
        assert Config.is_valid_plan("lifetime") is True
        assert Config.is_valid_plan("invalid_plan") is False


class TestPaymentConfig:
    """测试支付配置"""

    def test_zpay_not_configured_by_default(self):
        """测试Zpay默认未配置"""
        os.environ.pop("ZPAY_PID", None)
        os.environ.pop("ZPAY_PKEY", None)

        assert Config.is_zpay_configured() is False

    def test_zpay_configured(self):
        """测试Zpay已配置"""
        os.environ["ZPAY_PID"] = "test_pid"
        os.environ["ZPAY_PKEY"] = "test_pkey"

        assert Config.is_zpay_configured() is True
        assert Config.get_zpay_pid() == "test_pid"
        assert Config.get_zpay_pkey() == "test_pkey"

        os.environ.pop("ZPAY_PID", None)
        os.environ.pop("ZPAY_PKEY", None)


class TestLogConfig:
    """测试日志配置"""

    def test_default_log_level(self):
        """测试默认日志级别"""
        os.environ.pop("LOG_LEVEL", None)
        assert Config.get_log_level() == "INFO"

    def test_custom_log_level(self):
        """测试自定义日志级别"""
        os.environ["LOG_LEVEL"] = "DEBUG"
        assert Config.get_log_level() == "DEBUG"
        os.environ.pop("LOG_LEVEL", None)

    def test_log_verbose_default(self):
        """测试日志详细模式默认关闭"""
        os.environ.pop("LOG_VERBOSE", None)
        assert Config.is_log_verbose() is False

    def test_log_verbose_enabled(self):
        """测试启用日志详细模式"""
        os.environ["LOG_VERBOSE"] = "true"
        assert Config.is_log_verbose() is True
        os.environ.pop("LOG_VERBOSE", None)


class TestSecurityConfig:
    """测试安全配置"""

    def test_ssl_verify_enabled_by_default(self):
        """测试SSL验证默认启用"""
        os.environ.pop("DISABLE_SSL_VERIFY", None)
        assert Config.is_ssl_verify_disabled() is False

    def test_ssl_verify_disabled(self):
        """测试禁用SSL验证"""
        os.environ["DISABLE_SSL_VERIFY"] = "true"
        assert Config.is_ssl_verify_disabled() is True
        os.environ.pop("DISABLE_SSL_VERIFY", None)


class TestConfigValidation:
    """测试配置验证"""

    def test_validate_with_required_configs(self):
        """测试必需配置都存在"""
        os.environ["SUPABASE_URL"] = "https://test.supabase.co"
        os.environ["SUPABASE_KEY"] = "test_key"

        is_valid, missing = Config.validate_required_configs()

        assert is_valid is True
        assert len(missing) == 0

        os.environ.pop("SUPABASE_URL", None)
        os.environ.pop("SUPABASE_KEY", None)

    def test_validate_with_missing_configs(self):
        """测试缺少必需配置"""
        os.environ.pop("SUPABASE_URL", None)
        os.environ.pop("SUPABASE_KEY", None)

        is_valid, missing = Config.validate_required_configs()

        assert is_valid is False
        assert "SUPABASE_URL" in missing
        assert "SUPABASE_KEY" in missing


# ========================================
# 运行测试
# ========================================

if __name__ == "__main__":
    import pytest

    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
