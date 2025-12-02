@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo 测试任务确认崩溃修复
echo ========================================
echo.

echo 第1步: 关闭所有进程...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM GaiYa-v1.6.exe 2>nul
timeout /t 2 /nobreak >nul

echo 第2步: 删除旧日志...
del gaiya.log 2>nul

echo 第3步: 启动Python源码...
echo.
echo ⚠️  已修复的问题:
echo    1. TaskReviewWindow 参数传递错误
echo    2. on_review_completed 参数解包错误
echo.
start python main.py

echo 第4步: 等待启动...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo 📋 测试步骤:
echo ========================================
echo.
echo 1. 右键托盘图标 → "统计报告"
echo 2. 点击 "手动生成推理"
echo 3. 等待弹出任务确认窗口
echo 4. 点击 "全部确认"
echo 5. 检查是否成功完成而不崩溃
echo.
echo 预期结果:
echo ✓ 应该显示 "已成功确认 X 个任务!" 提示
echo ✓ 应用不应该崩溃
echo.
pause
