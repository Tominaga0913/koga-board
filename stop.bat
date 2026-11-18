@echo off
rem Stops everything started by start.bat (use this if you closed the start window).
powershell -NoProfile -ExecutionPolicy Bypass -Command "$f = Join-Path '%~dp0' 'logs\pids.txt'; if (Test-Path $f) { Get-Content $f | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }; Remove-Item $f; Write-Host 'Stopped.' } else { Write-Host 'Nothing to stop.' }"
pause
