"""
Apply i18n to create_config_tab() method
Replaces all hardcoded Chinese strings with tr() function calls
"""

def apply_i18n():
    with open('config_gui.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Open log file for detailed output
    log = open('i18n_apply_log.txt', 'w', encoding='utf-8')

    # Replacements: (line_number (1-based), old_text, new_text)
    replacements = [
        # Group titles
        (1556, '        basic_group = QGroupBox("🔧 基本设置")',
               '        basic_group = QGroupBox(tr("config.basic_settings_title"))'),

        (1690, '        color_group = QGroupBox("🎨 颜色设置")',
               '        color_group = QGroupBox(tr("config.color_settings_title"))'),

        (1889, '        visual_group = QGroupBox("✨ 视觉效果")',
               '        visual_group = QGroupBox(tr("config.visual_effects_title"))'),

        # Height presets - SKIP for now, handle manually later
        # (1583, ...)

        # Custom label
        (1594, '        custom_label = QLabel("自定义:")',
               '        custom_label = QLabel(tr("config.custom_label"))'),

        # Form labels
        (1610, '        basic_layout.addRow("进度条高度:", height_container)',
               '        basic_layout.addRow(tr("config.bar_height_label"), height_container)'),

        (1620, '        basic_layout.addRow("显示器索引:", self.screen_spin)',
               '        basic_layout.addRow(tr("config.screen_index_label"), self.screen_spin)'),

        # Milliseconds suffix
        (1627, '        self.interval_spin.setSuffix(" 毫秒")',
               '        self.interval_spin.setSuffix(" " + tr("unit.milliseconds"))'),

        (1628, '        basic_layout.addRow("更新间隔:", self.interval_spin)',
               '        basic_layout.addRow(tr("config.update_interval_label"), self.interval_spin)'),

        # Auto start checkbox and tooltip
        (1635, '        self.autostart_check = QCheckBox("开机自动启动")',
               '        self.autostart_check = QCheckBox(tr("config.auto_start_at_boot"))'),

        (1636, '        self.autostart_check.setToolTip("勾选后，GaiYa每日进度条将在Windows开机时自动启动")',
               '        self.autostart_check.setToolTip(tr("config.auto_start_tooltip"))'),

        (1652, '        basic_layout.addRow("自启动:", autostart_container)',
               '        basic_layout.addRow(tr("config.auto_start_label"), autostart_container)'),

        # Choose color button
        (1702, '        self.bg_color_btn = QPushButton("选择颜色")',
               '        self.bg_color_btn = QPushButton(tr("btn.choose_color"))'),

        (1715, '        color_layout.addRow("背景颜色:", bg_color_layout)',
               '        color_layout.addRow(tr("config.background_color_label"), bg_color_layout)'),

        (1722, '        color_layout.addRow("背景透明度:", self.opacity_spin)',
               '        color_layout.addRow(tr("config.background_opacity_label"), self.opacity_spin)'),

        # Marker color
        (1730, '        self.marker_color_btn = QPushButton("选择颜色")',
               '        self.marker_color_btn = QPushButton(tr("btn.choose_color"))'),

        (1743, '        color_layout.addRow("时间标记颜色:", marker_color_layout)',
               '        color_layout.addRow(tr("config.marker_color_label"), marker_color_layout)'),

        # Pixels suffix
        (1750, '        self.marker_width_spin.setSuffix(" 像素")',
               '        self.marker_width_spin.setSuffix(" " + tr("unit.pixels"))'),

        (1751, '        color_layout.addRow("时间标记宽度:", self.marker_width_spin)',
               '        color_layout.addRow(tr("config.marker_width_label"), self.marker_width_spin)'),

        # Marker type hint
        (1763, '        marker_type_hint = QLabel("(line=线条, image=图片, gif=动画)")',
               '        marker_type_hint = QLabel(tr("config.marker_type_hint"))'),

        (1768, '        color_layout.addRow("时间标记类型:", marker_type_layout)',
               '        color_layout.addRow(tr("config.marker_type_label"), marker_type_layout)'),

        # Marker image placeholder and browse button
        (1774, '        self.marker_image_input.setPlaceholderText("选择图片文件 (JPG/PNG/GIF/WebP)")',
               '        self.marker_image_input.setPlaceholderText(tr("config.choose_image_file"))'),

        (1777, '        marker_image_btn = QPushButton("📁 浏览")',
               '        marker_image_btn = QPushButton(tr("btn.browse"))'),

        (1783, '        color_layout.addRow("标记图片:", marker_image_layout)',
               '        color_layout.addRow(tr("config.marker_image_label"), marker_image_layout)'),

        # Marker size presets - similar to height presets, need special handling
        # Lines 1798-1800 will be handled separately

        # Custom label (second occurrence)
        (1816, '        custom_size_label = QLabel("自定义:")',
               '        custom_size_label = QLabel(tr("config.custom_label"))'),

        (1831, '        color_layout.addRow("标记图片大小:", size_container)',
               '        color_layout.addRow(tr("config.marker_image_size_label"), size_container)'),

        # X offset hint
        (1843, '        x_offset_hint = QLabel("(正值向右,负值向左)")',
               '        x_offset_hint = QLabel(tr("config.x_offset_hint"))'),

        (1849, '        color_layout.addRow("标记图片 X 偏移:", x_offset_layout)',
               '        color_layout.addRow(tr("config.marker_image_x_offset_label"), x_offset_layout)'),

        # Y offset hint
        (1858, '        y_offset_hint = QLabel("(正值向上,负值向下)")',
               '        y_offset_hint = QLabel(tr("config.y_offset_hint"))'),

        (1864, '        color_layout.addRow("标记图片 Y 偏移:", y_offset_layout)',
               '        color_layout.addRow(tr("config.marker_image_y_offset_label"), y_offset_layout)'),

        # Animation speed hint
        (1874, '        animation_speed_hint = QLabel("(100%=原速, 200%=2倍速)")',
               '        animation_speed_hint = QLabel(tr("config.animation_speed_hint"))'),

        (1880, '        color_layout.addRow("动画播放速度:", animation_speed_layout)',
               '        color_layout.addRow(tr("config.animation_speed_label"), animation_speed_layout)'),

        # Shadow effect checkbox
        (1896, '        self.shadow_check = QCheckBox("启用阴影效果")',
               '        self.shadow_check = QCheckBox(tr("config.enable_shadow_effect"))'),

        # Corner radius pixels suffix
        (1905, '        self.corner_radius_spin.setSuffix(" 像素")',
               '        self.corner_radius_spin.setSuffix(" " + tr("unit.pixels"))'),

        (1906, '        visual_layout.addRow("圆角半径:", self.corner_radius_spin)',
               '        visual_layout.addRow(tr("config.corner_radius_label"), self.corner_radius_spin)'),
    ]

    # Apply replacements
    changes_made = 0
    for line_num, old_text, new_text in replacements:
        idx = line_num - 1  # Convert to 0-based
        if idx < len(lines):
            current_line = lines[idx].rstrip('\n')
            if current_line == old_text:
                lines[idx] = new_text + '\n'
                changes_made += 1
                log.write(f'[OK] Line {line_num}\n')
                print(f'[OK] Line {line_num}')
            else:
                log.write(f'[SKIP] Line {line_num}: Content mismatch\n')
                log.write(f'  Expected: {old_text}\n')
                log.write(f'  Found:    {current_line}\n\n')
                print(f'[SKIP] Line {line_num}')

    # Write back
    with open('config_gui.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)

    log.write(f'\n[SUCCESS] Made {changes_made} changes\n')
    log.close()

    print(f'\n[SUCCESS] Made {changes_made} changes')
    print('Details written to i18n_apply_log.txt')
    return changes_made

if __name__ == '__main__':
    count = apply_i18n()
    print(f'\nTotal changes: {count}')
