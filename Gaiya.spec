# -*- mode: python ; coding: utf-8 -*-

# 导入版本信息
import sys
import os
import platform

# 将当前目录添加到 Python 路径，以便导入 version 模块
sys.path.insert(0, os.getcwd())
from version import get_exe_name, __app_name__, __version__

IS_MAC = platform.system() == 'Darwin'
IS_WIN = platform.system() == 'Windows'

# ========================================
# 动态依赖配置
# ========================================

hidden_imports = [
    'config_gui',
    'scene_editor',  # 场景编辑器（集成到主应用）
    'gaiya.core.theme_manager',
    'gaiya.utils.window_utils', # 新增：跨平台窗口工具
    'timeline_editor',
    'statistics_manager',
    'statistics_gui',
    'ai_client',  # AI客户端（调用Vercel云服务）
    'autostart_manager',  # 开机自启动管理器
    'gaiya.core',  # 添加gaiya.core包
    'gaiya.ui',  # 添加gaiya.ui包
    'gaiya.core.auth_client',  # 添加auth_client
    'gaiya.ui.auth_ui',  # 添加auth_ui
    'gaiya.ui.membership_ui',  # 添加membership_ui
    'gaiya.ui.pomodoro_panel',  # 番茄钟面板(红温专注仓)
    'gaiya.core.pomodoro_state',  # 番茄钟状态
    'gaiya.data.db_manager',  # 数据库管理器(专注会话)
    'i18n.translator',  # 添加translator
    'sqlite3',  # SQLite数据库支持
    'uuid',  # UUID生成
    'requests',  # HTTP请求库
    'httpx',  # HTTP请求库（OpenSSL后端，解决schannel SSL兼容性问题）
    'httpcore',  # httpx依赖
    'h2',  # HTTP/2支持
    'h11',  # HTTP/1.1支持
    'anyio',  # 异步I/O支持
    'certifi',  # SSL证书
    'socks',  # PySocks（SOCKS5代理支持）
    'socksio',  # httpx的SOCKS5支持
    'PySide6.QtWidgets',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtCharts',  # 图表库(用于统计报告趋势图)
    'PySide6.QtSvgWidgets',  # P0-1新增: SVG组件(用于FeatureCard图标)
    # jaraco 依赖 (pkg_resources需要)
    'jaraco',
    'jaraco.classes',
    'jaraco.functools',
    'jaraco.context',
    'jaraco.text',
    'more_itertools',
    'autocommand',  # jaraco.text依赖
    'backports.tarfile',  # jaraco.context依赖
    'platformdirs',  # pkg_resources依赖
]

# 平台特定依赖
if IS_WIN:
    hidden_imports.append('winreg')

if IS_MAC:
    # macOS特定库 (需要先安装 pyobjc)
    hidden_imports.extend(['objc', 'Foundation', 'AppKit'])

# 图标设置
icon_file = 'gaiya-logo2.ico'
if IS_MAC:
    # macOS应优先使用 .icns
    if os.path.exists('gaiya-logo2.icns'):
        icon_file = 'gaiya-logo2.icns'

