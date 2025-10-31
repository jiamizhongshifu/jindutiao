@echo off
chcp 65001 > nul
echo ========================================
echo PyDayBar 打包脚本
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

echo [3/3] 开始打包...
echo.
echo 使用 PyInstaller 打包 (单目录模式)...
pyinstaller --clean ^
    --noconsole ^
    --name PyDayBar ^
    --add-data "config.json;." ^
    --add-data "tasks.json;." ^
    --hidden-import config_gui ^
    --hidden-import theme_manager ^
    --hidden-import theme_ai_helper ^
    --hidden-import timeline_editor ^
    --hidden-import statistics_manager ^
    --hidden-import statistics_gui ^
    main.py

echo.
echo ========================================
echo 打包完成！
echo ========================================
echo.
echo 可执行文件位置: dist\PyDayBar\PyDayBar.exe
echo.
echo 首次运行说明:
echo 1. 进入 dist\PyDayBar 目录
echo 2. 双击 PyDayBar.exe 运行程序
echo 3. 程序会在同目录下自动创建 config.json 和 tasks.json
echo.
echo 按任意键退出...
pause >nul
