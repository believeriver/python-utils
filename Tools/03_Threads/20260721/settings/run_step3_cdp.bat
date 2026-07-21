@echo off
cd /d C:\path\to\your\network_monitor
call .venv\Scripts\activate.bat
python registration.py 3 >> logs\step3_cdp.log 2>&1