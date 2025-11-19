"""
validators.py 单元测试
测试所有输入验证函数，确保安全性和正确性
"""
import pytest
from api.validators import (
    validate_email,
    validate_phone,
    validate_password,
    validate_plan_type,
    validate_payment_amount,
    validate_user_id,
    validate_quota_type,
    sanitize_string,
    validate_otp_code
)


class TestEmailValidation:
    """邮箱验证测试"""

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

    def test_invalid_email_format(self):
        """测试无效的邮箱格式"""
        invalid_emails = [
            "invalid",
            "@example.com",
            "user@",
            "user @example.com",
            "user@example",
            "user..name@example.com",
            "user@.com"
        ]
        for email in invalid_emails:
            is_valid, error = validate_email(email)
            assert is_valid is False, f"{email} 应该是无效的"
            assert error == "邮箱格式不正确"

    def test_empty_email(self):
        """测试空邮箱"""
        is_valid, error = validate_email("")
        assert is_valid is False
        assert error == "邮箱不能为空"

    def test_email_too_long(self):
        """测试超长邮箱"""
        long_email = "a" * 250 + "@example.com"  # 超过254字符
        is_valid, error = validate_email(long_email)
        assert is_valid is False
        assert error == "邮箱地址过长"


class TestPhoneValidation:
    """手机号验证测试"""

    def test_valid_phone(self):
        """测试有效的中国手机号"""
        valid_phones = [
            "13812345678",
            "15987654321",
            "18612345678",
            "19912345678"
        ]
        for phone in valid_phones:
            is_valid, error = validate_phone(phone)
            assert is_valid is True, f"{phone} 应该是有效的"
            assert error == ""

    def test_invalid_phone_format(self):
        """测试无效的手机号格式"""
        invalid_phones = [
            "12345678901",  # 不是1开头
            "1381234567",   # 只有10位
            "138123456789", # 有12位
            "11812345678",  # 第二位不是3-9
            "138-1234-5678", # 包含连字符
            "138 1234 5678"  # 包含空格
        ]
        for phone in invalid_phones:
            is_valid, error = validate_phone(phone)
            assert is_valid is False, f"{phone} 应该是无效的"
            assert error == "手机号格式不正确"

    def test_empty_phone(self):
        """测试空手机号"""
        is_valid, error = validate_phone("")
        assert is_valid is False
        assert error == "手机号不能为空"


class TestPasswordValidation:
    """密码验证测试"""

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

    def test_password_too_short(self):
        """测试过短的密码"""
        is_valid, error = validate_password("Test123")  # 7位
        assert is_valid is False
        assert error == "密码长度至少8位"

    def test_password_too_long(self):
        """测试过长的密码"""
        long_password = "A1" + "a" * 127  # 129位
        is_valid, error = validate_password(long_password)
        assert is_valid is False
        assert error == "密码长度不能超过128位"

    def test_password_missing_uppercase(self):
        """测试缺少大写字母的密码"""
        is_valid, error = validate_password("test1234")
        assert is_valid is False
        assert error == "密码必须包含大写字母"

    def test_password_missing_lowercase(self):
        """测试缺少小写字母的密码"""
        is_valid, error = validate_password("TEST1234")
        assert is_valid is False
        assert error == "密码必须包含小写字母"

    def test_password_missing_digit(self):
        """测试缺少数字的密码"""
        is_valid, error = validate_password("TestTest")
        assert is_valid is False
        assert error == "密码必须包含数字"

    def test_empty_password(self):
        """测试空密码"""
        is_valid, error = validate_password("")
        assert is_valid is False
        assert error == "密码不能为空"

    def test_custom_min_length(self):
        """测试自定义最小长度"""
        is_valid, error = validate_password("Test12", min_length=10)
        assert is_valid is False
        assert error == "密码长度至少10位"


