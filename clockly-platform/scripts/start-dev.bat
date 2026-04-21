@echo off
pushd "%~dp0\.."
powershell.exe -ExecutionPolicy Bypass -File "scripts\start-dev.ps1"
popd
pause
