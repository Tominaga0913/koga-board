@echo off
rem Display PC: open the Yatabi board fullscreen (no switching).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0kiosk.ps1" -Site yatabi
