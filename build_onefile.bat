@echo off
chcp 65001 > nul
echo ========================================
echo Gaiya 单文件打包脚本
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
echo.
echo ⚠️  重要提示: 打包过程会清理 dist 目录！
echo    请确保用户数据文件（config.json, tasks.json, statistics.json 等）
echo    不在项目根目录的 dist 文件夹中，否则会被删除！
echo.
echo 等待 3 秒，按 Ctrl+C 取消...
timeout /t 3 /nobreak >nul
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
echo 清理完成
echo.

echo [3/3] 开始打包为单个EXE文件...
echo.
echo 注意: 使用 Gaiya.spec 文件进行打包，确保包含所有资源文件
echo 配置管理器已集成在主程序中，无需单独打包
echo.
pyinstaller --clean --noconfirm Gaiya.spec

echo.
echo ========================================
echo 打包完成！
echo ========================================
echo.
echo 可执行文件位置:
echo   - dist\Gaiya-v1.5.exe (主程序，包含集成配置管理器)
echo.
echo 使用说明:
echo 1. 将 Gaiya-v1.5.exe 复制到任意目录
echo 2. 双击运行，程序会自动创建配置文件
echo 3. 右键点击系统托盘图标选择"打开配置"即可打开配置管理器
echo.
echo 注意:
echo - 配置管理器已集成在主程序中，无需单独文件
echo - 单文件模式启动稍慢，但便于分发
echo.
echo 按任意键退出...
pause >nul
