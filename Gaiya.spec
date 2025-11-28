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
    'i18n.translator',  # 添加translator
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
        # 默认时间标记动图
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
        'PySide6.QtCharts',
        'PySide6.QtDataVisualization',
        'PySide6.QtPositioning',
        'PySide6.QtSensors',
        'PySide6.QtSerialPort',
        'PySide6.QtSql',
        'PySide6.QtTest',
        'PySide6.QtXml',

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
    upx=False,
    upx_exclude=[],
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