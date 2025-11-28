# -*- coding: utf-8 -*-
"""
GaiYa每日进度条 - 开机自启动管理器
跨平台支持：Windows (注册表) / macOS (LaunchAgents)
"""
import sys
import os
import logging
import platform
from pathlib import Path
from typing import Optional, List

# 定义接口协议（虽然Python是鸭子类型，但文档化有助于理解）
class AutoStartStrategy:
    def is_enabled(self) -> bool:
        raise NotImplementedError
    
    def enable(self) -> bool:
        raise NotImplementedError
    
    def disable(self) -> bool:
        raise NotImplementedError
    
    def get_executable_path(self) -> str:
        if getattr(sys, 'frozen', False):
            # 打包后的exe/app路径
            return sys.executable
        else:
            # 开发环境
            return sys.executable

# ==========================================
# Windows 实现策略
# ==========================================
class WindowsStrategy(AutoStartStrategy):
    REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    APP_NAME = "Gaiya"
    
    def __init__(self, logger):
        self.logger = logger
        # 仅在实例化时导入，防止非Windows平台崩溃
        try:
            import winreg
            self.winreg = winreg
        except ImportError:
            self.logger.error("无法导入 winreg 模块，Windows 自启动功能将不可用")
            self.winreg = None

    def get_executable_path(self) -> str:
        """Windows下，开发环境需要指向 pythonw.exe + main.py"""
        if getattr(sys, 'frozen', False):
            return sys.executable
        else:
            # 开发环境，使用pythonw运行main.py
            # 注意：这里返回的是完整的命令行字符串，包含参数
            return f'"{sys.executable}" "{Path(__file__).parent / "main.py"}"'

    def is_enabled(self) -> bool:
        if not self.winreg: return False
        try:
            key = self.winreg.OpenKey(
                self.winreg.HKEY_CURRENT_USER,
                self.REG_PATH,
                0,
                self.winreg.KEY_READ
            )
            try:
                value, _ = self.winreg.QueryValueEx(key, self.APP_NAME)
                self.winreg.CloseKey(key)
                
                # 检查路径是否匹配
                current_path = self.get_executable_path()
                return value.strip('"') == current_path.strip('"')
            except FileNotFoundError:
                self.winreg.CloseKey(key)
                return False
        except Exception as e:
            self.logger.error(f"Windows: 检查自启动状态失败: {e}")
            return False

    def enable(self) -> bool:
        if not self.winreg: return False
        try:
            exe_path = self.get_executable_path()
            key = self.winreg.OpenKey(
                self.winreg.HKEY_CURRENT_USER,
                self.REG_PATH,
                0,
                self.winreg.KEY_WRITE
            )
            self.winreg.SetValueEx(
                key,
                self.APP_NAME,
                0,
                self.winreg.REG_SZ,
                exe_path
            )
            self.winreg.CloseKey(key)
            self.logger.info(f"Windows: 已启用开机自启动: {exe_path}")
            return True
        except Exception as e:
            self.logger.error(f"Windows: 启用自启动失败: {e}")
            return False

    def disable(self) -> bool:
        if not self.winreg: return False
        try:
            key = self.winreg.OpenKey(
                self.winreg.HKEY_CURRENT_USER,
                self.REG_PATH,
                0,
                self.winreg.KEY_WRITE
            )
            try:
                self.winreg.DeleteValue(key, self.APP_NAME)
                self.logger.info("Windows: 已禁用开机自启动")
            except FileNotFoundError:
                pass # 本来就没启用
            finally:
                self.winreg.CloseKey(key)
            return True
        except Exception as e:
            self.logger.error(f"Windows: 禁用自启动失败: {e}")
            return False


# ==========================================
# macOS 实现策略
# ==========================================
class MacStrategy(AutoStartStrategy):
    PLIST_FILENAME = "com.gaiya.autostart.plist"
    
    def __init__(self, logger):
        self.logger = logger
        self.home_dir = Path.home()
        self.launch_agents_dir = self.home_dir / "Library" / "LaunchAgents"
        self.plist_path = self.launch_agents_dir / self.PLIST_FILENAME

    def _get_plist_content(self, exe_path: str, args: List[str] = None) -> str:
        """生成 LaunchAgent plist 内容"""
        if args is None:
            args = []
            
        # 构建参数部分 XML
        args_xml = f"    <string>{exe_path}</string>\n"
        for arg in args:
            args_xml += f"    <string>{arg}</string>\n"
            
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.gaiya.autostart</string>
    <key>ProgramArguments</key>
    <array>
    {args_xml.strip()}
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>ProcessType</key>
    <string>Interactive</string>
</dict>
</plist>
"""

    def is_enabled(self) -> bool:
        return self.plist_path.exists()

    def enable(self) -> bool:
        try:
            # 确保目录存在
            if not self.launch_agents_dir.exists():
                self.launch_agents_dir.mkdir(parents=True, exist_ok=True)
            
            # 获取执行路径和参数
            if getattr(sys, 'frozen', False):
                # macOS App Bundle 特殊处理
                # sys.executable 指向 /Applications/GaiYa.app/Contents/MacOS/GaiYa
                # LaunchAgent 通常直接指向这个二进制文件
                exe_path = sys.executable
                args = []
            else:
                # 开发环境
                exe_path = sys.executable
                args = [str(Path(__file__).parent / "main.py")]
            
            content = self._get_plist_content(exe_path, args)
            
            with open(self.plist_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            self.logger.info(f"macOS: 已创建自启动配置文件: {self.plist_path}")
            return True
        except Exception as e:
            self.logger.error(f"macOS: 启用自启动失败: {e}")
            return False

    def disable(self) -> bool:
        try:
            if self.plist_path.exists():
                self.plist_path.unlink()
                self.logger.info("macOS: 已删除自启动配置文件")
            return True
        except Exception as e:
            self.logger.error(f"macOS: 禁用自启动失败: {e}")
            return False


# ==========================================
# 主管理器类
# ==========================================
class AutoStartManager:
    """开机自启动管理器（工厂类）"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.system = platform.system()
        self._strategy = self._create_strategy()
        
        self.logger.info(f"初始化自启动管理器 - 系统: {self.system}")

    def _create_strategy(self) -> AutoStartStrategy:
        if self.system == "Windows":
            return WindowsStrategy(self.logger)
        elif self.system == "Darwin": # macOS
            return MacStrategy(self.logger)
        else:
            # Linux 或其他系统暂不支持，使用哑策略
            self.logger.warning(f"当前系统 {self.system} 暂不支持开机自启动设置")
            return DummyStrategy(self.logger)

    # 代理所有方法调用到具体策略
    def is_enabled(self) -> bool:
        return self._strategy.is_enabled()

    def enable(self) -> bool:
        return self._strategy.enable()

    def disable(self) -> bool:
        return self._strategy.disable()
    
    def set_enabled(self, enabled: bool) -> bool:
        if enabled:
            return self.enable()
        else:
            return self.disable()
            
    def get_executable_path(self) -> str:
        return self._strategy.get_executable_path()


class DummyStrategy(AutoStartStrategy):
    """用于不支持的平台的占位策略"""
    def __init__(self, logger):
        self.logger = logger
        
    def is_enabled(self) -> bool: return False
    def enable(self) -> bool: return False
    def disable(self) -> bool: return True
    def get_executable_path(self) -> str: return ""


# 测试代码
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    manager = AutoStartManager()
    
    print(f"当前系统: {platform.system()}")
    print(f"当前自启动状态: {manager.is_enabled()}")
    
    # 注意：在非Windows系统测试时，如果没有真实需求，不要随意调用enable()
    # 这里仅作为演示
    pass