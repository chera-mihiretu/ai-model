import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QColor, QPainter

from ..theme import QtTheme

class GlassInputDialog(QDialog):
    """
    Premium glass-styled modal dialog for inputs.
    Features:
    - Translucent background with blur/tint
    - Smooth fade-in animation
    - Premium typography and spacing
    """
    def __init__(self, title, label_text, placeholder="", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setFixedWidth(450)
        
        self._setup_ui(title, label_text, placeholder)
        
        # Animation
        self._opacity = 0.0
        self._opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        
    def _setup_ui(self, title, label_text, placeholder):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Main Container
        self.container = QFrame()
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(30, 32, 38, 245);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 20px;
            }}
        """)
        
        # Shadow for depth
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 120))
        self.container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(25, 25, 25, 25)
        container_layout.setSpacing(20)
        
        # Header (Title)
        header_label = QLabel(title)
        header_label.setFont(QtTheme.get_font_h2())
        header_label.setStyleSheet(f"color: {QtTheme.TEXT_PRIMARY}; font-weight: bold;")
        container_layout.addWidget(header_label)
        
        # Input Section
        input_layout = QVBoxLayout()
        input_layout.setSpacing(8)
        
        field_label = QLabel(label_text)
        field_label.setFont(QtTheme.get_font_ui())
        field_label.setStyleSheet(f"color: {QtTheme.TEXT_MUTED};")
        input_layout.addWidget(field_label)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(placeholder)
        self.input_field.setFont(QtTheme.get_font_ui())
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: rgba(255, 255, 255, 10);
                border: 1px solid rgba(255, 255, 255, 20);
                border-radius: 10px;
                padding: 12px 15px;
                color: {QtTheme.TEXT_PRIMARY};
                font-size: 15px;
            }}
            QLineEdit:focus {{
                border: 1px solid {QtTheme.ACCENT_PRIMARY};
                background-color: rgba(79, 70, 229, 20);
            }}
        """)
        self.input_field.returnPressed.connect(self.accept)
        input_layout.addWidget(self.input_field)
        
        container_layout.addLayout(input_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedSize(100, 40)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid rgba(255, 255, 255, 20);
                border-radius: 8px;
                color: {QtTheme.TEXT_MUTED};
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 10);
                color: {QtTheme.TEXT_PRIMARY};
            }}
        """)
        self.cancel_btn.clicked.connect(self.reject)
        
        self.confirm_btn = QPushButton("Create Project")
        self.confirm_btn.setFixedSize(130, 40)
        self.confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {QtTheme.ACCENT_PRIMARY};
                border: none;
                border-radius: 8px;
                color: white;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {QtTheme.ACCENT_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {QtTheme.ACCENT_PRIMARY};
            }}
        """)
        self.confirm_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.confirm_btn)
        
        container_layout.addLayout(button_layout)
        layout.addWidget(self.container)
        
    def exec(self):
        """Show dialog with animation."""
        self.setWindowOpacity(0.0)
        self.show()
        
        self._opacity_anim.stop()
        self._opacity_anim.setDuration(300)
        self._opacity_anim.setStartValue(0.0)
        self._opacity_anim.setEndValue(1.0)
        self._opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._opacity_anim.start()
        
        self.input_field.setFocus()
        return super().exec()

    @staticmethod
    def get_text(parent, title, label, placeholder=""):
        dialog = GlassInputDialog(title, label, placeholder, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.input_field.text(), True
        return "", False
