"""
API输入验证器（增强版）
提供统一的输入验证逻辑，确保API安全性
"""
import re
import uuid
from typing import Tuple, Optional, Any, Dict
from decimal import Decimal, InvalidOperation


# ============================================================================
# UUID验证（用于Supabase user_id）
# ============================================================================

def validate_uuid(value: str) -> Tuple[bool, str]:
    """
    验证UUID格式（RFC 4122标准）

    Args:
        value: UUID字符串

    Returns:
        (是否有效, 错误消息)
    """
    if not value:
        return False, "UUID不能为空"

    try:
        # 尝试解析UUID（支持UUID v1-v5）
        uuid_obj = uuid.UUID(value)

        # 验证格式（标准格式：8-4-4-4-12）
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if not re.match(uuid_pattern, value.lower()):
            return False, "UUID格式不正确"

        return True, ""

    except ValueError:
        return False, "UUID格式不正确"
    except Exception as e:
        return False, f"UUID验证失败: {str(e)}"


# ============================================================================
# 邮箱验证（严格模式）
# ============================================================================

def validate_email(email: str) -> Tuple[bool, str]:
    """
    验证邮箱格式（RFC 5322标准）

    Args:
        email: 邮箱地址

    Returns:
        (是否有效, 错误消息)
    """
    if not email:
        return False, "邮箱不能为空"

    # 长度限制（RFC 5321: local_part ≤ 64, domain ≤ 255, total ≤ 254）
    if len(email) > 254:
        return False, "邮箱地址过长（最多254字符）"

    # 严格邮箱格式验证
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "邮箱格式不正确"

    # 分离本地部分和域名部分
    try:
        local_part, domain = email.rsplit('@', 1)
    except ValueError:
        return False, "邮箱格式不正确（缺少@符号）"

    # 本地部分验证
    if len(local_part) > 64:
        return False, "邮箱本地部分过长（最多64字符）"

    # 检查连续的点号（不符合RFC 5322标准）
    if '..' in local_part:
        return False, "邮箱格式不正确（不允许连续的点号）"

    # 检查是否以点号开头或结尾
    if local_part.startswith('.') or local_part.endswith('.'):
        return False, "邮箱格式不正确（不允许以点号开头或结尾）"

    # 域名验证
    if len(domain) > 255:
        return False, "邮箱域名过长（最多255字符）"

    # 域名格式验证
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
    if not re.match(domain_pattern, domain):
        return False, "邮箱域名格式不正确"

    return True, ""


# ============================================================================
# 金额验证（增强版，防止负数和超大金额）
# ============================================================================

def validate_amount(amount: Any, min_amount: float = 0.01, max_amount: float = 999999.99) -> Tuple[bool, str, Optional[Decimal]]:
    """
    验证金额格式和范围

    Args:
        amount: 金额（可以是float、int、str或Decimal）
        min_amount: 最小金额（默认0.01）
        max_amount: 最大金额（默认999999.99）

    Returns:
        (是否有效, 错误消息, Decimal格式的金额)
    """
    if amount is None:
        return False, "金额不能为空", None

    # 转换为Decimal（避免浮点精度问题）
    try:
        if isinstance(amount, Decimal):
            decimal_amount = amount
        elif isinstance(amount, (int, float)):
            decimal_amount = Decimal(str(amount))
        elif isinstance(amount, str):
            decimal_amount = Decimal(amount)
        else:
            return False, f"金额类型不支持: {type(amount).__name__}", None
    except (InvalidOperation, ValueError):
        return False, "金额格式不正确", None

    # 防止负数
    if decimal_amount < 0:
        return False, "金额不能为负数", None

    # 防止零金额（根据业务需求）
    if decimal_amount == 0:
        return False, "金额必须大于0", None

    # 最小金额验证
    if decimal_amount < Decimal(str(min_amount)):
        return False, f"金额不能低于¥{min_amount:.2f}", None

    # 防止超大金额（防止整数溢出攻击）
    if decimal_amount > Decimal(str(max_amount)):
        return False, f"金额不能超过¥{max_amount:.2f}", None

    # 验证小数位数（最多2位）
    if decimal_amount.as_tuple().exponent < -2:
        return False, "金额最多支持2位小数", None

    return True, "", decimal_amount


def validate_plan_type(plan_type: str) -> Tuple[bool, str, Optional[float]]:
    """
    验证订阅计划类型并返回正确的价格

    Args:
        plan_type: 计划类型

    Returns:
        (是否有效, 错误消息, 正确的价格)
    """
    # ✅ 安全：定义合法的计划和对应的价格（与前端UI保持一致）
    VALID_PLANS = {
        "pro_monthly": 29.0,   # 月度会员：29元（2025-11更新）
        "pro_yearly": 199.0,   # 年度会员：199元（16.6元/月，年省149元）
        # "lifetime": 暂时隐藏（后续调整价格后启用）
    }

    if not plan_type:
        return False, "计划类型不能为空", None

    if plan_type not in VALID_PLANS:
        return False, f"无效的计划类型: {plan_type}", None

    return True, "", VALID_PLANS[plan_type]


