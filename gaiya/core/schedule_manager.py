# -*- coding: utf-8 -*-
"""
模板时间表管理器
管理每个模板的自动应用规则（按日期/星期/月份）
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set
from datetime import datetime, date, timedelta


class ScheduleManager:
    """模板时间表管理器"""

    def __init__(self, app_dir: Path, logger: Optional[logging.Logger] = None):
        """
        初始化时间表管理器

        Args:
            app_dir: 应用根目录
            logger: 日志记录器
        """
        self.app_dir = app_dir
        self.logger = logger or logging.getLogger(__name__)

        # 时间表配置文件路径
        self.schedule_file = app_dir / "template_schedules.json"

        # 时间表数据
        self.schedules: List[Dict] = []

        # 加载时间表配置
        self._load_schedules()

    def _load_schedules(self):
        """加载时间表配置文件"""
        if not self.schedule_file.exists():
            self.logger.info(f"时间表配置文件不存在，将创建新文件: {self.schedule_file}")
            self._create_default_schedules()
            return

        try:
            with open(self.schedule_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.schedules = data.get('schedules', [])
                self.logger.info(f"成功加载 {len(self.schedules)} 条时间表规则")
        except Exception as e:
            self.logger.error(f"加载时间表配置失败: {e}")
            self.schedules = []

    def _create_default_schedules(self):
        """创建默认时间表配置"""
        self.schedules = []
        self._save_schedules()

    def _save_schedules(self):
        """保存时间表配置到文件"""
        try:
            data = {
                "version": "1.0",
                "description": "PyDayBar 模板时间表配置",
                "schedules": self.schedules
            }
            with open(self.schedule_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"时间表配置已保存，共 {len(self.schedules)} 条规则")
            return True
        except Exception as e:
            self.logger.error(f"保存时间表配置失败: {e}")
            return False

    def get_all_schedules(self) -> List[Dict]:
        """获取所有时间表规则"""
        return self.schedules.copy()

    def get_schedules_for_template(self, template_id: str) -> List[Dict]:
        """
        获取指定模板的所有时间表规则

        Args:
            template_id: 模板ID

        Returns:
            该模板的所有时间表规则列表
        """
        return [s for s in self.schedules if s.get('template_id') == template_id]

    def add_schedule(self, template_id: str, schedule_type: str, **kwargs) -> bool:
        """
        添加时间表规则

        Args:
            template_id: 模板ID
            schedule_type: 规则类型 ('weekdays' | 'specific_dates' | 'monthly')
            **kwargs: 其他参数
                - weekdays: List[int] - 星期列表 (1=Monday, 7=Sunday)
                - dates: List[str] - 具体日期列表 (格式: YYYY-MM-DD)
                - days_of_month: List[int] - 每月的日期列表 (1-31)

        Returns:
            是否成功添加
        """
        try:
            # 检查冲突
            conflicts = self._check_conflicts(template_id, schedule_type, **kwargs)
            if conflicts:
                conflict_info = ', '.join([f"{c['template_id']} ({c['description']})" for c in conflicts])
                self.logger.warning(f"时间表规则冲突: {conflict_info}")
                return False

            new_schedule = {
                "template_id": template_id,
                "schedule_type": schedule_type,
                "enabled": True
            }

            # 根据类型添加相应的参数
            if schedule_type == 'weekdays':
                new_schedule['weekdays'] = kwargs.get('weekdays', [])
            elif schedule_type == 'specific_dates':
                new_schedule['dates'] = kwargs.get('dates', [])
            elif schedule_type == 'monthly':
                new_schedule['days_of_month'] = kwargs.get('days_of_month', [])
            else:
                self.logger.error(f"不支持的时间表类型: {schedule_type}")
                return False

            self.schedules.append(new_schedule)
            return self._save_schedules()

        except Exception as e:
            self.logger.error(f"添加时间表规则失败: {e}")
            return False

    def remove_schedule(self, index: int) -> bool:
        """
        删除时间表规则

        Args:
            index: 规则索引

        Returns:
            是否成功删除
        """
        try:
            if 0 <= index < len(self.schedules):
                removed = self.schedules.pop(index)
                self.logger.info(f"已删除时间表规则: {removed}")
                return self._save_schedules()
            else:
                self.logger.warning(f"无效的索引: {index}")
                return False
        except Exception as e:
            self.logger.error(f"删除时间表规则失败: {e}")
            return False

    def update_schedule(self, index: int, **kwargs) -> bool:
        """
        更新时间表规则

        Args:
            index: 规则索引
            **kwargs: 要更新的字段

        Returns:
            是否成功更新
        """
        try:
            if 0 <= index < len(self.schedules):
                self.schedules[index].update(kwargs)
                return self._save_schedules()
            else:
                self.logger.warning(f"无效的索引: {index}")
                return False
        except Exception as e:
            self.logger.error(f"更新时间表规则失败: {e}")
            return False

    def toggle_schedule(self, index: int) -> bool:
        """
        切换时间表规则的启用状态

        Args:
            index: 规则索引

        Returns:
            是否成功切换
        """
        try:
            if 0 <= index < len(self.schedules):
                current = self.schedules[index].get('enabled', True)
                self.schedules[index]['enabled'] = not current
                return self._save_schedules()
            else:
                self.logger.warning(f"无效的索引: {index}")
                return False
        except Exception as e:
            self.logger.error(f"切换时间表规则状态失败: {e}")
            return False

    def get_template_for_date(self, target_date: Optional[date] = None) -> Optional[str]:
        """
        获取指定日期应该应用的模板ID

        Args:
            target_date: 目标日期，默认为今天

        Returns:
            模板ID，如果没有匹配的规则则返回None
        """
        if target_date is None:
            target_date = date.today()

        # 只返回启用的规则
        enabled_schedules = [s for s in self.schedules if s.get('enabled', True)]

        # 优先级：specific_dates > monthly > weekdays
        # 1. 检查具体日期
        for schedule in enabled_schedules:
            if schedule['schedule_type'] == 'specific_dates':
                date_str = target_date.strftime('%Y-%m-%d')
                if date_str in schedule.get('dates', []):
                    self.logger.info(f"日期 {date_str} 匹配到具体日期规则: {schedule['template_id']}")
                    return schedule['template_id']

        # 2. 检查每月日期
        for schedule in enabled_schedules:
            if schedule['schedule_type'] == 'monthly':
                if target_date.day in schedule.get('days_of_month', []):
                    self.logger.info(f"日期 {target_date} 匹配到每月规则: {schedule['template_id']}")
                    return schedule['template_id']

        # 3. 检查星期
        for schedule in enabled_schedules:
            if schedule['schedule_type'] == 'weekdays':
                # isoweekday(): 1=Monday, 7=Sunday
                weekday = target_date.isoweekday()
                if weekday in schedule.get('weekdays', []):
                    self.logger.info(f"日期 {target_date} (星期{weekday}) 匹配到星期规则: {schedule['template_id']}")
                    return schedule['template_id']

        self.logger.debug(f"日期 {target_date} 没有匹配到任何时间表规则")
        return None

    def _check_conflicts(self, template_id: str, schedule_type: str, **kwargs) -> List[Dict]:
        """
        检查新规则是否与现有规则冲突

        Args:
            template_id: 新规则的模板ID
            schedule_type: 新规则的类型
            **kwargs: 新规则的参数

        Returns:
            冲突的规则列表（包含template_id和描述）
        """
        conflicts = []

        # 生成新规则会覆盖的日期集合
        new_rule_dates = self._get_rule_dates(schedule_type, **kwargs)

        # 检查与现有规则的冲突
        for schedule in self.schedules:
            # 跳过同一个模板的规则（允许同一模板有多条规则）
            if schedule['template_id'] == template_id:
                continue

            # 跳过未启用的规则
            if not schedule.get('enabled', True):
                continue

            # 获取现有规则的日期集合
            existing_dates = self._get_rule_dates(
                schedule['schedule_type'],
                weekdays=schedule.get('weekdays'),
                dates=schedule.get('dates'),
                days_of_month=schedule.get('days_of_month')
            )

            # 检查是否有交集
            if new_rule_dates & existing_dates:
                conflicts.append({
                    'template_id': schedule['template_id'],
                    'description': self._describe_schedule(schedule)
                })

        return conflicts

    def _get_rule_dates(self, schedule_type: str, **kwargs) -> Set[str]:
        """
        获取规则覆盖的日期集合（用于冲突检测）

        Args:
            schedule_type: 规则类型
            **kwargs: 规则参数

        Returns:
            日期标识集合（例如: {'MON', 'TUE', '2025-01-01', 'DAY-1', 'DAY-15'}）
        """
        dates = set()

        if schedule_type == 'weekdays':
            weekdays = kwargs.get('weekdays', [])
            # 使用 'MON', 'TUE' 等标识星期
            weekday_names = {1: 'MON', 2: 'TUE', 3: 'WED', 4: 'THU', 5: 'FRI', 6: 'SAT', 7: 'SUN'}
            for wd in weekdays:
                dates.add(weekday_names.get(wd, f'WD-{wd}'))

        elif schedule_type == 'specific_dates':
            # 直接使用日期字符串
            dates.update(kwargs.get('dates', []))

        elif schedule_type == 'monthly':
            days_of_month = kwargs.get('days_of_month', [])
            # 使用 'DAY-1', 'DAY-15' 等标识每月的日期
            for day in days_of_month:
                dates.add(f'DAY-{day}')

        return dates

    def _is_continuous_dates(self, sorted_dates: list) -> bool:
        """
        判断日期列表是否为连续日期

        Args:
            sorted_dates: 已排序的日期字符串列表 (格式: YYYY-MM-DD)

        Returns:
            是否为连续日期
        """
        if len(sorted_dates) < 3:
            return False

        try:
            # 将日期字符串转换为datetime对象
            date_objects = [datetime.strptime(d, '%Y-%m-%d') for d in sorted_dates]

            # 检查是否每两个相邻日期相差1天
            for i in range(len(date_objects) - 1):
                if date_objects[i + 1] - date_objects[i] != timedelta(days=1):
                    return False

            return True
        except Exception:
            return False

    def _describe_schedule(self, schedule: Dict) -> str:
        """
        生成时间表规则的可读描述

        Args:
            schedule: 时间表规则

        Returns:
            可读的描述字符串
        """
        schedule_type = schedule.get('schedule_type', '')

        if schedule_type == 'weekdays':
            weekdays = schedule.get('weekdays', [])
            weekday_names = {1: '周一', 2: '周二', 3: '周三', 4: '周四', 5: '周五', 6: '周六', 7: '周日'}
            names = [weekday_names.get(wd, f'星期{wd}') for wd in sorted(weekdays)]
            return ', '.join(names)

        elif schedule_type == 'specific_dates':
            dates = schedule.get('dates', [])
            # 对日期进行排序
            sorted_dates = sorted(dates)

            if len(sorted_dates) == 0:
                return "无日期"
            elif len(sorted_dates) == 1:
                # 单个日期，直接显示
                return sorted_dates[0]
            elif len(sorted_dates) == 2:
                # 两个日期，直接显示
                return f"{sorted_dates[0]}, {sorted_dates[1]}"
            elif self._is_continuous_dates(sorted_dates):
                # 连续日期范围，显示开始和结束
                return f"{sorted_dates[0]} 至 {sorted_dates[-1]} (共{len(sorted_dates)}天)"
            elif len(sorted_dates) <= 5:
                # 5个及以内，全部显示
                return ', '.join(sorted_dates)
            else:
                # 超过5个，显示首尾日期和总数
                return f"{sorted_dates[0]} ... {sorted_dates[-1]} (共{len(sorted_dates)}个)"

        elif schedule_type == 'monthly':
            days = schedule.get('days_of_month', [])
            return f"每月 {', '.join(map(str, sorted(days)))} 号"

        return "未知规则"

    def get_conflicts_for_date(self, target_date: Optional[date] = None) -> List[str]:
        """
        获取指定日期的所有冲突模板ID

        Args:
            target_date: 目标日期，默认为今天

        Returns:
            在该日期生效的所有模板ID列表
        """
        if target_date is None:
            target_date = date.today()

        matched_templates = []

        for schedule in self.schedules:
            if not schedule.get('enabled', True):
                continue

            schedule_type = schedule['schedule_type']

            # 检查具体日期
            if schedule_type == 'specific_dates':
                date_str = target_date.strftime('%Y-%m-%d')
                if date_str in schedule.get('dates', []):
                    matched_templates.append(schedule['template_id'])
                    continue

            # 检查每月日期
            if schedule_type == 'monthly':
                if target_date.day in schedule.get('days_of_month', []):
                    matched_templates.append(schedule['template_id'])
                    continue

            # 检查星期
            if schedule_type == 'weekdays':
                weekday = target_date.isoweekday()
                if weekday in schedule.get('weekdays', []):
                    matched_templates.append(schedule['template_id'])

        return matched_templates
