"""
subscription_manager.py 单元测试
测试订阅管理、续费、过期检查等功能
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta, timezone
from api.subscription_manager import SubscriptionManager


@pytest.fixture
def mock_supabase_client():
    """创建Mock的Supabase客户端"""
    client = Mock()
    client.table = Mock(return_value=Mock())
    return client


@pytest.fixture
def subscription_manager(mock_supabase_client):
    """创建SubscriptionManager实例"""
    with patch('api.subscription_manager.create_client', return_value=mock_supabase_client):
        with patch.dict('os.environ', {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_ANON_KEY': 'test-key'
        }):
            manager = SubscriptionManager()
            manager.client = mock_supabase_client
            return manager


class TestSubscriptionManagerInit:
    """测试SubscriptionManager初始化"""

    def test_init_with_credentials(self):
        """测试使用正确凭证初始化"""
        with patch('api.subscription_manager.create_client') as mock_create:
            mock_client = Mock()
            mock_create.return_value = mock_client

            # 同时patch模块级的全局变量
            with patch('api.subscription_manager.SUPABASE_URL', 'https://test.supabase.co'):
                with patch('api.subscription_manager.SUPABASE_KEY', 'test-key'):
                    manager = SubscriptionManager()
                    assert manager.client is not None

    def test_init_without_credentials(self):
        """测试缺少凭证时的初始化"""
        # Patch模块级的全局变量为空字符串
        with patch('api.subscription_manager.SUPABASE_URL', ''):
            with patch('api.subscription_manager.SUPABASE_KEY', ''):
                manager = SubscriptionManager()
                assert manager.client is None

    def test_plan_prices(self):
        """测试订阅计划价格定义"""
        assert SubscriptionManager.PLANS["pro_monthly"]["price"] == 29.0
        assert SubscriptionManager.PLANS["pro_yearly"]["price"] == 199.0
        assert SubscriptionManager.PLANS["lifetime"]["price"] == 599.0


class TestCreateSubscription:
    """测试创建订阅"""

    def test_create_monthly_subscription(self, subscription_manager, mock_supabase_client):
        """测试创建月度订阅"""
        mock_sub_response = Mock()
        mock_sub_response.data = [{"id": "sub-123", "plan_type": "pro_monthly"}]

        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_sub_response
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

        result = subscription_manager.create_subscription(
            user_id="user-123",
            plan_type="pro_monthly",
            payment_id="pay-123"
        )

        assert result["success"] is True
        assert result["subscription"]["plan_type"] == "pro_monthly"

    def test_create_yearly_subscription(self, subscription_manager, mock_supabase_client):
        """测试创建年度订阅"""
        mock_sub_response = Mock()
        mock_sub_response.data = [{"id": "sub-123", "plan_type": "pro_yearly"}]

        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_sub_response
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

        result = subscription_manager.create_subscription(
            user_id="user-123",
            plan_type="pro_yearly",
            payment_id="pay-123"
        )

        assert result["success"] is True

    def test_create_lifetime_subscription(self, subscription_manager, mock_supabase_client):
        """测试创建终身订阅"""
        mock_sub_response = Mock()
        mock_sub_response.data = [{"id": "sub-123", "plan_type": "lifetime"}]

        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_sub_response
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

        result = subscription_manager.create_subscription(
            user_id="user-123",
            plan_type="lifetime",
            payment_id="pay-123"
        )

        assert result["success"] is True
        # 终身订阅应该设置user_tier为lifetime
        assert result["subscription"]["plan_type"] == "lifetime"

    def test_create_subscription_invalid_plan(self, subscription_manager):
        """测试创建无效的订阅计划"""
        result = subscription_manager.create_subscription(
            user_id="user-123",
            plan_type="invalid_plan",
            payment_id="pay-123"
        )

        assert result["success"] is False
        assert result["error"] == "Invalid plan type"

    def test_create_subscription_without_client(self):
        """测试客户端未配置时创建订阅"""
        manager = SubscriptionManager()
        manager.client = None

        result = manager.create_subscription(
            user_id="user-123",
            plan_type="pro_monthly",
            payment_id="pay-123"
        )

        assert result["success"] is False
        assert result["error"] == "Supabase not configured"


class TestGetUserSubscription:
    """测试获取用户订阅"""

    def test_get_active_subscription(self, subscription_manager, mock_supabase_client):
        """测试获取活跃订阅"""
        mock_response = Mock()
        mock_response.data = [{
            "id": "sub-123",
            "plan_type": "pro_monthly",
            "status": "active",
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        }]

        (mock_supabase_client.table.return_value.select.return_value
         .eq.return_value.eq.return_value.order.return_value
         .limit.return_value.execute.return_value) = mock_response

        subscription = subscription_manager.get_user_subscription("user-123")

        assert subscription is not None
        assert subscription["plan_type"] == "pro_monthly"

    def test_get_no_subscription(self, subscription_manager, mock_supabase_client):
        """测试用户无订阅"""
        mock_response = Mock()
        mock_response.data = []

        (mock_supabase_client.table.return_value.select.return_value
         .eq.return_value.eq.return_value.order.return_value
         .limit.return_value.execute.return_value) = mock_response

        subscription = subscription_manager.get_user_subscription("user-123")

        assert subscription is None


class TestCheckSubscriptionStatus:
    """测试订阅状态检查"""

    def test_active_subscription(self, subscription_manager, mock_supabase_client):
        """测试活跃订阅状态"""
        future_time = datetime.now(timezone.utc) + timedelta(days=30)

        mock_response = Mock()
        mock_response.data = [{
            "id": "sub-123",
            "plan_type": "pro_monthly",
            "status": "active",
            "expires_at": future_time.isoformat(),
            "auto_renew": True
        }]

        (mock_supabase_client.table.return_value.select.return_value
         .eq.return_value.eq.return_value.order.return_value
         .limit.return_value.execute.return_value) = mock_response

        status = subscription_manager.check_subscription_status("user-123")

        assert status["is_active"] is True
        assert status["user_tier"] == "pro"
        assert status["auto_renew"] is True

    def test_expired_subscription(self, subscription_manager, mock_supabase_client):
        """测试过期订阅"""
        past_time = datetime.now(timezone.utc) - timedelta(days=1)

        mock_response = Mock()
        mock_response.data = [{
            "id": "sub-123",
            "plan_type": "pro_monthly",
            "status": "active",
            "expires_at": past_time.isoformat()
        }]

        (mock_supabase_client.table.return_value.select.return_value
         .eq.return_value.eq.return_value.order.return_value
         .limit.return_value.execute.return_value) = mock_response

        # Mock _expire_subscription方法
        with patch.object(subscription_manager, '_expire_subscription'):
            status = subscription_manager.check_subscription_status("user-123")

            assert status["is_active"] is False
            assert status["user_tier"] == "free"

    def test_lifetime_subscription(self, subscription_manager, mock_supabase_client):
        """测试终身订阅（无过期时间）"""
        mock_response = Mock()
        mock_response.data = [{
            "id": "sub-123",
            "plan_type": "lifetime",
            "status": "active",
            "expires_at": None
        }]

        (mock_supabase_client.table.return_value.select.return_value
         .eq.return_value.eq.return_value.order.return_value
         .limit.return_value.execute.return_value) = mock_response

        status = subscription_manager.check_subscription_status("user-123")

        assert status["is_active"] is True
        assert status["user_tier"] == "lifetime"

    def test_no_subscription(self, subscription_manager, mock_supabase_client):
        """测试无订阅用户"""
        mock_response = Mock()
        mock_response.data = []

        (mock_supabase_client.table.return_value.select.return_value
         .eq.return_value.eq.return_value.order.return_value
         .limit.return_value.execute.return_value) = mock_response

        status = subscription_manager.check_subscription_status("user-123")

        assert status["is_active"] is False
        assert status["user_tier"] == "free"


class TestSubscriptionPricing:
    """测试订阅定价安全性"""

    def test_monthly_price_cannot_be_tampered(self, subscription_manager, mock_supabase_client):
        """测试月度订阅价格不能被篡改"""
        mock_sub_response = Mock()
        mock_sub_response.data = [{"id": "sub-123"}]

        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_sub_response
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

        # 即使支付ID指示支付了1元，实际价格应该由系统决定
        result = subscription_manager.create_subscription(
            user_id="user-123",
            plan_type="pro_monthly",
            payment_id="pay-1-yuan"  # 假设这是1元的支付
        )

        # 系统应该使用正确的价格（29元）
        insert_call = mock_supabase_client.table.return_value.insert.call_args
        inserted_data = insert_call[0][0]
        assert inserted_data["price"] == 29.0

    def test_yearly_price_is_server_side_determined(self, subscription_manager, mock_supabase_client):
        """测试年度订阅价格由服务端决定"""
        mock_sub_response = Mock()
        mock_sub_response.data = [{"id": "sub-123"}]

        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_sub_response
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

        result = subscription_manager.create_subscription(
            user_id="user-123",
            plan_type="pro_yearly",
            payment_id="pay-123"
        )

        # 验证价格由PLANS定义决定，不可篡改
        insert_call = mock_supabase_client.table.return_value.insert.call_args
        inserted_data = insert_call[0][0]
        assert inserted_data["price"] == 199.0


class TestSubscriptionDuration:
    """测试订阅时长计算"""

    def test_monthly_subscription_duration(self, subscription_manager, mock_supabase_client):
        """测试月度订阅时长"""
        mock_sub_response = Mock()
        mock_sub_response.data = [{"id": "sub-123"}]

        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_sub_response
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

        # 使用naive datetime以匹配subscription_manager的实现
        before_create = datetime.now()
        subscription_manager.create_subscription(
            user_id="user-123",
            plan_type="pro_monthly",
            payment_id="pay-123"
        )

        # 验证expires_at应该在30天后
        insert_call = mock_supabase_client.table.return_value.insert.call_args
        inserted_data = insert_call[0][0]
        # 解析ISO格式的datetime字符串（subscription_manager存储的是naive datetime）
        expires_at = datetime.fromisoformat(inserted_data["expires_at"])

        expected_expiry = before_create + timedelta(days=30)
        time_diff = abs((expires_at - expected_expiry).total_seconds())
        assert time_diff < 2  # 允许2秒误差

    def test_lifetime_subscription_no_expiry(self, subscription_manager, mock_supabase_client):
        """测试终身订阅无过期时间"""
        mock_sub_response = Mock()
        mock_sub_response.data = [{"id": "sub-123"}]

        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_sub_response
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

        subscription_manager.create_subscription(
            user_id="user-123",
            plan_type="lifetime",
            payment_id="pay-123"
        )

        insert_call = mock_supabase_client.table.return_value.insert.call_args
        inserted_data = insert_call[0][0]
        assert inserted_data["expires_at"] is None
        assert inserted_data["auto_renew"] is False


class TestUserTierUpgrade:
    """测试用户等级升级"""

    def test_upgrade_to_pro_monthly(self, subscription_manager, mock_supabase_client):
        """测试升级到Pro月度"""
        mock_sub_response = Mock()
        mock_sub_response.data = [{"id": "sub-123"}]

        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_sub_response
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

        subscription_manager.create_subscription(
            user_id="user-123",
            plan_type="pro_monthly",
            payment_id="pay-123"
        )

        # 验证用户等级被设置为pro
        update_call = mock_supabase_client.table.return_value.update.call_args
        updated_data = update_call[0][0]
        assert updated_data["user_tier"] == "pro"

    def test_upgrade_to_lifetime(self, subscription_manager, mock_supabase_client):
        """测试升级到终身会员"""
        mock_sub_response = Mock()
        mock_sub_response.data = [{"id": "sub-123"}]

        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_sub_response
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

        subscription_manager.create_subscription(
            user_id="user-123",
            plan_type="lifetime",
            payment_id="pay-123"
        )

        # 验证用户等级被设置为lifetime
        update_call = mock_supabase_client.table.return_value.update.call_args
        updated_data = update_call[0][0]
        assert updated_data["user_tier"] == "lifetime"


class TestQuotaUpdate:
    """测试配额更新"""

    def test_quota_updated_on_subscription(self, subscription_manager, mock_supabase_client):
        """测试订阅时更新配额"""
        mock_sub_response = Mock()
        mock_sub_response.data = [{"id": "sub-123"}]

        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_sub_response
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

        subscription_manager.create_subscription(
            user_id="user-123",
            plan_type="pro_monthly",
            payment_id="pay-123"
        )

        # 验证配额被更新（应该调用了2次update：1次user_tier，1次quota）
        assert mock_supabase_client.table.return_value.update.call_count >= 2


class TestSubscriptionExpiry:
    """测试订阅过期处理（_expire_subscription是私有方法）"""

    def test_expire_subscription_updates_status(self, subscription_manager, mock_supabase_client):
        """测试过期处理更新订阅状态"""
        # Arrange: Mock update操作
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

        # Act: 调用私有方法
        subscription_manager._expire_subscription("user-123", "sub-123")

        # Assert: 验证update被调用（订阅状态、用户等级、配额）
        assert mock_supabase_client.table.return_value.update.call_count >= 2

    def test_expire_subscription_downgrades_tier(self, subscription_manager, mock_supabase_client):
        """测试过期后降级用户等级"""
        # Arrange
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

        # Act
        subscription_manager._expire_subscription("user-123", "sub-123")

        # Assert: 验证用户等级被降级为free
        update_calls = mock_supabase_client.table.return_value.update.call_args_list
        assert any("free" in str(call) for call in update_calls)

    def test_expire_subscription_without_client(self):
        """测试没有客户端时过期处理"""
        # Arrange: 创建没有客户端的manager
        with patch('api.subscription_manager.SUPABASE_URL', ''):
            with patch('api.subscription_manager.SUPABASE_KEY', ''):
                manager = SubscriptionManager()

                # Act: 调用过期方法（应该安全返回，不抛出异常）
                manager._expire_subscription("user-123", "sub-123")

                # Assert: 没有异常即为成功


class TestCancelSubscription:
    """测试取消订阅"""

    def test_cancel_active_subscription(self, subscription_manager, mock_supabase_client):
        """测试取消活跃订阅"""
        # Arrange: Mock get_user_subscription返回活跃订阅
        mock_subscription = {
            "id": "sub-123",
            "user_id": "user-123",
            "plan_type": "pro_monthly",
            "status": "active"
        }

        # Mock get_user_subscription方法
        with patch.object(subscription_manager, 'get_user_subscription', return_value=mock_subscription):
            mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

            # Act
            result = subscription_manager.cancel_subscription("user-123", "User requested cancellation")

            # Assert
            assert result["success"] is True
            # 验证update被调用（订阅状态、用户等级、配额）
            assert mock_supabase_client.table.return_value.update.call_count >= 2

    def test_cancel_downgrades_to_free(self, subscription_manager, mock_supabase_client):
        """测试取消订阅后降级到免费版"""
        # Arrange
        mock_subscription = {
            "id": "sub-123",
            "user_id": "user-123",
            "plan_type": "pro_yearly",
            "status": "active"
        }

        with patch.object(subscription_manager, 'get_user_subscription', return_value=mock_subscription):
            mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

            # Act
            result = subscription_manager.cancel_subscription("user-123", "Downgrade request")

            # Assert
            assert result["success"] is True
            # 验证用户等级被降为free
            update_calls = mock_supabase_client.table.return_value.update.call_args_list
            assert any("free" in str(call) for call in update_calls)

    def test_cancel_no_active_subscription(self, subscription_manager, mock_supabase_client):
        """测试取消不存在的订阅"""
        # Arrange: Mock get_user_subscription返回None
        with patch.object(subscription_manager, 'get_user_subscription', return_value=None):
            # Act
            result = subscription_manager.cancel_subscription("user-123", "Test cancellation")

            # Assert
            assert result["success"] is False
            assert "not found" in result["error"].lower() or "no active" in result["error"].lower()


class TestAutoRenew:
    """测试自动续费开关"""

    def test_enable_auto_renew(self, subscription_manager, mock_supabase_client):
        """测试开启自动续费"""
        # Arrange: Mock非终身订阅
        mock_subscription = {
            "id": "sub-123",
            "user_id": "user-123",
            "plan_type": "pro_monthly",
            "auto_renew": False,
            "status": "active"
        }

        with patch.object(subscription_manager, 'get_user_subscription', return_value=mock_subscription):
            mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

            # Act
            result = subscription_manager.toggle_auto_renew("user-123", auto_renew=True)

            # Assert
            assert result["success"] is True
            assert result["auto_renew"] is True

    def test_disable_auto_renew(self, subscription_manager, mock_supabase_client):
        """测试关闭自动续费"""
        # Arrange
        mock_subscription = {
            "id": "sub-123",
            "user_id": "user-123",
            "plan_type": "pro_yearly",
            "auto_renew": True,
            "status": "active"
        }

        with patch.object(subscription_manager, 'get_user_subscription', return_value=mock_subscription):
            mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

            # Act
            result = subscription_manager.toggle_auto_renew("user-123", auto_renew=False)

            # Assert
            assert result["success"] is True
            assert result["auto_renew"] is False

    def test_toggle_auto_renew_no_subscription(self, subscription_manager, mock_supabase_client):
        """测试切换不存在订阅的自动续费"""
        # Arrange: Mock get_user_subscription返回None
        with patch.object(subscription_manager, 'get_user_subscription', return_value=None):
            # Act
            result = subscription_manager.toggle_auto_renew("user-123", auto_renew=True)

            # Assert
            assert result["success"] is False
            assert "not found" in result["error"].lower() or "no active" in result["error"].lower()

    def test_toggle_auto_renew_lifetime_not_allowed(self, subscription_manager, mock_supabase_client):
        """测试终身订阅不允许开启自动续费"""
        # Arrange: Mock终身订阅
        mock_subscription = {
            "id": "sub-lifetime",
            "user_id": "user-123",
            "plan_type": "lifetime",
            "status": "active"
        }

        with patch.object(subscription_manager, 'get_user_subscription', return_value=mock_subscription):
            # Act
            result = subscription_manager.toggle_auto_renew("user-123", auto_renew=True)

            # Assert
            assert result["success"] is False
            assert "lifetime" in result["error"].lower() or "don't need" in result["error"].lower()


class TestSubscriptionHistory:
    """测试订阅历史查询（返回列表而不是字典）"""

    def test_get_subscription_history_with_records(self, subscription_manager, mock_supabase_client):
        """测试获取有记录的订阅历史"""
        # Arrange: Mock历史订阅记录
        mock_history = [
            {
                "id": "sub-1",
                "plan_type": "pro_monthly",
                "status": "expired",
                "created_at": "2024-01-01T00:00:00",
                "expires_at": "2024-02-01T00:00:00"
            },
            {
                "id": "sub-2",
                "plan_type": "pro_yearly",
                "status": "active",
                "created_at": "2024-02-01T00:00:00",
                "expires_at": "2025-02-01T00:00:00"
            }
        ]

        mock_history_response = Mock()
        mock_history_response.data = mock_history
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_history_response

        # Act
        result = subscription_manager.get_subscription_history("user-123")

        # Assert: get_subscription_history直接返回列表
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["plan_type"] == "pro_monthly"

    def test_get_subscription_history_empty(self, subscription_manager, mock_supabase_client):
        """测试获取空的订阅历史"""
        # Arrange: Mock空历史
        mock_history_response = Mock()
        mock_history_response.data = []
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_history_response

        # Act
        result = subscription_manager.get_subscription_history("user-123")

        # Assert
        assert isinstance(result, list)
        assert result == []

    def test_get_subscription_history_without_client(self):
        """测试没有客户端时获取历史"""
        # Arrange: 创建没有客户端的manager
        with patch('api.subscription_manager.SUPABASE_URL', ''):
            with patch('api.subscription_manager.SUPABASE_KEY', ''):
                manager = SubscriptionManager()

                # Act
                result = manager.get_subscription_history("user-123")

                # Assert: 返回空列表
                assert result == []


class TestRenewalProcessing:
    """测试订阅续费处理"""

    def test_process_renewal_monthly_subscription(self, subscription_manager, mock_supabase_client):
        """测试处理月度订阅续费"""
        # Arrange: Mock当前订阅
        current_time = datetime.now()
        mock_subscription = {
            "id": "sub-123",
            "user_id": "user-123",
            "plan_type": "pro_monthly",
            "status": "active",
            "expires_at": (current_time - timedelta(days=1)).isoformat(),  # 已过期
            "auto_renew": True
        }

        # Mock select查询（返回旧订阅）
        mock_sub_response = Mock()
        mock_sub_response.data = [mock_subscription]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_sub_response

        # Mock insert（创建新订阅）
        mock_new_sub = {"id": "sub-new", "status": "active"}
        mock_insert_response = Mock()
        mock_insert_response.data = [mock_new_sub]
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_insert_response

        # Mock update（标记旧订阅为renewed）
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

        # Act
        result = subscription_manager.process_renewal("sub-123", "pay-renewal-123")

        # Assert
        assert result["success"] is True
        assert result["subscription"] is not None
        # 验证insert被调用（创建新订阅）
        mock_supabase_client.table.return_value.insert.assert_called_once()

    def test_process_renewal_yearly_subscription(self, subscription_manager, mock_supabase_client):
        """测试处理年度订阅续费"""
        # Arrange
        current_time = datetime.now()
        mock_subscription = {
            "id": "sub-456",
            "user_id": "user-456",
            "plan_type": "pro_yearly",
            "status": "active",
            "expires_at": (current_time - timedelta(days=1)).isoformat(),
            "auto_renew": True
        }

        mock_sub_response = Mock()
        mock_sub_response.data = [mock_subscription]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_sub_response

        mock_new_sub = {"id": "sub-new-yearly", "status": "active"}
        mock_insert_response = Mock()
        mock_insert_response.data = [mock_new_sub]
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_insert_response
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

        # Act
        result = subscription_manager.process_renewal("sub-456", "pay-renewal-456")

        # Assert
        assert result["success"] is True
        assert result["subscription"]["status"] == "active"

    def test_process_renewal_subscription_not_found(self, subscription_manager, mock_supabase_client):
        """测试续费不存在的订阅"""
        # Arrange: Mock空结果
        mock_sub_response = Mock()
        mock_sub_response.data = []
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_sub_response

        # Act
        result = subscription_manager.process_renewal("sub-nonexist", "pay-123")

        # Assert
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_process_renewal_lifetime_not_allowed(self, subscription_manager, mock_supabase_client):
        """测试终身订阅不能续费"""
        # Arrange: Mock终身订阅（duration_days为None）
        mock_subscription = {
            "id": "sub-lifetime",
            "user_id": "user-123",
            "plan_type": "lifetime",
            "status": "active",
            "expires_at": None
        }

        mock_sub_response = Mock()
        mock_sub_response.data = [mock_subscription]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_sub_response

        # Act
        result = subscription_manager.process_renewal("sub-lifetime", "pay-123")

        # Assert
        assert result["success"] is False
        assert "cannot renew" in result["error"].lower()


# Pytest配置
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
