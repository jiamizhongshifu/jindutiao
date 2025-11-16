"""
场景系统模块

提供场景配置加载、渲染、事件管理等功能
"""

from .models import (
    EventTriggerType,
    EventActionType,
    EventAction,
    EventConfig,
    SceneItemPosition,
    SceneItem,
    RoadLayer,
    SceneLayer,
    CanvasConfig,
    SceneConfig,
)

from .loader import (
    ResourceCache,
    SceneLoader,
)

from .renderer import (
    SceneRenderer,
)

from .event_manager import (
    SceneEventManager,
)

from .scene_manager import (
    SceneManager,
)

__all__ = [
    # Models
    'EventTriggerType',
    'EventActionType',
    'EventAction',
    'EventConfig',
    'SceneItemPosition',
    'SceneItem',
    'RoadLayer',
    'SceneLayer',
    'CanvasConfig',
    'SceneConfig',
    # Loader
    'ResourceCache',
    'SceneLoader',
    # Renderer
    'SceneRenderer',
    # Event Manager
    'SceneEventManager',
    # Scene Manager
    'SceneManager',
]
