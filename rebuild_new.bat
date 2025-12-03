@echo off
chcp 65001 >nul
echo ========================================
echo 重新打包 GaiYa (新文件名)
echo ========================================
echo.

echo 1. 修改version.py临时改变文件名...
python -c "import re; f='version.py'; c=open(f,encoding='utf-8').read(); c=re.sub(r'VERSION_PATCH = \d+', 'VERSION_PATCH = 99', c); open(f,'w',encoding='utf-8').write(c); print('已修改为v1.6.99')"

echo.
echo 2. 开始打包...
python -m PyInstaller Gaiya.spec --noconfirm

echo.
echo 3. 恢复version.py...
git checkout version.py

echo.
echo 4. 检查结果...
if exist dist\GaiYa-v1.6.99.exe (
    echo ✓ 打包成功: dist\GaiYa-v1.6.99.exe
    dir dist\GaiYa-v1.6.99.exe
    echo.
    echo 请将 GaiYa-v1.6.99.exe 重命名为 GaiYa-v1.6.exe 使用
) else (
    echo ✗ 打包失败
)

echo.
pause
