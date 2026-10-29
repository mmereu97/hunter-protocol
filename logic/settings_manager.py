import json
import os

from config import Config

SETTINGS_FILE = Config.SETTINGS_FILE

DEFAULT_SETTINGS = {
    "last_active_tab_index": 0,
    "window_geometry": None,
    "knowledge_filter_index": 0,
    "monster_injection_count": 3,
    "ai_history_limit": 10,
    # --- NOI SETĂRI ---
    "question_recurrence_value": 6,
    "question_recurrence_unit": "Luni" # Zile, Săptămâni, Luni, Ani
}

class SettingsManager:
    @staticmethod
    def load_settings():
        if not os.path.exists(SETTINGS_FILE):
            return DEFAULT_SETTINGS.copy()
        
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                # Merge cu default-urile pentru chei noi
                return {**DEFAULT_SETTINGS, **data}
        except Exception:
            return DEFAULT_SETTINGS.copy()

    @staticmethod
    def save_settings(data):
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Eroare salvare setări: {e}")

    @staticmethod
    def update_key(key, value):
        current = SettingsManager.load_settings()
        current[key] = value
        SettingsManager.save_settings(current)