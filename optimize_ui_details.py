"""
UI细节优化脚本

优化config_gui.py中的：
1. 所有按钮样式（改为StyleManager）
2. 输入框样式
3. 表格样式
4. 字体大小统一
"""

import re


def optimize_config_gui():
    """优化config_gui.py的UI细节"""

    file_path = 'config_gui.py'

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 备份
    with open(file_path + '.before_optimize', 'w', encoding='utf-8') as f:
        f.write(content)

    lines = content.split('\n')
    fixed_lines = []

    for i, line in enumerate(lines, 1):
        original_line = line

        # ============================================================
        # 1. 优化橙色按钮（保存模板）-> 改为极简风格
        # ============================================================
        if 'background-color: #FF9800' in line and 'save_template_btn' in line:
            line = re.sub(
                r'setStyleSheet\("QPushButton \{[^}]+\}"\)',
                'setStyleSheet(StyleManager.button_minimal())',
                line
            )

        # ============================================================
        # 2. 优化紫色按钮（加载自定义）-> 改为极简风格
        # ============================================================
        if 'background-color: #9C27B0' in line:
            line = re.sub(
                r'setStyleSheet\("QPushButton \{[^}]+\}"\)',
                'setStyleSheet(StyleManager.button_minimal())',
                line
            )

        # ============================================================
        # 3. 优化模板按钮（保留颜色，但改为极简边框风格）
        # ============================================================
        # 这些是预设模板按钮，颜色有意义，改为边框风格
        if "btn.setStyleSheet(f\"QPushButton {{ background-color: {template['button_color']}" in line:
            # 改为边框风格：白底 + 彩色边框
            line = line.replace(
                "btn.setStyleSheet(f\"QPushButton {{ background-color: {template['button_color']}; color: white; padding: 6px; }}\")",
                "btn.setStyleSheet(f\"QPushButton {{ background-color: white; color: {template['button_color']}; border: 2px solid {template['button_color']}; border-radius: 6px; padding: 6px; }}\")"
            )

        # ============================================================
        # 4. 统一字体大小（去掉 15px 改为 14px）
        # ============================================================
        if 'font-size: 15px' in line:
            line = line.replace('font-size: 15px', 'font-size: 14px')

        # ============================================================
        # 5. 优化分组框标题样式（使用统一的副标题样式）
        # ============================================================
        if 'QGroupBox::title' in line and 'font-size: 14px' in line:
            # 确保分组框标题使用一致的颜色
            if '#666666' not in line:
                line = re.sub(
                    r'color: [^;]+;',
                    'color: #666666;',
                    line
                )

        fixed_lines.append(line)

    # 保存优化后的内容
    fixed_content = '\n'.join(fixed_lines)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)

    print(f"[完成] 已优化config_gui.py的UI细节")
    print(f"[备份] 备份文件：{file_path}.before_optimize")


if __name__ == '__main__':
    optimize_config_gui()
