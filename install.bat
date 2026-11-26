@echo off
setlocal EnableDelayedExpansion

title CareerForge Setup
echo ============================================================
echo   CareerForge -- Windows One-Click Installer
echo ============================================================
echo.

:: 1. Check Python installation
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python was not found in your system PATH.
    echo Please install Python 3.10 or newer from https://www.python.org/
    echo During installation, be sure to check "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

:: 2. Verify Python version >= 3.10
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python 3.10 or newer is required.
    for /f "tokens=*" %%v in ('python --version') do echo Current version: %%v
    echo Please upgrade Python from https://www.python.org/
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version') do echo [1/4] Found Python: %%v
echo.

:: 3. Create virtual environment
if exist "%~dp0.venv" goto venv_ready

echo [2/4] Creating virtual environment in .venv ...
python -m venv "%~dp0.venv"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)
echo       Virtual environment created successfully.
goto venv_continue

:venv_ready
echo [2/4] Virtual environment (.venv) already exists.

:venv_continue
echo.

:: 4. Install dependencies
echo [3/4] Installing CareerForge and required dependencies ...
call "%~dp0.venv\Scripts\activate.bat"
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -e "%~dp0."
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Package installation failed.
    pause
    exit /b 1
)
echo       Installation complete!
echo.

:: 5. Create local forge.cmd launcher for convenience
(
    echo @echo off
    echo "%%~dp0.venv\Scripts\forge.exe" %%*
) > "%~dp0forge.cmd"

:: 6. Run forge doctor
echo [4/4] Verifying system setup with forge doctor ...
echo.
"%~dp0.venv\Scripts\forge.exe" doctor
echo.

echo ============================================================
echo   CareerForge is installed and ready to use!
echo ============================================================
echo.
echo Quick commands you can run right now:
echo   forge --help                 Show all available workflow commands
echo   forge setup                  Run the interactive candidate profile wizard
echo   forge init                   Generate a fresh profile.yaml template
echo.
echo For AI assistants (Antigravity, Claude Code, Codex, Cursor):
echo   Refer to AGENTS.md in this directory for guided prompts.
echo ============================================================
echo.
pause
