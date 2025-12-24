class ThemeEngine:
    # 1. GLOBAL VISUAL IDENTITY (Hard-Coded)
    BG_MAIN = "#0B0E11"       # Deep Obsidian
    BG_SIDEBAR = "#15191E"    # Steel Charcoal
    BG_HOVER = "#1E293B"      # Active/Hover State
    
    ACCENT_PRIMARY = "#4F46E5" # Electric Indigo
    ACCENT_HOVER = "#4338ca"
    
    TEXT_PRIMARY = "#F3F4F6"  # Off-White
    TEXT_MUTED = "#9CA3AF"    # Cool Grey
    
    BORDER_COLOR = "#2D333B"  # Thin Slate
    
    # Fonts
    # Sidebar / UI
    FONT_UI = ("Inter", 14)
    FONT_HEADER = ("Inter", 11, "bold") # Breadcrumbs
    
    # Writing Zen Mode
    FONT_PROSE = ("Georgia", 17)
    
    # Dimensions
    SIDEBAR_WIDTH = 260
    EDITOR_WIDTH = 750
    ASSISTANT_WIDTH = 320
    CORNER_RADIUS = 20
    
    @staticmethod
    def get_prose_font():
        return ThemeEngine.FONT_PROSE

    @staticmethod
    def get_ui_font():
        return ThemeEngine.FONT_UI
