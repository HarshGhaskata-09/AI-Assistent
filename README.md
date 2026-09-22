# AI Assistent

**AI Assistent** is an offline, privacy-first, Python-based Voice Assistant designed to execute commands, track computer activity, manage habits, and answer queries naturally. It integrates powerful voice processing and local database management to run fully on your local machine without depending on cloud APIs for core speech recognition.

## Key Features

*   **Offline Voice Recognition:** Uses the local `Whisper` model for accurate and offline speech-to-text conversion.
*   **Natural Text-to-Speech:** Uses Windows SAPI (`win32com`) or `pyttsx3` for friendly voice output.
*   **Always-On Background Mode:** Runs silently in the background and activates instantly when it hears its wake word (e.g., *"AI Assistent"*, *"Assistant"*, *"Hey Assistant"*).
*   **Intelligent Command Processing:** Parses your natural language intents to perform actions like telling the time, opening applications, telling jokes, and more.
*   **Activity & Habit Tracking:** Monitors the applications you use and logs interactions into a local SQLite database (`data/ai_assistent.db`) to track your routines.
*   **Gujarati Commands Support:** Understands select regional commands.

---

## How It Works (Project Architecture)

The assistant uses a modular architecture built entirely in Python:

1.  **Voice Module (`modules/voice.py`):**
    Handles everything related to audio. It actively listens for the wake word using an efficient threshold algorithm. When the wake word is detected, it records your command, processes it locally via Whisper, and converts it to text.
2.  **Command Processor (`modules/commands.py` & `thinking_engine.py`):**
    The text is parsed to determine your *intent* (e.g., greeting, asking for time, opening an app). The thinking engine decides the best way to respond or execute the action.
3.  **Database Manager (`database/db_manager.py`):**
    Logs every interaction, wake word activation, and activity duration securely on your local machine. It stores preferences and tracks habits.
4.  **Action Execution (`ai_assistent.py`):**
    The main script orchestrates all these modules. It performs the required action (like opening Notepad, fetching information) and then passes the textual response back to the Voice Module to be spoken out loud.

---

## Setup & Installation

1. **Download the project:**
   - Click on the green **Code** button at the top of the repository and select **Download ZIP**.
   - Extract the downloaded ZIP file to your preferred folder.
   - Open a terminal or command prompt and navigate to the extracted folder (`cd ai-assistent-main`).

2. **Install the required dependencies:**
   Make sure you have Python 3.10+ installed.
   ```bash
   pip install -r requirements.txt
   ```

3. **Required System Setup (Windows):**
   - Ensure your microphone is properly connected and permitted in Windows settings.
   - For optimal voices, ensure Windows English TTS voices (e.g., Zira or David) are installed.

---

## Running the Assistant

There are a few simple batch scripts provided to run the assistant easily without using the terminal every time:

*   **`run_ai_assistent.bat`**: Runs the main assistant normally.
*   **`start_ai_assistent_testing.bat`**: Runs the assistant in testing mode (direct command input without waiting for a wake word).
*   **`start_ai_assistent_auto.bat`**: Runs the assistant in background mode (listens for wake words continuously).
*   **`start_ai_assistent_silent.vbs`**: Starts the assistant completely hidden in the background without a console window.

Alternatively, you can run it manually via python:
```bash
python ai_assistent.py --background
```

## Project Structure

```
├── ai_assistent.py              # Main entry point for the assistant
├── database/                    # SQLite Database logic (db_manager.py)
├── modules/                     # Core logic modules
│   ├── voice.py                 # TTS and STT (Whisper) logic
│   ├── commands.py              # Intent parsing and execution
│   ├── thinking_engine.py       # Decision making engine
│   └── activity_integration.py  # Computer usage tracking
├── data/                        # Contains the local SQLite database
├── logs/                        # Daily operation logs
└── requirements.txt             # Python dependencies
```

## Privacy

This project focuses on your privacy. The voice processing (using Whisper) and data storage (SQLite) happen completely locally on your computer. None of your voice data or usage history is sent to the cloud.
