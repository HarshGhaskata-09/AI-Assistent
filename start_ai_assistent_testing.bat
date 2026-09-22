@echo off
REM start_ai_assistent_testing.bat - Start AI Assistent in Testing Mode

REM Change to the script directory
cd /d "%~dp0"

echo ============================================
echo Starting HIRR in Testing Mode...
echo ============================================

REM Start AI Assistent in testing mode (direct commands, no wake word)
python ai_assistent.py --testing

pause
