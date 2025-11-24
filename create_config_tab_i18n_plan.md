# create_config_tab() 国际化方案

## 字符串映射计划 (42个字符串)

### 1. 分组标题 (3个)

| 行号 | 原文 | 翻译键 | 状态 | 英文翻译 |
|------|------|--------|------|----------|
| 1556 | 🔧 基本设置 | config.basic_settings_title | 新建 | 🔧 Basic Settings |
| 1690 | 🎨 颜色设置 | config.color_settings_title | 新建 | 🎨 Color Settings |
| 1889 | ✨ 视觉效果 | config.visual_effects_title | 新建 | ✨ Visual Effects |

### 2. 表单标签 (15个)

| 行号 | 原文 | 翻译键 | 状态 | 英文翻译 |
|------|------|--------|------|----------|
| 1610 | 进度条高度: | config.bar_height_label | 新建 | Bar Height: |
| 1620 | 显示器索引: | config.screen_index_label | 新建 | Screen Index: |
| 1628 | 更新间隔: | config.update_interval_label | 新建 | Update Interval: |
| 1652 | 自启动: | config.auto_start_label | 新建 | Auto Start: |
| 1715 | 背景颜色: | config.background_color_label | 新建 | Background Color: |
| 1722 | 背景透明度: | config.background_opacity_label | 新建 | Background Opacity: |
| 1743 | 时间标记颜色: | config.marker_color_label | 新建 | Time Marker Color: |
| 1751 | 时间标记宽度: | config.marker_width_label | 新建 | Time Marker Width: |
| 1768 | 时间标记类型: | config.marker_type_label | 新建 | Time Marker Type: |
| 1783 | 标记图片: | config.marker_image_label | 新建 | Marker Image: |
| 1831 | 标记图片大小: | config.marker_image_size_label | 新建 | Marker Image Size: |
| 1849 | 标记图片 X 偏移: | config.marker_image_x_offset_label | 新建 | Marker Image X Offset: |
| 1864 | 标记图片 Y 偏移: | config.marker_image_y_offset_label | 新建 | Marker Image Y Offset: |
| 1880 | 动画播放速度: | config.animation_speed_label | 新建 | Animation Speed: |
| 1906 | 圆角半径: | config.corner_radius_label | 新建 | Corner Radius: |

### 3. 按钮文本 (2个 - 去重后)

| 行号 | 原文 | 翻译键 | 状态 | 英文翻译 |
|------|------|--------|------|----------|
| 1702, 1730 | 选择颜色 | btn.choose_color | 新建 | Choose Color |
| 1777 | 📁 浏览 | btn.browse | 新建 | 📁 Browse |

### 4. 复选框文本 (2个)

| 行号 | 原文 | 翻译键 | 状态 | 英文翻译 |
|------|------|--------|------|----------|
| 1635 | 开机自动启动 | config.auto_start_at_boot | 新建 | Launch at system startup |
| 1896 | 启用阴影效果 | config.enable_shadow_effect | 新建 | Enable shadow effect |

### 5. 提示/帮助文本 (6个)

| 行号 | 原文 | 翻译键 | 状态 | 英文翻译 |
|------|------|--------|------|----------|
| 1636 | 勾选后，GaiYa每日进度条将在Windows开机时自动启动 | config.auto_start_tooltip | 新建 | When checked, GaiYa progress bar will automatically start when Windows boots |
| 1763 | (line=线条, image=图片, gif=动画) | config.marker_type_hint | 新建 | (line=Line, image=Image, gif=Animated) |
| 1774 | 选择图片文件 (JPG/PNG/GIF/WebP) | config.choose_image_file | 新建 | Choose image file (JPG/PNG/GIF/WebP) |
| 1843 | (正值向右,负值向左) | config.x_offset_hint | 新建 | (Positive=Right, Negative=Left) |
| 1858 | (正值向上,负值向下) | config.y_offset_hint | 新建 | (Positive=Up, Negative=Down) |
| 1874 | (100%=原速, 200%=2倍速) | config.animation_speed_hint | 新建 | (100%=Normal, 200%=2x Speed) |

### 6. 预设选项 (7个)

#### 高度预设 (4个)

| 行号 | 原文 | 翻译键 | 状态 | 英文翻译 |
|------|------|--------|------|----------|
| 1575 | 极细 | config.preset_extra_thin | 新建 | Extra Thin |
| 1576 | 细 | config.preset_thin | 新建 | Thin |
| 1577 | 标准 | config.preset_standard | 新建 | Standard |
| 1578 | 粗 | config.preset_thick | 新建 | Thick |

#### 标记大小预设 (3个)

| 行号 | 原文 | 翻译键 | 状态 | 英文翻译 |
|------|------|--------|------|----------|
| 1798 | 小 | config.size_small | 新建 | Small |
| 1799 | 中 | config.size_medium | 新建 | Medium |
| 1800 | 大 | config.size_large | 新建 | Large |

### 7. 单位/后缀文本 (2个 - 去重后)

| 行号 | 原文 | 翻译键 | 状态 | 英文翻译 |
|------|------|--------|------|----------|
| 1627 | 毫秒 | unit.milliseconds | 新建 | ms |
| 1750, 1905 | 像素 | unit.pixels | 新建 | px |

### 8. 其他标签 (1个)

| 行号 | 原文 | 翻译键 | 状态 | 英文翻译 |
|------|------|--------|------|----------|
| 1594, 1816 | 自定义: | config.custom_label | 新建 | Custom: |

---

## 统计

- **总字符串数**: 42个
- **去重后唯一字符串**: 38个
- **需要新建的翻译键**: 38个
- **已存在的翻译键**: 0个（但config命名空间有90个相关键）

## 注意事项

1. **emoji图标**: 保留在翻译文本中，确保中英文一致
2. **带冒号的标签**: 英文翻译也保留冒号
3. **单位后缀**: 使用标准英文缩写（ms, px）
4. **提示文本**: 括号内的简洁说明，保持格式一致

## 实施步骤

1. 创建新的翻译键并添加到 i18n/zh_CN.json 和 i18n/en_US.json
2. 修改 config_gui.py 的 create_config_tab() 方法，将所有硬编码字符串替换为 tr() 调用
3. 测试中英文切换，确保所有文本正确显示
