# PyInstaller hook for config_gui module
from PyInstaller.utils.hooks import collect_all

# Forcefully collect everything from config_gui
datas, binaries, hiddenimports = collect_all('config_gui')
