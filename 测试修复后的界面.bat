@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo 测试修复后的统计报告界面
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
echo ⚠️  已修复统计报告窗口布局问题
echo ⚠️  现在应该显示为独立窗口
echo.
start python main.py

echo 第4步: 等待启动...
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo 📋 测试步骤:
echo ========================================
echo.
echo 1. 右键托盘图标 → "统计报告"
echo 2. 检查窗口是否正常显示为独立窗口
echo 3. 查找"手动生成推理"按钮
echo 4. 点击按钮测试推理功能
echo.
echo 如果界面仍然异常,请截图并告诉我
echo.
pause