def validate_payment_amount(plan_type: str, submitted_amount: Any) -> Tuple[bool, str]:
    """
    验证支付金额是否与计划类型匹配（增强版）

    Args:
        plan_type: 计划类型
        submitted_amount: 提交的金额

    Returns:
        (是否有效, 错误消息)
    """
    # 1. 验证计划类型
    is_valid_plan, error, correct_amount = validate_plan_type(plan_type)
    if not is_valid_plan:
        return False, error

    # 2. 验证金额格式和范围
    is_valid_amount, error, decimal_amount = validate_amount(submitted_amount, min_amount=0.01, max_amount=10000.0)
    if not is_valid_amount:
        return False, error

    # 3. 严格验证：提交的金额必须与计划价格完全一致
    correct_decimal = Decimal(str(correct_amount))
    if abs(decimal_amount - correct_decimal) > Decimal("0.01"):  # 允许0.01的浮点误差
        return False, f"金额不正确，{plan_type}的价格应为¥{correct_amount:.2f}"

    return True, ""


# ============================================================================
# 手机号验证
# ============================================================================

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

    # 中国手机号：1开头，第二位为3-9，共11位数字
    pattern = r'^1[3-9]\d{9}$'
    if not re.match(pattern, phone):
        return False, "手机号格式不正确"

    return True, ""


# ============================================================================
# 密码验证
# ============================================================================

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


# ============================================================================
# 用户ID验证（兼容UUID和自定义ID）
# ============================================================================

def validate_user_id(user_id: str, require_uuid: bool = True) -> Tuple[bool, str]:
    """
    验证用户ID格式

    Args:
        user_id: 用户ID
        require_uuid: 是否要求UUID格式（Supabase Auth使用UUID）

    Returns:
        (是否有效, 错误消息)
    """
    if not user_id:
        return False, "用户ID不能为空"

    # 如果要求UUID格式（Supabase Auth的默认格式）
    if require_uuid:
        return validate_uuid(user_id)

    # 兼容模式：允许自定义ID格式
    if len(user_id) < 3:
        return False, "用户ID长度至少3位"

    if len(user_id) > 64:
        return False, "用户ID长度不能超过64位"

    # 允许字母、数字、下划线、连字符
    pattern = r'^[a-zA-Z0-9_-]+$'
    if not re.match(pattern, user_id):
        return False, "用户ID只能包含字母、数字、下划线和连字符"

    return True, ""


# ============================================================================
# 配额类型验证
# ============================================================================

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


# ============================================================================
# OTP验证码验证
# ============================================================================

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


# ============================================================================
# 字符串清理（防止XSS、SQL注入等）
# ============================================================================

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

    # 移除控制字符（防止注入攻击）
    cleaned = re.sub(r'[\x00-\x1F\x7F]', '', input_str)

    # 截断到最大长度（防止缓冲区溢出）
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]

    return cleaned.strip()


# ============================================================================
# Pydantic模型（结构化验证）
# ============================================================================

try:
    from pydantic import BaseModel, Field, EmailStr, field_validator
    from pydantic_core import PydanticCustomError

    class SignUpRequest(BaseModel):
        """注册请求验证模型"""
        email: EmailStr = Field(..., description="邮箱地址")
        password: str = Field(..., min_length=8, max_length=128, description="密码")

        @field_validator('password')
        @classmethod
        def validate_password_strength(cls, v: str) -> str:
            """验证密码强度"""
            is_valid, error = validate_password(v)
            if not is_valid:
                raise PydanticCustomError('password_weak', error)
            return v

    class SignInRequest(BaseModel):
        """登录请求验证模型"""
        email: EmailStr = Field(..., description="邮箱地址")
        password: str = Field(..., min_length=1, max_length=128, description="密码")

    class CreateOrderRequest(BaseModel):
        """创建订单请求验证模型"""
        user_id: str = Field(..., description="用户ID（UUID格式）")
        plan_type: str = Field(..., description="计划类型")
        amount: float = Field(..., gt=0, description="支付金额")

        @field_validator('user_id')
        @classmethod
        def validate_user_id_format(cls, v: str) -> str:
            """验证用户ID格式"""
            is_valid, error = validate_user_id(v, require_uuid=True)
            if not is_valid:
                raise PydanticCustomError('invalid_user_id', error)
            return v

        @field_validator('plan_type')
        @classmethod
        def validate_plan_type_enum(cls, v: str) -> str:
            """验证计划类型"""
            is_valid, error, _ = validate_plan_type(v)
            if not is_valid:
                raise PydanticCustomError('invalid_plan_type', error)
            return v

        @field_validator('amount')
        @classmethod
        def validate_amount_range(cls, v: float) -> float:
            """验证金额范围"""
            is_valid, error, _ = validate_amount(v)
            if not is_valid:
                raise PydanticCustomError('invalid_amount', error)
            return v

    class QuotaStatusRequest(BaseModel):
        """配额状态请求验证模型"""
        user_id: str = Field(..., description="用户ID（UUID格式）")
        quota_type: Optional[str] = Field(None, description="配额类型")

        @field_validator('user_id')
        @classmethod
        def validate_user_id_format(cls, v: str) -> str:
            is_valid, error = validate_user_id(v, require_uuid=True)
            if not is_valid:
                raise PydanticCustomError('invalid_user_id', error)
            return v

        @field_validator('quota_type')
        @classmethod
        def validate_quota_type_enum(cls, v: Optional[str]) -> Optional[str]:
            if v is None:
                return v
            is_valid, error = validate_quota_type(v)
            if not is_valid:
                raise PydanticCustomError('invalid_quota_type', error)
            return v

    # 标记Pydantic可用
    PYDANTIC_AVAILABLE = True

except ImportError:
    # Pydantic未安装，使用函数验证作为降级方案
    PYDANTIC_AVAILABLE = False

    # 定义占位符类
    class SignUpRequest:
        pass

    class SignInRequest:
        pass

    class CreateOrderRequest:
        pass

    class QuotaStatusRequest:
        pass
