@echo off
chcp 65001 >nul
echo ========================================
echo 打包完成后快速测试脚本
echo ========================================
echo.

REM 检查exe是否存在
if not exist "dist\GaiYa-v1.6.exe" (
    echo ❌ dist\GaiYa-v1.6.exe 不存在！
    echo.
    echo 请先运行打包命令:
    echo   build-fast.bat
    echo.
    pause
    exit /b 1
)

echo ✅ 找到 exe 文件
echo.

REM 显示文件信息
echo 📁 文件信息:
dir dist\GaiYa-v1.6.exe | findstr "GaiYa"
echo.

REM 检查文件大小(应该大于100MB)
for %%A in (dist\GaiYa-v1.6.exe) do set size=%%~zA
echo 文件大小: %size% 字节
echo.

if %size% LSS 100000000 (
    echo ⚠️  警告: 文件小于100MB,可能打包不完整
    echo.
)

echo ========================================
echo 🚀 准备启动测试
echo ========================================
echo.
echo 测试要点:
echo 1. 打开个人中心
echo 2. 查看是否有 "🔄 刷新" 按钮
echo 3. 点击刷新按钮
echo 4. 观察对话框是否自动关闭
echo 5. 检查刷新成功提示
echo.
echo 按任意键启动应用...
pause >nul

cd dist
start GaiYa-v1.6.exe

echo.
echo ✅ 应用已启动!
echo.
echo 📋 测试检查清单:
echo [ ] 刷新按钮显示
echo [ ] 点击刷新正常
echo [ ] 对话框自动关闭
echo [ ] 刷新成功提示
echo [ ] ��面正确更新
echo.
pause
