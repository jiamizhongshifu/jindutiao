@echo off
chcp 65001 >nul
echo ========================================
echo === GaiYa 完全重建（清理模式）===
echo ========================================
echo.
echo ⚠️  警告：此模式会删除所有缓存，打包速度较慢（60-90秒）
echo.
echo 📋 适用场景：
echo    1. 修改了 Gaiya.spec 配置文件
echo    2. 添加/删除了 hiddenimports
echo    3. 更新了 PySide6 或其他依赖库
echo    4. 打包出现异常错误（缓存损坏）
echo    5. build-fast.bat 打包失败时
echo.
echo 💡 建议：日常开发请使用 build-fast.bat（更快）
echo.
echo 🔄 同步版本信息...
python update_version_info.py
if errorlevel 1 (
    echo ❌ 版本同步失败！
    pause
    exit /b 1
)
echo.
echo 开始清理缓存...

if exist build (
    rmdir /s /q build
    echo ✅ build 目录已清理
) else (
    echo ℹ️  build 目录不存在
)

if exist dist (
    rmdir /s /q dist
    echo ✅ dist 目录已清理
) else (
    echo ℹ️  dist 目录不存在
)

echo.
echo 开始完全重建打包...
echo.

pyinstaller Gaiya.spec

echo.
if errorlevel 1 (
    echo ❌ 打包失败！
    echo.
    echo 💡 可能的解决方案：
    echo    1. 检查错误信息中的具体问题
    echo    2. 确认 Gaiya.spec 配置是否正确
    echo    3. 确认所有依赖库是否已安装
    echo    4. 尝试更新 PyInstaller：pip install --upgrade pyinstaller
    echo.
    pause
    exit /b 1
) else (
    echo.
    echo ========================================
    echo ✅ 完全重建成功！
    echo ========================================
    echo.
    echo 生成的文件：
    dir dist\*.exe
    echo.
    echo 💡 后续可使用 build-fast.bat 进行快速增量打包
    echo.
    pause
)
