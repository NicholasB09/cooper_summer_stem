"""
Posture Pal configuration.
 
Tweak the values below to match your ESP32 setup and personal preferences.
Everything else in the app reads from this file, so this is the only place
you should usually need to touch.
"""
 
import os
 
# ---------------------------------------------------------------------------
# Wi-Fi connection
# ---------------------------------------------------------------------------

# The IP Address of your ESP32. 
# If the ESP32 is creating its own Wi-Fi network (Access Point), 
# the default IP is usually "192.168.4.1".
ESP32_IP = "192.168.4.1" 

# The port your ESP32 TCP server is running on (usually 80 or 8080)
ESP32_PORT = 8080

# How long to wait for incoming data before cycling the loop to check 
# for outgoing data. Kept short so the GUI doesn't lag.
SOCKET_TIMEOUT = 0.3

# How long (seconds) to wait before retrying after a failed/lost connection.
RECONNECT_DELAY = 3.0
 
 
# If no recognized signal has been received in this many seconds (while
# otherwise connected), the app shows "No Signal" and pauses point tracking,
# instead of assuming you're still in whatever zone you were last in.
SIGNAL_STALE_AFTER = 5.0
 
# ---------------------------------------------------------------------------
# Signal text — must match what your ESP32 sends over serial. Matching is
# case-insensitive and whitespace is trimmed automatically on the Python side.
# ---------------------------------------------------------------------------
 
SIGNAL_TOO_FAR = "too far"
SIGNAL_OKAY = "okay"
SIGNAL_TOO_CLOSE = "too close"
 
# ---------------------------------------------------------------------------
# Outgoing commands (Python -> ESP32)
# ---------------------------------------------------------------------------
 
# When an animation is unlocked (or previewed) in the shop, the app sends:
#   UNLOCK:<animation_id>\n
# Change UNLOCK_PREFIX if your ESP32 sketch expects a different keyword.
UNLOCK_PREFIX = "UNLOCK"
 
# New: Command sent to ESP32 to set current posture as baseline
CALIBRATE_COMMAND = "CALIBRATE"

# ---------------------------------------------------------------------------
# Posture Points
# ---------------------------------------------------------------------------
 
POINTS_PER_SECOND_OKAY = 1.0     # Posture Points earned per second in the "okay" zone
AUTOSAVE_INTERVAL_SECONDS = 10   # how often progress is written to disk in the background
 
# ---------------------------------------------------------------------------
# Notification sounds
# ---------------------------------------------------------------------------
 
# Minimum seconds between repeated alerts for the same ongoing bad posture,
# so the app reminds you without nagging on every single ESP32 message.
ALERT_COOLDOWN_SECONDS = 20.0
 
# ---------------------------------------------------------------------------
# Paths (shouldn't need to change these)
# ---------------------------------------------------------------------------
 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
THUMBNAILS_DIR = os.path.join(ASSETS_DIR, "thumbnails")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")
DATA_DIR = os.path.join(BASE_DIR, "data")
SAVE_FILE = os.path.join(DATA_DIR, "save_data.json")
 
TOO_FAR_SOUND = os.path.join(SOUNDS_DIR, "too_far.wav")
TOO_CLOSE_SOUND = os.path.join(SOUNDS_DIR, "too_close.wav")