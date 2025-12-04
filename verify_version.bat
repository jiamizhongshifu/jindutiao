@echo off
chcp 65001 >nul
echo ========================================
echo === 版本验证工具 ===
echo ========================================
echo.
echo 1. 关闭所有GaiYa进程...
taskkill /F /IM GaiYa-v1.6.exe 2>nul
timeout /t 2 >nul
echo.
echo 2. 检查dist\GaiYa-v1.6.exe...
if exist dist\GaiYa-v1.6.exe (
    for %%F in (dist\GaiYa-v1.6.exe) do (
        echo ✅ 文件存在
        echo    大小: %%~zF 字节
        echo    修改时间: %%~tF
    )
) else (
    echo ❌ 文件不存在!
    pause
    exit /b 1
)
echo.
echo 3. 启动新版本...
start dist\GaiYa-v1.6.exe
echo.
echo ✅ 已启动新版本客户端
echo.
echo 📋 请测试以下功能:
echo    1. 点击"个人中心"
echo    2. 点击"刷新"查看会员状态
echo    3. 点击"升级会员"
echo    4. 选择套餐并点击"立即购买"
echo    5. 应该看到二维码支付对话框(而非"等待支付"弹窗)
echo.
pause
