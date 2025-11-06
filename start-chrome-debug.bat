@echo off
REM 关闭所有 Chrome 实例
taskkill /F /IM chrome.exe >nul 2>&1

REM 等待 2 秒
timeout /t 2 /nobreak >nul

REM 以调试模式启动 Chrome
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%TEMP%\chrome-debug" https://www.example.com

echo Chrome 已在调试模式下启动 (端口 9222)
echo 正在测试连接...
timeout /t 3 /nobreak >nul

REM 测试调试端口
curl -s http://localhost:9222/json/version
