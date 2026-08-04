"""Main application window: live posture status, points, streaks, and shop access."""

import os
import queue
import time
import tkinter as tk

import customtkinter as ctk

import config
from points_manager import PointsManager
from wifi_manager import WiFiManager

from sound_manager import SoundManager
from ui.shop_window import ShopWindow

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG_COLOR = "#1a1d24"
CARD_COLOR = "#242830"
MUTED_TEXT = "#9aa0ac"
LIGHT_TEXT = "#f5f5f7"

STATUS_STYLES = {
    "too_far": {"label": "TOO FAR", "sub": "Scoot in a little closer", "color": "#e5484d"},
    "too_close": {"label": "TOO CLOSE", "sub": "Ease back a bit", "color": "#e5484d"},
    "okay": {"label": "OKAY", "sub": "Perfect distance — keep it up!", "color": "#30a46c"},
    "unknown": {"label": "NO SIGNAL", "sub": "Waiting for your ESP32…", "color": "#5b616e"},
}


def format_duration(total_seconds):
    total_seconds = max(0, int(total_seconds))
    hours, rem = divmod(total_seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


class StatTile(ctk.CTkFrame):
    def __init__(self, master, title, **kwargs):
        super().__init__(master, corner_radius=12, fg_color=CARD_COLOR, **kwargs)
        ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=12), text_color=MUTED_TEXT).pack(pady=(12, 0))
        self.value_label = ctk.CTkLabel(self, text="--", font=ctk.CTkFont(size=20, weight="bold"))
        self.value_label.pack(pady=(2, 12))

    def set_value(self, text):
        self.value_label.configure(text=text)


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Posture Pal")
        self.geometry("420x600")
        self.minsize(380, 560)
        self.configure(fg_color=BG_COLOR)
        self._set_window_icon()

        self.points_manager = PointsManager()
        self.sound_manager = SoundManager()
        self.serial_manager = WiFiManager() # Kept the variable name the same so we don't have to rewrite the rest of the file!
        self.serial_manager.start()

        self.current_status_key = "unknown"
        self.last_message_time = 0.0
        self._last_autosave = time.monotonic()
        self.shop_window = None

        self._build_ui()
        self.serial_manager.start()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(150, self._poll)

    def _set_window_icon(self):
        # Best-effort cosmetic touch — never let icon quirks block startup.
        try:
            icon_path = os.path.join(config.ASSETS_DIR, "app_icon.png")
            self._icon_image = tk.PhotoImage(file=icon_path)
            self.iconphoto(True, self._icon_image)
        except Exception:
            pass

    # ---------------------------------------------------------------- UI --

    def _build_ui(self):
        ctk.CTkLabel(self, text="Posture Pal", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(24, 0))
        ctk.CTkLabel(self, text="Stay in the zone, earn Posture Points.",
                     font=ctk.CTkFont(size=12), text_color=MUTED_TEXT).pack(pady=(2, 20))

        self.status_card = ctk.CTkFrame(self, corner_radius=20, fg_color=STATUS_STYLES["unknown"]["color"],
                                         height=140)
        self.status_card.pack(padx=24, fill="x")
        self.status_card.pack_propagate(False)

        self.status_label = ctk.CTkLabel(self.status_card, text="NO SIGNAL",
                                          font=ctk.CTkFont(size=26, weight="bold"), text_color=LIGHT_TEXT)
        self.status_label.pack(pady=(30, 4))
        self.status_sub_label = ctk.CTkLabel(self.status_card, text="Waiting for your ESP32…",
                                              font=ctk.CTkFont(size=13), text_color=LIGHT_TEXT)
        self.status_sub_label.pack()

        stats_row = ctk.CTkFrame(self, fg_color="transparent")
        stats_row.pack(padx=24, pady=20, fill="x")
        stats_row.grid_columnconfigure((0, 1, 2), weight=1)

        self.streak_tile = StatTile(stats_row, "Current Streak")
        self.streak_tile.grid(row=0, column=0, padx=4, sticky="nsew")
        self.best_tile = StatTile(stats_row, "Best Streak")
        self.best_tile.grid(row=0, column=1, padx=4, sticky="nsew")
        self.points_tile = StatTile(stats_row, "Points")
        self.points_tile.grid(row=0, column=2, padx=4, sticky="nsew")

        self.shop_button = ctk.CTkButton(self, text="🛍  Open Shop", height=44,
                                          font=ctk.CTkFont(size=14, weight="bold"), command=self._open_shop)
        self.shop_button.pack(padx=24, pady=(4, 20), fill="x")

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=24, pady=16)
        self.connection_dot = ctk.CTkLabel(footer, text="●", text_color=MUTED_TEXT, font=ctk.CTkFont(size=14))
        self.connection_dot.pack(side="left")
        self.connection_label = ctk.CTkLabel(footer, text="Connecting…", font=ctk.CTkFont(size=12),
                                              text_color=MUTED_TEXT)
        self.connection_label.pack(side="left", padx=(6, 0))

    # ------------------------------------------------------------ polling --

    def _poll(self):
        self._drain_serial_queue()
        self._tick()
        self.after(150, self._poll)

    def _drain_serial_queue(self):
        while True:
            try:
                kind, value, extra = self.serial_manager.incoming_queue.get_nowait()
            except queue.Empty:
                break
            if kind == "data":
                self._handle_signal(value)
            elif kind == "status":
                self._handle_connection_status(value, extra)

    def _handle_signal(self, text):
        normalized = text.strip().lower()
        if normalized == config.SIGNAL_OKAY:
            key = "okay"
        elif normalized == config.SIGNAL_TOO_FAR:
            key = "too_far"
        elif normalized == config.SIGNAL_TOO_CLOSE:
            key = "too_close"
        else:
            return  # unrecognized line (debug print, etc.) — ignore it

        self.last_message_time = time.monotonic()
        self.current_status_key = key
        self._apply_status_style(key)

        if key == "too_far":
            self.sound_manager.play_alert("too_far")
        elif key == "too_close":
            self.sound_manager.play_alert("too_close")
        else:
            self.sound_manager.reset_cooldown()

    def _handle_connection_status(self, status, port):
        if status == "connected":
            self.connection_dot.configure(text_color="#30a46c")
            self.connection_label.configure(text=f"Connected — {port}")
        elif status == "no_port":
            self.connection_dot.configure(text_color="#e5484d")
            self.connection_label.configure(text="No serial port found — retrying…")
            self.current_status_key = "unknown"
            self._apply_status_style("unknown")
        else:  # "disconnected"
            self.connection_dot.configure(text_color="#e5484d")
            label = f"Lost connection to {port} — retrying…" if port else "Disconnected — retrying…"
            self.connection_label.configure(text=label)
            self.current_status_key = "unknown"
            self._apply_status_style("unknown")

    def _apply_status_style(self, key):
        style = STATUS_STYLES[key]
        self.status_card.configure(fg_color=style["color"])
        self.status_label.configure(text=style["label"])
        self.status_sub_label.configure(text=style["sub"])

    def _tick(self):
        now = time.monotonic()
        if self.current_status_key != "unknown" and now - self.last_message_time > config.SIGNAL_STALE_AFTER:
            self.current_status_key = "unknown"
            self._apply_status_style("unknown")

        is_okay = self.serial_manager.connected and self.current_status_key == "okay"
        self.points_manager.tick(is_okay)

        self.streak_tile.set_value(format_duration(self.points_manager.current_streak))
        self.best_tile.set_value(format_duration(self.points_manager.high_score))
        self.points_tile.set_value(str(int(self.points_manager.points)))

        if self.shop_window is not None and self.shop_window.winfo_exists():
            self.shop_window.refresh()

        if now - self._last_autosave > config.AUTOSAVE_INTERVAL_SECONDS:
            self.points_manager.save_if_dirty()
            self._last_autosave = now

    # ------------------------------------------------------------ actions --

    def _open_shop(self):
        if self.shop_window is not None and self.shop_window.winfo_exists():
            self.shop_window.focus()
            return
        self.shop_window = ShopWindow(self, self.points_manager, self.serial_manager.send_command)

    def _on_close(self):
        self.points_manager.save_if_dirty(force=True)
        self.serial_manager.stop()
        self.destroy()