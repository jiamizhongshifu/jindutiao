# create_scene_tab() 国际化方案

## 方法范围

- **主方法**: `create_scene_tab()` (lines 2449-2623, 175 lines)
- **相关方法**:
  - `on_scene_changed()` (lines 2625-2627, 3 lines)
  - `update_scene_description()` (lines 2629-2659, 31 lines)
  - `open_scene_editor()` (lines 2661-2690, 30 lines)
  - `_on_scene_editor_closed()` (lines 2692-2699, 8 lines)
  - `_refresh_scene_list()` (lines 2701-2748, 48 lines)
- **总计**: 约295行代码

## 字符串统计

- **原始提取**: 39个中文字符串
- **文档字符串**: 6个（跳过）
- **用户可见字符串**: 33个
- **去重后**: 约29个唯一翻译键

## 翻译键规划

### 1. 分组标题 (Group Titles) - 3个

| 行号 | 原文 | 翻译键 | 变量名 |
|------|------|--------|--------|
| 2460 | ⚙️ 基础设置 | scene.basic_settings_title | basic_group |
| 2484 | 🎬 场景选择 | scene.scene_selection_title | scene_select_group |
| 2582 | 🛠️ 高级功能 | scene.advanced_features_title | advanced_group |

### 2. 标签文本 (Labels) - 2个

| 行号 | 原文 | 翻译键 | 变量名 |
|------|------|--------|--------|
| 2455 | 配置场景效果,让进度条更具个性化 | scene.info_label | info_label |
| 2491 | 当前场景: | scene.current_scene_label | scene_label |

### 3. 复选框文本 (Checkboxes) - 2个

| 行号 | 原文 | 翻译键 | 变量名 |
|------|------|--------|--------|
| 2466 | ���用场景系统 | scene.enable_scene_system | scene_enabled_check |
| 2474 | 依然展示进度条 | scene.show_progress_bar | show_progress_in_scene_check |

### 4. 提示文本 (Tooltips) - 3个

| 行号 | 原文 | 翻译键 | 变量名 |
|------|------|--------|--------|
| 2477 | 场景模式下在场景上方叠加显示进度条 | scene.progress_bar_tooltip | show_progress_in_scene_check.setToolTip |
| 2563 | 重新扫描scenes目录，加载新导出的场景 | scene.refresh_button_tooltip | refresh_button.setToolTip |
| 2613 | 场景编辑器可以创建和编辑自定义场景效果 | scene.editor_hint | editor_hint |

### 5. 下拉框选项 (Combo Box Items) - 2个

| 行号 | 原文 | 翻译键 | 使用位置 |
|------|------|--------|--------|
| 2517, 2518, 2721, 2722 | 无场景 | scene.no_scene | scene_combo.addItem (4处) |
| 2534 | 无可用场景 | scene.no_available_scenes | scene_combo.addItem |

### 6. 按钮文本 (Buttons) - 2个

| 行号 | 原文 | 翻译键 | 变量名 |
|------|------|--------|--------|
| 2543 | 🔄 刷新场景 | scene.btn_refresh_scenes | refresh_button |
| 2589 | 🎨 打开场景编辑器 | scene.btn_open_editor | open_scene_editor_btn |

### 7. 状态消息 (Status Messages) - 2个

| 行号 | 原文 | 翻译键 | 使用位置 |
|------|------|--------|--------|
| 2570 | 请选择一个场景 | scene.please_select_scene | scene_description_label.setText |
| 2641 | 未选择场景,将显示默认进度条样式 | scene.no_scene_selected | scene_description_label.setText |

### 8. 场景描述 (Scene Description) - 5个

| 行号 | 原文 | 翻译键 | 使用位置 |
|------|------|--------|--------|
| 2650 | 无描述 | scene.no_description | metadata.get('description', ...) |
| 2652 | 未知 | scene.unknown_author | metadata.get('author', ...) |
| 2654 | 描述: {description}\n版本: {version}  作者: {author} | scene.scene_info_format | desc_text |
| 2657 | 无法加载场景信息 | scene.cannot_load_info | scene_description_label.setText |
| 2659 | 场景管理器未初始化 | scene.manager_not_initialized | scene_description_label.setText |

