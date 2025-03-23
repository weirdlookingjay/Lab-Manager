@echo off
setlocal EnableDelayedExpansion

echo Setting up Computer Agent...

REM Get absolute paths
set "INSTALL_DIR=%CD%"
set "VENV_DIR=%INSTALL_DIR%\agent_env"
set "PYTHON_PATH=%VENV_DIR%\Scripts\python.exe"
set "PIP_PATH=%VENV_DIR%\Scripts\pip.exe"
set "SCRIPT_PATH=%INSTALL_DIR%\computer_agent.py"
set "LOG_PATH=%INSTALL_DIR%\agent.log"
set "NSSM_PATH=%INSTALL_DIR%\nssm.exe"

REM Check if NSSM exists, if not download it
if not exist "%NSSM_PATH%" (
    echo Downloading NSSM...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile 'nssm.zip'}"
    powershell -Command "& {Expand-Archive -Path 'nssm.zip' -DestinationPath 'nssm_temp' -Force}"
    copy /Y "nssm_temp\nssm-2.24\win64\nssm.exe" "%NSSM_PATH%" >nul
    rmdir /S /Q nssm_temp
    del /F /Q nssm.zip
)

REM Create virtual environment if it doesn't exist
if not exist "%VENV_DIR%" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%" || goto :error
)

REM Activate virtual environment and install packages
echo Installing dependencies...
call "%VENV_DIR%\Scripts\activate.bat" || goto :error

REM Install required packages using the virtual environment's pip
"%PIP_PATH%" install --upgrade pip || goto :error
"%PIP_PATH%" install psutil python-dotenv websockets || goto :error

REM Verify dependencies are installed
echo Verifying dependencies...
"%PYTHON_PATH%" -c "import psutil, websockets" || goto :error

REM Stop and remove existing service if it exists
echo Checking for existing service...
sc query ComputerAgent >nul 2>&1
if not errorlevel 1 (
    echo Stopping existing service...
    "%NSSM_PATH%" stop ComputerAgent >nul 2>&1
    "%NSSM_PATH%" remove ComputerAgent confirm >nul 2>&1
    timeout /t 2 >nul
)

REM Install the service using NSSM
echo Installing service with NSSM...
"%NSSM_PATH%" install ComputerAgent "%PYTHON_PATH%" || goto :error
"%NSSM_PATH%" set ComputerAgent AppParameters "%SCRIPT_PATH%" || goto :error
"%NSSM_PATH%" set ComputerAgent DisplayName "Computer Management Agent" || goto :error
"%NSSM_PATH%" set ComputerAgent Description "Agent for computer management system" || goto :error
"%NSSM_PATH%" set ComputerAgent AppDirectory "%INSTALL_DIR%" || goto :error
"%NSSM_PATH%" set ComputerAgent AppEnvironmentExtra "PYTHONPATH=%VENV_DIR%\Lib\site-packages" || goto :error
"%NSSM_PATH%" set ComputerAgent Start SERVICE_AUTO_START || goto :error
"%NSSM_PATH%" set ComputerAgent ObjectName LocalSystem || goto :error
"%NSSM_PATH%" set ComputerAgent AppStdout "%INSTALL_DIR%\service_stdout.log" || goto :error
"%NSSM_PATH%" set ComputerAgent AppStderr "%INSTALL_DIR%\service_stderr.log" || goto :error
"%NSSM_PATH%" set ComputerAgent AppRestartDelay 10000 || goto :error

REM Start the service
echo Starting service...
"%NSSM_PATH%" start ComputerAgent || goto :error

REM Wait for service to start and verify it's running
echo Waiting for service to start...
for /l %%i in (1,1,10) do (
    timeout /t 1 /nobreak >nul
    sc query ComputerAgent | find "RUNNING" >nul
    if not errorlevel 1 (
        echo Service is running!
        goto :check_agent
    )
)

echo Service failed to start. Checking logs...
goto :show_logs

:check_agent
REM Verify agent is working by checking logs
timeout /t 2 /nobreak >nul
if exist "%LOG_PATH%" (
    findstr /c:"Connected to relay server" "%LOG_PATH%" >nul
    if not errorlevel 1 (
        echo Agent connected to relay server successfully!
        goto :success
    )
)

echo Agent not connected yet, checking logs...

:show_logs
echo.
echo Service Logs:
if exist "%LOG_PATH%" (
    type "%LOG_PATH%"
) else (
    echo No agent log found at: %LOG_PATH%
)

if exist "%INSTALL_DIR%\service_stderr.log" (
    echo.
    echo Service Error Log:
    type "%INSTALL_DIR%\service_stderr.log"
)
goto :error

:error
echo.
echo Installation failed! Please check the errors above.
exit /b 1

:success
echo.
echo Computer agent service has been installed and started successfully.
echo.
echo Log files:
echo   Service Log: %LOG_PATH%
echo   STDOUT Log: %INSTALL_DIR%\service_stdout.log
echo   STDERR Log: %INSTALL_DIR%\service_stderr.log
echo.
echo To manage the service, use these commands:
echo   %NSSM_PATH% start ComputerAgent   - Start the service
echo   %NSSM_PATH% stop ComputerAgent    - Stop the service
echo   %NSSM_PATH% restart ComputerAgent - Restart the service
echo   %NSSM_PATH% remove ComputerAgent  - Uninstall the service
echo.
pause
