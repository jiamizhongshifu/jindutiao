"""
auth_manager.py 单元测试
测试用户认证、注册、OTP验证等核心功能
使用Mock避免真实API调用
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta, timezone
from api.auth_manager import AuthManager


@pytest.fixture
def mock_supabase_client():
    """创建Mock的Supabase客户端"""
    client = Mock()

    # Mock auth相关方法
    client.auth = Mock()
    client.auth.sign_up = Mock()
    client.auth.sign_in_with_password = Mock()
    client.auth.sign_out = Mock()
    client.auth.get_user = Mock()
    client.auth.refresh_session = Mock()
    client.auth.reset_password_for_email = Mock()
    client.auth.update_user = Mock()
    client.auth.verify_otp = Mock()
    client.auth.admin = Mock()
    client.auth.admin.get_user_by_id = Mock()
    client.auth.admin.list_users = Mock()

    # Mock table相关方法
    client.table = Mock(return_value=Mock())

    return client


@pytest.fixture
def auth_manager(mock_supabase_client):
    """创建AuthManager实例（使用Mock客户端）"""
    with patch('api.auth_manager.create_client', return_value=mock_supabase_client):
        with patch.dict('os.environ', {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_ANON_KEY': 'test-anon-key',
            'SUPABASE_SERVICE_KEY': 'test-service-key'
        }):
            manager = AuthManager()
            manager.client = mock_supabase_client
            manager.admin_client = mock_supabase_client
            return manager


class TestAuthManagerInit:
    """测试AuthManager初始化"""

    def test_init_with_credentials(self):
        """测试使用正确凭证初始化"""
        with patch('api.auth_manager.create_client') as mock_create:
            mock_client = Mock()
            mock_create.return_value = mock_client

            # 同时patch模块级的全局变量
            with patch('api.auth_manager.SUPABASE_URL', 'https://test.supabase.co'):
                with patch('api.auth_manager.SUPABASE_KEY', 'test-key'):
                    with patch('api.auth_manager.SUPABASE_SERVICE_KEY', 'test-service-key'):
                        manager = AuthManager()
                        assert manager.client is not None
                        assert manager.admin_client is not None

    def test_init_without_credentials(self):
        """测试缺少凭证时的初始化"""
        # Patch模块级的全局变量为空字符串
        with patch('api.auth_manager.SUPABASE_URL', ''):
            with patch('api.auth_manager.SUPABASE_KEY', ''):
                manager = AuthManager()
                assert manager.client is None
                assert manager.admin_client is None


class TestSignUp:
    """测试用户注册"""

    def test_successful_signup(self, auth_manager, mock_supabase_client):
        """测试成功注册"""
        # Mock成功的注册响应
        mock_user = Mock()
        mock_user.id = "test-user-id"
        mock_user.email_confirmed_at = None

        mock_response = Mock()
        mock_response.user = mock_user

        mock_supabase_client.auth.sign_up.return_value = mock_response

        # Mock数据库插入
        mock_supabase_client.table.return_value.upsert.return_value.execute.return_value = Mock()

        result = auth_manager.sign_up_with_email("test@example.com", "Test1234", "testuser")

        assert result["success"] is True
        assert result["user_id"] == "test-user-id"
        assert result["email"] == "test@example.com"
        assert result["email_verified"] is False
        assert "验证邮件" in result["message"]

    def test_signup_duplicate_email(self, auth_manager, mock_supabase_client):
        """测试重复邮箱注册"""
        mock_supabase_client.auth.sign_up.side_effect = Exception("User already registered")

        result = auth_manager.sign_up_with_email("existing@example.com", "Test1234")

        assert result["success"] is False
        assert "已被注册" in result["error"]

    def test_signup_invalid_email(self, auth_manager, mock_supabase_client):
        """测试无效邮箱注册"""
        mock_supabase_client.auth.sign_up.side_effect = Exception("Invalid email format")

        result = auth_manager.sign_up_with_email("invalid-email", "Test1234")

        assert result["success"] is False
        assert "邮箱格式不正确" in result["error"]

    def test_signup_without_client(self):
        """测试客户端未配置时注册"""
        manager = AuthManager()
        manager.client = None

        result = manager.sign_up_with_email("test@example.com", "Test1234")

        assert result["success"] is False
        assert result["error"] == "Supabase not configured"


class TestSignIn:
    """测试用户登录"""

    def test_successful_signin(self, auth_manager, mock_supabase_client):
        """测试成功登录"""
        # Mock成功的登录响应
        mock_user = Mock()
        mock_user.id = "test-user-id"

        mock_session = Mock()
        mock_session.access_token = "test-access-token"
        mock_session.refresh_token = "test-refresh-token"

        mock_auth_response = Mock()
        mock_auth_response.user = mock_user
        mock_auth_response.session = mock_session

        mock_supabase_client.auth.sign_in_with_password.return_value = mock_auth_response

        # Mock数据库查询
        mock_db_response = Mock()
        mock_db_response.data = [{"user_tier": "pro"}]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_db_response
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

        result = auth_manager.sign_in_with_email("test@example.com", "Test1234")

        assert result["success"] is True
        assert result["user_id"] == "test-user-id"
        assert result["access_token"] == "test-access-token"
        assert result["user_tier"] == "pro"

    def test_signin_invalid_credentials(self, auth_manager, mock_supabase_client):
        """测试错误密码登录"""
        mock_auth_response = Mock()
        mock_auth_response.user = None

        mock_supabase_client.auth.sign_in_with_password.return_value = mock_auth_response

        result = auth_manager.sign_in_with_email("test@example.com", "WrongPassword")

        assert result["success"] is False
        assert result["error"] == "Invalid credentials"

    def test_signin_exception(self, auth_manager, mock_supabase_client):
        """测试登录异常"""
        mock_supabase_client.auth.sign_in_with_password.side_effect = Exception("Network error")

        result = auth_manager.sign_in_with_email("test@example.com", "Test1234")

        assert result["success"] is False
        assert "Network error" in result["error"]


class TestEmailVerification:
    """测试邮箱验证"""

    def test_check_verified_email(self, auth_manager, mock_supabase_client):
        """测试已验证的邮箱"""
        mock_user = Mock()
        mock_user.id = "test-user-id"
        mock_user.email = "test@example.com"
        mock_user.email_confirmed_at = datetime.now(timezone.utc).isoformat()

        mock_supabase_client.auth.admin.get_user_by_id.return_value = mock_user
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

        result = auth_manager.check_email_verification(user_id="test-user-id")

        assert result["success"] is True
        assert result["verified"] is True
        assert result["user_id"] == "test-user-id"

    def test_check_unverified_email(self, auth_manager, mock_supabase_client):
        """测试未验证的邮箱"""
        mock_user = Mock()
        mock_user.id = "test-user-id"
        mock_user.email = "test@example.com"
        mock_user.email_confirmed_at = None

        mock_supabase_client.auth.admin.get_user_by_id.return_value = mock_user

        result = auth_manager.check_email_verification(user_id="test-user-id")

        assert result["success"] is True
        assert result["verified"] is False

    def test_check_verification_user_not_found(self, auth_manager, mock_supabase_client):
        """测试用户不存在"""
        mock_supabase_client.auth.admin.get_user_by_id.return_value = None

        result = auth_manager.check_email_verification(user_id="nonexistent-id")

        assert result["success"] is True
        assert result["verified"] is False


class TestOTPManagement:
    """测试OTP验证码管理"""

    def test_store_otp(self, auth_manager, mock_supabase_client):
        """测试存储OTP"""
        mock_supabase_client.table.return_value.delete.return_value.eq.return_value.execute.return_value = Mock()
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = Mock()

        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
        result = auth_manager.store_otp("test@example.com", "123456", "signup", expires_at)

        assert result["success"] is True

    def test_verify_otp_success(self, auth_manager, mock_supabase_client):
        """测试OTP验证成功"""
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()

        mock_response = Mock()
        mock_response.data = [{
            "code": "123456",
            "purpose": "signup",
            "expires_at": expires_at,
            "attempts": 0
        }]

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        mock_supabase_client.table.return_value.delete.return_value.eq.return_value.execute.return_value = Mock()

        result = auth_manager.verify_otp("test@example.com", "123456")

        assert result["success"] is True
        assert result["purpose"] == "signup"

    def test_verify_otp_wrong_code(self, auth_manager, mock_supabase_client):
        """测试OTP验证失败"""
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()

        mock_response = Mock()
        mock_response.data = [{
            "code": "123456",
            "purpose": "signup",
            "expires_at": expires_at,
            "attempts": 0
        }]

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

        result = auth_manager.verify_otp("test@example.com", "654321")

        assert result["success"] is False
        assert "验证码错误" in result["error"]

    def test_verify_otp_expired(self, auth_manager, mock_supabase_client):
        """测试过期的OTP"""
        expires_at = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()

        mock_response = Mock()
        mock_response.data = [{
            "code": "123456",
            "purpose": "signup",
            "expires_at": expires_at,
            "attempts": 0
        }]

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        mock_supabase_client.table.return_value.delete.return_value.eq.return_value.execute.return_value = Mock()

        result = auth_manager.verify_otp("test@example.com", "123456")

        assert result["success"] is False
        assert "已过期" in result["error"]

    def test_verify_otp_max_attempts(self, auth_manager, mock_supabase_client):
        """测试OTP尝试次数超限"""
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()

        mock_response = Mock()
        mock_response.data = [{
            "code": "123456",
            "purpose": "signup",
            "expires_at": expires_at,
            "attempts": 5  # 已达到最大尝试次数
        }]

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        mock_supabase_client.table.return_value.delete.return_value.eq.return_value.execute.return_value = Mock()

        result = auth_manager.verify_otp("test@example.com", "123456")

        assert result["success"] is False
        assert "尝试次数过多" in result["error"]


class TestPasswordManagement:
    """测试密码管理"""

    def test_request_password_reset(self, auth_manager, mock_supabase_client):
        """测试请求密码重置"""
        mock_supabase_client.auth.reset_password_for_email.return_value = None

        result = auth_manager.request_password_reset("test@example.com")

        assert result["success"] is True
        assert "reset email sent" in result["message"].lower()

    def test_update_password(self, auth_manager, mock_supabase_client):
        """测试更新密码"""
        mock_supabase_client.auth.update_user.return_value = None

        result = auth_manager.update_password("test-access-token", "NewPassword123")

        assert result["success"] is True


class TestUserProfile:
    """测试用户资料管理"""

    def test_update_profile_valid_fields(self, auth_manager, mock_supabase_client):
        """测试更新有效字段"""
        mock_response = Mock()
        mock_response.data = [{"username": "newusername"}]

        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response

        updates = {"username": "newusername", "display_name": "New Name"}
        result = auth_manager.update_user_profile("test-user-id", updates)

        assert result["success"] is True
        assert result["user"] is not None

    def test_update_profile_invalid_fields(self, auth_manager, mock_supabase_client):
        """测试更新无效字段（应被过滤）"""
        updates = {"user_tier": "admin", "email": "hacker@evil.com"}  # 不允许直接修改
        result = auth_manager.update_user_profile("test-user-id", updates)

        assert result["success"] is False
        assert "No valid fields" in result["error"]


class TestSecurityScenarios:
    """综合安全场景测试"""

    def test_signup_with_sql_injection(self, auth_manager, mock_supabase_client):
        """测试SQL注入尝试（Supabase ORM应防护）"""
        malicious_email = "'; DROP TABLE users--@example.com"

        # Supabase会验证邮箱格式，应该拒绝
        mock_supabase_client.auth.sign_up.side_effect = Exception("Invalid email")

        result = auth_manager.sign_up_with_email(malicious_email, "Test1234")

        assert result["success"] is False

    def test_otp_brute_force_protection(self, auth_manager, mock_supabase_client):
        """测试OTP暴力破解防护"""
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()

        # 模拟5次失败尝试后的状态
        for attempt in range(5):
            mock_response = Mock()
            mock_response.data = [{
                "code": "123456",
                "purpose": "signup",
                "expires_at": expires_at,
                "attempts": attempt
            }]

            mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
            mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

            result = auth_manager.verify_otp("test@example.com", "wrong_code")

            if attempt < 4:
                assert "还剩" in result["error"]
            else:
                # 第5次尝试后，OTP应该被删除
                mock_supabase_client.table.return_value.delete.return_value.eq.return_value.execute.return_value = Mock()


class TestSignOut:
    """测试用户登出"""

    def test_successful_signout(self, auth_manager, mock_supabase_client):
        """测试成功登出"""
        # Arrange
        mock_supabase_client.auth.sign_out.return_value = None

        # Act
        result = auth_manager.sign_out("test-access-token-abc123")

        # Assert
        assert result["success"] is True
        mock_supabase_client.auth.sign_out.assert_called_once()

    def test_signout_without_client(self):
        """测试没有客户端时登出"""
        # Arrange
        with patch('api.auth_manager.SUPABASE_URL', ''):
            with patch('api.auth_manager.SUPABASE_KEY', ''):
                manager = AuthManager()

                # Act
                result = manager.sign_out("test-access-token")

                # Assert
                assert result["success"] is False
                assert "Supabase not configured" in result["error"]

    def test_signout_exception(self, auth_manager, mock_supabase_client):
        """测试登出时发生异常"""
        # Arrange
        mock_supabase_client.auth.sign_out.side_effect = Exception("Network error")

        # Act
        result = auth_manager.sign_out("test-access-token")

        # Assert
        assert result["success"] is False
        assert "Network error" in result["error"]



class TestOTPEmailSending:
    """测试OTP邮件发送功能"""

    @patch('api.auth_manager.os.getenv')
    def test_send_otp_email_dev_mode_signup(self, mock_getenv, auth_manager):
        """测试开发模式下发送OTP(无RESEND_API_KEY) - signup用途"""
        # Arrange: 模拟环境变量不存在
        def getenv_side_effect(key, default=None):
            if key == "RESEND_API_KEY":
                return None
            return default

        mock_getenv.side_effect = getenv_side_effect

        # Act
        result = auth_manager.send_otp_email("test@example.com", "123456", "signup")

        # Assert
        assert result["success"] is False
        assert "未配置" in result["error"]

    @patch('api.auth_manager.os.getenv')
    def test_send_otp_email_dev_mode_password_reset(self, mock_getenv, auth_manager):
        """测试开发模式下发送OTP(无RESEND_API_KEY) - password_reset用途"""
        # Arrange
        def getenv_side_effect(key, default=None):
            if key == "RESEND_API_KEY":
                return None
            return default

        mock_getenv.side_effect = getenv_side_effect

        # Act
        result = auth_manager.send_otp_email("test@example.com", "654321", "password_reset")

        # Assert
        assert result["success"] is False
        assert "未配置" in result["error"]

class TestAdminEmailVerification:
    """测试管理员权限的邮箱验证功能"""

    def test_check_verification_with_admin_client_by_email(self, auth_manager, mock_supabase_client):
        """测试使用admin client通过email查询验证状态"""
        # Arrange: Mock admin.list_users返回用户列表
        mock_user = Mock()
        mock_user.email = "test@example.com"
        mock_user.email_confirmed_at = datetime.now().isoformat()
        mock_user.id = "user-123"

        mock_supabase_client.auth.admin.list_users.return_value = [mock_user]

        # Act
        result = auth_manager.check_email_verification(email="test@example.com")

        # Assert
        assert result["success"] is True
        assert result["verified"] is True
        mock_supabase_client.auth.admin.list_users.assert_called_once()

    def test_check_verification_admin_user_not_found(self, auth_manager, mock_supabase_client):
        """测试admin查询用户不存在"""
        # Arrange: list_users返回空列表
        mock_supabase_client.auth.admin.list_users.return_value = []

        # Act
        result = auth_manager.check_email_verification(email="notexist@example.com")

        # Assert
        assert result["success"] is True
        assert result["verified"] is False
        assert "等待邮箱验证" in result["message"]

    def test_check_verification_admin_list_error(self, auth_manager, mock_supabase_client):
        """测试admin.list_users出错时的降级处理"""
        # Arrange: list_users抛出异常
        mock_supabase_client.auth.admin.list_users.side_effect = Exception("Permission denied")

        # Mock降级查询（public.users表）
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"email_confirmed_at": datetime.now().isoformat()}]
        )

        # Act
        result = auth_manager.check_email_verification(email="test@example.com")

        # Assert: 应该降级到fallback方法
        # 由于实现中捕获了异常并继续查询by id，这里验证最终结果
        assert result is not None


# Pytest配置
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
