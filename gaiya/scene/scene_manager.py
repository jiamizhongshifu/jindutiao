"""
场景管理器 - SceneManager

负责管理场景列表、切换、配置持久化等功能
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

from .loader import SceneLoader
from .models import SceneConfig


class SceneManager:
    """场景管理器 - 管理场景列表、切换和配置持久化

    职责:
    - 扫描scenes/目录获取所有可用场景
    - 场景元数据管理（名称、描述、版本）
    - 场景加载和卸载
    - 场景配置持久化（当前选择、启用状态）
    """

    def __init__(self, scenes_dir: Optional[str] = None):
        """初始化场景管理器

        Args:
            scenes_dir: 场景目录路径，默认为 'scenes/'
        """
        self.logger = logging.getLogger(__name__)

        # 场景加载器
        self.scene_loader = SceneLoader(scenes_dir)

        # 场景目录（直接使用SceneLoader确定的目录，确保一致性）
        self.scenes_dir = self.scene_loader.scenes_dir

        # 可用场景字典 {scene_name: scene_metadata}
        self.available_scenes: Dict[str, dict] = {}

        # 当前加载的场景
        self.current_scene_name: Optional[str] = None
        self.current_scene_config: Optional[SceneConfig] = None

        # 场景系统启用状态
        self.scene_enabled: bool = False

        # 初始化时扫描所有场景
        self.scan_scenes()

        self.logger.info(f"SceneManager initialized, found {len(self.available_scenes)} scenes")

    def scan_scenes(self) -> Dict[str, dict]:
        """扫描scenes/目录，获取所有可用场景

        Returns:
            场景字典 {scene_name: scene_metadata}
        """
        self.available_scenes.clear()

        if not self.scenes_dir.exists():
            self.logger.warning(f"Scenes directory not found: {self.scenes_dir}")
            return self.available_scenes

        # 遍历scenes/目录下的所有子目录
        for scene_dir in self.scenes_dir.iterdir():
            if not scene_dir.is_dir():
                continue

            # 检查是否存在config.json
            config_file = scene_dir / "config.json"
            if not config_file.exists():
                self.logger.debug(f"Skipping {scene_dir.name}: no config.json")
                continue

            # 读取场景元数据
            try:
                scene_config = self.scene_loader.load_scene(scene_dir.name)
                if scene_config:
                    metadata = {
                        'name': scene_config.name,
                        'description': scene_config.description,
                        'version': scene_config.version,
                        'author': scene_config.author,
                        'directory': str(scene_dir),
                    }
                    self.available_scenes[scene_dir.name] = metadata
                    self.logger.debug(f"Found scene: {scene_dir.name} - {metadata['name']}")
            except Exception as e:
                self.logger.error(f"Failed to load scene {scene_dir.name}: {e}", exc_info=True)

        self.logger.info(f"Scanned {len(self.available_scenes)} scenes from {self.scenes_dir}")
        return self.available_scenes

    def get_scene_list(self) -> List[str]:
        """获取场景名称列表（按字母顺序排序）

        Returns:
            场景名称列表
        """
        return sorted(self.available_scenes.keys())

    def get_scene_metadata(self, scene_name: str) -> Optional[dict]:
        """获取场景元数据

        Args:
            scene_name: 场景名称（目录名）

        Returns:
            场景元数据字典，如果场景不存在则返回None
        """
        return self.available_scenes.get(scene_name)

    def load_scene(self, scene_name: str) -> Optional[SceneConfig]:
        """加载指定场景

        Args:
            scene_name: 场景名称（目录名）

        Returns:
            场景配置对象，加载失败返回None
        """
        if scene_name not in self.available_scenes:
            self.logger.error(f"Scene not found: {scene_name}")
            return None

        try:
            # 使用SceneLoader加载场景
            scene_config = self.scene_loader.load_scene(scene_name)
            if scene_config:
                self.current_scene_name = scene_name
                self.current_scene_config = scene_config
                self.logger.info(f"Loaded scene: {scene_name}")
                return scene_config
            else:
                self.logger.error(f"Failed to load scene: {scene_name}")
                return None
        except Exception as e:
            self.logger.error(f"Exception while loading scene {scene_name}: {e}", exc_info=True)
            return None

    def unload_scene(self):
        """卸载当前场景"""
        if self.current_scene_name:
            self.logger.info(f"Unloading scene: {self.current_scene_name}")
            self.current_scene_name = None
            self.current_scene_config = None

    def set_enabled(self, enabled: bool):
        """启用/禁用场景系统

        Args:
            enabled: True表示启用，False表示禁用
        """
        self.scene_enabled = enabled
        self.logger.info(f"Scene system {'enabled' if enabled else 'disabled'}")

    def is_enabled(self) -> bool:
        """检查场景系统是否启用

        Returns:
            True表示启用，False表示禁用
        """
        return self.scene_enabled

    def get_current_scene_name(self) -> Optional[str]:
        """获取当前场景名称

        Returns:
            当前场景名称，如果没有加载场景则返回None
        """
        return self.current_scene_name

    def get_current_scene_config(self) -> Optional[SceneConfig]:
        """获取当前场景配置

        Returns:
            当前场景配置对象，如果没有加载场景则返回None
        """
        return self.current_scene_config

    def save_config(self, config_dict: dict) -> dict:
        """保存场景配置到配置字典

        这个方法将场景相关配置添加到主配置字典中，
        由主程序负责实际写入config.json文件

        Args:
            config_dict: 主配置字典

        Returns:
            更新后的配置字典
        """
        config_dict['scene'] = {
            'enabled': self.scene_enabled,
            'current_scene': self.current_scene_name,
        }
        self.logger.debug(f"Saved scene config: enabled={self.scene_enabled}, current={self.current_scene_name}")
        return config_dict

    def load_config(self, config_dict: dict):
        """从配置字典加载场景配置

        Args:
            config_dict: 主配置字典
        """
        scene_config = config_dict.get('scene', {})

        # 加载启用状态
        self.scene_enabled = scene_config.get('enabled', False)

        # 加载当前场景
        current_scene_name = scene_config.get('current_scene')
        if current_scene_name and current_scene_name in self.available_scenes:
            self.load_scene(current_scene_name)

        self.logger.info(
            f"Loaded scene config: enabled={self.scene_enabled}, "
            f"current={self.current_scene_name}"
        )
