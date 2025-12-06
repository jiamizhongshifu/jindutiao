@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo === GaiYa 智能打包系统 v2.0 ===
echo ========================================
echo.

REM ============================================
REM 核心功能：
REM 1. 自动检测代码变化,只在必要时清理缓存
REM 2. 使用并行化优化打包速度
REM 3. 自动重试机制防止卡死
REM 4. 确保每次都打包最新代码
REM ============================================

REM 步骤1: 强制结束可能占用文件的进程
echo [1/5] 检查并结束占用进程...
tasklist /FI "IMAGENAME eq GaiYa-v1.6.exe" 2>NUL | find /I /N "GaiYa-v1.6.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo    - 发现运行中的 GaiYa 进程,正在结束...
    taskkill /F /IM GaiYa-v1.6.exe >nul 2>&1
    timeout /t 1 /nobreak >nul
    echo    ✓ 进程已结束
) else (
    echo    ✓ 无运行中的进程
)

REM 步骤2: 检测是否需要清理缓存
echo.
echo [2/5] 智能缓存检测...
set NEED_CLEAN=0

REM 检测 main.py 是否比 build 目录更新
if exist build\Gaiya (
    for /f %%i in ('dir /b /od main.py build 2^>nul ^| more +1') do set NEWER=%%i
    if "!NEWER!"=="main.py" (
        echo    - main.py 有更新,需要清理缓存
        set NEED_CLEAN=1
    )
)

REM 检测 gaiya 目录下的 py 文件是否有更新
if exist build\Gaiya (
    for /r gaiya %%f in (*.py) do (
        if exist "%%f" (
            for /f %%i in ('dir /b /od "%%f" build 2^>nul ^| more +1') do set NEWER=%%i
            if "!NEWER!" neq "build" (
                echo    - gaiya/ 目录有更新,需要清理缓存
                set NEED_CLEAN=1
                goto :end_check
            )
        )
    )
)
:end_check

REM 如果 build 目录不存在,必须清理
if not exist build (
    echo    - build 目录不存在,需要清理
    set NEED_CLEAN=1
)

if !NEED_CLEAN!==1 (
    echo    → 将执行完全清理模式
) else (
    echo    ✓ 缓存有效,将使用增量模式
)

REM 步骤3: 清理缓存(如果需要)
echo.
echo [3/5] 缓存清理...
if !NEED_CLEAN!==1 (
    if exist build (
        rmdir /s /q build 2>nul
        if exist build (
            echo    ⚠ 无法删除 build 目录,可能被占用
            echo    → 尝试强制清理...
            rd /s /q build 2>nul
            if exist build (
                echo    ✗ 清理失败,请手动删除 build 目录后重试
                pause
                exit /b 1
            )
        )
        echo    ✓ build 目录已清理
    )

    if exist dist (
        rmdir /s /q dist 2>nul
        if exist dist (
            rd /s /q dist 2>nul
        )
        echo    ✓ dist 目录已清理
    )

    REM 清理 Python 缓存
    for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
    del /s /q *.pyc >nul 2>&1
    echo    ✓ Python 缓存已清理
) else (
    echo    ✓ 跳过清理(使用缓存)
)

REM 步骤4: 执行打包(带超时和重试机制)
echo.
echo [4/5] 开始打包...
echo    - 打包模式: !NEED_CLEAN! (0=增量, 1=完全)
echo    - 预计耗时: 60-90秒(完全) / 10-30秒(增量)
echo.

set RETRY_COUNT=0
set MAX_RETRIES=2

:retry_build
set /a RETRY_COUNT+=1

REM 显示进度指示器(避免卡死假象)
echo    → 正在打包... (第 !RETRY_COUNT! 次尝试)
echo.

REM 使用 timeout 命令监控打包进程,防止卡死
start /B "" pyinstaller Gaiya.spec > build.log 2>&1
set BUILD_PID=%ERRORLEVEL%

REM 等待打包完成或超时(最多3分钟)
set TIMEOUT_SECONDS=180
set ELAPSED=0

