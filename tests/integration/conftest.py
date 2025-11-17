"""
集成测试配置和Fixtures

提供集成测试所需的共享fixtures，包括：
- 测试数据库设置
- Mock Supabase客户端
- 测试用户数据
- 时间模拟工具
"""
import pytest
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from freezegun import freeze_time
import json


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase客户端，用于集成测试"""
    mock_client = MagicMock()

    # 模拟数据库存储
    mock_client._users_db = {}
    mock_client._subscriptions_db = {}
    mock_client._quotas_db = {}
    mock_client._payments_db = {}

    # Mock auth相关方法（Supabase实际API接收字典参数）
    mock_client.auth.sign_up.side_effect = lambda credentials: _mock_sign_up(
        mock_client, credentials
    )
    mock_client.auth.sign_in_with_password.side_effect = lambda credentials: _mock_sign_in(
        mock_client, credentials
    )
    mock_client.auth.get_user.side_effect = lambda token: _mock_get_user(
        mock_client, token
    )

    # Mock table相关方法
    def _mock_table(table_name):
        table_mock = Mock()
        table_mock._table_name = table_name
        table_mock._db = getattr(mock_client, f"_{table_name}_db")

        # 链式调用支持
        table_mock.select.return_value = table_mock
        table_mock.insert.return_value = table_mock
        table_mock.update.return_value = table_mock
        table_mock.delete.return_value = table_mock
        table_mock.eq.return_value = table_mock
        table_mock.single.return_value = table_mock
        table_mock.order.return_value = table_mock
        table_mock.limit.return_value = table_mock

        # execute方法实现
        table_mock.execute.side_effect = lambda: _mock_execute(table_mock)

        return table_mock

    mock_client.table.side_effect = _mock_table

    return mock_client


def _mock_sign_up(client, credentials):
    """模拟用户注册（接收字典参数）"""
    email = credentials.get("email")
    password = credentials.get("password")
    options = credentials.get("options", {})

    user_id = f"user-{len(client._users_db) + 1}"
    user = {
        "id": user_id,
        "email": email,
        "user_metadata": options.get("data", {}),
        "created_at": datetime.now().isoformat(),
        "email_confirmed_at": None  # 邮箱未验证
    }
    client._users_db[user_id] = user

    response = Mock()
    response.user = Mock()
    response.user.id = user_id
    response.user.email = email
    response.user.email_confirmed_at = None
    response.session = Mock()
    response.session.access_token = f"token-{user_id}"

    return response


def _mock_sign_in(client, credentials):
    """模拟用户登录（接收字典参数）"""
    email = credentials.get("email")
    password = credentials.get("password")

    # 查找用户
    user = next(
        (u for u in client._users_db.values() if u["email"] == email),
        None
    )

    if not user:
        raise Exception("Invalid credentials")

    response = Mock()
    response.user = Mock()
    response.user.id = user["id"]
    response.user.email = user["email"]
    response.session = Mock()
    response.session.access_token = f"token-{user['id']}"

    return response


def _mock_get_user(client, token):
    """模拟获取当前用户"""
    if not token or not token.startswith("token-"):
        raise Exception("Invalid token")

    user_id = token.replace("token-", "")
    user = client._users_db.get(user_id)

    if not user:
        raise Exception("User not found")

    response = Mock()
    response.user = Mock()
    response.user.id = user["id"]
    response.user.email = user["email"]

    return response


def _mock_execute(table_mock):
    """模拟数据库操作执行"""
    result = Mock()
    result.data = []

    # 根据表名返回不同的数据
    table_name = table_mock._table_name
    db = table_mock._db

    # 简单实现：返回所有数据
    result.data = list(db.values())

    return result


@pytest.fixture
def test_user_data():
    """测试用户数据"""
    return {
        "free_user": {
            "email": "free@test.com",
            "password": "Test123456",
            "username": "Free User"
        },
        "pro_user": {
            "email": "pro@test.com",
            "password": "Test123456",
            "username": "Pro User"
        },
        "expiring_user": {
            "email": "expiring@test.com",
            "password": "Test123456",
            "username": "Expiring User"
        }
    }


@pytest.fixture
def mock_zpay_client():
    """Mock ZPAY支付客户端"""
    mock_zpay = MagicMock()

    mock_zpay.create_order.return_value = {
        "success": True,
        "payment_url": "https://pay.zpay.com/test123",
        "params": {
            "pid": "test-merchant-123",
            "type": "alipay",
            "out_trade_no": "ORDER123",
            "money": "29.00",
            "name": "GaiYa月度会员",
            "sign": "test_signature"
        },
        "out_trade_no": "ORDER123"
    }

    mock_zpay.verify_notify.return_value = True

    mock_zpay.query_order.return_value = {
        "success": True,
        "order": {
            "out_trade_no": "ORDER123",
            "trade_no": "ZPAY987654321",
            "money": "29.00",
            "status": 1,  # 已支付
            "type": "alipay",
            "addtime": datetime.now().isoformat(),
            "endtime": datetime.now().isoformat()
        }
    }

    return mock_zpay


@pytest.fixture
def time_machine():
    """时间模拟工具（使用freezegun）"""
    class TimeMachine:
        def __init__(self):
            self.frozen_time = None

        def freeze_at(self, target_datetime):
            """冻结时间到指定时刻"""
            if self.frozen_time:
                self.frozen_time.stop()
            self.frozen_time = freeze_time(target_datetime)
            self.frozen_time.start()
            return target_datetime

        def advance(self, **kwargs):
            """推进时间（天、小时、分钟）"""
            if not self.frozen_time:
                raise RuntimeError("Time is not frozen")

            current = datetime.now()
            new_time = current + timedelta(**kwargs)
            self.frozen_time.stop()
            self.frozen_time = freeze_time(new_time)
            self.frozen_time.start()
            return new_time

        def reset(self):
            """重置时间"""
            if self.frozen_time:
                self.frozen_time.stop()
                self.frozen_time = None

    tm = TimeMachine()
    yield tm
    tm.reset()


@pytest.fixture
def integration_test_managers(mock_supabase_client, mock_zpay_client):
    """
    集成测试所需的所有管理器实例

    所有管理器共享相同的Mock数据库，模拟真实的数据流动
    """
    # 先patch环境变量，然后再导入模块（这样模块级变量会使用patch的值）
    with patch.dict('os.environ', {
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_ANON_KEY': 'test-anon-key',
        'ZPAY_PID': 'test-merchant-123',
        'ZPAY_PKEY': 'test-secret-key'
    }):
        # 使用patch确保所有管理器使用相同的mock client
        with patch('supabase.create_client', return_value=mock_supabase_client):
            # 在patch环境变量后才导入模块
            from api.auth_manager import AuthManager
            from api.subscription_manager import SubscriptionManager
            from api.quota_manager import QuotaManager

            managers = {
                "auth": AuthManager(),
                "subscription": SubscriptionManager(),
                "quota": QuotaManager(),
                "zpay": mock_zpay_client  # 直接使用mock zpay客户端
            }

            yield managers


@pytest.fixture
def assert_helpers():
    """测试断言辅助函数"""
    class AssertHelpers:
        @staticmethod
        def assert_user_tier(user_tier, expected_tier):
            """断言用户等级"""
            assert user_tier == expected_tier, f"Expected tier {expected_tier}, got {user_tier}"

        @staticmethod
        def assert_quota_remaining(quota_info, expected_remaining):
            """断言剩余配额"""
            actual = quota_info.get("remaining", 0)
            assert actual == expected_remaining, f"Expected {expected_remaining} quota, got {actual}"

        @staticmethod
        def assert_subscription_active(subscription_info):
            """断言订阅处于活跃状态"""
            assert subscription_info.get("status") == "active", "Subscription should be active"

        @staticmethod
        def assert_payment_success(payment_result):
            """断言支付成功"""
            assert payment_result.get("success") is True, "Payment should succeed"
            assert "payment_url" in payment_result, "Payment URL should be present"

    return AssertHelpers()


# 标记集成测试
def pytest_configure(config):
    """配置pytest，添加集成测试标记"""
    config.addinivalue_line(
        "markers", "integration: 集成测试标记（需要模拟数据库）"
    )
