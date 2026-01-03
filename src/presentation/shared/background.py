"""
Background Widget - Root widget that renders background image
"""
import logging
from pathlib import Path

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPainter, QColor


class BackgroundWidget(QWidget):
    """
    Root widget that renders background image ONCE.
    All other UI elements float above with FULL TRANSPARENCY.
    This is the ONLY widget that paints - all children are transparent.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.background_pixmap = None
        self.load_background()
        
        # DO NOT set auto-fill - we paint manually
        self.setAutoFillBackground(False)
        
        # Enable transparency for children
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)  # Root paints
    
    def load_background(self):
        """Load background image if it exists."""
        try:
            # Look for background image in assets folder
            current_dir = Path(__file__).parent.parent.parent.parent  # Go up to project root
            bg_path = current_dir / "assets" / "images" / "backgroundimg.png"
            
            # Fallback to old location
            if not bg_path.exists():
                bg_path = current_dir / "src" / "ui" / "assets" / "backgroundimg.png"
            
            if bg_path.exists():
                self.background_pixmap = QPixmap(str(bg_path))
                logging.info(f"Background image loaded: {bg_path}")
            else:
                logging.warning(f"Background image not found: {bg_path}")
        except Exception as e:
            logging.error(f"Failed to load background image: {e}")
    
    def paintEvent(self, event):
        """
        Paint the background image ONCE at root level.
        This is the ONLY paint event in the entire UI hierarchy.
        """
        painter = QPainter(self)
        
        if self.background_pixmap:
            # Scale to fill while maintaining aspect ratio
            scaled_pixmap = self.background_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Center the pixmap
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            
            painter.drawPixmap(x, y, scaled_pixmap)
        else:
            # Fallback: dark background if no image
            painter.fillRect(self.rect(), QColor("#0B0E11"))


