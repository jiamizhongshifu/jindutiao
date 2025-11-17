"""
API性能基准测试

使用pytest-benchmark进行性能基准测试，验证关键API的响应时间。

运行方法:
    pytest tests/performance/test_api_performance.py -v --benchmark-only

生成报告:
    pytest tests/performance/test_api_performance.py --benchmark-only \\
           --benchmark-json=reports/benchmark.json
"""

import pytest
import requests
from unittest.mock import Mock, patch
from datetime import datetime, timedelta


# 测试配置
API_BASE_URL = "https://jindutiao.vercel.app"
BENCHMARK_TIMEOUT = 10  # 秒


class TestQuotaAPIPerformance:
    """配额API性能测试"""

    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase客户端用于本地性能测试"""
        mock_client = Mock()

        # Mock数据库查询（返回固定数据以隔离数据库性能影响）
        mock_quota = {
            "user_id": "test-user",
            "daily_plan_total": 3,
            "daily_plan_used": 1,
            "weekly_report_total": 1,
            "weekly_report_used": 0,
            "chat_total": 10,
            "chat_used": 3,
            "user_tier": "free"
        }

        table_mock = Mock()
        table_mock.select.return_value = table_mock
        table_mock.eq.return_value = table_mock
        table_mock.single.return_value = table_mock
        table_mock.execute.return_value = Mock(data=mock_quota)

        mock_client.table.return_value = table_mock
        return mock_client

    def test_quota_manager_performance(self, benchmark, mock_supabase_client):
        """
        测试QuotaManager.get_quota_status性能

        验收标准:
        - 平均响应时间 < 50ms
        - P95响应时间 < 100ms
        """
        # 在patch环境变量后导入QuotaManager
        with patch.dict('os.environ', {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_ANON_KEY': 'test-key'
        }):
            with patch('supabase.create_client', return_value=mock_supabase_client):
                from api.quota_manager import QuotaManager

                quota_manager = QuotaManager()

                # Benchmark: 测量get_quota_status的执行时间
                result = benchmark(
                    quota_manager.get_quota_status,
                    user_id="test-user",
                    user_tier="free"
                )

                # 验证结果正确性
                assert "remaining" in result
                assert result["user_tier"] == "free"

    def test_quota_manager_use_quota_performance(self, benchmark, mock_supabase_client):
        """
        测试QuotaManager.use_quota性能

        验收标准:
        - 平均响应时间 < 100ms（包含数据库写操作）
        - P95响应时间 < 200ms
        """
        # Mock配额数据
        mock_quota = {
            "user_id": "test-user",
            "daily_plan_total": 3,
            "daily_plan_used": 1,
            "user_tier": "free"
        }

        # Mock表操作
        table_mock = Mock()
        table_mock.select.return_value = table_mock
        table_mock.eq.return_value = table_mock
        table_mock.single.return_value = table_mock
        table_mock.execute.return_value = Mock(data=mock_quota)

        # Mock update操作
        update_mock = Mock()
        update_mock.eq.return_value = update_mock
        update_mock.execute.return_value = Mock(data={"daily_plan_used": 2})
        table_mock.update.return_value = update_mock

        mock_supabase_client.table.return_value = table_mock

        with patch.dict('os.environ', {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_ANON_KEY': 'test-key'
        }):
            with patch('supabase.create_client', return_value=mock_supabase_client):
                from api.quota_manager import QuotaManager

                quota_manager = QuotaManager()

                # Benchmark: 测量use_quota的执行时间
                result = benchmark(
                    quota_manager.use_quota,
                    user_id="test-user",
                    quota_type="daily_plan",
                    amount=1
                )

                # 验证结果正确性
                assert result["success"] is True


class TestSubscriptionAPIPerformance:
    """订阅API性能测试"""

    @pytest.fixture
    def mock_supabase_for_subscription(self):
        """Mock Supabase客户端用于订阅性能测试"""
        mock_client = Mock()

        # Mock订阅数据
        mock_subscription = {
            "user_id": "test-user",
            "plan_type": "pro_monthly",
            "status": "active",
            "expires_at": (datetime.now() + timedelta(days=20)).isoformat()
        }

        table_mock = Mock()
        table_mock.select.return_value = table_mock
        table_mock.eq.return_value = table_mock
        table_mock.single.return_value = table_mock
        table_mock.execute.return_value = Mock(data=mock_subscription)

        mock_client.table.return_value = table_mock
        return mock_client

    def test_subscription_manager_get_subscription_performance(
        self,
        benchmark,
        mock_supabase_for_subscription
    ):
        """
        测试SubscriptionManager.get_user_subscription性能

        验收标准:
        - 平均响应时间 < 50ms
        - P95响应时间 < 100ms
        """
        with patch.dict('os.environ', {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_ANON_KEY': 'test-key'
        }):
            with patch('supabase.create_client', return_value=mock_supabase_for_subscription):
                from api.subscription_manager import SubscriptionManager

                subscription_manager = SubscriptionManager()

                # Benchmark
                result = benchmark(
                    subscription_manager.get_user_subscription,
                    user_id="test-user"
                )

                # 验证结果
                assert result is not None
                assert result["plan_type"] == "pro_monthly"


class TestE2EAPIPerformance:
    """端到端API性能测试（需要实际部署的API）"""

    @pytest.mark.skipif(
        API_BASE_URL == "",
        reason="API_BASE_URL not configured"
    )
    def test_quota_status_endpoint_response_time(self, benchmark):
        """
        测试 /api/quota-status 端点的实际响应时间

        验收标准:
        - P95响应时间 < 500ms
        """
        def call_quota_status_api():
            response = requests.get(
                f"{API_BASE_URL}/api/quota-status",
                params={"user_tier": "free"},
                timeout=BENCHMARK_TIMEOUT
            )
            return response

        # Benchmark
        response = benchmark(call_quota_status_api)

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "remaining" in data

    @pytest.mark.skipif(
        API_BASE_URL == "",
        reason="API_BASE_URL not configured"
    )
    def test_health_endpoint_response_time(self, benchmark):
        """
        测试 /api/health 端点的实际响应时间

        验收标准:
        - P95响应时间 < 200ms
        """
        def call_health_api():
            response = requests.get(
                f"{API_BASE_URL}/api/health",
                timeout=BENCHMARK_TIMEOUT
            )
            return response

        # Benchmark
        response = benchmark(call_health_api)

        # 验证响应
        assert response.status_code == 200


# Pytest-benchmark配置建议
"""
在pytest.ini中添加:

[pytest]
addopts = --benchmark-autosave --benchmark-save-data

性能基准对比:
1. 运行基准测试并保存结果:
   pytest tests/performance/test_api_performance.py --benchmark-save=baseline

2. 修改代码后对比性能:
   pytest tests/performance/test_api_performance.py --benchmark-compare=baseline

3. 查看详细统计:
   pytest tests/performance/test_api_performance.py --benchmark-columns=min,max,mean,stddev,median,ops

验收标准总结:
- QuotaManager.get_quota_status: 平均 < 50ms, P95 < 100ms
- QuotaManager.use_quota: 平均 < 100ms, P95 < 200ms
- SubscriptionManager.get_user_subscription: 平均 < 50ms, P95 < 100ms
- API端点 /api/quota-status: P95 < 500ms
- API端点 /api/health: P95 < 200ms
"""
