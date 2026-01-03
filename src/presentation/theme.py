"""
PyQt6 Theme Engine
Defines colors, fonts, and styling constants for the application.
Provides Qt StyleSheet generation for consistent theming.
"""

from PyQt6.QtGui import QFont, QColor, QPalette
from PyQt6.QtCore import Qt


class QtTheme:
    """Central theme configuration for PyQt6 application."""
    
    # ============================================================================
    # COLOR PALETTE (DARKENED BLACK GLASS OVERLAY - +40% OPACITY)
    # ============================================================================
    
    # =========================
    # DARKER BLACK GLASS THEME
    # =========================

    # Background Colors - DARKER BLACK GLASS for enhanced readability
    BG_MAIN = "rgba(0, 0, 0, 200)"              # 78% black (was 60%) - readable base
    BG_SIDEBAR = "rgba(0, 0, 0, 220)"           # 86% black (was 70%) - darker panels
    BG_HOVER = "rgba(0, 0, 0, 240)"             # 94% black (was 85%) - strong feedback
    BG_INPUT = "rgba(0, 0, 0, 200)"             # 78% black (was 65%) - input contrast
    CARD_BG = "rgba(0, 0, 0, 180)"              # 71% black (was 55%) - floating cards

    # Glass effect overlays
    GLASS_LIGHT = "rgba(255, 255, 255, 0.03)"   # Slightly dimmer subtle highlight
    GLASS_BORDER = "rgba(255, 255, 255, 0.10)"  # Slightly dimmer border glow
    GLASS_SHADOW = "rgba(0, 0, 0, 0.55)"        # Deeper shadow for depth

    # Panel overlays (darkened for containers)
    OVERLAY_LIGHT = "rgba(0, 0, 0, 180)"        # 71% black
    OVERLAY_MEDIUM = "rgba(0, 0, 0, 200)"       # 78% black
    OVERLAY_DARK = "rgba(0, 0, 0, 220)"         # 86% black

    # Accent Colors
    ACCENT_PRIMARY = "#4F46E5"   # Electric Indigo
    ACCENT_HOVER = "#4338ca"
    ACCENT_SECONDARY = "#8B5CF6"  # Violet

    # Text Colors
    TEXT_PRIMARY = "#F3F4F6"   # Off-White
    TEXT_SECONDARY = "#D1D5DB" # Light Grey
    TEXT_MUTED = "#9CA3AF"     # Cool Grey

    # Border & Divider Colors
    BORDER_COLOR = "#2D333B"   # Thin Slate

    # Gradients
    GRADIENT_START = "#4F46E5"
    GRADIENT_END = "#8B5CF6"

    # =========================
    # DIMENSIONS
    # =========================

    TOOLBAR_HEIGHT = 60
    SIDEBAR_WIDTH = 280
    EDITOR_WIDTH = 750
    ASSISTANT_WIDTH = 360

    CORNER_RADIUS = 12
    CARD_CORNER_RADIUS = 12
    CARD_PADDING = 20
    CARD_SPACING = 15

    # Layout proportions
    LEFT_PANEL_PCT = 0.18    # 18% of window width
    CENTER_PANEL_PCT = 0.60  # 60% of window width
    RIGHT_PANEL_PCT = 0.22   # 22% of window width

    
    # ============================================================================
    # FONTS
    # ============================================================================
    
    @staticmethod
    def get_font_ui() -> QFont:
        """Standard UI font."""
        font = QFont("Inter")
        font.setPixelSize(14)
        return font
    
    @staticmethod
    def get_font_content() -> QFont:
        """Standard content font."""
        font = QFont("Inter")
        font.setPixelSize(13)
        return font
    
    @staticmethod
    def get_font_header() -> QFont:
        """Header/breadcrumb font."""
        font = QFont("Inter")
        font.setPixelSize(11)
        font.setBold(True)
        return font
    
    @staticmethod
    def get_font_h3() -> QFont:
        """Sub-header font."""
        font = QFont("Inter")
        font.setPixelSize(13)
        font.setBold(True)
        return font
    
    @staticmethod
    def get_font_prose() -> QFont:
        """Writing/editor font."""
        font = QFont("Georgia")
        font.setPixelSize(17)
        return font
    
    @staticmethod
    def get_font_title() -> QFont:
        """Large title font."""
        font = QFont("Inter")
        font.setPixelSize(24)
        font.setBold(True)
        return font
    
    # ============================================================================
    # STYLESHEET GENERATION
    # ============================================================================
    
    @staticmethod
    def get_global_stylesheet() -> str:
        """
        Returns global Qt stylesheet for FULLY TRANSPARENT glass UI.
        All widgets are transparent by default, showing background image.
        """
        return f"""
            * {{
                color: {QtTheme.TEXT_PRIMARY};
                font-family: "Inter";
                font-size: 14px;
            }}
            
            QWidget {{
                background-color: transparent;
                border: none;
            }}
            
            QMainWindow {{
                background-color: transparent;
            }}
            
            /* Transparent widgets (default) */
            .TransparentWidget {{
                background-color: transparent;
            }}
            
            /* Glass sidebar - subtle translucent */
            .SidebarWidget {{
                background-color: {QtTheme.BG_SIDEBAR};
                border-right: 1px solid {QtTheme.GLASS_BORDER};
            }}
            
            /* Glass card - floating translucent */
            .CardWidget {{
                background-color: {QtTheme.CARD_BG};
                border: 1px solid {QtTheme.GLASS_BORDER};
                border-radius: {QtTheme.CARD_CORNER_RADIUS}px;
            }}
            
            /* Buttons - transparent with glow on hover */
            QPushButton {{
                background-color: {QtTheme.ACCENT_PRIMARY};
                color: {QtTheme.TEXT_PRIMARY};
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: {QtTheme.ACCENT_HOVER};
                border: 1px solid {QtTheme.GLASS_LIGHT};
            }}
            
            QPushButton:pressed {{
                background-color: {QtTheme.ACCENT_SECONDARY};
            }}
            
            QPushButton:disabled {{
                background-color: {QtTheme.BG_HOVER};
                color: {QtTheme.TEXT_MUTED};
            }}
            
            /* Transparent buttons with glass effect */
            QPushButton.TransparentButton {{
                background-color: transparent;
                border: 1px solid {QtTheme.GLASS_BORDER};
                color: {QtTheme.TEXT_MUTED};
            }}
            
            QPushButton.TransparentButton:hover {{
                background-color: {QtTheme.BG_HOVER};
                color: {QtTheme.TEXT_PRIMARY};
                border: 1px solid {QtTheme.GLASS_LIGHT};
            }}
            
            /* Input fields - glass translucent */
            QLineEdit {{
                background-color: {QtTheme.BG_INPUT};
                border: 1px solid {QtTheme.GLASS_BORDER};
                border-radius: 8px;
                padding: 8px 12px;
                color: {QtTheme.TEXT_PRIMARY};
            }}
            
            QLineEdit:focus {{
                border: 1px solid {QtTheme.ACCENT_PRIMARY};
                background-color: rgba(15, 18, 22, 0.40);
            }}
            
            /* Text editors - FULLY TRANSPARENT */
            QTextEdit, QPlainTextEdit {{
                background-color: transparent;
                border: none;
                color: {QtTheme.TEXT_PRIMARY};
                padding: 10px;
                selection-background-color: {QtTheme.ACCENT_PRIMARY};
                selection-color: {QtTheme.TEXT_PRIMARY};
            }}
            
            QTextEdit:focus, QPlainTextEdit:focus {{
                border: none;
                outline: none;
                background-color: transparent;
            }}
            
            /* Scrollbars - minimal glass */
            QScrollBar:vertical {{
                background-color: transparent;
                width: 10px;
                margin: 0px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {QtTheme.GLASS_BORDER};
                border-radius: 5px;
                min-height: 20px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {QtTheme.ACCENT_PRIMARY};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
            
            QScrollBar:horizontal {{
                background-color: transparent;
                height: 10px;
                margin: 0px;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {QtTheme.GLASS_BORDER};
                border-radius: 5px;
                min-width: 20px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background-color: {QtTheme.ACCENT_PRIMARY};
            }}
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
            
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: transparent;
            }}
            
            /* Labels - transparent */
            QLabel {{
                background-color: transparent;
                color: {QtTheme.TEXT_PRIMARY};
            }}
            
            QLabel.MutedText {{
                color: {QtTheme.TEXT_MUTED};
            }}
            
            /* Menu - glass translucent */
            QMenu {{
                background-color: {QtTheme.BG_SIDEBAR};
                border: 1px solid {QtTheme.GLASS_BORDER};
                padding: 5px;
                border-radius: 8px;
            }}
            
            QMenu::item {{
                padding: 8px 20px;
                border-radius: 4px;
                background-color: transparent;
            }}
            
            QMenu::item:selected {{
                background-color: {QtTheme.BG_HOVER};
                color: {QtTheme.ACCENT_PRIMARY};
            }}
            
            QMenu::separator {{
                height: 1px;
                background-color: {QtTheme.GLASS_BORDER};
                margin: 5px 0px;
            }}
            
            /* Tooltips - glass */
            QToolTip {{
                background-color: {QtTheme.BG_SIDEBAR};
                border: 1px solid {QtTheme.GLASS_BORDER};
                color: {QtTheme.TEXT_PRIMARY};
                padding: 5px;
                border-radius: 4px;
            }}
            
            /* Tab widget - transparent */
            QTabWidget::pane {{
                border: none;
                background-color: transparent;
            }}
            
            QTabBar::tab {{
                background-color: {QtTheme.BG_SIDEBAR};
                color: {QtTheme.TEXT_MUTED};
                padding: 10px 20px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 2px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {QtTheme.BG_HOVER};
                color: {QtTheme.ACCENT_PRIMARY};
                border: 1px solid {QtTheme.GLASS_BORDER};
            }}
            
            QTabBar::tab:hover {{
                background-color: {QtTheme.BG_HOVER};
            }}
            
            /* Scroll areas - transparent */
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            
            /* Frames - transparent */
            QFrame {{
                background-color: transparent;
                border: none;
            }}
        """
    
    @staticmethod
    def create_dark_palette() -> QPalette:
        """
        Creates a custom dark palette for the application.
        This ensures native Qt widgets respect the dark theme.
        """
        palette = QPalette()
        
        # Window colors
        palette.setColor(QPalette.ColorRole.Window, QColor(QtTheme.BG_MAIN))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(QtTheme.TEXT_PRIMARY))
        
        # Base colors (input fields)
        palette.setColor(QPalette.ColorRole.Base, QColor(QtTheme.BG_INPUT))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(QtTheme.BG_SIDEBAR))
        palette.setColor(QPalette.ColorRole.Text, QColor(QtTheme.TEXT_PRIMARY))
        
        # Button colors
        palette.setColor(QPalette.ColorRole.Button, QColor(QtTheme.ACCENT_PRIMARY))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(QtTheme.TEXT_PRIMARY))
        
        # Highlight colors
        palette.setColor(QPalette.ColorRole.Highlight, QColor(QtTheme.ACCENT_PRIMARY))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(QtTheme.TEXT_PRIMARY))
        
        # Disabled colors
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, 
                        QColor(QtTheme.TEXT_MUTED))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, 
                        QColor(QtTheme.TEXT_MUTED))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, 
                        QColor(QtTheme.TEXT_MUTED))
        
        return palette


    # ============================================================================
    # TRANSPARENCY HELPERS
    # ============================================================================
    
    @staticmethod
    def make_transparent(widget):
        """
        Apply full transparency to a widget (strict glass UI requirement).
        This ensures the background image is visible through the widget.
        """
        widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        widget.setAutoFillBackground(False)
        widget.setStyleSheet("background: transparent;")
    
    @staticmethod
    def apply_glass_effect(widget, opacity=0.25, border=True):
        """
        Apply glass/frosted effect with BLACK OVERLAY for readability.
        
        Args:
            widget: QWidget to apply effect to
            opacity: Black overlay opacity (0.0-1.0), default 0.25 (25%)
            border: Whether to add glass border glow
        """
        widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        widget.setAutoFillBackground(False)
        
        # Convert opacity to 0-255 range for RGBA alpha
        alpha = int(opacity * 255)
        
        border_style = f"border: 1px solid {QtTheme.GLASS_BORDER};" if border else ""
        widget.setStyleSheet(f"""
            background-color: rgba(0, 0, 0, {alpha});
            {border_style}
            border-radius: 8px;
        """)
    
    @staticmethod
    def apply_dark_overlay(widget, opacity=0.20):
        """
        Apply subtle black overlay for readability while keeping transparency.
        
        Args:
            widget: QWidget to apply overlay to
            opacity: Black overlay opacity (0.0-1.0), default 0.20 (20%)
        """
        widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        widget.setAutoFillBackground(False)
        
        # Convert opacity to 0-255 range
        alpha = int(opacity * 255)
        
        widget.setStyleSheet(f"background-color: rgba(0, 0, 0, {alpha});")

