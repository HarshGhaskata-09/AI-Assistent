@echo off
REM Run AI Assistent without virtual environment

REM Use system Python directly
set PYTHON_PATH=C:\Users\HARSH\AppData\Local\Microsoft\WindowsApps\python.exe

REM Check if system Python exists
if not exist "%PYTHON_PATH%" (
    echo System Python not found at %PYTHON_PATH%
    echo Using default python command...
    set PYTHON_PATH=python
)

REM Run AI Assistent
echo Starting AI Assistent Voice Assistant...
%PYTHON_PATH% ai_assistent.py %*

pause
