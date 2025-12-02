@echo off
chcp 65001 >nul
echo ========================================
echo GaiYa v1.6.6 强制更新脚本
echo ========================================
echo.

echo [1/5] 关闭所有旧进程...
taskkill /F /IM GaiYa-v1.6.exe 2>nul
if %errorlevel%==0 (
    echo ✓ 已关闭旧进程
) else (
    echo ℹ 没有运行中的进程
)
echo.

echo [2/5] 等待进程完全退出...
timeout /t 2 /nobreak >nul
echo ✓ 等待完成
echo.

echo [3/5] 备份旧日志...
cd /d "%~dp0dist"
if exist gaiya.log (
    copy gaiya.log gaiya.log.backup.%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.txt >nul
    echo ✓ 日志已备份
) else (
    echo ℹ 无需备份
)
echo.

echo [4/5] 清理旧日志...
del gaiya.log 2>nul
if %errorlevel%==0 (
    echo ✓ 旧日志已清理
) else (
    echo ℹ 无旧日志
)
echo.

echo [5/5] 启动最新版本...
echo ========================================
echo 正在启动 GaiYa-v1.6.exe (23:31版本)
echo ========================================
echo.
start "" "GaiYa-v1.6.exe"

timeout /t 2 /nobreak >nul
echo.
echo ✓ 启动完成!
echo.
echo 📝 测试步骤:
echo    1. 打开统计报告
echo    2. 点击 "🔄 手动生成推理"
echo    3. 等待5-10秒,应该弹出完成对话框
echo.
echo 🔍 验证方法:
echo    打开 dist\gaiya.log 搜索 "[手动推理]"
echo    应该看到完整的推理流程日志
echo.
pause
