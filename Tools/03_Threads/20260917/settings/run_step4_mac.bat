@echo off
cd /d C:\path\to\your\network_monitor
call .venv\Scripts\activate.bat
python registration.py 4 >> logs\step4_mac.log 2>&1