# database/db_manager.py - PHASE 2: SQLite Database (UPDATED)

import sqlite3
import json
import os
from datetime import datetime, timedelta
import shutil

class DatabaseManager:
    def __init__(self, db_path="data/ai_assistent.db"):
        """Initialize database connection"""
        self.db_path = db_path
        
        # Create data directory if not exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self.init_database()
        print(f"OK: Database initialized at {db_path}")
    
    def init_database(self):
        """Create all tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # USERS TABLE
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP,
                    preferences TEXT
                )
            ''')
            
            # WAKE WORD TABLE (NEW)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS wake_word_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    detected_text TEXT,
                    success BOOLEAN DEFAULT 1,
                    response_time_ms INTEGER
                )
            ''')
            
            # INTERACTIONS TABLE (all voice commands)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER DEFAULT 1,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    command_text TEXT NOT NULL,
                    command_type TEXT,
                    confidence REAL,
                    response_text TEXT,
                    success BOOLEAN DEFAULT 1,
                    processing_time_ms INTEGER,  -- NEW: Track performance
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # PATTERNS TABLE (learned commands)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_text TEXT UNIQUE NOT NULL,
                    command_type TEXT,
                    frequency INTEGER DEFAULT 1,
                    last_used TIMESTAMP,
                    confidence REAL DEFAULT 0.5
                )
            ''')
            
            # FEEDBACK TABLE (user ratings)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    interaction_id INTEGER UNIQUE,
                    rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                    correct_action BOOLEAN,
                    comment TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (interaction_id) REFERENCES interactions(id)
                )
            ''')
            
            # APP SHORTCUTS (UPDATED with more fields)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_shortcuts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_name TEXT UNIQUE NOT NULL,
                    app_path TEXT NOT NULL,
                    aliases TEXT,
                    category TEXT DEFAULT 'general',  -- NEW: App category
                    launch_count INTEGER DEFAULT 0,
                    last_launched TIMESTAMP,
                    is_default BOOLEAN DEFAULT 0
                )
            ''')
            
            # KNOWLEDGE BASE
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT,
                    question TEXT,
                    answer TEXT NOT NULL,
                    times_accessed INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP  -- NEW: Track last access
                )
            ''')
            
            # DAILY STATS (UPDATED with more fields)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE UNIQUE,
                    total_commands INTEGER DEFAULT 0,
                    successful_commands INTEGER DEFAULT 0,
                    wake_word_detections INTEGER DEFAULT 0,  -- NEW
                    unique_patterns INTEGER DEFAULT 0,
                    avg_confidence REAL DEFAULT 0,
                    avg_response_time_ms INTEGER DEFAULT 0  -- NEW
                )
            ''')
            
            # USER PREFERENCES (NEW)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id INTEGER DEFAULT 1,
                    preference_key TEXT,
                    preference_value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, preference_key),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # SCREENSHOTS TABLE (NEW)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS screenshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    filepath TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_size_kb INTEGER,
                    command_text TEXT,
                    success BOOLEAN DEFAULT 1
                )
            ''')
            
            # Insert default user if not exists
            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, username, created_at)
                VALUES (1, 'default_user', CURRENT_TIMESTAMP)
            ''')
            
            # Insert common app shortcuts with cross-platform support
            try:
                # Try to import platform paths utility
                import sys
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from utils.platform_paths import PlatformPaths
                
                default_apps = PlatformPaths.get_default_apps()
                
                for app_name, app_path, aliases, category, is_default in default_apps:
                    cursor.execute('''
                        INSERT OR IGNORE INTO app_shortcuts (app_name, app_path, aliases, category, is_default)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (app_name, app_path, aliases, category, is_default))
                
            except Exception as e:
                # Fallback to basic apps if platform_paths fails
                print(f"⚠️  Using fallback app list: {e}")
                basic_apps = [
                    ('notepad', 'notepad.exe', '["editor", "text"]', 'utilities', 1),
                    ('calculator', 'calc.exe', '["calc"]', 'utilities', 1),
                ]
                
                for app_name, app_path, aliases, category, is_default in basic_apps:
                    cursor.execute('''
                        INSERT OR IGNORE INTO app_shortcuts (app_name, app_path, aliases, category, is_default)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (app_name, app_path, aliases, category, is_default))
            
            conn.commit()
    
    # NEW: Log wake word detection
    def log_wake_word(self, detected_text, success=True, response_time_ms=None):
        """Log wake word detection events"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO wake_word_events (detected_text, success, response_time_ms)
                VALUES (?, ?, ?)
            ''', (detected_text, success, response_time_ms))
            
            # Update daily stats
            today = datetime.now().date()
            cursor.execute('''
                INSERT INTO daily_stats (date, wake_word_detections)
                VALUES (?, 1)
                ON CONFLICT(date) DO UPDATE SET
                    wake_word_detections = wake_word_detections + 1
            ''', (today,))
            
            conn.commit()
            return cursor.lastrowid
    
    # UPDATED: log_interaction with processing time
    def log_interaction(self, command, response, command_type="unknown", confidence=1.0, success=True, processing_time_ms=None):
        """Store a voice interaction"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO interactions 
                (user_id, command_text, command_type, confidence, response_text, success, processing_time_ms)
                VALUES (1, ?, ?, ?, ?, ?, ?)
            ''', (command, command_type, confidence, response, success, processing_time_ms))
            
            interaction_id = cursor.lastrowid
            
            # Update daily stats
            today = datetime.now().date()
            
            # Get current avg confidence
            cursor.execute('''
                SELECT AVG(confidence) FROM interactions 
                WHERE date(timestamp) = ?
            ''', (today,))
            avg_conf = cursor.fetchone()[0] or confidence
            
            # Get avg response time
            cursor.execute('''
                SELECT AVG(processing_time_ms) FROM interactions 
                WHERE date(timestamp) = ? AND processing_time_ms IS NOT NULL
            ''', (today,))
            avg_time = cursor.fetchone()[0] or processing_time_ms
            
            cursor.execute('''
                INSERT INTO daily_stats (
                    date, total_commands, successful_commands, 
                    avg_confidence, avg_response_time_ms
                )
                VALUES (?, 1, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    total_commands = total_commands + 1,
                    successful_commands = successful_commands + ?,
                    avg_confidence = ?,
                    avg_response_time_ms = ?
            ''', (today, 1 if success else 0, avg_conf, avg_time, 
                  1 if success else 0, avg_conf, avg_time))
            
            conn.commit()
            return interaction_id
    
    # NEW: Set user preference
    def set_preference(self, key, value, user_id=1):
        """Set a user preference"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_preferences (user_id, preference_key, preference_value, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, key, value))
            conn.commit()
            return True
    
    # NEW: Get user preference
    def get_preference(self, key, default=None, user_id=1):
        """Get a user preference"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT preference_value FROM user_preferences 
                WHERE user_id = ? AND preference_key = ?
            ''', (user_id, key))
            result = cursor.fetchone()
            return result[0] if result else default
    
    # NEW: Find app by name or alias
    def find_app(self, app_name):
        """
        Find an application by name or alias
        Args: app_name (str) - Name or alias of the app
        Returns: tuple (app_name, app_path) or None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # First try exact match
            cursor.execute('''
                SELECT app_name, app_path FROM app_shortcuts
                WHERE LOWER(app_name) = LOWER(?)
            ''', (app_name,))
            result = cursor.fetchone()
            
            if result:
                # Update launch count
                cursor.execute('''
                    UPDATE app_shortcuts 
                    SET launch_count = launch_count + 1,
                        last_launched = CURRENT_TIMESTAMP
                    WHERE LOWER(app_name) = LOWER(?)
                ''', (app_name,))
                conn.commit()
                return result
            
            # Try alias match
            cursor.execute('SELECT app_name, app_path, aliases FROM app_shortcuts')
            for row in cursor.fetchall():
                name, path, aliases_json = row
                if aliases_json:
                    try:
                        aliases = json.loads(aliases_json)
                        if any(app_name.lower() in alias.lower() for alias in aliases):
                            # Update launch count
                            cursor.execute('''
                                UPDATE app_shortcuts 
                                SET launch_count = launch_count + 1,
                                    last_launched = CURRENT_TIMESTAMP
                                WHERE app_name = ?
                            ''', (name,))
                            conn.commit()
                            return (name, path)
                    except:
                        pass
            
            return None
    
    # NEW: Add new app shortcut
    def add_app_shortcut(self, app_name, app_path, aliases=None, category='general'):
        """
        Add a new application shortcut
        Args:
            app_name (str) - Name of the app
            app_path (str) - Full path to executable
            aliases (list) - List of alternative names
            category (str) - App category
        Returns: bool - Success status
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            aliases_json = json.dumps(aliases) if aliases else None
            
            try:
                cursor.execute('''
                    INSERT INTO app_shortcuts (app_name, app_path, aliases, category)
                    VALUES (?, ?, ?, ?)
                ''', (app_name, app_path, aliases_json, category))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                # App already exists, update it
                cursor.execute('''
                    UPDATE app_shortcuts 
                    SET app_path = ?, aliases = ?, category = ?
                    WHERE app_name = ?
                ''', (app_path, aliases_json, category, app_name))
                conn.commit()
                return True
            except Exception as e:
                print(f"Error adding app shortcut: {e}")
                return False
    
    # NEW: Learn command pattern
    def learn_pattern(self, pattern_text, command_type):
        """
        Learn a new command pattern or update existing one
        Args:
            pattern_text (str) - The command text pattern
            command_type (str) - Type of command (greeting, open_app, etc.)
        Returns: bool - Success status
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            try:
                # Try to insert new pattern
                cursor.execute('''
                    INSERT INTO patterns (pattern_text, command_type, frequency, last_used)
                    VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                ''', (pattern_text, command_type))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                # Pattern exists, update frequency
                cursor.execute('''
                    UPDATE patterns 
                    SET frequency = frequency + 1,
                        last_used = CURRENT_TIMESTAMP,
                        confidence = MIN(confidence + 0.05, 1.0)
                    WHERE pattern_text = ?
                ''', (pattern_text,))
                conn.commit()
                return True
            except Exception as e:
                print(f"Error learning pattern: {e}")
                return False
    
    # NEW: Add knowledge to knowledge base
    def add_knowledge(self, question, answer, topic=None):
        """
        Add information to the knowledge base
        Args:
            question (str) - The question or key
            answer (str) - The answer or information
            topic (str) - Optional topic/category
        Returns: int - Knowledge ID or None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO knowledge_base (topic, question, answer, created_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (topic, question, answer))
                conn.commit()
                return cursor.lastrowid
            except Exception as e:
                print(f"Error adding knowledge: {e}")
                return None
    
    # NEW: Get knowledge from knowledge base
    def get_knowledge(self, topic):
        """
        Retrieve knowledge by topic
        Args: topic (str) - The topic to search for
        Returns: list of tuples (question, answer, times_accessed)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Search by topic or question containing the topic
            cursor.execute('''
                SELECT question, answer, times_accessed, id
                FROM knowledge_base
                WHERE LOWER(topic) LIKE LOWER(?) 
                   OR LOWER(question) LIKE LOWER(?)
                   OR LOWER(answer) LIKE LOWER(?)
                ORDER BY times_accessed DESC, created_at DESC
                LIMIT 5
            ''', (f'%{topic}%', f'%{topic}%', f'%{topic}%'))
            
            results = cursor.fetchall()
            
            # Update access count for found items
            if results:
                for row in results:
                    cursor.execute('''
                        UPDATE knowledge_base 
                        SET times_accessed = times_accessed + 1,
                            last_accessed = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (row[3],))
                conn.commit()
            
            return [(row[0], row[1], row[2]) for row in results]
    
    # NEW: Get today's statistics
    def get_today_stats(self):
        """
        Get statistics for today
        Returns: dict with today's stats
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            today = datetime.now().date()
            
            stats = {}
            
            # Get from daily_stats table
            cursor.execute('''
                SELECT total_commands, successful_commands, wake_word_detections,
                       avg_confidence, avg_response_time_ms
                FROM daily_stats
                WHERE date = ?
            ''', (today,))
            
            result = cursor.fetchone()
            if result:
                stats['total_commands'] = result[0]
                stats['successful_commands'] = result[1]
                stats['wake_word_detections'] = result[2]
                stats['avg_confidence'] = round(result[3], 2) if result[3] else 0
                stats['avg_response_time_ms'] = round(result[4], 2) if result[4] else 0
                stats['success_rate'] = round((result[1] / result[0] * 100), 1) if result[0] > 0 else 0
            else:
                stats = {
                    'total_commands': 0,
                    'successful_commands': 0,
                    'wake_word_detections': 0,
                    'avg_confidence': 0,
                    'avg_response_time_ms': 0,
                    'success_rate': 0
                }
            
            # Get most used command type today
            cursor.execute('''
                SELECT command_type, COUNT(*) as count
                FROM interactions
                WHERE date(timestamp) = ?
                GROUP BY command_type
                ORDER BY count DESC
                LIMIT 1
            ''', (today,))
            
            top_command = cursor.fetchone()
            stats['top_command_type'] = top_command[0] if top_command else 'None'
            stats['top_command_count'] = top_command[1] if top_command else 0
            
            return stats
    
    # NEW: Get wake word stats
    def get_wake_word_stats(self, days=7):
        """Get wake word detection statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_detections,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful,
                    AVG(response_time_ms) as avg_response_time
                FROM wake_word_events
                WHERE timestamp > DATE('now', '-' || ? || ' days')
            ''', (days,))
            return cursor.fetchone()
    
    # NEW: Get apps by category
    def get_apps_by_category(self, category):
        """Get all apps in a category"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT app_name, app_path, aliases, launch_count
                FROM app_shortcuts
                WHERE category = ?
                ORDER BY launch_count DESC
            ''', (category,))
            return cursor.fetchall()
    
    # NEW: Get most active hours
    def get_active_hours(self):
        """Get command activity by hour"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
                FROM interactions
                GROUP BY hour
                ORDER BY hour
            ''')
            return cursor.fetchall()
    # UPDATED: get_statistics with more metrics
    def get_statistics(self):
        """Get overall statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total interactions
            cursor.execute('SELECT COUNT(*) FROM interactions')
            stats['total_interactions'] = cursor.fetchone()[0]
            
            # Success rate
            cursor.execute('SELECT AVG(CASE WHEN success THEN 100 ELSE 0 END) FROM interactions')
            stats['success_rate'] = round(cursor.fetchone()[0] or 0, 2)
            
            # Unique patterns
            cursor.execute('SELECT COUNT(DISTINCT pattern_text) FROM patterns')
            stats['learned_patterns'] = cursor.fetchone()[0]
            
            # Wake word detections
            cursor.execute('SELECT COUNT(*) FROM wake_word_events')
            stats['wake_word_detections'] = cursor.fetchone()[0]
            
            # Most active hour
            cursor.execute('''
                SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
                FROM interactions
                GROUP BY hour
                ORDER BY count DESC
                LIMIT 1
            ''')
            hour_data = cursor.fetchone()
            stats['peak_hour'] = f"{hour_data[0]}:00" if hour_data else "N/A"
            
            # Average response time
            cursor.execute('SELECT AVG(processing_time_ms) FROM interactions WHERE processing_time_ms IS NOT NULL')
            avg_time = cursor.fetchone()[0]
            stats['avg_response_time_ms'] = round(avg_time, 2) if avg_time else 0
            
            # Top command types
            cursor.execute('''
                SELECT command_type, COUNT(*) as count
                FROM interactions
                GROUP BY command_type
                ORDER BY count DESC
                LIMIT 5
            ''')
            stats['top_commands'] = cursor.fetchall()
            
            # Total apps known
            cursor.execute('SELECT COUNT(*) FROM app_shortcuts')
            stats['total_apps'] = cursor.fetchone()[0]
            
            return stats
    
    # NEW: Export data to JSON
    def export_to_json(self, output_path=None):
        """Export database to JSON file"""
        if not output_path:
            output_path = f"data/export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {}
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Export all tables
            tables = ['users', 'interactions', 'patterns', 'feedback', 
                     'app_shortcuts', 'knowledge_base', 'daily_stats', 
                     'wake_word_events', 'user_preferences']
            
            for table in tables:
                try:
                    cursor.execute(f'SELECT * FROM {table}')
                    rows = cursor.fetchall()
                    data[table] = [dict(row) for row in rows]
                except:
                    data[table] = []
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        return output_path
    
    # NEW: Clean up old data with confirmation
    def cleanup_old_data(self, days=30, confirm=True):
        """Clean up old interaction data"""
        if confirm:
            print(f"\n⚠️ This will delete interactions older than {days} days")
            response = input("Are you sure? (yes/no): ")
            if response.lower() != 'yes':
                print("Cleanup cancelled")
                return 0
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Delete old interactions
            cursor.execute('''
                DELETE FROM interactions 
                WHERE timestamp < DATE('now', '-' || ? || ' days')
            ''', (days,))
            deleted = cursor.rowcount
            
            # Delete old wake word events
            cursor.execute('''
                DELETE FROM wake_word_events 
                WHERE timestamp < DATE('now', '-' || ? || ' days')
            ''', (days,))
            deleted += cursor.rowcount
            
            conn.commit()
            return deleted
    
    # NEW: Vacuum database (optimize)
    def vacuum(self):
        """Optimize database by reclaiming unused space"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('VACUUM')
            return True
    
    # UPDATED: backup_database with compression option
    def backup_database(self, backup_path=None, compress=False):
        """Create a backup of the database"""
        if not backup_path:
            backup_path = f"data/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        shutil.copy2(self.db_path, backup_path)
        
        if compress:
            import zipfile
            zip_path = backup_path + '.zip'
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(backup_path, os.path.basename(backup_path))
            os.remove(backup_path)
            return zip_path
        
        return backup_path
    
    # NEW: Log screenshot to database
    def log_screenshot(self, filename, filepath, command_text=None, file_size_kb=None, success=True):
        """
        Log screenshot information to database
        Args:
            filename (str) - Screenshot filename
            filepath (str) - Full path to screenshot
            command_text (str) - Command that triggered screenshot
            file_size_kb (int) - File size in KB
            success (bool) - Whether screenshot was successful
        Returns: int - Screenshot ID or None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO screenshots (filename, filepath, command_text, file_size_kb, success, timestamp)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (filename, filepath, command_text, file_size_kb, success))
                conn.commit()
                return cursor.lastrowid
            except Exception as e:
                print(f"Error logging screenshot: {e}")
                return None
    
    # NEW: Get screenshot history
    def get_screenshot_history(self, limit=10):
        """
        Get recent screenshot history
        Args: limit (int) - Number of screenshots to retrieve
        Returns: list of tuples (filename, filepath, timestamp, file_size_kb)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT filename, filepath, timestamp, file_size_kb, command_text
                FROM screenshots
                WHERE success = 1
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            return cursor.fetchall()
    
    # NEW: Get screenshot count
    def get_screenshot_count(self):
        """Get total number of screenshots taken"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM screenshots WHERE success = 1')
            return cursor.fetchone()[0]


