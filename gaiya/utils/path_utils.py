"""
路径处理工具函数
"""
import sys
from pathlib import Path


def get_app_dir():
    """获取应用程序目录(支持打包后的 exe)

    Returns:
        Path: 应用程序目录的Path对象
    """
    if getattr(sys, 'frozen', False):
        # 打包后的 exe,使用 exe 所在目录
        return Path(sys.executable).parent
    else:
        # 开发环境,使用脚本所在目录
        # 注意:这里返回项目根目录,即main.py所在的目录
        return Path(__file__).parent.parent.parent


def get_resource_path(relative_path):
    """获取资源文件路径(支持打包后的 exe)

    PyInstaller 打包后,资源文件会被解压到 _MEIPASS 临时目录

    Args:
        relative_path: 相对于应用根目录的相对路径

    Returns:
        Path: 资源文件的完整路径
    """
    if getattr(sys, 'frozen', False):
        # 打包后的 exe,资源文件在临时目录
        base_path = Path(sys._MEIPASS)
    else:
        # 开发环境,资源文件在脚本目录
        # 注意:这里返回项目根目录
        base_path = Path(__file__).parent.parent.parent

    return base_path / relative_path
