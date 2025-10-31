@echo off
chcp 65001 > nul
echo ========================================
echo PyDayBar 单文件打包脚本
echo ========================================
echo.

echo [1/3] 检查 PyInstaller...
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo PyInstaller 未安装，正在安装...
    pip install pyinstaller
) else (
    echo PyInstaller 已安装
)
echo.

echo [2/3] 清理旧的构建文件...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
echo 清理完成
echo.

echo [3/3] 开始打包为单个EXE文件...
echo.
pyinstaller --clean ^
    --onefile ^
    --noconsole ^
    --name PyDayBar ^
    --hidden-import config_gui ^
    --hidden-import theme_manager ^
    --hidden-import theme_ai_helper ^
    --hidden-import timeline_editor ^
    --hidden-import statistics_manager ^
    --hidden-import statistics_gui ^
    main.py

echo.
echo 同时打包配置工具...
pyinstaller --clean ^
    --onefile ^
    --noconsole ^
    --name PyDayBar-Config ^
    --hidden-import theme_manager ^
    --hidden-import theme_ai_helper ^
    --hidden-import timeline_editor ^
    config_gui.py

echo.
echo ========================================
echo 打包完成！
echo ========================================
echo.
echo 可执行文件位置:
echo   - dist\PyDayBar.exe (主程序)
echo   - dist\PyDayBar-Config.exe (配置工具)
echo.
echo 使用说明:
echo 1. 将 PyDayBar.exe 复制到任意目录
echo 2. 双击运行，程序会自动创建配置文件
echo 3. 可选: 将 PyDayBar-Config.exe 也复制过去，用于可视化配置
echo.
echo 注意: 单文件模式启动稍慢，但便于分发
echo.
echo 按任意键退出...
pause >nul
