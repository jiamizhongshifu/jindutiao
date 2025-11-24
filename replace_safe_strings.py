"""
Safe String Replacement - Only replace simple strings, skip f-strings
"""
import json
import re

def load_translation_map():
    with open('i18n_generation_report.json', 'r', encoding='utf-8') as f:
        report = json.load(f)
    return report['translation_map']

def is_in_fstring(line, pos):
    """Check if position is inside an f-string"""
    before = line[:pos]
    # Check for f" or f' before this position
    return bool(re.search(r'f["\']', before[-100:]))

def is_already_translated(line, pos):
    """Check if string is already in tr() call"""
    before = line[:pos]
    if 'tr(' in before[-100:]:
        last_tr = before.rfind('tr(')
        if last_tr != -1:
            substr = before[last_tr:]
            if substr.count('(') > substr.count(')'):
                return True
    return False

def replace_safe_strings(filename, translation_map):
    """Replace only safe, non-f-string occurrences"""
    print(f"Processing {filename} (safe mode)...")

    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    modified_lines = []
    safe_replacements = []
    skipped_fstrings = []

    for line_num, line in enumerate(lines, 1):
        # Skip comments, docstrings, logger
        stripped = line.strip()
        if (stripped.startswith('#') or '"""' in line or "'''" in line or
            'logger.' in line or 'logging.' in line or 'print(' in line):
            modified_lines.append(line)
            continue

        modified_line = line
        line_had_changes = False

        # Find Chinese strings
        patterns = [(r'"([^"]*[\u4e00-\u9fff][^"]*)"', '"'),
                   (r"'([^']*[\u4e00-\u9fff][^']*)'", "'")]

        for pattern, quote in patterns:
            matches = list(re.finditer(pattern, modified_line))

            for match in reversed(matches):
                chinese = match.group(1)
                start_pos = match.start()

                # Skip if in f-string
                if is_in_fstring(modified_line, start_pos):
                    skipped_fstrings.append({
                        'line': line_num,
                        'chinese': chinese,
                        'context': line.strip()[:100]
                    })
                    continue

                # Skip if already translated
                if is_already_translated(modified_line, start_pos):
                    continue

                # Look up key
                if chinese in translation_map:
                    key = translation_map[chinese]
                    replacement = f"tr('{key}')"

                    # Replace
                    modified_line = (modified_line[:start_pos] +
                                   replacement +
                                   modified_line[match.end():])

                    safe_replacements.append({
                        'line': line_num,
                        'original': chinese,
                        'key': key
                    })
                    line_had_changes = True

        modified_lines.append(modified_line)

    # Write output
    output_file = filename.replace('.py', '_i18n_safe.py')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(modified_lines)

    print(f"\nResults:")
    print(f"  Safe replacements: {len(safe_replacements)}")
    print(f"  Skipped f-strings: {len(skipped_fstrings)}")
    print(f"  Output: {output_file}")

    # Save reports
    with open('safe_replacements.json', 'w', encoding='utf-8') as f:
        json.dump(safe_replacements, f, ensure_ascii=False, indent=2)

    with open('skipped_fstrings.json', 'w', encoding='utf-8') as f:
        json.dump(skipped_fstrings, f, ensure_ascii=False, indent=2)

    print(f"  Reports: safe_replacements.json, skipped_fstrings.json")

    return len(safe_replacements), len(skipped_fstrings)

def main():
    print("=== Safe String Replacement Tool ===\n")

    translation_map = load_translation_map()
    print(f"Loaded {len(translation_map)} translations\n")

    safe_count, skipped_count = replace_safe_strings('config_gui.py', translation_map)

    print(f"\n[OK] Safe replacement completed!")
    print(f"Coverage: {safe_count}/(~{safe_count + skipped_count}) = {safe_count/(safe_count + skipped_count)*100:.1f}%")
    print(f"\nNext steps:")
    print(f"  1. Review config_gui_i18n_safe.py")
    print(f"  2. Handle f-strings separately")
    print(f"  3. Test the changes")

if __name__ == '__main__':
    main()
