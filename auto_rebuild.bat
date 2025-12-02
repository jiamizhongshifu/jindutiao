@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo === 自动完全重新打包 v1.6.8 ===
echo ========================================
echo.

echo 第1步: 关闭所有进程...
taskkill /F /IM GaiYa-v1.6.exe 2>nul
taskkill /F /IM python.exe 2>nul
timeout /t 3 /nobreak >nul

echo 第2步: 清理缓存目录...
if exist build (
    rmdir /s /q build
    echo ✅ build 目录已清理
)
if exist dist (
    rmdir /s /q dist
    echo ✅ dist 目录已清理
)

echo.
echo 第3步: 开始打包...
pyinstaller Gaiya.spec

echo.
if errorlevel 1 (
    echo ❌ 打包失败
    exit /b 1
) else (
    echo ✅ 打包成功
    echo.
    dir dist\*.exe
)
