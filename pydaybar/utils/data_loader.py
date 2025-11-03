"""
配置和任务数据加载工具
"""
import json
from pathlib import Path
from . import time_utils, path_utils


def load_config(app_dir, logger):
    """加载配置文件

    Args:
        app_dir: 应用程序目录（Path对象）
        logger: 日志记录器

    Returns:
        dict: 配置字典
    """
    config_file = app_dir / 'config.json'

    # 默认配置
    default_config = {
        "bar_height": 20,
        "position": "bottom",
        "background_color": "#505050",
        "background_opacity": 180,
        "marker_color": "#FF0000",
        "marker_width": 2,
        "marker_type": "gif",  # "line", "image", "gif"
        "marker_image_path": "kun.webp",  # 默认使用kun.webp
        "marker_size": 50,  # 标记图片大小(像素)
        "marker_y_offset": 0,  # 标记图片 Y 轴偏移(像素,正值向上,负值向下)
        "screen_index": 0,
        "update_interval": 1000,
        "enable_shadow": True,
        "corner_radius": 0,
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


def load_tasks(app_dir, logger):
    """加载并验证任务数据

    Args:
        app_dir: 应用程序目录（Path对象）
        logger: 日志记录器

    Returns:
        list: 任务列表
    """
    tasks_file = app_dir / 'tasks.json'

    # 如果文件不存在,尝试加载24小时模板
    if not tasks_file.exists():
        logger.info("tasks.json 不存在,尝试加载24小时模板")
        # 使用 get_resource_path 获取打包资源路径
        template_file = path_utils.get_resource_path('tasks_template_24h.json')

        if template_file.exists():
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    default_tasks = json.load(f)
                # 保存为 tasks.json(保存到 exe 所在目录)
                with open(tasks_file, 'w', encoding='utf-8') as f:
                    json.dump(default_tasks, f, indent=4, ensure_ascii=False)
                logger.info(f"已从模板加载 {len(default_tasks)} 个任务")
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
