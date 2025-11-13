# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['scene_editor.py'],
    pathex=[],
    binaries=[],
    datas=[
        # 场景编辑器可能需要的资源文件（如果有的话）
    ],
    hiddenimports=[
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
    name='SceneEditor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # 禁用UPX压缩,减少杀毒软件误报
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 禁用控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='gaiya-logo2.ico',  # 使用GaiYa的图标
)
