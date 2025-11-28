@echo off
REM Запускаем скрытый скрипт установки из папки src
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0src\install-windows.ps1"
pause