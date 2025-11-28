@echo off
REM BitNewton ASR Tools - Transcribe Wrapper
REM Автоматически использует встроенный Python

set "SCRIPT_DIR=%~dp0"
set "PYTHON_EXE=%SCRIPT_DIR%..\python\python.exe"
set "TRANSCRIBE_PY=%SCRIPT_DIR%..\src\transcribe.py"
set "PYTHONPATH=%SCRIPT_DIR%..\src;%PYTHONPATH%"

REM Проверка наличия встроенного Python
if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" "%TRANSCRIBE_PY%" %*
) else (
    REM Fallback на системный Python если embedded не найден
    python "%TRANSCRIBE_PY%" %*
)
