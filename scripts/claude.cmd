@echo off
REM Windows batch wrapper for Claude CLI
REM This wrapper ensures proper execution on Windows systems

setlocal enabledelayedexpansion

REM Try to find claude executable in various locations
set CLAUDE_EXE=
set SEARCH_PATHS=%CLAUDE_CLI_PATH%;%PATH%;%APPDATA%\npm;%LOCALAPPDATA%\Programs\claif\bin;%USERPROFILE%\.local\bin

REM Check CLAUDE_CLI_PATH first
if defined CLAUDE_CLI_PATH (
    if exist "%CLAUDE_CLI_PATH%\claude.cmd" (
        set CLAUDE_EXE=%CLAUDE_CLI_PATH%\claude.cmd
    ) else if exist "%CLAUDE_CLI_PATH%\claude.exe" (
        set CLAUDE_EXE=%CLAUDE_CLI_PATH%\claude.exe
    ) else if exist "%CLAUDE_CLI_PATH%" (
        set CLAUDE_EXE=%CLAUDE_CLI_PATH%
    )
)

REM Search in PATH if not found
if not defined CLAUDE_EXE (
    for %%i in (claude.cmd claude.exe claude.bat claude) do (
        set RESULT=
        for %%j in ("%%~$PATH:i") do set RESULT=%%~j
        if defined RESULT (
            set CLAUDE_EXE=!RESULT!
            goto :found
        )
    )
)

REM Check npm global installation
if not defined CLAUDE_EXE (
    if exist "%APPDATA%\npm\claude.cmd" (
        set CLAUDE_EXE=%APPDATA%\npm\claude.cmd
    ) else if exist "%APPDATA%\npm\claude.exe" (
        set CLAUDE_EXE=%APPDATA%\npm\claude.exe
    )
)

REM Check Claif installation directory
if not defined CLAUDE_EXE (
    if exist "%LOCALAPPDATA%\Programs\claif\bin\claude.cmd" (
        set CLAUDE_EXE=%LOCALAPPDATA%\Programs\claif\bin\claude.cmd
    ) else if exist "%LOCALAPPDATA%\Programs\claif\bin\claude.exe" (
        set CLAUDE_EXE=%LOCALAPPDATA%\Programs\claif\bin\claude.exe
    )
)

REM Check Claif claude-bin directory
if not defined CLAUDE_EXE (
    if exist "%LOCALAPPDATA%\Programs\claif\bin\claude-bin\claude.exe" (
        set CLAUDE_EXE=%LOCALAPPDATA%\Programs\claif\bin\claude-bin\claude.exe
    ) else if exist "%LOCALAPPDATA%\Programs\claif\bin\claude-bin\claude" (
        set CLAUDE_EXE=%LOCALAPPDATA%\Programs\claif\bin\claude-bin\claude
    )
)

:found
if not defined CLAUDE_EXE (
    echo Error: Claude CLI not found.
    echo.
    echo Please install Claude CLI using one of these methods:
    echo   npm install -g @anthropic-ai/claude-code
    echo   bun add -g @anthropic-ai/claude-code
    echo   claif install claude
    echo.
    echo Or set CLAUDE_CLI_PATH environment variable to the installation directory.
    exit /b 1
)

REM Change to the Claude directory and execute with arguments
cd /d "%~dp0\..\claude-bin" 2>nul
if errorlevel 1 (
    REM If claude-bin directory doesn't exist, execute directly
    "%CLAUDE_EXE%" %*
) else (
    REM Execute from claude-bin directory (for bundled installations)
    "./claude" %*
)
exit /b %ERRORLEVEL%