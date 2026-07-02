@echo off
REM Inicia o alarme com console visivel (util pra debug e primeiro login OAuth)
cd /d "%~dp0"
python "%~dp0alarme.py"
pause
