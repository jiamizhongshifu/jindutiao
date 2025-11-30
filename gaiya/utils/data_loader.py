"""
Config and task data loading utilities
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from . import time_utils, path_utils
from ..core.template_manager import TemplateManager


def init_i18n(config: Dict[str, Any], logger: logging.Logger) -> None:
    """Initialize i18n module based on config

    Args:
        config: Configuration dictionary
        logger: Logger instance for diagnostic messages
    """
    try:
        from i18n import set_language, get_system_locale

        language = config.get('language', 'auto')

        if language == 'auto':
            # Auto-detect system language
            actual_locale = get_system_locale()
            set_language(actual_locale)
            logger.info(f"i18n initialized with system locale: {actual_locale}")
        else:
            # Use specified language
            set_language(language)
            logger.info(f"i18n initialized with configured language: {language}")

    except ImportError as e:
        logger.warning(f"i18n module not available: {e}")
    except Exception as e:
        logger.error(f"Failed to initialize i18n: {e}")


def load_config(app_dir: Path, logger: logging.Logger) -> Dict[str, Any]:
    """Load configuration from config.json

    Args:
        app_dir: Application directory (Path object)
        logger: Logger instance

    Returns:
        Dict: Configuration dictionary with merged defaults
    """
    config_file = app_dir / 'config.json'

    # Default config
    default_config = {
        "language": "auto",  # "auto", "zh_CN", "en_US"
        "bar_height": 10,
        "position": "bottom",
        "background_color": "#505050",
        "background_opacity": 180,
        "marker_color": "#FF0000",
        "marker_width": 2,
        "marker_type": "gif",  # "line", "image", "gif"
        "marker_image_path": "kun.webp",  # Default to kun.webp
        "marker_size": 100,  # Marker image size (pixels)
        "marker_speed": 100,  # Animation speed (percentage, 100=normal)
        "marker_x_offset": 0,  # Marker X offset (pixels, positive=right)
        "marker_y_offset": -28,  # Marker Y offset (pixels, positive=up)
        "screen_index": 0,
        "update_interval": 1000,
        "enable_shadow": True,
        "corner_radius": 0,
        "activity_tracking": {
            "enabled": False,
            "polling_interval": 5,
            "min_session_duration": 5,
            "data_retention_days": 90
        },
        # 通知配置
        "notification": {
            "enabled": True,                    # 通知总开关
            "before_start_minutes": [10, 5],   # 任务开始前N分钟提醒
            "on_start": True,                   # 任务开始时提醒
            "before_end_minutes": [5],          # 任务结束前N分钟提醒
            "on_end": False,                    # 任务结束时提醒
            "sound_enabled": True,              # 声音开关
            "sound_file": "",                   # 自定义提示音路径
            "quiet_hours": {                    # 免打扰时段
                "enabled": False,
                "start": "22:00",
                "end": "08:00"
            }
        }
    }

    if not config_file.exists():
        logger.info("config.json 不存在,创建默认配置")
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4)
        return default_config

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        # 合并默认配置(防止缺失键)
        merged_config = {**default_config, **config}

        # 向后兼容：如果config.json中没有theme字段，添加默认主题配置
        if 'theme' not in merged_config:
            merged_config['theme'] = {
                'mode': 'preset',
                'current_theme_id': 'business',
                'auto_apply_task_colors': False
            }
            logger.info("检测到旧版本config.json，已添加默认主题配置")

        logger.info("配置文件加载成功")
        return merged_config
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析错误: {e}")
        return default_config
    except Exception as e:
        logger.error(f"加载配置失败: {e}", exc_info=True)
        return default_config


def load_tasks(app_dir: Path, logger: logging.Logger) -> List[Dict[str, str]]:
    """Load and validate task data from tasks.json

    Args:
        app_dir: Application directory (Path object)
        logger: Logger instance

    Returns:
        List[Dict]: List of validated task dictionaries with keys: start, end, task, color
    """
    tasks_file = app_dir / 'tasks.json'

    # 如果文件不存在,智能加载最佳匹配模板
    if not tasks_file.exists():
        logger.info("tasks.json 不存在,尝试智能匹配模板")

        # 尝试使用TemplateManager查找最佳匹配模板
        try:
            tm = TemplateManager(app_dir, logger)
            best_match = tm.get_best_match_template()

            if best_match:
                # 找到匹配的自动应用模板
                template_id = best_match['id']
                template_name = best_match['name']
                logger.info(f"✨ 智能匹配到模板: {template_name} ({template_id})")

                # 加载模板任务数据
                template_tasks = tm.load_template_tasks(template_id)
                if template_tasks:
                    # 保存为 tasks.json
                    with open(tasks_file, 'w', encoding='utf-8') as f:
                        json.dump(template_tasks, f, indent=4, ensure_ascii=False)
                    logger.info(f"✅ 已自动应用模板 {template_name}，包含 {len(template_tasks)} 个任务")
                    return template_tasks
        except Exception as e:
            logger.warning(f"智能模板匹配失败，退回到默认模板: {e}")

        # 如果没有找到自动应用模板，退回到24小时模板
        logger.info("未找到启用自动应用的模板，使用默认24小时模板")
        template_file = path_utils.get_resource_path('tasks_template_24h.json')

        if template_file.exists():
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    default_tasks = json.load(f)
                # 保存为 tasks.json(保存到 exe 所在目录)
                with open(tasks_file, 'w', encoding='utf-8') as f:
                    json.dump(default_tasks, f, indent=4, ensure_ascii=False)
                logger.info(f"已从24小时模板加载 {len(default_tasks)} 个任务")
                return default_tasks
            except Exception as e:
                logger.error(f"加载模板失败: {e}")

        # 如果模板也不存在,创建简单的默认任务
        logger.info("模板不存在,创建默认任务")
        default_tasks = [
            {"start": "09:00", "end": "12:00", "task": "上午工作", "color": "#4CAF50"}
        ]
        with open(tasks_file, 'w', encoding='utf-8') as f:
            json.dump(default_tasks, f, indent=4, ensure_ascii=False)
        return default_tasks

    try:
        with open(tasks_file, 'r', encoding='utf-8') as f:
            tasks = json.load(f)

        # 验证数据格式
        validated_tasks = []
        for i, task in enumerate(tasks):
            if all(key in task for key in ['start', 'end', 'task', 'color']):
                # 验证时间格式
                if time_utils.validate_time_format(task['start']) and \
                   time_utils.validate_time_format(task['end']):
                    validated_tasks.append(task)
                else:
                    logger.warning(f"任务 {i+1} 时间格式无效: {task}")
            else:
                logger.warning(f"任务 {i+1} 缺少必要字段: {task}")

        logger.info(f"成功加载 {len(validated_tasks)} 个任务")
        return validated_tasks
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析错误: {e}")
        return []
    except Exception as e:
        logger.error(f"加载任务失败: {e}", exc_info=True)
        return []
