@echo off
echo ========================================
echo GaiYa 重新打包脚本
echo ========================================
echo.

echo [1/4] 等待文件解锁...
timeout /t 2 /nobreak >nul

echo [2/4] 清理旧文件...
if exist dist\GaiYa-v1.6.exe.old del /F /Q dist\GaiYa-v1.6.exe.old 2>nul
if exist dist\GaiYa-v1.6.exe (
    echo 尝试重命名旧文件...
    ren dist\GaiYa-v1.6.exe GaiYa-v1.6.exe.old 2>nul
    if exist dist\GaiYa-v1.6.exe.old (
        del /F /Q dist\GaiYa-v1.6.exe.old 2>nul
    )
)

if exist build (
    echo 清理 build 目录...
    rmdir /s /q build 2>nul
)

echo.
echo [3/4] 开始打包...
pyinstaller Gaiya.spec

echo.
if exist dist\GaiYa-v1.6.exe (
    echo [4/4] 打包成功！
    echo.
    echo ========================================
    echo exe 文件: dist\GaiYa-v1.6.exe
    dir /b dist\*.exe
    echo ========================================
) else (
    echo [4/4] 打包失败！
    echo.
    echo 请确保：
    echo 1. 已关闭所有运行中的 GaiYa-v1.6.exe
    echo 2. 已关闭文件资源管理器中的 dist 目录
    echo 3. 防病毒软件未锁定文件
)

echo.
pause