class TestPlanTypeValidation:
    """订阅计划验证测试"""

    def test_valid_plan_types(self):
        """测试所有有效的订阅计划"""
        valid_plans = {
            "pro_monthly": 29.0,
            "pro_yearly": 199.0,
            "lifetime": 599.0
        }
        for plan_type, expected_price in valid_plans.items():
            is_valid, error, price = validate_plan_type(plan_type)
            assert is_valid is True, f"{plan_type} 应该是有效的"
            assert error == ""
            assert price == expected_price

    def test_invalid_plan_type(self):
        """测试无效的订阅计划"""
        invalid_plans = [
            "free",
            "enterprise",
            "pro_weekly",
            "fake_plan",
            "PRO_MONTHLY"  # 大小写敏感
        ]
        for plan_type in invalid_plans:
            is_valid, error, price = validate_plan_type(plan_type)
            assert is_valid is False
            assert f"无效的计划类型: {plan_type}" in error
            assert price is None

    def test_empty_plan_type(self):
        """测试空计划类型"""
        is_valid, error, price = validate_plan_type("")
        assert is_valid is False
        assert error == "计划类型不能为空"
        assert price is None


class TestPaymentAmountValidation:
    """支付金额验证测试（防篡改）"""

    def test_correct_payment_amount(self):
        """测试正确的支付金额"""
        test_cases = [
            ("pro_monthly", 29.0),
            ("pro_yearly", 199.0),
            ("lifetime", 599.0)
        ]
        for plan_type, amount in test_cases:
            is_valid, error = validate_payment_amount(plan_type, amount)
            assert is_valid is True
            assert error == ""

    def test_tampered_payment_amount(self):
        """测试被篡改的支付金额（关键安全测试）"""
        tampered_cases = [
            ("pro_monthly", 1.0),    # 篡改为1元
            ("pro_yearly", 29.0),    # 篡改为月度价格
            ("lifetime", 0.01),      # 篡改为0.01元
            ("pro_monthly", 100.0)   # 随意金额
        ]
        for plan_type, amount in tampered_cases:
            is_valid, error = validate_payment_amount(plan_type, amount)
            assert is_valid is False, f"应该拒绝篡改的金额: {plan_type}={amount}"
            assert "金额不正确" in error

    def test_floating_point_precision(self):
        """测试浮点数精度（允许0.01误差）"""
        is_valid, error = validate_payment_amount("pro_monthly", 29.001)
        assert is_valid is True  # 在误差范围内

        is_valid, error = validate_payment_amount("pro_monthly", 29.02)
        assert is_valid is False  # 超出误差范围

    def test_invalid_plan_in_payment(self):
        """测试无效计划类型的支付"""
        is_valid, error = validate_payment_amount("fake_plan", 100.0)
        assert is_valid is False
        assert "无效的计划类型" in error


class TestUserIdValidation:
    """用户ID验证测试"""

    def test_valid_user_id(self):
        """测试有效的用户ID"""
        valid_ids = [
            "user123",
            "test_user",
            "user-name",
            "abc123_xyz",
            "UUID-1234-5678"
        ]
        for user_id in valid_ids:
            is_valid, error = validate_user_id(user_id)
            assert is_valid is True, f"{user_id} 应该是有效的"
            assert error == ""

    def test_user_id_too_short(self):
        """测试过短的用户ID"""
        is_valid, error = validate_user_id("ab")
        assert is_valid is False
        assert error == "用户ID长度至少3位"

    def test_user_id_too_long(self):
        """测试过长的用户ID"""
        long_id = "a" * 65
        is_valid, error = validate_user_id(long_id)
        assert is_valid is False
        assert error == "用户ID长度不能超过64位"

    def test_user_id_invalid_characters(self):
        """测试包含非法字符的用户ID"""
        invalid_ids = [
            "user@123",
            "user#name",
            "user name",
            "user.name",
            "用户123"  # 中文
        ]
        for user_id in invalid_ids:
            is_valid, error = validate_user_id(user_id)
            assert is_valid is False
            assert error == "用户ID只能包含字母、数字、下划线和连字符"

    def test_empty_user_id(self):
        """测试空用户ID"""
        is_valid, error = validate_user_id("")
        assert is_valid is False
        assert error == "用户ID不能为空"


class TestQuotaTypeValidation:
    """配额类型验证测试"""

    def test_valid_quota_types(self):
        """测试所有有效的配额类型"""
        valid_types = [
            "daily_plan",
            "weekly_report",
            "chat",
            "theme_recommend",
            "theme_generate"
        ]
        for quota_type in valid_types:
            is_valid, error = validate_quota_type(quota_type)
            assert is_valid is True, f"{quota_type} 应该是有效的"
            assert error == ""

    def test_invalid_quota_type(self):
        """测试无效的配额类型"""
        invalid_types = [
            "monthly_plan",
            "daily_report",
            "chatbot",
            "theme_create",
            "invalid"
        ]
        for quota_type in invalid_types:
            is_valid, error = validate_quota_type(quota_type)
            assert is_valid is False
            assert f"无效的配额类型: {quota_type}" in error

    def test_empty_quota_type(self):
        """测试空配额类型"""
        is_valid, error = validate_quota_type("")
        assert is_valid is False
        assert error == "配额类型不能为空"


