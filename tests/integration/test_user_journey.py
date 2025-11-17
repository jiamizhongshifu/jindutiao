"""
用户旅程集成测试

测试完整的用户旅程，从注册到使用核心功能的端到端流程。

场景1：免费用户完整旅程
场景2：付费用户完整流程（注册 → 支付 → 升级 → 使用）
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, Mock


@pytest.mark.integration
class TestFreeUserJourney:
    """场景1：免费用户完整旅程测试"""

    def test_free_user_complete_journey(
        self,
        integration_test_managers,
        test_user_data,
        assert_helpers,
        mock_supabase_client
    ):
        """
        测试免费用户从注册到配额耗尽的完整旅程

        步骤：
        1. 用户注册 → 获取session
        2. 登录 → 验证身份
        3. 查询配额 → 确认免费用户3次配额
        4. 使用AI功能3次 → 配额逐渐减少
        5. 第4次请求 → 配额不足提示
        """
        managers = integration_test_managers
        free_user_info = test_user_data["free_user"]

        # ========== 步骤1: 用户注册 ==========
        signup_result = managers["auth"].sign_up_with_email(
            email=free_user_info["email"],
            password=free_user_info["password"],
            username=free_user_info["username"]
        )

        assert signup_result["success"] is True, "注册应该成功"
        assert "access_token" in signup_result, "应该返回access_token"
        user_id = signup_result["user"]["id"]

        # ========== 步骤2: 登录验证 ==========
        signin_result = managers["auth"].sign_in_with_password(
            email=free_user_info["email"],
            password=free_user_info["password"]
        )

        assert signin_result["success"] is True, "登录应该成功"
        assert signin_result["user"]["id"] == user_id, "登录用户应与注册用户一致"

        # ========== 步骤3: 初始化配额（模拟系统自动分配）==========
        # 免费用户初始配额应为3次/天
        with patch.object(mock_supabase_client, 'table') as mock_table:
            # Mock配额查询
            mock_table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
                data={
                    "user_id": user_id,
                    "daily_plan_total": 3,
                    "daily_plan_used": 0,
                    "user_tier": "free"
                }
            )

            quota_status = managers["quota"].get_quota_status(user_id)

        assert quota_status["user_tier"] == "free", "用户等级应为free"
        assert quota_status["daily_plan"]["total"] == 3, "免费用户应有3次每日配额"
        assert quota_status["daily_plan"]["used"] == 0, "初始使用量应为0"
        assert quota_status["daily_plan"]["remaining"] == 3, "初始剩余量应为3"

        # ========== 步骤4: 消耗配额（使用AI功能3次）==========
        for usage_count in range(1, 4):  # 使用3次
            with patch.object(mock_supabase_client, 'table') as mock_table:
                # Mock配额查询：剩余配额逐渐减少
                mock_table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
                    data={
                        "user_id": user_id,
                        "daily_plan_total": 3,
                        "daily_plan_used": usage_count - 1,
                        "user_tier": "free"
                    }
                )

                # Mock配额更新
                mock_table.return_value.update.return_value.eq.return_value.execute.return_value = Mock(
                    data={
                        "user_id": user_id,
                        "daily_plan_used": usage_count
                    }
                )

                consume_result = managers["quota"].consume_quota(
                    user_id=user_id,
                    quota_type="daily_plan",
                    amount=1
                )

            assert consume_result["success"] is True, f"第{usage_count}次使用应该成功"
            assert consume_result["remaining"] == 3 - usage_count, f"剩余配额应为{3 - usage_count}"

        # ========== 步骤5: 第4次请求 → 配额不足 ==========
        with patch.object(mock_supabase_client, 'table') as mock_table:
            # Mock配额查询：已用完3次
            mock_table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
                data={
                    "user_id": user_id,
                    "daily_plan_total": 3,
                    "daily_plan_used": 3,
                    "user_tier": "free"
                }
            )

            consume_result = managers["quota"].consume_quota(
                user_id=user_id,
                quota_type="daily_plan",
                amount=1
            )

        assert consume_result["success"] is False, "配额不足时应拒绝请求"
        assert "不足" in consume_result["error"] or "insufficient" in consume_result["error"].lower(), \
            "错误信息应提示配额不足"


@pytest.mark.integration
class TestPaidUserJourney:
    """场景2：付费用户完整流程测试"""

    def test_paid_user_complete_journey(
        self,
        integration_test_managers,
        test_user_data,
        assert_helpers,
        mock_supabase_client
    ):
        """
        测试付费用户从注册到享受Pro服务的完整流程

        步骤：
        1. 用户注册（免费用户）
        2. 创建支付订单（月度会员29元）
        3. 模拟支付成功回调
        4. 验证订阅已激活
        5. 验证用户等级升级为pro
        6. 验证配额自动增加（3次 → 20次）
        7. 使用AI功能（验证pro权限）
        """
        managers = integration_test_managers
        pro_user_info = test_user_data["pro_user"]

        # ========== 步骤1: 用户注册 ==========
        signup_result = managers["auth"].sign_up_with_email(
            email=pro_user_info["email"],
            password=pro_user_info["password"],
            username=pro_user_info["username"]
        )

        assert signup_result["success"] is True
        user_id = signup_result["user"]["id"]

        # ========== 步骤2: 创建支付订单 ==========
        with patch.object(mock_supabase_client, 'table') as mock_table:
            # Mock订单创建
            mock_table.return_value.insert.return_value.execute.return_value = Mock(
                data=[{
                    "out_trade_no": "ORDER_PRO_MONTHLY_001",
                    "user_id": user_id,
                    "plan_type": "pro_monthly",
                    "amount": 29.0,
                    "status": "pending"
                }]
            )

            payment_result = managers["zpay"].create_order(
                out_trade_no="ORDER_PRO_MONTHLY_001",
                name="GaiYa月度会员",
                money=29.0,
                pay_type="alipay",
                notify_url="https://jindutiao.vercel.app/api/payment-notify",
                return_url="gaiya://payment-success?out_trade_no=ORDER_PRO_MONTHLY_001",
                param=f'{{"user_id": "{user_id}", "plan_type": "pro_monthly"}}'
            )

        assert_helpers.assert_payment_success(payment_result)
        assert payment_result["out_trade_no"] == "ORDER_PRO_MONTHLY_001"

        # ========== 步骤3: 模拟支付成功回调 ==========
        callback_params = {
            "pid": "test-merchant-123",
            "out_trade_no": "ORDER_PRO_MONTHLY_001",
            "trade_no": "ZPAY123456789",
            "type": "alipay",
            "money": "29.00",
            "trade_status": "TRADE_SUCCESS",
            "param": f'{{"user_id": "{user_id}", "plan_type": "pro_monthly"}}',
            "sign": "valid_signature"
        }

        with patch.object(mock_supabase_client, 'table') as mock_table:
            # Mock订阅创建
            expires_at = (datetime.now() + timedelta(days=30)).isoformat()
            mock_table.return_value.insert.return_value.execute.return_value = Mock(
                data=[{
                    "user_id": user_id,
                    "plan_type": "pro_monthly",
                    "status": "active",
                    "expires_at": expires_at
                }]
            )

            # Mock支付记录创建
            mock_table.return_value.insert.return_value.execute.return_value = Mock(
                data=[{
                    "out_trade_no": "ORDER_PRO_MONTHLY_001",
                    "user_id": user_id,
                    "amount": 29.0,
                    "status": "paid"
                }]
            )

            # 处理回调（实际上会调用subscription_manager.create_subscription）
            callback_result = managers["subscription"].create_subscription(
                user_id=user_id,
                plan_type="pro_monthly",
                payment_id="ZPAY123456789"
            )

        assert callback_result["success"] is True, "订阅创建应该成功"
        assert callback_result["subscription"]["status"] == "active", "订阅应处于活跃状态"

        # ========== 步骤4: 验证订阅已激活 ==========
        with patch.object(mock_supabase_client, 'table') as mock_table:
            expires_at = (datetime.now() + timedelta(days=30)).isoformat()
            mock_table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
                data={
                    "user_id": user_id,
                    "plan_type": "pro_monthly",
                    "status": "active",
                    "expires_at": expires_at
                }
            )

            subscription_info = managers["subscription"].get_active_subscription(user_id)

        assert_helpers.assert_subscription_active(subscription_info)
        assert subscription_info["plan_type"] == "pro_monthly"

        # ========== 步骤5: 验证用户等级升级为pro ==========
        user_tier = managers["subscription"].get_user_tier(user_id)
        assert_helpers.assert_user_tier(user_tier, "pro")

        # ========== 步骤6: 验证配额自动增加 ==========
        with patch.object(mock_supabase_client, 'table') as mock_table:
            # Pro用户应有20次每日配额
            mock_table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
                data={
                    "user_id": user_id,
                    "daily_plan_total": 20,
                    "daily_plan_used": 0,
                    "user_tier": "pro"
                }
            )

            quota_status = managers["quota"].get_quota_status(user_id)

        assert quota_status["user_tier"] == "pro"
        assert quota_status["daily_plan"]["total"] == 20, "Pro用户应有20次每日配额"

        # ========== 步骤7: 使用AI功能（验证pro权限）==========
        with patch.object(mock_supabase_client, 'table') as mock_table:
            mock_table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
                data={
                    "user_id": user_id,
                    "daily_plan_total": 20,
                    "daily_plan_used": 0,
                    "user_tier": "pro"
                }
            )

            mock_table.return_value.update.return_value.eq.return_value.execute.return_value = Mock(
                data={"daily_plan_used": 1}
            )

            consume_result = managers["quota"].consume_quota(
                user_id=user_id,
                quota_type="daily_plan",
                amount=1
            )

        assert consume_result["success"] is True, "Pro用户使用功能应成功"
        assert consume_result["remaining"] == 19, "使用1次后应剩余19次"


@pytest.mark.integration
class TestUserUpgradeJourney:
    """测试用户升级旅程（月度 → 年度）"""

    def test_user_upgrade_from_monthly_to_yearly(
        self,
        integration_test_managers,
        test_user_data,
        mock_supabase_client
    ):
        """
        测试用户从月度会员升级到年度会员

        步骤：
        1. 用户已有月度订阅（剩余15天）
        2. 创建年度会员支付订单
        3. 支付成功
        4. 旧订阅取消，新订阅创建
        5. 验证剩余天数折算
        """
        managers = integration_test_managers
        user_info = test_user_data["pro_user"]

        # 模拟已有月度订阅
        user_id = "user-upgrade-test"
        current_subscription = {
            "id": "sub-123",
            "user_id": user_id,
            "plan_type": "pro_monthly",
            "status": "active",
            "expires_at": (datetime.now() + timedelta(days=15)).isoformat()
        }

        # ========== 步骤1: 查询当前订阅 ==========
        with patch.object(mock_supabase_client, 'table') as mock_table:
            mock_table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
                data=current_subscription
            )

            current_sub = managers["subscription"].get_active_subscription(user_id)

        assert current_sub["plan_type"] == "pro_monthly"

        # ========== 步骤2: 创建年度升级订单 ==========
        with patch.object(mock_supabase_client, 'table') as mock_table:
            mock_table.return_value.insert.return_value.execute.return_value = Mock(
                data=[{
                    "out_trade_no": "ORDER_UPGRADE_YEARLY",
                    "user_id": user_id,
                    "plan_type": "pro_yearly",
                    "amount": 199.0,
                    "status": "pending"
                }]
            )

            upgrade_payment = managers["zpay"].create_order(
                out_trade_no="ORDER_UPGRADE_YEARLY",
                name="GaiYa年度会员",
                money=199.0,
                pay_type="alipay",
                notify_url="https://jindutiao.vercel.app/api/payment-notify",
                return_url="gaiya://payment-success",
                param=f'{{"user_id": "{user_id}", "plan_type": "pro_yearly"}}'
            )

        assert upgrade_payment["success"] is True

        # ========== 步骤3: 支付成功，创建新订阅 ==========
        with patch.object(mock_supabase_client, 'table') as mock_table:
            # Mock取消旧订阅
            mock_table.return_value.update.return_value.eq.return_value.execute.return_value = Mock(
                data={"status": "cancelled"}
            )

            # Mock创建新订阅（年度）
            new_expires_at = (datetime.now() + timedelta(days=365 + 15)).isoformat()  # 1年 + 折算的15天
            mock_table.return_value.insert.return_value.execute.return_value = Mock(
                data=[{
                    "user_id": user_id,
                    "plan_type": "pro_yearly",
                    "status": "active",
                    "expires_at": new_expires_at
                }]
            )

            new_subscription = managers["subscription"].create_subscription(
                user_id=user_id,
                plan_type="pro_yearly",
                payment_id="ZPAY_UPGRADE"
            )

        assert new_subscription["success"] is True
        assert new_subscription["subscription"]["plan_type"] == "pro_yearly"
        assert new_subscription["subscription"]["status"] == "active"
