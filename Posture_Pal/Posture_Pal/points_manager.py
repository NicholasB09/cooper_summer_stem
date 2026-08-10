"""Tracks Posture Points, the current 'okay' streak, and the best streak (high score)."""

import time

import config
import storage


class PointsManager:
    def __init__(self):
        saved = storage.load_data()
        self.points = saved.get("points", 0)
        self.high_score = saved.get("high_score", 0)
        self.unlocked = set(saved.get("unlocked", []))

        self.current_streak = 0.0
        self._last_tick = time.monotonic()
        self._dirty = False

    def tick(self, is_okay):
        """
        Advance the internal clock. Call this regularly (e.g. every 100-300ms) with
        whether the tracked status is currently "okay". Points and the current streak
        only grow while is_okay is True; leaving the okay zone resets the streak
        (but never the point balance or the high score).
        """
        now = time.monotonic()
        dt = min(now - self._last_tick, 2.0)  # clamp so a long pause can't award a huge burst
        self._last_tick = now

        if is_okay:
            self.current_streak += dt
            self.points += dt * config.POINTS_PER_SECOND_OKAY
            if self.current_streak > self.high_score:
                self.high_score = self.current_streak
            self._dirty = True
        elif self.current_streak > 0:
            self.current_streak = 0.0
            self._dirty = True

    def can_afford(self, cost):
        return self.points >= cost

    def spend(self, cost):
        if not self.can_afford(cost):
            return False
        self.points -= cost
        self._dirty = True
        return True

    def unlock(self, animation_id):
        self.unlocked.add(animation_id)
        self._dirty = True

    def is_unlocked(self, animation_id):
        return animation_id in self.unlocked

    def save_if_dirty(self, force=False):
        if not (self._dirty or force):
            return
        storage.save_data({
            "points": self.points,
            "high_score": self.high_score,
            "unlocked": sorted(self.unlocked),
        })
        self._dirty = False