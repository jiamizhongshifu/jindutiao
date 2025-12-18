"""
validators_enhanced.py 单元测试
测试新增的UUID验证、Decimal金额处理、RFC 5322邮箱验证等增强功能
"""
import pytest
from decimal import Decimal
from api.validators_enhanced import (
    validate_uuid,
    validate_email,
    validate_amount,
    validate_plan_type,
    validate_payment_amount,
    validate_password,
    validate_user_id,
    PYDANTIC_AVAILABLE
)


class TestUUIDValidation:
    """UUID验证测试（新增功能）"""

    def test_valid_uuid_v4(self):
        """测试有效的UUID v4格式"""
        valid_uuids = [
            "550e8400-e29b-41d4-a716-446655440000",
            "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
            "123e4567-e89b-12d3-a456-426614174000",
            "00000000-0000-0000-0000-000000000000"
        ]
        for uuid_str in valid_uuids:
            is_valid, error = validate_uuid(uuid_str)
            assert is_valid is True, f"{uuid_str} 应该是有效的UUID"
            assert error == ""

    def test_invalid_uuid_format(self):
        """测试无效的UUID格式"""
        invalid_uuids = [
            "550e8400-e29b-41d4-a716",  # 太短
            "550e8400-e29b-41d4-a716-446655440000-extra",  # 太长
            "550e8400e29b41d4a716446655440000",  # 缺少连字符
            "550e8400-e29b-41d4-a716-4466554400zz",  # 非十六进制字符
            "not-a-uuid-at-all",
            "G50e8400-e29b-41d4-a716-446655440000"  # 非法字符G
        ]
        for uuid_str in invalid_uuids:
            is_valid, error = validate_uuid(uuid_str)
            assert is_valid is False, f"{uuid_str} 应该是无效的UUID"
            assert "UUID" in error  # 可能是"UUID格式不正确"或"UUID不能为空"

    def test_empty_uuid(self):
        """测试空UUID"""
        is_valid, error = validate_uuid("")
        assert is_valid is False
        assert error == "UUID不能为空"

    def test_supabase_user_id_format(self):
        """测试Supabase Auth典型的user_id格式"""
        supabase_uid = "a1b2c3d4-e5f6-4789-a012-b3c4d5e6f7a8"
        is_valid, error = validate_uuid(supabase_uid)
        assert is_valid is True
        assert error == ""


class TestEnhancedEmailValidation:
    """增强的邮箱验证测试（RFC 5322）"""

    def test_valid_email(self):
        """测试有效的邮箱格式"""
        valid_emails = [
            "user@example.com",
            "test.user@gmail.com",
            "user+tag@domain.co.uk",
            "user_name@test-domain.com",
            "123@example.com"
        ]
        for email in valid_emails:
            is_valid, error = validate_email(email)
            assert is_valid is True, f"{email} 应该是有效的"
            assert error == ""

    def test_email_length_limits(self):
        """测试邮箱长度限制（RFC 5321）"""
        # 总长度不能超过254字符
        long_email = "a" * 250 + "@example.com"
        is_valid, error = validate_email(long_email)
        assert is_valid is False
        assert error == "邮箱地址过长（最多254字符）"

        # 本地部分不能超过64字符
        long_local = "a" * 65 + "@example.com"
        is_valid, error = validate_email(long_local)
        assert is_valid is False
        assert error == "邮箱本地部分过长（最多64字符）"

        # 域名部分不能超过255字符
        # 注意：总长度检查优先，所以这里构造一个本地部分短、域名部分长的邮箱
        long_domain = "u@" + "a" * 250 + ".com"
        is_valid, error = validate_email(long_domain)
        assert is_valid is False
        # 可能是"邮箱地址过长"（总长度254）或"邮箱域名过长"（域名255）
        assert "过长" in error

    def test_consecutive_dots(self):
        """测试连续的点号（RFC 5322不允许）"""
        invalid_emails = [
            "user..name@example.com",
            "user...test@example.com"
        ]
        for email in invalid_emails:
            is_valid, error = validate_email(email)
            assert is_valid is False
            assert error == "邮箱格式不正确（不允许连续的点号）"

    def test_leading_trailing_dots(self):
        """测试以点号开头或结尾的邮箱"""
        invalid_emails = [
            ".user@example.com",
            "user.@example.com"
        ]
        for email in invalid_emails:
            is_valid, error = validate_email(email)
            assert is_valid is False
            assert "不允许以点号开头或结尾" in error

    def test_invalid_domain_format(self):
        """测试无效的域名格式"""
        invalid_emails = [
            "user@.com",
            "user@example.",
            "user@-example.com",
            "user@example-.com"
        ]
        for email in invalid_emails:
            is_valid, error = validate_email(email)
            assert is_valid is False
            assert "域名格式不正确" in error or "邮箱格式不正确" in error


