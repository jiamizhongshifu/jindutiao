"""
App Recommender - 智能应用分类推荐引擎

基于规则库和关键词匹配为应用推荐分类

Author: GaiYa Team
Date: 2025-12-09
"""

import logging
from typing import Dict, List, Optional


class AppRecommender:
    """应用分类推荐引擎 - 根据应用名称智能推荐分类"""

    # 内置应用知识库 (只列举部分,完整版见文末)
    KNOWN_APPS = {
        # 开发工具
        'code.exe': {'category': 'PRODUCTIVE', 'confidence': 0.95, 'emoji': '💻', 'description': 'VS Code - 代码编辑器'},
        'cursor.exe': {'category': 'PRODUCTIVE', 'confidence': 0.95, 'emoji': '✨', 'description': 'Cursor - AI代码编辑器'},
        'pycharm64.exe': {'category': 'PRODUCTIVE', 'confidence': 0.95, 'emoji': '🐍', 'description': 'PyCharm - Python IDE'},
        'webstorm64.exe': {'category': 'PRODUCTIVE', 'confidence': 0.95, 'emoji': '🌊', 'description': 'WebStorm - Web IDE'},
        'idea64.exe': {'category': 'PRODUCTIVE', 'confidence': 0.95, 'emoji': '💡', 'description': 'IntelliJ IDEA - Java IDE'},

        # 办公软件
        'winword.exe': {'category': 'PRODUCTIVE', 'confidence': 0.90, 'emoji': '📄', 'description': 'Word - 文档编辑'},
        'excel.exe': {'category': 'PRODUCTIVE', 'confidence': 0.90, 'emoji': '📊', 'description': 'Excel - 电子表格'},
        'powerpnt.exe': {'category': 'PRODUCTIVE', 'confidence': 0.90, 'emoji': '📽️', 'description': 'PowerPoint - 演示'},
        'notion.exe': {'category': 'PRODUCTIVE', 'confidence': 0.90, 'emoji': '📝', 'description': 'Notion - 笔记协作'},
        'obsidian.exe': {'category': 'PRODUCTIVE', 'confidence': 0.90, 'emoji': '📝', 'description': 'Obsidian - 知识管理'},

        # 浏览器
        'chrome.exe': {'category': 'NEUTRAL', 'confidence': 0.85, 'emoji': '🌐', 'description': 'Chrome - 网页浏览'},
        'msedge.exe': {'category': 'NEUTRAL', 'confidence': 0.85, 'emoji': '🌐', 'description': 'Edge - 网页浏览'},
        'firefox.exe': {'category': 'NEUTRAL', 'confidence': 0.85, 'emoji': '🦊', 'description': 'Firefox - 网页浏览'},

        # 通讯工具
        'wechat.exe': {'category': 'LEISURE', 'confidence': 0.90, 'emoji': '💬', 'description': '微信 - 即时通讯'},
        'qq.exe': {'category': 'LEISURE', 'confidence': 0.90, 'emoji': '🐧', 'description': 'QQ - 即时通讯'},
        'dingtalk.exe': {'category': 'PRODUCTIVE', 'confidence': 0.85, 'emoji': '📱', 'description': '钉钉 - 企业通讯'},
        'feishu.exe': {'category': 'PRODUCTIVE', 'confidence': 0.85, 'emoji': '🚀', 'description': '飞书 - 企业协作'},
        'slack.exe': {'category': 'PRODUCTIVE', 'confidence': 0.85, 'emoji': '💬', 'description': 'Slack - 团队协作'},
        'discord.exe': {'category': 'LEISURE', 'confidence': 0.85, 'emoji': '🎮', 'description': 'Discord - 语音聊天'},

        # 娱乐应用
        'bilibili.exe': {'category': 'LEISURE', 'confidence': 0.95, 'emoji': '📺', 'description': 'B站 - 视频播放'},
        'steam.exe': {'category': 'LEISURE', 'confidence': 0.95, 'emoji': '🎮', 'description': 'Steam - 游戏平台'},
        'cloudmusic.exe': {'category': 'LEISURE', 'confidence': 0.90, 'emoji': '🎵', 'description': '网易云音乐'},
        'qqmusic.exe': {'category': 'LEISURE', 'confidence': 0.90, 'emoji': '🎵', 'description': 'QQ音乐'},

        # 系统工具
        'explorer.exe': {'category': 'NEUTRAL', 'confidence': 0.90, 'emoji': '📁', 'description': '文件资源管理器'},
        'taskmgr.exe': {'category': 'NEUTRAL', 'confidence': 0.85, 'emoji': '⚙️', 'description': '任务管理器'},
        'windowsterminal.exe': {'category': 'PRODUCTIVE', 'confidence': 0.80, 'emoji': '💻', 'description': 'Windows Terminal'},
    }

    # 关键词规则 (用于模糊匹配)
    KEYWORD_RULES = [
        {'keywords': ['code', 'studio', 'ide', 'dev', 'git'], 'category': 'PRODUCTIVE', 'confidence': 0.75, 'emoji': '💻', 'description': '开发工具'},
        {'keywords': ['word', 'excel', 'office', 'notion'], 'category': 'PRODUCTIVE', 'confidence': 0.70, 'emoji': '📄', 'description': '办公软件'},
        {'keywords': ['game', 'play', 'steam', 'epic'], 'category': 'LEISURE', 'confidence': 0.80, 'emoji': '🎮', 'description': '游戏平台'},
        {'keywords': ['music', 'spotify', 'qq音乐'], 'category': 'LEISURE', 'confidence': 0.75, 'emoji': '🎵', 'description': '音乐播放'},
        {'keywords': ['video', 'player', 'bilibili'], 'category': 'LEISURE', 'confidence': 0.75, 'emoji': '📺', 'description': '视频播放'},
        {'keywords': ['chrome', 'edge', 'firefox', 'browser'], 'category': 'NEUTRAL', 'confidence': 0.65, 'emoji': '🌐', 'description': '网页浏览器'},
    ]

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def recommend_category(self, app_name: str) -> Dict:
        """推荐应用分类"""
        if not app_name:
            return self._default_recommendation('空应用名称')

        app_lower = app_name.lower()

        # 1. 精确匹配
        if app_lower in self.KNOWN_APPS:
            result = self.KNOWN_APPS[app_lower].copy()
            result['reason'] = f'✅ 已知应用: {result["description"]}'
            self.logger.debug(f"精确匹配: {app_name} -> {result['category']}")
            return result

        # 2. 关键词匹配
        for rule in self.KEYWORD_RULES:
            if any(kw in app_lower for kw in rule['keywords']):
                result = {
                    'category': rule['category'],
                    'confidence': rule['confidence'],
                    'emoji': rule['emoji'],
                    'description': rule['description'],
                    'reason': f'🔍 关键词匹配: {rule["description"]}'
                }
                self.logger.debug(f"关键词匹配: {app_name} -> {result['category']}")
                return result

        # 3. 默认中性
        return self._default_recommendation('无法识别的应用')

    def _default_recommendation(self, reason: str) -> Dict:
        return {
            'category': 'NEUTRAL',
            'confidence': 0.3,
            'emoji': '❓',
            'description': '未分类应用',
            'reason': f'⚠️ {reason},建议手动分类'
        }

    def batch_recommend(self, app_names: List[str]) -> Dict[str, Dict]:
        """批量推荐"""
        recommendations = {}
        for app_name in app_names:
            recommendations[app_name] = self.recommend_category(app_name)
        self.logger.info(f"批量推荐完成: {len(recommendations)} 个应用")
        return recommendations

    def get_recommendation_stats(self) -> Dict[str, int]:
        """获取推荐统计"""
        stats = {
            'total_known_apps': len(self.KNOWN_APPS),
            'total_rules': len(self.KEYWORD_RULES),
            'productive_apps': sum(1 for app in self.KNOWN_APPS.values() if app['category'] == 'PRODUCTIVE'),
            'leisure_apps': sum(1 for app in self.KNOWN_APPS.values() if app['category'] == 'LEISURE'),
            'neutral_apps': sum(1 for app in self.KNOWN_APPS.values() if app['category'] == 'NEUTRAL'),
        }
        return stats
