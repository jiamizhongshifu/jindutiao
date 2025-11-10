"""
优化输入框和表格样式脚本

为 config_gui.py 中的所有输入框和表格组件应用 StyleManager 样式
"""

import re


def optimize_inputs_and_tables():
    """优化 config_gui.py 中的输入框和表格样式"""

    file_path = 'config_gui.py'

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 备份
    with open(file_path + '.before_input_optimize', 'w', encoding='utf-8') as f:
        f.write(content)

    lines = content.split('\n')
    fixed_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]
        fixed_lines.append(line)

        # ============================================================
        # 1. 优化 QSpinBox (数字输入框)
        # ============================================================
        if re.search(r'self\.\w+_spin\s*=\s*QSpinBox\(\)', line):
            # 检查下一行是否已经有 setStyleSheet
            if i + 1 < len(lines) and 'setStyleSheet' not in lines[i + 1]:
                # 获取缩进
                indent = len(line) - len(line.lstrip())
                fixed_lines.append(' ' * indent + 'self.' + re.search(r'self\.(\w+_spin)', line).group(1) + '.setStyleSheet(StyleManager.input_number())')

        # ============================================================
        # 2. 优化 QLineEdit (文本输入框)
        # ============================================================
        elif re.search(r'self\.\w+(_input|_edit)\s*=\s*QLineEdit\(\)', line):
            if i + 1 < len(lines) and 'setStyleSheet' not in lines[i + 1]:
                indent = len(line) - len(line.lstrip())
                var_name = re.search(r'self\.(\w+)', line).group(1)
                fixed_lines.append(' ' * indent + f'self.{var_name}.setStyleSheet(StyleManager.input_text())')

        # ============================================================
        # 3. 优化 QTimeEdit (时间输入框)
        # ============================================================
        elif re.search(r'self\.\w+_time\s*=\s*QTimeEdit\(\)', line) or re.search(r'\w+_time\s*=\s*QTimeEdit\(\)', line):
            if i + 1 < len(lines) and 'setStyleSheet' not in lines[i + 1]:
                indent = len(line) - len(line.lstrip())
                # 提取变量名
                match = re.search(r'(self\.)?(\w+_time)', line)
                if match:
                    prefix = match.group(1) or ''
                    var_name = match.group(2)
                    fixed_lines.append(' ' * indent + f'{prefix}{var_name}.setStyleSheet(StyleManager.input_time())')

        # ============================================================
        # 4. 优化 QComboBox (下拉框)
        # ============================================================
        elif re.search(r'self\.\w+_combo\s*=\s*QComboBox\(\)', line) or re.search(r'\w+_combo\s*=\s*QComboBox\(\)', line):
            if i + 1 < len(lines) and 'setStyleSheet' not in lines[i + 1]:
                indent = len(line) - len(line.lstrip())
                match = re.search(r'(self\.)?(\w+_combo)', line)
                if match:
                    prefix = match.group(1) or ''
                    var_name = match.group(2)
                    fixed_lines.append(' ' * indent + f'{prefix}{var_name}.setStyleSheet(StyleManager.dropdown())')

        # ============================================================
        # 5. 优化 QTableWidget (表格)
        # ============================================================
        elif re.search(r'self\.\w+_table\s*=\s*QTableWidget\(\)', line) or re.search(r'\w+\s*=\s*QTableWidget\(\)', line):
            if i + 1 < len(lines) and 'setStyleSheet' not in lines[i + 1]:
                indent = len(line) - len(line.lstrip())
                match = re.search(r'(self\.)?(\w+)', line)
                if match:
                    prefix = match.group(1) or ''
                    var_name = match.group(2).replace('_table', '_table').strip()
                    fixed_lines.append(' ' * indent + f'{prefix}{var_name}.setStyleSheet(StyleManager.table())')

        i += 1

    # 保存优化后的内容
    fixed_content = '\n'.join(fixed_lines)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)

    print("[完成] 已优化 config_gui.py 的输入框和表格样式")
    print(f"[备份] 备份文件：{file_path}.before_input_optimize")


if __name__ == '__main__':
    optimize_inputs_and_tables()
