# -*- mode: python ; coding: utf-8 -*-

# 导入版本信息
import sys
import os
# 将当前目录添加到 Python 路径，以便导入 version 模块
sys.path.insert(0, os.getcwd())
from version import get_exe_name

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # UI主题系统（浅色主题）
        ('gaiya/ui/', 'gaiya/ui/'),
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
    hiddenimports=[
        'config_gui',
        'theme_manager',
        'timeline_editor',
        'statistics_manager',
        'statistics_gui',
        'ai_client',  # AI客户端（调用Vercel云服务）
        'autostart_manager',  # 开机自启动管理器
        'requests',  # HTTP请求库
        'httpx',  # HTTP请求库（OpenSSL后端，解决schannel SSL兼容性问题）
        'httpcore',  # httpx依赖
        'h2',  # HTTP/2支持
        'h11',  # HTTP/1.1支持
        'anyio',  # 异步I/O支持
        'certifi',  # SSL证书
        'socks',  # PySocks（SOCKS5代理支持）
        'socksio',  # httpx的SOCKS5支持
        'winreg',  # Windows注册表操作
        'PySide6.QtWidgets',
        'PySide6.QtCore',
        'PySide6.QtGui',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # WebEngine相关（~280MB） - 浏览器引擎，应用不需要
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebEngineQuick',
        'PySide6.QtWebChannel',
        'PySide6.QtWebSockets',
        'PySide6.QtPdf',
        'PySide6.QtPdfWidgets',

        # QML/Quick相关（~20MB） - 声明式UI框架，应用使用传统Widget
        'PySide6.QtQuick',
        'PySide6.QtQuickControls2',
        'PySide6.QtQuickWidgets',
        'PySide6.QtQml',

        # 3D和多媒体（~15MB） - 3D渲染和多媒体功能
        'PySide6.QtQuick3D',
        'PySide6.Qt3DAnimation',
        'PySide6.Qt3DCore',
        'PySide6.Qt3DExtras',
        'PySide6.Qt3DInput',
        'PySide6.Qt3DLogic',
        'PySide6.Qt3DRender',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',

        # 设计和开发工具（~10MB） - 仅开发时使用
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
    name=get_exe_name(),  # 从 version.py 自动获取版本号
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # 禁用UPX压缩,减少杀毒软件误报
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 禁用控制台窗口，提供更好的用户体验
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Windows版本信息（暂时禁用，后续测试）
    # version='version_info.txt',
    icon='gaiya-logo2.ico',  # 应用图标
)
