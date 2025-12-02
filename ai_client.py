# -*- coding: utf-8 -*-
"""
GaiYa每日进度条 - AI Client
客户端封装,用于在GUI中调用AI功能
统一使用代理服务器，保护API密钥安全
"""
import os
import requests
from typing import Dict, List, Optional
from PySide6.QtWidgets import QMessageBox


class GaiyaAIClient:
    """GaiYa每日进度条 - AI功能客户端"""

    def __init__(self, backend_url: Optional[str] = None, user_id: str = "user_demo"):
        """
        初始化AI客户端

        参数:
        - backend_url: 后端服务器URL，如果为None则使用默认Vercel服务
        - user_id: 用户ID
        """
        # 使用Vercel云端服务（避免本地API密钥泄露）
        if backend_url is None:
            backend_url = os.getenv(
                "GAIYA_API_URL",
                "https://api.gaiyatime.com"  # 默认Vercel服务器URL
            )

        self.backend_url = backend_url
        self.user_id = user_id
        self.user_tier = "free"  # 默认免费版
        self.timeout = 60  # API请求超时时间（秒）
        self.service_type = "cloud"  # 云端服务

    def set_user_tier(self, tier: str):
        """设置用户等级"""
        if tier in ["free", "pro"]:
            self.user_tier = tier

    def plan_tasks(self, user_input: str, parent_widget=None) -> Optional[Dict]:
        """
        调用任务规划API

        Args:
            user_input: 用户的自然语言输入
            parent_widget: 父窗口(用于显示对话框)

        Returns:
            {"tasks": [...], "quota_info": {...}} 或 None(如果失败)
        """
        try:
            response = requests.post(
                f"{self.backend_url}/api/plan-tasks",
                json={
                    "user_id": self.user_id,
                    "input": user_input,
                    "user_tier": self.user_tier
                },
                timeout=self.timeout
            )

            if response.status_code == 403:
                # 配额用尽
                data = response.json()
                self._show_quota_exceeded_dialog(data, parent_widget)
                return None

            if response.status_code == 200:
                return response.json()
            else:
                error_data = response.json()
                self._show_error_dialog(
                    f"任务规划失败: {error_data.get('error', '未知错误')}",
                    parent_widget
                )
                return None

        except requests.exceptions.Timeout:
            self._show_error_dialog("请求超时,请稍后重试", parent_widget)
            return None
        except requests.exceptions.ConnectionError:
            self._show_error_dialog(
                "无法连接到AI云服务\n请检查网络连接",
                parent_widget
            )
            return None
        except Exception as e:
            self._show_error_dialog(f"发生错误: {str(e)}", parent_widget)
            return None

    def generate_weekly_report(self, statistics: Dict, parent_widget=None) -> Optional[str]:
        """
        生成周报

        Args:
            statistics: 统计数据字典
            parent_widget: 父窗口

        Returns:
            Markdown格式的周报文本 或 None
        """
        try:
            response = requests.post(
                f"{self.backend_url}/api/generate-weekly-report",
                json={
                    "user_id": self.user_id,
                    "statistics": statistics,
                    "user_tier": self.user_tier
                },
                timeout=self.timeout
            )

            if response.status_code == 403:
                data = response.json()
                self._show_quota_exceeded_dialog(data, parent_widget)
                return None

            if response.status_code == 200:
                data = response.json()
                return data.get("report", "")
            else:
                error_data = response.json()
                self._show_error_dialog(
                    f"周报生成失败: {error_data.get('error', '未知错误')}",
                    parent_widget
                )
                return None

        except Exception as e:
            self._show_error_dialog(f"发生错误: {str(e)}", parent_widget)
            return None

    def chat_query(self, query: str, context: Dict, parent_widget=None) -> Optional[str]:
        """
        对话查询

        Args:
            query: 用户问题
            context: 统计数据上下文
            parent_widget: 父窗口

        Returns:
            AI回答 或 None
        """
        try:
            response = requests.post(
                f"{self.backend_url}/api/chat-query",
                json={
                    "user_id": self.user_id,
                    "query": query,
                    "context": context,
                    "user_tier": self.user_tier
                },
                timeout=self.timeout
            )

            if response.status_code == 403:
                data = response.json()
                self._show_quota_exceeded_dialog(data, parent_widget)
                return None

            if response.status_code == 200:
                data = response.json()
                return data.get("response", "")
            else:
                error_data = response.json()
                self._show_error_dialog(
                    f"查询失败: {error_data.get('error', '未知错误')}",
                    parent_widget
                )
                return None

        except Exception as e:
            self._show_error_dialog(f"发生错误: {str(e)}", parent_widget)
            return None

    def get_quota_status(self) -> Optional[Dict]:
        """
        查询配额状态

        Returns:
            配额信息字典 或 None
        """
        try:
            # Vercel冷启动可能需要10-15秒，使用较长的超时时间
            response = requests.get(
                f"{self.backend_url}/api/quota-status",
                params={
                    "user_id": self.user_id,
                    "user_tier": self.user_tier
                },
                timeout=20
            )

            if response.status_code == 200:
                return response.json()
            return None

        except Exception:
            return None

    def analyze_task_completion(self, date: str, task_completions: List[Dict], parent_widget=None) -> Optional[str]:
        """
        分析任务完成情况

        Args:
            date: 日期 (YYYY-MM-DD)
            task_completions: 任务完成数据列表
            parent_widget: 父窗口

        Returns:
            AI分析文本 或 None
        """
        try:
            response = requests.post(
                f"{self.backend_url}/api/analyze-task-completion",
                json={
                    "user_id": self.user_id,
                    "date": date,
                    "task_completions": task_completions,
                    "user_tier": self.user_tier
                },
                timeout=self.timeout
            )

            # 检查响应状态
            if response.status_code == 404:
                self._show_error_dialog(
                    "AI分析功能暂未部署\n\n"
                    "该功能需要在Vercel后端部署 analyze-task-completion.py\n"
                    "当前仅支持本地推理引擎",
                    parent_widget
                )
                return None

            if response.status_code == 429:
                # 配额用尽或速率限制
                try:
                    data = response.json()
                    self._show_quota_exceeded_dialog(data, parent_widget)
                except:
                    self._show_error_dialog("API配额已用尽，请稍后重试", parent_widget)
                return None

            if response.status_code == 200:
                try:
                    data = response.json()
                    return data.get("analysis", "")
                except ValueError:
                    self._show_error_dialog("服务器返回了无效的响应格式", parent_widget)
                    return None
            else:
                # 其他错误状态码
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', f'HTTP {response.status_code}')
                except:
                    error_msg = f"HTTP {response.status_code}: {response.text[:100]}"

                self._show_error_dialog(
                    f"分析失败: {error_msg}",
                    parent_widget
                )
                return None

        except requests.exceptions.Timeout:
            self._show_error_dialog("分析请求超时,请稍后重试", parent_widget)
            return None
        except requests.exceptions.ConnectionError:
            self._show_error_dialog(
                "无法连接到AI云服务\n请检查网络连接",
                parent_widget
            )
            return None
        except ValueError as e:
            # JSON解析错误
            self._show_error_dialog(
                f"响应解析失败\n可能是服务端返回了非JSON格式数据\n\n错误: {str(e)}",
                parent_widget
            )
            return None
        except Exception as e:
            self._show_error_dialog(f"发生错误: {str(e)}", parent_widget)
            return None

    def check_backend_health(self) -> bool:
        """
        检查后端服务器健康状态

        Returns:
            True表示服务器正常, False表示异常
        """
        try:
            # Vercel冷启动可能需要10-15秒，使用较长的超时时间
            response = requests.get(
                f"{self.backend_url}/api/health",
                timeout=15
            )
            return response.status_code == 200
        except Exception:
            return False

    def _show_quota_exceeded_dialog(self, data: Dict, parent_widget):
        """显示配额用尽对话框"""
        if parent_widget is None:
            return

        feature_names = {
            "daily_plan": "任务规划",
            "weekly_report": "周报生成",
            "chat": "对话查询"
        }

        feature = data.get("feature", "")
        feature_name = feature_names.get(feature, feature)
        used = data.get("used", 0)
        quota = data.get("quota", 0)
        tier = data.get("user_tier", "free")

        msg = QMessageBox(parent_widget)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("配额已用尽")
        msg.setText(f"您今日的 {feature_name} 配额已用尽")
        msg.setInformativeText(
            f"当前版本: {tier.upper()}\n"
            f"已使用: {used}/{quota}\n\n"
            "升级到专业版以获得更多配额!"
        )
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()

    def _show_error_dialog(self, error_message: str, parent_widget):
        """显示错误对话框"""
        if parent_widget is None:
            return

        msg = QMessageBox(parent_widget)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("错误")
        msg.setText(error_message)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()
