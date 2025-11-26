@echo off
REM Clear Windows Icon Cache
REM This will refresh the icons in Windows Explorer

echo Clearing Windows Icon Cache...
echo.

REM Stop Explorer
echo Stopping Windows Explorer...
taskkill /F /IM explorer.exe

REM Delete icon cache files
echo Deleting icon cache files...
cd /d "%userprofile%\AppData\Local"
attrib -h IconCache.db
del IconCache.db /a

REM Delete additional icon cache files (Windows 10/11)
cd /d "%userprofile%\AppData\Local\Microsoft\Windows\Explorer"
attrib -h iconcache*.db
del iconcache*.db /a

REM Restart Explorer
echo Restarting Windows Explorer...
start explorer.exe

echo.
echo Icon cache cleared successfully!
echo Please check if the exe icon is now updated.
echo.
pause
