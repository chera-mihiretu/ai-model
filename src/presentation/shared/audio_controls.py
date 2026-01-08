from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QComboBox, QFrame,
    QGraphicsDropShadowEffect, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QColor, QFont
from ..theme import QtTheme

class AudioControlWidget(QWidget):
    """
    Glass UI widget for TTS controls:
    [ Read Aloud | Stop ] [ Voice Select ] [ Download MP3 ]
    """
    
    read_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    download_clicked = pyqtSignal()
    voice_changed = pyqtSignal(str)
    
    def __init__(self, voices: list[str], parent=None):
        super().__init__(parent)
        self.voices = voices
        self.is_reading = False
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        self.setFixedHeight(50)
        
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(12)
        
        # Container with glass effect
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(30, 32, 36, 180);
                border: 1px solid {QtTheme.GLASS_BORDER};
                border-radius: 10px;
            }}
        """)
        
        # Inner layout
        inner = QHBoxLayout(container)
        inner.setContentsMargins(12, 6, 12, 6)
        inner.setSpacing(10)
        
        # 1. Read / Stop Button
        self.read_btn = QPushButton("▶ Read Aloud")
        self.read_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.read_btn.setFixedSize(110, 32)
        self.read_btn.clicked.connect(self._toggle_read)
        self._style_button(self.read_btn, accent=True)
        
        # 2. Status Label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {QtTheme.TEXT_MUTED}; font-size: 12px;")
        
        # 3. Voice Selector
        self.voice_combo = QComboBox()
        self.voice_combo.addItems(self.voices)
        self.voice_combo.setFixedWidth(120)
        self.voice_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.voice_combo.currentTextChanged.connect(self.voice_changed.emit)
        
        # Style ComboBox (Glass)
        self.voice_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: rgba(255, 255, 255, 10);
                border: 1px solid rgba(255, 255, 255, 20);
                border-radius: 6px;
                color: {QtTheme.TEXT_PRIMARY};
                padding: 4px 10px;
                font-size: 13px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #1E2024;
                color: {QtTheme.TEXT_PRIMARY};
                selection-background-color: {QtTheme.ACCENT_PRIMARY};
                border: 1px solid {QtTheme.GLASS_BORDER};
            }}
        """)
        
        # 4. Download Button
        self.download_btn = QPushButton("⬇ MP3")
        self.download_btn.setToolTip("Export Chapter as MP3")
        self.download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.download_btn.setFixedSize(80, 32)
        self.download_btn.clicked.connect(self.download_clicked.emit)
        self._style_button(self.download_btn, accent=False)
        
        inner.addWidget(self.read_btn)
        inner.addWidget(self.status_label)
        inner.addStretch()
        inner.addWidget(QLabel("Voice:"))
        inner.addWidget(self.voice_combo)
        inner.addWidget(self.download_btn)
        
        layout.addWidget(container)

    def _style_button(self, btn, accent=False):
        if accent:
            bg = f"rgba(79, 70, 229, 0.2)"
            border = f"rgba(79, 70, 229, 0.4)"
            hover = f"rgba(79, 70, 229, 0.4)"
        else:
            bg = "rgba(255, 255, 255, 0.05)"
            border = "rgba(255, 255, 255, 0.1)"
            hover = "rgba(255, 255, 255, 0.1)"
            
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 6px;
                color: {QtTheme.TEXT_PRIMARY};
                font-weight: 500;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
            QPushButton:pressed {{
                background-color: rgba(0, 0, 0, 0.2);
            }}
        """)

    def _toggle_read(self):
        if self.is_reading:
            # Stop
            self.stop_clicked.emit()
            self.set_reading_state(False)
        else:
            # Start
            self.read_clicked.emit()
            self.set_reading_state(True)
            
    def set_reading_state(self, reading: bool):
        self.is_reading = reading
        if reading:
            self.read_btn.setText("⏹ Stop")
            self.read_btn.setStyleSheet(self.read_btn.styleSheet().replace("rgba(79, 70, 229, 0.2)", "rgba(220, 38, 38, 0.3)")) # Red tint
            self.status_label.setText("Reading...")
        else:
            self.read_btn.setText("▶ Read Aloud")
            # Reset style
            self._style_button(self.read_btn, accent=True)
            self.status_label.setText("")

    def update_voice_list(self, voices: list[str]):
        """Update the list of available voices."""
        current = self.voice_combo.currentText()
        self.voice_combo.blockSignals(True)
        self.voice_combo.clear()
        self.voice_combo.addItems(voices)
        
        # Restore selection if possible
        if current in voices:
            self.voice_combo.setCurrentText(current)
        
        self.voice_combo.blockSignals(False)
        self.voices = voices

