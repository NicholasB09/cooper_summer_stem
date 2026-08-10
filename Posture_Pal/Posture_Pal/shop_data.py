"""
Definitions for animations that can be purchased in the Posture Points shop.

Edit this list to match the animations already programmed on your ESP32's OLED.
The "id" must exactly match whatever your ESP32 code expects after the
"UNLOCK:" prefix (see config.UNLOCK_PREFIX and the README for the protocol).
"""

import os

import config

ANIMATIONS = [
    {
        "id": "confetti",
        "name": "Confetti Burst",
        "description": "A colorful burst of falling confetti.",
        "cost": 50,
        "thumbnail": os.path.join(config.THUMBNAILS_DIR, "confetti.png"),
    },
    {
        "id": "starfield",
        "name": "Starfield",
        "description": "Twinkling stars drifting across the screen.",
        "cost": 75,
        "thumbnail": os.path.join(config.THUMBNAILS_DIR, "starfield.png"),
    },
    {
        "id": "rainbow_wave",
        "name": "Rainbow Wave",
        "description": "A smooth wave of color sweeping by.",
        "cost": 100,
        "thumbnail": os.path.join(config.THUMBNAILS_DIR, "rainbow.png"),
    },
    {
        "id": "fireworks",
        "name": "Pixel Fireworks",
        "description": "Fireworks bursting in pixel art style.",
        "cost": 150,
        "thumbnail": os.path.join(config.THUMBNAILS_DIR, "fireworks.png"),
    },
    {
        "id": "matrix_rain",
        "name": "Matrix Rain",
        "description": "Cascading characters, straight out of the Matrix.",
        "cost": 200,
        "thumbnail": os.path.join(config.THUMBNAILS_DIR, "matrix.png"),
    },
    {
        "id": "dancing_robot",
        "name": "Dancing Robot",
        "description": "A little robot dances to celebrate great posture.",
        "cost": 300,
        "thumbnail": os.path.join(config.THUMBNAILS_DIR, "robot.png"),
    },
]