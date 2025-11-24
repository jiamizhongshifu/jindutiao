#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Safely apply all i18n replacements with validation after each step
"""

import subprocess
import sys

def run_script(script_name):
    """Run a replacement script and return success status"""
    print(f"\n{'='*60}")
    print(f"Running: {script_name}")
    print('='*60)

    result = subprocess.run(['python', script_name], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    return result.returncode == 0

def validate_syntax():
    """Validate Python syntax"""
    result = subprocess.run(['python', '-m', 'py_compile', 'config_gui.py'],
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("✓ Syntax validation PASSED")
        return True
    else:
        print("✗ Syntax validation FAILED")
        print(result.stderr)
        return False

def main():
    # List of replacement scripts in safe order
    scripts = [
        'replace_common_ui_strings.py',
        'replace_schedule_strings.py',
        'replace_auth_strings.py',
        'replace_task_management_strings.py',
        'replace_membership_ui_supplement_strings.py',
        'replace_weekday_hardcoded_strings.py',
        'replace_updates_supplement_strings.py',
        'replace_common_ui_standalone_strings.py',
        'replace_simple_ui_strings.py',
    ]

    total_replacements = 0

    for script in scripts:
        if not run_script(script):
            print(f"\n✗ Failed to run {script}")
            sys.exit(1)

        # Validate syntax after each script
        if not validate_syntax():
            print(f"\n✗ Syntax error after running {script}")
            print("Stopping to prevent further issues")
            sys.exit(1)

    print("\n" + "="*60)
    print("✓ ALL REPLACEMENTS COMPLETED SUCCESSFULLY")
    print("="*60)
    print("\nFinal validation...")
    if validate_syntax():
        print("\n✓ Final syntax check PASSED")
    else:
        print("\n✗ Final syntax check FAILED")
        sys.exit(1)

if __name__ == '__main__':
    main()
