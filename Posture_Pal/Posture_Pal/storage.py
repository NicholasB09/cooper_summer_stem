"""Simple JSON-backed persistence for points, high score, and unlocked animations."""
 
import json
import os
 
import config
 
 
def load_data():
    """Load saved progress from disk. Returns an empty dict if nothing is saved yet."""
    if not os.path.exists(config.SAVE_FILE):
        return {}
    try:
        with open(config.SAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
 
 
def save_data(data):
    """Write progress to disk atomically, so a crash mid-write can't corrupt the save file."""
    os.makedirs(config.DATA_DIR, exist_ok=True)
    tmp_path = config.SAVE_FILE + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, config.SAVE_FILE)
 