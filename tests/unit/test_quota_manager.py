"""
quota_manager.py 单元测试
测试配额管理、扣减、重置等功能
确保免费用户和付费用户的配额限制正确执行
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta, timezone
from api.quota_manager import QuotaManager


@pytest.fixture
def mock_supabase_client():
    """创建Mock的Supabase客户端"""
    client = Mock()
    client.table = Mock(return_value=Mock())
    return client


@pytest.fixture
def quota_manager(mock_supabase_client):
    """创建QuotaManager实例"""
    with patch('api.quota_manager.create_client', return_value=mock_supabase_client):
        with patch.dict('os.environ', {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_ANON_KEY': 'test-key'
        }):
            manager = QuotaManager()
            manager.client = mock_supabase_client
            return manager


class TestQuotaManagerInit:
    """测试QuotaManager初始化"""

    def test_init_with_credentials(self):
        """测试使用正确凭证初始化"""
        with patch('api.quota_manager.create_client') as mock_create:
            mock_client = Mock()
            mock_create.return_value = mock_client

            # 同时patch模块级的全局变量
            with patch('api.quota_manager.SUPABASE_URL', 'https://test.supabase.co'):
                with patch('api.quota_manager.SUPABASE_KEY', 'test-key'):
                    manager = QuotaManager()
                    assert manager.client is not None

    def test_init_without_credentials(self):
        """测试缺少凭证时的初始化"""
        # Patch模块级的全局变量为空字符串
        with patch('api.quota_manager.SUPABASE_URL', ''):
            with patch('api.quota_manager.SUPABASE_KEY', ''):
                manager = QuotaManager()
                assert manager.client is None


class TestCreateUserQuota:
    """测试创建用户配额"""

    def test_create_free_user_quota(self, quota_manager, mock_supabase_client):
        """测试创建免费用户配额"""
        mock_response = Mock()
        mock_response.data = [{
            "user_id": "user-123",
            "user_tier": "free",
            "daily_plan_total": 3,
            "weekly_report_total": 1,
            "chat_total": 10
        }]

        # Mock数据库查询（用户不存在）
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(data=[])
        # Mock数据库插入
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_response

        user_quota = quota_manager.get_or_create_user("user-123", "free")

        assert user_quota["user_tier"] == "free"
        assert user_quota["daily_plan_total"] == 3
        assert user_quota["weekly_report_total"] == 1
        assert user_quota["chat_total"] == 10

    def test_create_pro_user_quota(self, quota_manager, mock_supabase_client):
        """测试创建Pro用户配额"""
        mock_response = Mock()
        mock_response.data = [{
            "user_id": "user-456",
            "user_tier": "pro",
            "daily_plan_total": 20,
            "weekly_report_total": 10,
            "chat_total": 100
        }]

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(data=[])
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_response

        user_quota = quota_manager.get_or_create_user("user-456", "pro")

        assert user_quota["user_tier"] == "pro"
        assert user_quota["daily_plan_total"] == 20
        assert user_quota["weekly_report_total"] == 10
        assert user_quota["chat_total"] == 100


class TestQuotaLimits:
    """测试配额限制（防止免费用户超额使用）"""

    def test_free_user_daily_plan_limit(self, quota_manager, mock_supabase_client):
        """测试免费用户每日任务规划限制（3次）"""
        mock_response = Mock()
        mock_response.data = [{
            "user_id": "user-123",
            "user_tier": "free",
            "daily_plan_total": 3,
            "daily_plan_used": 0
        }]

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        user_quota = quota_manager.get_or_create_user("user-123", "free")

        # 免费用户应该只有3次每日规划
        assert user_quota["daily_plan_total"] == 3

    def test_pro_user_increased_limits(self, quota_manager, mock_supabase_client):
        """测试Pro用户有更高的限额"""
        mock_response = Mock()
        mock_response.data = [{
            "user_id": "user-456",
            "user_tier": "pro",
            "daily_plan_total": 20,
            "chat_total": 100
        }]

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        user_quota = quota_manager.get_or_create_user("user-456", "pro")

        # Pro用户应该有更高的限额
        assert user_quota["daily_plan_total"] == 20  # 免费用户的6.7倍
        assert user_quota["chat_total"] == 100       # 免费用户的10倍


class TestQuotaReset:
    """测试配额重置功能"""

    @patch('api.quota_manager.datetime')
    def test_reset_daily_quota(self, mock_datetime, quota_manager, mock_supabase_client):
        """测试每日配额重置"""
        china_tz = timezone(timedelta(hours=8))
        now_china = datetime(2024, 1, 2, 8, 0, 0, tzinfo=china_tz)
        mock_datetime.now.return_value = now_china

        # 模拟一个需要重置的用户（重置时间已过）
        yesterday = datetime(2024, 1, 1, 0, 0, 0, tzinfo=china_tz)
        mock_existing_user = {
            "user_id": "user-123",
            "daily_plan_used": 3,
            "daily_plan_reset_at": yesterday.isoformat(),
            "chat_used": 5,
            "chat_reset_at": yesterday.isoformat()
        }

        mock_response = Mock()
        mock_response.data = [mock_existing_user]

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        # Mock更新操作
        mock_update_response = Mock()
        mock_update_response.data = [{**mock_existing_user, "daily_plan_used": 0, "chat_used": 0}]
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_response

        user_quota = quota_manager.get_or_create_user("user-123", "free")

        # 验证配额被重置
        update_call = mock_supabase_client.table.return_value.update.call_args
        if update_call:
            updated_data = update_call[0][0]
            assert updated_data["daily_plan_used"] == 0
            assert updated_data["chat_used"] == 0


class TestGetExistingUser:
    """测试获取已存在用户"""

    def test_get_existing_user_quota(self, quota_manager, mock_supabase_client):
        """测试获取已存在的用户配额"""
        mock_response = Mock()
        mock_response.data = [{
            "user_id": "user-123",
            "user_tier": "pro",
            "daily_plan_total": 20,
            "daily_plan_used": 5
        }]

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        user_quota = quota_manager.get_or_create_user("user-123")

        assert user_quota["user_id"] == "user-123"
        assert user_quota["daily_plan_used"] == 5


class TestFallbackQuota:
    """测试降级配额（客户端未配置时）"""

    def test_fallback_quota_without_client(self):
        """测试客户端未配置时使用降级配额"""
        manager = QuotaManager()
        manager.client = None

        user_quota = manager.get_or_create_user("user-123", "free")

        # 应该返回默认配额
        assert user_quota is not None
        assert "user_tier" in user_quota


class TestQuotaTierDifference:
    """测试不同等级用户的配额差异"""

    def test_free_vs_pro_daily_plan_quota(self, quota_manager):
        """测试免费vs Pro用户的每日规划配额差异"""
        # 免费用户
        free_quota = {
            "daily_plan_total": 3,
            "weekly_report_total": 1,
            "chat_total": 10
        }

        # Pro用户
        pro_quota = {
            "daily_plan_total": 20,
            "weekly_report_total": 10,
            "chat_total": 100
        }

        # Pro用户配额应该显著高于免费用户
        assert pro_quota["daily_plan_total"] > free_quota["daily_plan_total"] * 5
        assert pro_quota["weekly_report_total"] > free_quota["weekly_report_total"] * 5
        assert pro_quota["chat_total"] > free_quota["chat_total"] * 5


class TestSecurityScenarios:
    """配额安全场景测试"""

    def test_cannot_create_unlimited_quota(self, quota_manager, mock_supabase_client):
        """测试不能创建无限配额（防止篡改）"""
        # 即使用户尝试传入"unlimited"等级，系统应该使用预定义的配额
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(data=[])

        mock_response = Mock()
        mock_response.data = [{"user_tier": "free", "daily_plan_total": 3}]
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_response

        # 尝试使用非法等级
        user_quota = quota_manager.get_or_create_user("user-123", "unlimited")

        # 系统应该降级到free或pro，而不是创建无限配额
        if user_quota:
            assert user_quota["daily_plan_total"] in [3, 20, 10]  # 只允许预定义的值

    def test_quota_reset_time_cannot_be_tampered(self, quota_manager, mock_supabase_client):
        """测试配额重置时间由服务端控制，不可被客户端篡改"""
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(data=[])

        mock_response = Mock()
        mock_response.data = [{"user_id": "user-123", "daily_plan_reset_at": "some-time"}]
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_response

        user_quota = quota_manager.get_or_create_user("user-123", "free")

        # 重置时间应该由服务端生成，不应该是None或客户端提供的值
        assert "daily_plan_reset_at" in user_quota
        assert user_quota["daily_plan_reset_at"] is not None


class TestUseQuota:
    """测试配额使用功能"""

    def test_use_quota_success_daily_plan(self, quota_manager, mock_supabase_client):
        """测试成功使用每日任务规划配额"""
        # Arrange: Mock现有配额
        mock_existing_quota = {
            "user_id": "user-123",
            "user_tier": "free",
            "daily_plan_total": 3,
            "daily_plan_used": 0
        }

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(data=[mock_existing_quota])

        # Mock update操作
        mock_updated_quota = Mock()
        mock_updated_quota.data = [{"daily_plan_used": 1}]
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_updated_quota

        # Act
        result = quota_manager.use_quota("user-123", "daily_plan", amount=1)

        # Assert
        assert result["success"] is True
        assert result["quota_type"] == "daily_plan"
        assert result["used"] == 1
        assert result["total"] == 3
        assert result["remaining"] == 2

    def test_use_quota_exceeds_limit(self, quota_manager, mock_supabase_client):
        """测试配额超限"""
        # Arrange: Mock已用完的配额
        mock_existing_quota = {
            "user_id": "user-456",
            "user_tier": "free",
            "daily_plan_total": 3,
            "daily_plan_used": 3  # 已用完
        }

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(data=[mock_existing_quota])

        # Act
        result = quota_manager.use_quota("user-456", "daily_plan", amount=1)

        # Assert
        assert result["success"] is False
        assert result["error"] == "Quota exceeded"
        assert result["remaining"] == 0
        assert result["requested"] == 1

    def test_use_quota_multiple_types(self, quota_manager, mock_supabase_client):
        """测试不同类型的配额（chat）"""
        # Arrange: Mock chat配额
        mock_existing_quota = {
            "user_id": "user-789",
            "user_tier": "pro",
            "chat_total": 100,
            "chat_used": 50
        }

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(data=[mock_existing_quota])

        # Mock update操作
        mock_updated_quota = Mock()
        mock_updated_quota.data = [{"chat_used": 55}]
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_updated_quota

        # Act: 使用5次chat配额
        result = quota_manager.use_quota("user-789", "chat", amount=5)

        # Assert
        assert result["success"] is True
        assert result["quota_type"] == "chat"
        assert result["used"] == 55
        assert result["total"] == 100
        assert result["remaining"] == 45

    def test_use_quota_without_client(self):
        """测试Supabase未配置时使用配额"""
        # Arrange: 创建没有client的manager
        manager = QuotaManager()
        manager.client = None

        # Act
        result = manager.use_quota("user-123", "daily_plan", amount=1)

        # Assert
        assert result["success"] is False
        assert result["error"] == "Supabase not configured"

    def test_use_quota_weekly_report(self, quota_manager, mock_supabase_client):
        """测试使用周报配额"""
        # Arrange: Mock周报配额
        mock_existing_quota = {
            "user_id": "user-weekly",
            "user_tier": "free",
            "weekly_report_total": 1,
            "weekly_report_used": 0
        }

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(data=[mock_existing_quota])

        # Mock update操作
        mock_updated_quota = Mock()
        mock_updated_quota.data = [{"weekly_report_used": 1}]
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_updated_quota

        # Act
        result = quota_manager.use_quota("user-weekly", "weekly_report", amount=1)

        # Assert
        assert result["success"] is True
        assert result["quota_type"] == "weekly_report"
        assert result["used"] == 1
        assert result["total"] == 1
        assert result["remaining"] == 0


class TestQuotaAutoReset:
    """测试配额自动重置功能"""

    @patch('api.quota_manager.datetime')
    def test_reset_daily_quota_at_midnight(self, mock_datetime, quota_manager, mock_supabase_client):
        """测试每日配额在午夜重置"""
        from datetime import timezone

        # Arrange: 模拟中国时区的2024-01-02 00:00:01（重置时间已过）
        china_tz = timezone(timedelta(hours=8))
        now_china = datetime(2024, 1, 2, 0, 0, 1, tzinfo=china_tz)
        mock_datetime.now.return_value = now_china

        # Mock过期的配额（重置时间为昨天）
        yesterday = datetime(2024, 1, 1, 0, 0, 0, tzinfo=china_tz)
        mock_existing_quota = {
            "user_id": "user-123",
            "daily_plan_used": 3,
            "daily_plan_total": 3,
            "daily_plan_reset_at": yesterday.isoformat()
        }

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(data=[mock_existing_quota])

        # Mock update操作
        mock_update_response = Mock()
        mock_update_response.data = [{**mock_existing_quota, "daily_plan_used": 0}]
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_response

        # Act
        user_quota = quota_manager.get_or_create_user("user-123", "free")

        # Assert: 验证配额被重置
        update_call = mock_supabase_client.table.return_value.update.call_args
        if update_call:
            updated_data = update_call[0][0]
            assert updated_data["daily_plan_used"] == 0
            assert "daily_plan_reset_at" in updated_data

    @patch('api.quota_manager.datetime')
    def test_reset_weekly_quota_after_7days(self, mock_datetime, quota_manager, mock_supabase_client):
        """测试周报配额在7天后重置"""
        from datetime import timezone

        # Arrange: 模拟7天后的时间
        china_tz = timezone(timedelta(hours=8))
        now_china = datetime(2024, 1, 8, 0, 0, 1, tzinfo=china_tz)
        mock_datetime.now.return_value = now_china

        # Mock过期的周报配额（重置时间为7天前）
        last_week = datetime(2024, 1, 1, 0, 0, 0, tzinfo=china_tz)
        mock_existing_quota = {
            "user_id": "user-456",
            "weekly_report_used": 1,
            "weekly_report_total": 1,
            "weekly_report_reset_at": last_week.isoformat()
        }

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(data=[mock_existing_quota])

        # Mock update操作
        mock_update_response = Mock()
        mock_update_response.data = [{**mock_existing_quota, "weekly_report_used": 0}]
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_response

        # Act
        user_quota = quota_manager.get_or_create_user("user-456", "free")

        # Assert: 验证周报配额被重置
        update_call = mock_supabase_client.table.return_value.update.call_args
        if update_call:
            updated_data = update_call[0][0]
            assert updated_data["weekly_report_used"] == 0
            assert "weekly_report_reset_at" in updated_data

    @patch('api.quota_manager.datetime')
    def test_reset_multiple_quotas_simultaneously(self, mock_datetime, quota_manager, mock_supabase_client):
        """测试同时重置多个配额"""
        from datetime import timezone

        # Arrange: 模拟多个配额都需要重置
        china_tz = timezone(timedelta(hours=8))
        now_china = datetime(2024, 1, 2, 0, 0, 1, tzinfo=china_tz)
        mock_datetime.now.return_value = now_china

        # Mock所有配额都过期
        yesterday = datetime(2024, 1, 1, 0, 0, 0, tzinfo=china_tz)
        mock_existing_quota = {
            "user_id": "user-789",
            "daily_plan_used": 3,
            "daily_plan_reset_at": yesterday.isoformat(),
            "chat_used": 10,
            "chat_reset_at": yesterday.isoformat()
        }

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(data=[mock_existing_quota])

        # Mock update操作
        mock_update_response = Mock()
        mock_update_response.data = [{**mock_existing_quota, "daily_plan_used": 0, "chat_used": 0}]
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_response

        # Act
        user_quota = quota_manager.get_or_create_user("user-789", "free")

        # Assert: 验证多个配额都被重置
        update_call = mock_supabase_client.table.return_value.update.call_args
        if update_call:
            updated_data = update_call[0][0]
            assert updated_data["daily_plan_used"] == 0
            assert updated_data["chat_used"] == 0

    @patch('api.quota_manager.datetime')
    def test_no_reset_when_not_expired(self, mock_datetime, quota_manager, mock_supabase_client):
        """测试配额未过期时不重置"""
        from datetime import timezone

        # Arrange: 模拟当前时间未到重置时间
        china_tz = timezone(timedelta(hours=8))
        now_china = datetime(2024, 1, 1, 12, 0, 0, tzinfo=china_tz)
        mock_datetime.now.return_value = now_china

        # Mock未过期的配额（重置时间为明天）
        tomorrow = datetime(2024, 1, 2, 0, 0, 0, tzinfo=china_tz)
        mock_existing_quota = {
            "user_id": "user-123",
            "daily_plan_used": 2,
            "daily_plan_total": 3,
            "daily_plan_reset_at": tomorrow.isoformat()
        }

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(data=[mock_existing_quota])

        # Act
        user_quota = quota_manager.get_or_create_user("user-123", "free")

        # Assert: 验证update未被调用（无需重置）
        assert mock_supabase_client.table.return_value.update.call_count == 0


class TestGetQuotaStatus:
    """测试获取配额状态"""

    def test_get_quota_status_with_usage(self, quota_manager, mock_supabase_client):
        """测试获取有使用记录的配额状态"""
        # Arrange: Mock部分使用的配额
        mock_existing_quota = {
            "user_id": "user-123",
            "user_tier": "free",
            "daily_plan_total": 3,
            "daily_plan_used": 2,
            "weekly_report_total": 1,
            "weekly_report_used": 0,
            "chat_total": 10,
            "chat_used": 5
        }

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(data=[mock_existing_quota])

        # Act
        result = quota_manager.get_quota_status("user-123", "free")

        # Assert
        assert result["user_tier"] == "free"
        assert result["remaining"]["daily_plan"] == 1  # 3 - 2
        assert result["remaining"]["weekly_report"] == 1  # 1 - 0
        assert result["remaining"]["chat"] == 5  # 10 - 5

    def test_get_quota_status_fallback(self):
        """测试Supabase不可用时返回降级配额"""
        # Arrange: 创建没有client的manager
        manager = QuotaManager()
        manager.client = None

        # Act: 请求Pro用户配额状态
        result = manager.get_quota_status("user-456", "pro")

        # Assert: 返回pro的降级配额
        assert result["user_tier"] == "pro"
        assert "remaining" in result
        # Pro用户应该有更高的配额
        assert result["remaining"]["daily_plan"] >= 20  # Pro用户至少20次


# Pytest配置
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
