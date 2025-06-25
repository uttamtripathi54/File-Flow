import json
import os

class SettingsManager:
    """
    Manages application settings, loading them from and saving them to a JSON file.
    """
    def __init__(self, config_file="config.json"):
        # Determine the absolute path to the config file relative to the script's execution.
        # This assumes config.json is in the project root, one level up from src/.
        self.config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), config_file)
        self.settings = {}
        self._load_settings()

    def _load_settings(self):
        """Loads settings from the config JSON file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.settings = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Could not decode {self.config_file}. Using default settings.")
                self._set_default_settings()
            except Exception as e:
                print(f"Error loading settings from {self.config_file}: {e}. Using default settings.")
                self._set_default_settings()
        else:
            print(f"Config file not found at {self.config_file}. Creating with default settings.")
            self._set_default_settings()
            self._save_settings() # Save default settings if file didn't exist

    def _set_default_settings(self):
        """Sets a default structure for settings if the file is missing or corrupted."""
        self.settings = {
            "default_source_dir": "",
            "default_destination_dir": "",
            "file_categories": {
                "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xls", ".xlsx", ".ppt", ".pptx", ".csv"],
                "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"],
                "Videos": [".mp4", ".mkv", ".flv", ".avi", ".mov", ".wmv"],
                "Audio": [".mp3", ".wav", ".aac", ".flac", ".ogg"],
                "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
                "Executables": [".exe", ".msi", ".dmg", ".appimage"],
                "Code": [".py", ".java", ".c", ".cpp", ".html", ".css", ".js", ".php"],
                "Others": [] # Files not matching any category
            },
            "duplicate_handling": "rename", # Options: "skip", "rename"
            "enable_desktop_notifications": True,
            "log_file_path": "organizer_log.txt",
            "sort_by_date_format": "None", # Options: "None", "Year", "Year-Month", "Year-Month-Day"
            "exclude_folders": [".git", "venv", "__pycache__", "node_modules", ".DS_Store"] # New default excluded folders
        }

    def _save_settings(self):
        """Saves current settings to the JSON file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings to {self.config_file}: {e}")

    def get(self, key, default=None):
        """Retrieves a setting by key."""
        return self.settings.get(key, default)

    def set(self, key, value):
        """Sets a setting by key and immediately saves it."""
        self.settings[key] = value
        self._save_settings()

    def get_categories(self):
        """Returns the file categories mapping."""
        return self.settings.get("file_categories", {})

    def get_excluded_folders(self):
        """Returns the list of folder names to exclude from traversal."""
        return self.settings.get("exclude_folders", [])