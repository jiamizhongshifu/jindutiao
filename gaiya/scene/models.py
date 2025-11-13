"""
场景系统数据模型

定义场景配置、场景元素、事件等数据结构
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


class EventTriggerType(Enum):
    """事件触发器类型"""
    ON_HOVER = "on_hover"           # 鼠标悬停
    ON_CLICK = "on_click"           # 鼠标点击
    ON_TIME_REACH = "on_time_reach"  # 时间到达


class EventActionType(Enum):
    """事件动作类型"""
    SHOW_TOOLTIP = "show_tooltip"   # 显示提示
    SHOW_DIALOG = "show_dialog"     # 显示对话框
    OPEN_URL = "open_url"           # 打开链接


@dataclass
class EventAction:
    """事件动作"""
    type: str                      # 动作类型（show_tooltip, show_dialog, open_url）
    params: Dict[str, Any]         # 动作参数

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "params": self.params
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'EventAction':
        return cls(
            type=data.get("type", ""),
            params=data.get("params", {})
        )


@dataclass
class EventConfig:
    """事件配置"""
    trigger: str                   # 触发器类型（on_hover, on_click, on_time_reach）
    action: EventAction            # 动作配置

    def to_dict(self) -> dict:
        return {
            "trigger": self.trigger,
            "action": self.action.to_dict()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'EventConfig':
        return cls(
            trigger=data.get("trigger", ""),
            action=EventAction.from_dict(data.get("action", {}))
        )


@dataclass
class SceneItemPosition:
    """场景元素位置"""
    x_percent: float              # X位置（百分比，0-100）
    y_pixel: int                  # Y位置（像素）

    def to_dict(self) -> dict:
        return {
            "x_percent": self.x_percent,
            "y_pixel": self.y_pixel
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SceneItemPosition':
        return cls(
            x_percent=data.get("x_percent", 0.0),
            y_pixel=data.get("y_pixel", 0)
        )


@dataclass
class SceneItem:
    """场景元素"""
    id: str                        # 元素ID
    image: str                     # 图片文件名
    position: SceneItemPosition    # 位置
    scale: float                   # 缩放（1.0 = 100%）
    z_index: int                   # 层级（0-100）
    events: List[EventConfig] = field(default_factory=list)  # 事件列表

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "image": self.image,
            "position": self.position.to_dict(),
            "scale": self.scale,
            "z_index": self.z_index,
            "events": [event.to_dict() for event in self.events]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SceneItem':
        return cls(
            id=data.get("id", ""),
            image=data.get("image", ""),
            position=SceneItemPosition.from_dict(data.get("position", {})),
            scale=data.get("scale", 1.0),
            z_index=data.get("z_index", 51),
            events=[EventConfig.from_dict(e) for e in data.get("events", [])]
        )


@dataclass
class RoadLayer:
    """道路层配置"""
    type: str                      # 类型（tiled - 平铺）
    image: str                     # 图片文件名
    z_index: int = 50              # 层级（默认50）
    offset_x: int = 0              # X偏移
    offset_y: int = 0              # Y偏移
    scale: float = 1.0             # 缩放

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "image": self.image,
            "z_index": self.z_index,
            "offset_x": self.offset_x,
            "offset_y": self.offset_y,
            "scale": self.scale
        }

    @classmethod
    def from_dict(cls, data: dict) -> Optional['RoadLayer']:
        if not data:
            return None
        return cls(
            type=data.get("type", "tiled"),
            image=data.get("image", ""),
            z_index=data.get("z_index", 50),
            offset_x=data.get("offset_x", 0),
            offset_y=data.get("offset_y", 0),
            scale=data.get("scale", 1.0)
        )


@dataclass
class SceneLayer:
    """场景层配置"""
    items: List[SceneItem] = field(default_factory=list)  # 场景元素列表

    def to_dict(self) -> dict:
        return {
            "items": [item.to_dict() for item in self.items]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SceneLayer':
        return cls(
            items=[SceneItem.from_dict(item) for item in data.get("items", [])]
        )


@dataclass
class CanvasConfig:
    """画布配置"""
    width: int                     # 宽度（像素）
    height: int                    # 高度（像素）

    def to_dict(self) -> dict:
        return {
            "width": self.width,
            "height": self.height
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'CanvasConfig':
        return cls(
            width=data.get("width", 1000),
            height=data.get("height", 150)
        )


@dataclass
class SceneConfig:
    """场景完整配置"""
    scene_id: str                  # 场景ID
    name: str                      # 场景名称
    version: str                   # 配置版本
    canvas: CanvasConfig           # 画布配置
    road_layer: Optional[RoadLayer]  # 道路层（可选）
    scene_layer: SceneLayer        # 场景层

    def to_dict(self) -> dict:
        layers = {
            "scene": self.scene_layer.to_dict()
        }
        if self.road_layer:
            layers["road"] = self.road_layer.to_dict()

        return {
            "scene_id": self.scene_id,
            "name": self.name,
            "version": self.version,
            "canvas": self.canvas.to_dict(),
            "layers": layers
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SceneConfig':
        layers = data.get("layers", {})
        return cls(
            scene_id=data.get("scene_id", ""),
            name=data.get("name", ""),
            version=data.get("version", "1.0.0"),
            canvas=CanvasConfig.from_dict(data.get("canvas", {})),
            road_layer=RoadLayer.from_dict(layers.get("road")),
            scene_layer=SceneLayer.from_dict(layers.get("scene", {}))
        )

    def get_all_items_sorted_by_z(self) -> List[SceneItem]:
        """
        获取所有元素，按z-index排序（低到高）

        Returns:
            按z-index排序的元素列表
        """
        return sorted(self.scene_layer.items, key=lambda item: item.z_index)

    def get_road_z_index(self) -> int:
        """
        获取道路层的z-index

        Returns:
            道路层z-index，如果没有道路层则返回50
        """
        return self.road_layer.z_index if self.road_layer else 50
