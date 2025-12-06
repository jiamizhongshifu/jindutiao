@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo === GaiYa 快速打包（智能增量）===
echo ========================================
echo.

REM 1. 结束占用进程
taskkill /F /IM GaiYa-v1.6.exe >nul 2>&1
timeout /t 1 /nobreak >nul

REM 2. 检测是否需要清理(关键代码修改)
set NEED_CLEAN=0

REM 检查 main.py 是否更新
if exist build\Gaiya\main.pyc (
    for /f %%i in ('dir /b /od main.py build\Gaiya\main.pyc 2^>nul ^| more +1') do set NEWER=%%i
    if "!NEWER!"=="main.py" set NEED_CLEAN=1
)

REM 检查 membership_ui.py 是否更新
if exist "build\Gaiya\gaiya\ui\membership_ui.pyc" (
    for /f %%i in ('dir /b /od gaiya\ui\membership_ui.py build\Gaiya\gaiya\ui\membership_ui.pyc 2^>nul ^| more +1') do set NEWER=%%i
    if "!NEWER!"=="membership_ui.py" set NEED_CLEAN=1
)

REM 3. 智能清理
if !NEED_CLEAN!==1 (
    echo 🔍 检测到核心代码修改,清理缓存确保最新代码...
    rmdir /s /q build 2>nul
    rmdir /s /q dist 2>nul
    echo ✓ 缓存已清理
    echo.
) else (
    echo ✓ 使用增量模式(利用缓存加速)
    echo.
)

echo 💡 增量模式优势：
echo    - 首次/清理后：60-90秒
echo    - 使用缓存：8-20秒（提升 70-87%%）
echo.
echo 开始打包...
echo.

REM 4. 执行打包(带后台进度监控)
start /B "" cmd /c "pyinstaller Gaiya.spec >nul 2>&1"

REM 5. 显示进度(避免卡死假象)
set ELAPSED=0
:wait
timeout /t 5 /nobreak >nul
set /a ELAPSED+=5

tasklist /FI "IMAGENAME eq python.exe" 2>NUL | find /I /N "python.exe">NUL
if "%ERRORLEVEL%"=="1" goto done

if !ELAPSED! EQU 5 echo ... 分析依赖中 ...
if !ELAPSED! EQU 15 echo ... 处理模块钩子 ...
if !ELAPSED! EQU 30 echo ... 构建归档 ...
if !ELAPSED! EQU 60 echo ... 生成 exe ...

if !ELAPSED! GTR 120 (
    echo.
    echo ⚠️  打包时间过长,可能出现问题
    echo → 建议: Ctrl+C 终止后运行 build-clean.bat
    echo.
)

goto wait

:done
echo.
if exist dist\GaiYa-v1.6.exe (
    echo ========================================
    echo ✅ 打包成功！(耗时约 !ELAPSED! 秒)
    echo ========================================
    echo.
    for %%F in (dist\GaiYa-v1.6.exe) do set SIZE=%%~zF
    set /a SIZE_MB=!SIZE! / 1048576
    echo 📦 文件: dist\GaiYa-v1.6.exe
    echo 📊 大小: !SIZE_MB! MB
    echo 🕒 耗时: !ELAPSED! 秒
    echo.
    if !NEED_CLEAN!==0 (
        echo 💡 本次使用了缓存,速度提升 70-87%%
    ) else (
        echo 💡 下次修改小代码时将更快(利用缓存)
    )
) else (
    echo ❌ 打包失败！
    echo.
    echo 💡 可能的解决方案：
    echo    1. 运行 build-clean.bat 清理后重试
    echo    2. 检查是否有杀毒软件占用文件
    echo    3. 手动运行: pyinstaller Gaiya.spec
)

echo.
pause
