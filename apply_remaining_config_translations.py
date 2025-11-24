#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply remaining config UI translations to config_gui.py"""

import re
import sys
import io
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Mapping of Chinese strings to translation keys
REPLACEMENTS = [
    # Tab titles (using addTab or setTabText)
    ('外观配置', 'config.tabs.appearance'),
    ('任务管理', 'config.tabs.tasks'),
    ('场景设置', 'config.tabs.scene'),
    ('通知设置', 'config.tabs.notifications'),
    ('关于', 'config.tabs.about'),

    # Basic settings labels
    ('显示带索引', 'config.labels.show_index'),
    ('更新间隔', 'config.labels.update_interval'),
    ('自启动', 'config.labels.autostart'),
    ('时间标记宽度', 'config.labels.marker_width'),
    ('时间标记类型', 'config.labels.marker_type'),
    ('标记图片 X 偏移', 'config.labels.marker_x_offset'),
    ('标记图片 Y 偏移', 'config.labels.marker_y_offset'),
    ('动画播放速度', 'config.labels.animation_speed'),

    # Task management
    ('AI智能规划', 'config.ai.title'),
    ('预设主题颜色', 'config.theme.title'),
    ('预设模板', 'config.templates.preset_label'),
    ('我的模板', 'config.templates.custom_label'),
    ('可视化时间编辑器', 'config.editor.title'),

    # Table headers
    ('开始时间', 'config.table.start_time'),
    ('结束时间', 'config.table.end_time'),
    ('任务名称', 'config.table.task_name'),
    ('背景颜色', 'config.table.bg_color'),
    ('文字颜色', 'config.table.text_color'),
    ('操作', 'config.table.actions'),

    # Notifications
    ('基础设置', 'config.notifications.basic_settings'),
    ('提醒时机', 'config.notifications.timing'),
    ('任务开始前提醒', 'config.notifications.before_start'),
    ('任务结束前提醒', 'config.notifications.before_end'),
    ('免打扰时段', 'config.notifications.dnd_title'),
    ('播放Info音', 'config.notifications.play_sound'),
]

def main():
    print("=" * 80)
    print("应用剩余配置界面翻译")
    print("=" * 80)
    print()

    config_path = Path('config_gui.py')

    # Read file
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Create backup
    backup_path = config_path.with_suffix('.py.backup_remaining_i18n')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ 备份已创建: {backup_path}")
    print()

    # Apply replacements
    replaced_count = 0

    for chinese_text, i18n_key in REPLACEMENTS:
        # Try different patterns
        patterns = [
            (f'"{chinese_text}"', f'self.i18n.tr("{i18n_key}")'),
            (f"'{chinese_text}'", f"self.i18n.tr('{i18n_key}')"),
        ]

        for old_pattern, new_pattern in patterns:
            if old_pattern in content:
                count = content.count(old_pattern)
                content = content.replace(old_pattern, new_pattern)
                replaced_count += count
                if count > 0:
                    print(f"✓ 替换 {count}处: {chinese_text}")

    print()
    print(f"总计替换: {replaced_count} 处")
    print()

    # Write back
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("✓ 文件已更新: config_gui.py")
    print()
    print("=" * 80)
    print("完成!")
    print("=" * 80)

if __name__ == '__main__':
    main()
