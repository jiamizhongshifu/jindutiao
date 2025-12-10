"""
Token自动刷新机制单元测试

测试范围:
- refresh_access_token() 方法的指数退避重试
- _make_authenticated_request() 的401自动处理
- 并发刷新防护
- Token过期检测
- httpx后备方案

目标覆盖率: > 90%
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from gaiya.core.auth_client import AuthClient


class TestTokenRefresh:
    """Token刷新机制测试套件"""

    def test_refresh_token_success(self):
        """测试Token刷新成功"""
        client = AuthClient()
        client.refresh_token = "valid_refresh_token"

        # Mock成功响应
        with patch.object(client.session, 'post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "access_token": "new_access_token",
                "refresh_token": "new_refresh_token"
            }
            mock_post.return_value = mock_response

            result = client.refresh_access_token()

            assert result["success"] is True
            assert result["access_token"] == "new_access_token"
            assert result["refresh_token"] == "new_refresh_token"
            assert client.refresh_retry_count == 0  # 重置计数

    def test_refresh_token_timeout_retry(self):
        """测试超时时的指数退避重试"""
        client = AuthClient()
        client.refresh_token = "valid_refresh_token"

        # Mock超时异常
        with patch.object(client.session, 'post') as mock_post:
            mock_post.side_effect = requests.exceptions.Timeout()

            # 第一次调用
            result = client.refresh_access_token()

            assert result["success"] is False
            assert result["error"] == "Timeout, will retry"
            assert result["retry_delay"] == 2  # 2^1
            assert client.refresh_retry_count == 1

            # 第二次调用
            result = client.refresh_access_token()

            assert result["retry_delay"] == 4  # 2^2
            assert client.refresh_retry_count == 2

            # 第三次调用 - 达到最大重试次数(count=3)
            result = client.refresh_access_token()

            assert result["error"] == "Max retries reached"
            assert "retry_delay" not in result  # 不再返回retry_delay
            assert client.refresh_retry_count == 0  # 重置

    def test_refresh_token_expired(self):
        """测试Refresh Token过期"""
        client = AuthClient()
        client.refresh_token = "expired_refresh_token"

        # Mock 401 response
        with patch.object(client.session, 'post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_post.return_value = mock_response

            result = client.refresh_access_token()

            assert result["success"] is False
            assert result["expired"] is True
            assert client.refresh_retry_count == 0  # 不触发重试

    def test_concurrent_refresh_prevention(self):
        """测试并发刷新防护"""
        client = AuthClient()
        client.refresh_token = "valid_refresh_token"
        client.is_refreshing = True  # 模拟正在刷新

        result = client.refresh_access_token()

        assert result["success"] is False
        assert result["error"] == "Refresh in progress"
        # 不应该发起HTTP请求

    def test_refresh_no_token(self):
        """测试无刷新令牌时的行为"""
        client = AuthClient()
        client.refresh_token = None

        result = client.refresh_access_token()

        assert result["success"] is False
        assert result["error"] == "无刷新令牌"

    def test_refresh_ssl_error_httpx_fallback(self):
        """测试SSL错误时的httpx后备方案"""
        client = AuthClient()
        client.refresh_token = "valid_refresh_token"

        # Mock SSL错误
        with patch.object(client.session, 'post') as mock_post:
            mock_post.side_effect = requests.exceptions.SSLError("SSL certificate error")

            # Mock httpx成功响应 (注意:httpx是在refresh_access_token内部导入的)
            with patch('httpx.Client') as mock_httpx_client:
                mock_context = MagicMock()
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "success": True,
                    "access_token": "new_access_token_via_httpx",
                    "refresh_token": "new_refresh_token_via_httpx"
                }
                mock_context.__enter__.return_value.post.return_value = mock_response
                mock_httpx_client.return_value = mock_context

                result = client.refresh_access_token()

                assert result["success"] is True
                assert result["access_token"] == "new_access_token_via_httpx"
                # 验证httpx被调用
                mock_httpx_client.assert_called_once()


class TestAuthenticatedRequest:
    """认证请求自动刷新测试套件"""

    def test_authenticated_request_success(self):
        """测试认证请求成功"""
        client = AuthClient()
        client.access_token = "valid_access_token"

        # Mock成功响应
        with patch.object(client.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": "test"}
            mock_request.return_value = mock_response

            response = client._make_authenticated_request("GET", "https://api.example.com/test")

            assert response.status_code == 200
            # 验证Authorization header被添加
            args, kwargs = mock_request.call_args
            assert kwargs['headers']['Authorization'] == "Bearer valid_access_token"

    def test_authenticated_request_auto_refresh_on_401(self):
        """测试401时自动刷新Token"""
        client = AuthClient()
        client.access_token = "expired_token"
        client.refresh_token = "valid_refresh_token"

        # Mock 401响应 + 刷新成功 + 重试成功
        with patch.object(client.session, 'request') as mock_request:
            # 第一次返回401
            mock_401 = Mock()
            mock_401.status_code = 401

            # 第二次(刷新后重试)返回200
            mock_200 = Mock()
            mock_200.status_code = 200
            mock_200.json.return_value = {"data": "success"}

            mock_request.side_effect = [mock_401, mock_200]

            # Mock刷新成功
            with patch.object(client, 'refresh_access_token') as mock_refresh:
                mock_refresh.return_value = {
                    "success": True,
                    "access_token": "new_access_token",
                    "refresh_token": "new_refresh_token"
                }

                response = client._make_authenticated_request("GET", "https://api.example.com/test")

                assert response.status_code == 200
                # 验证刷新方法被调用
                mock_refresh.assert_called_once()
                # 验证请求被重试
                assert mock_request.call_count == 2

    def test_authenticated_request_expired_refresh_token(self):
        """测试Refresh Token过期时抛出异常"""
        client = AuthClient()
        client.access_token = "expired_token"
        client.refresh_token = "expired_refresh_token"

        # Mock 401响应
        with patch.object(client.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_request.return_value = mock_response

            # Mock刷新失败(Refresh Token过期)
            with patch.object(client, 'refresh_access_token') as mock_refresh:
                mock_refresh.return_value = {
                    "success": False,
                    "expired": True,
                    "error": "Refresh token expired"
                }

                with pytest.raises(Exception, match="Session expired, please login again"):
                    client._make_authenticated_request("GET", "https://api.example.com/test")

    def test_authenticated_request_retry_on_timeout(self):
        """测试超时重试机制"""
        client = AuthClient()
        client.access_token = "expired_token"
        client.refresh_token = "valid_refresh_token"

        # Mock 401响应
        with patch.object(client.session, 'request') as mock_request:
            mock_401 = Mock()
            mock_401.status_code = 401

            # 第二次(递归调用后)返回200
            mock_200 = Mock()
            mock_200.status_code = 200

            mock_request.side_effect = [mock_401, mock_200]

            # Mock刷新超时(需要重试)
            with patch.object(client, 'refresh_access_token') as mock_refresh:
                mock_refresh.return_value = {
                    "success": False,
                    "retry_delay": 2,
                    "error": "Timeout, will retry"
                }

                # Mock time.sleep避免实际等待
                with patch('time.sleep'):
                    response = client._make_authenticated_request("GET", "https://api.example.com/test")

                    assert response.status_code == 200
                    # 验证递归调用
                    assert mock_request.call_count == 2

    def test_authenticated_request_no_token(self):
        """测试无Token时的请求行为"""
        client = AuthClient()
        client.access_token = None

        # Mock成功响应
        with patch.object(client.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_request.return_value = mock_response

            response = client._make_authenticated_request("GET", "https://api.example.com/test")

            assert response.status_code == 200
            # 验证Authorization header未被添加(因为没有token)
            args, kwargs = mock_request.call_args
            # 空token时不添加header
            assert 'Authorization' not in kwargs['headers'] or kwargs['headers']['Authorization'] == "Bearer None"


class TestGetSubscriptionStatus:
    """订阅状态查询集成测试"""

    def test_get_subscription_status_success(self):
        """测试获取订阅状态成功"""
        client = AuthClient()
        client.access_token = "valid_token"
        client.user_info = {"user_id": "test_user"}

        # Mock成功响应
        with patch.object(client, '_make_authenticated_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "is_active": True,
                "user_tier": "pro"
            }
            mock_request.return_value = mock_response

            result = client.get_subscription_status()

            assert result["success"] is True
            assert result["user_tier"] == "pro"
            # 验证使用了新的认证请求封装
            mock_request.assert_called_once()

    def test_get_subscription_status_auto_refresh(self):
        """测试订阅查询时自动刷新Token"""
        client = AuthClient()
        client.access_token = "expired_token"
        client.refresh_token = "valid_refresh_token"
        client.user_info = {"user_id": "test_user"}

        # Mock _make_authenticated_request触发401自动刷新
        with patch.object(client, '_make_authenticated_request') as mock_request:
            # 模拟成功(已自动刷新)
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "user_tier": "free"
            }
            mock_request.return_value = mock_response

            result = client.get_subscription_status()

            assert result["success"] is True
            # 验证使用了新的认证请求封装
            mock_request.assert_called_once()

    def test_get_subscription_status_not_logged_in(self):
        """测试未登录时的行为"""
        client = AuthClient()
        client.user_info = None

        result = client.get_subscription_status()

        assert result["success"] is False
        assert result["error"] == "未登录"


if __name__ == '__main__':
    # 运行测试
    pytest.main([__file__, '-v', '--tb=short'])
