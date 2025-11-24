"""
Smart I18n Generator for config_gui.py
Automatically scans, categorizes, and generates translation keys
"""
import re
import json
from collections import defaultdict


class SmartI18nGenerator:
    def __init__(self):
        self.chinese_strings = []
        self.translation_map = {}
        self.existing_keys = set()

        # Load existing translations
        self.load_existing_translations()

        # Predefined translation mappings (high confidence)
        self.direct_mappings = {
            # Windows/Dialogs
            '配置': 'config.title',
            '保存为模板': 'dialog.save_template',
            '选择模板': 'dialog.select_template',
            '颜色选择器': 'dialog.color_picker',
            '时间选择': 'dialog.time_picker',

            # Buttons
            '确定': 'button.ok',
            '取消': 'button.cancel',
            '保存': 'button.save',
            '应用': 'button.apply',
            '重置': 'button.reset',
            '关闭': 'button.close',
            '删除': 'button.delete',
            '添加': 'button.add',
            '编辑': 'button.edit',
            '刷新': 'button.refresh',
            '预览': 'button.preview',
            '生成': 'button.generate',
            '导入': 'button.import',
            '导出': 'button.export',
            '选择': 'button.select',
            '清除': 'button.clear',
            '登录': 'account.login',
            '退出登录': 'account.logout',
            '注册': 'account.register',
            '升级会员': 'button.upgrade',
            '重试': 'button.retry',

            # Messages
            '提示': 'message.info',
            '警告': 'message.warning',
            '错误': 'message.error',
            '成功': 'message.success',
            '保存成功': 'message.save_success',
            '保存失败': 'message.save_failed',
            '加载成功': 'message.load_success',
            '加载失败': 'message.load_failed',
            '删除成功': 'message.delete_success',
            '操作成功': 'message.operation_success',
            '操作失败': 'message.operation_failed',
            '请稍候...': 'message.please_wait',
            '加载中...': 'message.loading',

            # Config - Tabs
            '外观设置': 'config.appearance',
            '任务管理': 'config.tasks',
            'AI功能': 'config.ai',
            '账号管理': 'config.account',
            '场景设置': 'config.scene',
            '关于': 'config.about',

            # Config - Fields (already exist)
            '语言': 'config.language',
            '进度条高度': 'config.bar_height',
            '进度条位置': 'config.bar_position',
            '顶部': 'config.position_top',
            '底部': 'config.position_bottom',
            '透明度': 'config.transparency',
            '背景颜色': 'config.background_color',
            '圆角大小': 'config.corner_radius',
            '阴影效果': 'config.shadow',
            '开机自启动': 'config.auto_start',
            '显示器': 'config.monitor',

            # Tasks
            '任务名称': 'tasks.name',
            '开始时间': 'tasks.start_time',
            '结束时间': 'tasks.end_time',
            '颜色': 'tasks.color',
            '添加任务': 'tasks.add_task',
            '编辑任务': 'tasks.edit_task',
            '删除任务': 'tasks.delete_task',
            '模板': 'tasks.template',
            '加载模板': 'tasks.load_template',
            '保存为模板': 'tasks.save_as_template',
            '主题配色': 'tasks.theme',
            '应用主题': 'tasks.apply_theme',

            # Account
            '未登录': 'account.not_logged_in',
            '邮箱': 'account.email',
            '密码': 'account.password',
            '验证码': 'account.verification_code',
            '发送验证码': 'account.send_code',

            # AI
            'AI生成任务': 'ai.generate_tasks',
            'AI配色推荐': 'ai.generate_theme',
            'AI正在生成中...': 'ai.generating',
            '生成成功': 'ai.generate_success',
            '生成失败': 'ai.generate_failed',

            # Membership
            '会员中心': 'membership.title',
            '免费版': 'membership.free',
            '月度会员': 'membership.pro_monthly',
            '年度会员': 'membership.pro_yearly',
            '当前套餐': 'membership.current_plan',
        }

    def load_existing_translations(self):
        """Load existing translation keys"""
        try:
            with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
                zh = json.load(f)

            # Flatten all keys
            def flatten(obj, prefix=''):
                for k, v in obj.items():
                    full_key = f"{prefix}.{k}" if prefix else k
                    if isinstance(v, dict):
                        flatten(v, full_key)
                    else:
                        self.existing_keys.add(full_key)

            flatten(zh)
            print(f"Loaded {len(self.existing_keys)} existing translation keys")
        except Exception as e:
            print(f"Warning: Could not load existing translations: {e}")

    def scan_file(self, filename):
        """Scan a file for Chinese strings"""
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, 1):
            # Skip comments and logger
            if line.strip().startswith('#') or 'logger.' in line or '"""' in line or "'''" in line:
                continue

            # Find Chinese strings
            patterns = [
                r'"([^"]*[\u4e00-\u9fff][^"]*)"',
                r"'([^']*[\u4e00-\u9fff][^']*)'",
            ]

            for pattern in patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    chinese = match.group(1)

                    # Skip if too long (likely descriptions)
                    if len(chinese) > 100:
                        continue

                    # Skip if part of tr() call
                    before = line[:match.start()]
                    if 'tr(' in before[-10:]:
                        continue

                    self.chinese_strings.append({
                        'line': line_num,
                        'text': chinese,
                        'context': line.strip()[:100]
                    })

        print(f"Found {len(self.chinese_strings)} Chinese strings in {filename}")

    def generate_translation_keys(self):
        """Generate translation keys for all Chinese strings"""
        # Count occurrences
        string_counts = defaultdict(int)
        for item in self.chinese_strings:
            string_counts[item['text']] += 1

        # Generate keys
        for chinese, count in string_counts.items():
            # Check direct mapping first
            if chinese in self.direct_mappings:
                key = self.direct_mappings[chinese]
                if key in self.existing_keys:
                    self.translation_map[chinese] = key
                    continue

            # Generate new key
            # Try to categorize
            category = self.categorize_string(chinese)

            # Create key name
            key_name = self.create_key_name(chinese)
            key = f"{category}.{key_name}"

            # Ensure uniqueness
            counter = 0
            original_key = key
            while key in self.existing_keys or key in [v for v in self.translation_map.values()]:
                counter += 1
                key = f"{original_key}_{counter}"

            self.translation_map[chinese] = key

        print(f"Generated {len(self.translation_map)} translation mappings")

    def categorize_string(self, text):
        """Categorize a string based on content"""
        # Keywords for categorization
        categories = {
            'config': ['设置', '配置', '高度', '宽度', '位置', '颜色', '透明', '圆角', '阴影'],
            'tasks': ['任务', '时间', '模板', '主题', '配色'],
            'dialog': ['对话', '选择', '确定', '取消'],
            'account': ['账号', '登录', '注册', '邮箱', '密码'],
            'ai': ['AI', '生成', '智能', '推荐'],
            'membership': ['会员', '套餐', '价格'],
            'message': ['提示', '警告', '错误', '成功', '失败'],
        }

        for cat, keywords in categories.items():
            if any(kw in text for kw in keywords):
                return cat

        return 'general'

    def create_key_name(self, text):
        """Create a key name from Chinese text"""
        # Remove special characters
        clean = re.sub(r'[^\u4e00-\u9fff\w]', '', text)

        # Use hash for unique identifier
        if len(clean) > 20:
            clean = clean[:20]

        # Create readable key
        key_map = {
            '设置': 'settings',
            '配置': 'config',
            '显示': 'display',
            '位置': 'position',
            '颜色': 'color',
            '大小': 'size',
            '时间': 'time',
            '任务': 'task',
            '模板': 'template',
            '主题': 'theme',
            '标记': 'marker',
            '图片': 'image',
            '动画': 'animation',
        }

        for cn, en in key_map.items():
            if cn in clean:
                return en

        # Fallback: use text hash
        return f"text_{abs(hash(clean)) % 10000}"

    def generate_new_translations(self):
        """Generate new translation entries"""
        new_zh = defaultdict(dict)
        new_en = defaultdict(dict)

        for chinese, key in self.translation_map.items():
            # Skip if already exists
            if key in self.existing_keys:
                continue

            # Split category and key_name
            parts = key.split('.', 1)
            if len(parts) != 2:
                continue

            category, key_name = parts

            # Add to new translations
            new_zh[category][key_name] = chinese
            new_en[category][key_name] = f"[TODO] {chinese}"  # Placeholder

        return dict(new_zh), dict(new_en)

    def save_translations(self, new_zh, new_en):
        """Save new translations to files"""
        # Load existing
        with open('i18n/zh_CN.json', 'r', encoding='utf-8') as f:
            zh = json.load(f)
        with open('i18n/en_US.json', 'r', encoding='utf-8') as f:
            en = json.load(f)

        # Merge new translations
        for category, translations in new_zh.items():
            if category not in zh:
                zh[category] = {}
            zh[category].update(translations)

        for category, translations in new_en.items():
            if category not in en:
                en[category] = {}
            en[category].update(translations)

        # Save
        with open('i18n/zh_CN.json', 'w', encoding='utf-8') as f:
            json.dump(zh, f, ensure_ascii=False, indent=2)
        with open('i18n/en_US.json', 'w', encoding='utf-8') as f:
            json.dump(en, f, ensure_ascii=False, indent=2)

        print(f"Updated translation files")

    def generate_report(self):
        """Generate a detailed report"""
        report = {
            'total_strings': len(self.chinese_strings),
            'unique_strings': len(set(item['text'] for item in self.chinese_strings)),
            'mappings': len(self.translation_map),
            'using_existing_keys': sum(1 for k in self.translation_map.values() if k in self.existing_keys),
            'new_keys_needed': sum(1 for k in self.translation_map.values() if k not in self.existing_keys),
            'translation_map': self.translation_map
        }

        with open('i18n_generation_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n=== Report ===")
        print(f"Total strings found: {report['total_strings']}")
        print(f"Unique strings: {report['unique_strings']}")
        print(f"Using existing keys: {report['using_existing_keys']}")
        print(f"New keys needed: {report['new_keys_needed']}")
        print(f"\nReport saved to: i18n_generation_report.json")


def main():
    print("=== Smart I18n Generator ===\n")

    generator = SmartI18nGenerator()

    # Step 1: Scan file
    print("\nStep 1: Scanning config_gui.py...")
    generator.scan_file('config_gui.py')

    # Step 2: Generate translation keys
    print("\nStep 2: Generating translation keys...")
    generator.generate_translation_keys()

    # Step 3: Generate new translations
    print("\nStep 3: Generating new translation entries...")
    new_zh, new_en = generator.generate_new_translations()

    print(f"New Chinese translations: {sum(len(v) for v in new_zh.values())} keys")
    print(f"New English translations: {sum(len(v) for v in new_en.values())} keys")

    # Step 4: Save translations
    if new_zh:
        print("\nStep 4: Saving translations...")
        generator.save_translations(new_zh, new_en)
    else:
        print("\nNo new translations needed!")

    # Step 5: Generate report
    print("\nStep 5: Generating report...")
    generator.generate_report()

    print("\n=== Generation Complete ===")


if __name__ == '__main__':
    main()
