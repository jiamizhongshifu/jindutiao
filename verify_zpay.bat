@echo off
chcp 65001 >nul
echo ============================================================
echo Z-Pay凭证快速验证
echo ============================================================
echo.

echo 当前环境变量:
echo ZPAY_PID=%ZPAY_PID%
echo ZPAY_PKEY=%ZPAY_PKEY%
echo.

if "%ZPAY_PID%"=="" (
    echo [错误] ZPAY_PID 未设置
    echo.
    echo 请先设置环境变量:
    echo   set ZPAY_PID=你的商户ID
    echo   set ZPAY_PKEY=你的商户密钥
    pause
    exit /b 1
)

if "%ZPAY_PKEY%"=="" (
    echo [错误] ZPAY_PKEY 未设置
    pause
    exit /b 1
)

echo 运行Python测试...
echo.
python test_zpay_credentials.py

echo.
echo ============================================================
pause
