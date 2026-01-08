import customtkinter as ctk
from src.ui.theme_engine import ThemeEngine

class StoryBibleDrawer(ctk.CTkFrame):
    """
    Slim left-side drawer containing Story Bible tab navigation.
    Slides vertically from bottom-left to middle-left.
    """
    def __init__(self, master, on_tab_select):
        super().__init__(master, width=200, corner_radius=0, fg_color=ThemeEngine.BG_SIDEBAR)
        self.on_tab_select = on_tab_select
        self.grid_propagate(False)
        
        # Header
        ctk.CTkLabel(
            self, 
            text="📖 STORY BIBLE",
            font=ThemeEngine.FONT_H3,
            text_color=ThemeEngine.TEXT_PRIMARY
        ).pack(pady=(20, 10))
        
        # 7 Bible Tabs
        self.tabs = [
            "Braindump",
            "Genre", 
            "Style",
            "Synopsis",
            "Characters",
            "World Building",
            "Outline"
        ]
        
        self.tab_buttons = {}
        
        for tab_name in self.tabs:
            btn = ctk.CTkButton(
                self,
                text=tab_name,
                fg_color="transparent",
                text_color=ThemeEngine.TEXT_MUTED,
                anchor="w",
                height=36,
                hover_color=ThemeEngine.BG_HOVER,
                command=lambda t=tab_name: self.select_tab(t)
            )
            btn.pack(fill="x", padx=10, pady=3)
            self.tab_buttons[tab_name] = btn
    
    def select_tab(self, tab_name):
        """Update visual state and trigger callback."""
        # Update button states
        for name, btn in self.tab_buttons.items():
            if name == tab_name:
                btn.configure(fg_color=ThemeEngine.BG_HOVER, text_color=ThemeEngine.ACCENT_PRIMARY)
            else:
                btn.configure(fg_color="transparent", text_color=ThemeEngine.TEXT_MUTED)
        
        # Notify main window
        if self.on_tab_select:
            self.on_tab_select(tab_name)
