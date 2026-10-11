@echo off
rem Double-click to extract everything in ..\pack into ..\unpacked.
rem Drop a game folder onto this file (or pass --root DIR) to use another location.
setlocal
set "DROP=%~f1"
set "ATTR=%~a1"
cd /d "%~dp0"

set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY (
    echo Python 3.9 or newer was not found. Install it from https://www.python.org/ and try again.
    pause
    exit /b 1
)

if /i "%ATTR:~0,1%"=="d" (
    %PY% extract_all.py --root "%DROP%\." %2 %3 %4 %5 %6 %7 %8 %9
) else (
    %PY% extract_all.py %*
)
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" echo Finished with errors ^(exit code %RC%^).
pause
exit /b %RC%
