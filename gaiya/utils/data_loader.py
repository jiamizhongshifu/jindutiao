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
        "bar_height": 6,
        "position": "bottom",
        "background_color": "#000000",
        "background_opacity": 204,
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
        "autostart_initialized": False,  # 首次运行标志，用于自动开启自启动
        "activity_tracking": {
            "enabled": True,  # 默认开启行为识别
            "polling_interval": 5,
            "min_session_duration": 5,
            "data_retention_days": 90
        },
        # 通知配置
        "notification": {
            "enabled": True,                    # 通知总开关
            "before_start_minutes": [],         # 任务开始前N分钟提醒 (默认不提醒)
            "on_start": True,                   # 任务开始时提醒
            "before_end_minutes": [],           # 任务结束前N分钟提醒 (默认不提醒)
            "on_end": False,                    # 任务结束时提醒
            "sound_enabled": True,              # 声音开关
            "sound_file": "",                   # 自定义提示音路径
            "quiet_hours": {                    # 免打扰时段
                "enabled": False,
                "start": "22:00",
                "end": "08:00"
            }
        },
        # 任务完成推理调度器配置
        "task_completion_scheduler": {
            "enabled": True,                    # 是否启用自动推理
            "trigger_time": "21:00",            # 每日触发时间
            "trigger_on_startup": False,        # 启动时是否推理昨日数据
            "auto_confirm_all": False,          # 完全自动确认 (True=所有任务自动确认,不弹窗)
            "auto_confirm_threshold": 0         # 自动确认阈值 (0=不自动确认, 90=自动确认完成度≥90%的高置信度任务)
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


def load_daily_tasks() -> Dict[str, Dict]:
    """
    加载每日任务计划 (用于任务完成推理)

    从 tasks.json 加载任务,并转换为推理引擎所需的格式

    Returns:
        {
            'time-block-0': {
                'name': '深度睡眠',
                'task_type': 'rest',
                'start_time': '00:00',
                'end_time': '06:00',
                'duration_minutes': 360
            },
            ...
        }
    """
    from pathlib import Path
    import json
    import logging

    logger = logging.getLogger("gaiya.utils.data_loader")

    # 获取应用目录
    try:
        from . import path_utils
        app_dir = path_utils.get_app_dir()
    except Exception:
        # 如果无法获取app_dir,使用当前目录
        app_dir = Path.cwd()

    tasks_file = app_dir / 'tasks.json'

    if not tasks_file.exists():
        logger.warning(f"tasks.json 不存在: {tasks_file}")
        return {}

    try:
        with open(tasks_file, 'r', encoding='utf-8') as f:
            tasks = json.load(f)

        # 转换为推理引擎格式
        daily_tasks = {}

        for idx, task in enumerate(tasks):
            # 生成 time_block_id
            time_block_id = f"time-block-{idx}"

            # 解析时间
            start_time = task.get('start', '00:00')
            end_time = task.get('end', '00:00')

            # 计算时长 (分钟)
            try:
                from datetime import datetime
                start_dt = datetime.strptime(start_time, '%H:%M')
                end_dt = datetime.strptime(end_time, '%H:%M')

                # 处理跨天情况
                if end_dt <= start_dt:
                    from datetime import timedelta
                    end_dt += timedelta(days=1)

                duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
            except Exception as e:
                logger.warning(f"计算任务时长失败 ({task.get('task')}): {e}")
                duration_minutes = 0

            # 推断任务类型
            task_name = task.get('task', '未命名任务')
            task_type = infer_task_type(task_name)

            daily_tasks[time_block_id] = {
                'name': task_name,
                'task_type': task_type,
                'start_time': start_time,
                'end_time': end_time,
                'duration_minutes': duration_minutes,
                'color': task.get('color', '#FFFFFF')
            }

        logger.info(f"加载每日任务: {len(daily_tasks)} 个")
        return daily_tasks

    except Exception as e:
        logger.error(f"加载每日任务失败: {e}", exc_info=True)
        return {}


def infer_task_type(task_name: str) -> str:
    """
    根据任务名称推断任务类型

    Args:
        task_name: 任务名称

    Returns:
        'work', 'rest', 'exercise', 'study', 'entertainment', 'other'
    """
    task_name_lower = task_name.lower()

    # 工作相关
    work_keywords = ['工作', 'work', '开发', '编程', '会议', 'meeting', '项目']
    if any(keyword in task_name_lower for keyword in work_keywords):
        return 'work'

    # 休息相关
    rest_keywords = ['睡眠', 'sleep', '休息', 'rest', '午休', 'nap']
    if any(keyword in task_name_lower for keyword in rest_keywords):
        return 'rest'

    # 运动相关
    exercise_keywords = ['运动', 'exercise', '健身', 'gym', '跑步', 'running']
    if any(keyword in task_name_lower for keyword in exercise_keywords):
        return 'exercise'

    # 学习相关
    study_keywords = ['学习', 'study', '阅读', 'reading', '课程', 'course']
    if any(keyword in task_name_lower for keyword in study_keywords):
        return 'study'

    # 娱乐相关
    entertainment_keywords = ['娱乐', 'entertainment', '游戏', 'game', '电影', 'movie']
    if any(keyword in task_name_lower for keyword in entertainment_keywords):
        return 'entertainment'

    return 'other'
