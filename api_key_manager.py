# -*- coding: utf-8 -*-
"""
API密钥管理器
安全地管理API密钥，支持内置默认密钥和用户自定义密钥
"""
import os
import base64
from pathlib import Path
from typing import Optional


class APIKeyManager:
    """API密钥管理器（单例模式）"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化API密钥管理器"""
        if hasattr(self, '_initialized'):
            return
        
        # 内置默认API密钥（用于新用户，免费额度）
        # 注意：这是经过base64编码的，实际使用时需要解码
        # 在生产环境中，可以使用更复杂的加密方式
        self._default_key_encoded = None  # 在打包时设置
        self._default_key = None  # 运行时解码
        
        # 用户自定义密钥路径
        self._user_env_file = None
        
        self._initialized = True
    
    def get_default_api_key(self) -> Optional[str]:
        """
        获取内置默认API密钥
        
        返回:
        - API密钥字符串，如果不存在则返回None
        """
        if self._default_key is not None:
            return self._default_key
        
        # 尝试从环境变量获取（打包时设置）
        default_key_env = os.getenv('PYDAYBAR_DEFAULT_API_KEY')
        if default_key_env:
            try:
                # 如果是base64编码的，解码
                if default_key_env.startswith('base64:'):
                    encoded = default_key_env[7:]  # 移除 'base64:' 前缀
                    self._default_key = base64.b64decode(encoded).decode('utf-8')
                else:
                    self._default_key = default_key_env
                return self._default_key
            except Exception:
                pass
        
        # 尝试从代码中获取（如果直接嵌入）
        # 注意：在生产环境中，这里应该使用更安全的加密方式
        # 例如：使用PyInstaller的隐藏导入，或者使用环境变量
        return None
    
    def get_user_api_key(self, env_file_path: Optional[Path] = None) -> Optional[str]:
        """
        获取用户自定义API密钥
        
        参数:
        - env_file_path: .env文件路径，如果为None则自动查找
        
        返回:
        - API密钥字符串，如果不存在则返回None
        """
        if env_file_path is None:
            env_file_path = self._find_env_file()
        
        if env_file_path and env_file_path.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(dotenv_path=env_file_path)
                user_key = os.getenv("TUZI_API_KEY")
                
                # 检查是否是占位符
                if user_key and user_key.strip() and 'your_api_key_here' not in user_key.lower():
                    return user_key
            except Exception:
                pass
        
        return None
    
    def get_api_key(self, env_file_path: Optional[Path] = None) -> Optional[str]:
        """
        获取API密钥（优先级：用户密钥 > 默认密钥）
        
        参数:
        - env_file_path: .env文件路径
        
        返回:
        - API密钥字符串，如果都不存在则返回None
        """
        # 优先级1: 用户自定义密钥
        user_key = self.get_user_api_key(env_file_path)
        if user_key:
            return user_key
        
        # 优先级2: 内置默认密钥
        default_key = self.get_default_api_key()
        if default_key:
            return default_key
        
        return None
    
    def _find_env_file(self) -> Optional[Path]:
        """查找.env文件"""
        # 检查PYDAYBAR_ENV_FILE环境变量
        env_file_env = os.getenv('PYDAYBAR_ENV_FILE')
        if env_file_env:
            env_path = Path(env_file_env)
            if env_path.exists():
                return env_path
        
        # 检查当前目录
        current_env = Path('.env')
        if current_env.exists():
            return current_env
        
        # 检查应用目录（打包后）
        import sys
        if getattr(sys, 'frozen', False):
            app_dir = Path(sys.executable).parent
            app_env = app_dir / '.env'
            if app_env.exists():
                return app_env
        
        # 检查父目录（开发环境）
        parent_env = Path('..') / '.env'
        if parent_env.exists():
            return parent_env
        
        return None
    
    def is_user_key_configured(self) -> bool:
        """检查用户是否配置了自定义密钥"""
        return self.get_user_api_key() is not None
    
    def get_key_source(self) -> str:
        """
        获取当前使用的API密钥来源
        
        返回:
        - 'user': 用户自定义密钥
        - 'default': 内置默认密钥
        - 'none': 未找到密钥
        """
        if self.get_user_api_key():
            return 'user'
        elif self.get_default_api_key():
            return 'default'
        else:
            return 'none'

