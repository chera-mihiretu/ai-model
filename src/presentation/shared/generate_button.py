from PyQt6.QtWidgets import QPushButton, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, pyqtProperty, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor
from ..theme import QtTheme

class GenerateButton(QPushButton):
    """
    Premium glass-style generate button for Story Bible tabs.
    Features subtle hover animations and loading states.
    """
    def __init__(self, parent=None):
        super().__init__("✨", parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedWidth(100)
        self.setFixedHeight(28)
        
        # Base styles
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid {QtTheme.GLASS_BORDER};
                border-radius: 6px;
                color: {QtTheme.TEXT_SECONDARY};
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }}
            QPushButton:hover {{
                background-color: rgba(79, 70, 229, 0.1);
                border: 1px solid rgba(79, 70, 229, 0.4);
                color: {QtTheme.TEXT_PRIMARY};
            }}
            QPushButton:disabled {{
                background-color: rgba(255, 255, 255, 0.02);
                color: {QtTheme.TEXT_MUTED};
                border: 1px solid rgba(255, 255, 255, 0.05);
            }}
        """)
        
        # Shadow effect for subtle depth
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(8)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(2)
        self.shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(self.shadow)
        
        self.setToolTip("Generate content directly using AI context")

    def set_loading(self, loading: bool):
        """Toggle loading state."""
        if loading:
            self.setEnabled(False)
            self.setText("Generating...")
            self.setToolTip("AI is thinking...")
        else:
            self.setEnabled(True)
            self.setText("✨")
            self.setToolTip("Generate content directly using AI context")
