# ai_assistent.py - AI ASSISTENT - ALWAYS AUTO-START MODE

import time
import threading
import sys
import os
import argparse

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now imports will work
from modules.voice import VoiceHandler
from modules.commands import CommandProcessor
from database.db_manager import DatabaseManager

class AIAssistent:
    def __init__(self, use_win32_voice=True, voice_gender='female'):
        """
        Initialize complete AI Assistent system
        Args:
            use_win32_voice (bool): Use win32com for better audio
            voice_gender (str): 'male' or 'female' (default: 'female')
        """
        print("\n" + "="*50)
        print("🚀 STARTING AI ASSISTENT")
        print("="*50)
        
        # Initialize all modules
        try:
            self.voice = VoiceHandler(use_win32=use_win32_voice, voice_gender=voice_gender)
            print("✅ Voice module initialized")
        except Exception as e:
            print(f"❌ Voice module failed: {e}")
            self.voice = None
        
        try:
            self.processor = CommandProcessor(self.voice)
            print("✅ Command processor initialized")
        except Exception as e:
            print(f"❌ Command processor failed: {e}")
            self.processor = None
        
        try:
            self.db = DatabaseManager()
            print("✅ Database manager initialized")
        except Exception as e:
            print(f"❌ Database failed: {e}")
            self.db = None
        
        # State
        self.running = True
        self.active = False
        
        print("="*50)
        if self.voice and self.processor:
            print("✅ AI Assistent initialized successfully!\n")
        else:
            print("⚠️ AI Assistent initialized with some errors\n")
    
    def wake_word_listener(self):
        """Background thread to listen for wake word with wave animation"""
        if not self.voice:
            print("❌ Voice module not available")
            return
        
        # Announce ready status
        print("\n🎤 AI Assistent is now listening in background...")
        print("💡 Say: 'hello', 'hey', 'hi', or 'ai assistent' to activate")
        print("⏸️  Press Ctrl+C to stop\n")
        
        # Speak welcome message
        self.voice.speak("AI Assistent is ready and listening in background!")
        
        while self.running:
            # Listen for wake word
            if self.voice.listen_for_wake_word_with_indicator():
                self.active = True
                
                # Respond with cool message
                import random
                responses = [
                    "Yes? I'm listening.",
                    "I'm listening boss!",
                    "Yes boss, I'm ready!",
                    "I'm here, what do you need?",
                    "Ready to help boss!",
                    "At your service!"
                ]
                response_text = random.choice(responses)
                
                self.voice.speak(response_text)
                
                # Get actual command
                command = self.voice.listen(timeout=5)
                
                if command and self.processor:
                    # Process the command
                    print(f"\n📝 Processing: {command}")
                    
                    # Parse
                    print("⚙️ Parsing...")
                    parsed = self.processor.parse(command)
                    print(f"✅ Intent: {parsed['intent']}")
                    
                    # Execute
                    print("⚙️ Executing...")
                    response = self.processor.execute(parsed)
                    
                    print(f"✅ Response: {response}")
                    print(f"🤖 AI Assistent: {response}")
                    print("🔊 Speaking response...")
                    self.voice.speak(response)
                    
                    print("✅ Speech completed!")
                    
                    # If exit command, stop
                    if parsed['intent'] == 'exit':
                        self.running = False
                        break
                elif command:
                    # Echo what was said
                    print(f"📝 Echoing: {command}")
                    
                    self.voice.speak(f"You said: {command}")
                    print("✅ Echo completed!")
                
                self.active = False
                
                # Show ready message again
                print("\n🎤 Ready... (listening for wake word)")
            
            time.sleep(0.1)
    
    def run_background(self):
        """Run AI Assistent in background mode (wake word activation)"""
        if not self.voice:
            print("❌ Cannot run: Voice module not available")
            return
        
        # Start wake word listener in background
        listener_thread = threading.Thread(target=self.wake_word_listener)
        listener_thread.daemon = True
        listener_thread.start()
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.running = False
            self.voice.speak("Goodbye boss!")
            print("\n👋 AI Assistent stopped")
    
    def run_testing(self):
        """Run AI Assistent in testing mode (direct commands, no wake word)"""
        if not self.voice:
            print("❌ Cannot run: Voice module not available")
            return
        
        print("\n" + "="*50)
        print("🧪 TESTING MODE - Direct command input")
        print("="*50)
        print("No wake word needed - just speak your command!")
        print("Say 'exit' to quit")
        print("="*50 + "\n")
        
        self.voice.speak("Testing mode activated boss! Speak your commands directly.")
        
        while self.running:
            print("\n🎤 Listening for command...")
            command = self.voice.listen(timeout=5)
            
            if command and self.processor:
                print(f"📝 You said: {command}")
                parsed = self.processor.parse(command)
                response = self.processor.execute(parsed)
                
                print(f"🤖 AI Assistent: {response}")
                self.voice.speak(response)
                
                if parsed['intent'] == 'exit':
                    self.running = False
                    break
            
            time.sleep(0.5)


# =====================================================
# MAIN ENTRY POINT
# =====================================================

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="AI Assistent")
    parser.add_argument("--background", "-b", action="store_true", help="Background mode")
    parser.add_argument("--testing", "-t", action="store_true", help="Testing mode")
    parser.add_argument("--voice", choices=["male", "female"], default="female")
    args = parser.parse_args()
    
    ai_assistent = AIAssistent(voice_gender=args.voice)
    
    if args.background:
        ai_assistent.run_background()
    elif args.testing:
        ai_assistent.run_testing()
    else:
        print("Use --background or --testing mode")
