"""
批量修复config_gui.py中的颜色问题

自动将白色文字改为深色，但保留套餐卡片区域的白色文字。
"""

import re


def fix_config_gui_colors():
    """修复config_gui.py中的颜色"""

    file_path = 'config_gui.py'

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 保存原始内容（备份）
    with open(file_path + '.backup', 'w', encoding='utf-8') as f:
        f.write(content)

    lines = content.split('\n')
    fixed_lines = []

    # 套餐卡片区域（保留白色文字）
    # _create_plan_card (2920-3011)
    # _create_featured_plan_card (3012-3165)
    # _create_lifetime_plan_card (3295-3450)
    card_ranges = [
        (2920, 3011),
        (3012, 3165),
        (3295, 3450)
    ]

    def is_in_card_area(line_num):
        """检查行号是否在卡片区域"""
        for start, end in card_ranges:
            if start <= line_num <= end:
                return True
        return False

    for i, line in enumerate(lines, 1):
        # 在卡片区域，保持原样
        if is_in_card_area(i):
            fixed_lines.append(line)
            continue

        original_line = line

        # 1. 修复QGroupBox标题颜色
        if 'QGroupBox::title' in line and 'color: white' in line:
            line = line.replace('color: white', 'color: #666666')

        # 2. 修复提示文字颜色
        if 'font-size: 9pt' in line or 'font-size: 8pt' in line or 'font-size: 11px' in line or 'font-size: 10px' in line:
            if 'color: white' in line:
                line = line.replace('color: white', 'color: #888888')

        # 3. 修复普通标签颜色
        if '.setStyleSheet(' in line and 'color: white' in line:
            # 排除按钮（按钮的白色文字通常在彩色背景上，保留）
            if 'background-color:' not in line:
                line = line.replace('color: white', 'color: #333333')

        # 4. 修复rgba白色为深色
        line = re.sub(
            r'color: rgba\(255,\s*255,\s*255,\s*0\.([0-9]+)\)',
            r'color: rgba(51, 51, 51, 0.\1)',
            line
        )

        # 5. 替换按钮样式
        # 绿色保存按钮
        if 'background-color: #4CAF50; color: white' in line:
            line = re.sub(
                r'setStyleSheet\("QPushButton \{ background-color: #4CAF50; color: white;[^}]*\}"\)',
                'setStyleSheet(StyleManager.button_primary())',
                line
            )

        # 蓝色按钮
        if 'background-color: #2196F3; color: white' in line:
            line = re.sub(
                r'setStyleSheet\("QPushButton \{ background-color: #2196F3; color: white;[^}]*\}"\)',
                'setStyleSheet(StyleManager.button_minimal())',
                line
            )

        # 红色删除按钮
        if 'background-color: #f44336; color: white' in line:
            line = re.sub(
                r'setStyleSheet\("QPushButton \{ background-color: #f44336; color: white;[^}]*\}"\)',
                'setStyleSheet(StyleManager.button_danger())',
                line
            )

        fixed_lines.append(line)

    # 保存修复后的内容
    fixed_content = '\n'.join(fixed_lines)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)

    print(f"[完成] 已修复config_gui.py")
    print(f"[备份] 备份文件：{file_path}.backup")


if __name__ == '__main__':
    fix_config_gui_colors()