# =====================================================
# TEST UPDATED DATABASE
# =====================================================

if __name__ == "__main__":
    print("=" * 50)
    print("📊 TESTING HIRR DATABASE (UPDATED)")
    print("=" * 50)
    
    # Create database
    db = DatabaseManager()
    
    # Test 1: Log wake word events
    print("\n📝 Test 1: Logging wake word events...")
    db.log_wake_word("ai_assistent", True, 150)
    db.log_wake_word("hello ai_assistent", True, 200)
    db.log_wake_word("ai_assistent", True, 120)
    print("✅ Wake word events logged")
    
    # Test 2: Log interactions with processing time
    print("\n📝 Test 2: Logging interactions with timing...")
    id1 = db.log_interaction("hello ai_assistent", "Hello!", "greeting", 1.0, True, 50)
    id2 = db.log_interaction("open chrome", "Opening Chrome", "open_app", 0.9, True, 300)
    id3 = db.log_interaction("what time", "Time is 2:30", "time_query", 1.0, True, 45)
    print(f"✅ Logged interactions with timing")
    
    # Test 3: User preferences
    print("\n📝 Test 3: Setting user preferences...")
    db.set_preference("wake_word", "ai_assistent")
    db.set_preference("voice_speed", "175")
    db.set_preference("default_browser", "chrome")
    print(f"✅ Preferences saved")
    
    # Test 4: Get apps by category
    print("\n📝 Test 4: Getting apps by category...")
    browsers = db.get_apps_by_category('browser')
    print(f"   Browsers: {[app[0] for app in browsers]}")
    
    # Test 5: Wake word stats
    print("\n📝 Test 5: Wake word statistics...")
    wake_stats = db.get_wake_word_stats()
    if wake_stats:
        print(f"   Total detections: {wake_stats[0]}")
        print(f"   Success rate: {wake_stats[1]/wake_stats[0]*100:.1f}%")
        print(f"   Avg response: {wake_stats[2]:.0f}ms")
    
    # Test 6: Active hours
    print("\n📝 Test 6: Active hours...")
    hours = db.get_active_hours()
    for hour, count in hours:
        print(f"   {hour}:00 - {count} commands")
    
    # Test 7: Enhanced statistics
    print("\n📝 Test 7: Getting enhanced statistics...")
    stats = db.get_statistics()
    for key, value in stats.items():
        if key != 'top_commands':
            print(f"   • {key}: {value}")
    
    print("\n   Top command types:")
    for cmd_type, count in stats.get('top_commands', []):
        print(f"     - {cmd_type}: {count}")
    
    # Test 8: Export to JSON
    print("\n📝 Test 8: Exporting to JSON...")
    json_file = db.export_to_json()
    print(f"   ✅ Exported to {json_file}")
    
    # Test 9: NEW METHODS - Find app
    print("\n📝 Test 9: Testing find_app()...")
    app = db.find_app("chrome")
    if app:
        print(f"   ✅ Found: {app[0]} at {app[1]}")
    else:
        print("   ❌ App not found")
    
    # Test 10: NEW METHODS - Add app shortcut
    print("\n📝 Test 10: Testing add_app_shortcut()...")
    success = db.add_app_shortcut("test_app", "C:\\test\\app.exe", ["test", "myapp"], "testing")
    print(f"   {'✅' if success else '❌'} Add app shortcut: {success}")
    
    # Test 11: NEW METHODS - Learn pattern
    print("\n📝 Test 11: Testing learn_pattern()...")
    success = db.learn_pattern("open the browser", "open_app")
    print(f"   {'✅' if success else '❌'} Learn pattern: {success}")
    
    # Test 12: NEW METHODS - Add and get knowledge
    print("\n📝 Test 12: Testing add_knowledge() and get_knowledge()...")
    kb_id = db.add_knowledge("What is Python?", "Python is a programming language", "programming")
    print(f"   ✅ Added knowledge with ID: {kb_id}")
    
    knowledge = db.get_knowledge("python")
    if knowledge:
        print(f"   ✅ Retrieved {len(knowledge)} knowledge items")
        for q, a, count in knowledge[:2]:
            print(f"      Q: {q}")
            print(f"      A: {a[:50]}...")
    
    # Test 13: NEW METHODS - Get today's stats
    print("\n📝 Test 13: Testing get_today_stats()...")
    today_stats = db.get_today_stats()
    print(f"   Today's commands: {today_stats['total_commands']}")
    print(f"   Success rate: {today_stats['success_rate']}%")
    print(f"   Top command: {today_stats['top_command_type']} ({today_stats['top_command_count']}x)")
    
    print("\n✅ Database test complete!")

    print(f"📁 Database location: {db.db_path}")