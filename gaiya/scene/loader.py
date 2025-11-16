"""
场景加载器 - SceneLoader

负责加载和验证场景配置，处理资源路径，支持PyInstaller打包环境
"""

import json
import os
import sys
import logging
from pathlib import Path
from typing import Optional, List, Dict
from PySide6.QtGui import QPixmap

from .models import SceneConfig


class ResourceCache:
    """资源缓存 - 缓存已加载的QPixmap对象"""

    def __init__(self):
        self._cache: Dict[str, QPixmap] = {}
        self.logger = logging.getLogger(__name__)

    def get(self, path: str) -> Optional[QPixmap]:
        """获取缓存的QPixmap"""
        return self._cache.get(path)

    def put(self, path: str, pixmap: QPixmap):
        """缓存QPixmap"""
        if not pixmap.isNull():
            self._cache[path] = pixmap
            self.logger.debug(f"Cached pixmap: {path} ({pixmap.width()}x{pixmap.height()})")

    def preload(self, paths: List[str]) -> int:
        """预加载多个图片资源

        Args:
            paths: 图片文件路径列表

        Returns:
            成功加载的图片数量
        """
        success_count = 0
        for path in paths:
            if path not in self._cache:
                pixmap = QPixmap(path)
                if not pixmap.isNull():
                    self.put(path, pixmap)
                    success_count += 1
                else:
                    self.logger.warning(f"Failed to load image: {path}")

        return success_count

    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self.logger.info("Resource cache cleared")

    def size(self) -> int:
        """获取缓存中的资源数量"""
        return len(self._cache)


