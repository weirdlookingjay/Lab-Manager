@echo off
echo Stopping and removing Computer Agent Service...

REM Stop and remove the service
python computer_agent.py stop
python computer_agent.py remove

echo Done! Computer Agent Service has been removed.
pause
