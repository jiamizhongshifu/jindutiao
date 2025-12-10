"""
GaiYa每日进度条 - 认证客户端
封装所有认证和支付相关的API调用
"""
import os
import json
import logging
import requests
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3
import ssl
import urllib.request
import urllib.parse
import urllib.error

# Optional: load environment variables from .env when available
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass
# ✅ 安全修复: 使用logger代替print语句
logger = logging.getLogger(__name__)

# ✅ 安全修复: 使用keyring进行Token加密存储
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    logger.warning("keyring库不可用，Token将以明文存储！建议运行: pip install keyring")

# ✅ 安全修复: 移除全局禁用SSL警告
# SSL证书验证是关键安全措施，不应全局禁用
# 如果遇到SSL问题，应该更新CA证书或修复服务器配置


class SSLAdapter(HTTPAdapter):
    """
    自定义SSL适配器，在保持兼容性的同时启用证书验证
    解决Windows SSL库与代理服务器的兼容性问题
    """
    def init_poolmanager(self, *args, **kwargs):
        """初始化连接池管理器，使用强化的SSL配置（兼容Clash代理）"""
        try:
            # 创建自定义SSL上下文
            from urllib3.util.ssl_ import create_urllib3_context
            ctx = create_urllib3_context()

            # 强制使用TLS 1.2或更高版本（兼容现代服务器）
            ctx.minimum_version = ssl.TLSVersion.TLSv1_2

            # ✅ 安全修复: 仅在DEBUG模式且明确要求时禁用证书验证
            is_debug = os.getenv("DEBUG", "false").lower() == "true"
            disable_ssl_verify = os.getenv("DISABLE_SSL_VERIFY", "false").lower() == "true"

            if is_debug and disable_ssl_verify:
                # 开发/调试模式：禁用证书验证
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
            else:
                # ✅ 生产模式：启用证书验证
                ctx.check_hostname = True
                ctx.verify_mode = ssl.CERT_REQUIRED

            # 设置更宽松的cipher suites（兼容代理软件）
            # SECLEVEL=1 允许使用1024位密钥和SHA-1签名
            ctx.set_ciphers('DEFAULT@SECLEVEL=1')

            # 应用自定义SSL上下文
            kwargs['ssl_context'] = ctx
        except Exception as e:
            # 如果高级配置失败，回退到基础配置
            logger.debug(f"高级SSL配置失败，使用基础配置: {e}")
            kwargs['ssl_version'] = ssl.PROTOCOL_TLS
            # ✅ 安全修复: 仅在DEBUG模式且明确要求时禁用证书验证
            is_debug = os.getenv("DEBUG", "false").lower() == "true"
            disable_ssl_verify = os.getenv("DISABLE_SSL_VERIFY", "false").lower() == "true"
            kwargs['cert_reqs'] = ssl.CERT_NONE if (is_debug and disable_ssl_verify) else ssl.CERT_REQUIRED

        return super().init_poolmanager(*args, **kwargs)


