import os
import sys
import platform

# Only works on Windows
if platform.system() == 'Windows':
    import winreg

class AppScanner:
    def __init__(self, logger=None):
        self.logger = logger
        self.apps = {}
        
        if platform.system() != 'Windows':
            self._log("AppScanner only works on Windows. Disabled.")
            return
            
        self._log("🔍 Initializing Deep App Scanner...")
        self.scan_registry()

    def _log(self, msg):
        if self.logger:
            self.logger.info(msg)
        else:
            print(msg)

    def scan_registry(self):
        """Scans Windows Registry for installed execution paths."""
        paths_to_scan = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
        ]

        count = 0
        for hkey, subkey in paths_to_scan:
            try:
                registry_key = winreg.OpenKey(hkey, subkey, 0, winreg.KEY_READ)
                num_subkeys, _, _ = winreg.QueryInfoKey(registry_key)
                
                for i in range(num_subkeys):
                    try:
                        app_name_ext = winreg.EnumKey(registry_key, i)
                        app_path_key = winreg.OpenKey(registry_key, app_name_ext)
                        app_path, _ = winreg.QueryValueEx(app_path_key, "")
                        
                        if app_path and os.path.exists(app_path):
                            # Clean up name: "photoshop.exe" -> "photoshop"
                            clean_name = app_name_ext.lower().replace('.exe', '')
                            self.apps[clean_name] = app_path
                            count += 1
                            
                        winreg.CloseKey(app_path_key)
                    except WindowsError:
                        continue
                winreg.CloseKey(registry_key)
            except WindowsError:
                continue

        self._log(f"✅ Deep Scanner found {count} applications registered in OS paths.")

    def find_app(self, app_name):
        """Finds application path by name."""
        if not self.apps:
            return None
            
        app_name = app_name.lower().strip()
        
        # Direct match
        if app_name in self.apps:
            return self.apps[app_name]
            
        # Partial match
        for registered_name, path in self.apps.items():
            if app_name in registered_name or registered_name in app_name:
                return path
                
        return None

if __name__ == "__main__":
    scanner = AppScanner()
    print("Test Search 'chrome':", scanner.find_app("chrome"))
    print("Test Search 'notepad':", scanner.find_app("notepad"))
    
    # Just printing 5 random found apps
    print("\nSample found apps:")
    for i, (k, v) in enumerate(scanner.apps.items()):
        print(f" - {k}: {v}")
        if i >= 4:
            break