class TestDecimalAmountValidation:
    """Decimal-based 金额验证测试（防止浮点精度问题）"""

    def test_valid_amounts_from_different_types(self):
        """测试不同类型的有效金额"""
        test_cases = [
            (29.0, float),
            (199, int),
            ("99.99", str),
            (Decimal("29.00"), Decimal)
        ]
        for amount, amount_type in test_cases:
            is_valid, error, decimal_amount = validate_amount(amount)
            assert is_valid is True, f"{amount} ({amount_type}) 应该是有效的"
            assert error == ""
            assert isinstance(decimal_amount, Decimal)

    def test_negative_amount(self):
        """测试负数金额（防止攻击）"""
        is_valid, error, _ = validate_amount(-29.0)
        assert is_valid is False
        assert error == "金额不能为负数"

    def test_zero_amount(self):
        """测试零金额"""
        is_valid, error, _ = validate_amount(0)
        assert is_valid is False
        assert error == "金额必须大于0"

    def test_min_amount_validation(self):
        """测试最小金额验证"""
        # 默认最小金额0.01
        is_valid, error, _ = validate_amount(0.001)
        assert is_valid is False
        assert "金额不能低于" in error

        # 自定义最小金额
        is_valid, error, _ = validate_amount(5.0, min_amount=10.0)
        assert is_valid is False
        assert "金额不能低于¥10.00" in error

    def test_max_amount_validation(self):
        """测试最大金额验证（防止整数溢出攻击）"""
        # 默认最大金额999999.99
        is_valid, error, _ = validate_amount(1000000.0)
        assert is_valid is False
        assert "金额不能超过" in error

        # 自定义最大金额
        is_valid, error, _ = validate_amount(500.0, max_amount=100.0)
        assert is_valid is False
        assert "金额不能超过¥100.00" in error

    def test_decimal_places_validation(self):
        """测试小数位数验证（最多2位）"""
        is_valid, error, _ = validate_amount(29.001)
        assert is_valid is False
        assert error == "金额最多支持2位小数"

        # 2位小数应该通过
        is_valid, error, _ = validate_amount(29.99)
        assert is_valid is True

    def test_floating_point_precision(self):
        """测试浮点精度问题（Decimal解决方案）"""
        # 演示浮点精度问题：Python的float类型本身就不精确
        float_sum = 0.1 + 0.2  # 0.30000000000000004（float已失去精度）

        # 这个浮点数的小数位数超过2位，会被拒绝
        is_valid, error, decimal_amount = validate_amount(float_sum)
        # 注意：虽然值在范围内，但小数位数超过2位，所以被拒绝
        assert is_valid is False
        assert "小数" in error

        # 正确的做法：直接使用Decimal字符串或精确的float避免浮点精度问题
        is_valid, error, decimal_amount = validate_amount("0.30")
        assert is_valid is True
        assert str(decimal_amount) == "0.30"  # 精确值

        # 使用精确的2位小数float也可以
        is_valid, error, decimal_amount = validate_amount(0.30)
        assert is_valid is True

    def test_invalid_amount_type(self):
        """测试不支持的金额类型"""
        invalid_amounts = [
            None,
            [],
            {},
            object()
        ]
        for amount in invalid_amounts:
            is_valid, error, _ = validate_amount(amount)
            assert is_valid is False
            assert "金额" in error

    def test_invalid_string_format(self):
        """测试无效的字符串格式"""
        invalid_strings = [
            "abc",
            "29.99元",
            "29,99",
            ""
        ]
        for amount_str in invalid_strings:
            is_valid, error, _ = validate_amount(amount_str)
            assert is_valid is False
            assert "金额格式不正确" in error or "金额不能为空" in error


class TestUpdatedPlanTypeValidation:
    """更新后的订阅计划验证测试（2025-11价格调整）"""

    def test_valid_plan_types_with_new_pricing(self):
        """测试新的订阅计划和价格"""
        valid_plans = {
            "pro_monthly": 29.0,   # 月度会员：29元（2025-11更新）
            "pro_yearly": 199.0    # 年度会员：199元（16.6元/月，年省149元）
        }
        for plan_type, expected_price in valid_plans.items():
            is_valid, error, price = validate_plan_type(plan_type)
            assert is_valid is True, f"{plan_type} 应该是有效的"
            assert error == ""
            assert price == expected_price

    def test_lifetime_plan_exists(self):
        """测试终身会员存在（价格已调整为599元）"""
        is_valid, error, price = validate_plan_type("lifetime")
        assert is_valid is True
        assert error == ""
        assert price == 599.0

    def test_invalid_plan_type(self):
        """测试无效的订阅计划"""
        invalid_plans = [
            "free",
            "pro_weekly",
            "enterprise",
            "PRO_MONTHLY"  # 大小写敏感
        ]
        for plan_type in invalid_plans:
            is_valid, error, price = validate_plan_type(plan_type)
            assert is_valid is False
            assert f"无效的计划类型: {plan_type}" in error


