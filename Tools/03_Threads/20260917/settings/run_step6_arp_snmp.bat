@echo off
cd /d C:\path\to\your\network_monitor
call .venv\Scripts\activate.bat
python registration.py 6 >> logs\step6_arp.log 2>&1