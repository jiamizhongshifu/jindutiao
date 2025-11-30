"""
App分类管理器
管理应用程序的分类规则和用户自定义设置
"""

import logging
from typing import Dict, List, Optional, Set
from gaiya.data.db_manager import db

logger = logging.getLogger("gaiya.services.app_category_manager")

class AppCategoryManager:
    """App分类管理器"""

    # 默认分类映射
    DEFAULT_APP_CATEGORIES = {
        "WINWORD.EXE": "PRODUCTIVE",
        "EXCEL.EXE": "PRODUCTIVE",
        "POWERPNT.EXE": "PRODUCTIVE",
        "Code.exe": "PRODUCTIVE",
        "idea64.exe": "PRODUCTIVE",
        "Figma.exe": "PRODUCTIVE",
        "Photoshop.exe": "PRODUCTIVE",
        "Illustrator.exe": "PRODUCTIVE",
        "PremierePro.exe": "PRODUCTIVE",
        "AfterFX.exe": "PRODUCTIVE",
        "Chrome.exe": "PRODUCTIVE",  # 可以后期按域名细化
        "msedge.exe": "PRODUCTIVE",  # 可以后期按域名细化
        "Firefox.exe": "PRODUCTIVE",

        "WeChat.exe": "LEISURE",
        "QQ.exe": "LEISURE",
        "TIM.exe": "LEISURE",
        "DingTalk.exe": "LEISURE",
        "FeiQ.exe": "LEISURE",
        "Telegram.exe": "LEISURE",
        "Discord.exe": "LEISURE",
        "Slack.exe": "LEISURE",

        "steam.exe": "LEISURE",
        "Battle.net.exe": "LEISURE",
        "EpicGamesLauncher.exe": "LEISURE",
        "Origin.exe": "LEISURE",
        "Uplay.exe": "LEISURE",
        "WutheringWaves.exe": "LEISURE",
        "GenshinImpact.exe": "LEISURE",

        "explorer.exe": "NEUTRAL",
        "cmd.exe": "NEUTRAL",
        "PowerShell.exe": "NEUTRAL",
        "WindowsTerminal.exe": "NEUTRAL",
        "Taskmgr.exe": "NEUTRAL",
        "regedit.exe": "NEUTRAL",
        "msconfig.exe": "NEUTRAL",
        "services.msc": "NEUTRAL",

        "notepad.exe": "NEUTRAL",
        "calc.exe": "NEUTRAL",
        "mspaint.exe": "NEUTRAL",
        "SnippingTool.exe": "NEUTRAL",
        "winrar.exe": "NEUTRAL",
        "7zFM.exe": "NEUTRAL",

        "vlc.exe": "LEISURE",
        "PotPlayerMini64.exe": "LEISURE",
        "网易云音乐.exe": "LEISURE",
        "QQ音乐.exe": "LEISURE",
        "酷狗音乐.exe": "LEISURE",
        "Spotify.exe": "LEISURE"
    }

    def __init__(self):
        self._category_cache: Dict[str, str] = {}
        self._ignored_apps: Set[str] = set()
        self._load_categories()

    def _load_categories(self):
        """从数据库加载分类设置"""
        try:
            all_categories = db.get_all_app_categories()
            for process_name, category, is_ignored in all_categories:
                self._category_cache[process_name.upper()] = category
                if is_ignored:
                    self._ignored_apps.add(process_name.upper())

            logger.info(f"已加载 {len(self._category_cache)} 个App分类设置")
        except Exception as e:
            logger.error(f"加载App分类设置失败: {e}")
            # 使用默认分类
            self._category_cache = {k.upper(): v for k, v in self.DEFAULT_APP_CATEGORIES.items()}

    def get_app_category(self, process_name: str) -> str:
        """获取App分类"""
        if not process_name:
            return "UNKNOWN"

        process_name_upper = process_name.upper()

        # 检查是否被忽略
        if process_name_upper in self._ignored_apps:
            return "IGNORED"

        # 检查缓存
        if process_name_upper in self._category_cache:
            return self._category_cache[process_name_upper]

        # 使用默认分类
        if process_name_upper in self.DEFAULT_APP_CATEGORIES:
            category = self.DEFAULT_APP_CATEGORIES[process_name_upper]
            self._category_cache[process_name_upper] = category
            return category

        # 未知分类
        return "UNKNOWN"

    def set_app_category(self, process_name: str, category: str, is_ignored: bool = False):
        """设置App分类"""
        try:
            process_name_upper = process_name.upper()

            # 更新数据库
            db.set_app_category(process_name, category, is_ignored)

            # 更新缓存
            self._category_cache[process_name_upper] = category
            if is_ignored:
                self._ignored_apps.add(process_name_upper)
            else:
                self._ignored_apps.discard(process_name_upper)

            logger.info(f"已更新 {process_name} 分类为 {category} (忽略: {is_ignored})")
        except Exception as e:
            logger.error(f"设置App分类失败: {e}")

    def get_all_categories(self) -> List[Dict]:
        """获取所有分类设置"""
        categories = []
        for process_name, category in self._category_cache.items():
            categories.append({
                'process_name': process_name,
                'category': category,
                'is_ignored': process_name in self._ignored_apps
            })
        return categories

    def get_recent_apps(self, days: int = 7) -> List[Dict]:
        """获取最近使用的App列表"""
        try:
            from datetime import datetime, timedelta
            start_date = datetime.now() - timedelta(days=days)

            # 这里需要从数据库查询最近的行为记录
            # 暂时返回缓存中的数据
            recent_apps = []
            for process_name, category in self._category_cache.items():
                recent_apps.append({
                    'process_name': process_name,
                    'category': category,
                    'is_ignored': process_name in self._ignored_apps,
                    'last_seen': None,  # 需要从数据库查询
                    'total_duration': 0  # 需要从数据库查询
                })

            return recent_apps
        except Exception as e:
            logger.error(f"获取最近App列表失败: {e}")
            return []

    def import_default_categories(self):
        """导入默认分类设置"""
        try:
            for process_name, category in self.DEFAULT_APP_CATEGORIES.items():
                if process_name.upper() not in self._category_cache:
                    db.set_app_category(process_name, category, False)
                    self._category_cache[process_name.upper()] = category

            logger.info(f"已导入 {len(self.DEFAULT_APP_CATEGORIES)} 个默认App分类")
        except Exception as e:
            logger.error(f"导入默认分类失败: {e}")

    def clear_all_data(self):
        """清除所有分类数据"""
        try:
            # 清除数据库中的分类数据
            # 这里需要在数据库管理器中添加相应方法

            # 清除缓存
            self._category_cache.clear()
            self._ignored_apps.clear()

            logger.info("已清除所有App分类数据")
        except Exception as e:
            logger.error(f"清除分类数据失败: {e}")

    def get_category_stats(self) -> Dict[str, int]:
        """获取分类统计"""
        stats = {
            "PRODUCTIVE": 0,
            "LEISURE": 0,
            "NEUTRAL": 0,
            "UNKNOWN": 0,
            "IGNORED": 0
        }

        for category in self._category_cache.values():
            if category in stats:
                stats[category] += 1

        stats["IGNORED"] = len(self._ignored_apps)
        return stats

# 全局实例
app_category_manager = AppCategoryManager()