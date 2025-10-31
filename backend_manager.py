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
            self.app_dir = Path(sys.executable).parent
        else:
            self.app_dir = Path(__file__).parent

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
        if not self.env_file.exists():
            self.logger.warning("未找到 .env 配置文件")
            return False

        try:
            with open(self.env_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 检查是否包含有效的API密钥(不是占位符)
                if 'TUZI_API_KEY=' in content and 'your_api_key_here' not in content:
                    return True
        except Exception as e:
            self.logger.error(f"读取 .env 文件失败: {e}")

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
