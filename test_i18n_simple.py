"""
Test i18n loading - Simple version without emoji
"""
import sys
from pathlib import Path

print("=== Testing i18n Module ===\n")

# Test 1: Can we import i18n?
try:
    import i18n
    from i18n import tr, get_language, set_language, get_available_languages
    print("[OK] i18n module imported successfully")
except ImportError as e:
    print(f"[ERROR] Failed to import i18n: {e}")
    sys.exit(1)

# Test 2: Check where i18n is looking for translation files
print(f"\ni18n module location: {i18n.__file__}")
i18n_dir = Path(i18n.__file__).parent
print(f"i18n directory: {i18n_dir}")
print(f"i18n directory exists: {i18n_dir.exists()}")

# Test 3: List translation files
print(f"\nSearching for *.json files in: {i18n_dir}")
json_files = list(i18n_dir.glob("*.json"))
print(f"Found {len(json_files)} JSON files:")
for f in json_files:
    print(f"  - {f.name} ({f.stat().st_size} bytes)")

# Test 4: Check available languages
available = get_available_languages()
print(f"\nAvailable languages: {available}")

# Test 5: Get current language
current = get_language()
print(f"Current language: {current}")

# Test 6: Try to switch to English
print("\n--- Switching to English ---")
success = set_language("en_US")
print(f"Switch to en_US: {'SUCCESS' if success else 'FAILED'}")
current = get_language()
print(f"Current language after switch: {current}")

# Test 7: Test actual translation
print("\n--- Testing Translations ---")
test_keys = [
    ('menu.config', 'Expected: Open Settings'),
    ('menu.quit', 'Expected: Quit'),
    ('button.save', 'Expected: Save'),
    ('button.cancel', 'Expected: Cancel'),
]

for key, expected in test_keys:
    result = tr(key)
    status = 'FOUND' if result != key else 'MISSING'
    print(f"[{status}] {key}: {result}")
    if expected:
        print(f"         {expected}")

# Test 8: Try switching back to Chinese
print("\n--- Switching to Chinese ---")
success = set_language("zh_CN")
print(f"Switch to zh_CN: {'SUCCESS' if success else 'FAILED'}")

for key, _ in test_keys[:2]:
    result = tr(key)
    print(f"  {key}: {result}")

print("\n=== Test Complete ===")
