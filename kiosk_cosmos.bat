@echo off
rem Display PC: show the Koga bus board and the original Nishitetsu Bus Navi page, switching every 10 s.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0kiosk.ps1" -Site cosmos
