"""
API输入验证器
提供统一的输入验证逻辑，确保API安全性
"""
import re
from typing import Tuple, Optional


def validate_email(email: str) -> Tuple[bool, str]:
    """
    验证邮箱格式

    Args:
        email: 邮箱地址

    Returns:
        (是否有效, 错误消息)
    """
    if not email:
        return False, "邮箱不能为空"

    # 基本邮箱格式验证
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "邮箱格式不正确"

    # 长度限制
    if len(email) > 254:
        return False, "邮箱地址过长"

    # 检查连续的点号（不符合RFC 5322标准）
    local_part = email.split('@')[0]
    if '..' in local_part:
        return False, "邮箱格式不正确"

    # 检查是否以点号开头或结尾
    if local_part.startswith('.') or local_part.endswith('.'):
        return False, "邮箱格式不正确"

    return True, ""


def validate_phone(phone: str) -> Tuple[bool, str]:
    """
    验证中国手机号格式

    Args:
        phone: 手机号

    Returns:
        (是否有效, 错误消息)
    """
    if not phone:
        return False, "手机号不能为空"

    # 中国手机号：1开头，11位数字
    pattern = r'^1[3-9]\d{9}$'
    if not re.match(pattern, phone):
        return False, "手机号格式不正确"

    return True, ""


def validate_password(password: str, min_length: int = 8) -> Tuple[bool, str]:
    """
    验证密码强度

    Args:
        password: 密码
        min_length: 最小长度，默认8

    Returns:
        (是否有效, 错误消息)
    """
    if not password:
        return False, "密码不能为空"

    if len(password) < min_length:
        return False, f"密码长度至少{min_length}位"

    if len(password) > 128:
        return False, "密码长度不能超过128位"

    # 检查是否包含大写字母
    if not re.search(r'[A-Z]', password):
        return False, "密码必须包含大写字母"

    # 检查是否包含小写字母
    if not re.search(r'[a-z]', password):
        return False, "密码必须包含小写字母"

    # 检查是否包含数字
    if not re.search(r'[0-9]', password):
        return False, "密码必须包含数字"

    return True, ""


def validate_plan_type(plan_type: str) -> Tuple[bool, str, Optional[float]]:
    """
    验证订阅计划类型并返回正确的价格

    ⚠️ 关键修复: 从SubscriptionManager读取价格,确保全局统一

    Args:
        plan_type: 计划类型

    Returns:
        (是否有效, 错误消息, 正确的价格)
    """
    # ✅ 修复: 从SubscriptionManager导入,确保价格一致
    try:
        from subscription_manager import SubscriptionManager
    except ImportError:
        import os
        import sys
        sys.path.insert(0, os.path.dirname(__file__))
        from subscription_manager import SubscriptionManager

    sm = SubscriptionManager()

    if not plan_type:
        return False, "计划类型不能为空", None

    if plan_type not in sm.PLANS:
        return False, f"无效的计划类型: {plan_type}", None

    return True, "", sm.PLANS[plan_type]["price"]


def validate_payment_amount(plan_type: str, submitted_amount: float) -> Tuple[bool, str]:
    """
    验证支付金额是否与计划类型匹配

    Args:
        plan_type: 计划类型
        submitted_amount: 提交的金额

    Returns:
        (是否有效, 错误消息)
    """
    is_valid, error, correct_amount = validate_plan_type(plan_type)

    if not is_valid:
        return False, error

    # ✅ 严格验证：提交的金额必须与计划价格完全一致
    if abs(submitted_amount - correct_amount) > 0.01:  # 允许0.01的浮点误差
        return False, f"金额不正确，{plan_type}的价格应为¥{correct_amount:.2f}"

    return True, ""


def validate_user_id(user_id: str) -> Tuple[bool, str]:
    """
    验证用户ID格式

    Args:
        user_id: 用户ID

    Returns:
        (是否有效, 错误消息)
    """
    if not user_id:
        return False, "用户ID不能为空"

    # 长度限制
    if len(user_id) < 3:
        return False, "用户ID长度至少3位"

    if len(user_id) > 64:
        return False, "用户ID长度不能超过64位"

    # 允许字母、数字、下划线、连字符
    pattern = r'^[a-zA-Z0-9_-]+$'
    if not re.match(pattern, user_id):
        return False, "用户ID只能包含字母、数字、下划线和连字符"

    return True, ""


def validate_quota_type(quota_type: str) -> Tuple[bool, str]:
    """
    验证配额类型

    Args:
        quota_type: 配额类型

    Returns:
        (是否有效, 错误消息)
    """
    VALID_QUOTA_TYPES = [
        "daily_plan",
        "weekly_report",
        "chat",
        "theme_recommend",
        "theme_generate"
    ]

    if not quota_type:
        return False, "配额类型不能为空"

    if quota_type not in VALID_QUOTA_TYPES:
        return False, f"无效的配额类型: {quota_type}"

    return True, ""


def sanitize_string(input_str: str, max_length: int = 255) -> str:
    """
    清理字符串，移除潜在危险字符

    Args:
        input_str: 输入字符串
        max_length: 最大长度

    Returns:
        清理后的字符串
    """
    if not input_str:
        return ""

    # 移除控制字符
    cleaned = re.sub(r'[\x00-\x1F\x7F]', '', input_str)

    # 截断到最大长度
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]

    return cleaned.strip()


def validate_otp_code(otp_code: str) -> Tuple[bool, str]:
    """
    验证OTP验证码格式

    Args:
        otp_code: OTP验证码

    Returns:
        (是否有效, 错误消息)
    """
    if not otp_code:
        return False, "验证码不能为空"

    # 6位数字
    pattern = r'^\d{6}$'
    if not re.match(pattern, otp_code):
        return False, "验证码格式不正确（应为6位数字）"

    return True, ""
