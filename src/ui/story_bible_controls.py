import customtkinter as ctk
from src.ui.theme_engine import ThemeEngine

class StoryBibleControls(ctk.CTkFrame):
    """
    Bottom-left floating control panel for Story Bible.
    Expands vertically to show tabs.
    """
    def __init__(self, master, on_tab_select, on_back_to_writing):
        super().__init__(
            master, 
            fg_color=ThemeEngine.BG_SIDEBAR, 
            corner_radius=10, 
            border_width=1, 
            border_color=ThemeEngine.BORDER_COLOR
        )
        
        self.on_tab_select = on_tab_select
        self.on_back = on_back_to_writing
        self.is_expanded = False
        
        # Layout: Row 0 = Menu (Hidden), Row 1 = Toggle Button
        self.grid_columnconfigure(0, weight=1)
        
        # 1. Menu Container (Hidden state)
        self.menu_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        # Back To Writing (Top? Or Bottom of list?)
        self.btn_back = ctk.CTkButton(
            self.menu_frame, 
            text="⬅ Back to Writing", 
            command=self.go_back,
            fg_color=ThemeEngine.ACCENT_PRIMARY,
            hover_color=ThemeEngine.ACCENT_HOVER,
            anchor="w"
        )
        self.btn_back.pack(fill="x", padx=5, pady=(5, 10))
        
        # Tabs
        self.tabs = ["Braindump", "Genre", "Style", "Synopsis", "Characters", "World", "Outline"]
        for tab in self.tabs:
            btn = ctk.CTkButton(
                self.menu_frame, 
                text=tab, 
                command=lambda t=tab: self.select_tab(t),
                fg_color="transparent",
                text_color=ThemeEngine.TEXT_PRIMARY,
                hover_color=ThemeEngine.BG_HOVER,
                anchor="w",
                height=30
            )
            btn.pack(fill="x", padx=5, pady=2)
            
        # 2. Main Toggle Button (Always visible)
        self.toggle_btn = ctk.CTkButton(
            self, 
            text="📖 Story Bible", 
            command=self.toggle_menu,
            width=160,
            height=40,
            font=("Inter", 13, "bold"),
            fg_color=ThemeEngine.ACCENT_PRIMARY,
            hover_color=ThemeEngine.ACCENT_HOVER
        )
        self.toggle_btn.grid(row=1, column=0, padx=10, pady=10)
        
    def toggle_menu(self):
        if self.is_expanded:
            self.menu_frame.grid_forget()
        else:
            self.menu_frame.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")
        self.is_expanded = not self.is_expanded
        
    def select_tab(self, tab_name):
        """User clicked a bible section."""
        self.on_tab_select(tab_name)
        # We keep the menu open to allow rapid switching
        
    def go_back(self):
        """User wants to return to editor."""
        self.on_back()
        # Optionally collapse menu?
        self.toggle_menu()
