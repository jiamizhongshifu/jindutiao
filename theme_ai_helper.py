# -*- coding: utf-8 -*-
"""
PyDayBar AI 主题助手
提供AI驱动的主题推荐和生成功能
"""

import requests
from typing import Dict, List, Optional
from PySide6.QtWidgets import QMessageBox
import json


class ThemeAIHelper:
    """AI 主题助手"""
    
    def __init__(self, ai_client):
        """
        初始化AI主题助手
        
        参数:
        - ai_client: PyDayBarAIClient 实例
        """
        self.ai_client = ai_client
    
    def analyze_task_names(self, tasks: List[Dict]) -> Dict:
        """
        分析任务名称，提取关键词和类型分布
        
        参数:
        - tasks: 任务列表
        
        返回:
        - 包含任务类型分布和关键词的字典
        """
        task_types = {}
        keywords = []
        
        # 任务类型关键词映射
        type_keywords = {
            'work': ['工作', '上班', '办公', '代码', '开发', '会议', '开会', 'work', 'office'],
            'break': ['休息', '午休', '小憩', 'break', 'rest'],
            'study': ['学习', '阅读', '课程', 'study', 'learn', 'read'],
            'exercise': ['运动', '健身', '锻炼', '跑步', 'exercise', 'sport', 'fitness'],
            'meeting': ['会议', '讨论', 'meeting', 'discuss'],
            'other': ['其他', 'other']
        }
        
        for task in tasks:
            task_name = task.get('task', '').lower()
            
            # 统计任务类型
            for task_type, keywords_list in type_keywords.items():
                for keyword in keywords_list:
                    if keyword.lower() in task_name:
                        task_types[task_type] = task_types.get(task_type, 0) + 1
                        break
            
            # 提取关键词
            keywords.append(task_name)
        
        return {
            'task_types': task_types,
            'keywords': keywords,
            'total_tasks': len(tasks)
        }
    
    def recommend_themes(self, tasks_data: List[Dict], statistics: Optional[Dict] = None) -> Optional[List[Dict]]:
        """
        基于任务分析推荐主题（考虑任务名称）
        
        参数:
        - tasks_data: 任务列表 [{"task": "工作", "start": "09:00", ...}, ...]
        - statistics: 统计数据（可选）
        
        返回:
        - 推荐主题列表，每个包含：主题名称、配色方案、推荐理由
        """
        try:
            # 分析任务名称
            task_analysis = self.analyze_task_names(tasks_data)
            
            # 构建请求数据
            request_data = {
                "tasks": tasks_data,
                "task_analysis": task_analysis,
                "statistics": statistics or {}
            }
            
            # 调用后端API
            response = requests.post(
                f"{self.ai_client.backend_url}/api/recommend-theme",
                json={
                    "user_id": self.ai_client.user_id,
                    "tasks": tasks_data,
                    "task_analysis": task_analysis,
                    "statistics": statistics or {},
                    "user_tier": self.ai_client.user_tier
                },
                timeout=self.ai_client.timeout
            )
            
            if response.status_code == 403:
                # 配额用尽
                data = response.json()
                self.ai_client._show_quota_exceeded_dialog(data, None)
                return None
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return data.get('recommendations', [])
                else:
                    self.ai_client._show_error_dialog(
                        f"推荐失败: {data.get('error', '未知错误')}",
                        None
                    )
                    return None
            else:
                error_data = response.json()
                self.ai_client._show_error_dialog(
                    f"推荐失败: {error_data.get('error', '未知错误')}",
                    None
                )
                return None
                
        except requests.exceptions.Timeout:
            self.ai_client._show_error_dialog("请求超时,请稍后重试", None)
            return None
        except requests.exceptions.ConnectionError:
            self.ai_client._show_error_dialog(
                "无法连接到AI服务器\n请确保backend_api.py正在运行",
                None
            )
            return None
        except Exception as e:
            self.ai_client._show_error_dialog(f"发生错误: {str(e)}", None)
            return None
    
    def generate_theme_from_description(self, description: str) -> Optional[Dict]:
        """
        从自然语言描述生成主题
        
        参数:
        - description: 如"清新自然的工作主题"
        
        返回:
        - 完整主题配置字典
        """
        try:
            # 调用后端API
            response = requests.post(
                f"{self.ai_client.backend_url}/api/generate-theme",
                json={
                    "user_id": self.ai_client.user_id,
                    "description": description,
                    "user_tier": self.ai_client.user_tier
                },
                timeout=self.ai_client.timeout
            )
            
            if response.status_code == 403:
                # 配额用尽
                data = response.json()
                self.ai_client._show_quota_exceeded_dialog(data, None)
                return None
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return data.get('theme', {})
                else:
                    self.ai_client._show_error_dialog(
                        f"生成失败: {data.get('error', '未知错误')}",
                        None
                    )
                    return None
            else:
                error_data = response.json()
                self.ai_client._show_error_dialog(
                    f"生成失败: {error_data.get('error', '未知错误')}",
                    None
                )
                return None
                
        except requests.exceptions.Timeout:
            self.ai_client._show_error_dialog("请求超时,请稍后重试", None)
            return None
        except requests.exceptions.ConnectionError:
            self.ai_client._show_error_dialog(
                "无法连接到AI服务器\n请确保backend_api.py正在运行",
                None
            )
            return None
        except Exception as e:
            self.ai_client._show_error_dialog(f"发生错误: {str(e)}", None)
            return None

