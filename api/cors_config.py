"""
GaiYa每日进度条 - CORS安全配置
定义允许访问API的可信来源，防止跨站请求伪造
"""
import os
from typing import List

# 允许的CORS源白名单
# 生产环境应仅包含实际部署的域名
ALLOWED_ORIGINS = [
    # Vercel生产环境
    "https://jindutiao.vercel.app",

    # 自定义域名（如果配置了）
    "https://gaiya.app",
    "https://www.gaiya.app",
    "https://gaiyatime.com",
    "https://www.gaiyatime.com",

    # 本地开发环境
    "http://localhost:3000",
    "http://localhost:5000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5000",
]

# 开发模式：允许所有源（仅用于测试，生产环境禁用）
DEV_MODE = os.getenv("CORS_DEV_MODE") == "true"


def get_cors_origin(request_origin: str) -> str:
    """
    根据请求来源返回安全的CORS Origin

    Args:
        request_origin: 请求的Origin头

    Returns:
        允许的CORS Origin（如果请求源在白名单中）
        或默认的第一个允许源（如果请求源不在白名单中）
    """
    # 开发模式：允许所有源（仅用于测试）
    if DEV_MODE:
        return request_origin if request_origin else "*"

    # 生产模式：仅允许白名单中的源
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
    if DEV_MODE:
        return True

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
        # 如果没有提供请求源，使用默认源或 *（开发模式）
        allowed_origin = "*" if DEV_MODE else ALLOWED_ORIGINS[0]

    return {
        "Access-Control-Allow-Origin": allowed_origin,
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "3600",  # 预检请求缓存1小时
    }
