#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复config_gui.py中的语法错误
"""

import re

def fix_syntax_errors(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 修复ftr(已经完成

    # 修复多行字符串连接中间有tr()调用的情况
    # 例如：
    #   "text1\n"
    #   "text2\n"
    #   tr("key")
    # 应该改为：
    #   "text1\n"
    #   "text2\n" +
    #   tr("key")

    # 查找模式：字符串字面量后面直接跟tr(，但没有+
    # 使用正则表达式查找这种模式并添加 +
    content = re.sub(
        r'("\n)\s*(tr\()',
        r'\1 +\n                \2',
        content
    )

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("Fixed syntax errors")

if __name__ == '__main__':
    fix_syntax_errors('config_gui.py')
