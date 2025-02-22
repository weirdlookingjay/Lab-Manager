@echo off
cd /d D:\Code\aw\labv2
call .\venv\Scripts\activate.bat
python manage.py run_scheduled_scans
