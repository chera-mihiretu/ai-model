class ThemeEngine:
    # 1. GLOBAL VISUAL IDENTITY (Hard-Coded)
    BG_MAIN = "#0B0E11"       # Deep Obsidian
    BG_SIDEBAR = "#15191E"    # Steel Charcoal
    BG_HOVER = "#1E293B"      # Active/Hover State
    BG_INPUT = "#0F1216"      # Input Background (Slightly lighter than Main)
    
    ACCENT_PRIMARY = "#4F46E5" # Electric Indigo
    ACCENT_HOVER = "#4338ca"
    ACCENT_SECONDARY = "#8B5CF6" # Violet
    
    TEXT_PRIMARY = "#F3F4F6"  # Off-White
    TEXT_MUTED = "#9CA3AF"    # Cool Grey
    
    BORDER_COLOR = "#2D333B"  # Thin Slate
    
    # Fonts
    # Sidebar / UI
    FONT_UI = ("Inter", 14)
    FONT_HEADER = ("Inter", 11, "bold") # Breadcrumbs
    FONT_H3 = ("Inter", 13, "bold") # Sub-headers
    
    # Writing Zen Mode
    FONT_PROSE = ("Georgia", 17)
    
    # Dimensions
    SIDEBAR_WIDTH = 260
    EDITOR_WIDTH = 750
    ASSISTANT_WIDTH = 320
    CORNER_RADIUS = 20
    
    # Sudowrite-style Layout
    TOOLBAR_HEIGHT = 60
    LEFT_PANEL_PCT = 0.18   # 18% of window width
    CENTER_PANEL_PCT = 0.60 # 60% of window width
    RIGHT_PANEL_PCT = 0.22  # 22% of window width
    
    # Story Bible Cards
    CARD_BG = "#1A1F2E"           # Light background for cards
    CARD_CORNER_RADIUS = 12
    CARD_PADDING = 20
    CARD_SPACING = 15             # Space between cards
    
    # Gradients
    GRADIENT_START = "#4F46E5"
    GRADIENT_END = "#8B5CF6"
    
    @staticmethod
    def get_prose_font():
        return ThemeEngine.FONT_PROSE

    @staticmethod
    def get_ui_font():
        return ThemeEngine.FONT_UI
