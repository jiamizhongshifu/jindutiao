"""
Intelligent String Replacement Tool
Replaces hardcoded Chinese strings with tr() calls in config_gui.py
"""
import json
import re
from pathlib import Path

def load_translation_map():
    """Load the translation map from report"""
    with open('i18n_generation_report.json', 'r', encoding='utf-8') as f:
        report = json.load(f)
    return report['translation_map']

def is_already_translated(line, pos):
    """Check if this string is already in a tr() call"""
    # Look backwards to see if there's tr( before this string
    before = line[:pos]
    # Count parentheses balance
    paren_count = before.count('(') - before.count(')')
    # If tr( appears and we're inside it
    if 'tr(' in before[-100:]:
        # Check if we're inside the tr() call
        last_tr = before.rfind('tr(')
        if last_tr != -1:
            substr = before[last_tr:]
            open_paren = substr.count('(')
            close_paren = substr.count(')')
            if open_paren > close_paren:
                return True
    return False

def replace_in_file(filename, translation_map):
    """Replace hardcoded strings in a file"""
    print(f"Processing {filename}...")

    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')

    modified_lines = []
    replacements = []

    for line_num, line in enumerate(lines, 1):
        # Skip comments and docstrings
        stripped = line.strip()
        if stripped.startswith('#') or '"""' in line or "'''" in line:
            modified_lines.append(line)
            continue

        # Skip logger lines
        if 'logger.' in line or 'logging.' in line or 'print(' in line:
            modified_lines.append(line)
            continue

        modified_line = line

        # Find all Chinese strings in this line
        patterns = [
            (r'"([^"]*[\u4e00-\u9fff][^"]*)"', '"'),
            (r"'([^']*[\u4e00-\u9fff][^']*)'", "'"),
        ]

        for pattern, quote in patterns:
            matches = list(re.finditer(pattern, modified_line))

            # Process matches from right to left to preserve positions
            for match in reversed(matches):
                chinese = match.group(1)
                start_pos = match.start()

                # Skip if already translated
                if is_already_translated(modified_line, start_pos):
                    continue

                # Look up translation key
                if chinese in translation_map:
                    key = translation_map[chinese]

                    # Special handling for strings with formatting
                    if '{' in chinese and '}' in chinese:
                        # Keep format string but use tr()
                        # Example: f"{tr('key', var=value)}"
                        # For now, just replace simple cases
                        replacement = f"tr('{key}')"
                    elif ':' in chinese or '：' in chinese:
                        # Label with colon - replace
                        replacement = f"tr('{key}')"
                    else:
                        # Standard replacement
                        replacement = f"tr('{key}')"

                    # Replace in line
                    original = match.group(0)
                    modified_line = modified_line[:start_pos] + replacement + modified_line[match.end():]

                    replacements.append({
                        'line': line_num,
                        'original': chinese,
                        'key': key,
                        'before': line.strip()[:80],
                        'after': modified_line.strip()[:80]
                    })

        modified_lines.append(modified_line)

    # Write modified content
    output_file = filename.replace('.py', '_i18n.py')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(modified_lines))

    print(f"\nReplacement Summary:")
    print(f"  Total replacements: {len(replacements)}")
    print(f"  Output file: {output_file}")

    # Save replacement report
    report_file = 'replacement_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(replacements, f, ensure_ascii=False, indent=2)
    print(f"  Report saved to: {report_file}")

    # Show first 10 replacements
    print("\nFirst 10 replacements:")
    for i, rep in enumerate(replacements[:10], 1):
        print(f"{i}. Line {rep['line']}: {rep['original'][:40]} -> tr('{rep['key']}')")

    return len(replacements)

def main():
    print("=== Hardcoded String Replacement Tool ===\n")

    # Load translation map
    print("Loading translation map...")
    translation_map = load_translation_map()
    print(f"Loaded {len(translation_map)} translations\n")

    # Process config_gui.py
    count = replace_in_file('config_gui.py', translation_map)

    print(f"\n[OK] Replacement completed!")
    print(f"Modified file: config_gui_i18n.py")
    print(f"Next step: Review the changes and test")

if __name__ == '__main__':
    main()
