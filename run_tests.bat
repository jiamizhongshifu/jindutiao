@echo off
REM Windows测试运行脚本

echo ========================================
echo GaiYa 单元测试执行脚本
echo ========================================
echo.

echo [1/4] 检查pytest是否安装...
python -m pytest --version >nul 2>&1
if errorlevel 1 (
    echo pytest未安装，正在安装...
    pip install pytest pytest-cov pytest-mock
) else (
    echo pytest已安装
)
echo.

echo [2/4] 运行单元测试...
python -m pytest tests/unit/ -v --tb=short --color=yes
echo.

echo [3/4] 生成覆盖率报告...
python -m pytest tests/unit/ --cov=api --cov-report=html --cov-report=term
echo.

echo [4/4] 完成！
echo 覆盖率HTML报告已生成到: htmlcov\index.html
echo.
echo 按任意键退出...
pause >nul
