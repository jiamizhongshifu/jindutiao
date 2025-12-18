"""
GaiYa每日进度条 - CORS安全配置
定义允许访问API的可信来源，防止跨站请求伪造
"""
import os
from typing import List

# 检测是否为生产环境
_IS_PRODUCTION = os.getenv("VERCEL_ENV") == "production"

# 允许的CORS源白名单
# 生产环境仅包含实际部署的域名
ALLOWED_ORIGINS: List[str] = [
    # Vercel生产环境
    "https://jindutiao.vercel.app",

    # 自定义域名（如果配置了）
    "https://gaiya.app",
    "https://www.gaiya.app",
    "https://gaiyatime.com",
    "https://www.gaiyatime.com",
]

# 非生产环境添加本地开发地址
if not _IS_PRODUCTION:
    ALLOWED_ORIGINS.extend([
        "http://localhost:3000",
        "http://localhost:5000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5000",
    ])

# [SECURITY] 已移除DEV_MODE - 不再支持允许所有源的不安全模式
# 本地开发时使用 VERCEL_ENV != "production" 自动添加localhost


def get_cors_origin(request_origin: str) -> str:
    """
    根据请求来源返回安全的CORS Origin

    Args:
        request_origin: 请求的Origin头

    Returns:
        允许的CORS Origin（如果请求源在白名单中）
        或默认的第一个允许源（如果请求源不在白名单中）
    """
    # 仅允许白名单中的源
    if request_origin in ALLOWED_ORIGINS:
        return request_origin

    # 请求源不在白名单中，返回默认的生产环境源
    # 注意：这会导致浏览器拒绝该请求（预期行为）
    return ALLOWED_ORIGINS[0]


def is_origin_allowed(request_origin: str) -> bool:
    """
    检查请求源是否在白名单中

    Args:
        request_origin: 请求的Origin头

    Returns:
        True if allowed, False otherwise
    """
    return request_origin in ALLOWED_ORIGINS


def get_cors_headers(request_origin: str = None) -> dict:
    """
    生成完整的CORS响应头

    Args:
        request_origin: 请求的Origin头（可选）

    Returns:
        CORS响应头字典
    """
    # 确定允许的源
    if request_origin:
        allowed_origin = get_cors_origin(request_origin)
    else:
        # 如果没有提供请求源，使用默认源
        # [SECURITY] 非生产环境也不使用 "*"，始终使用白名单
        allowed_origin = ALLOWED_ORIGINS[0]

    return {
        "Access-Control-Allow-Origin": allowed_origin,
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "3600",  # 预检请求缓存1小时
    }
