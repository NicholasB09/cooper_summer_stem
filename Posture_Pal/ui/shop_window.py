"""Shop window for unlocking OLED animations using Posture Points."""

import customtkinter as ctk

import config
from shop_data import ANIMATIONS

BG_COLOR = "#0F172A"
CARD_BG = "#1E293B"
CARD_BORDER = "#334155"
TEXT_PRIMARY = "#F8FAFC"
TEXT_SECONDARY = "#94A3B8"


class ShopWindow(ctk.CTkToplevel):
    def __init__(self, master, points_manager, send_command_cb):
        super().__init__(master)
        self.title("Posture Pal — Reward Shop")
        self.geometry("460x580")
        self.resizable(False, False)
        self.configure(fg_color=BG_COLOR)

        self.points_manager = points_manager
        self.send_command = send_command_cb
        self._item_buttons = {}

        # Keep window on top
        self.attributes("-topmost", True)

        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(24, 12))

        ctk.CTkLabel(
            header,
            text="Animation Shop",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=TEXT_PRIMARY
        ).pack(side="left")

        # Balance Indicator
        self.balance_badge = ctk.CTkFrame(
            header,
            corner_radius=12,
            fg_color=CARD_BG,
            border_width=1,
            border_color=CARD_BORDER
        )
        self.balance_badge.pack(side="right")

        self.balance_label = ctk.CTkLabel(
            self.balance_badge,
            text="",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#38BDF8"
        )
        self.balance_label.pack(padx=12, pady=6)

        # Scrollable items container
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # Build item cards once
        for item in ANIMATIONS:
            self._render_item_card(item)

        # Initial state update
        self.refresh()

    def _render_item_card(self, item):
        anim_id = item["id"]

        card = ctk.CTkFrame(
            self.scroll_frame,
            corner_radius=14,
            fg_color=CARD_BG,
            border_width=1,
            border_color=CARD_BORDER
        )
        card.pack(fill="x", pady=6, padx=8)

        # Title & Info
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=14, pady=12)

        ctk.CTkLabel(
            info_frame,
            text=item["name"],
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            info_frame,
            text=item["description"],
            font=ctk.CTkFont(size=11),
            text_color=TEXT_SECONDARY,
            wraplength=220,
            justify="left"
        ).pack(anchor="w", pady=(2, 0))

        # Action Button Container
        action_frame = ctk.CTkFrame(card, fg_color="transparent")
        action_frame.pack(side="right", padx=14, pady=12)

        btn = ctk.CTkButton(
            action_frame,
            text="",
            width=90,
            height=34,
            corner_radius=10,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        btn.pack()

        # Save button reference for lightweight updates
        self._item_buttons[anim_id] = btn

    def refresh(self):
        """Smoothly update balance label and button states without destroying widgets."""
        points = int(self.points_manager.points)
        self.balance_label.configure(text=f"💎 {points} Points")

        for item in ANIMATIONS:
            anim_id = item["id"]
            if anim_id not in self._item_buttons:
                continue

            btn = self._item_buttons[anim_id]
            cost = item["cost"]
            unlocked = self.points_manager.is_unlocked(anim_id)
            can_afford = self.points_manager.can_afford(cost)

            if unlocked:
                btn.configure(
                    text="Display ✨",
                    fg_color="#059669",
                    hover_color="#047857",
                    state="normal",
                    command=lambda a=anim_id: self._trigger_animation(a)
                )
            else:
                btn.configure(
                    text=f"💎 {cost}",
                    fg_color="#0284C7" if can_afford else "#334155",
                    hover_color="#0369A1" if can_afford else "#334155",
                    state="normal" if can_afford else "disabled",
                    command=lambda i=item: self._buy_animation(i)
                )

    def _buy_animation(self, item):
        if self.points_manager.spend(item["cost"]):
            self.points_manager.unlock(item["id"])
            self._trigger_animation(item["id"])
            self.refresh()

    def _trigger_animation(self, anim_id):
        cmd = f"{config.UNLOCK_PREFIX}:{anim_id}"
        self.send_command(cmd)
        print(cmd)