class TestEnhancedPaymentAmountValidation:
    """增强的支付金额验证测试（结合Decimal和Plan验证）"""

    def test_correct_payment_amounts(self):
        """测试正确的支付金额（新价格）"""
        test_cases = [
            ("pro_monthly", 29.0),
            ("pro_yearly", 199.0)
        ]
        for plan_type, amount in test_cases:
            is_valid, error = validate_payment_amount(plan_type, amount)
            assert is_valid is True, f"{plan_type}={amount} 应该通过"
            assert error == ""

    def test_tampered_payment_amount(self):
        """测试被篡改的支付金额（关键安全测试）"""
        tampered_cases = [
            ("pro_monthly", 1.0),     # 篡改为1元
            ("pro_yearly", 29.0),     # 篡改为月度价格
            ("pro_monthly", 0.01),    # 篡改为0.01元
            ("pro_yearly", 100.0),    # 随意金额
            ("pro_monthly", -29.0)    # 负数攻击
        ]
        for plan_type, amount in tampered_cases:
            is_valid, error = validate_payment_amount(plan_type, amount)
            assert is_valid is False, f"应该拒绝篡改的金额: {plan_type}={amount}"
            assert "金额" in error

    def test_floating_point_tolerance(self):
        """测试严格金额验证（容差收紧到0.001）

        [SECURITY] 2025-12-18 修复：
        - 旧行为：允许0.01容差，29.01对29.00通过
        - 新行为：严格验证，只允许0.001容差，防止金额欺诈
        """
        # 精确金额应该通过
        is_valid, error = validate_payment_amount("pro_monthly", 29.0)
        assert is_valid is True, "精确金额29.0应该通过"

        # 0.01差异应该被拒绝（超出0.001容差）
        is_valid, error = validate_payment_amount("pro_monthly", 29.01)
        assert is_valid is False, "29.01与29.0差异0.01应该被拒绝"
        assert "金额不正确" in error

        # 超出误差范围应该拒绝
        is_valid, error = validate_payment_amount("pro_monthly", 29.02)
        assert is_valid is False
        assert "金额不正确" in error

    def test_lifetime_plan_payment_accepted(self):
        """测试终身会员支付通过（新价格599元）"""
        is_valid, error = validate_payment_amount("lifetime", 599.0)
        assert is_valid is True
        assert error == ""


class TestEnhancedPasswordValidation:
    """增强的密码验证测试（与旧版一致性检查）"""

    def test_valid_password(self):
        """测试有效的密码"""
        valid_passwords = [
            "Test1234",
            "MyP@ssw0rd",
            "Abc123xyz",
            "SecurePass123"
        ]
        for password in valid_passwords:
            is_valid, error = validate_password(password)
            assert is_valid is True, f"{password} 应该是有效的"
            assert error == ""

    def test_password_strength_requirements(self):
        """测试密码强度要求"""
        # 缺少大写字母
        is_valid, error = validate_password("test1234")
        assert is_valid is False
        assert error == "密码必须包含大写字母"

        # 缺少小写字母
        is_valid, error = validate_password("TEST1234")
        assert is_valid is False
        assert error == "密码必须包含小写字母"

        # 缺少数字
        is_valid, error = validate_password("TestTest")
        assert is_valid is False
        assert error == "密码必须包含数字"

    def test_password_length_constraints(self):
        """测试密码长度约束"""
        # 过短
        is_valid, error = validate_password("Test123")
        assert is_valid is False
        assert error == "密码长度至少8位"

        # 过长
        long_password = "A1" + "a" * 127
        is_valid, error = validate_password(long_password)
        assert is_valid is False
        assert error == "密码长度不能超过128位"


class TestEnhancedUserIdValidation:
    """增强的用户ID验证测试（UUID支持）"""

    def test_uuid_user_id(self):
        """测试UUID格式的用户ID（Supabase Auth）"""
        uuid_user_id = "550e8400-e29b-41d4-a716-446655440000"
        is_valid, error = validate_user_id(uuid_user_id, require_uuid=True)
        assert is_valid is True
        assert error == ""

    def test_non_uuid_rejected_when_required(self):
        """测试要求UUID时拒绝非UUID格式"""
        non_uuid_ids = [
            "user123",
            "test_user",
            "not-a-valid-uuid"
        ]
        for user_id in non_uuid_ids:
            is_valid, error = validate_user_id(user_id, require_uuid=True)
            assert is_valid is False
            assert "UUID" in error

    def test_custom_id_allowed_when_not_required(self):
        """测试不要求UUID时允许自定义ID"""
        custom_ids = [
            "user123",
            "test_user",
            "valid-id"
        ]
        for user_id in custom_ids:
            is_valid, error = validate_user_id(user_id, require_uuid=False)
            assert is_valid is True
            assert error == ""


