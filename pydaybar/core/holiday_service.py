# -*- coding: utf-8 -*-
"""
节假日服务
提供节假日查询功能，使用 timor.tech 免费API
"""

import json
import logging
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict


class HolidayService:
    """节假日查询服务"""

    # API基础URL
    API_BASE_URL = "http://timor.tech/api/holiday"

    def __init__(self, app_dir: Path, logger: Optional[logging.Logger] = None):
        """
        初始化节假日服务

        Args:
            app_dir: 应用根目录
            logger: 日志记录器
        """
        self.app_dir = app_dir
        self.logger = logger or logging.getLogger(__name__)

        # 缓存文件路径
        self.cache_dir = app_dir / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "holidays_cache.json"

        # 内存缓存
        self.holiday_cache: Dict = {}

        # 加载本地缓存
        self._load_cache()

    def _load_cache(self):
        """从本地文件加载缓存"""
        if not self.cache_file.exists():
            self.logger.info("节假日缓存文件不存在，将首次从API获取")
            return

        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                self.holiday_cache = json.load(f)
            self.logger.info(f"成功加载节假日缓存，包含 {len(self.holiday_cache)} 年的数据")
        except Exception as e:
            self.logger.error(f"加载节假日缓存失败: {e}")
            self.holiday_cache = {}

    def _save_cache(self):
        """保存缓存到本地文件"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.holiday_cache, f, ensure_ascii=False, indent=2)
            self.logger.debug("节假日缓存已保存")
        except Exception as e:
            self.logger.error(f"保存节假日缓存失败: {e}")

    def _fetch_year_holidays(self, year: int) -> Optional[Dict]:
        """
        从API获取指定年份的节假日数据

        Args:
            year: 年份

        Returns:
            节假日数据字典，失败返回None
        """
        url = f"{self.API_BASE_URL}/year/{year}"

        # 添加User-Agent避免403错误
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        try:
            self.logger.info(f"正在从API获取 {year} 年节假日数据...")
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            # API返回格式：{"holiday": {...}}
            if 'holiday' in data:
                self.logger.info(f"✅ 成功获取 {year} 年节假日数据")
                return data['holiday']
            else:
                self.logger.warning(f"API返回数据格式异常: {data}")
                return None

        except requests.exceptions.Timeout:
            self.logger.warning(f"获取节假日数据超时（年份：{year}）")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"获取节假日数据失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"解析节假日数据失败: {e}")
            return None

    def _ensure_year_data(self, year: int) -> bool:
        """
        确保指定年份的数据已缓存

        Args:
            year: 年份

        Returns:
            是否成功获取数据
        """
        year_key = str(year)

        # 检查缓存是否已存在
        if year_key in self.holiday_cache:
            self.logger.debug(f"{year} 年节假日数据已缓存")
            return True

        # 从API获取
        holiday_data = self._fetch_year_holidays(year)
        if holiday_data:
            self.holiday_cache[year_key] = holiday_data
            self._save_cache()
            return True

        return False

    def is_holiday(self, date: Optional[datetime] = None) -> bool:
        """
        判断指定日期是否为节假日

        Args:
            date: 日期对象，默认为今天

        Returns:
            是否为节假日
        """
        if date is None:
            date = datetime.now()

        year = date.year
        # API的key格式是 "MM-DD"，不是 "YYYY-MM-DD"
        date_key = date.strftime("%m-%d")
        full_date_str = date.strftime("%Y-%m-%d")

        # 确保年份数据已缓存
        if not self._ensure_year_data(year):
            self.logger.warning(f"无法获取 {year} 年节假日数据，默认判断为非节假日")
            return False

        # 查询缓存
        year_key = str(year)
        year_data = self.holiday_cache.get(year_key, {})

        # 在年度数据中查找日期（使用 MM-DD 格式）
        day_info = year_data.get(date_key)

        if day_info is None:
            # 日期不在节假日数据中，说明是工作日
            return False

        # 检查 holiday 字段
        # API数据格式：{"01-01": {"holiday": true, "name": "元旦", "wage": 3, "date": "2025-01-01", ...}}
        is_holiday_flag = day_info.get('holiday', False)

        if is_holiday_flag:
            holiday_name = day_info.get('name', '节假日')
            self.logger.debug(f"{full_date_str} 是节假日: {holiday_name}")

        return is_holiday_flag

    def get_holiday_info(self, date: Optional[datetime] = None) -> Optional[Dict]:
        """
        获取指定日期的节假日详细信息

        Args:
            date: 日期对象，默认为今天

        Returns:
            节假日信息字典，非节假日返回None
        """
        if date is None:
            date = datetime.now()

        year = date.year
        # API的key格式是 "MM-DD"
        date_key = date.strftime("%m-%d")

        # 确保年份数据已缓存
        if not self._ensure_year_data(year):
            return None

        # 查询缓存
        year_key = str(year)
        year_data = self.holiday_cache.get(year_key, {})
        day_info = year_data.get(date_key)

        if day_info and day_info.get('holiday', False):
            return day_info

        return None

    def prefetch_current_year(self):
        """
        预取当前年份的节假日数据（可在后台调用）
        """
        current_year = datetime.now().year
        self._ensure_year_data(current_year)

    def prefetch_next_year(self):
        """
        预取下一年的节假日数据（用于跨年准备）
        """
        next_year = datetime.now().year + 1
        self._ensure_year_data(next_year)

    def clear_cache(self):
        """清空缓存"""
        self.holiday_cache = {}
        if self.cache_file.exists():
            self.cache_file.unlink()
        self.logger.info("节假日缓存已清空")

    def get_upcoming_holidays(self, days: int = 30) -> list:
        """
        获取未来N天内的节假日列表

        Args:
            days: 查询天数

        Returns:
            节假日列表 [{'date': '2025-01-01', 'name': '元旦', ...}, ...]
        """
        today = datetime.now()
        upcoming = []

        for i in range(days):
            check_date = today + timedelta(days=i)
            holiday_info = self.get_holiday_info(check_date)

            if holiday_info:
                upcoming.append({
                    'date': check_date.strftime("%Y-%m-%d"),
                    **holiday_info
                })

        return upcoming
