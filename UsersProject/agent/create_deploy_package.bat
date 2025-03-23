@echo off
echo Creating deployment package...

REM Create deploy directory
set "DEPLOY_DIR=agent_deploy"
if exist "%DEPLOY_DIR%" rd /s /q "%DEPLOY_DIR%"
mkdir "%DEPLOY_DIR%"

REM Copy required files
copy computer_agent.py "%DEPLOY_DIR%\"
copy requirements.txt "%DEPLOY_DIR%\"
copy agent_setup.bat "%DEPLOY_DIR%\"

REM Create .env file with correct settings
echo RELAY_URL=ws://192.168.72.19:8765> "%DEPLOY_DIR%\.env"
echo COMPUTER_AGENT_TOKEN=JXpV2Tl9UR1LQrhnhPQrzJ6GPCFlnEIzzlAkN3PkeT8>> "%DEPLOY_DIR%\.env"

echo.
echo Deployment package created in: %DEPLOY_DIR%
echo Copy this folder to remote computers and run agent_setup.bat
echo.
pause
