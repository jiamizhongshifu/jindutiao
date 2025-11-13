# 场景进度条系统技术方案

> **版本**: v0.2.0
> **创建日期**: 2025-11-13
> **最后更新**: 2025-11-13
> **状态**: 🟢 核心决策已确认，准备开发

---

## 📋 目录

- [1. 项目概述](#1-项目概述)
- [2. 核心架构设计](#2-核心架构设计)
- [3. 数据结构定义](#3-数据结构定义)
- [4. 技术实现方案](#4-技术实现方案)
- [5. 用户交互流程](#5-用户交互流程)
- [6. 云端热更新机制](#6-云端热更新机制)
- [7. 分阶段实施计划](#7-分阶段实施计划)
- [8. 已确认的技术决策](#8-已确认的技术决策)
- [9. 待讨论的问题](#9-待讨论的问题)
- [10. 更新日志](#10-更新日志)

---

## 1. 项目概述

### 1.1 核心目标

将进度条从**单纯的时间可视化工具**升级为**互动式场景化体验平台**，通过预设计的视觉场景替代传统的色块进度条，提供更丰富的视觉体验和交互玩法。

### 1.2 核心特性

- ✅ **场景化渲染**: 使用预设计的PNG场景图层替代色块
- ✅ **事件绑定系统**: 场景元素支持悬停、点击、时间触发等交互
- ✅ **任务信息覆盖**: 鼠标悬停显示任务信息，替代色块显示
- ✅ **云端热更新**: 品牌合作元素支持云端配置和每日更新
- ✅ **可视化编辑器**: 图形化工具设计和配置场景

### 1.3 设计原则

1. **保持现有交互**: 任务编辑仍在配置管理器中进行，不改变用户习惯
2. **性能优先**: 场景渲染帧率稳定在30fps以上
3. **渐进式开发**: 先实现核心功能，后续逐步添加高级特性
4. **配置化驱动**: 所有场景通过JSON配置文件定义，便于扩展

---

## 2. 核心架构设计

### 2.1 分层渲染架构

```
┌─────────────────────────────────────────────────────┐
│  场景进度条 (SceneProgressBar)                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │  事件绑定系统 (Event Binding System)        │   │
│  │  - 鼠标悬停事件                              │   │
│  │  - 鼠标点击事件                              │   │
│  │  - 时间触发事件                              │   │
│  │  - 任务信息覆盖层                            │   │
│  └─────────────────────────────────────────────┘   │
│           ↓ 绑定到                                  │
│  ┌─────────────────────────────────────────────┐   │
│  │  场景层 (Scene Layer)                       │   │
│  │  - 场景元素 (树木、云朵、建筑等)             │   │
│  │  - 每个元素可配置事件                        │   │
│  │  - 支持本地/云端两种来源                     │   │
│  └─────────────────────────────────────────────┘   │
│           ↓ 叠加在                                  │
│  ┌─────────────────────────────────────────────┐   │
│  │  道路层 (Road Layer)                        │   │
│  │  - 平铺重复的道路素材                        │   │
│  │  - 作为进度条的基础轨道                      │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 2.2 核心概念澄清

#### ❌ 错误理解（之前）
```
事件层 = 独立的视觉层，用于显示任务标记、品牌道具
```

#### ✅ 正确理解（现在）
```
事件系统 = 对场景元素的交互配置
- 不是独立的视觉层
- 是场景元素的属性配置
- 定义元素的交互行为（悬停、点击、时间触发）
```

### 2.3 渲染流程

```python
def paintEvent(self, event):
    painter = QPainter(self)
    painter.setRenderHint(QPainter.Antialiasing)

    # 1. 绘制道路层（平铺）
    self._draw_road_layer(painter)

    # 2. 绘制场景层（场景元素）
    self._draw_scene_layer(painter)

    # 3. 绘制时间标记（当前时间指针）
    self._draw_time_marker(painter)

    # 注意：任务信息不在这里绘制，通过悬停显示QToolTip
```

---

## 3. 数据结构定义

### 3.1 场景配置文件结构

**文件路径**: `themes/{scene_id}/config.json`

```json
{
  "scene_id": "pixel_forest_v1",
  "name": "像素森林",
  "version": "1.0.0",
  "author": "GaiYa Team",
  "created_at": "2025-11-13",
  "description": "宁静的像素风格森林场景",

  "dimensions": {
    "height": 150,
    "road_height": 80
  },

  "layers": {
    "road": {
      "type": "tiled",
      "image": "themes/pixel_forest_v1/road_tile.png",
      "tile_width": 256,
      "y_position": 70
    },

    "scene": {
      "type": "positioned",
      "items": [
        {
          "id": "tree_left",
          "image": "themes/pixel_forest_v1/tree_1.png",
          "position_percent": 0.15,
          "y_position": 30,
          "z_index": 1,
          "source": "local",
          "events": null
        },

        {
          "id": "bench",
          "image": "themes/pixel_forest_v1/bench.png",
          "position_percent": 0.5,
          "y_position": 60,
          "z_index": 1,
          "source": "local",
          "events": [
            {
              "trigger": {
                "type": "on_time_reach",
                "time": "12:00"
              },
              "action": {
                "type": "show_tooltip",
                "content": "🍔 午休时间到啦！",
                "duration": 3000
              }
            },
            {
              "trigger": {
                "type": "on_hover"
              },
              "action": {
                "type": "show_dialog",
                "title": "休息区",
                "message": "这是一个舒适的长椅，适合午休"
              }
            }
          ]
        },

        {
          "id": "brand_slot_1",
          "position_percent": 0.42,
          "y_position": 65,
          "z_index": 2,
          "source": "cloud",
          "cloud_config": {
            "fetch_url": "https://api.gaiya.app/v1/scenes/pixel_forest_v1/brand-items/slot-1",
            "update_interval": 86400,
            "fallback_image": "themes/pixel_forest_v1/placeholder.png"
          },
          "events": []
        }
      ]
    }
  },

  "task_display": {
    "mode": "hover_overlay",
    "hover_style": {
      "show_tooltip": true,
      "tooltip_format": "{icon} {name}\n{start_time} - {end_time}",
      "background_color": "rgba(0, 0, 0, 180)",
      "text_color": "white",
      "font_size": 11,
      "border_radius": 4,
      "padding": 8
    }
  }
}
```

### 3.2 事件类型定义

#### 3.2.1 触发器类型 (Trigger)

| 类型 | 说明 | 参数 |
|------|------|------|
| `on_hover` | 鼠标悬停 | 无 |
| `on_click` | 鼠标点击 | 无 |
| `on_time_reach` | 时间标记到达 | `time`: "HH:MM" |

#### 3.2.2 动作类型 (Action)

| 类型 | 说明 | 参数 |
|------|------|------|
| `show_tooltip` | 显示气泡提示 | `content`, `duration` |
| `show_dialog` | 显示对话框 | `title`, `message` |
| `open_url` | 打开URL | `url`, `track` (是否统计) |

### 3.3 云端品牌元素API

#### 请求

```http
GET /api/v1/scenes/{scene_id}/brand-items/{slot_id}
```

#### 响应

```json
{
  "updated_at": "2025-11-13T06:00:00Z",
  "item": {
    "id": "starbucks_morning_cup",
    "image_url": "https://cdn.gaiya.app/brand/starbucks_cup.png",
    "events": [
      {
        "trigger": {
          "type": "on_click"
        },
        "action": {
          "type": "open_url",
          "url": "https://starbucks.com/promo?utm_source=gaiya",
          "track": true
        }
      },
      {
        "trigger": {
          "type": "on_hover"
        },
        "action": {
          "type": "show_tooltip",
          "content": "☕ 星巴客早安优惠券",
          "duration": 2000
        }
      }
    ]
  }
}
```

### 3.4 目录结构

```
themes/
├── pixel_forest_v1/
│   ├── config.json              # 场景配置文件
│   ├── preview.png              # 场景预览图（用于选择界面）
│   ├── road_tile.png            # 道路平铺素材（256x80px）
│   ├── tree_1.png               # 场景元素：树1
│   ├── tree_2.png               # 场景元素：树2
│   ├── cloud_1.png              # 场景元素：云1
│   ├── bench.png                # 场景元素：长椅
│   └── placeholder.png          # 品牌位占位符
│
├── city_night_v1/
│   ├── config.json
│   ├── ...
│
└── default/                      # 默认色块进度条（向后兼容）
    └── config.json
```

---

## 4. 技术实现方案

### 4.1 核心类设计

#### 4.1.1 SceneProgressBar (场景进度条主类)

```python
class SceneProgressBar(QWidget):
    """场景进度条主类"""

    def __init__(self, scene_config_path: str, tasks: list):
        super().__init__()
        self.scene_config = self.load_scene_config(scene_config_path)
        self.tasks = tasks
        self.scene_items = []
        self.cloud_items = []
        self.event_handlers = {}
        self.cached_pixmaps = {}

        self._init_scene_items()
        self._register_event_handlers()
        self._fetch_cloud_items()

    def load_scene_config(self, path: str) -> dict:
        """加载场景配置文件"""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _init_scene_items(self):
        """初始化场景元素"""
        for item_config in self.scene_config['layers']['scene']['items']:
            item = SceneItem(item_config, self)
            self.scene_items.append(item)

            if item.source == 'cloud':
                self.cloud_items.append(item)

    def _register_event_handlers(self):
        """注册事件处理器"""
        for item in self.scene_items:
            if not item.events:
                continue

            for event_config in item.events:
                trigger = event_config['trigger']
                action = event_config['action']

                if trigger['type'] == 'on_hover':
                    item.hover_action = action
                elif trigger['type'] == 'on_click':
                    item.click_action = action
                elif trigger['type'] == 'on_time_reach':
                    self.event_handlers[trigger['time']] = action

    def paintEvent(self, event):
        """绘制进度条"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        self._draw_road_layer(painter)
        self._draw_scene_layer(painter)
        self._draw_time_marker(painter)

    def _draw_road_layer(self, painter):
        """绘制道路层（平铺）"""
        road_config = self.scene_config['layers']['road']

        # 缓存道路图块
        if 'road_tile' not in self.cached_pixmaps:
            self.cached_pixmaps['road_tile'] = QPixmap(road_config['image'])

        tile_pixmap = self.cached_pixmaps['road_tile']
        tile_width = road_config['tile_width']
        y_pos = road_config['y_position']

        # 平铺绘制
        repeat_count = math.ceil(self.width() / tile_width)
        for i in range(repeat_count):
            painter.drawPixmap(i * tile_width, y_pos, tile_pixmap)

    def _draw_scene_layer(self, painter):
        """绘制场景层"""
        # 按z_index排序
        sorted_items = sorted(self.scene_items, key=lambda x: x.z_index)

        for item in sorted_items:
            if item.pixmap:
                x = item.position_percent * self.width()
                y = item.y_position
                painter.drawPixmap(int(x), y, item.pixmap)

    def _draw_time_marker(self, painter):
        """绘制当前时间标记"""
        current_time = QTime.currentTime()
        seconds = current_time.hour() * 3600 + current_time.minute() * 60 + current_time.second()
        time_percent = seconds / (24 * 3600)

        x = time_percent * self.width()

        # 绘制红色竖线
        painter.setPen(QPen(QColor(255, 0, 0), 2))
        painter.drawLine(int(x), 0, int(x), self.height())

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        # 检查是否悬停在场景元素上
        for item in self.scene_items:
            if item.contains_point(event.pos(), self.width()):
                if item.hover_action:
                    self.trigger_action(item.hover_action)
                    self.setCursor(Qt.PointingHandCursor)
                    return

        # 显示任务信息
        self.setCursor(Qt.ArrowCursor)
        self.show_task_overlay(event.pos())

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        for item in self.scene_items:
            if item.contains_point(event.pos(), self.width()):
                if item.click_action:
                    self.trigger_action(item.click_action)
                return

    def trigger_action(self, action: dict):
        """执行动作"""
        action_type = action['type']

        if action_type == 'show_tooltip':
            QToolTip.showText(
                QCursor.pos(),
                action['content'],
                self,
                QRect(),
                action.get('duration', 2000)
            )

        elif action_type == 'show_dialog':
            QMessageBox.information(
                self,
                action['title'],
                action['message']
            )

        elif action_type == 'open_url':
            QDesktopServices.openUrl(QUrl(action['url']))

            if action.get('track'):
                self.track_event('click', action['url'])

    def show_task_overlay(self, pos):
        """显示任务信息覆盖层"""
        time_percent = pos.x() / self.width()
        seconds = time_percent * 24 * 3600

        task = self.get_task_at_time(seconds)

        if task:
            overlay_config = self.scene_config['task_display']['hover_style']
            tooltip_format = overlay_config['tooltip_format']

            tooltip_text = tooltip_format.format(
                icon=task.get('icon', ''),
                name=task['name'],
                start_time=task['start_time'],
                end_time=task['end_time']
            )

            QToolTip.showText(
                self.mapToGlobal(pos),
                tooltip_text,
                self
            )

    def get_task_at_time(self, seconds: float) -> dict:
        """获取指定时间点的任务"""
        for task in self.tasks:
            if task['start_seconds'] <= seconds < task['end_seconds']:
                return task
        return None

    def check_time_triggers(self, current_time: QTime):
        """检查时间触发事件"""
        time_str = current_time.toString("HH:mm")

        if time_str in self.event_handlers:
            action = self.event_handlers[time_str]
            self.trigger_action(action)
```

#### 4.1.2 SceneItem (场景元素类)

```python
class SceneItem:
    """场景元素类"""

    def __init__(self, config: dict, parent_widget):
        self.id = config['id']
        self.position_percent = config['position_percent']
        self.y_position = config['y_position']
        self.z_index = config.get('z_index', 0)
        self.source = config.get('source', 'local')
        self.events = config.get('events', [])
        self.parent_widget = parent_widget

        # 加载图片
        if self.source == 'local':
            self.pixmap = QPixmap(config['image'])
        else:
            self.cloud_config = config['cloud_config']
            self.pixmap = QPixmap(self.cloud_config['fallback_image'])

        self.hover_action = None
        self.click_action = None

    def contains_point(self, pos: QPoint, parent_width: int) -> bool:
        """判断点是否在元素范围内（矩形碰撞检测）"""
        if not self.pixmap:
            return False

        x = self.position_percent * parent_width
        y = self.y_position
        w = self.pixmap.width()
        h = self.pixmap.height()

        return (x <= pos.x() <= x + w) and (y <= pos.y() <= y + h)
```

#### 4.1.3 CloudItemManager (云端元素管理器)

```python
class CloudItemManager:
    """云端元素管理器"""

    def __init__(self, parent_widget):
        self.parent = parent_widget
        self.cache = {}
        self.cache_file = 'cloud_items_cache.json'

        # 定时更新
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.check_updates)
        self.update_timer.start(3600000)  # 每小时检查一次

        self.load_cache()

    def fetch_cloud_item(self, item: SceneItem):
        """拉取云端元素（异步）"""
        url = item.cloud_config['fetch_url']

        # 使用QNetworkAccessManager进行异步请求
        manager = QNetworkAccessManager(self.parent)
        request = QNetworkRequest(QUrl(url))

        reply = manager.get(request)
        reply.finished.connect(
            lambda: self.on_fetch_completed(reply, item)
        )

    def on_fetch_completed(self, reply, item: SceneItem):
        """拉取完成回调"""
        if reply.error():
            print(f"云端元素拉取失败: {reply.errorString()}")
            return

        data = json.loads(reply.readAll().data().decode('utf-8'))

        # 下载图片
        self.download_image(data['item']['image_url'], item, data)

    def download_image(self, url: str, item: SceneItem, data: dict):
        """下载图片"""
        manager = QNetworkAccessManager(self.parent)
        request = QNetworkRequest(QUrl(url))

        reply = manager.get(request)
        reply.finished.connect(
            lambda: self.on_image_downloaded(reply, item, data)
        )

    def on_image_downloaded(self, reply, item: SceneItem, data: dict):
        """图片下载完成"""
        if reply.error():
            print(f"图片下载失败: {reply.errorString()}")
            return

        image_data = reply.readAll()
        pixmap = QPixmap()
        pixmap.loadFromData(image_data)

        # 更新元素
        item.pixmap = pixmap
        item.events = data['item']['events']

        # 重新注册事件
        self.parent._register_event_handlers()

        # 缓存
        self.cache[item.id] = {
            'updated_at': data['updated_at'],
            'image_data': image_data.toBase64().data().decode('utf-8'),
            'events': data['item']['events']
        }
        self.save_cache()

        # 触发重绘
        self.parent.update()

    def load_cache(self):
        """加载本地缓存"""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                self.cache = json.load(f)

    def save_cache(self):
        """保存缓存"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f)

    def check_updates(self):
        """检查更新"""
        for item in self.parent.cloud_items:
            self.fetch_cloud_item(item)
```

### 4.2 性能优化策略

#### 4.2.1 图层预缓存

```python
def _preload_pixmaps(self):
    """预加载所有图片到缓存"""
    # 道路层
    road_config = self.scene_config['layers']['road']
    self.cached_pixmaps['road_tile'] = QPixmap(road_config['image'])

    # 场景层
    for item in self.scene_items:
        if item.source == 'local' and item.pixmap:
            # 已经在初始化时加载
            pass
```

#### 4.2.2 脏矩形更新

```python
def update_scene_item(self, item: SceneItem):
    """只更新指定元素的区域"""
    x = int(item.position_percent * self.width())
    y = item.y_position
    w = item.pixmap.width()
    h = item.pixmap.height()

    self.update(QRect(x, y, w, h))
```

#### 4.2.3 帧率限制

```python
def __init__(self):
    # ...
    self.last_paint_time = 0
    self.min_frame_interval = 1000 / 30  # 30fps

def paintEvent(self, event):
    current_time = QTime.currentTime().msecsSinceStartOfDay()

    if current_time - self.last_paint_time < self.min_frame_interval:
        return

    self.last_paint_time = current_time

    # 正常绘制流程...
```

---

## 5. 用户交互流程

### 5.1 任务编辑流程（保持现有方式）

```
用户操作：
┌────────────────────────────────────────┐
│ 1. 右键托盘图标 → 打开配置管理器       │
│ 2. 在时间轴编辑器中拖动色块            │
│ 3. 点击保存                            │
└────────────────────────────────────────┘
                 ↓
┌────────────────────────────────────────┐
│ 桌面进度条显示：                       │
│                                        │
│ 如果选择"默认进度条":                  │
│   → 显示色块                           │
│                                        │
│ 如果选择"像素森林场景":                │
│   → 显示场景，不显示色块               │
│   → 鼠标悬停显示任务信息               │
└────────────────────────────────────────┘
```

### 5.2 场景模式下的任务信息查看

```
鼠标操作：
┌────────────────────────────────────────┐
│ 鼠标悬停在场景进度条上                 │
└────────────────────────────────────────┘
                 ↓
┌────────────────────────────────────────┐
│ 系统计算：                             │
│ - 鼠标位置 → 时间百分比                │
│ - 查找该时间点的任务                   │
└────────────────────────────────────────┘
                 ↓
┌────────────────────────────────────────┐
│ 显示QToolTip:                          │
│   ┌─────────────┐                      │
│   │ 📚 学习时间  │                      │
│   │ 10:00-12:00 │                      │
│   └─────────────┘                      │
└────────────────────────────────────────┘
```

### 5.3 场景元素交互

#### 示例1：悬停显示提示

```
鼠标悬停在"长椅"元素上
         ↓
触发 on_hover 事件
         ↓
显示QToolTip: "这是一个舒适的长椅，适合午休"
```

#### 示例2：点击打开链接

```
点击"星巴克杯子"元素
         ↓
触发 on_click 事件
         ↓
打开浏览器 → https://starbucks.com/promo
         ↓
上报点击数据 → 后台统计
```

#### 示例3：时间触发

```
当前时间到达 12:00
         ↓
触发 on_time_reach 事件
         ↓
显示QToolTip: "🍔 午休时间到啦！"
```

### 5.4 场景选择流程

```
配置管理器 → 主题设置 → 场景主题
         ↓
┌────────────────────────────────────────┐
│ ○ 默认进度条（色块样式）               │
│ ● 像素森林                             │
│ ○ 城市夜景                             │
│ ○ 海洋微风                             │
└────────────────────────────────────────┘
         ↓
应用场景 → 桌面进度条实时切换
```

### 5.5 限制说明（场景模式下）

在场景模式下，以下操作**不支持**：

- ❌ 在托盘菜单中直接编辑任务
- ❌ 在桌面进度条上拖动色块
- ❌ 在桌面进度条上调整任务时间

**原因**：场景是预设计的视觉效果，不提供可视化编辑接口。任务编辑仍需在配置管理器中进行。

---

## 6. 云端热更新机制

### 6.1 更新时机

采用**组合方案**：

1. **应用启动时拉取**（优先级最高）
   ```python
   def __init__(self):
       # ...
       self.cloud_manager = CloudItemManager(self)
       self.cloud_manager.fetch_all_on_startup()
   ```

2. **每24小时检查一次**
   ```python
   self.update_timer.start(86400000)  # 24小时
   ```

3. **手动刷新**（可选）
   ```python
   # 配置管理器中添加"刷新云端元素"按钮
   def refresh_cloud_items(self):
       self.cloud_manager.force_update()
   ```

### 6.2 缓存策略

#### 6.2.1 缓存文件格式

**文件路径**: `cloud_items_cache.json`

```json
{
  "last_update": "2025-11-13T06:00:00Z",
  "items": {
    "pixel_forest_v1_brand_slot_1": {
      "updated_at": "2025-11-13T06:00:00Z",
      "image_data": "iVBORw0KGgoAAAANS...",  // Base64编码
      "events": [...]
    }
  }
}
```

#### 6.2.2 缓存有效期判断

```python
def is_cache_valid(self, item_id: str) -> bool:
    """判断缓存是否有效"""
    if item_id not in self.cache:
        return False

    cached_item = self.cache['items'][item_id]
    updated_at = datetime.fromisoformat(cached_item['updated_at'])
    now = datetime.now()

    return (now - updated_at).total_seconds() < 86400  # 24小时
```

### 6.3 降级策略

当云端拉取失败时：

1. **使用本地缓存**（如果存在且未过期）
2. **使用占位符图片**（fallback_image）
3. **记录错误日志**，下次启动重试

```python
def fetch_cloud_item_with_fallback(self, item: SceneItem):
    """带降级策略的拉取"""
    try:
        self.fetch_cloud_item(item)
    except Exception as e:
        logging.error(f"云端拉取失败: {e}")

        # 尝试使用缓存
        if item.id in self.cache and self.is_cache_valid(item.id):
            self.load_from_cache(item)
        else:
            # 使用占位符
            item.pixmap = QPixmap(item.cloud_config['fallback_image'])
```

### 6.4 数据统计上报

```python
def track_event(self, event_type: str, url: str):
    """上报事件统计"""
    data = {
        'item_id': self.get_item_id_from_url(url),
        'user_id': self.get_hashed_user_id(),
        'action': event_type,
        'timestamp': datetime.now().isoformat()
    }

    # 异步上报
    self.analytics_queue.append(data)

    # 批量上报（每10条或每5分钟）
    if len(self.analytics_queue) >= 10:
        self.flush_analytics()
```

---

## 7. 分阶段实施计划（MVP聚焦版）

> **核心目标**：优先把编辑器和场景搭建跑通，云端热更新延后到Phase 5-6。

---

### Phase 1: 核心场景渲染 ⏱️ 3天

**目标**: 实现静态场景的道路平铺和场景元素定位

#### Day 1: 重构绘制逻辑
- [ ] 创建 `scene_renderer.py` 模块
- [ ] 实现 `SceneProgressBar` 基础类
- [ ] 实现道路层平铺逻辑
- [ ] 单元测试：不同窗口宽度下的平铺效果

#### Day 2: 场景元素定位
- [ ] 实现 `SceneItem` 类
- [ ] 场景元素按相对位置绘制
- [ ] z_index排序和分层绘制
- [ ] 单元测试：元素位置正确性

#### Day 3: 创建示例场景
- [ ] 设计"像素森林"场景
- [ ] 准备素材：道路、树木、云朵
- [ ] 编写 `pixel_forest_v1/config.json`
- [ ] 集成测试：完整场景渲染

**验收标准**:
- ✅ 道路正确平铺，无间隙
- ✅ 场景元素在正确的相对位置
- ✅ 帧率稳定在30fps以上
- ✅ 支持窗口宽度动态调整

**输出文件**:
- `scene_renderer.py`
- `themes/pixel_forest_v1/config.json`
- `themes/pixel_forest_v1/*.png`

---

### Phase 2: 可视化场景编辑器 ⏱️ 7天

**目标**: 开发图形化工具，实现场景的拖拽式设计和配置导出

> **⭐ 核心优先级**：这是整个系统的关键工具，优先开发确保设计师能快速产出场景。

#### Day 1-2: 编辑器UI框架

**技术选型**：
- **框架**: PySide6 (与主程序同栈，便于代码复用)
- **布局**: 三栏式布局（元素库 | 画布预览 | 属性面板）
- **画布**: QGraphicsView + QGraphicsScene（支持拖拽、缩放）

**UI布局设计**：
```
┌────────────────────────────────────────────────────────────┐
│  GaiYa 场景编辑器 v1.0                    [最小化] [最大化] [关闭]  │
├─────────┬──────────────────────────┬─────────────────────┤
│         │  工具栏                  │                     │
│         │  [新建] [保存] [导出]    │                     │
│         ├──────────────────────────┤                     │
│  素材库  │                          │    属性面板          │
│         │                          │                     │
│ 道路层   │    画布预览区域           │  ┌─ 基本信息 ─────┐│
│ ▼       │    (1200x150px)          │  │ 场景名称:       ││
│  road.png│                          │  │ [像素森林]      ││
│         │   [实时渲染的进度条]      │  │                 ││
│ 场景层   │                          │  │ 进度条高度:     ││
│ ▼       │                          │  │ [150] px        ││
│  tree.png│  [可拖拽的场景元素]      │  └─────────────────┘│
│  bench.png                          │                     │
│  cloud.png [可缩放、旋转]           │  ┌─ 选中元素 ─────┐│
│         │                          │  │ ID: tree_1      ││
│ [+导入]  │                          │  │ X位置: 15.0%    ││
│         │                          │  │ Y位置: 30 px    ││
│         │                          │  │ 缩放: 100%      ││
│         │                          │  │ Z轴: 1          ││
│         │                          │  │                 ││
│         │                          │  │ [+添加事件]     ││
│         │                          │  └─────────────────┘│
└─────────┴──────────────────────────┴─────────────────────┘
```

**Day 1任务**：
- [ ] 创建 `scene_editor.py` 主窗口
- [ ] 实现三栏布局（QSplitter）
- [ ] 元素库列表（QListWidget）
- [ ] 画布区域（QGraphicsView）
- [ ] 属性面板（QVBoxLayout + QFormLayout）

**Day 2任务**：
- [ ] 工具栏功能（新建、保存、导出）
- [ ] 文件对话框集成
- [ ] 场景配置加载/保存逻辑
- [ ] 基本样式美化

---

#### Day 3-4: 拖拽交互与元素操作

**核心功能**：
1. **素材导入**：
   ```python
   def import_asset(self, file_path: str):
       """导入PNG素材到元素库"""
       pixmap = QPixmap(file_path)
       item = QListWidgetItem(QIcon(pixmap), os.path.basename(file_path))
       item.setData(Qt.UserRole, file_path)  # 存储路径
       self.asset_list.addItem(item)
   ```

2. **拖拽到画布**：
   ```python
   class SceneCanvas(QGraphicsView):
       def dragEnterEvent(self, event):
           if event.mimeData().hasUrls():
               event.acceptProposedAction()

       def dropEvent(self, event):
           # 从元素库拖拽 or 从文件管理器拖拽
           pos = self.mapToScene(event.pos())
           self.add_scene_item(image_path, pos.x(), pos.y())
   ```

3. **元素可编辑操作**：
   - ✅ **拖动定位**：QGraphicsItem.setFlag(ItemIsMovable)
   - ✅ **缩放调整**：鼠标滚轮或句柄拖拽
   - ✅ **删除元素**：Delete键 or 右键菜单
   - ✅ **Z轴排序**：QGraphicsItem.setZValue()

**Day 3任务**：
- [ ] 实现素材导入功能（支持批量）
- [ ] 拖拽到画布功能
- [ ] 元素移动逻辑
- [ ] 实时坐标显示

**Day 4任务**：
- [ ] 缩放功能（Transform handle）
- [ ] 删除功能（键盘+右键菜单）
- [ ] Z轴调整（图层顺序）
- [ ] 撤销/重做功能（QUndoStack）

---

#### Day 5-6: 属性编辑与事件配置

**属性面板功能**：

1. **基本属性**：
   ```python
   # 自动同步：画布元素 ↔ 属性面板
   def on_item_selected(self, item: SceneItemGraphics):
       self.prop_id.setText(item.id)
       self.prop_x_percent.setValue(item.x_percent * 100)
       self.prop_y_pixel.setValue(item.y_pixel)
       self.prop_scale.setValue(item.scale * 100)
       self.prop_z_index.setValue(item.z_value)
   ```

2. **事件配置界面**：
   ```
   ┌─ 事件配置 ───────────────────┐
   │                             │
   │  已配置事件:                 │
   │  ┌───────────────────────┐ │
   │  │ ● on_hover → tooltip  │ │
   │  │ ● on_click → URL      │ │
   │  └───────────────────────┘ │
   │                             │
   │  [+ 添加新事件]              │
   │                             │
   │  ┌─ 新事件 ─────────────┐  │
   │  │ 触发器:               │  │
   │  │ ○ 鼠标悬停            │  │
   │  │ ● 鼠标点击            │  │
   │  │ ○ 时间到达            │  │
   │  │                       │  │
   │  │ 动作:                 │  │
   │  │ [▼ 打开URL]           │  │
   │  │ URL: [___________]    │  │
   │  │ □ 统计点击数          │  │
   │  │                       │  │
   │  │  [保存]  [取消]       │  │
   │  └───────────────────────┘  │
   └─────────────────────────────┘
   ```

**Day 5任务**：
- [ ] 属性面板双向绑定
- [ ] X/Y坐标实时同步
- [ ] 缩放比例调整
- [ ] Z轴排序UI

**Day 6任务**：
- [ ] 事件配置对话框
- [ ] 事件列表管理
- [ ] 事件类型选择器
- [ ] 动作参数配置

---

#### Day 7: 导出与场景预览

**导出功能**：

1. **JSON配置生成**：
   ```python
   def export_scene_config(self) -> dict:
       """将画布状态导出为config.json"""
       config = {
           "scene_id": self.scene_id,
           "name": self.scene_name,
           "version": "1.0.0",
           "layers": {
               "road": self.export_road_layer(),
               "scene": {
                   "items": [
                       item.to_config_dict()
                       for item in self.scene_items
                   ]
               }
           }
       }
       return config
   ```

2. **预览图生成**：
   ```python
   def generate_preview_image(self) -> QPixmap:
       """生成场景预览图（用于场景选择界面）"""
       pixmap = QPixmap(1200, 150)
       painter = QPainter(pixmap)
       self.scene.render(painter)
       painter.end()
       return pixmap
   ```

3. **资源打包**：
   ```python
   def export_scene_bundle(self, output_dir: str):
       """导出完整场景包"""
       # 1. 创建场景目录
       scene_dir = os.path.join(output_dir, self.scene_id)
       os.makedirs(scene_dir, exist_ok=True)

       # 2. 复制所有素材文件
       for item in self.scene_items:
           shutil.copy(item.image_path, scene_dir)

       # 3. 保存config.json
       config = self.export_scene_config()
       with open(f"{scene_dir}/config.json", 'w') as f:
           json.dump(config, f, indent=2)

       # 4. 生成预览图
       preview = self.generate_preview_image()
       preview.save(f"{scene_dir}/preview.png")
   ```

**Day 7任务**：
- [ ] JSON导出功能
- [ ] 预览图生成
- [ ] 场景资源打包
- [ ] 导出向导界面
- [ ] 配置文件验证

---

**Phase 2验收标准**：
- ✅ 可以通过拖拽上传素材到元素库
- ✅ 可以将素材拖拽到画布并自由定位
- ✅ 可以调整元素大小（缩放功能）
- ✅ 可以配置元素的交互事件
- ✅ 可以导出完整的`config.json`
- ✅ 可以生成场景预览图
- ✅ 导出的场景可以在主程序中正常渲染

**输出文件**：
- `scene_editor.py` - 主窗口
- `scene_canvas.py` - 画布组件
- `scene_item_graphics.py` - 可编辑场景元素
- `event_config_dialog.py` - 事件配置对话框
- `themes/example_scene/` - 示例场景（用于测试）

---

### Phase 3: 事件绑定系统 ⏱️ 4天

**目标**: 场景元素支持悬停、点击、时间触发等交互

#### Day 1: 事件配置解析
- [ ] 解析事件配置（trigger + action）
- [ ] 构建事件处理器映射表
- [ ] 单元测试：配置解析正确性

#### Day 2: 鼠标事件处理
- [ ] 实现碰撞检测（矩形方式）
- [ ] `mouseMoveEvent` - 悬停检测
- [ ] `mousePressEvent` - 点击检测
- [ ] 单元测试：鼠标事件响应

#### Day 3: 时间触发事件
- [ ] 定时器检查当前时间
- [ ] 触发 `on_time_reach` 事件
- [ ] 单元测试：时间触发准确性

#### Day 4: 动作执行
- [ ] 实现 `show_tooltip` 动作
- [ ] 实现 `show_dialog` 动作
- [ ] 实现 `open_url` 动作
- [ ] 集成测试：完整事件流程

**验收标准**:
- ✅ 鼠标悬停正确显示提示
- ✅ 点击元素触发对应动作
- ✅ 时间到达时自动触发事件
- ✅ 鼠标悬停时光标变为手型

**输出文件**:
- `scene_renderer.py` (更新)
- 测试用例文件

---

### Phase 4: 任务信息显示 ⏱️ 2天

**目标**: 鼠标悬停显示任务信息，替代色块显示

#### Day 1: 任务查询逻辑
- [ ] 实现 `get_task_at_time()` 方法
- [ ] 鼠标位置 → 时间百分比转换
- [ ] 单元测试：任务查询准确性

#### Day 2: 悬停覆盖层UI
- [ ] 使用QToolTip显示任务信息
- [ ] 样式配置（背景色、字体等）
- [ ] 格式化任务信息（icon + name + time）
- [ ] 集成测试：悬停显示效果

**验收标准**:
- ✅ 鼠标悬停正确显示任务
- ✅ 任务信息格式美观
- ✅ 无任务时不显示提示
- ✅ 样式与配置文件一致

**输出文件**:
- `scene_renderer.py` (更新)

---

### Phase 5: 云端热更新 ⏱️ 3天

**目标**: 品牌元素支持云端配置和每日更新

> **注**：此阶段优先级较低，可在MVP验证后实施。

#### Day 1: 云端拉取逻辑
- [ ] 创建 `CloudItemManager` 类
- [ ] 实现异步HTTP请求
- [ ] API调用和响应解析
- [ ] 单元测试：API调用成功

#### Day 2: 本地缓存机制
- [ ] 实现缓存读写
- [ ] 缓存有效期判断
- [ ] 降级策略（缓存→占位符）
- [ ] 单元测试：缓存逻辑

#### Day 3: 自动更新检查
- [ ] 启动时拉取云端元素
- [ ] 定时检查更新（24小时）
- [ ] 图片下载和元素更新
- [ ] 集成测试：完整更新流程

**验收标准**:
- ✅ 启动时成功拉取云端元素
- ✅ 缓存正确保存和读取
- ✅ 网络失败时正确降级
- ✅ 元素更新后自动刷新UI

**输出文件**:
- `cloud_item_manager.py`
- `cloud_items_cache.json` (示例)

---

### Phase 6: 集成到主程序 ⏱️ 2天

**目标**: 将场景进度条集成到主程序，提供场景选择功能

#### Day 1: 配置管理器集成
- [ ] 添加"场景主题"选项卡
- [ ] 场景列表展示（带预览图）
- [ ] 场景切换功能
- [ ] 保存场景选择到配置文件

#### Day 2: 主窗口集成
- [ ] 根据配置加载场景进度条
- [ ] 默认进度条 ↔ 场景进度条切换
- [ ] 任务数据同步
- [ ] 全流程测试

**验收标准**:
- ✅ 用户可以选择场景
- ✅ 切换场景即时生效
- ✅ 任务编辑功能正常
- ✅ 向后兼容默认进度条

**输出文件**:
- `main.py` (更新)
- `config_gui.py` (更新)

---

## 8. 已确认的技术决策

| 决策项 | 选择方案 | 确认日期 | 备注 |
|--------|----------|----------|------|
| **碰撞检测方式** | 矩形边界检测（简单高效） | 2025-11-13 | - |
| **云端更新频率** | 组合方案：启动拉取 + 24小时检查 | 2025-11-13 | - |
| **道路层渲染** | 平铺重复，动态适配宽度 | 2025-11-13 | - |
| **场景元素定位** | 相对位置百分比（0.0-1.0） | 2025-11-13 | - |
| **任务编辑方式** | 保持现有配置管理器，不在桌面进度条编辑 | 2025-11-13 | - |
| **事件系统架构** | 事件绑定到场景元素，非独立层 | 2025-11-13 | - |
| **性能目标** | 30fps稳定帧率 | 2025-11-13 | - |
| **开发优先级** | ⭐ **先编辑器+场景渲染，云端热更新延后** | 2025-11-13 | **核心聚焦点** |
| **场景编辑器方案** | ✅ **可视化编辑器（Qt桌面应用）** | 2025-11-13 | 拖拽式、所见即所得 |
| **元素尺寸限制** | ❌ **不限制固定尺寸，编辑器内可缩放** | 2025-11-13 | 设计师自由度高 |
| **配置文件位置** | 安装目录（`themes/`） | 2025-11-13 | 便于资源打包 |
| **品牌道具定向** | ❌ 暂时不需要区域/画像定向 | 2025-11-13 | 简化MVP需求 |
| **资源图片格式** | 仅支持PNG | 2025-11-13 | 后续可扩展SVG |
| **数据统计粒度** | 仅点击数统计 | 2025-11-13 | 不需要曝光时长等 |

---

## 9. 待讨论的问题（MVP后）

> **注**：以下问题优先级较低，在完成编辑器+场景渲染核心功能后再讨论。

### 9.1 产品设计（Phase 6+）

- [ ] **场景切换动画**
  - 是否需要平滑的过渡动画？
  - 淡入淡出 vs 无动画切换？

- [ ] **场景定价策略**
  - 部分场景免费，部分付费？
  - 会员专属场景？

- [ ] **用户自定义场景**
  - 是否允许用户上传自己设计的场景？
  - 场景分享社区？

### 9.2 运营相关（Phase 6+）

- [ ] **品牌合作流程**
  - 如何对接品牌方？
  - 投放数据如何展示给品牌方？

- [ ] **场景更新频率**
  - 多久推出一个新场景？
  - 节日主题场景（春节、圣诞等）？

### 9.3 技术扩展（Phase 6+）

- [ ] **DPI适配策略**
  - 是否需要多套尺寸适配不同DPI？
  - 自动缩放 vs 固定像素？

- [ ] **SVG矢量图支持**
  - 性能影响评估
  - 渲染质量对比

- [ ] **品牌元素审核机制**
  - 云端配置的品牌元素如何审核？
  - 是否需要敏感词过滤？

---

## 10. 更新日志

### v0.2.0 - 2025-11-13 ⭐ **核心决策确认版**

#### 确认的重大决策
- ✅ **场景编辑器方案**：采用可视化编辑器（Qt桌面应用）
- ✅ **元素尺寸策略**：不限制固定尺寸，编辑器内可自由缩放
- ✅ **配置文件位置**：安装目录（`themes/`）
- ✅ **资源格式**：仅支持PNG（暂不支持SVG）
- ✅ **数据统计粒度**：仅点击数（暂不需要曝光时长）
- ✅ **品牌道具定向**：暂不实施区域/画像定向

#### 调整的开发计划
- 📋 **优先级调整**：将可视化编辑器提升到Phase 2（从Phase 5提前）
- 📋 **云端热更新延后**：移至Phase 5（从Phase 4延后）
- 📋 **总工期调整**：从19天延长至21天（编辑器7天 vs 原5天）

#### 新增内容
- ✅ **Phase 2详细设计**：可视化编辑器完整技术方案（7天）
  - Day 1-2: UI框架（三栏布局）
  - Day 3-4: 拖拽交互与元素操作
  - Day 5-6: 属性编辑与事件配置
  - Day 7: 导出与场景预览
- ✅ **编辑器核心功能明确**：
  - 拖拽式元素定位
  - 实时缩放调整
  - 事件可视化配置
  - 完整场景包导出

#### 明确的聚焦点
- 🎯 **核心目标**：优先把编辑器和场景搭建跑通
- 🎯 **MVP范围**：Phase 1-4 + Phase 6（跳过Phase 5云端热更新）

---

### v0.1.0 - 2025-11-13

#### 新增
- ✅ 初始版本
- ✅ 完整的架构设计
- ✅ 数据结构定义
- ✅ 核心类实现方案
- ✅ 分阶段实施计划

#### 确认
- ✅ 碰撞检测方式：矩形边界
- ✅ 云端更新频率：组合方案
- ✅ 事件系统架构：绑定到场景元素

---

## 附录

### A. 参考资料

- [Qt QPainter 文档](https://doc.qt.io/qt-6/qpainter.html)
- [Qt 事件系统](https://doc.qt.io/qt-6/eventsandfilters.html)
- [JSON Schema 规范](https://json-schema.org/)

### B. 相关文件

- `QUICKREF.md` - 项目快速参考
- `DEV_CHECKLIST.md` - 开发检查清单
- `CLAUDE.md` - AI助手配置

### C. 联系方式

- 创始人微信: `drmrzhong`
- 项目仓库: https://github.com/jiamizhongshifu/jindutiao

---

**文档维护者**: Claude Code
**审核人**: @drmrzhong
**下次审核日期**: 2025-11-14
