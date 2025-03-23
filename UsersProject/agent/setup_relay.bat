@echo off
echo Setting up Relay Server...

REM Get absolute paths
set "INSTALL_DIR=%CD%"
set "VENV_DIR=%INSTALL_DIR%\relay_env"
set "PYTHON_PATH=%VENV_DIR%\Scripts\python.exe"
set "SCRIPT_PATH=%INSTALL_DIR%\relay_server.py"
set "LOG_PATH=%INSTALL_DIR%\relay.log"

REM Create virtual environment if it doesn't exist
if not exist "%VENV_DIR%" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
)

REM Activate virtual environment and install packages
call "%VENV_DIR%\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Download NSSM if not present
if not exist "%INSTALL_DIR%\nssm.exe" (
    echo Downloading NSSM...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile 'nssm.zip'}"
    powershell -Command "& {Expand-Archive -Path 'nssm.zip' -DestinationPath 'nssm' -Force}"
    copy "nssm\nssm-2.24\win64\nssm.exe" "%INSTALL_DIR%\nssm.exe"
    rd /s /q nssm
    del nssm.zip
)

REM Kill any existing Python processes using port 8765
echo Cleaning up any existing processes...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8765"') do (
    echo Killing process %%a using port 8765...
    taskkill /F /PID %%a 2>nul
)
timeout /t 2 >nul

REM Stop and remove existing service if it exists
echo Checking for existing service...
"%INSTALL_DIR%\nssm.exe" status RelayServer >nul 2>&1
if not ERRORLEVEL 1 (
    echo Stopping existing service...
    "%INSTALL_DIR%\nssm.exe" stop RelayServer
    "%INSTALL_DIR%\nssm.exe" remove RelayServer confirm
    timeout /t 2
)

REM Configure and install service
echo Installing relay service...
"%INSTALL_DIR%\nssm.exe" install RelayServer "%PYTHON_PATH%"
"%INSTALL_DIR%\nssm.exe" set RelayServer AppParameters "%SCRIPT_PATH%"
"%INSTALL_DIR%\nssm.exe" set RelayServer DisplayName "Computer Management Relay Server"
"%INSTALL_DIR%\nssm.exe" set RelayServer Description "Relay server for computer management system"
"%INSTALL_DIR%\nssm.exe" set RelayServer AppDirectory "%INSTALL_DIR%"
"%INSTALL_DIR%\nssm.exe" set RelayServer AppEnvironmentExtra "PATH=%VENV_DIR%\Scripts;%PATH%"
"%INSTALL_DIR%\nssm.exe" set RelayServer Start SERVICE_AUTO_START
"%INSTALL_DIR%\nssm.exe" set RelayServer ObjectName LocalSystem
"%INSTALL_DIR%\nssm.exe" set RelayServer AppStdout "%LOG_PATH%"
"%INSTALL_DIR%\nssm.exe" set RelayServer AppStderr "%LOG_PATH%"

REM Set failure actions to restart
"%INSTALL_DIR%\nssm.exe" set RelayServer AppExit Default Restart
"%INSTALL_DIR%\nssm.exe" set RelayServer AppRestartDelay 10000

REM Start the service
echo Starting relay service...
"%INSTALL_DIR%\nssm.exe" start RelayServer

REM Check service status with retries
echo Checking service status...
set max_retries=5
set retry_count=0
:check_status
timeout /t 2 >nul
"%INSTALL_DIR%\nssm.exe" status RelayServer | findstr "SERVICE_RUNNING" >nul
if ERRORLEVEL 1 (
    set /a retry_count+=1
    if %retry_count% lss %max_retries% (
        echo Service not running yet, checking again...
        goto check_status
    ) else (
        echo Service failed to start after %max_retries% attempts
        if exist "%LOG_PATH%" type "%LOG_PATH%"
        exit /b 1
    )
) else (
    echo Service is running successfully!
)

echo.
echo Please make sure port 8765 is open in the firewall.
echo To check logs, view: %LOG_PATH%

REM Add firewall rule if it doesn't exist
echo Checking firewall rule...
netsh advfirewall firewall show rule name="Relay Server" >nul 2>&1
if ERRORLEVEL 1 (
    echo Adding firewall rule...
    netsh advfirewall firewall add rule name="Relay Server" dir=in action=allow protocol=TCP localport=8765
)

pause
