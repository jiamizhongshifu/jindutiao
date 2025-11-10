@echo off
echo Refreshing Windows Icon Cache...
echo.

REM Kill Windows Explorer
taskkill /f /im explorer.exe

REM Delete icon cache files
cd /d %userprofile%\AppData\Local\Microsoft\Windows\Explorer
del /f /q iconcache*.db
del /f /q thumbcache*.db

REM Restart Windows Explorer
start explorer.exe

echo.
echo Icon cache has been refreshed!
echo Please check the exe file icon now.
echo.
pause
