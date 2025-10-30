# -*- coding: utf-8 -*-
"""
PyDayBar AI Client
客户端封装,用于在GUI中调用AI功能
"""
import requests
from typing import Dict, List, Optional
from PySide6.QtWidgets import QMessageBox


class PyDayBarAIClient:
    """PyDayBar AI 功能客户端"""

    def __init__(self, backend_url: str = "http://localhost:5000", user_id: str = "user_demo"):
        self.backend_url = backend_url
        self.user_id = user_id
        self.user_tier = "free"  # 默认免费版
        self.timeout = 60

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
                "无法连接到AI服务器\n请确保backend_api.py正在运行",
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
            response = requests.get(
                f"{self.backend_url}/api/quota-status",
                params={
                    "user_id": self.user_id,
                    "user_tier": self.user_tier
                },
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            return None

        except Exception:
            return None

    def check_backend_health(self) -> bool:
        """
        检查后端服务器健康状态

        Returns:
            True表示服务器正常, False表示异常
        """
        try:
            response = requests.get(
                f"{self.backend_url}/health",
                timeout=5
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