class SceneLoader:
    """场景配置加载器

    支持从JSON文件加载场景配置，处理资源路径（开发环境和打包环境）
    """

    def __init__(self, scenes_dir: Optional[str] = None):
        """初始化场景加载器

        Args:
            scenes_dir: 场景目录路径，默认为 scenes/
        """
        self.logger = logging.getLogger(__name__)
        self.resource_cache = ResourceCache()

        # 确定场景目录
        if scenes_dir:
            self.scenes_dir = Path(scenes_dir)
        else:
            self.scenes_dir = self._get_default_scenes_dir()

        self.logger.info(f"SceneLoader initialized with scenes_dir: {self.scenes_dir}")

    def _get_default_scenes_dir(self) -> Path:
        """获取默认的场景目录

        处理两种环境：
        1. 开发环境：项目根目录下的 scenes/
        2. 打包环境：exe所在目录下的 scenes/ (与exe同级)
        """
        if getattr(sys, 'frozen', False):
            # PyInstaller 打包环境
            # sys.executable 是 exe 文件的完整路径
            # 场景目录应该在 exe 所在目录下（而不是临时解压目录）
            base_dir = Path(sys.executable).parent
            self.logger.info(f"Running in packaged mode, exe_dir: {base_dir}")
        else:
            # 开发环境
            # __file__ 是当前文件路径（gaiya/scene/loader.py）
            # 项目根目录是 __file__ 的上上上级
            base_dir = Path(__file__).parent.parent.parent
            self.logger.info(f"Running in development mode, base_dir: {base_dir}")

        scenes_dir = base_dir / "scenes"

        # 确保目录存在
        if not scenes_dir.exists():
            self.logger.warning(f"Scenes directory not found: {scenes_dir}")
            # 在开发环境中创建目录，在打包环境中也创建（用户可能删除了）
            scenes_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created scenes directory: {scenes_dir}")

        return scenes_dir

    def get_available_scenes(self) -> List[str]:
        """获取所有可用的场景列表

        扫描 scenes/ 目录，返回包含 config.json 的子目录名称

        Returns:
            场景名称列表，例如：['default', 'pixel_forest', 'cyberpunk_city']
        """
        if not self.scenes_dir.exists():
            self.logger.warning(f"Scenes directory does not exist: {self.scenes_dir}")
            return []

        scenes = []
        for item in self.scenes_dir.iterdir():
            if item.is_dir():
                config_file = item / "config.json"
                if config_file.exists():
                    scenes.append(item.name)

        self.logger.info(f"Found {len(scenes)} available scenes: {scenes}")
        return scenes

    def load_scene(self, scene_name: str) -> Optional[SceneConfig]:
        """加载场景配置

        Args:
            scene_name: 场景名称（子目录名），例如 'default'

        Returns:
            SceneConfig 对象，如果加载失败则返回 None
        """
        scene_dir = self.scenes_dir / scene_name
        config_file = scene_dir / "config.json"

        if not config_file.exists():
            self.logger.error(f"Scene config not found: {config_file}")
            return None

        try:
            # 读取JSON文件
            with open(config_file, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)

            # 验证配置
            if not self.validate_config(config_dict):
                self.logger.error(f"Scene config validation failed: {scene_name}")
                return None

            # 解析为 SceneConfig 对象
            scene_config = SceneConfig.from_dict(config_dict)

            # 解析资源路径（相对路径 → 绝对路径）
            self._resolve_resource_paths(scene_config, scene_dir)

            self.logger.info(f"Successfully loaded scene: {scene_name}")
            return scene_config

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON: {config_file}, error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to load scene: {scene_name}, error: {e}")
            return None

    def validate_config(self, config: dict) -> bool:
        """验证场景配置的有效性

        Args:
            config: 配置字典

        Returns:
            配置是否有效
        """
        # 检查必需字段
        required_fields = ['scene_id', 'name', 'version', 'canvas', 'layers']
        for field in required_fields:
            if field not in config:
                self.logger.error(f"Missing required field: {field}")
                return False

        # 检查 canvas 字段
        canvas = config.get('canvas', {})
        if 'width' not in canvas or 'height' not in canvas:
            self.logger.error("Canvas missing width or height")
            return False

        # 检查 layers 字段
        layers = config.get('layers', {})
        if 'scene' not in layers:
            self.logger.error("Missing scene layer")
            return False

        self.logger.debug(f"Config validation passed for scene: {config.get('scene_id')}")
        return True

    def _resolve_resource_paths(self, scene_config: SceneConfig, scene_dir: Path):
        """解析资源路径（相对路径转换为绝对路径）

        Args:
            scene_config: 场景配置对象
            scene_dir: 场景目录路径
        """
        # 解析道路层图片路径
        if scene_config.road_layer:
            road_image = scene_config.road_layer.image
            if not os.path.isabs(road_image):
                # 相对路径 → 绝对路径
                abs_path = scene_dir / road_image
                scene_config.road_layer.image = str(abs_path.resolve())
                self.logger.debug(f"Resolved road image path: {scene_config.road_layer.image}")

        # 解析场景元素图片路径
        for item in scene_config.scene_layer.items:
            if not os.path.isabs(item.image):
                # 图片路径可能已经包含 assets/ 前缀（新版场景编辑器导出格式）
                # 也可能不包含（旧版格式）
                # 直接使用相对于 scene_dir 的路径
                abs_path = scene_dir / item.image
                item.image = str(abs_path.resolve())
                self.logger.debug(f"Resolved item image path: {item.image}")

    def preload_scene_resources(self, scene_config: SceneConfig) -> int:
        """预加载场景的所有图片资源到缓存

        Args:
            scene_config: 场景配置对象

        Returns:
            成功加载的资源数量
        """
        paths = []

        # 收集道路层图片
        if scene_config.road_layer:
            paths.append(scene_config.road_layer.image)

        # 收集场景元素图片
        for item in scene_config.scene_layer.items:
            paths.append(item.image)

        # 预加载
        success_count = self.resource_cache.preload(paths)

        self.logger.info(f"Preloaded {success_count}/{len(paths)} resources for scene: {scene_config.name}")
        return success_count

    def get_cached_pixmap(self, path: str) -> Optional[QPixmap]:
        """获取缓存的QPixmap

        Args:
            path: 图片文件路径

        Returns:
            QPixmap 对象，如果未缓存则返回 None
        """
        return self.resource_cache.get(path)
