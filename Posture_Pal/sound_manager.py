"""Plays short notification sounds when posture drifts out of the okay zone."""

import time

import pygame

import config


class SoundManager:
    def __init__(self):
        self.enabled = True
        self.sounds = {}
        try:
            pygame.mixer.init()
            self.sounds["too_far"] = pygame.mixer.Sound(config.TOO_FAR_SOUND)
            self.sounds["too_close"] = pygame.mixer.Sound(config.TOO_CLOSE_SOUND)
        except Exception as exc:  # depends on the host machine's audio setup
            print(f"[SoundManager] Audio unavailable, alerts will be silent: {exc}")
            self.enabled = False

        self._last_played = {}

    def play_alert(self, key):
        """Play the alert for `key` ("too_far" or "too_close"), respecting a cooldown."""
        if not self.enabled:
            return
        now = time.monotonic()
        if now - self._last_played.get(key, 0.0) >= config.ALERT_COOLDOWN_SECONDS:
            self.sounds[key].play()
            self._last_played[key] = now

    def reset_cooldown(self):
        """Call when posture returns to okay so the next alert fires immediately."""
        self._last_played.clear()