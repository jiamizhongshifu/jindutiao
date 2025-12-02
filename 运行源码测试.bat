@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo 直接运行Python源码 (不使用exe)
echo ========================================
echo.
echo 关闭所有exe进程...
taskkill /F /IM GaiYa-v1.6.exe 2>nul
timeout /t 2 /nobreak >nul
echo.
echo 启动Python源码版本...
python main.py
