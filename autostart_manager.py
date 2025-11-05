# -*- coding: utf-8 -*-
"""
GaiYa每日进度条 - 开机自启动管理器
使用Windows注册表实现开机自启动功能
"""
import winreg
import sys
import logging
from pathlib import Path
from typing import Optional


class AutoStartManager:
    """Windows开机自启动管理器"""

    # 注册表路径
    REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    # 应用程序名称（在注册表中的键名）
    APP_NAME = "Gaiya"

    def __init__(self):
        """初始化自启动管理器"""
        self.logger = logging.getLogger(__name__)

    def get_executable_path(self) -> str:
        """
        获取可执行文件的完整路径

        Returns:
            可执行文件的完整路径
        """
        if getattr(sys, 'frozen', False):
            # 打包后的exe路径
            exe_path = sys.executable
        else:
            # 开发环境，使用pythonw运行main.py
            exe_path = f'"{sys.executable}" "{Path(__file__).parent / "main.py"}"'

        return exe_path

    def is_enabled(self) -> bool:
        """
        检查是否已启用开机自启动

        Returns:
            True表示已启用，False表示未启用
        """
        try:
            # 打开注册表键
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.REG_PATH,
                0,
                winreg.KEY_READ
            )

            try:
                # 尝试读取值
                value, _ = winreg.QueryValueEx(key, self.APP_NAME)
                winreg.CloseKey(key)

                # 检查路径是否匹配当前可执行文件
                current_path = self.get_executable_path()

                # 处理路径比较（去除引号进行比较）
                stored_path = value.strip('"')
                expected_path = current_path.strip('"')

                return stored_path == expected_path
            except FileNotFoundError:
                # 键不存在
                winreg.CloseKey(key)
                return False
        except Exception as e:
            self.logger.error(f"检查自启动状态失败: {e}")
            return False

    def enable(self) -> bool:
        """
        启用开机自启动

        Returns:
            True表示成功，False表示失败
        """
        try:
            # 获取可执行文件路径
            exe_path = self.get_executable_path()

            # 打开注册表键（如果不存在则创建）
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.REG_PATH,
                0,
                winreg.KEY_WRITE
            )

            # 设置值
            winreg.SetValueEx(
                key,
                self.APP_NAME,
                0,
                winreg.REG_SZ,
                exe_path
            )

            winreg.CloseKey(key)

            self.logger.info(f"已启用开机自启动: {exe_path}")
            return True
        except Exception as e:
            self.logger.error(f"启用自启动失败: {e}")
            return False

    def disable(self) -> bool:
        """
        禁用开机自启动

        Returns:
            True表示成功，False表示失败
        """
        try:
            # 打开注册表键
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.REG_PATH,
                0,
                winreg.KEY_WRITE
            )

            try:
                # 删除值
                winreg.DeleteValue(key, self.APP_NAME)
                self.logger.info("已禁用开机自启动")
                result = True
            except FileNotFoundError:
                # 键不存在，认为已经禁用
                self.logger.info("自启动项不存在，无需禁用")
                result = True
            finally:
                winreg.CloseKey(key)

            return result
        except Exception as e:
            self.logger.error(f"禁用自启动失败: {e}")
            return False

    def set_enabled(self, enabled: bool) -> bool:
        """
        设置开机自启动状态

        Args:
            enabled: True为启用，False为禁用

        Returns:
            True表示成功，False表示失败
        """
        if enabled:
            return self.enable()
        else:
            return self.disable()

    def get_registry_value(self) -> Optional[str]:
        """
        获取注册表中存储的值（用于调试）

        Returns:
            注册表中的值，如果不存在则返回None
        """
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.REG_PATH,
                0,
                winreg.KEY_READ
            )

            try:
                value, _ = winreg.QueryValueEx(key, self.APP_NAME)
                winreg.CloseKey(key)
                return value
            except FileNotFoundError:
                winreg.CloseKey(key)
                return None
        except Exception as e:
            self.logger.error(f"读取注册表值失败: {e}")
            return None


# 测试代码
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    manager = AutoStartManager()

    print(f"可执行文件路径: {manager.get_executable_path()}")
    print(f"当前自启动状态: {'已启用' if manager.is_enabled() else '未启用'}")
    print(f"注册表值: {manager.get_registry_value()}")

    # 测试启用
    if manager.enable():
        print("✓ 启用自启动成功")
    else:
        print("✗ 启用自启动失败")

    print(f"启用后状态: {'已启用' if manager.is_enabled() else '未启用'}")

    # 测试禁用
    if manager.disable():
        print("✓ 禁用自启动成功")
    else:
        print("✗ 禁用自启动失败")

    print(f"禁用后状态: {'已启用' if manager.is_enabled() else '未启用'}")
