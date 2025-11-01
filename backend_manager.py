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
import threading
from pathlib import Path
from typing import Optional


class BackendManager:
    """AI后端服务管理器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """初始化后端管理器"""
        self.logger = logger or logging.getLogger(__name__)
        self.backend_process = None
        self.backend_url = "http://localhost:5000"
        self._start_lock = threading.Lock()  # 防止重复启动的锁

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
        
        # .env文件路径：优先在应用目录，然后查找父目录（开发环境）
        self.env_file = self.app_dir / ".env"
        if not self.env_file.exists():
            # 尝试查找父目录的.env文件（开发环境）
            parent_env = self.app_dir.parent / ".env"
            if parent_env.exists():
                self.env_file = parent_env
                self.logger.info(f"找到父目录的.env文件: {self.env_file}")

    def check_backend_health(self) -> bool:
        """检查后端服务是否健康"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=2)
            is_healthy = response.status_code == 200
            if is_healthy:
                self.logger.debug(f"后端健康检查通过: {response.status_code}")
            else:
                self.logger.debug(f"后端健康检查失败: HTTP {response.status_code}")
            return is_healthy
        except Exception as e:
            self.logger.debug(f"后端健康检查异常: {type(e).__name__}")
            return False

    def is_backend_configured(self, _checked_paths=None) -> bool:
        """
        检查后端是否已配置(API密钥等)
        
        参数:
        - _checked_paths: 内部参数，用于防止递归循环
        """
        if _checked_paths is None:
            _checked_paths = set()
        
        self.logger.info(f"检查 .env 文件: {self.env_file}")
        self.logger.info(f"文件是否存在: {self.env_file.exists()}")
        
        # 优先检查用户自定义密钥
        if self.env_file.exists() and str(self.env_file.absolute()) not in _checked_paths:
            _checked_paths.add(str(self.env_file.absolute()))
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
                                    self.logger.info("API密钥验证通过（用户自定义密钥）")
                                    return True
                                else:
                                    self.logger.warning(f"API密钥值可能无效: {key_value[:10]}...")
                                    break
            except Exception as e:
                self.logger.error(f"读取 .env 文件失败: {e}", exc_info=True)
        
        # 如果没有用户密钥，检查是否有内置默认密钥
        try:
            from api_key_manager import APIKeyManager
            api_key_manager = APIKeyManager()
            default_key = api_key_manager.get_default_api_key()
            if default_key:
                self.logger.info("检测到内置默认API密钥，可以使用")
                return True
        except ImportError:
            self.logger.debug("API密钥管理器模块未找到，跳过默认密钥检查")
        except Exception as e:
            self.logger.debug(f"检查默认密钥失败: {e}")
        
        # 尝试查找其他可能的路径（只检查一次）
        if not self.env_file.exists() or str(self.env_file.absolute()) in _checked_paths:
            alternative_paths = [
                self.app_dir.parent / ".env",
                Path.home() / ".env",
            ]
            for alt_path in alternative_paths:
                alt_path_str = str(alt_path.absolute())
                if alt_path.exists() and alt_path_str not in _checked_paths:
                    self.logger.info(f"发现备用 .env 文件: {alt_path}")
                    self.env_file = alt_path
                    _checked_paths.add(alt_path_str)
                    # 递归检查（但只检查一次）
                    return self.is_backend_configured(_checked_paths)
        
        self.logger.warning("未找到有效的API密钥配置")
        return False

    def start_backend(self) -> bool:
        """启动后端服务"""
        self.logger.info("=" * 50)
        self.logger.info("开始启动AI后端服务...")
        
        # 检查后端脚本是否存在
        if not self.backend_script.exists():
            self.logger.error(f"后端脚本不存在: {self.backend_script}")
            self.logger.error(f"  应用目录: {self.app_dir}")
            self.logger.error(f"  资源目录: {self.resource_dir}")
            return False

        # 检查是否已配置
        if not self.is_backend_configured():
            self.logger.warning("AI后端未配置,跳过自动启动")
            self.logger.warning(f"  .env文件路径: {self.env_file}")
            self.logger.warning("  提示: 请确保.env文件包含有效的TUZI_API_KEY")
            return False

        # 检查是否已运行
        self.logger.info("检查后端服务是否已在运行...")
        if self.check_backend_health():
            self.logger.info("✓ AI后端服务已在运行")
            return True
        
        self.logger.info("后端服务未运行，开始启动...")

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
                    self.logger.info(f"使用Python解释器: {python_exe}")
            else:
                # 开发环境：直接使用当前Python
                python_exe = sys.executable
                self.logger.info(f"使用Python解释器: {python_exe}")

            self.logger.info(f"后端脚本路径: {self.backend_script}")
            self.logger.info(f"工作目录: {self.app_dir}")
            self.logger.info(f".env文件路径: {self.env_file}")

            # 准备环境变量（确保.env文件路径可被后端脚本访问）
            env = os.environ.copy()
            # 设置环境变量，让后端脚本知道.env文件的位置
            if self.env_file.exists():
                env['PYDAYBAR_ENV_FILE'] = str(self.env_file.absolute())
                # 如果.env文件不在当前工作目录，将其复制到工作目录（临时方案）
                target_env = self.app_dir / ".env"
                if target_env != self.env_file and self.env_file.exists():
                    try:
                        import shutil
                        shutil.copy2(self.env_file, target_env)
                        self.logger.info(f"已复制.env文件到工作目录: {target_env}")
                    except Exception as e:
                        self.logger.warning(f"复制.env文件失败: {e}，将尝试直接使用原路径")

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
                env=env,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            # 立即检查进程是否仍在运行（如果启动失败会立即退出）
            time.sleep(0.5)
            if self.backend_process.poll() is not None:
                # 进程已退出，读取错误信息
                try:
                    stdout, stderr = self.backend_process.communicate(timeout=1)
                    if stderr:
                        error_msg = stderr.decode('utf-8', errors='ignore')
                        self.logger.error(f"后端进程立即退出，错误信息: {error_msg}")
                    if stdout:
                        output_msg = stdout.decode('utf-8', errors='ignore')
                        self.logger.info(f"后端进程输出: {output_msg}")
                except Exception as e:
                    self.logger.error(f"读取进程输出失败: {e}")
                return False

            self.logger.info(f"后端进程已启动，PID: {self.backend_process.pid}")

            # 等待服务启动(最多10秒)
            self.logger.info("等待后端服务响应...")
            for i in range(20):
                time.sleep(0.5)
                if self.check_backend_health():
                    self.logger.info("✓ AI后端服务启动成功（健康检查通过）")
                    return True
                if i % 4 == 0:  # 每2秒记录一次进度
                    self.logger.info(f"等待后端服务启动... ({i*0.5:.1f}秒)")

            self.logger.warning("AI后端服务启动超时（10秒内未响应）")
            # 输出进程的错误信息（如果有）
            if self.backend_process.poll() is not None:
                try:
                    stdout, stderr = self.backend_process.communicate(timeout=1)
                    if stderr:
                        error_msg = stderr.decode('utf-8', errors='ignore')[:500]
                        self.logger.error(f"后端进程错误输出: {error_msg}")
                except:
                    pass
            return False

        except Exception as e:
            self.logger.error(f"启动AI后端服务失败: {e}", exc_info=True)
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
        def start_in_background():
            """在后台线程启动后端服务"""
            # 使用锁防止重复启动
            if not self._start_lock.acquire(blocking=False):
                self.logger.debug("后端启动正在进行中，跳过重复启动")
                return
            
            try:
                self.logger.info("=" * 50)
                self.logger.info("异步检查AI后端服务状态...")
                
                # 快速检查后端是否已运行（避免重复启动）
                if self.check_backend_health():
                    self.logger.info("✓ AI后端服务已在运行")
                    return

                # 检查是否已有进程在运行
                if self.backend_process is not None and self.backend_process.poll() is None:
                    self.logger.info("后端进程已在运行中，等待启动完成...")
                    # 等待最多5秒
                    for i in range(10):
                        time.sleep(0.5)
                        if self.check_backend_health():
                            self.logger.info("✓ AI后端服务已启动")
                            return
                    self.logger.warning("后端进程运行中，但健康检查失败")

                self.logger.info("后端服务未运行，正在后台启动...")
                success = self.start_backend()
                if success:
                    self.logger.info("=" * 50)
                    self.logger.info("✓ AI后端服务启动成功")
                    self.logger.info("=" * 50)
                else:
                    self.logger.warning("=" * 50)
                    self.logger.warning("⚠ AI后端服务启动失败，可能原因：")
                    self.logger.warning("  1. 后端脚本不存在")
                    self.logger.warning("  2. .env文件未配置或API密钥无效")
                    self.logger.warning("  3. Python解释器未找到（打包后）")
                    self.logger.warning("  4. 端口5000被占用")
                    self.logger.warning("  5. 后端脚本启动超时")
                    self.logger.warning("=" * 50)
            except Exception as e:
                self.logger.error("=" * 50)
                self.logger.error(f"后台启动AI后端服务异常: {e}", exc_info=True)
                self.logger.error("=" * 50)
            finally:
                self._start_lock.release()

        # 在新线程中启动,避免阻塞UI
        thread = threading.Thread(target=start_in_background, daemon=True)
        thread.start()
