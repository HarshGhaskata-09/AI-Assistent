#!/usr/bin/env python3
# utils/platform_paths.py - Cross-platform application path detection

import os
import platform
import shutil
from pathlib import Path


class PlatformPaths:
    """Cross-platform application path finder"""
    
    @staticmethod
    def get_system():
        """Get current operating system"""
        return platform.system()
    
    @staticmethod
    def get_home_dir():
        """Get user home directory"""
        return str(Path.home())
    
    @staticmethod
    def get_username():
        """Get current username safely"""
        try:
            return os.getlogin()
        except:
            return os.environ.get('USERNAME') or os.environ.get('USER') or 'user'
    
    @staticmethod
    def find_app_path(app_name):
        """
        Find application path across different operating systems
        Args: app_name (str) - Name of the application
        Returns: str - Path to application or None
        """
        system = PlatformPaths.get_system()
        app_name_lower = app_name.lower()
        
        # Check if app is in PATH first (works on all platforms)
        path_result = shutil.which(app_name)
        if path_result:
            return path_result
        
        # Platform-specific search
        if system == 'Windows':
            return PlatformPaths._find_windows_app(app_name_lower)
        elif system == 'Darwin':  # macOS
            return PlatformPaths._find_macos_app(app_name_lower)
        elif system == 'Linux':
            return PlatformPaths._find_linux_app(app_name_lower)
        
        return None
    
    @staticmethod
    def _find_windows_app(app_name):
        """Find application on Windows"""
        username = PlatformPaths.get_username()
        
        # Common Windows application paths
        search_paths = {
            'chrome': [
                r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
                f'C:\\Users\\{username}\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe'
            ],
            'firefox': [
                r'C:\Program Files\Mozilla Firefox\firefox.exe',
                r'C:\Program Files (x86)\Mozilla Firefox\firefox.exe'
            ],
            'edge': [
                r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
                r'C:\Program Files\Microsoft\Edge\Application\msedge.exe'
            ],
            'vscode': [
                f'C:\\Users\\{username}\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe',
                r'C:\Program Files\Microsoft VS Code\Code.exe',
                r'C:\Program Files (x86)\Microsoft VS Code\Code.exe'
            ],
            'notepad': ['notepad.exe'],
            'notepad++': [
                r'C:\Program Files\Notepad++\notepad++.exe',
                r'C:\Program Files (x86)\Notepad++\notepad++.exe'
            ],
            'calculator': ['calc.exe'],
            'explorer': ['explorer.exe'],
            'cmd': ['cmd.exe'],
            'powershell': ['powershell.exe'],
            'spotify': [
                f'C:\\Users\\{username}\\AppData\\Roaming\\Spotify\\Spotify.exe'
            ],
            'discord': [
                f'C:\\Users\\{username}\\AppData\\Local\\Discord\\app-*\\Discord.exe'
            ],
            'slack': [
                f'C:\\Users\\{username}\\AppData\\Local\\slack\\slack.exe'
            ],
            'zoom': [
                r'C:\Program Files\Zoom\bin\Zoom.exe',
                f'C:\\Users\\{username}\\AppData\\Roaming\\Zoom\\bin\\Zoom.exe'
            ]
        }
        
        # Check if app is in our known paths
        if app_name in search_paths:
            for path in search_paths[app_name]:
                # Handle wildcards
                if '*' in path:
                    import glob
                    matches = glob.glob(path)
                    if matches:
                        return matches[0]
                elif os.path.exists(path):
                    return path
        
        return None
    
    @staticmethod
    def _find_macos_app(app_name):
        """Find application on macOS"""
        
        # Common macOS application paths
        search_paths = {
            'chrome': [
                '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
            ],
            'firefox': [
                '/Applications/Firefox.app/Contents/MacOS/firefox'
            ],
            'safari': [
                '/Applications/Safari.app/Contents/MacOS/Safari'
            ],
            'vscode': [
                '/Applications/Visual Studio Code.app/Contents/MacOS/Electron'
            ],
            'spotify': [
                '/Applications/Spotify.app/Contents/MacOS/Spotify'
            ],
            'slack': [
                '/Applications/Slack.app/Contents/MacOS/Slack'
            ],
            'zoom': [
                '/Applications/zoom.us.app/Contents/MacOS/zoom.us'
            ],
            'terminal': [
                '/System/Applications/Utilities/Terminal.app/Contents/MacOS/Terminal'
            ]
        }
        
        # Check if app is in our known paths
        if app_name in search_paths:
            for path in search_paths[app_name]:
                if os.path.exists(path):
                    return path
        
        # Try to find .app bundle
        app_bundle = f'/Applications/{app_name.capitalize()}.app'
        if os.path.exists(app_bundle):
            return f'open -a "{app_bundle}"'
        
        return None
    
    @staticmethod
    def _find_linux_app(app_name):
        """Find application on Linux"""
        
        # Common Linux application names
        app_mapping = {
            'chrome': 'google-chrome',
            'firefox': 'firefox',
            'vscode': 'code',
            'spotify': 'spotify',
            'slack': 'slack',
            'zoom': 'zoom',
            'terminal': 'gnome-terminal',
            'calculator': 'gnome-calculator',
            'notepad': 'gedit'
        }
        
        # Map to Linux app name
        linux_app = app_mapping.get(app_name, app_name)
        
        # Check if in PATH
        path = shutil.which(linux_app)
        if path:
            return path
        
        # Check common installation directories
        common_dirs = [
            '/usr/bin',
            '/usr/local/bin',
            '/snap/bin',
            '/opt',
            f'{PlatformPaths.get_home_dir()}/.local/bin'
        ]
        
        for directory in common_dirs:
            app_path = os.path.join(directory, linux_app)
            if os.path.exists(app_path):
                return app_path
        
        return None
    
    @staticmethod
    def get_default_apps():
        """
        Get default applications for current platform
        Returns: list of tuples (app_name, app_path, aliases, category, is_default)
        """
        system = PlatformPaths.get_system()
        
        if system == 'Windows':
            return PlatformPaths._get_windows_defaults()
        elif system == 'Darwin':
            return PlatformPaths._get_macos_defaults()
        elif system == 'Linux':
            return PlatformPaths._get_linux_defaults()
        
        return []
    
    @staticmethod
    def _get_windows_defaults():
        """Get default Windows applications"""
        apps = []
        app_list = [
            ('chrome', 'browser', '["google", "browser"]'),
            ('firefox', 'browser', '["mozilla"]'),
            ('edge', 'browser', '["microsoft edge"]'),
            ('notepad', 'utilities', '["editor", "text"]'),
            ('calculator', 'utilities', '["calc"]'),
            ('explorer', 'system', '["files", "folder"]'),
            ('cmd', 'system', '["command prompt", "terminal"]'),
            ('powershell', 'system', '["shell"]'),
            ('vscode', 'development', '["code", "visual studio"]'),
            ('spotify', 'entertainment', '["music"]')
        ]
        
        for app_name, category, aliases in app_list:
            path = PlatformPaths.find_app_path(app_name)
            if path:
                is_default = 1 if category in ['browser', 'utilities', 'system'] else 0
                apps.append((app_name, path, aliases, category, is_default))
        
        return apps
    
    @staticmethod
    def _get_macos_defaults():
        """Get default macOS applications"""
        apps = []
        app_list = [
            ('chrome', 'browser', '["google", "browser"]'),
            ('firefox', 'browser', '["mozilla"]'),
            ('safari', 'browser', '["apple browser"]'),
            ('terminal', 'system', '["console", "shell"]'),
            ('vscode', 'development', '["code", "visual studio"]'),
            ('spotify', 'entertainment', '["music"]')
        ]
        
        for app_name, category, aliases in app_list:
            path = PlatformPaths.find_app_path(app_name)
            if path:
                is_default = 1 if category in ['browser', 'system'] else 0
                apps.append((app_name, path, aliases, category, is_default))
        
        return apps
    
    @staticmethod
    def _get_linux_defaults():
        """Get default Linux applications"""
        apps = []
        app_list = [
            ('chrome', 'browser', '["google", "browser"]'),
            ('firefox', 'browser', '["mozilla"]'),
            ('terminal', 'system', '["console", "shell"]'),
            ('calculator', 'utilities', '["calc"]'),
            ('notepad', 'utilities', '["editor", "text", "gedit"]'),
            ('vscode', 'development', '["code", "visual studio"]'),
            ('spotify', 'entertainment', '["music"]')
        ]
        
        for app_name, category, aliases in app_list:
            path = PlatformPaths.find_app_path(app_name)
            if path:
                is_default = 1 if category in ['browser', 'system'] else 0
                apps.append((app_name, path, aliases, category, is_default))
        
        return apps


# Test function
if __name__ == "__main__":
    print("=" * 60)
    print("🔍 PLATFORM PATH DETECTION TEST")
    print("=" * 60)
    
    print(f"\n📊 System: {PlatformPaths.get_system()}")
    print(f"📁 Home: {PlatformPaths.get_home_dir()}")
    print(f"👤 User: {PlatformPaths.get_username()}")
    
    print("\n" + "=" * 60)
    print("🔎 SEARCHING FOR APPLICATIONS")
    print("=" * 60)
    
    test_apps = ['chrome', 'firefox', 'vscode', 'notepad', 'calculator', 'spotify']
    
    for app in test_apps:
        path = PlatformPaths.find_app_path(app)
        status = "✅" if path else "❌"
        print(f"{status} {app:15} -> {path or 'Not found'}")
    
    print("\n" + "=" * 60)
    print("📦 DEFAULT APPLICATIONS")
    print("=" * 60)
    
    defaults = PlatformPaths.get_default_apps()
    for app_name, path, aliases, category, is_default in defaults:
        print(f"✅ {app_name:15} [{category:12}] -> {path}")
    
    print(f"\n✅ Found {len(defaults)} default applications")
