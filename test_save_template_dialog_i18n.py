"""
Test SaveTemplateDialog i18n translations
验证SaveTemplateDialog的所有翻译是否正确
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import i18n module
from i18n import tr, set_language, get_language

def test_translations():
    """Test all SaveTemplateDialog translations"""
    print("=== SaveTemplateDialog I18n Test ===\n")

    # Set language to English
    set_language("en_US")
    current_lang = get_language()
    print(f"Current language: {current_lang}")
    print(f"Expected: en_US")
    print(f"Status: {'[OK] PASS' if current_lang == 'en_US' else '[FAIL] FAIL'}\n")

    # Test cases: (key, expected_en, expected_zh)
    test_cases = [
        # Window title
        ("dialog.save_template_title", "Save as Template", "保存为模板"),

        # Hint labels
        ("dialog.select_or_new", "Select a template to overwrite or enter a new name:", "选择要覆盖的模板或输入新的模板名称:"),
        ("dialog.enter_name", "Enter template name:", "请输入模板名称:"),

        # Placeholders
        ("tasks.template_4", "Select historical template or enter new name", "选择历史模板或输入新名称"),
        ("tasks.template_5", "Example: Weekday template", "例如: 工作日模板"),

        # Error messages
        ("message.input_error", "Input Error", "输入错误"),
        ("dialog.template_name_empty", "Template name cannot be empty!", "模板名称不能为空!"),
    ]

    print("=== Testing English Translations ===\n")
    set_language("en_US")

    all_passed = True
    for key, expected_en, _ in test_cases:
        result = tr(key)
        passed = result == expected_en
        all_passed = all_passed and passed

        status = "[OK]" if passed else "[FAIL]"
        print(f"{status} {key}")
        print(f"   Expected: {expected_en}")
        print(f"   Got:      {result}")
        if not passed:
            print(f"   [WARN]  MISMATCH!")
        print()

    print("=== Testing Chinese Translations ===\n")
    set_language("zh_CN")

    for key, _, expected_zh in test_cases:
        result = tr(key)
        passed = result == expected_zh
        all_passed = all_passed and passed

        status = "[OK]" if passed else "[FAIL]"
        print(f"{status} {key}")
        print(f"   Expected: {expected_zh}")
        print(f"   Got:      {result}")
        if not passed:
            print(f"   [WARN]  MISMATCH!")
        print()

    # Test parameter substitution
    print("=== Testing Parameter Substitution ===\n")
    set_language("en_US")

    result = tr('tasks.text_3308', template_name="Work Schedule", task_count=5)
    expected = "Work Schedule (5 tasks)"
    passed = result == expected
    all_passed = all_passed and passed

    status = "[OK]" if passed else "[FAIL]"
    print(f"{status} Dynamic text with parameters")
    print(f"   Key: tasks.text_3308")
    print(f"   Parameters: template_name='Work Schedule', task_count=5")
    print(f"   Expected: {expected}")
    print(f"   Got:      {result}")
    if not passed:
        print(f"   [WARN]  MISMATCH!")
    print()

    # Test Chinese parameter substitution
    set_language("zh_CN")
    result_zh = tr('tasks.text_3308', template_name="工作日程", task_count=5)
    expected_zh = "工作日程 (5个任务)"
    passed_zh = result_zh == expected_zh
    all_passed = all_passed and passed_zh

    status = "[OK]" if passed_zh else "[FAIL]"
    print(f"{status} Chinese dynamic text with parameters")
    print(f"   Expected: {expected_zh}")
    print(f"   Got:      {result_zh}")
    if not passed_zh:
        print(f"   [WARN]  MISMATCH!")
    print()

    # Final summary
    print("=" * 50)
    if all_passed:
        print("[OK] ALL TESTS PASSED! SaveTemplateDialog i18n is working correctly.")
    else:
        print("[FAIL] SOME TESTS FAILED! Please check the mismatches above.")
    print("=" * 50)

    return all_passed

if __name__ == "__main__":
    success = test_translations()
    sys.exit(0 if success else 1)
