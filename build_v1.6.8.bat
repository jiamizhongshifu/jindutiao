@echo off
REM ============================================
REM GaiYa v1.6.8 打包脚本
REM ============================================

echo ============================================
echo GaiYa v1.6.8 打包开始
echo ============================================
echo.

REM 1. 清理旧的构建文件
echo [1/5] 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo 清理完成
echo.

REM 2. 清理测试数据（可选）
echo [2/5] 清理测试数据...
python clean_test_data.py
echo.

REM 3. 验证版本号
echo [3/5] 验证版本号...
python -c "from version import __version__, __release_date__; print(f'版本: {__version__}'); print(f'发布日期: {__release_date__}')"
echo.

REM 4. 开始打包
echo [4/5] 开始打包...
pyinstaller Gaiya.spec
echo.

REM 5. 验证打包结果
echo [5/5] 验证打包结果...
if exist "dist\GaiYa-v1.6.exe" (
    echo ✓ 打包成功！
    echo.
    echo 可执行文件位置: dist\GaiYa-v1.6.exe
    echo.

    REM 显示文件大小
    for %%F in ("dist\GaiYa-v1.6.exe") do (
        echo 文件大小: %%~zF 字节
    )

    echo.
    echo ============================================
    echo 打包完成！
    echo ============================================
    echo.
    echo 下一步:
    echo 1. 运行 dist\GaiYa-v1.6.exe 测试
    echo 2. 测试任务回顾窗口（托盘菜单 - 今日任务回顾）
    echo 3. 测试统计报告手动推理（统计报告 - 手动生成推理）
    echo 4. 确认没有卡死问题后发布
    echo.
) else (
    echo ✗ 打包失败！
    echo 请检查上面的错误信息
    exit /b 1
)

pause
