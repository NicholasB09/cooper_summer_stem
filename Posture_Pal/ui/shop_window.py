import customtkinter as ctk
from PIL import Image
import os
import shop_data
import config

class ShopWindow(ctk.CTkToplevel):
    def __init__(self, master, points_manager, send_command_callback):
        super().__init__(master)
        self.title("Posture Points Shop")
        self.geometry("600x500")
        self.minsize(500, 400)
        
        # Bring window to front
        self.lift()
        self.attributes("-topmost", True)
        self.after(10, lambda: self.attributes("-topmost", False))

        self.points_manager = points_manager
        self.send_command_callback = send_command_callback
        
        self.buttons = []
        self._build_ui()

    def _build_ui(self):
        # Header
        self.header = ctk.CTkLabel(self, text="Animation Shop", font=ctk.CTkFont(size=24, weight="bold"))
        self.header.pack(pady=(20, 5))
        
        # Points Display
        self.points_label = ctk.CTkLabel(
            self, 
            text=f"Available Points: {int(self.points_manager.points)}", 
            font=ctk.CTkFont(size=16),
            text_color="#30a46c"
        )
        self.points_label.pack(pady=(0, 20))
        
        # Scrollable Grid Area
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Make a 2-column grid
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        self.scroll_frame.grid_columnconfigure(1, weight=1)
        
        self._populate_grid()

    def _populate_grid(self):
        row, col = 0, 0
        
        for anim in shop_data.ANIMATIONS:
            # Create a card for each animation
            card = ctk.CTkFrame(self.scroll_frame, corner_radius=10, fg_color="#242830")
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            # Load Thumbnail Image (with a fallback if the file is missing)
            try:
                img = Image.open(anim["thumbnail"])
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(120, 120))
                img_label = ctk.CTkLabel(card, image=ctk_img, text="")
                img_label.image = ctk_img  # Prevent garbage collection
            except FileNotFoundError:
                img_label = ctk.CTkLabel(card, text="[Image Missing]", width=120, height=120, fg_color="#1a1d24")
            
            img_label.pack(pady=(15, 10))
            
            # Text info
            ctk.CTkLabel(card, text=anim["name"], font=ctk.CTkFont(size=16, weight="bold")).pack()
            ctk.CTkLabel(card, text=anim["description"], font=ctk.CTkFont(size=12), text_color="#9aa0ac", wraplength=200).pack(pady=(0, 10))
            
            # Buy / Unlocked Button
            btn = ctk.CTkButton(card, text="", command=lambda a=anim: self._buy_animation(a))
            btn.pack(pady=(0, 15))
            
            self.buttons.append((btn, anim))
            
            # Grid math
            col += 1
            if col > 1:
                col = 0
                row += 1
                
        self.refresh() # Set initial button states

    def refresh(self):
        """Updates the points label and button states based on current points."""
        self.points_label.configure(text=f"Available Points: {int(self.points_manager.points)}")
        
        for btn, anim in self.buttons:
            if self.points_manager.is_unlocked(anim["id"]):
                btn.configure(text="Unlocked", state="disabled", fg_color="#30a46c")
            elif self.points_manager.can_afford(anim["cost"]):
                btn.configure(text=f"Buy ({anim['cost']} pts)", state="normal", fg_color=["#3B8ED0", "#1F6AA5"])
            else:
                btn.configure(text=f"Buy ({anim['cost']} pts)", state="disabled", fg_color="#5b616e")

    def _buy_animation(self, anim):
        if self.points_manager.spend(anim["cost"]):
            self.points_manager.unlock(anim["id"])
            # Send the signal to the ESP32!
            self.send_command_callback(f"{config.UNLOCK_PREFIX}:{anim['id']}")
            self.refresh()