# ========================================
# 分析配置
# ========================================

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # i18n internationalization files
        ('i18n/', 'i18n/'),
        # UI主题系统（浅色主题）
        ('gaiya/ui/', 'gaiya/ui/'),
        # 场景系统资源（打包默认场景到exe内部）
        ('scenes/default/', 'scenes/default/'),
        # 任务模板文件
        ('tasks_template_24h.json', '.'),
        ('tasks_template_workday.json', '.'),
        ('tasks_template_student.json', '.'),
        ('tasks_template_freelancer.json', '.'),
        ('tasks_template_night_shift.json', '.'),
        ('tasks_template_creator.json', '.'),
        ('tasks_template_fitness.json', '.'),
        ('tasks_template_entrepreneur.json', '.'),
        ('tasks_template_remote_work.json', '.'),
        ('tasks_template_part_time.json', '.'),
        ('tasks_template_weekend_relax.json', '.'),
        ('tasks_template_flexible.json', '.'),
        # 模板配置文件
        ('templates_config.json', '.'),
        # 标记图片预设资源（assets/markers目录）
        ('assets/markers/', 'assets/markers/'),
        # UI资源文件（复选框对勾图标）
        ('assets/checkmark.png', 'assets/'),
        # 新手引导SVG图标（P0-1新增）
        ('assets/icons/', 'assets/icons/'),
        # 弹幕预设内容库
        ('gaiya/data/danmaku_presets.json', 'gaiya/data/'),
        # 行为识别数据文件
        ('gaiya/data/behavior_danmaku.json', 'gaiya/data/'),
        ('gaiya/data/app_rules.json', 'gaiya/data/'),
        ('gaiya/data/domain_rules.json', 'gaiya/data/'),
        # AI场景预设配置文件
        ('gaiya/data/ai_scene_presets.json', 'gaiya/data/'),
        # 默认时间标记动图（向后兼容旧版本，保留根目录的kun.webp）
        ('kun.webp', '.'),
        ('kun.gif', '.'),
        ('kun_100x100.gif', '.'),
        # 微信二维码图片
        ('qun.jpg', '.'),
        # 应用Logo图片
        ('Gaiya-logo.png', '.'),
        ('Gaiya-logo-wbk.png', '.'),
        ('gaiya-logo2.png', '.'),
        ('gaiya-logo2-wbk.png', '.'),
        # AI客户端（调用Vercel云服务）
        ('ai_client.py', '.'),
        # 异步网络请求包装器
        ('gaiya/core/async_worker.py', 'gaiya/core/'),
        # 开机自启动管理器
        ('autostart_manager.py', '.'),
    ],
    hiddenimports=hidden_imports,
    hookspath=['.'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # ✅ 体积优化: 排除不需要的模块,减少打包体积

        # WebEngine相关（~280MB）
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebEngineQuick',
        'PySide6.QtWebChannel',
        'PySide6.QtWebSockets',
        'PySide6.QtPdf',
        'PySide6.QtPdfWidgets',

        # QML/Quick相关（~20MB）
        'PySide6.QtQuick',
        'PySide6.QtQuickControls2',
        'PySide6.QtQuickWidgets',
        'PySide6.QtQml',

        # 3D和多媒体（~15MB）
        'PySide6.QtQuick3D',
        'PySide6.Qt3DAnimation',
        'PySide6.Qt3DCore',
        'PySide6.Qt3DExtras',
        'PySide6.Qt3DInput',
        'PySide6.Qt3DLogic',
        'PySide6.Qt3DRender',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',

        # 设计和开发工具（~10MB）
        'PySide6.QtDesigner',
        'PySide6.QtUiTools',
        'PySide6.QtHelp',

        # 其他不需要的模块（~10MB）
        'PySide6.QtBluetooth',
        # 'PySide6.QtCharts',  # ❌ 已启用 - 用于统计报告趋势图
        'PySide6.QtDataVisualization',
        'PySide6.QtPositioning',
        'PySide6.QtSensors',
        'PySide6.QtSerialPort',
        'PySide6.QtSql',
        'PySide6.QtTest',
        'PySide6.QtXml',

        # P0-2新增: 额外可排除的模块（~3-5MB）
        # 'PySide6.QtNetwork',  # ❌ 已启用 - PaymentManager异步网络请求需要
        'PySide6.QtPrintSupport',  # 无打印功能
        'PySide6.QtOpenGL',  # 无3D OpenGL渲染需求
        'PySide6.QtOpenGLWidgets',

        # 数据科学库
        'matplotlib', 'scipy', 'pandas', 'sklearn', 'numpy.distutils',

        # 其他GUI库
        'tkinter', '_tkinter', 'PyQt5', 'PyQt6',

        # 测试框架
        'pytest', 'unittest', 'nose', '_pytest',

        # 文档生成
        'sphinx', 'docutils', 'jinja2',

        # 其他
        'IPython', 'notebook', 'jupyter',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=get_exe_name(),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # ✅ P0-2: 启用UPX压缩(预期减少25-30MB)
    upx_exclude=[
        # 排除Qt核心库,避免压缩后崩溃
        'Qt6Core.dll',
        'Qt6Gui.dll',
        'Qt6Widgets.dll',
        'Qt6Svg.dll',  # FeatureCard使用的SVG支持
        # 排除Python核心库
        'python*.dll',
        'vcruntime*.dll',
        # 排除可能导致问题的其他库
        'libcrypto*.dll',
        'libssl*.dll',
    ],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

# ========================================
# macOS BUNDLE 配置
# ========================================
if IS_MAC:
    app = BUNDLE(
        exe,
        name=f'{__app_name__}.app',
        icon=icon_file,
        bundle_identifier='com.gaiya.desktop',
        version=__version__,
        info_plist={
            'NSHighResolutionCapable': 'True',
            'LSBackgroundOnly': 'False',
            'CFBundleShortVersionString': __version__,
            'CFBundleVersion': __version__,
            'NSHumanReadableCopyright': 'Copyright © 2025 GaiYa Team. All rights reserved.',
        },
    )