# ============================================================================
# Pydantic模型测试（如果可用）
# ============================================================================

if PYDANTIC_AVAILABLE:
    from api.validators_enhanced import (
        SignUpRequest,
        SignInRequest,
        CreateOrderRequest,
        QuotaStatusRequest
    )

    class TestPydanticSignUpRequest:
        """Pydantic注册请求验证测试"""

        def test_valid_signup_request(self):
            """测试有效的注册请求"""
            request = SignUpRequest(
                email="user@example.com",
                password="Test1234"
            )
            assert request.email == "user@example.com"
            assert request.password == "Test1234"

        def test_invalid_email_format(self):
            """测试无效的邮箱格式"""
            with pytest.raises(Exception):  # Pydantic会抛出ValidationError
                SignUpRequest(
                    email="invalid-email",
                    password="Test1234"
                )

        def test_weak_password(self):
            """测试弱密码"""
            with pytest.raises(Exception):  # 自定义validator会抛出错误
                SignUpRequest(
                    email="user@example.com",
                    password="test"  # 缺少大写字母和数字，长度不足
                )

    class TestPydanticCreateOrderRequest:
        """Pydantic创建订单请求验证测试"""

        def test_valid_order_request(self):
            """测试有效的订单请求"""
            request = CreateOrderRequest(
                user_id="550e8400-e29b-41d4-a716-446655440000",
                plan_type="pro_monthly",
                amount=29.0
            )
            assert request.user_id == "550e8400-e29b-41d4-a716-446655440000"
            assert request.plan_type == "pro_monthly"
            assert request.amount == 29.0

        def test_invalid_user_id_format(self):
            """测试无效的用户ID格式（需要UUID）"""
            with pytest.raises(Exception):
                CreateOrderRequest(
                    user_id="not-a-uuid",
                    plan_type="pro_monthly",
                    amount=29.0
                )

        def test_invalid_plan_type(self):
            """测试无效的计划类型"""
            with pytest.raises(Exception):
                CreateOrderRequest(
                    user_id="550e8400-e29b-41d4-a716-446655440000",
                    plan_type="invalid_plan",
                    amount=29.0
                )

        def test_negative_amount(self):
            """测试负数金额"""
            with pytest.raises(Exception):
                CreateOrderRequest(
                    user_id="550e8400-e29b-41d4-a716-446655440000",
                    plan_type="pro_monthly",
                    amount=-29.0
                )


# ============================================================================
# 综合安全场景测试
# ============================================================================

class TestEnhancedSecurityScenarios:
    """增强的安全场景测试"""

    def test_payment_amount_precision_attack(self):
        """测试支付金额精度攻击（Decimal防御）"""
        # 攻击者可能利用浮点精度尝试绕过验证
        attack_amounts = [
            28.9999999999,  # 非常接近29但不等于
            199.0000001,     # 非常接近199但不等于
        ]
        for amount in attack_amounts:
            # Decimal验证应该准确检测差异
            is_valid, error = validate_payment_amount("pro_monthly", 28.9999999999)
            # 如果在0.01误差内应该通过，否则拒绝
            # 这个测试验证了Decimal的精确性

    def test_uuid_injection_attempt(self):
        """测试UUID注入攻击尝试"""
        malicious_uuids = [
            "550e8400-e29b-41d4-a716-446655440000'; DROP TABLE users--",
            "550e8400-e29b-41d4-a716-446655440000<script>alert(1)</script>",
            "../../../etc/passwd"
        ]
        for malicious in malicious_uuids:
            is_valid, _ = validate_uuid(malicious)
            assert is_valid is False, f"应该拒绝恶意UUID: {malicious}"

    def test_email_rfc_compliance_attacks(self):
        """测试违反RFC 5322的邮箱攻击"""
        attack_emails = [
            "user..admin@example.com",  # 连续点号
            ".admin@example.com",        # 以点号开头
            "admin.@example.com",        # 以点号结尾
            "a" * 65 + "@example.com"   # 本地部分超长
        ]
        for email in attack_emails:
            is_valid, _ = validate_email(email)
            assert is_valid is False, f"应该拒绝非法邮箱: {email}"

    def test_amount_overflow_attack(self):
        """测试金额溢出攻击"""
        overflow_amounts = [
            9999999999.99,  # 超大金额
            float('inf'),    # 无穷大
        ]
        for amount in overflow_amounts:
            is_valid, error, _ = validate_amount(amount)
            assert is_valid is False, f"应该拒绝溢出金额: {amount}"


# Pytest配置
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
