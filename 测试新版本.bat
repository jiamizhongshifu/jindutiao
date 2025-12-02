@echo off
chcp 65001 >nul
cd /d "%~dp0\dist"

echo ========================================
echo 测试 GaiYa v1.6.8 新版本
echo ========================================
echo.

echo 第1步: 关闭旧进程...
taskkill /F /IM GaiYa-v1.6.exe 2>nul
timeout /t 3 /nobreak >nul

echo 第2步: 删除旧日志...
del gaiya.log 2>nul

echo 第3步: 启动新版本...
echo.
echo ⚠️  请等待应用启动完成后(约5秒)
echo.
start GaiYa-v1.6.exe

echo 第4步: 等待启动...
timeout /t 5 /nobreak >nul

echo.
echo 第5步: 打开日志文件...
notepad gaiya.log

echo.
echo ========================================
echo 📋 验证清单:
echo ========================================
echo.
echo ✓ 搜索: "任务完成推理调度器已启动"
echo   ├─ 找到了 → ✅ 调度器初始化成功
echo   └─ 没找到 → ❌ 仍是旧版本
echo.
echo ✓ 检查日志时间戳
echo   └─ 应该是今天 10:2X (不是 10:13)
echo.
pause