class TestSanitizeString:
    """字符串清理测试"""

    def test_normal_string(self):
        """测试正常字符串"""
        result = sanitize_string("Hello World")
        assert result == "Hello World"

    def test_remove_control_characters(self):
        """测试移除控制字符"""
        result = sanitize_string("Hello\x00\x01\x1FWorld\x7F")
        assert result == "HelloWorld"

    def test_truncate_long_string(self):
        """测试截断超长字符串"""
        long_string = "a" * 300
        result = sanitize_string(long_string, max_length=100)
        assert len(result) == 100

    def test_strip_whitespace(self):
        """测试去除首尾空白"""
        result = sanitize_string("  Hello World  ")
        assert result == "Hello World"

    def test_empty_string(self):
        """测试空字符串"""
        result = sanitize_string("")
        assert result == ""

    def test_none_input(self):
        """测试None输入"""
        result = sanitize_string(None)
        assert result == ""


class TestOTPCodeValidation:
    """OTP验证码验证测试"""

    def test_valid_otp(self):
        """测试有效的6位OTP"""
        valid_codes = [
            "123456",
            "000000",
            "999999",
            "012345"
        ]
        for otp in valid_codes:
            is_valid, error = validate_otp_code(otp)
            assert is_valid is True, f"{otp} 应该是有效的"
            assert error == ""

    def test_invalid_otp_length(self):
        """测试无效长度的OTP"""
        invalid_codes = [
            "12345",    # 5位
            "1234567",  # 7位
            "123",      # 3位
        ]
        for otp in invalid_codes:
            is_valid, error = validate_otp_code(otp)
            assert is_valid is False
            assert error == "验证码格式不正确（应为6位数字）"

    def test_otp_with_letters(self):
        """测试包含字母的OTP"""
        invalid_codes = [
            "12345a",
            "abc123",
            "ABCDEF"
        ]
        for otp in invalid_codes:
            is_valid, error = validate_otp_code(otp)
            assert is_valid is False
            assert error == "验证码格式不正确（应为6位数字）"

    def test_empty_otp(self):
        """测试空OTP"""
        is_valid, error = validate_otp_code("")
        assert is_valid is False
        assert error == "验证码不能为空"


class TestSecurityScenarios:
    """综合安全场景测试"""

    def test_sql_injection_attempt(self):
        """测试SQL注入尝试"""
        malicious_inputs = [
            "user'; DROP TABLE users--",
            "admin' OR '1'='1",
            "1' UNION SELECT * FROM users--"
        ]
        for malicious in malicious_inputs:
            # 邮箱验证应拒绝
            is_valid, _ = validate_email(malicious)
            assert is_valid is False

    def test_xss_attempt_in_user_id(self):
        """测试XSS攻击尝试"""
        malicious_ids = [
            "<script>alert('xss')</script>",
            "user<img src=x onerror=alert(1)>",
            "user';--"
        ]
        for malicious in malicious_ids:
            is_valid, _ = validate_user_id(malicious)
            assert is_valid is False

    def test_payment_amount_tampering_scenarios(self):
        """测试支付金额篡改场景（关键安全测试）"""
        scenarios = [
            # (计划类型, 用户提交金额, 应该被拒绝)
            ("pro_yearly", 0.01, True),    # 篡改为1分钱
            ("lifetime", 199.0, True),     # 篡改为年度价格
            ("pro_monthly", -29.0, True),  # 负数
            ("pro_monthly", 29.00, False), # 正确金额
        ]
        for plan, amount, should_reject in scenarios:
            is_valid, _ = validate_payment_amount(plan, amount)
            if should_reject:
                assert is_valid is False, f"应该拒绝篡改: {plan}={amount}"
            else:
                assert is_valid is True, f"应该接受正确金额: {plan}={amount}"


# Pytest配置
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
