#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix string concatenation issues from batch replacement
"""

import re

def fix_string_concatenation():
    """Fix multi-line string concatenation with tr() calls"""

    file_path = 'config_gui.py'

    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    changes_made = 0

    # Fix 1: ftr(...) should be f + tr(...)
    # This was an error from the regex replacement
    pattern1 = r'ftr\('
    matches1 = re.findall(pattern1, content)
    if matches1:
        print(f"Found {len(matches1)} ftr(...) patterns to fix")
        content = re.sub(pattern1, 'f" + tr(', content)
        changes_made += len(matches1)

    # Fix 2: Look for patterns where tr() is followed by a string literal without + operator
    # Pattern: tr("...") followed by whitespace and then "..." on next line
    # This is tricky because we need to add + before tr() in multi-line strings

    # For now, let me search for specific problematic lines and fix them manually
    # Pattern: ) + "\n" + tr( means we need + before tr(

    lines = content.split('\n')
    fixed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if line ends with tr("...") but next line starts with a string or f"
        if i < len(lines) - 1:
            # Pattern: line ends with tr("...") or tr("...") + "\n"
            # and next line starts with whitespace + "..." or f"..."
            if 'tr("' in line and not line.rstrip().endswith('+') and not line.rstrip().endswith('('):
                next_line = lines[i + 1].lstrip()
                if next_line.startswith('"') or next_line.startswith('f"'):
                    # Need to add + at end of current line or beginning of next
                    if line.rstrip().endswith(')'):
                        # Add + after the closing paren of tr()
                        line = line.rstrip() + ' +'
                        changes_made += 1

        fixed_lines.append(line)
        i += 1

    content = '\n'.join(fixed_lines)

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Made {changes_made} changes")
    print(f"File updated: {file_path}")

if __name__ == '__main__':
    print("Fixing string concatenation issues...")
    fix_string_concatenation()
    print("\nDone!")
