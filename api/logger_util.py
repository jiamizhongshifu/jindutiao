"""
统一日志工具模块

✅ 安全修复 (Priority 10): 日志规范化
- 统一日志格式和级别
- 自动脱敏敏感信息（邮箱、IP、Token等）
- 结构化日志输出
- 可配置的详细程度（通过环境变量控制）

使用示例:
    from logger_util import get_logger

    logger = get_logger("auth-signin")
    logger.info("User login attempt", email="user@example.com")  # 自动脱敏
    logger.error("Login failed", error=str(e))
    logger.debug("Debug info", data=some_data)  # 仅在DEBUG模式显示
"""

import sys
import os
import re
from datetime import datetime
from typing import Any, Dict, Optional
from enum import Enum


class LogLevel(Enum):
    """日志级别"""
    DEBUG = 0    # 详细调试信息（仅开发环境）
    INFO = 1     # 一般信息（默认级别）
    WARNING = 2  # 警告信息
    ERROR = 3    # 错误信息
    CRITICAL = 4 # 严重错误


class Logger:
    """统一的日志记录器"""

    def __init__(self, module_name: str):
        """
        初始化日志记录器

        Args:
            module_name: 模块名称（如 "auth-signin", "payment-create-order"）
        """
        self.module_name = module_name

        # 从环境变量读取日志级别
        env_level = os.getenv("LOG_LEVEL", "INFO").upper()
        level_map = {
            "DEBUG": LogLevel.DEBUG,
            "INFO": LogLevel.INFO,
            "WARNING": LogLevel.WARNING,
            "ERROR": LogLevel.ERROR,
            "CRITICAL": LogLevel.CRITICAL
        }
        self.min_level = level_map.get(env_level, LogLevel.INFO)

        # 是否显示详细信息（敏感数据脱敏前的原始值）
        # ⚠️ 生产环境必须设置为 False
        self.verbose = os.getenv("LOG_VERBOSE", "false").lower() == "true"

    def _sanitize_email(self, email: str) -> str:
        """
        邮箱地址脱敏

        例如: user@example.com → u***@example.com
        """
        if not email or "@" not in email:
            return email

        local, domain = email.split("@", 1)
        if len(local) <= 1:
            sanitized_local = local
        else:
            sanitized_local = local[0] + "***"

        return f"{sanitized_local}@{domain}"

    def _sanitize_ip(self, ip: str) -> str:
        """
        IP地址脱敏

        例如: 192.168.1.100 → 192.168.***.***
        """
        if not ip:
            return ip

        # IPv4
        if "." in ip and ip.count(".") == 3:
            parts = ip.split(".")
            return "{}.{}.{}.{}".format(parts[0], parts[1], "***", "***")

        # IPv6 - 保留前两段
        if ":" in ip:
            parts = ip.split(":")
            if len(parts) >= 2:
                return f"{parts[0]}:{parts[1]}:***:***"

        return ip

    def _sanitize_token(self, token: str) -> str:
        """
        Token脱敏

        例如: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... → eyJh...VC***（前4+后3）
        """
        if not token or len(token) < 10:
            return "***"

        return f"{token[:4]}...{token[-3:]}***"

    def _sanitize_value(self, key: str, value: Any) -> Any:
        """
        根据键名自动脱敏值

        Args:
            key: 参数名
            value: 参数值

        Returns:
            脱敏后的值
        """
        if value is None:
            return None

        # 如果开启verbose模式，不脱敏（仅用于开发/调试）
        if self.verbose:
            return value

        value_str = str(value)

        # 邮箱地址
        if any(k in key.lower() for k in ["email", "mail"]):
            return self._sanitize_email(value_str)

        # IP地址
        if any(k in key.lower() for k in ["ip", "addr", "address"]) and "email" not in key.lower():
            return self._sanitize_ip(value_str)

        # Token/密钥/密码
        if any(k in key.lower() for k in ["token", "key", "password", "secret", "auth"]):
            return self._sanitize_token(value_str)

        # 用户ID（UUID格式） - 保留前8位
        if "user_id" in key.lower() or "id" in key.lower():
            if len(value_str) > 16 and "-" in value_str:  # 可能是UUID
                return f"{value_str[:8]}***"

        return value

    def _format_message(self, level: LogLevel, message: str, **kwargs) -> str:
        """
        格式化日志消息

        格式: [时间戳] [级别] [模块名] 消息 key1=value1 key2=value2

        Args:
            level: 日志级别
            message: 主要消息
            **kwargs: 附加的键值对参数

        Returns:
            格式化后的日志字符串
        """
        # 时间戳（ISO 8601格式，精确到毫秒）
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        # 级别标记
        level_str = level.name

        # 构建基础消息
        parts = [f"[{timestamp}]", f"[{level_str}]", f"[{self.module_name}]", message]

        # 添加键值对参数（自动脱敏）
        if kwargs:
            sanitized_params = []
            for key, value in kwargs.items():
                sanitized_value = self._sanitize_value(key, value)
                sanitized_params.append(f"{key}={sanitized_value}")

            parts.append(" | ".join(sanitized_params))

        return " ".join(parts)

    def _log(self, level: LogLevel, message: str, **kwargs):
        """
        内部日志输出方法

        Args:
            level: 日志级别
            message: 消息内容
            **kwargs: 附加参数
        """
        # 检查日志级别
        if level.value < self.min_level.value:
            return

        formatted_msg = self._format_message(level, message, **kwargs)
        print(formatted_msg, file=sys.stderr)

    def debug(self, message: str, **kwargs):
        """
        调试级别日志（仅在LOG_LEVEL=DEBUG时显示）

        用于详细的调试信息，生产环境不显示
        """
        self._log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """
        信息级别日志（默认级别）

        用于一般的操作记录（如用户登录、订单创建等）
        """
        self._log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """
        警告级别日志

        用于潜在问题（如速率限制触发、降级策略启用等）
        """
        self._log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """
        错误级别日志

        用于错误情况（如API调用失败、数据验证失败等）
        """
        self._log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """
        严重错误级别日志

        用于严重错误（如系统崩溃、数据损坏等）
        """
        self._log(LogLevel.CRITICAL, message, **kwargs)


# ========================================
# 便捷函数
# ========================================

def get_logger(module_name: str) -> Logger:
    """
    获取指定模块的日志记录器

    Args:
        module_name: 模块名称（如 "auth-signin"）

    Returns:
        Logger实例

    Example:
        logger = get_logger("auth-signin")
        logger.info("User login attempt", email="user@example.com", ip="192.168.1.1")

        输出:
        [2025-11-17T10:30:45.123Z] [INFO] [auth-signin] User login attempt email=u***@example.com | ip=192.168.***。***
    """
    return Logger(module_name)


# ========================================
# 遗留兼容性（逐步迁移时使用）
# ========================================

def legacy_log(module_name: str, message: str, level: str = "INFO"):
    """
    兼容旧的日志格式（逐步迁移期间使用）

    旧格式: print(f"[MODULE] message", file=sys.stderr)
    新格式: logger.info("message")

    Args:
        module_name: 模块名称
        message: 日志消息
        level: 日志级别（"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"）
    """
    logger = get_logger(module_name)
    level_map = {
        "DEBUG": logger.debug,
        "INFO": logger.info,
        "WARNING": logger.warning,
        "ERROR": logger.error,
        "CRITICAL": logger.critical
    }
    log_func = level_map.get(level.upper(), logger.info)
    log_func(message)
