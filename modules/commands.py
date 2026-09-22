# modules/commands.py - PHASE 4: Command Processing

import re
import os
import webbrowser
import subprocess
from datetime import datetime
import sys
import random
import time
import ctypes  # For Windows system commands
import platform  # To detect OS
import psutil  # For system info
import requests
import wikipedia

# Add parent directory to path so we can import database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_manager import DatabaseManager
from utils.error_handler import get_error_handler, handle_errors, safe_execute
from modules.wishes import WishHandler
from modules.activity_integration import ActivityIntegration
from modules.voice_reports import VoiceReportReader
from modules.thinking_engine import ThinkingEngine
from modules.nlp_engine import NLPEngine
from modules.app_scanner import AppScanner



class CommandProcessor:
    def __init__(self, voice_handler=None):
        """Initialize command processor with database connection and error handling"""
        self.error_handler = get_error_handler()
        self.error_handler.logger.info("Initializing Command Processor...")
        self.db = DatabaseManager()
        
        # Initialize wish handler
        self.wish_handler = WishHandler()
        
        # Initialize activity tracking
        self.activity = ActivityIntegration(self.db)
        self.activity.start_background_tracking()
        
        # Initialize voice report reader
        self.voice = voice_handler
        self.voice_reporter = VoiceReportReader(voice_handler, self.activity)
        
        # Load user preferences
        self.wake_word = self.db.get_preference("wake_word", "ai_assistent")
        self.voice_speed = int(self.db.get_preference("voice_speed", "175"))
        self.default_browser = self.db.get_preference("default_browser", "chrome")
        
        # Initialize Thinking Engine (The "Brain")
        self.brain = ThinkingEngine(self.db)
        
        # Initialize NLP Intent Classifier (The new "Understanding")
        self.error_handler.logger.info("Loading NLP Engine...")
        self.nlp_engine = NLPEngine("data/intents.json", logger=self.error_handler.logger)
        
        # Initialize Deep App Scanner
        self.error_handler.logger.info("Loading App Scanner...")
        self.app_scanner = AppScanner(logger=self.error_handler.logger)
        

        
        # Jokes collection (MOVED BEFORE responses)
        self.jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Why did the scarecrow win an award? Because he was outstanding in his field!",
            "Why don't eggs tell jokes? They'd crack each other up!",
            "What do you call a fake noodle? An impasta!",
            "Why did the math book look sad? Because it had too many problems!",
            "What's the best thing about Switzerland? I don't know, but the flag is a big plus!",
            "Why don't skeletons fight each other? They don't have the guts!"
        ]
        
        # Quotes collection (MOVED BEFORE responses)
        self.quotes = [
            "The only way to do great work is to love what you do. - Steve Jobs",
            "Everything you've ever wanted is on the other side of fear. - George Addair",
            "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
            "Stay hungry, stay foolish. - Steve Jobs",
            "The best time to plant a tree was 20 years ago. The second best time is now. - Chinese Proverb"
        ]
        
        # Response templates (UPDATED WITH BOSS STYLE)
        self.responses = {
            'greeting': [
                "Hello boss! How can I help you?",
                "Hi boss! What can I do for you?",
                "Yes boss! I'm listening.",
                "Ready to help boss!",
                "At your service boss!",
                "I'm here boss! What do you need?",
                "Hey boss! What's up?",
                "Hello boss! Ready when you are."
            ],
            'time': "Boss, the current time is {time}",
            'date': "Boss, today is {date}",
            'weather': "Checking the weather for {location} boss...",
            'open_app': "OK boss! Opening {app}",
            'search': "Sure thing boss! Searching for {query}",
            'file': "Done boss! File operation completed",
            'volume': "Done boss! Volume {action}",
            'system': "Sure thing boss! {action}",
            'remember': "Got it boss! I'll remember that: {info}",
            'recall': "Boss, here's what I know: {info}",
            'stats': "Boss, here are your stats: {stats}",
            'joke': self.get_random_joke(),
            'quote': self.get_random_quote(),
            'preferences': "Done boss! Updated {setting} to {value}",
            'help': self.get_help_text(),
            'exit': "Goodbye boss! See you later!",
            'unknown': "Sorry boss, I'm not sure how to do that. Try saying 'help' to see what I can do."
        }
        
        print(f"✅ Command Processor ready!")
        print(f"   Wake word: '{self.wake_word}'")
        print(f"   Voice speed: {self.voice_speed}")
        print(f"   Default browser: {self.default_browser}")
    
    def parse(self, text):
        """
        Parse command text to determine intent using NLP Engine.
        Falls back to 'unknown' which triggers ThinkingEngine.
        Args: text (str) - What user said
        Returns: dict with intent and parameters
        """
        text = text.lower().strip()
        start_time = time.time()
        
        # 1. Ask NLP Engine
        nlp_result = self.nlp_engine.analyze(text)
        intent = nlp_result["intent"]
        confidence = nlp_result["confidence"]
        entities = nlp_result.get("entities", {})
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # 2. If confidence is too low, send straight to fallback (unknown)
        if confidence < 0.40:
            return {
                'intent': 'unknown',
                'params': None,
                'raw_text': text,
                'confidence': confidence,
                'processing_time_ms': processing_time
            }
            
        # 3. Map new NLP tags to legacy system parameters
        action = None
        legacy_intent = intent
        
        path_replace_map = ["open ", "start ", "launch ", "run "]
        
        if intent in ['volume_up', 'volume_down', 'volume_mute']:
            action = intent.split('_')[1]
            legacy_intent = 'volume'
            
        elif intent in ['brightness_up', 'brightness_down']:
            action = intent.split('_')[1]
            legacy_intent = 'brightness'
            
        elif intent.startswith('system_') and intent != 'system_info':
            action = intent.split('_')[1]
            if action == 'shutdown': action = 'shutdown'
            legacy_intent = 'system'
            
        elif intent == 'open_app':
            action = text
            for x in path_replace_map: action = action.replace(x, '')
            action = action.strip()
            
        elif intent == 'web_search':
            action = text.split('for')[-1].strip() if 'for' in text else text.replace('search','').strip()
            
        elif intent == 'weather':
            action = text.split('in')[-1].strip() if 'in' in text else 'current location'
            if 'GPE' in entities and entities['GPE']:
                 action = entities['GPE'][0] # location
                 
        elif intent == 'knowledge_query':
            action = text.split('about')[-1].strip() if 'about' in text else text.replace('what is','').replace('who is', '').strip()
            
        elif intent == 'preferences':
            if 'wake word' in text: action = ('wake_word', 'ai_assistent')
            elif 'voice speed' in text: action = ('voice_speed', '175')
            elif 'browser' in text: action = ('default_browser', 'chrome')
            
        # Specific fallback extraction for wishes using SpaCy NER
        elif intent.endswith('_wish'):
            name = None
            if 'PERSON' in entities and entities['PERSON']:
                name = entities['PERSON'][0] # Best confident SpaCy Entity extraction
            else:
                 # fallback simple word picking
                 words = text.split()
                 if "to" in words: 
                     idx = words.index("to")
                     if idx + 1 < len(words): name = " ".join(words[idx+1:])
            
            action = [name] if name else None

        return {
            'intent': legacy_intent,
            'params': action,
            'raw_text': text,
            'confidence': confidence,
            'processing_time_ms': processing_time
        }
    
    # Wish handling methods
    def handle_birthday_wish(self, params, raw_text):
        """Handle birthday wish requests"""
        if not params:
            return "Who would you like to wish a happy birthday to?"
        
        name = params[0] if isinstance(params, (list, tuple)) and params else params
        wish_type, detected_name, extra = self.wish_handler.detect_wish_type(raw_text)
        
        # Get the wish - use the name from params (correctly extracted by regex)
        # Only use detected_name if params name is generic
        if name.lower() in ['friend', 'someone', 'person']:
            name_to_use = detected_name
        else:
            name_to_use = name
        
        if wish_type == 'birthday':
            relation = extra.get('relation')
            wish = self.wish_handler.get_birthday_wish(name_to_use, relation=relation)
        else:
            wish = self.wish_handler.get_birthday_wish(name_to_use)
        
        # Log the wish
        self.wish_handler.log_wish('birthday', name_to_use, wish)
        return f"Happy Birthday {name_to_use}! {wish}"
    
    def handle_congrats_wish(self, params, raw_text):
        """Handle congratulations wishes"""
        if not params:
            return "Who would you like to congratulate?"
        
        name = params[0] if isinstance(params, (list, tuple)) and params else params
        wish_type, detected_name, extra = self.wish_handler.detect_wish_type(raw_text)
        
        # Use the name from params (correctly extracted by regex)
        if name.lower() in ['friend', 'someone', 'person']:
            name_to_use = detected_name
        else:
            name_to_use = name
        
        achievement = extra.get('achievement', 'general')
        wish = self.wish_handler.get_congrats_wish(name_to_use, achievement=achievement)
        
        self.wish_handler.log_wish('congrats', name_to_use, wish)
        return f"Congratulations {name_to_use}! {wish}"
    
    def handle_anniversary_wish(self, params, raw_text):
        """Handle anniversary wishes"""
        if not params:
            return "Who would you like to wish a happy anniversary to?"
        
        name = params[0] if isinstance(params, (list, tuple)) and params else params
        wish_type, detected_name, extra = self.wish_handler.detect_wish_type(raw_text)
        
        # Use the name from params (correctly extracted by regex)
        if name.lower() in ['friend', 'someone', 'person']:
            name_to_use = detected_name
        else:
            name_to_use = name
        
        years = extra.get('years')
        wish = self.wish_handler.get_anniversary_wish(name_to_use, years=years)
        
        self.wish_handler.log_wish('anniversary', name_to_use, wish)
        return f"Happy Anniversary {name_to_use}! {wish}"
    
    def handle_surprise_wish(self, params, raw_text):
        """Handle surprise wishes"""
        if not params:
            return "Who would you like to send a surprise wish to?"
        
        name = params[0] if isinstance(params, (list, tuple)) and params else params
        wish_type, detected_name, extra = self.wish_handler.detect_wish_type(raw_text)
        
        # Use the name from params (correctly extracted by regex)
        if name.lower() in ['friend', 'someone', 'person']:
            name_to_use = detected_name
        else:
            name_to_use = name
        
        wish = self.wish_handler.get_surprise_wish(name_to_use)
        
        self.wish_handler.log_wish('surprise', name_to_use, wish)
        return f"Surprise for {name_to_use}! {wish}"
    
    def handle_festival_wish(self, params, raw_text):
        """Handle festival wishes"""
        if not params or len(params) < 2:
            return "Which festival would you like to wish for?"
        
        festival, name = params[0], params[1] if len(params) > 1 else "everyone"
        wish = self.wish_handler.get_festival_wish(name, festival)
        
        self.wish_handler.log_wish('festival', name, wish)
        return wish
    
    def handle_generic_wish(self, params, raw_text):
        """Handle generic wishes"""
        if not params:
            return "Who would you like to send a wish to?"
        
        name = params[0] if isinstance(params, (list, tuple)) and params else params
        wish_type, detected_name, extra = self.wish_handler.detect_wish_type(raw_text)
        
        # Use the name from params (correctly extracted by regex)
        if name.lower() in ['friend', 'someone', 'person']:
            name_to_use = detected_name
        else:
            name_to_use = name
        
        # Get appropriate wish based on detected type
        if wish_type == 'birthday':
            wish = self.wish_handler.get_birthday_wish(name_to_use)
        elif wish_type == 'congrats':
            achievement = extra.get('achievement', 'general')
            wish = self.wish_handler.get_congrats_wish(name_to_use, achievement)
        elif wish_type == 'anniversary':
            wish = self.wish_handler.get_anniversary_wish(name_to_use)
        elif wish_type == 'festival':
            festival = extra.get('festival', 'festival')
            wish = self.wish_handler.get_festival_wish(name_to_use, festival)
        else:
            wish = self.wish_handler.get_surprise_wish(name_to_use)
        
        self.wish_handler.log_wish(wish_type, name_to_use, wish)
        return f"Wish for {name_to_use}: {wish}"
    
    @handle_errors(context="Command execution", user_friendly=True, default_return="Sorry, I encountered an error processing that command.")
    def execute(self, command_data):
        """
        Execute the command based on intent with comprehensive error handling (English exclusively)
        Args: command_data (dict) - Parsed command
        Returns: response text
        """
        try:
            intent = command_data['intent']
            params = command_data['params']
            raw_text = command_data['raw_text']
            confidence = command_data['confidence']
            processing_time = command_data.get('processing_time_ms', None)
            
            self.error_handler.logger.info(f"Executing command: intent={intent}, params={params}")
        except KeyError as e:
            self.error_handler.log_error(e, "Invalid command data", "ERROR")
            return "Invalid command format. Please try again."
        
        response = ""
        
        # Handle English commands
        if intent == 'greeting':
            response = random.choice(self.responses['greeting'])
        
        elif intent == 'time':
            current_time = datetime.now().strftime("%I:%M %p")
            response = self.responses['time'].format(time=current_time)
        
        elif intent == 'date':
            current_date = datetime.now().strftime("%A, %B %d, %Y")
            response = self.responses['date'].format(date=current_date)
        
        elif intent == 'brightness':
            response = self.control_brightness(params)
        
        elif intent == 'screenshot':
            response = self.take_screenshot()
        
        elif intent == 'system_info':
            response = self.get_system_info()
        
        elif intent == 'empty_recycle':
            response = self.empty_recycle_bin()
        
        elif intent == 'weather':
            location = params if params and params.lower() != 'your location' else None
            response = self.get_live_weather(location)

        
        elif intent == 'open_app':
            if params:
                response = self.open_application(params)
            else:
                response = "What app should I open boss?"
        
        elif intent == 'web_search':
            if params:
                response = self.open_web_browser(params)
            else:
                response = "What should I search for boss?"
        
        elif intent == 'knowledge_query':
            if params:
                response = self.get_wikipedia_summary(params)
            else:
                response = "What would you like to know about boss?"

        
        elif intent == 'volume':
            response = self.control_volume(params)
        
        elif intent == 'system':
            response = self.handle_system_command(params)
        
        elif intent == 'remember':
            if params:
                response = self.remember_info(params)
            else:
                # Extract info from raw text
                info = raw_text.replace('remember', '').replace('that', '').strip()
                if info:
                    response = self.remember_info(info)
                else:
                    response = "What should I remember boss?"
        
        elif intent == 'recall':
            if params:
                response = self.recall_info(params)
            else:
                # Extract topic from raw text
                topic = raw_text.replace('what did I tell you about', '').replace('what do you know about', '').replace('tell me about', '').strip()
                if topic:
                    response = self.recall_info(topic)
                else:
                    response = "What do you want me to recall boss?"
        
        elif intent == 'joke':
            response = self.get_random_joke()
        
        elif intent == 'quote':
            response = self.get_random_quote()
        
        elif intent == 'preferences':
            if params:
                response = self.update_preference(params)
            else:
                response = "What preference would you like to change boss?"
        
        elif intent == 'stats':
            response = self.show_stats()
        
        elif intent == 'help':
            response = self.responses['help']
        
        elif intent == 'activity_summary':
            response = self.show_activity_summary()
        
        elif intent == 'weekly_summary':
            response = self.show_weekly_summary()
        
        elif intent == 'productivity_report':
            response = self.show_productivity_report()
        
        elif intent == 'habits':
            response = self.show_habits()
        
        elif intent == 'app_usage':
            response = self.show_app_usage()
        
        elif intent == 'exit':
            response = self.responses['exit']
        
        # Wish handling
        elif intent == 'birthday_wish':
            response = self.handle_birthday_wish(params, raw_text)
        
        elif intent == 'congrats_wish':
            response = self.handle_congrats_wish(params, raw_text)
        
        elif intent == 'anniversary_wish':
            response = self.handle_anniversary_wish(params, raw_text)
        
        elif intent == 'surprise_wish':
            response = self.handle_surprise_wish(params, raw_text)
        
        elif intent == 'festival_wish':
            response = self.handle_festival_wish(params, raw_text)
        
        elif intent == 'wish':
            response = self.handle_generic_wish(params, raw_text)
        
        else:
            # If standard patterns fail, use the Thinking Engine (New logic!)
            thoughts = self.brain.analyze(raw_text)
            
            if thoughts['intent_type'] == 'knowledge_query' or thoughts['intent_type'] == 'conversational':
                response = thoughts['response']
            elif thoughts['intent_type'] == 'system_action':
                response = thoughts['response']
            else:
                response = self.responses['unknown']
        
        # Log interaction to database with processing time
        self.db.log_interaction(
            raw_text, response, intent, confidence, 
            intent != 'unknown', processing_time
        )
        
        # Track activity
        command_data = {
            'intent': intent,
            'confidence': confidence
        }
        self.activity.track_command_execution(command_data, response, processing_time)
        
        # Learn pattern if successful
        if intent != 'unknown':
            self.db.learn_pattern(raw_text, intent)
        
        return response
    
    def open_application(self, app_name):
        """Open an application"""
        app_name = app_name.lower()
        
        # Check database for app
        app = self.db.find_app(app_name)
        
        if app:
            try:
                os.startfile(app[1])
                return f"OK boss! {app[0]} is open!"
            except:
                return f"Sorry boss, couldn't open {app_name}"
        
        # Try platform-specific path finder
        try:
            from utils.platform_paths import PlatformPaths
            
            app_path = PlatformPaths.find_app_path(app_name)
            if app_path:
                try:
                    if platform.system() == 'Windows':
                        os.startfile(app_path)
                    elif platform.system() == 'Darwin':  # macOS
                        subprocess.Popen(['open', '-a', app_path])
                    else:  # Linux
                        subprocess.Popen([app_path])
                    
                    # Save to database for future
                    self.db.add_app_shortcut(app_name, app_path)
                    return f"OK boss! {app_name} is open!"
                except Exception as e:
                    return f"Found {app_name} boss, but couldn't open it: {str(e)}"
        except ImportError:
            pass
        
        # Fallback: try common executable names
        common_executables = {
            'notepad': 'notepad.exe',
            'calculator': 'calc.exe',
            'explorer': 'explorer.exe',
            'word': 'winword.exe',
            'excel': 'excel.exe',
            'powershell': 'powershell.exe',
            'cmd': 'cmd.exe',
            'terminal': 'cmd.exe' if platform.system() == 'Windows' else 'gnome-terminal',
        }
        
        if app_name in common_executables:
            try:
                if platform.system() == 'Windows':
                    os.startfile(common_executables[app_name])
                else:
                    subprocess.Popen([common_executables[app_name]])
                
                self.db.add_app_shortcut(app_name, common_executables[app_name])
                return f"OK boss! {app_name} is open!"
            except:
                pass
                
        # Deep Scanner fallback
        scanned_path = self.app_scanner.find_app(app_name)
        if scanned_path:
            try:
                os.startfile(scanned_path)
                self.db.add_app_shortcut(app_name, scanned_path)
                return f"OK boss! I found {app_name} in OS Registry and opened it!"
            except:
                pass
        
        return f"Sorry boss, couldn't find {app_name}. Try adding it with 'remember app {app_name} path'"

    
    def open_web_browser(self, query):
        """Standard search: Opens browser directly"""
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.google.com/search?q={encoded_query}"
        
        try:
            import webbrowser
            webbrowser.open(url)
            return f"OK boss! Opening Chrome to search for '{query}'."
        except Exception as e:
            return f"Sorry boss, I couldn't open the browser: {str(e)}"

    def get_live_weather(self, location=None):
        """Fetch live weather from the free wttr.in API."""
        loc_str = location if location else ""
        url = f"https://wttr.in/{loc_str}?format=j1"
        try:
            print(f"🌍 Fetching live weather for {loc_str or 'your location'}...")
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                current = data['current_condition'][0]
                temp = current['temp_C']
                desc = current['weatherDesc'][0]['value']
                actual_location = data['nearest_area'][0]['areaName'][0]['value']
                return f"Boss, it is currently {temp} degrees and {desc} in {actual_location}."
            else:
                return f"Sorry boss, I couldn't reach the weather service right now."
        except Exception as e:
            self.error_handler.log_error(e, "Weather API Error")
            return f"Sorry boss, I am having trouble connecting to the weather service."

    def get_wikipedia_summary(self, query):
        """Knowledge query: Summarizes info using Wikipedia API"""
        print(f"📖 AI Assistent is researching '{query}' on Wikipedia...")
        try:
            # fetch exactly 2 sentences
            summary = wikipedia.summary(query, sentences=2, auto_suggest=True)
            return f"Here is what I found boss: {summary}"
        except wikipedia.exceptions.DisambiguationError as e:
            # Multiple matches
            options = e.options[:2]
            return f"Boss, Wikipedia has multiple entries for '{query}'. Did you mean {options[0]} or {options[1]}?"
        except wikipedia.exceptions.PageError:
            return f"Sorry boss, I couldn't find any information on '{query}'."
        except Exception as e:
            self.error_handler.log_error(e, "Wikipedia API Error")
            return f"Sorry boss, I couldn't reach Wikipedia right now."
    
    def control_volume(self, action):
        """Control system volume with cross-platform support"""
        
        # Try pyautogui first (most reliable and simple)
        try:
            import pyautogui
            
            if action == 'up' or action == 'increase':
                pyautogui.press('volumeup', presses=5)
                return "Done boss! Volume up"
            elif action == 'down' or action == 'decrease':
                pyautogui.press('volumedown', presses=5)
                return "Done boss! Volume down"
            elif action == 'mute':
                pyautogui.press('volumemute')
                return "Done boss! Volume muted"
            elif action == 'unmute':
                pyautogui.press('volumemute')  # Toggle mute
                return "Done boss! Volume unmuted"
            elif action == 'max':
                pyautogui.press('volumeup', presses=50)
                return "Done boss! Volume maximum"
            elif action == 'min':
                pyautogui.press('volumedown', presses=50)
                return "Done boss! Volume minimum"
            else:
                return f"Done boss! Volume {action}"
                
        except ImportError:
            # pyautogui not installed, try pycaw
            try:
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                
                if action == 'up' or action == 'increase':
                    current = volume.GetMasterVolumeLevelScalar()
                    volume.SetMasterVolumeLevelScalar(min(current + 0.1, 1.0), None)
                elif action == 'down' or action == 'decrease':
                    current = volume.GetMasterVolumeLevelScalar()
                    volume.SetMasterVolumeLevelScalar(max(current - 0.1, 0.0), None)
                elif action == 'max':
                    volume.SetMasterVolumeLevelScalar(1.0, None)
                elif action == 'min':
                    volume.SetMasterVolumeLevelScalar(0.0, None)
                elif action == 'mute':
                    volume.SetMute(1, None)
                elif action == 'unmute':
                    volume.SetMute(0, None)
                
                return f"Done boss! Volume {action}"
                
            except Exception as e:
                # All methods failed
                return f"Sorry boss, volume control not available. Error: {str(e)}"
        
        except Exception as e:
            return f"Error controlling volume: {str(e)}"
    
    def handle_system_command(self, action):
        """Handle system commands like shutdown, restart, sleep, lock"""
        
        # Check if running on Windows
        is_windows = platform.system() == 'Windows'
        
        if not is_windows:
            return "System commands are currently only supported on Windows."
        
        try:
            if action == 'shutdown':
                response = "Sure thing boss! Shutting down in 30 seconds. Say 'cancel shutdown' to abort."
                # Windows shutdown command with 30 second delay
                subprocess.Popen(['shutdown', '/s', '/t', '30', '/c', 'AI Assistent: Shutting down as requested'])
                
            elif action == 'restart':
                response = "You got it boss! Restarting in 30 seconds. Say 'cancel restart' to abort."
                # Windows restart command with 30 second delay
                subprocess.Popen(['shutdown', '/r', '/t', '30', '/c', 'AI Assistent: Restarting as requested'])
                
            elif action == 'sleep':
                response = "OK boss! Putting computer to sleep in 5 seconds..."
                # Sleep after 5 seconds to allow response to be spoken
                time.sleep(5)
                # Windows sleep command (suspend)
                subprocess.Popen(['rundll32.exe', 'powrprof.dll,SetSuspendState', '0', '1', '0'])
                
            elif action == 'lock':
                response = "Locking now boss!"
                # Lock workstation immediately
                ctypes.windll.user32.LockWorkStation()
                
            elif action == 'cancel':
                response = "Done boss! Cancelled shutdown/restart."
                # Cancel any pending shutdown or restart
                subprocess.Popen(['shutdown', '/a'])
                
            else:
                response = f"Sorry boss, unknown system action: {action}"
            
            return response
            
        except Exception as e:
            return f"Error executing system command: {str(e)}. Make sure you have administrator privileges."
    
    def control_brightness(self, action):
        """Control screen brightness"""
        try:
            # Try screen-brightness-control (most reliable)
            try:
                import screen_brightness_control as sbc
                
                current = sbc.get_brightness()[0]
                
                if action == 'up':
                    new_brightness = min(current + 10, 100)
                    sbc.set_brightness(new_brightness)
                    return f"Done boss! Brightness increased to {new_brightness}%"
                elif action == 'down':
                    new_brightness = max(current - 10, 0)
                    sbc.set_brightness(new_brightness)
                    return f"Done boss! Brightness decreased to {new_brightness}%"
                else:
                    return f"Done boss! Brightness {action}"
                    
            except ImportError:
                # Fallback to WMI (Windows only)
                if platform.system() == 'Windows':
                    import wmi
                    c = wmi.WMI(namespace='wmi')
                    methods = c.WmiMonitorBrightnessMethods()[0]
                    
                    # Get current brightness
                    current = c.WmiMonitorBrightness()[0].CurrentBrightness
                    
                    if action == 'up':
                        new_brightness = min(current + 10, 100)
                        methods.WmiSetBrightness(new_brightness, 0)
                        return f"Done boss! Brightness increased to {new_brightness}%"
                    elif action == 'down':
                        new_brightness = max(current - 10, 0)
                        methods.WmiSetBrightness(new_brightness, 0)
                        return f"Done boss! Brightness decreased to {new_brightness}%"
                else:
                    return "Brightness control is currently only supported on Windows."
                    
        except ImportError:
            return "Sorry boss, brightness control requires screen-brightness-control. Install with: pip install screen-brightness-control"
        except Exception as e:
            return f"Sorry boss, error controlling brightness: {str(e)}"
    
    def take_screenshot(self):
        """Take a screenshot and save to Desktop/AI Assistent/Screenshots folder with database logging"""
        try:
            import pyautogui
            from datetime import datetime
            
            # Get Desktop path (works on any PC)
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            
            # Create AI Assistent/Screenshots folder structure on Desktop
            ai_assistent_folder = os.path.join(desktop_path, "AI Assistent")
            screenshots_dir = os.path.join(ai_assistent_folder, "Screenshots")
            
            # Create folders if they don't exist
            if not os.path.exists(ai_assistent_folder):
                os.makedirs(ai_assistent_folder)
            if not os.path.exists(screenshots_dir):
                os.makedirs(screenshots_dir)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(screenshots_dir, filename)
            
            # Take screenshot
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            
            # Get file size in KB
            file_size_kb = os.path.getsize(filepath) // 1024
            
            # Log to database
            screenshot_id = self.db.log_screenshot(
                filename=filename,
                filepath=filepath,
                command_text="take screenshot",
                file_size_kb=file_size_kb,
                success=True
            )
            
            return f"Done boss! Screenshot saved to Desktop/AI Assistent/Screenshots ({file_size_kb}KB)"
        except ImportError:
            return "Screenshot requires pyautogui. Install with: pip install pyautogui"
        except Exception as e:
            # Log failed screenshot attempt
            try:
                self.db.log_screenshot(
                    filename="failed",
                    filepath="",
                    command_text="take screenshot",
                    success=False
                )
            except:
                pass
            return f"Error taking screenshot: {str(e)}"
    
    def get_system_info(self):
        """Get system information"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # RAM usage
            ram = psutil.virtual_memory()
            ram_percent = ram.percent
            ram_used_gb = ram.used / (1024**3)
            ram_total_gb = ram.total / (1024**3)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            info = f"CPU: {cpu_percent}%, RAM: {ram_percent}% ({ram_used_gb:.1f}GB / {ram_total_gb:.1f}GB), Disk: {disk_percent}%"
            
            return f"Boss, system info: {info}"
        except Exception as e:
            return f"Error getting system info: {str(e)}"
    
    def empty_recycle_bin(self):
        """Empty recycle bin"""
        try:
            if platform.system() == 'Windows':
                import winshell
                winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
                return "Done boss! Recycle bin emptied."
            else:
                return "Recycle bin emptying is currently only supported on Windows."
        except ImportError:
            return "Recycle bin requires winshell. Install with: pip install winshell"
        except Exception as e:
            return f"Error emptying recycle bin: {str(e)}"
    
    def remember_info(self, info):
        """Store information in knowledge base"""
        # Extract a question-answer pair
        if ' is ' in info:
            parts = info.split(' is ', 1)
            question = f"what is {parts[0]}"
            answer = parts[1]
            self.db.add_knowledge(question, answer, parts[0])
        else:
            # Store as general fact
            self.db.add_knowledge("general", info, info[:20])
        
        return f"Got it boss! I'll remember: {info[:50]}"
    
    def recall_info(self, topic):
        """Recall stored information"""
        answer = self.db.get_knowledge(topic)
        if answer:
            return f"Boss, here's what I know: {answer}"
        return f"Sorry boss, I don't know anything about {topic} yet."
    
    def get_random_joke(self):
        """Get a random joke"""
        return random.choice(self.jokes)
    
    def get_random_quote(self):
        """Get a random inspirational quote"""
        return random.choice(self.quotes)
    
    def update_preference(self, pref_data):
        """Update user preferences"""
        if isinstance(pref_data, tuple) and len(pref_data) == 2:
            pref_type, value = pref_data
            
            if pref_type == 'wake_word':
                self.wake_word = value
                self.db.set_preference('wake_word', value)
                return f"Done boss! Wake word changed to '{value}'"
            
            elif pref_type == 'voice_speed':
                try:
                    speed = int(value)
                    self.voice_speed = speed
                    self.db.set_preference('voice_speed', str(speed))
                    return f"Done boss! Voice speed set to {speed}"
                except:
                    return "Boss, please provide a valid number for voice speed"
            
            elif pref_type == 'default_browser':
                self.default_browser = value
                self.db.set_preference('default_browser', value)
                return f"Done boss! Default browser changed to {value}"
        
        return "Preference updated boss!"
    
    def show_stats(self):
        """Show interaction statistics"""
        stats = self.db.get_statistics()
        today = self.db.get_today_stats()
        
        stats_text = ""
        
        if today:
            stats_text += f"Today you gave me {today['total_commands']} commands, {today['successful_commands']} successful ({today['success_rate']}%). "
        
        stats_text += f"Total: {stats['total_interactions']} commands. "
        stats_text += f"Success rate: {stats['success_rate']}%. "
        stats_text += f"I've learned {stats['learned_patterns']} patterns. "
        
        if 'wake_word_detections' in stats:
            stats_text += f"You called me {stats['wake_word_detections']} times. "
        
        if 'avg_response_time_ms' in stats and stats['avg_response_time_ms']:
            stats_text += f"Average response: {stats['avg_response_time_ms']}ms. "
        
        return f"Boss, here are your stats: {stats_text}"
    
    def show_activity_summary(self):
        """Show today's activity summary"""
        if self.voice_reporter:
            self.voice_reporter.read_daily_summary()
        else:
            from modules.activity_integration import ActivityReporter
            reporter = ActivityReporter(self.activity)
            summary = reporter.format_daily_summary()
            return summary
        return "Daily summary read aloud"
    
    def show_weekly_summary(self):
        """Show weekly activity summary"""
        if self.voice_reporter:
            self.voice_reporter.read_weekly_summary()
        else:
            from modules.activity_integration import ActivityReporter
            reporter = ActivityReporter(self.activity)
            summary = reporter.format_weekly_summary()
            return summary
        return "Weekly summary read aloud"
    
    def show_productivity_report(self):
        """Show productivity report"""
        if self.voice_reporter:
            self.voice_reporter.read_productivity_report("daily")
        else:
            from modules.activity_integration import ActivityReporter
            reporter = ActivityReporter(self.activity)
            report = reporter.format_productivity_report("daily")
            return report
        return "Productivity report read aloud"
    
    def show_habits(self):
        """Show learned habits"""
        if self.voice_reporter:
            self.voice_reporter.read_habits()
        else:
            from modules.activity_integration import ActivityReporter
            reporter = ActivityReporter(self.activity)
            habits = reporter.format_habits()
            return habits
        return "Habits read aloud"
    
    def show_app_usage(self):
        """Show app usage statistics"""
        if self.voice_reporter:
            self.voice_reporter.read_app_usage(7)
        else:
            from modules.activity_integration import ActivityReporter
            reporter = ActivityReporter(self.activity)
            usage = reporter.format_app_usage(7)
            return usage
        return "App usage read aloud"
    
    def get_help_text(self):
        """Get help text"""
        return """Boss, I can help you with:

WAKE WORD: Just say 'hello', 'hey', 'hi', or 'ai_assistent' to activate me!

BASIC COMMANDS:
• Greetings: hello, hi, good morning, how are you
• Time & Date: what time, what date, what day
• Weather: weather in [city], temperature (coming soon)

APPLICATIONS:
• Open apps: open chrome, open notepad, open calculator
• Web search: search for [query], what is [topic], google [query]

SYSTEM CONTROL:
• Volume: volume up/down, mute, max volume, min volume
• System: shutdown, restart, sleep, lock computer

MEMORY & LEARNING:
• Remember: remember that [info], note that [info]
• Recall: what did I tell you about [topic], tell me about [topic]

FUN:
• Jokes: tell me a joke, make me laugh
• Quotes: inspire me, give me a quote

PREFERENCES:
• Change wake word: change wake word to [word]
• Change voice speed: change voice speed to [number]
• Change browser: change browser to [name]

STATISTICS:
• Stats: show stats, how many commands, today's stats

EXIT:
• Goodbye: exit, quit, goodbye, bye

Try saying something boss!"""
    
    def get_wake_word(self):
        """Get current wake word"""
        return self.wake_word


