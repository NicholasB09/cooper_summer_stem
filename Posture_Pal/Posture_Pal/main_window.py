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

# --- Modern Palette ---
BG_COLOR = "#0F172A"        # Deep Slate
CARD_BG = "#1E293B"         # Dark Surface
CARD_BORDER = "#334155"     # Subtle Outline
TEXT_PRIMARY = "#F8FAFC"    # Crisp White
TEXT_SECONDARY = "#94A3B8"  # Slate Muted
ACCENT_BLUE = "#38BDF8"     # Sky Accent

STATUS_STYLES = {
    "too_far": {
        "label": "TOO FAR AWAY",
        "sub": "Scoot a little closer to your display",
        "bg": "#451A1A",
        "border": "#991B1B",
        "badge_bg": "#7F1D1D",
        "badge_text": "#FCA5A5",
        "icon": "↔️"
    },
    "too_close": {
        "label": "TOO CLOSE",
        "sub": "Ease back and relax your posture",
        "bg": "#451A1A",
        "border": "#991B1B",
        "badge_bg": "#7F1D1D",
        "badge_text": "#FCA5A5",
        "icon": "⚠️"
    },
    "okay": {
        "label": "PERFECT POSTURE",
        "sub": "You're in the optimal zone — keep it up!",
        "bg": "#064E3B",
        "border": "#059669",
        "badge_bg": "#065F46",
        "badge_text": "#6EE7B7",
        "icon": "✨"
    },
    "unknown": {
        "label": "WAITING FOR SIGNAL",
        "sub": "Connecting to your ESP32 posture monitor…",
        "bg": "#182232",
        "border": "#334155",
        "badge_bg": "#334155",
        "badge_text": "#94A3B8",
        "icon": "📡"
    },
}