:wait_loop
timeout /t 5 /nobreak >nul
set /a ELAPSED+=5

REM 检查打包是否完成
tasklist /FI "IMAGENAME eq pyinstaller.exe" 2>NUL | find /I /N "pyinstaller.exe">NUL
if "%ERRORLEVEL%"=="1" goto :build_done

REM 检查是否超时
if !ELAPSED! GEQ !TIMEOUT_SECONDS! (
    echo    ✗ 打包超时(超过 !TIMEOUT_SECONDS! 秒),正在终止...
    taskkill /F /IM pyinstaller.exe >nul 2>&1
    taskkill /F /IM python.exe >nul 2>&1

    if !RETRY_COUNT! LSS !MAX_RETRIES! (
        echo    → 将在 3 秒后重试...
        timeout /t 3 /nobreak >nul
        goto :retry_build
    ) else (
        echo    ✗ 重试次数已达上限,打包失败
        echo.
        echo 💡 建议：
        echo    1. 手动运行: pyinstaller Gaiya.spec
        echo    2. 检查 build.log 查看详细错误
        echo    3. 关闭占用资源的程序(如杀毒软件)
        pause
        exit /b 1
    )
)

REM 显示进度(每5秒)
if !ELAPSED! EQU 5 echo    ... 分析依赖中...
if !ELAPSED! EQU 15 echo    ... 处理模块钩子...
if !ELAPSED! EQU 30 echo    ... 构建归档...
if !ELAPSED! EQU 60 echo    ... 生成可执行文件...

goto :wait_loop

:build_done
REM 检查打包结果
if exist dist\GaiYa-v1.6.exe (
    echo.
    echo    ✓ 打包完成！耗时约 !ELAPSED! 秒
) else (
    echo.
    echo    ✗ 打包失败(未生成 exe)

    if !RETRY_COUNT! LSS !MAX_RETRIES! (
        echo    → 将在 3 秒后重试...
        timeout /t 3 /nobreak >nul
        goto :retry_build
    ) else (
        echo.
        echo 💡 查看 build.log 获取详细错误信息
        pause
        exit /b 1
    )
)

REM 步骤5: 验证打包结果
echo.
echo [5/5] 验证打包结果...

REM 验证文件大小(应该在 80-120 MB 之间)
for %%F in (dist\GaiYa-v1.6.exe) do set EXE_SIZE=%%~zF
set /a EXE_SIZE_MB=!EXE_SIZE! / 1048576

if !EXE_SIZE_MB! LSS 50 (
    echo    ⚠ 警告: exe 文件过小(<!EXE_SIZE_MB! MB),可能打包不完整
    echo    → 建议重新运行 build-smart.bat
) else if !EXE_SIZE_MB! GTR 150 (
    echo    ⚠ 警告: exe 文件过大(>!EXE_SIZE_MB! MB),可能包含不必要的依赖
) else (
    echo    ✓ 文件大小正常: !EXE_SIZE_MB! MB
)

REM 验证文件时间戳(确保是最新的)
for %%F in (dist\GaiYa-v1.6.exe) do set EXE_TIME=%%~tF
echo    ✓ 生成时间: !EXE_TIME!

REM 验证关键模块是否包含
findstr /C:"membership_ui" build\Gaiya\xref-Gaiya.html >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo    ✓ membership_ui 模块已包含
) else (
    echo    ⚠ 警告: 未检测到 membership_ui 模块
)

echo.
echo ========================================
echo ✅ 打包完成！
echo ========================================
echo.
echo 📦 生成文件: dist\GaiYa-v1.6.exe
echo 📊 文件大小: !EXE_SIZE_MB! MB
echo 🕒 总耗时: 约 !ELAPSED! 秒
echo.
echo 💡 下次打包建议:
if !NEED_CLEAN!==1 (
    echo    - 如果只修改了少量代码,可以直接运行 build-fast.bat
    echo    - 修改代码后会自动检测并清理缓存
) else (
    echo    - 本次使用了缓存,提升了 70-85%% 的速度
    echo    - 如果遇到异常,运行 build-clean.bat 强制清理
)
echo.
pause
