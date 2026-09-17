@echo off
cd /d C:\path\to\your\network_monitor
call .venv\Scripts\activate.bat
python registration.py 7 >> logs\step7_liveness.log 2>&1