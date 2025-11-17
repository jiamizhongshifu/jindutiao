"""
测试 http_utils 模块

验证HTTP请求/响应工具函数的正确性:
- 请求体解析
- 成功/错误响应发送
- 字段验证
- 错误处理
"""

import sys
import os
import json
from pathlib import Path
from io import BytesIO
from http.server import BaseHTTPRequestHandler
from unittest.mock import MagicMock, patch

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "api"))

from http_utils import (
    parse_request_body,
    send_success_response,
    send_error_response,
    validate_required_fields,
    handle_internal_error,
    BaseAPIHandler
)


class MockHTTPHandler:
    """模拟HTTP请求处理器"""

    def __init__(self, body: bytes = b'', content_type: str = 'application/json'):
        self.headers = {'Content-Length': str(len(body))}
        self.rfile = BytesIO(body)
        self.wfile = BytesIO()
        self.path = '/test'
        self.allowed_origin = '*'
        self._response_code = None
        self._response_headers = {}

    def send_response(self, code):
        self._response_code = code

    def send_header(self, key, value):
        self._response_headers[key] = value

    def end_headers(self):
        pass

    def get_response_data(self):
        """获取响应数据"""
        return self.wfile.getvalue().decode('utf-8')

    def get_response_json(self):
        """获取响应JSON"""
        return json.loads(self.get_response_data())


class TestParseRequestBody:
    """测试请求体解析"""

    def test_parse_valid_json(self):
        """测试解析有效JSON"""
        handler = MockHTTPHandler(b'{"email": "test@example.com", "password": "Test123"}')
        data, error = parse_request_body(handler)

        assert error is None
        assert data == {"email": "test@example.com", "password": "Test123"}

    def test_parse_empty_body(self):
        """测试空请求体"""
        handler = MockHTTPHandler(b'')
        data, error = parse_request_body(handler)

        assert data is None
        assert error == "Empty request body"

    def test_parse_invalid_json(self):
        """测试无效JSON"""
        handler = MockHTTPHandler(b'{invalid json}')
        data, error = parse_request_body(handler)

        assert data is None
        assert error == "Invalid JSON"

    def test_parse_invalid_encoding(self):
        """测试无效编码"""
        # 使用无效的UTF-8字节序列
        handler = MockHTTPHandler(b'\xff\xfe')
        data, error = parse_request_body(handler)

        assert data is None
        assert "encoding" in error.lower()


class TestSendSuccessResponse:
    """测试成功响应发送"""

    def test_send_basic_success(self):
        """测试基本成功响应"""
        handler = MockHTTPHandler()
        send_success_response(handler, {"message": "操作成功"})

        assert handler._response_code == 200
        assert handler._response_headers['Content-Type'] == 'application/json'

        response = handler.get_response_json()
        assert response['success'] is True
        assert response['message'] == "操作成功"

    def test_send_success_with_rate_info(self):
        """测试带速率限制信息的成功响应"""
        handler = MockHTTPHandler()
        rate_info = {
            "total": 10,
            "remaining": 5,
            "reset_at": "2025-01-01T00:00:00Z"
        }
        send_success_response(handler, {"user_id": "123"}, rate_info)

        assert handler._response_headers['X-RateLimit-Limit'] == '10'
        assert handler._response_headers['X-RateLimit-Remaining'] == '5'
        assert handler._response_headers['X-RateLimit-Reset'] == '2025-01-01T00:00:00Z'

        response = handler.get_response_json()
        assert response['success'] is True
        assert response['user_id'] == "123"

    def test_send_success_custom_status(self):
        """测试自定义状态码的成功响应"""
        handler = MockHTTPHandler()
        send_success_response(handler, {"created": True}, status_code=201)

        assert handler._response_code == 201


