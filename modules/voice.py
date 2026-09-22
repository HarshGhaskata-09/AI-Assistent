# modules/voice.py - COMPLETE UPDATED VERSION WITH FLEXIBLE WAKE WORDS (FIXED)

import pyttsx3
import speech_recognition as sr
import time
import os
import sys
import re
import random

class VoiceHandler:
    def __init__(self, use_win32=False, voice_gender='female'):
        """
        Initialize voice engine and speech recognition
        Args:
            use_win32 (bool): Use win32com instead of pyttsx3
            voice_gender (str): 'male' or 'female' (default: 'female')
        """
        print("🎤 Initializing AI Assistent's voice...")
        
        self.use_win32 = use_win32
        self.win32_speaker = None
        self.voice_gender = voice_gender.lower()
        
        # Text-to-Speech Engine (AI Assistent speaks)
        if use_win32:
            # Use Windows SAPI directly via win32com
            try:
                import win32com.client
                self.win32_speaker = win32com.client.Dispatch("SAPI.SpVoice")
                
                # Set voice based on gender preference
                voices = self.win32_speaker.GetVoices()
                voice_set = False
                
                if self.voice_gender == 'female':
                    # Look for Zira (female English voice)
                    for i in range(voices.Count):
                        voice = voices.Item(i)
                        voice_name = voice.GetDescription()
                        if 'zira' in voice_name.lower():
                            self.win32_speaker.Voice = voice
                            print(f"✅ Using female voice: {voice_name}")
                            voice_set = True
                            break
                else:
                    # Look for David (male English voice)
                    for i in range(voices.Count):
                        voice = voices.Item(i)
                        voice_name = voice.GetDescription()
                        if 'david' in voice_name.lower():
                            self.win32_speaker.Voice = voice
                            print(f"✅ Using male voice: {voice_name}")
                            voice_set = True
                            break
                
                if not voice_set:
                    print(f"⚠️ Preferred voice not found, using default")
                
                self.win32_speaker.Volume = 100
                self.win32_speaker.Rate = -1  # Slightly slower
                print("✅ Text-to-Speech engine initialized (win32com)")
                self.engine = None
            except Exception as e:
                print(f"❌ Failed to initialize win32com: {e}")
                print("   Falling back to pyttsx3...")
                self.use_win32 = False
                try:
                    self.engine = pyttsx3.init()
                    print("✅ Text-to-Speech engine initialized (pyttsx3)")
                except Exception as e2:
                    print(f"❌ Failed to initialize TTS engine: {e2}")
                    self.engine = None
        else:
            # Use pyttsx3
            try:
                self.engine = pyttsx3.init()
                print("✅ Text-to-Speech engine initialized (pyttsx3)")
            except Exception as e:
                print(f"❌ Failed to initialize TTS engine: {e}")
                print("   Will continue without speech output")
                self.engine = None
        
        # Speech Recognition Engine (AI Assistent listens)
        try:
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            print("✅ Speech recognition engine initialized")
        except Exception as e:
            print(f"❌ Failed to initialize microphone: {e}")
            print("   Please check your microphone connection")
            self.recognizer = None
            self.microphone = None
        
        # Wake word variations - UPDATED with more options
        self.wake_words = [
            'AI Assistent',           # Main name
            'hir',            # Short version
            'here',           # Similar sounding
            'hear',           # Similar sounding
            'her',            # Similar sounding
            'hur',            # Similar sounding
        ]
        
        # Wake phrases - UPDATED with common combinations
        self.wake_phrases = [
            'hello AI Assistent',
            'hello hir',
            'hey ai assistent',
            'hey hir',
            'hi AI Assistent',
            'hi hir',
            'hello here',
            'hey here',
            'hi here',
            'hello hear',
            'hey hear',
            'okay AI Assistent',
            'ok AI Assistent',
            'okay hir',
            'hey',
            'hello',
            'hi',
            'yo',
            'wake up',
            'are you there',
            'AI Assistent are you there',
            'hey siri',        # Common mistake
            'hey google',      # Common mistake
            'alexa'            # Common mistake
        ]
        
        # Configure voice if engine is available
        if self.engine:
            self.set_voice()
        
        # Adjust for ambient noise if microphone is available
        if self.microphone:
            self.adjust_for_noise()
        
        print("✅ Voice Handler ready!")
        print(f"   Wake words: {', '.join(self.wake_words)}")
        print(f"   Wake phrases: {', '.join(self.wake_phrases[:5])}...")
    
    def adjust_for_noise(self):
        """Adjust microphone for ambient noise with longer duration for accuracy"""
        try:
            with self.microphone as source:
                print("🔊 Tuning microphone for your room... Please wait (1.5s)")
                # Better noise adjustment duration
                self.recognizer.adjust_for_ambient_noise(source, duration=1.5)
                # Set dynamic energy threshold to listen better
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.energy_threshold = 4500  # Aggressive VAD filter for fans/AC
                # Whisper processes chunks better if they are tight:
                self.recognizer.pause_threshold = 1.0  # Cut off slightly faster to prevent run-ons
                # Wait for at least 0.4s of silence before starting a phrase
                self.recognizer.non_speaking_duration = 0.4
                print("✅ Microphone tuning complete! Ready to hear 'AI Assistent'")
        except Exception as e:
            print(f"⚠️ Noise adjustment failed: {e}")
    
    def set_voice(self):
        """Set a friendly voice for AI Assistent"""
        try:
            voices = self.engine.getProperty('voices')
            
            # Try to set female voice (index 1), fallback to male
            if len(voices) > 1:
                self.engine.setProperty('voice', voices[1].id)
                print(f"🎵 Using voice: {voices[1].name}")
            else:
                self.engine.setProperty('voice', voices[0].id)
                print(f"🎵 Using voice: {voices[0].name}")
            
            # Adjust speed and volume for better clarity
            self.engine.setProperty('rate', 150)  # Slower speed for clarity (was 175)
            self.engine.setProperty('volume', 1.0)  # Maximum volume (was 0.9)
            
            print(f"🔊 Voice settings: Rate=150, Volume=1.0")
        except Exception as e:
            print(f"⚠️ Voice configuration failed: {e}")
    
    def speak(self, text):
        """
        AI Assistent speaks the given text
        Args: text (str) - What AI Assistent should say
        """
        print(f"\n🤖 AI Assistent: {text}")
        
        # Use win32com if available
        if self.use_win32 and self.win32_speaker:
            try:
                print("🔊 Speaking (win32)...")
                self.win32_speaker.Speak(text)
                print("✅ Speech completed")
                return
            except Exception as e:
                print(f"❌ win32 speech error: {e}")
                # Fall through to pyttsx3
        
        # Use pyttsx3
        if not self.engine:
            print(f"🤖 [TTS Disabled] AI Assistent would say: {text}")
            return
            
        try:
            # Clear any pending speech
            self.engine.stop()
            
            # Add the text to speak
            self.engine.say(text)
            
            # Run and wait for completion
            print("🔊 Speaking (pyttsx3)...")
            self.engine.runAndWait()
            print("✅ Speech completed")
            
        except Exception as e:
            print(f"❌ Speech error: {e}")
            # Try to recover
            try:
                self.engine = pyttsx3.init()
                self.set_voice()
                self.engine.say(text)
                self.engine.runAndWait()
                print("✅ Speech completed (after recovery)")
            except:
                print(f"❌ Could not recover TTS engine")
    
    def listen(self, timeout=None, phrase_limit=None):
        """
        Listen for voice input and convert to text
        Args:
            timeout (int): Seconds to wait for speech
            phrase_limit (int): Max seconds for a phrase
        Returns:
            str: The spoken text, or empty string if failed
        """
        if not self.recognizer or not self.microphone:
            print("❌ Speech recognition not available")
            return ""
        
        print("\n👂 Listening... (speak now)")
        
        try:
            with self.microphone as source:
                # Listen with timeout
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_limit
                )
            # Convert speech to text using OFFLINE Whisper local model
            print("🧠 Processing offline with Whisper...")
            text = self.recognizer.recognize_whisper(audio, model="tiny", language="english").lower().strip()
            
            # Whisper Anti-Hallucination Guard (Static Noise)
            hallucinations = ["thank you.", "thank you", "bye.", "you.", "i don't know.", "am i?", ""]
            if text in hallucinations:
                return ""
            
            print(f"📝 Recognized: {text}")
            return text

            
        except sr.WaitTimeoutError:
            print("⏰ No speech detected")
            return ""
        except sr.UnknownValueError:
            print("🤔 Could not understand audio")
            return ""
        except sr.RequestError as e:
            print(f"❌ Recognition service error: {e}")
            return ""
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return ""
    
    def is_wake_word_detected(self, text):
        """
        Check if text contains any wake word or phrase
        Args: text (str) - The recognized speech
        Returns: bool - True if wake word detected
        """
        if not text:
            return False
        
        text = text.lower().strip()
        
        # Whisper Anti-Hallucination Guard
        hallucinations = ["thank you.", "thank you", "bye.", "you.", "i don't know.", "am i?", ""]
        if text in hallucinations:
            return False
        
        # Strict wake words specifically tuned to not catch random Whisper noise
        ai_assistent_sounds = ['AI Assistent', 'here', 'hir', 'hello', 'hey ai assistent', 'hi', 'hey']
        for s in ai_assistent_sounds:
            if re.search(r'\b' + re.escape(s) + r'\b', text):
                print(f"✨ Accurate match for 'AI Assistent' (detected as '{s}')")
                return True
        
        return False
    
    def listen_for_wake_word(self, timeout=None):
        """
        Continuously listen for any wake word/phrase with better detection
        Args:
            timeout (int): Seconds to wait for speech
        Returns:
            bool: True if wake word detected
        """
        if not self.recognizer or not self.microphone:
            return False
        
        try:
            with self.microphone as source:
                # Quick ambient noise adjustment
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                # Listen for wake word
                print(f"\r🔊 Listening for wake word... (say hello, hey, AI Assistent, etc.)", end="", flush=True)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=2)
            
            # Process audio with local Whisper
            text = self.recognizer.recognize_whisper(audio, model="tiny", language="english").lower().strip()
            
            # Check for wake word using our flexible method
            if self.is_wake_word_detected(text):
                print(f"\n✨ Wake word detected! You said: '{text}'")
                return True
            else:
                # For debugging - show what was heard but not recognized as wake
                print(f"\r👂 Heard: '{text}' (not wake word)", end="", flush=True)
            
        except sr.WaitTimeoutError:
            # No speech - normal, just continue
            pass
        except sr.UnknownValueError:
            # Speech but couldn't understand
            print(f"\r🤔 Heard something but couldn't understand", end="", flush=True)
        except sr.RequestError as e:
            print(f"\n❌ Network error: {e}")
        except Exception as e:
            print(f"\n❌ Error: {e}")
        
        return False
    
    def listen_for_wake_word_with_indicator(self, wake_word=None):
        """
        Better version with visual indicator and flexible detection
        Args:
            wake_word (str, optional): Specific wake word to listen for
        Returns:
            bool: True if wake word detected
        """
        if not self.recognizer or not self.microphone:
            print("❌ Microphone not available")
            return False
        
        # Use the provided wake_word or default to None (will use all wake words)
        if wake_word:
            print(f"\n🎤 Say '{wake_word}' to activate...")
        else:
            # Different indicator messages for variety
            indicators = [
                "🎤 Say 'hello', 'hey', 'AI Assistent' or just 'hi'...",
                "🔊 Listening... (try: hey, hello, AI Assistent)",
                "👂 I'm here! Say something like 'hey ai assistent'...",
                "🎙️ Wake me with 'hello', 'hi', or just 'AI Assistent'",
                "🔉 Waiting for wake word... (try: 'hey' or 'AI Assistent')"
            ]
            
            # Rotate through indicators
            indicator = random.choice(indicators)
            print(f"\n{indicator}")
        
        try:
            with self.microphone as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                # Listen with timeout
                audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=2)
            
            # Process the audio with Whisper
            print("🔄 Processing offline...")
            text = self.recognizer.recognize_whisper(audio, model="tiny", language="english").lower()
            print(f"📝 Heard: '{text}'")

            
            # Check for wake word using flexible method
            if wake_word:
                # Check only the specific wake word
                if (wake_word.lower() in text or 
                    f"hello {wake_word.lower()}" in text or 
                    f"hey {wake_word.lower()}" in text or
                    f"hi {wake_word.lower()}" in text):
                    print(f"✨ Wake word '{wake_word}' detected!")
                    return True
            else:
                # Use the flexible detection from is_wake_word_detected
                if self.is_wake_word_detected(text):
                    print(f"✨ Wake word detected! Activating ai_assistent...")
                    return True
            
            print(f"❌ Not a wake word. Try saying 'hey ai assistent', 'hello', or just 'AI Assistent'")
            
        except sr.WaitTimeoutError:
            print("⏰ No speech detected")
        except sr.UnknownValueError:
            print("🤔 Could not understand - please speak clearly")
        except sr.RequestError as e:
            print(f"❌ Recognition error: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        return False
    
    def test_microphone(self):
        """Test if microphone is working"""
        if not self.recognizer or not self.microphone:
            print("❌ Microphone not available")
            return False
            
        print("\n🎤 Testing microphone...")
        print("Please say something (you have 3 seconds)")
        
        text = self.listen(timeout=3)
        
        if text:
            print(f"✅ Microphone working! Heard: {text}")
            self.speak(f"I heard you say: {text}")
            return True
        else:
            print("❌ Microphone test failed")
            print("\nTroubleshooting tips:")
            print("  1. Check if microphone is connected")
            print("  2. Check microphone permissions in Windows")
            print("  3. Try a different microphone")
            return False
    
    def list_microphones(self):
        """List all available microphones"""
        try:
            print("\n🎤 Available microphones:")
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                print(f"  {index}: {name}")
            return True
        except Exception as e:
            print(f"❌ Failed to list microphones: {e}")
            return False
    
    def set_microphone(self, device_index):
        """Set specific microphone by index"""
        try:
            self.microphone = sr.Microphone(device_index=device_index)
            print(f"✅ Microphone set to device {device_index}")
            self.adjust_for_noise()
            return True
        except Exception as e:
            print(f"❌ Failed to set microphone: {e}")
            return False
    
    def set_voice_speed(self, speed):
        """Change how fast AI Assistent speaks"""
        if self.engine:
            self.engine.setProperty('rate', speed)
            print(f"⚡ Voice speed set to {speed}")
    
    def set_voice_volume(self, volume):
        """Change AI Assistent's volume (0.0 to 1.0)"""
        if self.engine:
            self.engine.setProperty('volume', max(0.0, min(1.0, volume)))
            print(f"🔊 Voice volume set to {volume}")
    
    def get_wake_words_list(self):
        """Get list of accepted wake words/phrases"""
        return {
            'exact_words': self.wake_words,
            'phrases': self.wake_phrases,
            'greetings': ['hello', 'hey', 'hi', 'yo']
        }


# =====================================================
# SIMPLE DEMO - Run this file directly to test
# =====================================================

def demo_mode():
    """Simple demo to test voice functionality"""
    print("=" * 50)
    print("🔊 AI Assistent VOICE ASSISTANT - DEMO MODE")
    print("=" * 50)
    print("Commands you can say:")
    print("  • 'hello' - AI Assistent greets you")
    print("  • 'time' - Tell current time")
    print("  • 'test' - Test microphone")
    print("  • 'list' - List available microphones")
    print("  • 'exit' - Quit demo")
    print("=" * 50)
    
    # Create voice handler
    ai_assistent = VoiceHandler()
    
    # Welcome message
    ai_assistent.speak("Hello! I am ai_assistent. Say something to test me.")
    
    while True:
        # Listen for command
        command = ai_assistent.listen(timeout=5)
        
        if command:
            if "hello" in command or "hi" in command:
                ai_assistent.speak("Hello! How can I help you?")
            
            elif "time" in command:
                current_time = time.strftime("%I:%M %p")
                ai_assistent.speak(f"The time is {current_time}")
            
            elif "test" in command:
                ai_assistent.test_microphone()
            
            elif "list" in command:
                ai_assistent.list_microphones()
            
            elif "exit" in command or "quit" in command or "bye" in command:
                ai_assistent.speak("Goodbye! Call me anytime.")
                break
            
            else:
                ai_assistent.speak(f"You said: {command}")
        
        # Small delay between listens
        time.sleep(0.5)

# =====================================================
# WAKE WORD DEMO - Run to test wake word activation
# =====================================================

def wake_word_demo():
    """Demo with flexible wake word detection"""
    print("=" * 50)
    print("🔊 AI Assistent WAKE WORD DEMO - FLEXIBLE DETECTION")
    print("=" * 50)
    print("You can wake me by saying:")
    print("  • 'AI Assistent' (main name)")
    print("  • 'hir' (short version)")
    print("  • 'hey ai assistent'")
    print("  • 'hello AI Assistent'")
    print("  • 'hi AI Assistent'")
    print("  • Just 'hey', 'hello', or 'hi'")
    print("=" * 50)
    print("Press Ctrl+C to exit")
    print("=" * 50)
    
    ai_assistent = VoiceHandler()
    ai_assistent.speak("Wake word demo started. Try saying hello, hey, or AI Assistent to wake me!")
    
    try:
        while True:
            if ai_assistent.listen_for_wake_word_with_indicator():
                ai_assistent.speak("Yes? I'm listening!")
                
                # Get actual command
                command = ai_assistent.listen(timeout=5)
                
                if command:
                    if "time" in command:
                        current_time = time.strftime("%I:%M %p")
                        ai_assistent.speak(f"The time is {current_time}")
                    elif "joke" in command:
                        ai_assistent.speak("Why don't scientists trust atoms? Because they make up everything!")
                    elif "bye" in command or "exit" in command:
                        ai_assistent.speak("Goodbye!")
                        break
                    else:
                        ai_assistent.speak(f"You said: {command}")
                else:
                    ai_assistent.speak("I didn't catch that. Try again.")
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n👋 Demo ended")

# =====================================================
# MICROPHONE SETUP TOOL
# =====================================================

def microphone_setup():
    """Help user set up their microphone"""
    print("=" * 50)
    print("🎤 AI Assistent MICROPHONE SETUP")
    print("=" * 50)
    
    ai_assistent = VoiceHandler()
    
    # List available microphones
    ai_assistent.list_microphones()
    
    # Ask user to select microphone
    try:
        choice = input("\nEnter microphone number (or press Enter to use default): ").strip()
        if choice:
            ai_assistent.set_microphone(int(choice))
    except ValueError:
        print("⚠️ Invalid input, using default microphone")
    
    # Test the microphone
    ai_assistent.test_microphone()

# =====================================================
# WAKE WORD TESTER - See what triggers wake word
# =====================================================

def wake_word_tester():
    """Test what phrases trigger the wake word"""
    print("=" * 50)
    print("🎯 WAKE WORD TESTER")
    print("=" * 50)
    print("Say different phrases to see what wakes AI Assistent")
    print("Press Ctrl+C to exit")
    print("=" * 50)
    
    ai_assistent = VoiceHandler()
    
    try:
        while True:
            if ai_assistent.listen_for_wake_word_with_indicator():
                print("✅ This would wake AI Assistent!")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n👋 Testing ended")

# =====================================================
# MAIN - Choose which demo to run
# =====================================================

if __name__ == "__main__":
    print("\n🎙️ AI Assistent VOICE MODULE")
    print("Choose mode:")
    print("1. Wake word demo (flexible detection)")
    print("2. Simple command demo")
    print("3. Microphone test only")
    print("4. Microphone setup")
    print("5. List all microphones")
    print("6. Wake word tester (see what works)")
    
    choice = input("Enter 1, 2, 3, 4, 5, or 6: ").strip()
    
    if choice == "2":
        demo_mode()
    elif choice == "3":
        ai_assistent = VoiceHandler()
        ai_assistent.test_microphone()
    elif choice == "4":
        microphone_setup()
    elif choice == "5":
        ai_assistent = VoiceHandler()
        ai_assistent.list_microphones()
    elif choice == "6":
        wake_word_tester()
    else:
        wake_word_demo()
