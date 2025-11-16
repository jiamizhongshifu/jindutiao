"""
场景渲染器 - SceneRenderer

负责将场景配置渲染到进度条,支持道路层、场景元素、时间标记的分层渲染
"""

import logging
from typing import Optional, List, Tuple
from PySide6.QtCore import QRectF, Qt, QPointF
from PySide6.QtGui import QPainter, QPixmap, QPen, QBrush, QColor

from .models import SceneConfig, SceneItem, RoadLayer
from .loader import ResourceCache


class SceneRenderer:
    """场景渲染器 - 将场景绘制到进度条

    职责:
    - 渲染道路层(平铺,支持z-index)
    - 渲染场景元素(按z-index排序)
    - 渲染时间标记(坤坤动图)
    - 处理层级混合渲染
    """

    def __init__(self, scene: Optional[SceneConfig] = None, cache: Optional[ResourceCache] = None):
        """初始化场景渲染器

        Args:
            scene: 场景配置对象
            cache: 资源缓存对象
        """
        self.logger = logging.getLogger(__name__)
        self.scene = scene
        self.cache = cache or ResourceCache()

        # 渲染状态
        self._prepared = False

        self.logger.debug("SceneRenderer initialized")

    def set_scene(self, scene: SceneConfig):
        """设置要渲染的场景

        Args:
            scene: 场景配置对象
        """
        self.scene = scene
        self._prepared = False
        self.logger.info(f"Scene set: {scene.name} v{scene.version}")

    def prepare_resources(self, scene: Optional[SceneConfig] = None):
        """预加载场景资源到缓存

        Args:
            scene: 场景配置对象,如果为None则使用当前场景

        Returns:
            成功加载的资源数量
        """
        if scene:
            self.scene = scene

        if not self.scene:
            self.logger.warning("No scene to prepare resources")
            return 0

        # 收集所有需要加载的资源路径
        resource_paths = []

        # 1. 道路层图片
        if self.scene.road_layer and self.scene.road_layer.image:
            resource_paths.append(self.scene.road_layer.image)

        # 2. 场景元素图片
        for item in self.scene.scene_layer.items:
            if item.image:
                resource_paths.append(item.image)

        # 预加载资源
        success_count = self.cache.preload(resource_paths)
        self._prepared = True

        self.logger.info(f"Prepared {success_count}/{len(resource_paths)} resources")
        return success_count

    def render(self, painter: QPainter, canvas_rect: QRectF, progress: float):
        """渲染完整场景

        这是主渲染入口,按正确的层级顺序渲染所有元素

        Args:
            painter: Qt画笔对象
            canvas_rect: 画布矩形区域 (进度条的绘制区域)
            progress: 当前进度 (0.0 - 1.0)
        """
        if not self.scene:
            return

        if not self._prepared:
            self.logger.warning("Resources not prepared, preparing now...")
            self.prepare_resources()

        # 获取所有元素(道路层+场景元素)并按z-index排序
        all_items = self._get_all_renderable_items()

        # 按z-index从小到大排序(小的在下,大的在上)
        all_items.sort(key=lambda x: x[0])

        # 依次渲染每个元素
        for z_index, item_type, item_data in all_items:
            if item_type == 'road':
                self._render_road_layer(painter, canvas_rect, item_data)
            elif item_type == 'item':
                self._render_scene_item(painter, canvas_rect, item_data)

        # 最后渲染时间标记(坤坤动图) - 始终在最上层
        # TODO: 实现时间标记渲染
        # self._render_timeline_marker(painter, canvas_rect, progress)

    def _get_all_renderable_items(self) -> List[Tuple[int, str, any]]:
        """获取所有可渲染元素,返回 (z_index, type, data) 元组列表

        Returns:
            元素列表,每个元素为 (z_index, item_type, item_data)
            - z_index: 层级索引
            - item_type: 'road' 或 'item'
            - item_data: RoadLayer 或 SceneItem 对象
        """
        items = []

        # 添加道路层
        if self.scene.road_layer and self.scene.road_layer.image:
            items.append((self.scene.road_layer.z_index, 'road', self.scene.road_layer))

        # 添加场景元素
        for item in self.scene.scene_layer.items:
            if item.image:
                items.append((item.z_index, 'item', item))

        return items

    def _render_road_layer(self, painter: QPainter, canvas_rect: QRectF, road: RoadLayer):
        """渲染道路层(平铺模式)

        Args:
            painter: Qt画笔对象
            canvas_rect: 画布矩形区域
            road: 道路层配置对象
        """
        # 从缓存获取道路图片
        pixmap = self.cache.get(road.image)
        if not pixmap:
            self.logger.warning(f"Road image not found in cache: {road.image}")
            return

        # 先缩放图片
        scaled_pixmap = pixmap
        if road.scale != 1.0:
            scaled_width = int(pixmap.width() * road.scale)
            scaled_height = int(pixmap.height() * road.scale)
            scaled_pixmap = pixmap.scaled(
                scaled_width, scaled_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

        # 道路层扩展到整个窗口宽度（作为背景填充）
        # 使用painter.device()获取窗口宽度，从屏幕最左侧开始平铺
        device_width = painter.device().width()
        road_x = 0  # 从屏幕最左侧开始，不应用offset_x（作为背景填充）
        road_y = canvas_rect.y() + road.offset_y
        road_width = device_width  # 使用整个窗口宽度

        # 根据type字段决定渲染模式(默认为tiled,水平平铺)
        if road.type == "tiled" or road.type == "repeat-x":
            # 水平平铺 - 使用已缩放的图片，不再二次缩放
            self._tile_horizontal_no_scale(painter, scaled_pixmap, road_x, road_y, road_width)
        else:
            # 拉伸模式
            road_height = canvas_rect.height()
            target_rect = QRectF(road_x, road_y, road_width, road_height)
            painter.drawPixmap(target_rect, scaled_pixmap, QRectF(scaled_pixmap.rect()))

    def _tile_horizontal_no_scale(self, painter: QPainter, pixmap: QPixmap,
                                  x: float, y: float, width: float):
        """水平平铺绘制 - 不进行缩放，使用原始pixmap尺寸

        Args:
            painter: Qt画笔对象
            pixmap: 已缩放的源图片
            x, y: 起始位置
            width: 目标区域宽度
        """
        tile_width = pixmap.width()
        tile_height = pixmap.height()

        # 水平方向重复绘制
        current_x = x
        while current_x < x + width:
            # 计算当前图块的实际宽度(最后一块可能不完整)
            remaining_width = x + width - current_x
            actual_width = min(tile_width, remaining_width)

            # 计算源图片的裁剪区域
            source_rect = QRectF(0, 0, actual_width, tile_height)
            target_rect = QRectF(current_x, y, actual_width, tile_height)

            painter.drawPixmap(target_rect, pixmap, source_rect)

            current_x += tile_width

    def _tile_horizontal(self, painter: QPainter, pixmap: QPixmap,
                        x: float, y: float, width: float, height: float):
        """水平平铺绘制

        Args:
            painter: Qt画笔对象
            pixmap: 源图片
            x, y: 起始位置
            width, height: 目标区域尺寸
        """
        # 缩放图片到目标高度
        scaled_height = height
        scaled_width = pixmap.width() * (height / pixmap.height())

        # 水平方向重复绘制
        current_x = x
        while current_x < x + width:
            # 计算当前图块的实际宽度(最后一块可能不完整)
            remaining_width = x + width - current_x
            actual_width = min(scaled_width, remaining_width)

            # 计算源图片的裁剪区域
            source_width = pixmap.width() * (actual_width / scaled_width)
            source_rect = QRectF(0, 0, source_width, pixmap.height())

            # 绘制
            target_rect = QRectF(current_x, y, actual_width, scaled_height)
            painter.drawPixmap(target_rect, pixmap, source_rect)

            current_x += scaled_width

    def _tile_vertical(self, painter: QPainter, pixmap: QPixmap,
                      x: float, y: float, width: float, height: float):
        """垂直平铺绘制

        Args:
            painter: Qt画笔对象
            pixmap: 源图片
            x, y: 起始位置
            width, height: 目标区域尺寸
        """
        # 缩放图片到目标宽度
        scaled_width = width
        scaled_height = pixmap.height() * (width / pixmap.width())

        # 垂直方向重复绘制
        current_y = y
        while current_y < y + height:
            # 计算当前图块的实际高度(最后一块可能不完整)
            remaining_height = y + height - current_y
            actual_height = min(scaled_height, remaining_height)

            # 计算源图片的裁剪区域
            source_height = pixmap.height() * (actual_height / scaled_height)
            source_rect = QRectF(0, 0, pixmap.width(), source_height)

            # 绘制
            target_rect = QRectF(x, current_y, scaled_width, actual_height)
            painter.drawPixmap(target_rect, pixmap, source_rect)

            current_y += scaled_height

    def _tile_both(self, painter: QPainter, pixmap: QPixmap,
                  x: float, y: float, width: float, height: float):
        """双向平铺绘制

        Args:
            painter: Qt画笔对象
            pixmap: 源图片
            x, y: 起始位置
            width, height: 目标区域尺寸
        """
        # 保持原始比例
        tile_width = pixmap.width()
        tile_height = pixmap.height()

        # 双向重复绘制
        current_y = y
        while current_y < y + height:
            remaining_height = y + height - current_y
            actual_height = min(tile_height, remaining_height)

            current_x = x
            while current_x < x + width:
                remaining_width = x + width - current_x
                actual_width = min(tile_width, remaining_width)

                # 计算裁剪区域
                source_rect = QRectF(0, 0, actual_width, actual_height)
                target_rect = QRectF(current_x, current_y, actual_width, actual_height)

                painter.drawPixmap(target_rect, pixmap, source_rect)

                current_x += tile_width

            current_y += tile_height

    def _render_scene_item(self, painter: QPainter, canvas_rect: QRectF, item: SceneItem):
        """渲染场景元素

        Args:
            painter: Qt画笔对象
            canvas_rect: 画布矩形区域
            item: 场景元素对象
        """
        # 从缓存获取图片
        pixmap = self.cache.get(item.image)
        if not pixmap:
            self.logger.warning(f"Scene item image not found in cache: {item.image}")
            return

        # 计算元素位置和尺寸
        # X位置: 根据百分比计算
        item_x = canvas_rect.x() + canvas_rect.width() * (item.position.x_percent / 100.0)
        # Y位置: 从canvas顶部的像素偏移
        item_y = canvas_rect.y() + item.position.y_pixel

        # 尺寸: 原始图片尺寸 * 缩放比例
        item_width = pixmap.width() * item.scale
        item_height = pixmap.height() * item.scale

        # 绘制元素
        target_rect = QRectF(item_x, item_y, item_width, item_height)
        painter.drawPixmap(target_rect, pixmap, QRectF(pixmap.rect()))

    def _render_timeline_marker(self, painter: QPainter, canvas_rect: QRectF, progress: float):
        """渲染时间标记(坤坤动图)

        Args:
            painter: Qt画笔对象
            canvas_rect: 画布矩形区域
            progress: 当前进度 (0.0 - 1.0)
        """
        # TODO: 实现时间标记渲染
        # 这里需要集成主程序中的坤坤动图逻辑
        # 暂时留空,后续实现
        pass
