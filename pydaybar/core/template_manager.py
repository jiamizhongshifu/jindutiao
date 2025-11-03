# -*- coding: utf-8 -*-
"""
PyDayBar 模板管理器
负责管理任务模板、自动应用条件等
"""

import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from .holiday_service import HolidayService


class TemplateManager:
    """任务模板管理器"""

    def __init__(self, app_dir: Path, logger: Optional[logging.Logger] = None):
        """
        初始化模板管理器

        Args:
            app_dir: 应用根目录（用于存放用户数据）
            logger: 日志记录器
        """
        self.app_dir = app_dir
        self.logger = logger or logging.getLogger(__name__)

        # 模板配置文件路径（只读资源，从打包目录读取）
        if getattr(sys, 'frozen', False):
            # 打包后：从 _MEIPASS 读取
            base_path = Path(sys._MEIPASS)
        else:
            # 开发环境：从项目根目录读取
            base_path = Path(__file__).parent.parent.parent

        self.config_file = base_path / "templates_config.json"
        self.template_base_path = base_path  # 保存资源路径，用于加载模板json文件

        # 模板数据
        self.templates: List[Dict] = []

        # 初始化节假日服务
        self.holiday_service = HolidayService(app_dir, logger)

        # 加载模板配置
        self._load_templates_config()

    def _load_templates_config(self):
        """加载模板配置文件"""
        if not self.config_file.exists():
            self.logger.warning(f"模板配置文件不存在: {self.config_file}")
            return

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.templates = config.get('templates', [])
                self.logger.info(f"成功加载 {len(self.templates)} 个模板配置")
        except Exception as e:
            self.logger.error(f"加载模板配置失败: {e}")

    def _save_templates_config(self):
        """保存模板配置文件"""
        try:
            config = {
                "version": "1.0",
                "description": "PyDayBar 任务模板配置",
                "templates": self.templates
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            self.logger.info("模板配置已保存")
            return True
        except Exception as e:
            self.logger.error(f"保存模板配置失败: {e}")
            return False

    def get_all_templates(self, include_custom: bool = True) -> List[Dict]:
        """
        获取所有模板

        Args:
            include_custom: 是否包含自定义模板，默认为True

        Returns:
            模板列表（预设模板 + 自定义模板）
        """
        all_templates = self.templates.copy()

        if include_custom:
            # 加载自定义模板
            custom_templates = self._load_custom_templates()
            all_templates.extend(custom_templates)

        return all_templates

    def get_template_by_id(self, template_id: str) -> Optional[Dict]:
        """
        根据ID获取模板（包括预设模板和自定义模板）

        Args:
            template_id: 模板ID

        Returns:
            模板信息，不存在则返回None
        """
        # 先从预设模板中查找
        for template in self.templates:
            if template.get('id') == template_id:
                return template.copy()

        # 再从自定义模板中查找
        custom_templates = self._load_custom_templates()
        for template in custom_templates:
            if template.get('id') == template_id:
                return template.copy()

        return None

    def get_template_by_filename(self, filename: str) -> Optional[Dict]:
        """根据文件名获取模板"""
        for template in self.templates:
            if template.get('filename') == filename:
                return template.copy()
        return None

    def load_template_tasks(self, template_id: str) -> Optional[List[Dict]]:
        """
        加载模板的任务数据

        Args:
            template_id: 模板ID

        Returns:
            任务列表，失败返回None
        """
        template = self.get_template_by_id(template_id)
        if not template:
            self.logger.warning(f"模板不存在: {template_id}")
            return None

        filename = template.get('filename')
        if not filename:
            self.logger.warning(f"模板文件名为空: {template_id}")
            return None

        # 判断是自定义模板还是预设模板
        is_custom = template.get('is_custom', False)

        if is_custom:
            # 自定义模板从用户数据目录读取
            template_path = self.app_dir / filename
        else:
            # 预设模板从资源目录读取（与templates_config.json同目录）
            template_path = self.template_base_path / filename

        if not template_path.exists():
            self.logger.warning(f"模板文件不存在: {template_path}")
            return None

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                tasks = json.load(f)
            self.logger.info(f"成功加载模板 {template_id} 的任务数据")
            return tasks
        except Exception as e:
            self.logger.error(f"加载模板任务失败: {e}")
            return None

    def get_date_type(self, date: Optional[datetime] = None) -> str:
        """
        获取日期类型

        Args:
            date: 日期对象，默认为今天

        Returns:
            'weekday' | 'weekend' | 'holiday'
        """
        if date is None:
            date = datetime.now()

        # 节假日优先判断（节假日优先级最高）
        if self._is_holiday(date):
            return 'holiday'

        # 获取星期几 (1=Monday, 7=Sunday)
        weekday = date.isoweekday()

        # 周末判断
        if weekday in [6, 7]:
            return 'weekend'

        return 'weekday'

    def get_matching_templates(self, date: Optional[datetime] = None) -> List[Dict]:
        """
        获取匹配当前日期条件的模板

        Args:
            date: 日期对象，默认为今天

        Returns:
            匹配的模板列表，按优先级排序
        """
        date_type = self.get_date_type(date)
        matching = []

        for template in self.templates:
            auto_apply = template.get('auto_apply', {})

            # 检查是否启用自动应用
            if not auto_apply.get('enabled', False):
                continue

            # 检查条件是否匹配
            conditions = auto_apply.get('conditions', [])
            if not conditions or date_type in conditions:
                matching.append(template)

        # 按优先级排序（优先级高的在前）
        matching.sort(key=lambda t: t.get('auto_apply', {}).get('priority', 0), reverse=True)

        self.logger.info(f"日期类型: {date_type}, 匹配到 {len(matching)} 个模板")
        return matching

    def get_best_match_template(self, date: Optional[datetime] = None) -> Optional[Dict]:
        """
        获取最佳匹配的模板（优先级最高的）

        Args:
            date: 日期对象，默认为今天

        Returns:
            最佳匹配的模板，无匹配返回None
        """
        matching = self.get_matching_templates(date)
        if matching:
            return matching[0]
        return None

    def toggle_auto_apply(self, template_id: str) -> bool:
        """
        切换模板的自动应用状态

        Args:
            template_id: 模板ID

        Returns:
            操作是否成功
        """
        for template in self.templates:
            if template.get('id') == template_id:
                auto_apply = template.setdefault('auto_apply', {})
                current_enabled = auto_apply.get('enabled', False)
                auto_apply['enabled'] = not current_enabled
                self.logger.info(f"模板 {template_id} 自动应用已{'启用' if not current_enabled else '禁用'}")
                return self._save_templates_config()

        self.logger.warning(f"模板不存在: {template_id}")
        return False

    def set_auto_apply(self, template_id: str, enabled: bool,
                      conditions: Optional[List[str]] = None,
                      priority: Optional[int] = None) -> bool:
        """
        设置模板的自动应用配置

        Args:
            template_id: 模板ID
            enabled: 是否启用自动应用
            conditions: 应用条件列表 ['weekday', 'weekend', 'holiday']
            priority: 优先级 (1-10)

        Returns:
            操作是否成功
        """
        for template in self.templates:
            if template.get('id') == template_id:
                auto_apply = template.setdefault('auto_apply', {})
                auto_apply['enabled'] = enabled

                if conditions is not None:
                    auto_apply['conditions'] = conditions

                if priority is not None:
                    auto_apply['priority'] = priority

                self.logger.info(f"模板 {template_id} 自动应用配置已更新")
                return self._save_templates_config()

        self.logger.warning(f"模板不存在: {template_id}")
        return False

    def _is_holiday(self, date: datetime) -> bool:
        """
        判断是否为节假日

        Args:
            date: 日期对象

        Returns:
            是否为节假日
        """
        return self.holiday_service.is_holiday(date)

    def _load_custom_templates(self) -> List[Dict]:
        """
        加载用户自定义模板

        Returns:
            自定义模板列表
        """
        custom_templates = []
        meta_file = self.app_dir / "custom_templates_meta.json"

        if not meta_file.exists():
            return custom_templates

        try:
            import json
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta_data = json.load(f)

            for template_meta in meta_data.get('templates', []):
                # 转换为标准模板格式
                custom_template = {
                    "id": template_meta['id'],
                    "name": template_meta['name'],
                    "filename": template_meta['filename'],
                    "description": template_meta.get('description', ''),
                    "button_color": "#2196F3",  # 自定义模板使用蓝色
                    "is_custom": True  # 标记为自定义模板
                }
                custom_templates.append(custom_template)

            self.logger.info(f"加载了 {len(custom_templates)} 个自定义模板")

        except Exception as e:
            self.logger.error(f"加载自定义模板失败: {e}")

        return custom_templates