### 9. 日志消息 (Logging Messages) - 5个

| 行号 | 原文 | 翻译键 | 使用位置 |
|------|------|--------|--------|
| 2682 | 场景编辑器已打开 | message.scene_editor_opened | logging.info |
| 2685 | 打开场景编辑器失败: {e} | message.error_open_editor | logging.error |
| 2695 | 场景编辑器已关闭 | message.scene_editor_closed | logging.info |
| 2740 | 场景列表已刷新,共 {len(scene_list)} 个场景 | message.scene_list_refreshed | logging.info |
| 2742 | 刷新场景列表失败: {e} | message.error_refresh_scenes | logging.error |

### 10. 错误对话框 (Error Dialogs) - 4个

| 行号 | 原文 | 翻译键 | 使用位置 |
|------|------|--------|--------|
| 2688 | 错误 | dialog.error | QMessageBox.critical (title) |
| 2689 | 打开场景编辑器失败:\n{str(e)}\n\n请检查日志文件获取详细信息 | message.error_open_editor_detail | QMessageBox.critical (message) |
| 2746 | 刷新失败 | dialog.refresh_failed | QMessageBox.critical (title) |
| 2747 | 刷新场景列表时出错:\n{e} | message.error_refresh_detail | QMessageBox.critical (message) |

## 翻译键总结

### scene命名空间 (20个)
- scene.basic_settings_title
- scene.scene_selection_title
- scene.advanced_features_title
- scene.info_label
- scene.current_scene_label
- scene.enable_scene_system
- scene.show_progress_bar
- scene.progress_bar_tooltip
- scene.refresh_button_tooltip
- scene.editor_hint
- scene.no_scene
- scene.no_available_scenes
- scene.btn_refresh_scenes
- scene.btn_open_editor
- scene.please_select_scene
- scene.no_scene_selected
- scene.no_description
- scene.unknown_author
- scene.scene_info_format
- scene.cannot_load_info
- scene.manager_not_initialized

### message命名空间 (7个)
- message.scene_editor_opened
- message.error_open_editor
- message.scene_editor_closed
- message.scene_list_refreshed
- message.error_refresh_scenes
- message.error_open_editor_detail
- message.error_refresh_detail

### dialog命名空间 (2个)
- dialog.error (可能已存在)
- dialog.refresh_failed

**总计**: 29个新翻译键

## 参数替换说明

以下翻译键包含参数替换：

1. **scene.scene_info_format**: `{description}`, `{version}`, `{author}`
2. **message.error_open_editor**: `{e}`
3. **message.scene_list_refreshed**: `{count}` (将 `{len(scene_list)}` 改为 `{count}`)
4. **message.error_refresh_scenes**: `{e}`
5. **message.error_open_editor_detail**: `{e}`
6. **message.error_refresh_detail**: `{e}`

## 实施步骤

1. **添加翻译键**: 将29个翻译键添加到 `i18n/zh_CN.json` 和 `i18n/en_US.json`
2. **创建自动替换脚本**: 处理简单的字符串替换
3. **手动修复**: 处理复杂的情况（如参数替换、多行代码）
4. **验证语法**: 确保所有修改后的代码仍然有效
5. **测试**: 切换语言测试所有场景相关功能

## 注意事项

1. **"错误"对话框标题**: `dialog.error` 可能已经在其他地方定义，���要检查是否复用
2. **无场景**: 出现4次，应使用同一个翻译键 `scene.no_scene`
3. **日志消息**: 虽然日志通常不需要国际化，但为了完整性，我们仍然将其包含
4. **场景信息格式化**: Line 2654的多行字符串需要特别处理

## 修改文件清单

- `config_gui.py`: 约33处修改（不含docstring）
- `i18n/zh_CN.json`: 添加29个键
- `i18n/en_US.json`: 添加29个键
