@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo 成就弹窗 UI 测试
echo ========================================
echo.
echo 将依次显示四种稀有度的成就弹窗:
echo - 普通 (灰色)
echo - 稀有 (蓝色)
echo - 史诗 (紫色+光晕)
echo - 传说 (金色+光晕)
echo.
echo 点击"太棒了!"按钮关闭后显示下一个...
echo.

"C:\Users\Sats\AppData\Local\Programs\Python\Python311\python.exe" test_achievement_popup.py

echo.
echo 测试完成!
pause
