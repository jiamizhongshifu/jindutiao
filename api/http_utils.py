"""
HTTP请求/响应工具函数

✅ 安全修复 (Priority 11): 代码重复提取
- 统一HTTP请求解析逻辑
- 统一响应格式（成功/错误/速率限制）
- 减少代码重复，提高可维护性
"""
import json
import sys
from http.server import BaseHTTPRequestHandler
from typing import Optional, Dict, Any, Tuple
from logger_util import get_logger

logger = get_logger("http-utils")


def parse_request_body(handler: BaseHTTPRequestHandler) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    解析HTTP请求体

    Args:
        handler: HTTP请求处理器实例

    Returns:
        (解析后的JSON数据, 错误消息)
        如果成功返回 (data, None)
        如果失败返回 (None, error_message)

    Example:
        data, error = parse_request_body(self)
        if error:
            send_error_response(self, 400, error)
            return
    """
    try:
        # 1. 检查Content-Length
        content_length = int(handler.headers.get('Content-Length', 0))
        if content_length == 0:
            logger.warning("Empty request body", endpoint=handler.path)
            return None, "Empty request body"

        # 2. 读取请求体
        body = handler.rfile.read(content_length).decode('utf-8')

        # 3. 解析JSON
        data = json.loads(body)
        logger.debug("Request body parsed successfully", endpoint=handler.path)
        return data, None

    except UnicodeDecodeError as e:
        logger.error("Request body decode failed", endpoint=handler.path, error=str(e))
        return None, "Invalid request encoding"
    except json.JSONDecodeError as e:
        logger.error("JSON decode failed", endpoint=handler.path, error=str(e))
        return None, "Invalid JSON"
    except Exception as e:
        logger.error("Unexpected error parsing request", endpoint=handler.path, error=str(e))
        return None, f"Request parsing error: {str(e)}"


def send_success_response(
    handler: BaseHTTPRequestHandler,
    data: Dict[str, Any],
    rate_info: Optional[Dict[str, Any]] = None,
    status_code: int = 200
):
    """
    发送成功响应（包含速率限制响应头）

    Args:
        handler: HTTP请求处理器实例
        data: 响应数据（自动添加 success: True）
        rate_info: 速率限制信息（可选）
        status_code: HTTP状态码，默认200

    Example:
        send_success_response(self, {
            "message": "操作成功",
            "user_id": user_id
        }, rate_info)
    """
    try:
        # 1. 设置HTTP状态码
        handler.send_response(status_code)

        # 2. 设置响应头
        handler.send_header('Content-Type', 'application/json')
        handler.send_header('Access-Control-Allow-Origin', getattr(handler, 'allowed_origin', '*'))

        # 3. 添加速率限制响应头（如果提供）
        if rate_info:
            handler.send_header('X-RateLimit-Limit', str(rate_info.get("total", 0)))
            handler.send_header('X-RateLimit-Remaining', str(rate_info.get("remaining", 0)))
            handler.send_header('X-RateLimit-Reset', rate_info.get("reset_at", ""))

        handler.end_headers()

        # 4. 构造响应体
        response = {"success": True, **data}
        handler.wfile.write(json.dumps(response).encode('utf-8'))

        logger.debug("Success response sent", endpoint=handler.path, status=status_code)

    except Exception as e:
        logger.error("Failed to send success response", endpoint=handler.path, error=str(e))
        # 降级处理：发送简单的错误响应
        try:
            handler.send_response(500)
            handler.end_headers()
            handler.wfile.write(b'{"success": false, "error": "Response generation failed"}')
        except (OSError, BrokenPipeError):
            pass  # 连接已关闭，无法发送响应


def send_error_response(
    handler: BaseHTTPRequestHandler,
    status_code: int,
    message: str,
    rate_info: Optional[Dict[str, Any]] = None,
    details: Optional[Dict[str, Any]] = None
):
    """
    发送错误响应（包含速率限制响应头）

    Args:
        handler: HTTP请求处理器实例
        status_code: HTTP错误状态码（如400, 401, 500）
        message: 错误消息
        rate_info: 速率限制信息（可选）
        details: 额外的错误详情（可选）

    Example:
        send_error_response(self, 400, "Missing email", rate_info)
        send_error_response(self, 401, "Invalid credentials", details={"attempts_left": 2})
    """
    try:
        # 1. 设置HTTP状态码
        handler.send_response(status_code)

        # 2. 设置响应头
        handler.send_header('Content-Type', 'application/json')
        handler.send_header('Access-Control-Allow-Origin', getattr(handler, 'allowed_origin', '*'))

        # 3. 添加速率限制响应头（如果提供）
        if rate_info:
            handler.send_header('X-RateLimit-Limit', str(rate_info.get("total", 0)))
            handler.send_header('X-RateLimit-Remaining', str(rate_info.get("remaining", 0)))
            handler.send_header('X-RateLimit-Reset', rate_info.get("reset_at", ""))

        handler.end_headers()

        # 4. 构造错误响应体
        error_response = {
            "success": False,
            "error": message
        }

        # 添加额外详情（如果提供）
        if details:
            error_response.update(details)

        handler.wfile.write(json.dumps(error_response).encode('utf-8'))

        logger.warning("Error response sent", endpoint=handler.path, status=status_code, error_msg=message)

    except Exception as e:
        logger.critical("Failed to send error response", endpoint=handler.path, error=str(e))
        # 降级处理：发送纯文本错误
        try:
            handler.send_response(500)
            handler.end_headers()
            handler.wfile.write(b'Internal Server Error')
        except (OSError, BrokenPipeError):
            pass  # 连接已关闭，无法发送响应


def validate_required_fields(
    data: Dict[str, Any],
    required_fields: list,
    field_names: Optional[Dict[str, str]] = None
) -> Tuple[bool, Optional[str]]:
    """
    验证请求数据中的必需字段

    Args:
        data: 请求数据
        required_fields: 必需字段列表
        field_names: 字段的中文名称映射（可选），如 {"email": "邮箱", "password": "密码"}

    Returns:
        (验证是否通过, 错误消息)
        如果通过返回 (True, None)
        如果失败返回 (False, error_message)

    Example:
        is_valid, error = validate_required_fields(
            data,
            ["email", "password"],
            {"email": "邮箱", "password": "密码"}
        )
        if not is_valid:
            send_error_response(self, 400, error)
            return
    """
    field_names = field_names or {}
    missing_fields = []

    for field in required_fields:
        if field not in data or not data.get(field):
            # 使用中文名称（如果提供），否则使用英文字段名
            display_name = field_names.get(field, field)
            missing_fields.append(display_name)

    if missing_fields:
        if len(missing_fields) == 1:
            error_msg = f"Missing {missing_fields[0]}"
        else:
            error_msg = f"Missing fields: {', '.join(missing_fields)}"

        logger.warning("Required fields validation failed", missing=missing_fields)
        return False, error_msg

    return True, None


def handle_internal_error(
    handler: BaseHTTPRequestHandler,
    exception: Exception,
    context: str = ""
):
    """
    统一处理内部错误

    Args:
        handler: HTTP请求处理器实例
        exception: 异常对象
        context: 错误上下文描述（如 "processing payment"）

    Example:
        try:
            # ... 业务逻辑 ...
        except Exception as e:
            handle_internal_error(self, e, "processing user login")
            return
    """
    error_msg = f"Internal server error: {str(exception)}"

    logger.error(
        "Internal server error",
        endpoint=handler.path,
        context=context,
        error=str(exception),
        exception_type=type(exception).__name__
    )

    send_error_response(handler, 500, error_msg)


# ========================================
# 基类辅助（可选）
# ========================================

class BaseAPIHandler(BaseHTTPRequestHandler):
    """
    API处理器基类（可选使用）

    提供了通用的辅助方法，减少子类中的代码重复。
    子类可以继承此类并重写 do_POST/do_GET 方法。

    Example:
        class handler(BaseAPIHandler):
            def do_POST(self):
                # 解析请求体
                data, error = self.parse_body()
                if error:
                    return  # 错误已自动处理

                # 验证字段
                is_valid, error = self.validate_fields(
                    data,
                    ["email", "password"],
                    {"email": "邮箱", "password": "密码"}
                )
                if not is_valid:
                    return  # 错误已自动处理

                # 业务逻辑
                # ...

                # 发送成功响应
                self.send_success({"message": "操作成功"})
    """

    allowed_origin = '*'  # 可被子类覆盖

    def parse_body(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """解析请求体（自动处理错误）"""
        data, error = parse_request_body(self)
        if error:
            send_error_response(self, 400, error)
        return data, error

    def validate_fields(
        self,
        data: Dict[str, Any],
        required_fields: list,
        field_names: Optional[Dict[str, str]] = None
    ) -> Tuple[bool, Optional[str]]:
        """验证必需字段（自动处理错误）"""
        is_valid, error = validate_required_fields(data, required_fields, field_names)
        if not is_valid:
            send_error_response(self, 400, error)
        return is_valid, error

    def send_success(self, data: Dict[str, Any], rate_info: Optional[Dict[str, Any]] = None):
        """发送成功响应"""
        send_success_response(self, data, rate_info)

    def send_error(
        self,
        status_code: int,
        message: str,
        rate_info: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """发送错误响应"""
        send_error_response(self, status_code, message, rate_info, details)

    def handle_error(self, exception: Exception, context: str = ""):
        """处理内部错误"""
        handle_internal_error(self, exception, context)
