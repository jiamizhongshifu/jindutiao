# -*- coding: utf-8 -*-
"""
PyDayBar Backend Manager
AI后端服务自动管理模块
"""
import os
import sys
import subprocess
import time
import logging
import requests
from pathlib import Path
from typing import Optional


class BackendManager:
    """AI后端服务管理器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """初始化后端管理器"""
        self.logger = logger or logging.getLogger(__name__)
        self.backend_process = None
        self.backend_url = "http://localhost:5000"

        # 获取应用程序目录
        if getattr(sys, 'frozen', False):
            # 打包后的情况
            self.app_dir = Path(sys.executable).parent
            # 资源文件在临时目录中（单文件模式）
            if hasattr(sys, '_MEIPASS'):
                self.resource_dir = Path(sys._MEIPASS)
            else:
                self.resource_dir = self.app_dir
        else:
            self.app_dir = Path(__file__).parent
            self.resource_dir = self.app_dir

        # 后端脚本路径：优先从资源目录，然后从应用目录
        self.backend_script = self.resource_dir / "backend_api.py"
        if not self.backend_script.exists():
            self.backend_script = self.app_dir / "backend_api.py"
        
        self.env_file = self.app_dir / ".env"

    def check_backend_health(self) -> bool:
        """检查后端服务是否健康"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    def is_backend_configured(self) -> bool:
        """检查后端是否已配置(API密钥等)"""
        self.logger.info(f"检查 .env 文件: {self.env_file}")
        self.logger.info(f"文件是否存在: {self.env_file.exists()}")
        
        if not self.env_file.exists():
            self.logger.warning(f"未找到 .env 配置文件: {self.env_file}")
            # 尝试查找其他可能的路径
            alternative_paths = [
                self.app_dir.parent / ".env",
                Path.home() / ".env",
            ]
            for alt_path in alternative_paths:
                if alt_path.exists():
                    self.logger.info(f"发现备用 .env 文件: {alt_path}")
                    self.env_file = alt_path
                    break
            else:
                return False

        try:
            with open(self.env_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self.logger.info(f".env 文件内容长度: {len(content)} 字符")
                # 检查是否包含有效的API密钥(不是占位符)
                has_key = 'TUZI_API_KEY=' in content
                has_placeholder = 'your_api_key_here' in content
                self.logger.info(f"包含 TUZI_API_KEY: {has_key}, 包含占位符: {has_placeholder}")
                
                if has_key and not has_placeholder:
                    # 进一步验证：提取API密钥值
                    for line in content.split('\n'):
                        if line.strip().startswith('TUZI_API_KEY='):
                            key_value = line.split('=', 1)[1].strip()
                            if key_value and len(key_value) > 10:  # 基本验证：密钥长度应该大于10
                                self.logger.info("API密钥验证通过")
                                return True
                            else:
                                self.logger.warning(f"API密钥值可能无效: {key_value[:10]}...")
                                return False
                    self.logger.warning("未找到有效的API密钥值")
                    return False
                else:
                    self.logger.warning("API密钥配置不完整或包含占位符")
                    return False
        except Exception as e:
            self.logger.error(f"读取 .env 文件失败: {e}", exc_info=True)

        return False

    def start_backend(self) -> bool:
        """启动后端服务"""
        # 检查后端脚本是否存在
        if not self.backend_script.exists():
            self.logger.error(f"后端脚本不存在: {self.backend_script}")
            return False

        # 检查是否已配置
        if not self.is_backend_configured():
            self.logger.warning("AI后端未配置,跳过自动启动")
            return False

        # 检查是否已运行
        if self.check_backend_health():
            self.logger.info("AI后端服务已在运行")
            return True

        try:
            self.logger.info("正在启动AI后端服务...")

            # 获取Python解释器路径
            if getattr(sys, 'frozen', False):
                # 打包后的情况：使用系统Python或尝试从临时目录找到Python
                # 优先尝试使用系统Python
                import shutil
                python_exe = shutil.which('python') or shutil.which('python3')
                if not python_exe:
                    # 如果找不到，尝试使用临时目录中的Python（PyInstaller解压的）
                    import tempfile
                    temp_dir = Path(tempfile.gettempdir())
                    # PyInstaller会在临时目录创建_MEFrozen目录
                    for python_path in [
                        temp_dir / '_MEI' / 'python311.dll' / '..' / 'python.exe',  # 假设的路径
                        sys.executable.parent / 'python.exe',
                    ]:
                        if python_path.exists():
                            python_exe = str(python_path)
                            break
                
                if not python_exe:
                    self.logger.error("打包后无法找到Python解释器,AI服务无法启动")
                    self.logger.info("提示: 请确保系统已安装Python并添加到PATH,或使用单目录模式打包")
                    return False
            else:
                # 开发环境：直接使用当前Python
                python_exe = sys.executable

            # 启动后端进程(隐藏窗口)
            startupinfo = None
            if sys.platform == 'win32':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            self.backend_process = subprocess.Popen(
                [python_exe, str(self.backend_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.app_dir),
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )

            # 等待服务启动(最多10秒)
            for i in range(20):
                time.sleep(0.5)
                if self.check_backend_health():
                    self.logger.info("✓ AI后端服务启动成功")
                    return True

            self.logger.warning("AI后端服务启动超时")
            return False

        except Exception as e:
            self.logger.error(f"启动AI后端服务失败: {e}")
            return False

    def stop_backend(self):
        """停止后端服务"""
        if self.backend_process:
            try:
                self.logger.info("正在停止AI后端服务...")
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
                self.logger.info("AI后端服务已停止")
            except subprocess.TimeoutExpired:
                self.logger.warning("后端服务未能及时停止,强制终止")
                self.backend_process.kill()
            except Exception as e:
                self.logger.error(f"停止后端服务失败: {e}")

    def ensure_backend_running(self) -> bool:
        """确保后端服务正在运行"""
        if self.check_backend_health():
            return True

        return self.start_backend()

    def ensure_backend_running_async(self):
        """异步确保后端服务正在运行(不阻塞UI线程)"""
        import threading

        def start_in_background():
            """在后台线程启动后端服务"""
            try:
                if self.check_backend_health():
                    self.logger.info("AI后端服务已在运行")
                    return

                self.logger.info("正在后台启动AI后端服务...")
                self.start_backend()
            except Exception as e:
                self.logger.error(f"后台启动AI后端服务失败: {e}")

        # 在新线程中启动,避免阻塞UI
        thread = threading.Thread(target=start_in_background, daemon=True)
        thread.start()
