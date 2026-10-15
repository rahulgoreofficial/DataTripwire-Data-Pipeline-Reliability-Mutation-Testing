@echo off
setlocal

title DataTripwire // The Data Reliability Lab

REM 1. Determine project root from batch file directory
set "PROJECT_ROOT=%~dp0"
cd /d "%PROJECT_ROOT%"

echo ===========================================================
echo   DATATRIPWIRE // THE DATA RELIABILITY LAB
echo   Windows One-Click Development Startup
echo ===========================================================
echo.

REM 2. Check for Python availability
set "PYTHON_CMD="
python --version >nul 2>&1 && set "PYTHON_CMD=python"
if "%PYTHON_CMD%"=="" (
    py -3 --version >nul 2>&1 && set "PYTHON_CMD=py -3"
)
if "%PYTHON_CMD%"=="" goto :no_python

REM 3. Check for Node.js availability
node --version >nul 2>&1 || goto :no_node

REM 4. Check for npm availability (using call because npm is a .cmd batch file on Windows)
call npm --version >nul 2>&1 || goto :no_npm

REM 5. Launch the DataTripwire Python Orchestrator
echo [STARTUP] Environment prerequisites verified.
echo [STARTUP] Invoking DataTripwire supervisor orchestrator...
echo.

%PYTHON_CMD% scripts\dev.py %*
set "EXIT_CODE=%ERRORLEVEL%"

if %EXIT_CODE% NEQ 0 (
    echo.
    echo [STOPPED] DataTripwire exited with error code %EXIT_CODE%.
    echo Review the error output above.
    pause
)

exit /b %EXIT_CODE%

:no_python
echo [ERROR] Python 3 was not detected on your system or in your PATH.
echo.
echo DataTripwire requires Python 3.11 or newer.
echo Please download and install Python from:
echo   https://www.python.org/downloads/
echo.
echo IMPORTANT: Make sure to check the box "Add python.exe to PATH"
echo during installation.
echo.
pause
exit /b 1

:no_node
echo [ERROR] Node.js was not detected on your system or in your PATH.
echo.
echo DataTripwire requires Node.js 18 or newer (LTS recommended).
echo Please download and install Node.js from:
echo   https://nodejs.org/
echo.
pause
exit /b 1

:no_npm
echo [ERROR] npm was not detected on your system or in your PATH.
echo.
echo npm is bundled with Node.js. Please install or repair Node.js from:
echo   https://nodejs.org/
echo.
pause
exit /b 1
