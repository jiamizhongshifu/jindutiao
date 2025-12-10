"""
推理规则库 (Inference Rules)

定义常见应用使用模式的推理规则
用于 AutoInferenceEngine 自动识别任务类型

规则结构:
{
    '规则名称': {
        'apps': [应用列表],                  # 主应用
        'concurrent_apps': [并发应用列表],   # 经常同时使用的应用 (可选)
        'domains': [域名列表],               # 网站域名 (可选,未来扩展)
        'task_name': '任务名称',
        'type': '任务类型',                  # work/learning/life/entertainment
        'confidence': 置信度                 # 0.0-1.0
    }
}
"""

INFERENCE_RULES = {
    # ==================== 开发相关 ====================
    'coding_python': {
        'apps': ['pycharm', 'vscode', 'cursor'],  # 添加 Cursor 支持
        'concurrent_apps': ['chrome', 'firefox', 'edge'],
        'domains': ['github.com', 'stackoverflow.com', 'localhost'],
        'task_name': 'Python开发',
        'type': 'work',
        'confidence': 0.92
    },

    'coding_web': {
        'apps': ['vscode', 'sublime text', 'webstorm', 'cursor'],  # 添加 Cursor 支持
        'concurrent_apps': ['chrome', 'firefox'],
        'domains': ['github.com', 'stackoverflow.com', 'localhost'],
        'task_name': 'Web开发',
        'type': 'work',
        'confidence': 0.90
    },

    'coding_java': {
        'apps': ['idea', 'intellij', 'eclipse'],
        'concurrent_apps': ['chrome', 'firefox'],
        'task_name': 'Java开发',
        'type': 'work',
        'confidence': 0.92
    },

    'coding_mobile': {
        'apps': ['android studio', 'xcode'],
        'task_name': '移动应用开发',
        'type': 'work',
        'confidence': 0.95
    },

    'git_operations': {
        'apps': ['github desktop', 'sourcetree', 'gitkraken'],
        'task_name': '代码版本管理',
        'type': 'work',
        'confidence': 0.88
    },

    # ==================== 办公文档 ====================
    'document_writing': {
        'apps': ['word', 'winword', 'wps'],
        'task_name': '文档编写',
        'type': 'work',
        'confidence': 0.85
    },

    'presentation': {
        'apps': ['powerpoint', 'powerpnt', 'wpp'],
        'task_name': 'PPT制作',
        'type': 'work',
        'confidence': 0.90
    },

    'spreadsheet': {
        'apps': ['excel', 'et'],
        'task_name': '表格处理',
        'type': 'work',
        'confidence': 0.85
    },

    'note_taking': {
        'apps': ['notion', 'onenote', 'evernote', 'obsidian', 'typora', 'joplin'],
        'task_name': '笔记整理',
        'type': 'work',
        'confidence': 0.82
    },

    'pdf_reading': {
        'apps': ['acrobat', 'foxit', 'pdf reader', 'sumatra'],
        'task_name': '文档阅读',
        'type': 'learning',
        'confidence': 0.80
    },

    # ==================== 设计创作 ====================
    'ui_design': {
        'apps': ['figma', 'sketch', 'xd', 'adobe xd'],
        'task_name': 'UI设计',
        'type': 'work',
        'confidence': 0.92
    },

    'graphic_design': {
        'apps': ['photoshop', 'illustrator', 'affinity'],
        'task_name': '平面设计',
        'type': 'work',
        'confidence': 0.90
    },

    'video_editing': {
        'apps': ['premiere', 'after effects', 'final cut', 'davinci'],
        'task_name': '视频剪辑',
        'type': 'work',
        'confidence': 0.93
    },

    '3d_modeling': {
        'apps': ['blender', 'maya', '3ds max', 'cinema 4d'],
        'task_name': '3D建模',
        'type': 'work',
        'confidence': 0.95
    },

    # ==================== 会议沟通 ====================
    'video_meeting': {
        'apps': ['zoom', 'teams', 'microsoft teams', 'webex'],
        'task_name': '视频会议',
        'type': 'work',
        'confidence': 0.95
    },

    'im_chat': {
        'apps': ['wechat', 'weixin', 'dingtalk', 'feishu', 'slack', 'discord'],
        'task_name': '即时沟通',
        'type': 'work',
        'confidence': 0.85
    },

    'email': {
        'apps': ['outlook', 'thunderbird', 'mailbird', 'foxmail'],
        'task_name': '邮件处理',
        'type': 'work',
        'confidence': 0.88
    },

    # ==================== 数据分析 ====================
    'data_analysis': {
        'apps': ['jupyter', 'rstudio', 'spss', 'tableau'],
        'task_name': '数据分析',
        'type': 'work',
        'confidence': 0.90
    },

    'database': {
        'apps': ['navicat', 'datagrip', 'dbeaver', 'sql server', 'mysql workbench'],
        'task_name': '数据库管理',
        'type': 'work',
        'confidence': 0.92
    },

    # ==================== 学习研究 ====================
    'online_learning': {
        'apps': ['chrome', 'firefox', 'edge'],
        'domains': [
            'coursera.org', 'udemy.com', 'edx.org', 'bilibili.com/video',
            'youtube.com/watch', 'mooc.org', 'xuetangx.com'
        ],
        'task_name': '在线学习',
        'type': 'learning',
        'confidence': 0.85
    },

    'research': {
        'apps': ['zotero', 'mendeley', 'endnote'],
        'concurrent_apps': ['chrome', 'firefox', 'pdf reader'],
        'task_name': '学术研究',
        'type': 'learning',
        'confidence': 0.88
    },

    # ==================== 娱乐休闲 ====================
    'gaming': {
        'apps': ['steam', 'epic games', 'origin', 'uplay', 'league of legends', 'dota 2'],
        'task_name': '游戏娱乐',
        'type': 'entertainment',
        'confidence': 0.95
    },

    'music': {
        'apps': ['spotify', 'apple music', 'qq music', 'netease music', 'foobar2000'],
        'task_name': '音乐欣赏',
        'type': 'entertainment',
        'confidence': 0.90
    },

    'video_streaming': {
        'apps': ['chrome', 'firefox', 'edge'],
        'domains': [
            'youtube.com/watch', 'bilibili.com/video', 'netflix.com',
            'iqiyi.com', 'youku.com', 'v.qq.com'
        ],
        'task_name': '视频娱乐',
        'type': 'entertainment',
        'confidence': 0.88
    },

    # ==================== 系统工具 ====================
    'terminal': {
        'apps': ['cmd', 'powershell', 'terminal', 'iterm', 'wsl', 'git bash'],
        'task_name': '终端操作',
        'type': 'work',
        'confidence': 0.85
    },

    'file_management': {
        'apps': ['explorer', 'total commander', 'directory opus', 'finder'],
        'task_name': '文件管理',
        'type': 'neutral',
        'confidence': 0.75
    },

    # ==================== 通用浏览 ====================
    'web_browsing': {
        'apps': ['chrome', 'firefox', 'edge', 'safari', 'opera', 'brave'],
        'task_name': '网页浏览',
        'type': 'neutral',
        'confidence': 0.70
    },

    # ==================== 内容创作 ====================
    'blogging': {
        'apps': ['typora', 'obsidian', 'notion', 'bear'],
        'concurrent_apps': ['chrome', 'firefox'],
        'task_name': '内容写作',
        'type': 'work',
        'confidence': 0.83
    },

    'screen_recording': {
        'apps': ['obs', 'camtasia', 'screen flow', 'bandicam'],
        'task_name': '录屏/直播',
        'type': 'work',
        'confidence': 0.92
    },
}


# ==================== 辅助函数 ====================

def get_rule_by_app(app_name: str):
    """根据应用名称查找匹配的规则"""
    app_lower = app_name.lower()

    for rule_name, rule in INFERENCE_RULES.items():
        # 检查主应用列表
        if any(app.lower() in app_lower or app_lower in app.lower()
               for app in rule.get('apps', [])):
            return rule

    return None


def get_all_task_types():
    """获取所有任务类型"""
    types = set()
    for rule in INFERENCE_RULES.values():
        types.add(rule['type'])
    return sorted(types)


def get_rules_by_type(task_type: str):
    """获取指定类型的所有规则"""
    return {
        name: rule
        for name, rule in INFERENCE_RULES.items()
        if rule['type'] == task_type
    }
