# modules/wishes.py - Complete Wishes Handler for AI Assistent Voice Assistant

import random
import json
import os
from datetime import datetime

class WishHandler:
    def __init__(self):
        """Initialize wish handler with multilingual wishes"""
        self.wish_history_file = "data/wish_history.json"
        
        # Birthday wishes in multiple languages
        self.birthday_wishes = {
            'english': [
                "Happy Birthday {name}! May all your dreams come true!",
                "Wishing you a fantastic birthday {name}! Have a wonderful day!",
                "Happy Birthday {name}! May this year bring you joy and success!",
                "Many happy returns of the day {name}! Enjoy your special day!",
                "Happy Birthday {name}! Wishing you health, happiness, and prosperity!",
                "Cheers to you on your birthday {name}! Make it memorable!",
                "Happy Birthday {name}! May you be blessed with everything you wish for!",
                "Warmest birthday wishes to you {name}! Have an amazing year ahead!",
                "Happy Birthday {name}! Celebrate big and enjoy every moment!",
                "Wishing you the happiest of birthdays {name}! You deserve the best!",
                "Happy Birthday {name}! May your day be filled with love and laughter!",
                "Another year older, another year wiser! Happy Birthday {name}!",
                "Happy Birthday {name}! Here's to another year of wonderful memories!",
                "Sending you lots of love on your birthday {name}! Have a blast!",
                "Happy Birthday {name}! May this year be your best one yet!"
            ]
        }
        
        # Congratulations wishes
        self.congrats_wishes = {
            'general': [
                "Congratulations {name}! Well done!",
                "Congrats {name}! You deserve this success!",
                "Congratulations {name}! So proud of you!",
                "Well done {name}! Keep up the great work!",
                "Congratulations {name}! This is just the beginning!"
            ],
            'job': [
                "Congratulations on your new job {name}! Best wishes!",
                "Congrats on the new job {name}! You'll do great!",
                "Congratulations {name}! Wishing you success in your new role!"
            ],
            'promotion': [
                "Congratulations on your promotion {name}! Well deserved!",
                "Congrats on the promotion {name}! Keep climbing!"
            ],
            'graduation': [
                "Congratulations on your graduation {name}! Proud of you!",
                "Congrats graduate {name}! The world is yours!"
            ]
        }
        
        # Anniversary wishes
        self.anniversary_wishes = {
            'english': [
                "Happy Anniversary {name}! Wishing you many more years of love!",
                "Congratulations on your anniversary {name}! Stay blessed!",
                "Happy Anniversary {name}! May your love grow stronger!",
                "Wishing you a wonderful anniversary {name}!",
                "Happy Anniversary {name}! Here's to many more years together!"
            ]
        }
        
        # Festival wishes
        self.festival_wishes = {
            'diwali': [
                "Happy Diwali {name}! May the festival of lights bring joy to your life!",
                "Wishing you a bright and prosperous Diwali {name}!",
                "Happy Diwali {name}! May Goddess Lakshmi bless you!"
            ],
            'holi': [
                "Happy Holi {name}! Enjoy the festival of colors!",
                "Wishing you a colorful Holi {name}!"
            ],
            'navratri': [
                "Happy Navratri {name}! Jai Mata Di!",
                "Wishing you a blessed Navratri {name}!"
            ],
            'christmas': [
                "Merry Christmas {name}! May Santa bring you joy!",
                "Wishing you a wonderful Christmas {name}!"
            ],
            'eid': [
                "Eid Mubarak {name}! May Allah bless you!",
                "Wishing you a joyous Eid {name}!"
            ],
            'newyear': [
                "Happy New Year {name}! Wishing you success in the coming year!",
                "New Year wishes {name}! May this year be amazing!"
            ]
        }
        
        # Surprise/Funny wishes
        self.surprise_wishes = [
            "Hey {name}! Someone special asked me to send you lots of love!",
            "{name}, you're awesome! Keep being amazing!",
            "Surprise {name}! You're the best!",
            "{name}, you rock! Never forget that!",
            "Special message for {name}: You're incredible!",
            "{name}, sending you positive vibes and good wishes!",
            "Hey {name}! Just wanted to say you're doing great!",
            "{name}, you're a star! Shine bright!"
        ]
        
        # Relation-based wishes
        self.relation_wishes = {
            'mother': [
                "Happy Birthday Mom! You're the best mother in the world!",
                "Wishing you a wonderful birthday Mom! Love you!"
            ],
            'father': [
                "Happy Birthday Dad! You're my hero!",
                "Wishing you a great birthday Dad! Love you!"
            ],
            'brother': [
                "Happy Birthday Bro! Have an awesome day!",
                "Wishing you the best birthday brother!"
            ],
            'sister': [
                "Happy Birthday Sis! You're the best!",
                "Wishing you a wonderful birthday sister!"
            ],
            'friend': [
                "Happy Birthday my friend! Let's celebrate!",
                "Wishing you an amazing birthday buddy!"
            ],
            'wife': [
                "Happy Birthday my love! You mean the world to me!",
                "Wishing you the happiest birthday darling!"
            ],
            'husband': [
                "Happy Birthday my dear husband! Love you always!",
                "Wishing you a fantastic birthday sweetheart!"
            ]
        }
    
    def get_birthday_wish(self, name, language='english', relation=None):
        """Get a birthday wish for someone"""
        # Check if relation-specific wish is requested
        if relation and relation.lower() in self.relation_wishes:
            wish = random.choice(self.relation_wishes[relation.lower()])
        else:
            # Get language-specific wish
            if language.lower() in self.birthday_wishes:
                wish = random.choice(self.birthday_wishes[language.lower()])
            else:
                wish = random.choice(self.birthday_wishes['english'])
        
        return wish.format(name=name)
    
    def get_congrats_wish(self, name, achievement='general'):
        """Get a congratulations wish"""
        if achievement.lower() in self.congrats_wishes:
            wish = random.choice(self.congrats_wishes[achievement.lower()])
        else:
            wish = random.choice(self.congrats_wishes['general'])
        
        return wish.format(name=name)
    
    def get_anniversary_wish(self, name, language='english', years=None):
        """Get an anniversary wish"""
        if language.lower() in self.anniversary_wishes:
            wish = random.choice(self.anniversary_wishes[language.lower()])
        else:
            wish = random.choice(self.anniversary_wishes['english'])
        
        wish = wish.format(name=name)
        
        if years:
            wish += f" {years} years of togetherness!"
        
        return wish
    
    def get_festival_wish(self, name, festival):
        """Get a festival wish"""
        festival = festival.lower()
        
        # Handle variations
        if 'new year' in festival or 'newyear' in festival:
            festival = 'newyear'
        
        if festival in self.festival_wishes:
            wish = random.choice(self.festival_wishes[festival])
        else:
            wish = f"Happy {festival.title()} {name}! Wishing you joy and happiness!"
        
        return wish.format(name=name)
    
    def get_surprise_wish(self, name):
        """Get a surprise wish"""
        wish = random.choice(self.surprise_wishes)
        return wish.format(name=name)
    
    def detect_wish_type(self, text):
        """
        Smart detection of wish type from voice command
        Returns: (wish_type, name, extra_info)
        """
        text = text.lower().strip()
        
        # Birthday detection (English)
        if 'birthday' in text:
            name = self._extract_name(text, ['birthday', 'to'])
            relation = self._detect_relation(text)
            return ('birthday', name, {'relation': relation})
        
        # Congratulations detection (English)
        if 'congratulat' in text or 'congrats' in text:
            name = self._extract_name(text, ['congratulations', 'congrats', 'to'])
            achievement = self._detect_achievement(text)
            return ('congrats', name, {'achievement': achievement})
        
        # Anniversary detection (English)
        if 'anniversary' in text:
            name = self._extract_name(text, ['anniversary', 'to'])
            years = self._extract_years(text)
            return ('anniversary', name, {'years': years})
        
        # Festival detection
        festivals = ['diwali', 'holi', 'navratri', 'christmas', 'eid', 'new year']
        for festival in festivals:
            if festival in text or festival.replace(' ', '') in text:
                name = self._extract_name(text, [festival, 'to', 'happy'])
                return ('festival', name, {'festival': festival})
        
        # Surprise wish detection
        if 'surprise' in text or 'special message' in text:
            name = self._extract_name(text, ['surprise', 'wish', 'for', 'to', 'special', 'message'])
            return ('surprise', name, {})
        
        # Generic wish
        name = self._extract_name(text, ['wish', 'to', 'send'])
        return ('generic', name, {})
    
    def _extract_name(self, text, skip_words):
        """Extract name from text by removing skip words"""
        words = text.split()
        name_words = []
        
        skip = False
        for word in words:
            word_clean = word.strip('.,!?')
            if word_clean.lower() in skip_words:
                skip = True
                continue
            if skip:
                name_words.append(word_clean)
        
        if name_words:
            return ' '.join(name_words).title()
        return "Friend"
    
    def _detect_relation(self, text):
        """Detect relation from text"""
        relations = {
            'mother': ['mom', 'mother'],
            'father': ['dad', 'father', 'papa', 'daddy'],
            'brother': ['brother', 'bro'],
            'sister': ['sister', 'sis'],
            'friend': ['friend', 'buddy'],
            'wife': ['wife'],
            'husband': ['husband']
        }
        
        text_lower = text.lower()
        for relation, keywords in relations.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return relation
        return None
    
    def _detect_achievement(self, text):
        """Detect achievement type from text"""
        text_lower = text.lower()
        if 'job' in text_lower:
            return 'job'
        if 'promotion' in text_lower:
            return 'promotion'
        if 'graduation' in text_lower:
            return 'graduation'
        return 'general'
    
    def _extract_years(self, text):
        """Extract year number from text"""
        import re
        # Look for patterns like "5th", "10 years", etc.
        match = re.search(r'(\d+)(?:th|st|nd|rd)?\s*(?:year)?', text)
        if match:
            return match.group(1)
        return None
    
    def log_wish(self, wish_type, name, wish_text):
        """Log wish to history file"""
        try:
            # Create data directory if not exists
            os.makedirs('data', exist_ok=True)
            
            # Load existing history
            if os.path.exists(self.wish_history_file):
                with open(self.wish_history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            else:
                history = []
            
            # Add new wish
            wish_entry = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'type': wish_type,
                'name': name,
                'wish': wish_text
            }
            history.append(wish_entry)
            
            # Save history
            with open(self.wish_history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error logging wish: {e}")
            return False
    
    def get_wish_history(self, limit=10):
        """Get recent wish history"""
        try:
            if os.path.exists(self.wish_history_file):
                with open(self.wish_history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                return history[-limit:]
            return []
        except Exception as e:
            print(f"Error reading wish history: {e}")
            return []


# =====================================================
# TEST FUNCTION
# =====================================================

if __name__ == "__main__":
    print("=" * 70)
    print("🎉 TESTING WISH HANDLER")
    print("=" * 70)
    
    wish_handler = WishHandler()
    
    # Test 1: Birthday wishes
    print("\n📝 Test 1: Birthday Wishes")
    print("-" * 70)
    print("English:", wish_handler.get_birthday_wish("Raj", "english"))
    print("Mother:", wish_handler.get_birthday_wish("Mom", relation="mother"))
    
    # Test 2: Congratulations
    print("\n📝 Test 2: Congratulations")
    print("-" * 70)
    print("General:", wish_handler.get_congrats_wish("Amit"))
    print("New Job:", wish_handler.get_congrats_wish("Priya", "job"))
    print("Promotion:", wish_handler.get_congrats_wish("Rahul", "promotion"))
    
    # Test 3: Anniversary
    print("\n📝 Test 3: Anniversary Wishes")
    print("-" * 70)
    print("English:", wish_handler.get_anniversary_wish("Mom and Dad", "english", "25"))
    
    # Test 4: Festival wishes
    print("\n📝 Test 4: Festival Wishes")
    print("-" * 70)
    print("Diwali:", wish_handler.get_festival_wish("Family", "diwali"))
    print("Holi:", wish_handler.get_festival_wish("Friends", "holi"))
    print("Christmas:", wish_handler.get_festival_wish("Everyone", "christmas"))
    
    # Test 5: Surprise wishes
    print("\n📝 Test 5: Surprise Wishes")
    print("-" * 70)
    print(wish_handler.get_surprise_wish("Neha"))
    print(wish_handler.get_surprise_wish("Raj"))
    
    # Test 6: Smart detection
    print("\n📝 Test 6: Smart Wish Detection")
    print("-" * 70)
    test_commands = [
        "wish happy birthday to Raj",
        "congratulate Priya on her new job",
        "happy anniversary to mom and dad",
        "surprise wish for Neha",
        "happy diwali to family"
    ]
    
    for cmd in test_commands:
        wish_type, name, extra = wish_handler.detect_wish_type(cmd)
        print(f"'{cmd}' -> Type: {wish_type}, Name: {name}, Extra: {extra}")
    
    # Test 7: Wish logging
    print("\n📝 Test 7: Wish Logging")
    print("-" * 70)
    wish_handler.log_wish("birthday", "Test User", "Happy Birthday!")
    print("✅ Wish logged successfully")
    
    history = wish_handler.get_wish_history(5)
    print(f"✅ Retrieved {len(history)} wishes from history")
    
    print("\n" + "=" * 70)
    print("✅ All tests completed!")
    print("=" * 70)
