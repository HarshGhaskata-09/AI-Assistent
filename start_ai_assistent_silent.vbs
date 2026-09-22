' start_ai_assistent_silent.vbs - Start AI Assistent silently in background (no console window)

Set WshShell = CreateObject("WScript.Shell")

' Get the directory where this script is located
scriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)

' Change to script directory and run AI Assistent in background mode
WshShell.CurrentDirectory = scriptDir
WshShell.Run "python ai_assistent.py --background", 0, False

' 0 = Hidden window
' False = Don't wait for completion
