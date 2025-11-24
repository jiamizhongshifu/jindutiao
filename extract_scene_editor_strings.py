#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 scene_editor.py 提取所有中文字符串
"""

import re

def extract_strings():
    """提取字符串并分类"""

    file_path = 'scene_editor.py'

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取所有中文字符串（单引号和双引号）
    pattern = r'["\']([^"\']*[\u4e00-\u9fff][^"\']*)["\']'
    matches = re.findall(pattern, content)

    # 去重并保持顺序
    strings = []
    seen = set()
    for s in matches:
        if s not in seen and s.strip():
            strings.append(s)
            seen.add(s)

    # 分类字符串
    ui_strings = []  # UI可见字符串
    doc_strings = []  # 文档字符串
    log_strings = []  # 日志字符串
    other_strings = []  # 其他

    for s in strings:
        # 简单分类逻辑
        if any(keyword in s for keyword in ['按钮', '标签', '对话框', '窗口', '菜单', '工具栏', '选择', '确定', '取消', '保存', '加载', '导出', '删除', '添加', '编辑', '复制', '粘贴', '撤销', '重做']):
            ui_strings.append(s)
        elif any(keyword in s for keyword in ['功能', '创建', '版本', '说明', '描述']):
            doc_strings.append(s)
        elif any(keyword in s for keyword in ['日志', '错误', '警告', '成功', '失败']):
            log_strings.append(s)
        else:
            # 根据长度判断
            if len(s) <= 50:
                ui_strings.append(s)
            else:
                doc_strings.append(s)

    # 输出到文件
    output_file = 'scene_editor_strings_raw.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"从 {file_path} 中提取到 {len(strings)} 个唯一的中文字符串\n")
        f.write(f"- UI可见字符串: {len(ui_strings)} 个\n")
        f.write(f"- 文档字符串: {len(doc_strings)} 个\n")
        f.write(f"- 日志字符串: {len(log_strings)} 个\n")
        f.write(f"- 其他字符串: {len(other_strings)} 个\n\n")
        f.write("="*80 + "\n\n")

        # 查找字符串在文件中的行号
        lines = content.split('\n')

        def find_line(s):
            for line_num, line in enumerate(lines, 1):
                if s in line:
                    return line_num
            return 0

        f.write("=== 所有字符串（按出现顺序）===\n\n")
        for i, s in enumerate(strings, 1):
            line_num = find_line(s)
            # 限制长度以便阅读
            display_s = s if len(s) <= 80 else s[:77] + "..."
            f.write(f"{i}. (Line {line_num}) {display_s}\n")

    print(f"提取完成! 共找到 {len(strings)} 个唯一的中文字符串")
    print(f"- UI可见字符串: {len(ui_strings)} 个")
    print(f"- 文档字符串: {len(doc_strings)} 个")
    print(f"- 日志字符串: {len(log_strings)} 个")
    print(f"- 其他字符串: {len(other_strings)} 个")
    print(f"结果已保存到: {output_file}")

if __name__ == '__main__':
    extract_strings()
