# -*- coding: utf-8 -*-
"""
PyDayBar 主题管理器
管理主题切换、配置持久化和UI组件注册
"""

import json
import logging
import platform
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from PySide6.QtCore import QObject, Signal

from i18n.translator import tr


class ThemeManager(QObject):
    """
    主题管理器 (单例模式)
    管理主题切换、配置持久化和UI组件注册
    """
    
    # 单例实例
    _instance = None
    
    # 主题变更信号
    theme_changed = Signal()  # 主题变更时发出信号
    
    # 内置预设主题
    DEFAULT_PRESET_THEMES = {
        "business": {
            "id": "business",
            "name": "商务专业",
            "type": "preset",
            "background_color": "#1E1E1E",
            "background_opacity": 220,
            "task_colors": ["#1976D2", "#388E3C", "#F57C00", "#7B1FA2"],
            "marker_color": "#FF5252",
            "text_color": "#FFFFFF",
            "accent_color": "#2196F3",
            "description": "深色背景，蓝色系工作，适合商务场景"
        },
        "fresh": {
            "id": "fresh",
            "name": "清新自然",
            "type": "preset",
            "background_color": "#F5F5F5",
            "background_opacity": 240,
            "task_colors": ["#66BB6A", "#FFD54F", "#FF7043", "#7E57C2"],
            "marker_color": "#FF5252",
            "text_color": "#424242",
            "accent_color": "#66BB6A",
            "description": "浅色背景，自然色系，清新舒适"
        },
        "warm": {
            "id": "warm",
            "name": "温暖橙色",
            "type": "preset",
            "background_color": "#FFF8E1",
            "background_opacity": 250,
            "task_colors": ["#FF9800", "#FF6F00", "#FFB300", "#FFC107"],
            "marker_color": "#D32F2F",
            "text_color": "#5D4037",
            "accent_color": "#FF9800",
            "description": "暖色调，温馨舒适，适合日常使用"
        },
        "minimal": {
            "id": "minimal",
            "name": "极简黑白",
            "type": "preset",
            "background_color": "#FFFFFF",
            "background_opacity": 255,
            "task_colors": ["#000000", "#424242", "#757575", "#9E9E9E"],
            "marker_color": "#F44336",
            "text_color": "#212121",
            "accent_color": "#000000",
            "description": "极简风格，黑白灰配色，专注高效"
        },
        "tech": {
            "id": "tech",
            "name": "科技蓝",
            "type": "preset",
            "background_color": "#0D1117",
            "background_opacity": 230,
            "task_colors": ["#58A6FF", "#79C0FF", "#7C3AED", "#A855F7"],
            "marker_color": "#FF6B6B",
            "text_color": "#C9D1D9",
            "accent_color": "#58A6FF",
            "description": "深色背景，蓝色系，科技感十足"
        },
        "ocean": {
            "id": "ocean",
            "name": "海洋蓝",
            "type": "preset",
            "background_color": "#E3F2FD",
            "background_opacity": 250,
            "task_colors": ["#2196F3", "#03A9F4", "#00BCD4", "#0097A7"],
            "marker_color": "#F44336",
            "text_color": "#1565C0",
            "accent_color": "#2196F3",
            "description": "浅蓝色调，清新宁静，适合专注工作"
        },
        "forest": {
            "id": "forest",
            "name": "森林绿",
            "type": "preset",
            "background_color": "#E8F5E9",
            "background_opacity": 250,
            "task_colors": ["#4CAF50", "#66BB6A", "#8BC34A", "#9CCC65"],
            "marker_color": "#FF5722",
            "text_color": "#2E7D32",
            "accent_color": "#4CAF50",
            "description": "绿色系，自然清新，适合学习和工作"
        },
        "sunset": {
            "id": "sunset",
            "name": "日落橙",
            "type": "preset",
            "background_color": "#FFF3E0",
            "background_opacity": 250,
            "task_colors": ["#FF9800", "#FF6F00", "#E65100", "#FFB300"],
            "marker_color": "#E91E63",
            "text_color": "#E65100",
            "accent_color": "#FF9800",
            "description": "橙色系，温暖活力，适合创意工作"
        },
        "lavender": {
            "id": "lavender",
            "name": "薰衣草紫",
            "type": "preset",
            "background_color": "#F3E5F5",
            "background_opacity": 250,
            "task_colors": ["#9C27B0", "#BA68C8", "#CE93D8", "#E1BEE7"],
            "marker_color": "#FF4081",
            "text_color": "#6A1B9A",
            "accent_color": "#9C27B0",
            "description": "紫色系，优雅舒适，适合思考和学习"
        },
        "dark": {
            "id": "dark",
            "name": "深色模式",
            "type": "preset",
            "background_color": "#121212",
            "background_opacity": 240,
            "task_colors": ["#BB86FC", "#03DAC6", "#CF6679", "#6200EE"],
            "marker_color": "#FF1744",
            "text_color": "#FFFFFF",
            "accent_color": "#BB86FC",
            "description": "深色背景，Material Design深色主题，护眼舒适"
        },
        "light": {
            "id": "light",
            "name": "浅色模式",
            "type": "preset",
            "background_color": "#FAFAFA",
            "background_opacity": 255,
            "task_colors": ["#6200EE", "#03DAC6", "#018786", "#B00020"],
            "marker_color": "#FF1744",
            "text_color": "#000000",
            "accent_color": "#6200EE",
            "description": "浅色背景，Material Design浅色主题，明亮清晰"
        }
    }
    
    def __new__(cls, app_dir: Optional[Path] = None):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(ThemeManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, app_dir: Optional[Path] = None):
        """初始化主题管理器"""
        # 避免重复初始化
        if hasattr(self, '_initialized'):
            return
        
        super().__init__()
        
        # 设置应用目录
        if app_dir is None:
            import sys
            if getattr(sys, 'frozen', False):
                self.app_dir = Path(sys.executable).parent
            else:
                self.app_dir = Path(__file__).parent
        else:
            self.app_dir = app_dir
        
        self.themes_file = self.app_dir / 'themes.json'
        self.config_file = self.app_dir / 'config.json'
        
        # 日志
        self.logger = logging.getLogger(__name__)
        
        # 当前主题配置
        self.current_theme_config = None
        
        # UI组件注册列表
        self._registered_components = []
        
        # 主题数据缓存
        self._themes_cache = None
        self._themes_cache_timestamp = None
        
        # 初始化主题系统
        self._initialize_themes()
        
        # 加载当前主题
        self._load_current_theme()
        
        self._initialized = True
    
    def _initialize_themes(self):
        """初始化主题文件"""
        if not self.themes_file.exists():
            self.logger.info("themes.json 不存在，创建默认主题文件")
            self._create_default_themes_file()
        else:
            # 检查并合并默认预设主题（确保预设主题完整）
            self._merge_default_preset_themes()
    
    def _create_default_themes_file(self):
        """创建默认主题文件"""
        themes_data = {
            "preset_themes": self.DEFAULT_PRESET_THEMES.copy(),
            "custom_themes": {},
            "ai_generated_themes": {}
        }
        
        try:
            with open(self.themes_file, 'w', encoding='utf-8') as f:
                json.dump(themes_data, f, indent=4, ensure_ascii=False)
            self.logger.info("已创建默认 themes.json")
        except Exception as e:
            self.logger.error(f"创建 themes.json 失败: {e}")
    
    def _merge_default_preset_themes(self):
        """合并默认预设主题到现有文件"""
        try:
            with open(self.themes_file, 'r', encoding='utf-8') as f:
                themes_data = json.load(f)
            
            # 确保预设主题存在
            if 'preset_themes' not in themes_data:
                themes_data['preset_themes'] = {}
            
            # 合并默认预设主题（不覆盖用户可能修改的主题）
            for theme_id, theme_config in self.DEFAULT_PRESET_THEMES.items():
                if theme_id not in themes_data['preset_themes']:
                    themes_data['preset_themes'][theme_id] = theme_config
            
            # 确保其他分类存在
            if 'custom_themes' not in themes_data:
                themes_data['custom_themes'] = {}
            if 'ai_generated_themes' not in themes_data:
                themes_data['ai_generated_themes'] = {}
            
            # 保存更新后的文件
            with open(self.themes_file, 'w', encoding='utf-8') as f:
                json.dump(themes_data, f, indent=4, ensure_ascii=False)
            
            # 清除缓存，强制下次重新加载
            self._themes_cache = None
            self._themes_cache_timestamp = None
            
        except Exception as e:
            self.logger.error(f"合并预设主题失败: {e}")
    
    def _load_current_theme(self):
        """加载当前主题配置（静默加载，不触发信号）"""
        try:
            # 加载config.json中的主题模式配置
            if not self.config_file.exists():
                self.logger.info("config.json 不存在，使用默认主题")
                self._set_default_theme_silent()
                return
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            theme_config = config.get('theme', {})
            theme_mode = theme_config.get('mode', 'preset')
            current_theme_id = theme_config.get('current_theme_id', 'fresh')
            
            # 根据模式加载主题（静默加载，不触发信号）
            if theme_mode == 'system':
                # 跟随系统主题
                system_theme = self.detect_system_theme()
                self._load_theme_by_id_silent(system_theme, 'preset')
            elif theme_mode == 'dark':
                self._load_theme_by_id_silent('dark', 'preset')
            elif theme_mode == 'light':
                self._load_theme_by_id_silent('light', 'preset')
            elif theme_mode == 'preset':
                self._load_theme_by_id_silent(current_theme_id, 'preset')
            elif theme_mode == 'custom':
                # 加载自定义主题
                self._load_theme_by_id_silent(current_theme_id, 'custom')
            else:
                # 默认使用商务专业主题
                self._load_theme_by_id_silent('business', 'preset')
                
        except Exception as e:
            self.logger.error(f"加载当前主题失败: {e}")
            self._set_default_theme_silent()
    
    def _set_default_theme_silent(self):
        """设置默认主题（静默，不触发信号）"""
        self._load_theme_by_id_silent('fresh', 'preset')
    
    def _load_theme_by_id_silent(self, theme_id: str, theme_type: str = 'preset') -> bool:
        """根据ID加载主题（静默版本，不触发信号）

        ✅ 性能优化: 复用get_all_themes()的缓存机制,避免重复文件读取
        """
        try:
            # ✅ 使用缓存的主题数据(避免重复读取themes.json)
            themes_data = self.get_all_themes()

            theme_key = f"{theme_type}_themes"
            if theme_key not in themes_data:
                self.logger.error(f"主题类型 {theme_type} 不存在")
                return False

            if theme_id not in themes_data[theme_key]:
                self.logger.error(f"主题 {theme_id} 不存在")
                return False

            theme_config = themes_data[theme_key][theme_id]
            self.current_theme_config = theme_config.copy()

            # 不保存到config.json（避免循环）
            # 不发出信号（避免初始化时触发）

            return True

        except Exception as e:
            self.logger.error(f"加载主题失败: {e}")
            return False
    
    def _load_theme_by_id(self, theme_id: str, theme_type: str = 'preset') -> bool:
        """根据ID加载主题

        ✅ 性能优化: 复用get_all_themes()的缓存机制,避免重复文件读取
        """
        try:
            # ✅ 使用缓存的主题数据(避免重复读取themes.json)
            themes_data = self.get_all_themes()

            theme_key = f"{theme_type}_themes"
            if theme_key not in themes_data:
                self.logger.error(f"主题类型 {theme_type} 不存在")
                return False

            if theme_id not in themes_data[theme_key]:
                self.logger.error(f"主题 {theme_id} 不存在")
                return False

            theme_config = themes_data[theme_key][theme_id]
            self.current_theme_config = theme_config.copy()

            # 保存到config.json
            self._save_theme_mode_to_config(theme_type, theme_id)

            # 发出主题变更信号
            self.theme_changed.emit()

            return True

        except Exception as e:
            self.logger.error(f"加载主题失败: {e}")
            return False
    
    def _save_theme_mode_to_config(self, mode: str, theme_id: str):
        """保存主题模式到config.json"""
        try:
            # 加载现有配置
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {}
            
            # 更新主题配置
            if 'theme' not in config:
                config['theme'] = {}
            
            config['theme']['mode'] = mode
            config['theme']['current_theme_id'] = theme_id
            
            # 保存配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            self.logger.info(f"已保存主题模式: {mode}, 主题ID: {theme_id}")
            
        except Exception as e:
            self.logger.error(f"保存主题模式失败: {e}")
    
    def set_theme_mode(self, mode: str):
        """
        设置主题模式
        
        参数:
        - mode: "dark" | "light" | "system" | "preset" | "custom"
        """
        if mode == 'system':
            system_theme = self.detect_system_theme()
            self.apply_preset_theme(system_theme)
        elif mode == 'dark':
            self.apply_preset_theme('dark')
        elif mode == 'light':
            self.apply_preset_theme('light')
        else:
            # preset 或 custom 模式需要指定主题ID
            self.logger.warning(f"设置主题模式 {mode} 需要指定主题ID")
    
    def apply_preset_theme(self, preset_name: str) -> bool:
        """
        应用预设主题
        
        参数:
        - preset_name: 预设主题ID（如 "business", "fresh"）
        
        返回:
        - 是否成功应用
        """
        return self._load_theme_by_id(preset_name, 'preset')
    
    def apply_custom_theme(self, theme_config: dict, theme_id: Optional[str] = None) -> bool:
        """
        应用自定义主题
        
        参数:
        - theme_config: 主题配置字典
        - theme_id: 主题ID（如果为None，则自动生成）
        
        返回:
        - 是否成功应用
        """
        try:
            # 如果未提供ID，自动生成
            if theme_id is None:
                theme_id = f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 确保主题配置完整
            if 'id' not in theme_config:
                theme_config['id'] = theme_id
            if 'type' not in theme_config:
                theme_config['type'] = 'custom'
            if 'created_at' not in theme_config:
                theme_config['created_at'] = datetime.now().strftime('%Y-%m-%d')
            
            # 加载现有主题文件
            with open(self.themes_file, 'r', encoding='utf-8') as f:
                themes_data = json.load(f)
            
            # 添加到自定义主题
            if 'custom_themes' not in themes_data:
                themes_data['custom_themes'] = {}
            
            themes_data['custom_themes'][theme_id] = theme_config.copy()
            
            # 保存主题文件
            with open(self.themes_file, 'w', encoding='utf-8') as f:
                json.dump(themes_data, f, indent=4, ensure_ascii=False)
            
            # 清除缓存，强制下次重新加载
            self._themes_cache = None
            self._themes_cache_timestamp = None
            
            # 应用主题
            self.current_theme_config = theme_config.copy()
            
            # 保存到config.json
            self._save_theme_mode_to_config('custom', theme_id)
            
            # 发出主题变更信号
            self.theme_changed.emit()
            
            self.logger.info(f"已应用自定义主题: {theme_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"应用自定义主题失败: {e}")
            return False
    
    def get_current_theme(self) -> Optional[dict]:
        """
        获取当前主题配置
        
        返回:
        - 当前主题配置字典，如果未设置则返回None
        """
        return self.current_theme_config.copy() if self.current_theme_config else None
    
    def get_all_themes(self) -> Dict[str, Any]:
        """
        获取所有主题(带缓存机制)

        ✅ 性能优化: 基于文件修改时间(mtime)的智能缓存
        - 首次调用: 从磁盘加载 themes.json
        - 后续调用: 如果文件未修改,返回缓存(节省50-100ms)
        - 文件修改: 自动刷新缓存

        返回:
        - 包含所有主题的字典 {"preset_themes": {}, "custom_themes": {}, "ai_generated_themes": {}}
        """
        # 检查缓存是否有效(文件修改时间)
        try:
            if self.themes_file.exists():
                current_mtime = self.themes_file.stat().st_mtime
                if (self._themes_cache is not None and
                    self._themes_cache_timestamp is not None and
                    self._themes_cache_timestamp == current_mtime):
                    # 缓存有效，应用翻译后返回
                    self.logger.debug("ThemeManager: 使用缓存的主题数据(避免文件I/O)")
                    if "preset_themes" in self._themes_cache:
                        self._translate_preset_themes(self._themes_cache["preset_themes"])
                    return self._themes_cache
        except Exception as e:
            self.logger.debug(f"检查缓存时出错: {e}")
        
        # 缓存无效或不存在，重新加载
        try:
            self.logger.debug("ThemeManager: 从磁盘加载主题数据(缓存失效或首次加载)")
            with open(self.themes_file, 'r', encoding='utf-8') as f:
                themes_data = json.load(f)

            # Apply translations to preset themes
            if "preset_themes" in themes_data:
                self._translate_preset_themes(themes_data["preset_themes"])

            # 更新缓存
            try:
                if self.themes_file.exists():
                    self._themes_cache_timestamp = self.themes_file.stat().st_mtime
                    self.logger.debug(f"ThemeManager: 缓存已更新 (mtime={self._themes_cache_timestamp})")
                else:
                    self._themes_cache_timestamp = None
            except Exception:
                self._themes_cache_timestamp = None

            self._themes_cache = themes_data
            return themes_data
        except Exception as e:
            self.logger.error(f"加载所有主题失败: {e}")
            themes_data = {
                "preset_themes": self.DEFAULT_PRESET_THEMES.copy(),
                "custom_themes": {},
                "ai_generated_themes": {}
            }
            # Apply translations to preset themes
            self._translate_preset_themes(themes_data["preset_themes"])
            return themes_data

    def _translate_preset_themes(self, preset_themes: dict):
        """
        Translate name and description fields for preset themes

        Args:
        - preset_themes: Dictionary of preset themes to translate (modified in-place)
        """
        for theme_id, theme_data in preset_themes.items():
            if theme_data.get("type") == "preset":
                # Translate name
                theme_data["name"] = tr(f"themes.{theme_id}.name")
                # Translate description
                theme_data["description"] = tr(f"themes.{theme_id}.description")

    def register_ui_component(self, component, apply_immediately=True):
        """
        注册UI组件，主题变更时自动通知
        
        参数:
        - component: UI组件对象（需要实现 apply_theme 方法）
        - apply_immediately: 是否立即应用主题（默认True，但初始化时建议设为False）
        """
        if component not in self._registered_components:
            self._registered_components.append(component)
            self.logger.debug(f"已注册UI组件: {type(component).__name__}")
            
            # 连接主题变更信号（确保不重复连接）
            # 使用disconnect确保不会重复连接
            try:
                self.theme_changed.disconnect(component.apply_theme)
            except (TypeError, RuntimeError):
                # 如果没有连接过，disconnect会抛出异常，这是正常的
                pass
            
            # 连接信号
            if hasattr(component, 'apply_theme'):
                self.theme_changed.connect(component.apply_theme)
            
            # 立即应用当前主题（仅在组件已就绪时）
            if apply_immediately and hasattr(component, 'apply_theme'):
                try:
                    component.apply_theme()
                except Exception as e:
                    self.logger.error(f"注册时应用主题失败: {e}", exc_info=True)
    
    def unregister_ui_component(self, component):
        """取消注册UI组件"""
        if component in self._registered_components:
            self._registered_components.remove(component)
            
            # 断开信号连接
            if hasattr(component, 'apply_theme'):
                try:
                    self.theme_changed.disconnect(component.apply_theme)
                except (TypeError, RuntimeError):
                    # 如果没有连接过，disconnect会抛出异常，这是正常的
                    pass
            
            self.logger.debug(f"已取消注册UI组件: {type(component).__name__}")
    
    def detect_system_theme(self) -> str:
        """
        检测系统主题（深色/浅色）
        
        返回:
        - "dark" 或 "light"
        """
        if platform.system() == 'Windows':
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
                )
                try:
                    value = winreg.QueryValueEx(key, "AppsUseLightTheme")[0]
                    return "light" if value == 1 else "dark"
                except:
                    return "light"
                finally:
                    winreg.CloseKey(key)
            except Exception as e:
                self.logger.warning(f"检测Windows系统主题失败: {e}")
                return "light"
        elif platform.system() == 'Darwin':  # macOS
            # macOS检测逻辑（需要后续实现）
            return "light"
        else:  # Linux
            # Linux检测逻辑（需要后续实现）
            return "light"
    
    def adapt_task_colors(self, tasks: List[dict], theme: Optional[dict] = None, 
                         apply_theme_colors: bool = False) -> List[dict]:
        """
        适配任务颜色到主题
        
        参数:
        - tasks: 任务列表
        - theme: 主题配置（如果为None，使用当前主题）
        - apply_theme_colors: 是否应用主题配色（False=保持原颜色，True=应用主题配色）
        
        返回:
        - 适配后的任务列表
        """
        if not apply_theme_colors:
            return tasks.copy()  # 保持原颜色
        
        # 使用当前主题或指定主题
        if theme is None:
            theme = self.current_theme_config
        
        if not theme:
            return tasks.copy()
        
        # 智能分配：根据任务类型或顺序分配主题配色
        theme_colors = theme.get('task_colors', [])
        if not theme_colors:
            return tasks.copy()
        
        adapted_tasks = []
        
        # 策略: 尝试根据任务名称关键词匹配颜色
        task_type_mapping = {
            '工作': 0, '上班': 0, '办公': 0, 'work': 0,
            '休息': 1, '午休': 1, '小憩': 1, 'break': 1, 'break': 1,
            '学习': 2, '阅读': 2, '课程': 2, 'study': 2, 'learn': 2,
            '运动': 3, '健身': 3, '锻炼': 3, 'exercise': 3, 'sport': 3,
            '会议': 4, '讨论': 4, 'meeting': 4,
            '其他': 5, 'other': 5
        }
        
        for task in tasks:
            task_copy = task.copy()
            task_name = task.get('task', '').lower()
            
            # 尝试匹配任务类型
            color_index = None
            for keyword, index in task_type_mapping.items():
                if keyword.lower() in task_name:
                    color_index = index % len(theme_colors)
                    break
            
            # 如果未匹配到，按顺序分配
            if color_index is None:
                color_index = len(adapted_tasks) % len(theme_colors)
            
            task_copy['color'] = theme_colors[color_index]
            adapted_tasks.append(task_copy)
        
        return adapted_tasks