# =====================================================
# TEST UPDATED COMMAND PROCESSOR
# =====================================================

if __name__ == "__main__":
    print("=" * 50)
    print("🎯 TESTING AI ASSISTENT COMMAND PROCESSOR (UPDATED)")
    print("=" * 50)
    
    # Create processor
    processor = CommandProcessor()
    
    # Test new commands
    test_commands = [
        "hello",
        "hello ai_assistent",
        "how are you",
        "what time",
        "today's date",
        "weather in London",
        "open chrome",
        "search for Python tutorials",
        "what is artificial intelligence",
        "volume up",
        "max volume",
        "lock computer",
        "tell me a joke",
        "inspire me",
        "remember that my favorite color is blue",
        "what did I tell you about favorite",
        "change wake word to jarvis",
        "show stats",
        "help",
        "goodbye"
    ]
    
    print("\n📝 Testing commands:\n")
    
    for cmd in test_commands:
        print(f"User: {cmd}")
        
        # Parse command
        parsed = processor.parse(cmd)
        print(f"  Intent: {parsed['intent']}")
        print(f"  Params: {parsed['params']}")
        print(f"  Processing: {parsed['processing_time_ms']}ms")
        
        # Execute command
        response = processor.execute(parsed)
        print(f"  AI Assistent: {response}\n")
    
    # Show final stats
    print("\n📊 Final Statistics:")
    stats = processor.db.get_statistics()
    for key, value in stats.items():
        if key != 'top_commands':
            print(f"  • {key}: {value}")
    
    print("\n✅ Command processor test complete!")