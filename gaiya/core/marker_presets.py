# -*- coding: utf-8 -*-
"""
GaiYa Marker Presets Manager
Manage built-in and custom marker image presets
"""
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


# Built-in marker presets configuration
MARKER_PRESETS = {
    "kun": {
        "id": "kun",
        "name": "坤坤打篮球",
        "file": "kun.webp",
        "default_size": 80,
        "default_x_offset": 0,
        "default_y_offset": 0,
        "description": "经典坤坤打篮球动画"
    },
    "gaiya": {
        "id": "gaiya",
        "name": "GaiYa 走路",
        "file": "gaiya.gif",
        "default_size": 60,
        "default_x_offset": 0,
        "default_y_offset": 0,
        "description": "GaiYa 吉祥物走路动画"
    },
    "custom": {
        "id": "custom",
        "name": "自定义图片",
        "file": "",  # Will be set by user
        "default_size": 50,
        "default_x_offset": 0,
        "default_y_offset": 0,
        "description": "上传您自己的标记图片"
    }
}


class MarkerPresetManager:
    """Marker preset manager - handles preset switching and parameter management"""

    def __init__(self):
        """Initialize preset manager"""
        self._presets = MARKER_PRESETS.copy()
        self._current_preset_id = "kun"  # Default preset
        self._preset_params = {}  # Store user-customized parameters

    @staticmethod
    def get_marker_path(filename: str) -> str:
        """
        Get marker image absolute path (supports both dev and packaged environments)

        Args:
            filename: Marker image filename

        Returns:
            Absolute path to marker image
        """
        if not filename:
            return ""

        # Check if running in PyInstaller bundle
        if getattr(sys, 'frozen', False):
            # PyInstaller mode: use _MEIPASS
            base_path = Path(sys._MEIPASS)
        else:
            # Development mode: use project root
            base_path = Path(__file__).parent.parent.parent

        marker_path = base_path / 'assets' / 'markers' / filename

        # Verify file exists
        if not marker_path.exists():
            logger.warning(f"Marker image not found: {marker_path}")
            return ""

        return str(marker_path)

    def get_preset(self, preset_id: str) -> Optional[Dict]:
        """
        Get preset information by ID

        Args:
            preset_id: Preset ID (kun/gaiya/custom)

        Returns:
            Preset info dict or None if not found
        """
        return self._presets.get(preset_id)

    def get_all_presets(self) -> List[Dict]:
        """
        Get all available presets

        Returns:
            List of preset info dicts
        """
        return list(self._presets.values())

    def get_current_preset_id(self) -> str:
        """Get current active preset ID"""
        return self._current_preset_id

    def set_current_preset_id(self, preset_id: str) -> bool:
        """
        Set current active preset

        Args:
            preset_id: Preset ID to activate

        Returns:
            True if successful, False if preset not found
        """
        if preset_id not in self._presets:
            logger.error(f"Invalid preset ID: {preset_id}")
            return False

        self._current_preset_id = preset_id
        logger.info(f"Switched to preset: {preset_id}")
        return True

    def get_preset_params(self, preset_id: str) -> Dict:
        """
        Get parameters for a preset (user-customized or default)

        Args:
            preset_id: Preset ID

        Returns:
            Parameters dict with size, x_offset, y_offset
        """
        preset = self.get_preset(preset_id)
        if not preset:
            return {"size": 50, "x_offset": 0, "y_offset": 0}

        # Return user-customized params if available, otherwise defaults
        if preset_id in self._preset_params:
            return self._preset_params[preset_id].copy()

        return {
            "size": preset["default_size"],
            "x_offset": preset["default_x_offset"],
            "y_offset": preset["default_y_offset"]
        }

    def save_preset_params(self, preset_id: str, params: Dict) -> bool:
        """
        Save user-customized parameters for a preset

        Args:
            preset_id: Preset ID
            params: Parameters dict with size, x_offset, y_offset

        Returns:
            True if successful
        """
        if preset_id not in self._presets:
            logger.error(f"Invalid preset ID: {preset_id}")
            return False

        # Validate and normalize parameters
        validated_params = {
            "size": max(10, min(200, params.get("size", 50))),
            "x_offset": max(-100, min(100, params.get("x_offset", 0))),
            "y_offset": max(-100, min(100, params.get("y_offset", 0)))
        }

        self._preset_params[preset_id] = validated_params
        logger.info(f"Saved params for preset {preset_id}: {validated_params}")
        return True

    def reset_to_default(self, preset_id: str) -> Dict:
        """
        Reset preset parameters to defaults

        Args:
            preset_id: Preset ID

        Returns:
            Default parameters dict
        """
        preset = self.get_preset(preset_id)
        if not preset:
            return {"size": 50, "x_offset": 0, "y_offset": 0}

        # Remove user-customized params
        if preset_id in self._preset_params:
            del self._preset_params[preset_id]

        default_params = {
            "size": preset["default_size"],
            "x_offset": preset["default_x_offset"],
            "y_offset": preset["default_y_offset"]
        }

        logger.info(f"Reset preset {preset_id} to defaults: {default_params}")
        return default_params

    def set_custom_image_path(self, file_path: str) -> bool:
        """
        Set custom marker image file path

        Args:
            file_path: Absolute path to custom image

        Returns:
            True if file exists and is valid
        """
        if not file_path or not os.path.exists(file_path):
            logger.error(f"Custom image file not found: {file_path}")
            return False

        # Update custom preset file path
        self._presets["custom"]["file"] = file_path
        logger.info(f"Set custom marker image: {file_path}")
        return True

    def get_current_marker_path(self) -> str:
        """
        Get current active marker image path

        Returns:
            Absolute path to current marker image
        """
        preset = self.get_preset(self._current_preset_id)
        if not preset:
            return ""

        filename = preset["file"]

        # For custom preset, file is already absolute path
        if self._current_preset_id == "custom":
            return filename if os.path.exists(filename) else ""

        # For built-in presets, use get_marker_path
        return self.get_marker_path(filename)

    def load_from_config(self, config: Dict):
        """
        Load preset settings from config dict

        Args:
            config: Config dict from config.json
        """
        # 迁移旧配置:如果没有marker_preset_id,根据marker_image_path自动识别预设
        if "marker_preset_id" not in config:
            old_path = config.get("marker_image_path", "")

            if old_path:
                # 尝试匹配内置预设
                if "kun.webp" in old_path or "kun.gif" in old_path:
                    self.set_current_preset_id("kun")
                    logger.info(f"Migrated old config to 'kun' preset (from path: {old_path})")
                elif "gaiya.gif" in old_path:
                    self.set_current_preset_id("gaiya")
                    logger.info(f"Migrated old config to 'gaiya' preset (from path: {old_path})")
                else:
                    # 自定义图片
                    self.set_current_preset_id("custom")
                    self.set_custom_image_path(old_path)
                    logger.info(f"Migrated old config to 'custom' preset (from path: {old_path})")
            else:
                # 默认使用kun预设
                self.set_current_preset_id("kun")
                logger.info("No marker config found, initialized with 'kun' preset")

            # 迁移旧的参数到当前预设
            if "marker_size" in config or "marker_x_offset" in config or "marker_y_offset" in config:
                old_params = {
                    "size": config.get("marker_size", 80),
                    "x_offset": config.get("marker_x_offset", 0),
                    "y_offset": config.get("marker_y_offset", 0)
                }
                self.save_preset_params(self._current_preset_id, old_params)
                logger.info(f"Migrated old params to preset '{self._current_preset_id}': {old_params}")
        else:
            # 新配置格式:直接加载preset_id
            self.set_current_preset_id(config["marker_preset_id"])

        # Load custom parameters for each preset
        if "marker_presets_params" in config:
            for preset_id, params in config["marker_presets_params"].items():
                if preset_id in self._presets:
                    self.save_preset_params(preset_id, params)

        logger.info(f"Loaded preset config: current={self._current_preset_id}")

    def save_to_config(self) -> Dict:
        """
        Export preset settings to config dict

        Returns:
            Config dict to merge into config.json
        """
        return {
            "marker_preset_id": self._current_preset_id,
            "marker_presets_params": self._preset_params.copy()
        }
