"""
测试logger_util模块

验证日志规范化功能:
- 日志级别控制
- 敏感信息脱敏
- 日志格式统一
- 环境变量配置
"""

import sys
import os
from pathlib import Path
from io import StringIO

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "api"))

# 导入被测试模块
from logger_util import get_logger, LogLevel, Logger


class TestLoggerSanitization:
    """测试敏感信息脱敏功能"""

    def test_sanitize_email(self):
        """测试邮箱地址脱敏"""
        logger = Logger("test")

        # 正常邮箱
        assert logger._sanitize_email("user@example.com") == "u***@example.com"
        assert logger._sanitize_email("john.doe@company.co.uk") == "j***@company.co.uk"

        # 短邮箱
        assert logger._sanitize_email("a@b.com") == "a@b.com"

        # 空值
        assert logger._sanitize_email("") == ""
        assert logger._sanitize_email(None) is None

    def test_sanitize_ip(self):
        """测试IP地址脱敏"""
        logger = Logger("test")

        # IPv4
        assert logger._sanitize_ip("192.168.1.100") == "192.168.***.***"
        assert logger._sanitize_ip("10.0.0.1") == "10.0.***.***"

        # IPv6
        assert logger._sanitize_ip("2001:0db8:85a3:0000:0000:8a2e:0370:7334") == "2001:0db8:***:***"

        # 空值
        assert logger._sanitize_ip("") == ""
        assert logger._sanitize_ip(None) is None

    def test_sanitize_token(self):
        """测试Token脱敏"""
        logger = Logger("test")

        # 长Token
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        sanitized = logger._sanitize_token(token)
        assert sanitized.startswith("eyJh...")
        assert sanitized.endswith("R8U***")

        # 短Token
        assert logger._sanitize_token("short") == "***"

    def test_sanitize_value_auto_detection(self):
        """测试根据键名自动脱敏"""
        logger = Logger("test")

        # 邮箱
        assert logger._sanitize_value("email", "user@example.com") == "u***@example.com"
        assert logger._sanitize_value("user_email", "test@test.com") == "t***@test.com"

        # IP
        assert logger._sanitize_value("client_ip", "192.168.1.1") == "192.168.***.***"
        assert logger._sanitize_value("ip_address", "10.0.0.1") == "10.0.***.***"

        # Token
        assert logger._sanitize_value("access_token", "long_token_value_here").endswith("***")
        assert logger._sanitize_value("api_key", "sk-1234567890").endswith("***")

        # UUID
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        sanitized_id = logger._sanitize_value("user_id", user_id)
        assert sanitized_id.startswith("550e8400")
        assert sanitized_id.endswith("***")

        # 普通值（不脱敏）
        assert logger._sanitize_value("plan_type", "pro_monthly") == "pro_monthly"
        assert logger._sanitize_value("amount", 29.0) == 29.0


class TestLoggerLevels:
    """测试日志级别控制"""

    def test_log_level_filtering(self, capsys):
        """测试日志级别过滤"""
        # 设置日志级别为WARNING
        os.environ["LOG_LEVEL"] = "WARNING"

        logger = Logger("test")

        # DEBUG和INFO不应显示
        logger.debug("This is debug")
        logger.info("This is info")

        # WARNING应该显示
        logger.warning("This is warning")

        # 清理环境变量
        os.environ.pop("LOG_LEVEL", None)

        # 捕获标准错误输出
        captured = capsys.readouterr()

        # 验证
        assert "This is debug" not in captured.err
        assert "This is info" not in captured.err
        assert "This is warning" in captured.err

    def test_default_log_level(self, capsys):
        """测试默认日志级别（INFO）"""
        # 清除环境变量
        os.environ.pop("LOG_LEVEL", None)

        logger = Logger("test")

        logger.debug("Debug message")
        logger.info("Info message")

        captured = capsys.readouterr()

        # DEBUG不显示，INFO显示
        assert "Debug message" not in captured.err
        assert "Info message" in captured.err


class TestLoggerFormat:
    """测试日志格式"""

    def test_log_message_format(self, capsys):
        """测试日志消息格式"""
        logger = Logger("auth-signin")

        logger.info("User login attempt", email="user@example.com", ip="192.168.1.1")

        captured = capsys.readouterr()

        # 验证格式：[时间戳] [级别] [模块名] 消息 key=value
        assert "[INFO]" in captured.err
        assert "[auth-signin]" in captured.err
        assert "User login attempt" in captured.err
        assert "email=u***@example.com" in captured.err
        assert "ip=192.168.***.***" in captured.err

    def test_log_with_multiple_params(self, capsys):
        """测试多个参数的日志"""
        logger = Logger("payment")

        logger.info(
            "Order created",
            user_id="550e8400-e29b-41d4-a716-446655440000",
            amount=29.0,
            plan_type="pro_monthly"
        )

        captured = capsys.readouterr()

        assert "Order created" in captured.err
        assert "user_id=550e8400***" in captured.err
        assert "amount=29.0" in captured.err
        assert "plan_type=pro_monthly" in captured.err


class TestLoggerVerboseMode:
    """测试详细模式（不脱敏）"""

    def test_verbose_mode_no_sanitization(self, capsys):
        """测试verbose模式下不脱敏"""
        # 开启verbose模式
        os.environ["LOG_VERBOSE"] = "true"

        logger = Logger("test")

        logger.info("Debug info", email="user@example.com", ip="192.168.1.1")

        # 清理环境变量
        os.environ.pop("LOG_VERBOSE", None)

        captured = capsys.readouterr()

        # verbose模式下应显示完整信息
        assert "email=user@example.com" in captured.err
        assert "ip=192.168.1.1" in captured.err


class TestGetLogger:
    """测试便捷函数"""

    def test_get_logger_function(self, capsys):
        """测试get_logger函数"""
        logger = get_logger("test-module")

        assert logger.module_name == "test-module"

        logger.info("Test message")

        captured = capsys.readouterr()
        assert "[test-module]" in captured.err


# ========================================
# 运行测试
# ========================================

if __name__ == "__main__":
    import pytest

    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