class TestSendErrorResponse:
    """测试错误响应发送"""

    def test_send_basic_error(self):
        """测试基本错误响应"""
        handler = MockHTTPHandler()
        send_error_response(handler, 400, "Invalid input")

        assert handler._response_code == 400
        assert handler._response_headers['Content-Type'] == 'application/json'

        response = handler.get_response_json()
        assert response['success'] is False
        assert response['error'] == "Invalid input"

    def test_send_error_with_rate_info(self):
        """测试带速率限制信息的错误响应"""
        handler = MockHTTPHandler()
        rate_info = {
            "total": 10,
            "remaining": 0,
            "reset_at": "2025-01-01T00:00:00Z"
        }
        send_error_response(handler, 429, "Rate limit exceeded", rate_info)

        assert handler._response_code == 429
        assert handler._response_headers['X-RateLimit-Remaining'] == '0'

        response = handler.get_response_json()
        assert response['success'] is False
        assert response['error'] == "Rate limit exceeded"

    def test_send_error_with_details(self):
        """测试带额外详情的错误响应"""
        handler = MockHTTPHandler()
        details = {"attempts_left": 2, "locked_until": "2025-01-01T00:00:00Z"}
        send_error_response(handler, 401, "Invalid credentials", details=details)

        response = handler.get_response_json()
        assert response['success'] is False
        assert response['error'] == "Invalid credentials"
        assert response['attempts_left'] == 2
        assert response['locked_until'] == "2025-01-01T00:00:00Z"


class TestValidateRequiredFields:
    """测试必需字段验证"""

    def test_validate_all_fields_present(self):
        """测试所有字段都存在"""
        data = {"email": "test@example.com", "password": "Test123"}
        is_valid, error = validate_required_fields(data, ["email", "password"])

        assert is_valid is True
        assert error is None

    def test_validate_missing_single_field(self):
        """测试缺少单个字段"""
        data = {"email": "test@example.com"}
        is_valid, error = validate_required_fields(data, ["email", "password"])

        assert is_valid is False
        assert "password" in error

    def test_validate_missing_multiple_fields(self):
        """测试缺少多个字段"""
        data = {}
        is_valid, error = validate_required_fields(data, ["email", "password", "username"])

        assert is_valid is False
        assert "email" in error or "password" in error

    def test_validate_with_chinese_names(self):
        """测试使用中文字段名"""
        data = {"email": "test@example.com"}
        field_names = {"email": "邮箱", "password": "密码"}
        is_valid, error = validate_required_fields(data, ["email", "password"], field_names)

        assert is_valid is False
        assert "密码" in error

    def test_validate_empty_value(self):
        """测试空字符串值"""
        data = {"email": "", "password": "Test123"}
        is_valid, error = validate_required_fields(data, ["email", "password"])

        assert is_valid is False
        assert "email" in error


class TestHandleInternalError:
    """测试内部错误处理"""

    def test_handle_internal_error(self):
        """测试内部错误处理"""
        handler = MockHTTPHandler()
        exception = ValueError("Something went wrong")

        handle_internal_error(handler, exception, "processing payment")

        assert handler._response_code == 500

        response = handler.get_response_json()
        assert response['success'] is False
        assert "Internal server error" in response['error']


class TestBaseAPIHandler:
    """测试基类辅助方法"""

    def test_parse_body_success(self):
        """测试基类的请求体解析"""
        # 创建一个简单的处理器实例
        class TestHandler(BaseAPIHandler):
            def __init__(self):
                self.headers = {'Content-Length': '30'}
                self.rfile = BytesIO(b'{"email": "test@example.com"}')
                self.wfile = BytesIO()
                self.path = '/test'
                self._response_code = None
                self._response_headers = {}

            def send_response(self, code):
                self._response_code = code

            def send_header(self, key, value):
                self._response_headers[key] = value

            def end_headers(self):
                pass

        handler = TestHandler()
        data, error = handler.parse_body()

        # 成功解析
        assert error is None
        assert data['email'] == "test@example.com"

    def test_validate_fields_success(self):
        """测试基类的字段验证"""
        class TestHandler(BaseAPIHandler):
            def __init__(self):
                self.wfile = BytesIO()
                self.path = '/test'
                self._response_code = None

            def send_response(self, code):
                self._response_code = code

            def send_header(self, key, value):
                pass

            def end_headers(self):
                pass

        handler = TestHandler()
        data = {"email": "test@example.com", "password": "Test123"}
        is_valid, error = handler.validate_fields(data, ["email", "password"])

        assert is_valid is True
        assert error is None


# ========================================
# 运行测试
# ========================================

if __name__ == "__main__":
    import pytest

    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