def format_duration(total_seconds):
    total_seconds = max(0, int(total_seconds))
    hours, rem = divmod(total_seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


class StatTile(ctk.CTkFrame):
    """Reusable card display for real-time stats."""
    def __init__(self, master, title, icon="📊", **kwargs):
        super().__init__(
            master,
            corner_radius=16,
            fg_color=CARD_BG,
            border_width=1,
            border_color=CARD_BORDER,
            **kwargs
        )
        
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(pady=(12, 2), padx=12, fill="x")
        
        ctk.CTkLabel(
            header,
            text=f"{icon}  {title}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT_SECONDARY
        ).pack(anchor="w")

        # Metric Value
        self.value_label = ctk.CTkLabel(
            self,
            text="--",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=TEXT_PRIMARY
        )
        self.value_label.pack(pady=(0, 12), padx=12, anchor="w")

    def set_value(self, text):
        self.value_label.configure(text=text)


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Posture Pal")
        self.geometry("440x650")
        self.minsize(400, 600)
        self.configure(fg_color=BG_COLOR)
        self._set_window_icon()

        # Core logic setup (Architecture unchanged)
        self.points_manager = PointsManager()
        self.sound_manager = SoundManager()
        self.serial_manager = WiFiManager()
        self.serial_manager.start()

        self.current_status_key = "unknown"
        self.last_message_time = 0.0
        self._last_autosave = time.monotonic()
        self.shop_window = None

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(150, self._poll)

    def _set_window_icon(self):
        try:
            icon_path = os.path.join(config.ASSETS_DIR, "app_icon.png")
            self._icon_image = tk.PhotoImage(file=icon_path)
            self.iconphoto(True, self._icon_image)
        except Exception:
            pass

    # ---------------------------------------------------------------- UI --

    def _build_ui(self):
        # App Title Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(pady=(28, 16), padx=24, fill="x")

        ctk.CTkLabel(
            header_frame,
            text="POSTURE PAL",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            header_frame,
            text="Live ergonomics & real-time point tracking",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SECONDARY
        ).pack(anchor="w", pady=(2, 0))

        # Main Posture Display Card
        self.status_card = ctk.CTkFrame(
            self,
            corner_radius=20,
            fg_color=STATUS_STYLES["unknown"]["bg"],
            border_width=2,
            border_color=STATUS_STYLES["unknown"]["border"],
            height=165
        )
        self.status_card.pack(padx=24, fill="x")
        self.status_card.pack_propagate(False)

        # Status Pill Badge
        self.badge_frame = ctk.CTkFrame(
            self.status_card,
            corner_radius=20,
            fg_color=STATUS_STYLES["unknown"]["badge_bg"]
        )
        self.badge_frame.pack(anchor="w", padx=20, pady=(18, 0))

        self.badge_label = ctk.CTkLabel(
            self.badge_frame,
            text="📡  STATUS",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=STATUS_STYLES["unknown"]["badge_text"]
        )
        self.badge_label.pack(padx=12, pady=4)

        # Main Status Headline & Subtitle
        self.status_label = ctk.CTkLabel(
            self.status_card,
            text="WAITING FOR SIGNAL",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=TEXT_PRIMARY
        )
        self.status_label.pack(anchor="w", padx=20, pady=(10, 2))

        self.status_sub_label = ctk.CTkLabel(
            self.status_card,
            text="Connecting to your ESP32 posture monitor…",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SECONDARY
        )
        self.status_sub_label.pack(anchor="w", padx=20)

        # Statistics Row (Streak / Best / Points)
        stats_row = ctk.CTkFrame(self, fg_color="transparent")
        stats_row.pack(padx=24, pady=20, fill="x")
        stats_row.grid_columnconfigure((0, 1, 2), weight=1)

        self.streak_tile = StatTile(stats_row, "STREAK", icon="🔥")
        self.streak_tile.grid(row=0, column=0, padx=(0, 4), sticky="nsew")

        self.best_tile = StatTile(stats_row, "BEST", icon="👑")
        self.best_tile.grid(row=0, column=1, padx=4, sticky="nsew")

        self.points_tile = StatTile(stats_row, "POINTS", icon="💎")
        self.points_tile.grid(row=0, column=2, padx=(4, 0), sticky="nsew")

        # Shop Action Button
        self.shop_button = ctk.CTkButton(
            self,
            text="🛍   Open Reward Shop",
            height=48,
            corner_radius=14,
            fg_color="#0284C7",
            hover_color="#0369A1",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._open_shop
        )
        self.shop_button.pack(padx=24, pady=(4, 20), fill="x")

        # Footer Status Bar
        footer = ctk.CTkFrame(
            self,
            fg_color=CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=CARD_BORDER,
            height=40
        )
        footer.pack(side="bottom", fill="x", padx=24, pady=20)
        footer.pack_propagate(False)

        self.connection_dot = ctk.CTkLabel(
            footer,
            text="●",
            text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(size=14)
        )
        self.connection_dot.pack(side="left", padx=(14, 0))

        self.connection_label = ctk.CTkLabel(
            footer,
            text="Connecting…",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT_SECONDARY
        )
        self.connection_label.pack(side="left", padx=(8, 0))

    # ------------------------------------------------------------ Polling --

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
            return  # Ignore debug logs/unrecognized output

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
            self.connection_dot.configure(text_color="#10B981")
            self.connection_label.configure(text=f"Connected to ESP32 ({port})")
        elif status == "no_port":
            self.connection_dot.configure(text_color="#EF4444")
            self.connection_label.configure(text="No network host found — retrying…")
            self.current_status_key = "unknown"
            self._apply_status_style("unknown")
        else:  # "disconnected"
            self.connection_dot.configure(text_color="#EF4444")
            label = f"Lost connection ({port}) — retrying…" if port else "Disconnected — retrying…"
            self.connection_label.configure(text=label)
            self.current_status_key = "unknown"
            self._apply_status_style("unknown")

    def _apply_status_style(self, key):
        style = STATUS_STYLES[key]
        self.status_card.configure(fg_color=style["bg"], border_color=style["border"])
        self.badge_frame.configure(fg_color=style["badge_bg"])
        self.badge_label.configure(text=f"{style['icon']}  STATUS", text_color=style["badge_text"])
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
        self.points_tile.set_value(f"{int(self.points_manager.points)}")

        if self.shop_window is not None and self.shop_window.winfo_exists():
            self.shop_window.refresh()

        if now - self._last_autosave > config.AUTOSAVE_INTERVAL_SECONDS:
            self.points_manager.save_if_dirty()
            self._last_autosave = now

    # ------------------------------------------------------------ Actions --

    def _open_shop(self):
        if self.shop_window is not None and self.shop_window.winfo_exists():
            self.shop_window.focus()
            return
        self.shop_window = ShopWindow(self, self.points_manager, self.serial_manager.send_command)

    def _on_close(self):
        self.points_manager.save_if_dirty(force=True)
        self.serial_manager.stop()
        self.destroy()