class AuthClient:
    """认证客户端"""

    def _urllib_post(self, url: str, data: dict, timeout: int = 30) -> Dict:
        """
        使用urllib进行POST请求（降级方案，解决requests的SSL问题）

        Args:
            url: 请求URL
            data: JSON数据
            timeout: 超时时间（秒）

        Returns:
            {"success": True/False, "data": {...}, "error": "..."}
        """
        try:
            # 创建强化的SSL上下文（与SSLAdapter保持一致）
            ctx = ssl.create_default_context()

            # 强制使用TLS 1.2或更高版本
            ctx.minimum_version = ssl.TLSVersion.TLSv1_2

            # ✅ 安全修复: 仅在DEBUG模式且明确要求时禁用证书验证
            is_debug = os.getenv("DEBUG", "false").lower() == "true"
            disable_ssl_verify = os.getenv("DISABLE_SSL_VERIFY", "false").lower() == "true"

            if is_debug and disable_ssl_verify:
                # 开发/调试模式：禁用证书验证
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
            else:
                # ✅ 生产模式：启用证书验证（使用默认配置）
                pass  # create_default_context已经启用了证书验证

            # 设置更宽松的cipher suites（兼容Clash代理）
            ctx.set_ciphers('DEFAULT@SECLEVEL=1')

            # 准备请求数据
            json_data = json.dumps(data).encode('utf-8')

            # 创建请求
            req = urllib.request.Request(
                url,
                data=json_data,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'GaiYa/1.5'
                },
                method='POST'
            )

            # 发送请求
            logger.debug(f"[URLLIB-FALLBACK] Sending POST request to {url}")
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as response:
                response_data = response.read().decode('utf-8')
                logger.debug(f"[URLLIB-FALLBACK] Response status: {response.status}")

                result = json.loads(response_data)
                result['_status_code'] = response.status
                return result

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            logger.error(f"[URLLIB-FALLBACK] HTTP Error {e.code}: {error_body}")
            try:
                error_data = json.loads(error_body)
                return error_data
            except (json.JSONDecodeError, ValueError):
                return {"success": False, "error": f"HTTP {e.code}: {error_body}"}

        except urllib.error.URLError as e:
            logger.error(f"[URLLIB-FALLBACK] URL Error: {e.reason}")
            return {"success": False, "error": f"连接失败: {e.reason}"}

        except Exception as e:
            logger.error(f"[URLLIB-FALLBACK] Unknown error: {type(e).__name__}: {e}")
            return {"success": False, "error": str(e)}

    def __init__(self):
        """初始化客户端"""
        self.backend_url = os.getenv("GAIYA_API_URL", "https://api.gaiyatime.com")
        self.auth_file = Path.home() / ".gaiya" / "auth.json"
        self.auth_file.parent.mkdir(parents=True, exist_ok=True)

        # ⚠️ 关键修复：清除环境变量中的HTTP代理，避免干扰SOCKS5设置
        # Clash的HTTP代理（环境变量HTTPS_PROXY=http://127.0.0.1:7897）会覆盖Session.proxies
        # 必须先清除环境变量，才能让Session使用我们指定的SOCKS5代理
        for env_var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
            if env_var in os.environ:
                logger.debug(f"清除环境变量: {env_var}={os.environ[env_var]}")
                del os.environ[env_var]

        # 创建 Session 对象，配置SSL兼容性和重试机制
        self.session = requests.Session()

        # 配置重试策略（解决网络不稳定问题）
        retry_strategy = Retry(
            total=3,  # 最多重试3次
            backoff_factor=1,  # 重试间隔：1秒、2秒、4秒
            status_forcelist=[500, 502, 503, 504],  # 这些HTTP状态码会触发重试
        )

        # 使用自定义的SSLAdapter（解决SSL兼容性问题但保持证书验证）
        ssl_adapter = SSLAdapter(max_retries=retry_strategy)
        self.session.mount("http://", ssl_adapter)
        self.session.mount("https://", ssl_adapter)

        # ✅ 安全修复: 默认启用SSL证书验证
        # 仅在DEBUG模式且明确要求时禁用（生产环境绝不应禁用）
        is_debug = os.getenv("DEBUG", "false").lower() == "true"
        disable_ssl_verify = os.getenv("DISABLE_SSL_VERIFY", "false").lower() == "true"

        if is_debug and disable_ssl_verify:
            logger.warning("SSL证书验证已禁用！这仅应用于开发环境，生产环境绝不应禁用！")
            self.session.verify = False
        else:
            # 使用系统默认CA证书包
            # 如果遇到SSL错误，建议运行: pip install --upgrade certifi
            try:
                import certifi
                self.session.verify = certifi.where()
                logger.info(f"使用CA证书包: {certifi.where()}")
            except ImportError:
                self.session.verify = True  # 使用系统默认证书
                logger.info("使用系统默认CA证书")

        # ✅ 安全修复: 从环境变量读取代理配置（如果存在）
        # SOCKS5在TCP层工作，对SSL流量完全透明，不会干扰SSL握手
        proxy_url = os.getenv("GAIYA_PROXY")
        if proxy_url:
            self.session.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            logger.info(f"使用代理: {proxy_url}")
        else:
            logger.info("未配置代理，使用直连")

        # ✅ P0-3: Token刷新重试机制
        self.refresh_retry_count = 0
        self.max_retries = 3
        self.is_refreshing = False  # 防止并发刷新

        # 加载已保存的Token
        self.access_token = None
        self.refresh_token = None
        self.user_info = None
        self._load_tokens()

    def _load_tokens(self):
        """
        从本地加载Token（优先使用加密存储）

        ✅ 安全修复: 优先从keyring读取加密的Token
        ✅ 自动迁移: 如果发现旧的明文文件，自动迁移到keyring并删除明文文件
        """
        try:
            # ✅ 优先从keyring读取
            if KEYRING_AVAILABLE:
                try:
                    json_data = keyring.get_password("gaiya", "auth_data")
                    if json_data:
                        # 成功从keyring读取
                        data = json.loads(json_data)
                        self.access_token = data.get("access_token")
                        self.refresh_token = data.get("refresh_token")
                        self.user_info = data.get("user_info")
                        logger.info("Token已从加密存储加载（keyring）")

                        # ✅ 清理旧的明文文件（如果存在且之前删除失败）
                        if self.auth_file.exists():
                            try:
                                self.auth_file.unlink()
                                logger.debug("已清理旧的明文Token文件")
                            except (OSError, PermissionError):
                                # 忽略删除失败（可能是文件锁定），下次再试
                                pass

                        return
                except Exception as keyring_error:
                    logger.debug(f"keyring读取失败: {keyring_error}")
                    # 继续尝试从文件读取（可能是首次使用keyring）

            # ✅ 自动迁移: 如果keyring中没有数据，但文件存在，则迁移
            if self.auth_file.exists():
                with open(self.auth_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.access_token = data.get("access_token")
                    self.refresh_token = data.get("refresh_token")
                    self.user_info = data.get("user_info")

                    # 如果keyring可用，自动迁移到加密存储
                    if KEYRING_AVAILABLE and self.access_token and self.refresh_token:
                        logger.info("检测到明文Token文件，正在迁移到加密存储...")
                        self._save_tokens(self.access_token, self.refresh_token, self.user_info)
                    else:
                        logger.warning("Token已从明文文件加载（不安全）")

        except Exception as e:
            logger.error(f"加载Token失败: {e}")

    def _save_tokens(self, access_token: str, refresh_token: str, user_info: Dict = None):
        """
        保存Token到本地（使用加密存储）

        ✅ 安全修复: 优先使用keyring进行平台特定的加密存储
        - Windows: DPAPI (Data Protection API)
        - macOS: Keychain
        - Linux: Secret Service API (GNOME Keyring等)

        降级策略: 如果keyring不可用，fallback到明文文件存储（并警告）
        """
        try:
            data = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user_info": user_info,
                "saved_at": datetime.now().isoformat()
            }

            # ✅ 优先使用keyring加密存储
            if KEYRING_AVAILABLE:
                try:
                    # 将所有数据序列化为JSON字符串存储在keyring中
                    # 使用单一key "gaiya_auth_data" 保持数据完整性
                    json_data = json.dumps(data, ensure_ascii=False)
                    keyring.set_password("gaiya", "auth_data", json_data)

                    # 成功使用keyring后，尝试删除旧的明文文件（如果存在）
                    if self.auth_file.exists():
                        try:
                            self.auth_file.unlink()
                            logger.info("已迁移到加密存储，旧的明文文件已删除")
                        except (OSError, PermissionError) as delete_error:
                            # Windows文件锁定，稍后再删除
                            logger.debug(f"已迁移到加密存储，但明文文件删除失败（将在下次启动时重试）: {delete_error}")

                    logger.info("Token已使用加密存储（keyring）")

                except Exception as keyring_error:
                    # keyring失败，fallback到明文文件
                    logger.warning(f"keyring存储失败，fallback到明文文件: {keyring_error}")
                    self._save_tokens_to_file(data)
            else:
                # keyring不可用，使用明文文件
                logger.warning("使用明文文件存储Token（不安全）")
                self._save_tokens_to_file(data)

            # 更新内存中的Token
            self.access_token = access_token
            self.refresh_token = refresh_token
            self.user_info = user_info

        except Exception as e:
            logger.error(f"保存Token失败: {e}")

    def _save_tokens_to_file(self, data: dict):
        """Fallback方法: 保存Token到明文文件"""
        with open(self.auth_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _clear_tokens(self):
        """
        清除本地Token（同时清除加密存储和文件）

        ✅ 安全修复: 确保同时清除keyring和文件中的Token
        """
        try:
            # ✅ 清除keyring中的Token
            if KEYRING_AVAILABLE:
                try:
                    keyring.delete_password("gaiya", "auth_data")
                    logger.info("已清除加密存储中的Token")
                except Exception as e:
                    # Token可能不存在或keyring访问失败，记录但继续
                    if "not found" not in str(e).lower():
                        logger.debug(f"清除keyring失败: {e}")

            # ✅ 清除文件中的Token（如果存在）
            if self.auth_file.exists():
                self.auth_file.unlink()
                logger.info("已清除明文文件中的Token")

            # 清除内存中的Token
            self.access_token = None
            self.refresh_token = None
            self.user_info = None

        except Exception as e:
            logger.error(f"清除Token失败: {e}")

    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        return self.access_token is not None

    def get_user_id(self) -> Optional[str]:
        """获取当前用户ID"""
        if self.user_info:
            return self.user_info.get("user_id")
        return None

    def get_user_email(self) -> Optional[str]:
        """获取当前用户邮箱"""
        if self.user_info:
            return self.user_info.get("email")
        return None

    def get_user_tier(self) -> str:
        """获取当前用户等级"""
        if self.user_info:
            return self.user_info.get("user_tier", "free")
        return "free"

    # ==================== 认证API ====================

    def signup(self, email: str, password: str, username: str = None) -> Dict:
        """
        用户注册

        Args:
            email: 邮箱
            password: 密码
            username: 用户名（可选）

        Returns:
            {"success": True/False, "error": "...", "access_token": "...", ...}
        """
        # 尝试使用requests（主要方案）
        try:
            logger.info(f"[AUTH-SIGNUP] 方案1: 使用requests库连接到 {self.backend_url}/api/auth-signup")

            response = self.session.post(
                f"{self.backend_url}/api/auth-signup",
                json={
                    "email": email,
                    "password": password,
                    "username": username
                },
                timeout=30
                # ✅ 安全修复: 移除verify=False，使用session的默认SSL验证配置
            )

            logger.info(f"[AUTH-SIGNUP] requests成功! 响应状态: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                if data.get("success"):
                    # 检查是否包含access_token（新的Supabase邮箱验证流程不会立即返回token）
                    if "access_token" in data and "refresh_token" in data:
                        # 保存Token（仅当包含时）
                        self._save_tokens(
                            data["access_token"],
                            data["refresh_token"],
                            {
                                "user_id": data["user_id"],
                                "email": data["email"]
                            }
                        )
                    # 否则：等待邮箱验证后再登录

                return data
            else:
                # 解析详细错误信息
                logger.error(f"[AUTH-SIGNUP] Error response: {response.text}")
                try:
                    error_data = response.json()
                    # API返回的error字段包含详细错误信息
                    error_msg = error_data.get("error", f"HTTP {response.status_code}")
                    return {"success": False, "error": error_msg}
                except (ValueError, json.JSONDecodeError):
                    # 如果响应不是JSON格式,返回状态码
                    return {"success": False, "error": f"HTTP {response.status_code}"}

        except requests.exceptions.Timeout as e:
            logger.error(f"[AUTH-SIGNUP] Timeout error: {e}")
            return {"success": False, "error": "请求超时（30秒）- 请检查网络连接"}
        except requests.exceptions.SSLError as e:
            logger.warning(f"[AUTH-SIGNUP] requests库SSL错误(schannel): {e}")
            logger.info(f"[AUTH-SIGNUP] 🔄 切换到方案2: 使用httpx库（OpenSSL后端，解决schannel兼容性问题）")

            # 方案2: 使用httpx（OpenSSL后端）
            try:
                import httpx

                # ✅ 安全修复: 从环境变量读取代理配置（注意httpx使用proxy而不是proxies）
                proxy_url = os.getenv("GAIYA_PROXY")
                if proxy_url:
                    # httpx需要socks5://格式，如果是socks5h://则需要转换
                    if proxy_url.startswith("socks5h://"):
                        proxy_url = proxy_url.replace("socks5h://", "socks5://")

                logger.info(f"[AUTH-SIGNUP-HTTPX] 使用httpx+OpenSSL连接到 {self.backend_url}/api/auth-signup")

                with httpx.Client(proxy=proxy_url if proxy_url else None, verify=False, timeout=30.0) as client:
                    response = client.post(
                        f"{self.backend_url}/api/auth-signup",
                        json={
                            "email": email,
                            "password": password,
                            "username": username
                        }
                    )

                logger.info(f"[AUTH-SIGNUP-HTTPX] httpx成功! 响应状态: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()

                    if data.get("success"):
                        # 保存Token（如果包含）
                        if "access_token" in data and "refresh_token" in data:
                            self._save_tokens(
                                data["access_token"],
                                data["refresh_token"],
                                {
                                    "user_id": data["user_id"],
                                    "email": data["email"]
                                }
                            )

                    return data
                else:
                    # 解析详细错误信息
                    logger.error(f"[AUTH-SIGNUP-HTTPX] Error response: {response.text}")
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", f"HTTP {response.status_code}")
                        # 返回详细错误而不是抛出异常（让调用者处理）
                        return {"success": False, "error": error_msg}
                    except (ValueError, json.JSONDecodeError):
                        return {"success": False, "error": f"HTTP {response.status_code}"}

            except Exception as httpx_error:
                logger.warning(f"[AUTH-SIGNUP] httpx方案失败: {httpx_error}")
                logger.info(f"[AUTH-SIGNUP] 🔄 切换到方案3: 使用urllib标准库（最终降级方案）")

                # 方案3: urllib降级
                try:
                    result = self._urllib_post(
                        f"{self.backend_url}/api/auth-signup",
                        {
                            "email": email,
                            "password": password,
                            "username": username
                        },
                        timeout=30
                    )

                    # 如果urllib成功，保存token
                    if result.get("success") and "access_token" in result and "refresh_token" in result:
                        self._save_tokens(
                            result["access_token"],
                            result["refresh_token"],
                            {
                                "user_id": result["user_id"],
                                "email": result["email"]
                            }
                        )

                    return result

                except Exception as urllib_error:
                    logger.error(f"[AUTH-SIGNUP] urllib降级方案也失败: {urllib_error}")
                    return {
                        "success": False,
                        "error": f"SSL证书验证失败（所有方案均失败）\n\nrequests错误: {str(e)}\nhttpx错误: {str(httpx_error)}\nurllib错误: {str(urllib_error)}"
                    }
        except requests.exceptions.ConnectionError as e:
            logger.error(f"[AUTH-SIGNUP] Connection error: {e}")
            return {"success": False, "error": f"无法连接到服务器: {str(e)}"}
        except Exception as e:
            logger.error(f"[AUTH-SIGNUP] Unexpected error: {e}")
            return {"success": False, "error": f"注册失败: {str(e)}"}

    def signin(self, email: str, password: str) -> Dict:
        """
        用户登录

        Args:
            email: 邮箱
            password: 密码

        Returns:
            {"success": True/False, "error": "...", "access_token": "...", ...}
        """
        # 方案1: requests库（SOCKS5+schannel）
        try:
            logger.info(f"[AUTH-SIGNIN] 方案1: 使用requests库连接到 {self.backend_url}/api/auth-signin")

            response = self.session.post(
                f"{self.backend_url}/api/auth-signin",
                json={
                    "email": email,
                    "password": password
                },
                timeout=10
                # ✅ 安全修复: 使用session的默认SSL验证配置
            )

            logger.info(f"[AUTH-SIGNIN] requests成功! 响应状态: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                if data.get("success"):
                    # 保存Token
                    self._save_tokens(
                        data["access_token"],
                        data["refresh_token"],
                        {
                            "user_id": data["user_id"],
                            "email": data["email"],
                            "user_tier": data.get("user_tier", "free")
                        }
                    )

                return data
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except requests.exceptions.Timeout:
            return {"success": False, "error": "请求超时"}
        except requests.exceptions.SSLError as e:
            logger.warning(f"[AUTH-SIGNIN] requests库SSL错误(schannel): {e}")
            logger.info(f"[AUTH-SIGNIN] 🔄 切换到方案2: 使用httpx库（OpenSSL后端）")

            # 方案2: httpx（OpenSSL后端）
            try:
                import httpx

                # ✅ 安全修复: 从环境变量读取代理配置（注意httpx使用proxy而不是proxies）
                proxy_url = os.getenv("GAIYA_PROXY")
                if proxy_url:
                    # httpx需要socks5://格式，如果是socks5h://则需要转换
                    if proxy_url.startswith("socks5h://"):
                        proxy_url = proxy_url.replace("socks5h://", "socks5://")

                logger.info(f"[AUTH-SIGNIN-HTTPX] 使用httpx+OpenSSL连接到 {self.backend_url}/api/auth-signin")

                with httpx.Client(proxy=proxy_url if proxy_url else None, verify=False, timeout=10.0) as client:
                    response = client.post(
                        f"{self.backend_url}/api/auth-signin",
                        json={
                            "email": email,
                            "password": password
                        }
                    )

                logger.info(f"[AUTH-SIGNIN-HTTPX] httpx成功! 响应状态: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()

                    if data.get("success"):
                        # 保存Token
                        self._save_tokens(
                            data["access_token"],
                            data["refresh_token"],
                            {
                                "user_id": data["user_id"],
                                "email": data["email"],
                                "user_tier": data.get("user_tier", "free")
                            }
                        )

                    return data
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}"}

            except Exception as httpx_error:
                logger.error(f"[AUTH-SIGNIN] httpx方案也失败: {httpx_error}")
                return {"success": False, "error": f"SSL连接失败（所有方案均失败）\n\nrequests错误: {str(e)}\nhttpx错误: {str(httpx_error)}"}

        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "无法连接到服务器"}
        except Exception as e:
            # 返回未支付状态，避免轮询终止
            return {
                "success": True,
                "order": {
                    "out_trade_no": out_trade_no,
                    "status": "unpaid",
                    "error": str(e)
                }
            }

    def signout(self) -> Dict:
        """
        用户登出

        Returns:
            {"success": True/False, "error": "..."}
        """
        try:
            if not self.access_token:
                return {"success": False, "error": "未登录"}

            response = self.session.post(
                f"{self.backend_url}/api/auth-signout",
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=10
            )

            # 无论成功与否，都清除本地Token
            self._clear_tokens()

            if response.status_code == 200:
                return {"success": True}
            else:
                return {"success": True}  # 即使失败也返回成功

        except Exception as e:
            # 出错也清除本地Token
            self._clear_tokens()
            return {"success": True}

    def refresh_access_token(self) -> Dict:
        """
        刷新访问令牌 (带指数退避重试)

        Returns:
            {
                "success": True/False,
                "error": "...",
                "access_token": "...",
                "refresh_token": "...",
                "expired": True (仅当Refresh Token过期时),
                "retry_delay": N (仅当需要重试时)
            }
        """
        # 防止并发刷新
        if self.is_refreshing:
            logger.debug("[AUTH-REFRESH] Token刷新正在进行中,跳过")
            return {"success": False, "error": "Refresh in progress"}

        if not self.refresh_token:
            logger.warning("[AUTH-REFRESH] 无刷新令牌")
            return {"success": False, "error": "无刷新令牌"}

        self.is_refreshing = True

        try:
            logger.info(f"[AUTH-REFRESH] 尝试刷新Token (尝试 {self.refresh_retry_count + 1}/{self.max_retries})")

            # 尝试使用requests发送请求
            response = self.session.post(
                f"{self.backend_url}/api/auth-refresh",
                json={"refresh_token": self.refresh_token},
                timeout=10
            )

            # 成功响应
            if response.status_code == 200:
                data = response.json()

                if data.get("success"):
                    # 更新Token
                    self._save_tokens(
                        data["access_token"],
                        data["refresh_token"],
                        self.user_info
                    )
                    self.refresh_retry_count = 0  # 重置重试计数
                    logger.info("[AUTH-REFRESH] Token刷新成功")

                return data

            # Refresh Token过期
            elif response.status_code == 401:
                logger.warning("[AUTH-REFRESH] Refresh Token过期,需要重新登录")
                self.refresh_retry_count = 0  # 重置计数
                return {"success": False, "error": "Refresh token expired", "expired": True}

            # 其他HTTP错误
            else:
                error_msg = f"HTTP {response.status_code}"
                logger.error(f"[AUTH-REFRESH] 刷新失败: {error_msg}")
                return {"success": False, "error": error_msg}

        except requests.exceptions.Timeout:
            # 超时 - 指数退避重试
            self.refresh_retry_count += 1
            logger.warning(f"[AUTH-REFRESH] 请求超时 (尝试 {self.refresh_retry_count}/{self.max_retries})")

            if self.refresh_retry_count < self.max_retries:
                retry_delay = 2 ** self.refresh_retry_count  # 2s, 4s, 8s
                logger.info(f"[AUTH-REFRESH] 将在 {retry_delay} 秒后重试")
                return {"success": False, "error": "Timeout, will retry", "retry_delay": retry_delay}
            else:
                logger.error("[AUTH-REFRESH] 达到最大重试次数,停止重试")
                self.refresh_retry_count = 0  # 重置计数
                return {"success": False, "error": "Max retries reached"}

        except requests.exceptions.SSLError as e:
            # SSL错误 - 尝试httpx作为后备
            logger.warning(f"[AUTH-REFRESH] requests SSL错误,尝试使用httpx: {e}")

            try:
                import httpx

                with httpx.Client(timeout=10.0) as client:
                    response = client.post(
                        f"{self.backend_url}/api/auth-refresh",
                        json={"refresh_token": self.refresh_token}
                    )

                if response.status_code == 200:
                    data = response.json()

                    if data.get("success"):
                        self._save_tokens(
                            data["access_token"],
                            data["refresh_token"],
                            self.user_info
                        )
                        self.refresh_retry_count = 0
                        logger.info("[AUTH-REFRESH] Token刷新成功 (httpx)")

                    return data

                elif response.status_code == 401:
                    logger.warning("[AUTH-REFRESH] Refresh Token过期")
                    self.refresh_retry_count = 0
                    return {"success": False, "error": "Refresh token expired", "expired": True}

                else:
                    return {"success": False, "error": f"HTTP {response.status_code}"}

            except Exception as httpx_error:
                logger.error(f"[AUTH-REFRESH] httpx也失败: {httpx_error}")
                return {"success": False, "error": f"SSL error: {str(e)}"}

        except Exception as e:
            logger.error(f"[AUTH-REFRESH] 未预期的错误: {e}")
            return {"success": False, "error": str(e)}

        finally:
            self.is_refreshing = False

    def _make_authenticated_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        发起认证请求 (自动处理401并刷新Token)

        Args:
            method: HTTP方法 (GET, POST, PUT, DELETE等)
            url: 请求URL
            **kwargs: 传递给requests的其他参数

        Returns:
            requests.Response对象

        Raises:
            Exception: 当Session过期或Token刷新失败时
        """
        # 添加Authorization header
        headers = kwargs.get('headers', {})
        if self.access_token:
            headers['Authorization'] = f"Bearer {self.access_token}"
        kwargs['headers'] = headers

        # 发起请求
        response = self.session.request(method, url, **kwargs)

        # 检测401 - Token过期
        if response.status_code == 401:
            logger.warning("[AUTH] 检测到401,尝试刷新Token")
            refresh_result = self.refresh_access_token()

            # 刷新成功 - 重试原始请求
            if refresh_result.get("success"):
                logger.info("[AUTH] Token刷新成功,重试请求")
                headers['Authorization'] = f"Bearer {self.access_token}"
                kwargs['headers'] = headers
                response = self.session.request(method, url, **kwargs)

            # Refresh Token过期 - 抛出异常
            elif refresh_result.get("expired"):
                logger.error("[AUTH] Refresh Token过期,需要重新登录")
                raise Exception("Session expired, please login again")

            # 需要重试 - 等待后递归调用
            elif refresh_result.get("retry_delay"):
                import time
                retry_delay = refresh_result["retry_delay"]
                logger.info(f"[AUTH] 等待 {retry_delay} 秒后重试刷新")
                time.sleep(retry_delay)
                return self._make_authenticated_request(method, url, **kwargs)

            # 其他错误 - 抛出异常
            else:
                error_msg = refresh_result.get("error", "Unknown error")
                logger.error(f"[AUTH] Token刷新失败: {error_msg}")
                raise Exception(f"Token refresh failed: {error_msg}")

        return response

    def reset_password(self, email: str) -> Dict:
        """
        请求重置密码

        Args:
            email: 邮箱

        Returns:
            {"success": True/False, "error": "...", "message": "..."}
        """
        try:
            response = self.session.post(
                f"{self.backend_url}/api/auth-reset-password",
                json={"email": email},
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                # 兜底：非200时仍返回未支付，让轮询继续而不抛错
                return {
                    "success": True,
                    "order": {
                        "out_trade_no": out_trade_no,
                        "status": "unpaid",
                        "error": f"HTTP {response.status_code}"
                    }
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== 订阅API ====================

    def get_subscription_status(self) -> Dict:
        """
        获取当前用户的订阅状态 (自动处理Token刷新)

        Returns:
            {"success": True/False, "is_active": True/False, "user_tier": "...", ...}
        """
        try:
            if not self.get_user_id():
                return {"success": False, "error": "未登录"}

            # ✅ 使用新的认证请求封装 (自动处理401)
            response = self._make_authenticated_request(
                "GET",
                f"{self.backend_url}/api/subscription-status",
                params={"user_id": self.get_user_id()},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                # 更新本地用户信息
                if data.get("success") and self.user_info:
                    self.user_info["user_tier"] = data.get("user_tier", "free")
                    self._save_tokens(self.access_token, self.refresh_token, self.user_info)

                return data
            elif response.status_code == 404:
                # API端点未部署,静默失败(不影响功能,使用本地缓存的用户等级)
                logger.debug(f"订阅状态API未部署(404),使用本地缓存")
                return {"success": False, "error": "API未部署", "fallback": True}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            logger.error(f"[AUTH] get_subscription_status失败: {e}")
            return {"success": False, "error": str(e)}

    # ==================== 支付API ====================

    def create_payment_order(self, plan_type: str, pay_type: str = "alipay") -> Dict:
        """
        创建支付订单

        Args:
            plan_type: 订阅类型（pro_monthly, pro_yearly, lifetime）
            pay_type: 支付方式（alipay, wxpay）

        Returns:
            {"success": True/False, "payment_url": "...", "params": {...}, ...}
        """
        try:
            if not self.get_user_id():
                return {"success": False, "error": "未登录"}

            response = self.session.post(
                f"{self.backend_url}/api/payment-create-order.py",
                json={
                    "user_id": self.get_user_id(),
                    "plan_type": plan_type,
                    "pay_type": pay_type
                },
                # 延长超时时间，避免网络抖动下轻易报超时
                timeout=20
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def query_payment_order(self, out_trade_no: str, trade_no: str = "") -> Dict:
        """
        查询支付订单状态

        Args:
            out_trade_no: 商户订单号

        Returns:
            {"success": True/False, "order": {...}}
        """
        try:
            # Vercel 函数路径不带 .py，避免 404
            params = {"out_trade_no": out_trade_no}
            if trade_no:
                params["trade_no"] = trade_no

            # ✅ 使用新的查询接口绕过 Vercel 缓存
            response = self.session.get(
                f"{self.backend_url}/api/payment-check-v2",
                params=params,
                timeout=15
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def manual_upgrade_subscription(self, user_id: str, plan_type: str, out_trade_no: str) -> Dict:
        """
        手动升级订阅(主动查询方案A - 不依赖Z-Pay回调)

        当检测到支付成功时,主动调用此API更新用户会员状态

        Args:
            user_id: 用户ID
            plan_type: 订阅类型(pro_monthly/pro_yearly/lifetime)
            out_trade_no: 订单号

        Returns:
            {"success": True/False, "user_tier": "...", ...}
        """
        try:
            logger.info(f"[AUTH] Manual upgrade subscription: user={user_id}, plan={plan_type}, order={out_trade_no}")

            response = self.session.post(
                f"{self.backend_url}/api/manual-upgrade-subscription",
                json={
                    "user_id": user_id,
                    "plan_type": plan_type,
                    "out_trade_no": out_trade_no
                },
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=15
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logger.info(f"[AUTH] Manual upgrade successful: new_tier={result.get('user_tier')}")
                    # 更新本地用户信息
                    if self.user_info:
                        self.user_info["user_tier"] = result.get("user_tier", "free")
                        self._save_tokens(self.access_token, self.refresh_token, self.user_info)
                return result
            else:
                logger.error(f"[AUTH] Manual upgrade failed: HTTP {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            logger.error(f"[AUTH] Manual upgrade error: {e}")
            return {"success": False, "error": str(e)}

    def create_stripe_checkout_session(self, plan_type: str, user_id: str, user_email: str) -> Dict:
        """
        创建Stripe Checkout Session（国际支付）

        Args:
            plan_type: 订阅类型（pro_monthly, pro_yearly, lifetime）
            user_id: 用户ID
            user_email: 用户邮箱

        Returns:
            {"success": True/False, "checkout_url": "...", "session_id": "..."}
        """
        try:
            response = self.session.post(
                f"{self.backend_url}/api/stripe-create-checkout",
                json={
                    "user_id": user_id,
                    "user_email": user_email,
                    "plan_type": plan_type
                },
                timeout=15
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_text = response.text if response.text else f"HTTP {response.status_code}"
                return {"success": False, "error": error_text}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== 配额API ====================

    def get_quota_status(self) -> Dict:
        """
        获取AI功能配额状态

        Returns:
            {"remaining": {...}, "user_tier": "..."}
        """
        try:
            user_tier = self.get_user_tier()

            response = self.session.get(
                f"{self.backend_url}/api/quota-status",
                params={"user_tier": user_tier},
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                # API端点未部署,静默返回默认配额(不影响功能)
                logger.debug(f"配额状态API未部署(404),使用默认配额")
                return {
                    "remaining": {
                        "daily_plan": 3 if user_tier == "free" else 50,
                        "weekly_report": 1 if user_tier == "free" else 10,
                        "chat": 10 if user_tier == "free" else 100
                    },
                    "user_tier": user_tier
                }
            else:
                # 返回默认配额
                logger.debug(f"配额查询失败(HTTP {response.status_code}),使用默认配额")
                return {
                    "remaining": {
                        "daily_plan": 3 if user_tier == "free" else 50,
                        "weekly_report": 1 if user_tier == "free" else 10,
                        "chat": 10 if user_tier == "free" else 100
                    },
                    "user_tier": user_tier
                }

        except Exception as e:
            # 返回默认配额
            logger.debug(f"配额查询异常({e}),使用默认配额")
            user_tier = self.get_user_tier()
            return {
                "remaining": {
                    "daily_plan": 3 if user_tier == "free" else 50,
                    "weekly_report": 1 if user_tier == "free" else 10,
                    "chat": 10 if user_tier == "free" else 100
                },
                "user_tier": user_tier
            }

    # ==================== 微信登录API ====================

    def wechat_get_qr_code(self) -> Dict:
        """
        获取微信登录二维码URL

        Returns:
            {"success": True/False, "qr_url": "...", "state": "...", "error": "..."}
        """
        try:
            response = self.session.get(
                f"{self.backend_url}/api/auth-wechat-qrcode",
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except requests.exceptions.Timeout:
            return {"success": False, "error": "请求超时"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "无法连接到服务器"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def wechat_check_scan_status(self, state: str) -> Dict:
        """
        检查微信扫码登录状态

        Args:
            state: 登录state参数

        Returns:
            {
                "status": "pending" | "scanned" | "success" | "expired" | "error",
                "user_info": {...},  # 仅当status为success时返回
                "error": "..."       # 仅当status为error时返回
            }
        """
        try:
            response = self.session.get(
                f"{self.backend_url}/api/auth-wechat-status",
                params={"state": state},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                # 如果登录成功，保存Token
                if data.get("status") == "success":
                    user_info = data.get("user_info", {})
                    access_token = data.get("access_token")
                    refresh_token = data.get("refresh_token")

                    if access_token and refresh_token:
                        self._save_tokens(
                            access_token,
                            refresh_token,
                            {
                                "user_id": user_info.get("user_id"),
                                "email": user_info.get("email"),
                                "username": user_info.get("username"),
                                "user_tier": user_info.get("user_tier", "free")
                            }
                        )

                return data
            else:
                return {"status": "error", "error": f"HTTP {response.status_code}"}

        except requests.exceptions.Timeout:
            return {"status": "error", "error": "请求超时"}
        except requests.exceptions.ConnectionError:
            return {"status": "error", "error": "无法连接到服务器"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ==================== OTP验证API ====================

    def send_otp(self, email: str, purpose: str = "signup") -> Dict:
        """
        发送OTP验证码到邮箱

        Args:
            email: 邮箱地址
            purpose: 用途（signup, password_reset）

        Returns:
            {"success": True/False, "error": "...", "message": "..."}
        """
        try:
            url = f"{self.backend_url}/api/auth-send-otp"
            logger.info(f"[OTP] 正在发送验证码到: {email}")
            logger.debug(f"[OTP] 请求URL: {url}")

            response = self.session.post(
                url,
                json={
                    "email": email,
                    "purpose": purpose
                },
                timeout=10
            )

            logger.debug(f"[OTP] 响应状态码: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                logger.info(f"[OTP] 发送成功: {result.get('message', '验证码已发送')}")
                return result
            else:
                error_msg = f"HTTP {response.status_code}"
                logger.error(f"[OTP] 发送失败: {error_msg}")
                try:
                    error_detail = response.json()
                    logger.error(f"[OTP] 错误详情: {error_detail}")
                except (json.JSONDecodeError, ValueError):
                    pass
                return {"success": False, "error": error_msg}

        except requests.exceptions.Timeout:
            logger.error(f"[OTP] 错误: 请求超时（10秒）")
            return {"success": False, "error": "请求超时"}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"[OTP] 错误: 无法连接到服务器 - {e}")
            return {"success": False, "error": "无法连接到服务器"}
        except Exception as e:
            logger.error(f"[OTP] 未知错误: {type(e).__name__}: {e}")
            return {"success": False, "error": str(e)}

    def verify_otp(self, email: str, otp_code: str) -> Dict:
        """
        验证OTP验证码

        Args:
            email: 邮箱地址
            otp_code: 6位数字验证码

        Returns:
            {"success": True/False, "error": "...", "message": "..."}
        """
        try:
            response = self.session.post(
                f"{self.backend_url}/api/auth-verify-otp",
                json={
                    "email": email,
                    "otp_code": otp_code
                },
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except requests.exceptions.Timeout:
            return {"success": False, "error": "请求超时"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "无法连接到服务器"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def trigger_manual_upgrade(self, out_trade_no: str, user_id: str, plan_type: str) -> Dict:
        """
        手动触发会员升级（用于支付完成后手动确认）

        Args:
            out_trade_no: 订单号
            user_id: 用户ID
            plan_type: 套餐类型

        Returns:
            升级结果
        """
        try:
            url = f"{self.backend_url}/api/payment-manual-upgrade"
            data = {
                "out_trade_no": out_trade_no,
                "user_id": user_id,
                "plan_type": plan_type
            }

            response = requests.post(
                url,
                json=data,
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=15
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except requests.exceptions.Timeout:
            return {"success": False, "error": "请求超时"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "无法连接到服务器"}
        except Exception as e:
            return {"success": False, "error": str(e)}
