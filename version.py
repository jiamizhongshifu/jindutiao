"""
GaiYa每日进度条 - 版本信息
单一事实来源 (Single Source of Truth)

本文件定义了应用的版本号和相关元信息。
所有其他文件应从此处导入版本信息，而不是硬编码。
"""

# ========================================
# 版本信息
# ========================================

__version__ = "1.6.5"
__app_name__ = "GaiYa"
__app_name_zh__ = "盖亚"
__slogan__ = "让每一天都清晰可见"
__release_date__ = "2025-11-28"
__build_type__ = "release"  # release / debug / beta

# ========================================
# 构建信息
# ========================================

# 版本号组成部分
VERSION_MAJOR = 1
VERSION_MINOR = 6
VERSION_PATCH = 5

# 完整版本字符串
VERSION_STRING = f"{__app_name__} v{__version__}"
VERSION_STRING_ZH = f"{__app_name__}每日进度条 v{__version__}"

# ========================================
# PyInstaller 相关
# ========================================

def get_exe_name() -> str:
    """
    获取可执行文件名称（用于PyInstaller spec文件）

    Returns:
        str: exe文件名（不含.exe后缀）

    Example:
        >>> get_exe_name()
        'Gaiya-v1.6'
    """
    return f"{__app_name__}-v{VERSION_MAJOR}.{VERSION_MINOR}"


def get_full_exe_name() -> str:
    """
    获取完整的可执行文件名称（含.exe后缀）

    Returns:
        str: 完整exe文件名

    Example:
        >>> get_full_exe_name()
        'Gaiya-v1.6.exe'
    """
    return f"{get_exe_name()}.exe"


# ========================================
# 应用元信息
# ========================================

APP_METADATA = {
    "name": __app_name__,
    "name_zh": __app_name_zh__,
    "version": __version__,
    "slogan": __slogan__,
    "release_date": __release_date__,
    "build_type": __build_type__,
    "description": "用进度条让时间流逝清晰可见的桌面工具",
    "author": "GaiYa 团队",
    "license": "MIT",
    "wechat": "drmrzhong",
    "repository": "https://github.com/jiamizhongshifu/jindutiao",
}


# ========================================
# 版本对比工具
# ========================================

def get_version_tuple() -> tuple:
    """
    获取版本号元组（用于版本对比）

    Returns:
        tuple: (major, minor, patch)

    Example:
        >>> get_version_tuple()
        (1, 6, 0)
    """
    return (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)


def is_newer_than(major: int, minor: int, patch: int = 0) -> bool:
    """
    检查当前版本是否新于指定版本

    Args:
        major: 主版本号
        minor: 次版本号
        patch: 修订版本号（默认0）

    Returns:
        bool: 如果当前版本更新则返回True

    Example:
        >>> is_newer_than(1, 4, 0)
        True
        >>> is_newer_than(1, 6, 0)
        False
    """
    current = get_version_tuple()
    target = (major, minor, patch)
    return current > target


# ========================================
# 显示函数
# ========================================

def get_about_text() -> str:
    """
    获取"关于"对话框文本

    Returns:
        str: 关于对话框显示的文本
    """
    return f"""
{VERSION_STRING_ZH}

{__slogan__}

发布日期: {__release_date__}
许可协议: {APP_METADATA['license']}

创始人微信: {APP_METADATA['wechat']}
仓库: {APP_METADATA['repository']}

Made with Love by {APP_METADATA['author']}
""".strip()


def get_version_info() -> dict:
    """
    获取完整版本信息（用于日志、调试等）

    Returns:
        dict: 包含所有版本信息的字典
    """
    return {
        "app_name": __app_name__,
        "app_name_zh": __app_name_zh__,
        "version": __version__,
        "version_tuple": get_version_tuple(),
        "release_date": __release_date__,
        "build_type": __build_type__,
        "exe_name": get_exe_name(),
    }


# ========================================
# 模块测试
# ========================================

if __name__ == "__main__":
    print("=== GaiYa 版本信息 ===")
    print(f"应用名称: {__app_name__} ({__app_name_zh__})")
    print(f"版本号: {__version__}")
    print(f"Slogan: {__slogan__}")
    print(f"发布日期: {__release_date__}")
    print(f"EXE文件名: {get_full_exe_name()}")
    print()
    print("=== 版本对比测试 ===")
    print(f"当前版本 > 1.4.0? {is_newer_than(1, 4, 0)}")
    print(f"当前版本 > 1.5.0? {is_newer_than(1, 5, 0)}")
    print(f"当前版本 > 1.6.0? {is_newer_than(1, 6, 0)}")
    print()
    print("=== 关于文本 ===")
    print(get_about_text())
