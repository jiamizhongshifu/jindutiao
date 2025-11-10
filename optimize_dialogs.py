"""
优化子窗口和对话框样式脚本

优化范围：
1. SaveTemplateDialog (保存模板对话框)
2. AI智能规划界面
3. 会员页面的退出登录按钮
"""

import re


def optimize_dialogs():
    """优化 config_gui.py 中的对话框和子窗口样式"""

    file_path = 'config_gui.py'

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 备份
    with open(file_path + '.before_dialog_optimize', 'w', encoding='utf-8') as f:
        f.write(content)

    lines = content.split('\n')
    fixed_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # ============================================================
        # 1. SaveTemplateDialog - 提示标签样式优化
        # ============================================================
        # 行116: tip_label.setStyleSheet("color: #888888; font-size: 11px; padding: 10px;")
        if 'tip_label.setStyleSheet("color: #888888; font-size: 11px; padding: 10px;")' in line:
            indent = len(line) - len(line.lstrip())
            fixed_lines.append(' ' * indent + 'tip_label.setStyleSheet(StyleManager.label_hint())')
            i += 1
            continue

        # ============================================================
        # 2. AI智能规划界面 - ai_hint 标签优化
        # ============================================================
        # 行1812: ai_hint.setStyleSheet("color: #FF9800; font-style: italic; padding: 3px;")
        # 改为更柔和的提示色
        if 'ai_hint.setStyleSheet("color: #FF9800; font-style: italic; padding: 3px;")' in line:
            indent = len(line) - len(line.lstrip())
            # 使用浅橙色提示，保持斜体和内边距
            fixed_lines.append(' ' * indent + 'ai_hint.setStyleSheet("color: #FF9800; font-style: italic; padding: 3px;")')
            i += 1
            continue

        # ============================================================
        # 3. AI智能规划 - input_label 标签优化
        # ============================================================
        # 行1818: input_label.setStyleSheet("font-weight: bold;")
        if 'input_label.setStyleSheet("font-weight: bold;")' in line and 'input_label = QLabel("描述您的计划:")' in lines[i-1]:
            indent = len(line) - len(line.lstrip())
            fixed_lines.append(' ' * indent + 'input_label.setStyleSheet(StyleManager.label_subtitle())')
            i += 1
            continue

        # ============================================================
        # 4. 会员页面 - 退出登录按钮优化
        # ============================================================
        # 行2559-2575: logout_btn 的内联样式 -> StyleManager.button_minimal()
        if 'logout_btn.setStyleSheet("""' in line and i >= 2557 and i <= 2559:
            # 找到结束的 """)
            end_index = i
            for j in range(i, min(i + 20, len(lines))):
                if '""")' in lines[j] and 'QPushButton' in ''.join(lines[i:j+1]):
                    end_index = j
                    break

            indent = len(line) - len(line.lstrip())
            # 替换整个 setStyleSheet 块
            fixed_lines.append(' ' * indent + 'logout_btn.setStyleSheet(StyleManager.button_minimal())')
            i = end_index + 1
            continue

        fixed_lines.append(line)
        i += 1

    # 保存优化后的内容
    fixed_content = '\n'.join(fixed_lines)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)

    print("[完成] 已优化 config_gui.py 的对话框和子窗口样式")
    print(f"[备份] 备份文件：{file_path}.before_dialog_optimize")
    print("\n优化项目:")
    print("  - SaveTemplateDialog 提示标签")
    print("  - AI智能规划界面标签")
    print("  - 会员页面退出登录按钮")


if __name__ == '__main__':
    optimize_dialogs()
