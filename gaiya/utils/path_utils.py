"""
Path utility functions for bundled and development environments
"""
import sys
from pathlib import Path


def get_app_dir() -> Path:
    """Get application directory (supports bundled exe)

    Returns:
        Path: Application root directory path
    """
    if getattr(sys, 'frozen', False):
        # 打包后的 exe,使用 exe 所在目录
        return Path(sys.executable).parent
    else:
        # 开发环境,使用脚本所在目录
        # 注意:这里返回项目根目录,即main.py所在的目录
        return Path(__file__).parent.parent.parent


def get_resource_path(relative_path: str) -> Path:
    """Get resource file path (supports bundled exe)

    When bundled with PyInstaller, resources are extracted to _MEIPASS temp directory.

    Args:
        relative_path: Resource path relative to application root

    Returns:
        Path: Absolute path to resource file
    """
    if getattr(sys, 'frozen', False):
        # 打包后的 exe,资源文件在临时目录
        base_path = Path(sys._MEIPASS)
    else:
        # 开发环境,资源文件在脚本目录
        # 注意:这里返回项目根目录
        base_path = Path(__file__).parent.parent.parent

    return base_path / relative_path
