@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo 直接运行Python源码 (绕过exe)
echo ========================================
echo.

echo 第1步: 关闭所有exe进程...
taskkill /F /IM GaiYa-v1.6.exe 2>nul
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo 第2步: 删除旧日志...
del gaiya.log 2>nul

echo 第3步: 启动Python源码...
echo.
echo ⚠️  这会直接运行Python源码,包含所有最新修复
echo.
start python main.py

echo 第4步: 等待启动...
timeout /t 5 /nobreak >nul

echo.
echo 第5步: 打开日志查看...
notepad gaiya.log

echo.
echo ========================================
echo 📋 验证清单:
echo ========================================
echo.
echo ✓ 搜索: "任务完成推理调度器已启动"
echo   ├─ 找到了 → ✅ 源码正确
echo   └─ 没找到 → ❌ 源码有问题
echo.
echo ✓ 然后测试手动推理:
echo   1. 右键托盘 → 统计报告
echo   2. 点击"手动生成推理"
echo   3. 查看是否成功
echo.
pause
