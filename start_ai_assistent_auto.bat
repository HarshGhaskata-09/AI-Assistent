@echo off
REM start_ai_assistent_auto.bat - Start AI Assistent in Background Mode

REM Change to the script directory
cd /d "%~dp0"

echo ============================================
echo Starting HIRR in Background Mode...
echo ============================================

REM Start AI Assistent in background mode (wake word activation)
python ai_assistent.py --background

pause
