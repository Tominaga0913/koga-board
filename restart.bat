@echo off
rem Reload the boards with the latest code. Public URLs stay the same.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0restart.ps1"
