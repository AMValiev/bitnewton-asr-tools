@echo off
REM BitNewton ASR Tools - Summarize Wrapper
REM Автоматически использует встроенный Python

set "SCRIPT_DIR=%~dp0"
set "PYTHON_EXE=%SCRIPT_DIR%..\python\python.exe"
set "SUMMARIZE_PY=%SCRIPT_DIR%..\src\summarize.py"
set "PYTHONPATH=%SCRIPT_DIR%..\src;%PYTHONPATH%"

REM Проверка наличия встроенного Python
if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" "%SUMMARIZE_PY%" %*
) else (
    REM Fallback на системный Python если embedded не найден
    python "%SUMMARIZE_PY%" %*
)
