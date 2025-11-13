# GaiYa 场景资源目录

此目录用于存放 GaiYa 进度条的场景配置和资源文件。

## 目录结构

```
scenes/
├── default/                  # 默认场景
│   ├── config.json          # 场景配置文件
│   ├── road.png             # 道路层图片
│   └── assets/              # 场景元素资源
│       ├── tree.png         # 树木图片
│       └── house.png        # 房屋图片
├── pixel_forest/            # 像素森林场景（示例）
│   ├── config.json
│   └── assets/
└── cyberpunk_city/          # 赛博朋克城市场景（示例）
    ├── config.json
    └── assets/
```

## 场景配置文件格式 (config.json)

```json
{
  "scene_id": "场景唯一ID",
  "name": "场景显示名称",
  "version": "1.0.0",
  "canvas": {
    "width": 1000,    // 画布宽度（进度条宽度）
    "height": 150     // 画布高度（进度条高度）
  },
  "layers": {
    "road": {         // 道路层（可选）
      "type": "tiled",
      "image": "road.png",     // 相对路径（相对于场景目录）
      "z_index": 50,           // 层级（0-100，默认50）
      "offset_x": 0,           // X偏移（像素）
      "offset_y": 0,           // Y偏移（像素）
      "scale": 1.0             // 缩放（1.0 = 100%）
    },
    "scene": {        // 场景层（必需）
      "items": [
        {
          "id": "元素唯一ID",
          "image": "tree.png",   // 相对路径（相对于 assets/ 目录）
          "position": {
            "x_percent": 20.0,   // X位置（百分比，0-100）
            "y_pixel": 50        // Y位置（像素）
          },
          "scale": 1.0,          // 缩放（1.0 = 100%）
          "z_index": 51,         // 层级（0-100）
          "events": [            // 事件列表（可选）
            {
              "trigger": "on_hover",  // 触发器类型
              "action": {
                "type": "show_tooltip",  // 动作类型
                "params": {
                  "text": "提示文本"
                }
              }
            }
          ]
        }
      ]
    }
  }
}
```

## 事件类型

### 触发器类型 (trigger)
- `on_hover`: 鼠标悬停
- `on_click`: 鼠标点击
- `on_time_reach`: 时间到达（进度到达指定百分比）

### 动作类型 (action.type)
- `show_tooltip`: 显示提示
  - params: `{"text": "提示文本"}`
- `show_dialog`: 显示对话框
  - params: `{"text": "对话框内容"}`
- `open_url`: 打开链接
  - params: `{"url": "https://example.com"}`

## Z-Index 层级系统

- **0-49**: 显示在道路层下方
- **50**: 道路层默认层级（可调整）
- **51-100**: 显示在道路层上方

场景元素默认 z-index 为 51（在道路上方）。

## 创建新场景

1. 在 `scenes/` 目录下创建新文件夹，例如 `my_scene/`
2. 在文件夹中创建 `config.json` 文件（参考上述格式）
3. 创建 `assets/` 子目录（如果需要场景元素）
4. 将道路图片放在 `my_scene/` 目录下
5. 将场景元素图片放在 `my_scene/assets/` 目录下
6. 在 GaiYa 配置界面中选择新场景

## 图片资源要求

- **道路图片**: PNG格式，建议高度与进度条高度一致（默认150px）
- **场景元素**: PNG格式，建议使用透明背景
- **文件大小**: 单张图片建议不超过 500KB
- **命名规范**: 使用英文小写字母、数字、下划线，例如 `tree_01.png`

## 打包说明

使用 PyInstaller 打包时：
- `scenes/` 目录应与打包后的 exe 文件放在同一目录
- 程序会自动检测并加载 `scenes/` 目录中的所有场景
- 支持在运行时动态添加新场景（无需重新打包）

## 性能优化

- 场景资源会在加载时预缓存到内存（QPixmap缓存）
- 建议场景元素数量不超过 20 个
- 建议单个场景的总图片资源不超过 10MB

## 示例场景

### default（默认场景）
- 包含道路层和 3 个场景元素（2棵树，1座房子）
- 演示了不同的 z-index 层级（45, 51, 52）
- 演示了悬停提示和点击对话框事件

### 更多场景示例
敬请期待...

---

**版本**: 1.0.0
**创建日期**: 2025-11-13
**兼容性**: GaiYa v1.5+
