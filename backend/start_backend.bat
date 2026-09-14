@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
echo ============================================================
echo    AutoTest Backend - dang khoi dong...
echo.
echo    - Doi dong "Uvicorn running on http://127.0.0.1:8000"
echo    - GIU NGUYEN cua so nay khi dang dung extension
echo    - DONG cua so nay (hoac Ctrl+C) de TAT backend
echo ============================================================
echo.
".venv\Scripts\python.exe" -m uvicorn main:app --port 8000
echo.
echo Backend da dung. Bam phim bat ky de dong...
pause >nul
