#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""自动应用 create_scene_tab() 国际化修改"""

import re

# Read the file
with open('config_gui.py', 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')

# Track changes
changes_made = 0
skipped = []
log_messages = []

# Define replacements (line_number, old_string, new_string, description)
replacements = [
    # Group titles
    (2460, 'basic_group = QGroupBox("⚙️ 基础设置")',
     'basic_group = QGroupBox(tr("scene.basic_settings_title"))',
     "Basic settings group title"),

    (2484, 'scene_select_group = QGroupBox("🎬 场景选择")',
     'scene_select_group = QGroupBox(tr("scene.scene_selection_title"))',
     "Scene selection group title"),

    (2582, 'advanced_group = QGroupBox("🛠️ 高级功能")',
     'advanced_group = QGroupBox(tr("scene.advanced_features_title"))',
     "Advanced features group title"),

    # Labels
    (2455, 'info_label = QLabel("配置场景效果,让进度条更具个性化")',
     'info_label = QLabel(tr("scene.info_label"))',
     "Info label"),

    (2491, 'scene_label = QLabel("当前场景:")',
     'scene_label = QLabel(tr("scene.current_scene_label"))',
     "Current scene label"),

    # Checkboxes
    (2466, 'self.scene_enabled_check = QCheckBox("启用场景系统")',
     'self.scene_enabled_check = QCheckBox(tr("scene.enable_scene_system"))',
     "Enable scene system checkbox"),

    (2474, 'self.show_progress_in_scene_check = QCheckBox("依然展示进度条")',
     'self.show_progress_in_scene_check = QCheckBox(tr("scene.show_progress_bar"))',
     "Show progress bar checkbox"),

    # Tooltips
    (2477, 'self.show_progress_in_scene_check.setToolTip("场景模式下在场景上方叠加显示进度条")',
     'self.show_progress_in_scene_check.setToolTip(tr("scene.progress_bar_tooltip"))',
     "Progress bar tooltip"),

    (2563, 'refresh_button.setToolTip("重新扫描scenes目录，加载新导出的场景")',
     'refresh_button.setToolTip(tr("scene.refresh_button_tooltip"))',
     "Refresh button tooltip"),

    (2613, 'editor_hint = QLabel("场景编辑器可以创建和编辑自定义场景效果")',
     'editor_hint = QLabel(tr("scene.editor_hint"))',
     "Editor hint label"),

    # Combo box items
    (2517, 'self.scene_combo.addItem("无场景", None)',
     'self.scene_combo.addItem(tr("scene.no_scene"), None)',
     "No scene option 1"),

    (2518, 'self.scene_combo.addItem("无场景", None)',
     'self.scene_combo.addItem(tr("scene.no_scene"), None)',
     "No scene option 2"),

    (2534, 'self.scene_combo.addItem("无可用场景", None)',
     'self.scene_combo.addItem(tr("scene.no_available_scenes"), None)',
     "No available scenes option"),

    (2721, 'self.scene_combo.addItem("无场景", None)',
     'self.scene_combo.addItem(tr("scene.no_scene"), None)',
     "No scene option 3"),

    (2722, 'self.scene_combo.addItem("无场景", None)',
     'self.scene_combo.addItem(tr("scene.no_scene"), None)',
     "No scene option 4"),

    # Buttons
    (2543, 'refresh_button = QPushButton("🔄 刷新场景")',
     'refresh_button = QPushButton(tr("scene.btn_refresh_scenes"))',
     "Refresh scenes button"),

    (2589, 'self.open_scene_editor_btn = QPushButton("🎨 打开场景编辑器")',
     'self.open_scene_editor_btn = QPushButton(tr("scene.btn_open_editor"))',
     "Open editor button"),

    # Status messages
    (2570, 'self.scene_description_label = QLabel("请选择一个场景")',
     'self.scene_description_label = QLabel(tr("scene.please_select_scene"))',
     "Please select scene label"),

    (2641, 'self.scene_description_label.setText("未选择场景,将显示默认进度条样式")',
     'self.scene_description_label.setText(tr("scene.no_scene_selected"))',
     "No scene selected message"),

    # Scene description (needs special handling for metadata.get defaults)
    # Note: Lines 2650, 2652 will be handled manually due to .get() default values

    (2657, 'self.scene_description_label.setText("无法加载场景信息")',
     'self.scene_description_label.setText(tr("scene.cannot_load_info"))',
     "Cannot load info message"),

    (2659, 'self.scene_description_label.setText("场景管理器未初始化")',
     'self.scene_description_label.setText(tr("scene.manager_not_initialized"))',
     "Manager not initialized message"),

    # Logging messages
    (2682, 'logging.info("场景编辑器已打开")',
     'logging.info(tr("message.scene_editor_opened"))',
     "Editor opened log"),

    (2685, 'logging.error(f"打开场景编辑器失败: {e}", exc_info=True)',
     'logging.error(tr("message.error_open_editor", e=str(e)), exc_info=True)',
     "Error open editor log"),

    (2695, 'logging.info("场景编辑器已关闭")',
     'logging.info(tr("message.scene_editor_closed"))',
     "Editor closed log"),

    # Note: Line 2740 needs special handling for len(scene_list)

    (2742, 'logging.error(f"刷新场景列表失败: {e}", exc_info=True)',
     'logging.error(tr("message.error_refresh_scenes", e=str(e)), exc_info=True)',
     "Error refresh scenes log"),

    # Error dialogs
    (2688, '"错误",',
     'tr("dialog.error"),',
     "Error dialog title"),

    # Note: Lines 2689, 2746, 2747 need special handling for multi-line strings
]

# Apply replacements
for line_num, old_str, new_str, desc in replacements:
    idx = line_num - 1
    if idx < len(lines):
        original_line = lines[idx]
        if old_str in original_line:
            lines[idx] = original_line.replace(old_str, new_str)
            changes_made += 1
            log_messages.append(f"✓ Line {line_num}: {desc}")
        else:
            skipped.append((line_num, desc, "String not found in line"))
            log_messages.append(f"✗ Line {line_num}: {desc} - SKIPPED (string not found)")
    else:
        skipped.append((line_num, desc, "Line number out of range"))
        log_messages.append(f"✗ Line {line_num}: {desc} - SKIPPED (out of range)")

# Write back
with open('config_gui.py', 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(lines))

# Write log
with open('scene_i18n_apply_log.txt', 'w', encoding='utf-8') as f:
    f.write('=== Scene Tab Internationalization Application Log ===\n\n')
    f.write(f'Total replacements attempted: {len(replacements)}\n')
    f.write(f'Successful: {changes_made}\n')
    f.write(f'Skipped: {len(skipped)}\n\n')

    f.write('=== Detailed Log ===\n')
    for msg in log_messages:
        f.write(msg + '\n')

    if skipped:
        f.write('\n=== Skipped Items (Manual Fix Required) ===\n')
        for line_num, desc, reason in skipped:
            f.write(f'Line {line_num}: {desc} - {reason}\n')

    f.write('\n=== Manual Fixes Required ===\n')
    f.write('Line 2650: Replace metadata.get("description", "无描述") with metadata.get("description", tr("scene.no_description"))\n')
    f.write('Line 2652: Replace metadata.get("author", "未知") with metadata.get("author", tr("scene.unknown_author"))\n')
    f.write('Line 2654: Replace f"描述: {description}\\n版本: {version}  作者: {author}" with tr("scene.scene_info_format", ...)\n')
    f.write('Line 2689: Replace multi-line error message with tr("message.error_open_editor_detail", e=str(e))\n')
    f.write('Line 2740: Replace f"场景列表已刷新,共 {len(scene_list)} 个场景" with tr("message.scene_list_refreshed", count=len(scene_list))\n')
    f.write('Line 2746: Replace "刷新失败" with tr("dialog.refresh_failed")\n')
    f.write('Line 2747: Replace f"刷新场景列表时出错:\\n{e}" with tr("message.error_refresh_detail", e=str(e))\n')

print(f'Changes made: {changes_made}/{len(replacements)}')
print(f'Skipped: {len(skipped)}')
print(f'Log written to scene_i18n_apply_log.txt')
print(f'\nManual fixes required: 7 items')
print('Please check scene_i18n_apply_log.txt for details')
