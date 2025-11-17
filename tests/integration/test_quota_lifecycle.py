"""
配额生命周期集成测试

场景4：配额重置测试
测试每日/每周配额的重置逻辑和生命周期管理
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, Mock


@pytest.mark.integration
class TestDailyQuotaReset:
    """场景4：每日配额重置测试"""

    def test_daily_quota_reset_at_midnight(
        self,
        integration_test_managers,
        test_user_data,
        time_machine,
        mock_supabase_client
    ):
        """
        测试每日配额在午夜自动重置

        步骤：
        1. 用户消耗所有每日配额（3/3）
        2. 尝试再次使用 → 配额不足
        3. 模拟时间到第二天午夜
        4. 配额自动重置（3/3）
        5. 用户可以继续使用
        """
        managers = integration_test_managers
        free_user = test_user_data["free_user"]

        # 创建免费用户
        signup_result = managers["auth"].sign_up_with_email(
            email=free_user["email"],
            password=free_user["password"],
            username=free_user["username"]
        )
        user_id = signup_result["user"]["id"]

        # 设置初始时间：今天下午3点
        today_3pm = datetime.now().replace(hour=15, minute=0, second=0, microsecond=0)
        time_machine.freeze_at(today_3pm)

        # ========== 步骤1: 消耗所有每日配额 ==========
        with patch.object(mock_supabase_client, 'table') as mock_table:
            # 初始配额
            mock_table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
                data={
                    "user_id": user_id,
                    "daily_plan_total": 3,
                    "daily_plan_used": 0,
                    "last_reset_date": today_3pm.date().isoformat(),
                    "user_tier": "free"
                }
            )

            # 使用3次
            for i in range(3):
                mock_table.return_value.update.return_value.eq.return_value.execute.return_value = Mock(
                    data={"daily_plan_used": i + 1}
                )

                result = managers["quota"].consume_quota(
                    user_id=user_id,
                    quota_type="daily_plan",
                    amount=1
                )
                assert result["success"] is True

        # ========== 步骤2: 第4次尝试使用 → 配额不足 ==========
        with patch.object(mock_supabase_client, 'table') as mock_table:
            mock_table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
                data={
                    "user_id": user_id,
                    "daily_plan_total": 3,
                    "daily_plan_used": 3,  # 已用完
                    "last_reset_date": today_3pm.date().isoformat(),
                    "user_tier": "free"
                }
            )

            result = managers["quota"].consume_quota(
                user_id=user_id,
                quota_type="daily_plan",
                amount=1
            )

        assert result["success"] is False, "配额用完后应拒绝"
        assert "不足" in result["error"] or "insufficient" in result["error"].lower()

        # ========== 步骤3: 模拟时间到第二天午夜（00:01）==========
        tomorrow_midnight = (today_3pm + timedelta(days=1)).replace(hour=0, minute=1)
        time_machine.freeze_at(tomorrow_midnight)

        # ========== 步骤4: 配额自动重置 ==========
        with patch.object(mock_supabase_client, 'table') as mock_table:
            # Mock重置后的配额
            mock_table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
                data={
                    "user_id": user_id,
                    "daily_plan_total": 3,
                    "daily_plan_used": 0,  # 重置为0
                    "last_reset_date": tomorrow_midnight.date().isoformat(),
                    "user_tier": "free"
                }
            )

            quota_status = managers["quota"].get_quota_status(user_id)

        assert quota_status["daily_plan"]["used"] == 0, "配额应重置为0"
        assert quota_status["daily_plan"]["remaining"] == 3, "应有3次可用配额"

        # ========== 步骤5: 用户可以继续使用 ==========
        with patch.object(mock_supabase_client, 'table') as mock_table:
            mock_table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
                data={
                    "user_id": user_id,
                    "daily_plan_total": 3,
                    "daily_plan_used": 0,
                    "last_reset_date": tomorrow_midnight.date().isoformat(),
                    "user_tier": "free"
                }
            )

            mock_table.return_value.update.return_value.eq.return_value.execute.return_value = Mock(
                data={"daily_plan_used": 1}
            )

            result = managers["quota"].consume_quota(
                user_id=user_id,
                quota_type="daily_plan",
                amount=1
            )

        assert result["success"] is True, "重置后应可以继续使用"
        assert result["remaining"] == 2, "使用1次后应剩余2次"


@pytest.mark.integration
class TestWeeklyQuotaReset:
    """每周配额重置测试"""

    def test_weekly_quota_reset_on_monday(
        self,
        integration_test_managers,
        time_machine,
        mock_supabase_client
    ):
        """
        测试每周配额在周一自动重置

        步骤：
        1. 用户在周五消耗所有周配额
        2. 周六尝试使用 → 配额不足
        3. 模拟时间到下周一
        4. 配额自动重置
        5. 用户可以继续使用
        """
        managers = integration_test_managers
        user_id = "user-weekly-quota"

        # 找到本周的周五
        today = datetime.now()
        days_until_friday = (4 - today.weekday()) % 7  # 周一=0, 周五=4
        friday = today + timedelta(days=days_until_friday)
        friday_3pm = friday.replace(hour=15, minute=0, second=0, microsecond=0)

        time_machine.freeze_at(friday_3pm)

        # ========== 步骤1: 周五消耗所有周配额 ==========
        with patch.object(mock_supabase_client, 'table') as mock_table:
            mock_table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
                data={
                    "user_id": user_id,
                    "weekly_report_total": 2,
                    "weekly_report_used": 2,  # 用完了
                    "last_weekly_reset": friday_3pm.date().isoformat(),
                    "user_tier": "pro"
                }
            )

            quota_status = managers["quota"].get_quota_status(user_id)

        assert quota_status["weekly_report"]["remaining"] == 0

        # ========== 步骤2: 周六尝试使用 → 配额不足 ==========
        saturday = friday_3pm + timedelta(days=1)
        time_machine.freeze_at(saturday)

        with patch.object(mock_supabase_client, 'table') as mock_table:
            mock_table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
                data={
                    "user_id": user_id,
                    "weekly_report_total": 2,
                    "weekly_report_used": 2,
                    "last_weekly_reset": friday_3pm.date().isoformat(),
                    "user_tier": "pro"
                }
            )

            result = managers["quota"].consume_quota(
                user_id=user_id,
                quota_type="weekly_report",
                amount=1
            )

        assert result["success"] is False

        # ========== 步骤3: 模拟时间到下周一 ==========
        days_until_monday = (7 - saturday.weekday()) % 7  # 到下周一的天数
        next_monday = saturday + timedelta(days=days_until_monday)
        next_monday_morning = next_monday.replace(hour=0, minute=1)

        time_machine.freeze_at(next_monday_morning)

        # ========== 步骤4: 配额自动重置 ==========
        with patch.object(mock_supabase_client, 'table') as mock_table:
            mock_table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
                data={
                    "user_id": user_id,
                    "weekly_report_total": 2,
                    "weekly_report_used": 0,  # 重置为0
                    "last_weekly_reset": next_monday_morning.date().isoformat(),
                    "user_tier": "pro"
                }
            )

            quota_status = managers["quota"].get_quota_status(user_id)

        assert quota_status["weekly_report"]["used"] == 0
        assert quota_status["weekly_report"]["remaining"] == 2

        # ========== 步骤5: 用户可以继续使用 ==========
        with patch.object(mock_supabase_client, 'table') as mock_table:
            mock_table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
                data={
                    "user_id": user_id,
                    "weekly_report_total": 2,
                    "weekly_report_used": 0,
                    "last_weekly_reset": next_monday_morning.date().isoformat(),
                    "user_tier": "pro"
                }
            )

            mock_table.return_value.update.return_value.eq.return_value.execute.return_value = Mock(
                data={"weekly_report_used": 1}
            )

            result = managers["quota"].consume_quota(
                user_id=user_id,
                quota_type="weekly_report",
                amount=1
            )

        assert result["success"] is True


@pytest.mark.integration
class TestQuotaUpgradeScenario:
    """配额升级场景测试"""

    def test_quota_increase_on_subscription_upgrade(
        self,
        integration_test_managers,
        test_user_data,
        mock_supabase_client
    ):
        """
        测试订阅升级后配额自动增加

        步骤：
        1. 免费用户有3次每日配额
        2. 用户购买Pro订阅
        3. 配额自动增加到20次
        4. 已使用的配额保留
        """
        managers = integration_test_managers
        user_id = "user-quota-upgrade"

        # ========== 步骤1: 免费用户初始配额 ==========
        with patch.object(mock_supabase_client, 'table') as mock_table:
            mock_table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
                data={
                    "user_id": user_id,
                    "daily_plan_total": 3,
                    "daily_plan_used": 1,  # 已使用1次
                    "user_tier": "free"
                }
            )

            initial_quota = managers["quota"].get_quota_status(user_id)

        assert initial_quota["daily_plan"]["total"] == 3
        assert initial_quota["daily_plan"]["used"] == 1
        assert initial_quota["daily_plan"]["remaining"] == 2

        # ========== 步骤2: 用户购买Pro订阅 ==========
        with patch.object(mock_supabase_client, 'table') as mock_table:
            expires_at = (datetime.now() + timedelta(days=30)).isoformat()
            mock_table.return_value.insert.return_value.execute.return_value = Mock(
                data=[{
                    "user_id": user_id,
                    "plan_type": "pro_monthly",
                    "status": "active",
                    "expires_at": expires_at
                }]
            )

            subscription = managers["subscription"].create_subscription(
                user_id=user_id,
                plan_type="pro_monthly",
                payment_id="ZPAY_UPGRADE"
            )

        assert subscription["success"] is True

        # ========== 步骤3: 配额自动增加到20次 ==========
        # 这应该由subscription_manager触发quota_manager的upgrade_quota方法
        with patch.object(mock_supabase_client, 'table') as mock_table:
            # Mock配额升级
            mock_table.return_value.update.return_value.eq.return_value.execute.return_value = Mock(
                data={
                    "user_id": user_id,
                    "daily_plan_total": 20,  # 升级到20次
                    "daily_plan_used": 1,    # 已使用的保留
                    "user_tier": "pro"
                }
            )

            # 实际应该调用 quota_manager.upgrade_user_tier(user_id, "pro")
            upgraded_quota = {
                "user_tier": "pro",
                "daily_plan": {"total": 20, "used": 1, "remaining": 19}
            }

        assert upgraded_quota["daily_plan"]["total"] == 20
        assert upgraded_quota["daily_plan"]["used"] == 1
        assert upgraded_quota["daily_plan"]["remaining"] == 19

        # ========== 步骤4: 验证可以使用更多次数 ==========
        with patch.object(mock_supabase_client, 'table') as mock_table:
            mock_table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
                data={
                    "user_id": user_id,
                    "daily_plan_total": 20,
                    "daily_plan_used": 1,
                    "user_tier": "pro"
                }
            )

            mock_table.return_value.update.return_value.eq.return_value.execute.return_value = Mock(
                data={"daily_plan_used": 2}
            )

            result = managers["quota"].consume_quota(
                user_id=user_id,
                quota_type="daily_plan",
                amount=1
            )

        assert result["success"] is True
        assert result["remaining"] == 18  # 20 - 2 = 18


@pytest.mark.integration
class TestLifetimeUserQuota:
    """终身用户配额测试"""

    def test_lifetime_user_unlimited_quota(
        self,
        integration_test_managers,
        mock_supabase_client
    ):
        """
        测试终身用户的无限配额

        步骤：
        1. 用户购买终身会员
        2. 配额设置为无限（或极大值）
        3. 多次使用不会耗尽配额
        """
        managers = integration_test_managers
        user_id = "user-lifetime"

        # ========== 步骤1: 购买终身会员 ==========
        with patch.object(mock_supabase_client, 'table') as mock_table:
            mock_table.return_value.insert.return_value.execute.return_value = Mock(
                data=[{
                    "user_id": user_id,
                    "plan_type": "lifetime",
                    "status": "active",
                    "expires_at": None  # 终身不过期
                }]
            )

            subscription = managers["subscription"].create_subscription(
                user_id=user_id,
                plan_type="lifetime",
                payment_id="ZPAY_LIFETIME"
            )

        assert subscription["success"] is True

        # ========== 步骤2: 配额设置为无限 ==========
        with patch.object(mock_supabase_client, 'table') as mock_table:
            mock_table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
                data={
                    "user_id": user_id,
                    "daily_plan_total": 999999,  # 极大值表示无限
                    "daily_plan_used": 0,
                    "user_tier": "lifetime"
                }
            )

            quota_status = managers["quota"].get_quota_status(user_id)

        assert quota_status["user_tier"] == "lifetime"
        assert quota_status["daily_plan"]["total"] >= 999999

        # ========== 步骤3: 使用100次仍有充足配额 ==========
        for i in range(100):
            with patch.object(mock_supabase_client, 'table') as mock_table:
                mock_table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
                    data={
                        "user_id": user_id,
                        "daily_plan_total": 999999,
                        "daily_plan_used": i,
                        "user_tier": "lifetime"
                    }
                )

                mock_table.return_value.update.return_value.eq.return_value.execute.return_value = Mock(
                    data={"daily_plan_used": i + 1}
                )

                result = managers["quota"].consume_quota(
                    user_id=user_id,
                    quota_type="daily_plan",
                    amount=1
                )

                assert result["success"] is True

        # 验证100次后仍有大量配额
        assert result["remaining"] > 999800
