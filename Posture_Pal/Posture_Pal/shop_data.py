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
    
        {
    "id": "cat_robot",
    "name": "Kitty",
    "description": "Turn your robot into a cat",
    "cost": 500,
    "thumbnail": "data:image/png;base64,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",
        }
]