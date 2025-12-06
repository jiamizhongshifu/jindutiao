@echo off
chcp 65001 >nul
echo ========================================
echo === 清理旧的打包脚本 ===
echo ========================================
echo.
echo 将保留以下三个优化脚本:
echo   ✓ build-fast.bat     - 日常快速打包(推荐)
echo   ✓ build-smart.bat    - 智能打包系统
echo   ✓ build-clean.bat    - 完全清理重建
echo.
echo 将移动以下旧脚本到 .old_build_scripts/ 目录:
echo   - build.bat
echo   - build_onefile.bat
echo   - build_v1.6.8.bat
echo   - rebuild.bat
echo   - rebuild_new.bat
echo   - auto_rebuild.bat
echo   - test_after_build.bat
echo.
echo 按任意键继续,或 Ctrl+C 取消...
pause >nul
echo.

REM 创建备份目录
if not exist .old_build_scripts mkdir .old_build_scripts
echo [1/7] 创建备份目录: .old_build_scripts

REM 移动旧脚本
if exist build.bat (
    move build.bat .old_build_scripts\ >nul 2>&1
    echo [2/7] ✓ 移动 build.bat
) else (
    echo [2/7] ⊘ build.bat 不存在,跳过
)

if exist build_onefile.bat (
    move build_onefile.bat .old_build_scripts\ >nul 2>&1
    echo [3/7] ✓ 移动 build_onefile.bat
) else (
    echo [3/7] ⊘ build_onefile.bat 不存在,跳过
)

if exist build_v1.6.8.bat (
    move build_v1.6.8.bat .old_build_scripts\ >nul 2>&1
    echo [4/7] ✓ 移动 build_v1.6.8.bat
) else (
    echo [4/7] ⊘ build_v1.6.8.bat 不存在,跳过
)

if exist rebuild.bat (
    move rebuild.bat .old_build_scripts\ >nul 2>&1
    echo [5/7] ✓ 移动 rebuild.bat
) else (
    echo [5/7] ⊘ rebuild.bat 不存在,跳过
)

if exist rebuild_new.bat (
    move rebuild_new.bat .old_build_scripts\ >nul 2>&1
    echo [6/7] ✓ 移动 rebuild_new.bat
) else (
    echo [6/7] ⊘ rebuild_new.bat 不存在,跳过
)

if exist auto_rebuild.bat (
    move auto_rebuild.bat .old_build_scripts\ >nul 2>&1
    echo [7/7] ✓ 移动 auto_rebuild.bat
) else (
    echo [7/7] ⊘ auto_rebuild.bat 不存在,跳过
)

if exist test_after_build.bat (
    move test_after_build.bat .old_build_scripts\ >nul 2>&1
    echo [额外] ✓ 移动 test_after_build.bat
) else (
    echo [额外] ⊘ test_after_build.bat 不存在,跳过
)

echo.
echo ========================================
echo ✅ 清理完成！
echo ========================================
echo.
echo 当前保留的打包脚本:
dir /b build*.bat 2>nul
echo.
echo 备份的旧脚本位于: .old_build_scripts\
echo 如需恢复,可以手动移动回来
echo.
echo 💡 推荐使用:
echo    - 日常开发: build-fast.bat
echo    - 首次打包: build-smart.bat
echo    - 遇到问题: build-clean.bat
echo.
pause
