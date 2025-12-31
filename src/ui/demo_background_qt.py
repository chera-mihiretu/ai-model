
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFrame, QComboBox)
from PyQt6.QtCore import Qt
from animated_background import AnimatedBackground

class DemoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Animated Background Demo")
        self.resize(1000, 700)

        # Main Container
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Use a stack-like layout to put content ON TOP of background
        # Since QLayouts don't support Z-ordering easily, we'll use a parent/child relationship
        # where the background is the parent, or we just put the background behind via absolute positioning.
        # EASIEST WAY: Make AnimatedBackground the central widget's base, and put a layout inside it? 
        # But AnimatedBackground paints itself. So yes.
        
        # Actually, let's make a container that holds the background and controls separately
        # to show it can fill a specific area.
        
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Top Controls
        self.controls_layout = QHBoxLayout()
        self.main_layout.addLayout(self.controls_layout)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "Custom Blue", "Custom Purple"])
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        
        self.controls_layout.addWidget(QLabel("Select Theme:"))
        self.controls_layout.addWidget(self.theme_combo)
        self.controls_layout.addStretch()
        
        # Content Area - We want the background to be behind this area.
        # We'll create a container QWidget that IS the animated background
        self.content_area = AnimatedBackground(theme="Dark")
        self.content_area.setSizePolicy(
            self.content_area.sizePolicy().Policy.Expanding,
            self.content_area.sizePolicy().Policy.Expanding
        )
        
        self.main_layout.addWidget(self.content_area, stretch=1)
        
        # Add some "fake" content inside the animated background to show transparency/layering
        # We need a layout INSIDE the AnimatedBackground for this.
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(50, 50, 50, 50)
        
        # Example Card 1
        self.card1 = QFrame()
        self.card1.setStyleSheet("background-color: rgba(255, 255, 255, 30); border-radius: 15px; border: 1px solid rgba(255,255,255,50);")
        self.card1.setMinimumHeight(200)
        
        l1 = QLabel("Story Bible - Characters", self.card1)
        l1.setStyleSheet("color: white; font-size: 24px; font-weight: bold; background: transparent;")
        l1.move(20, 20)
        
        l2 = QLabel("This content floats above the pulsating background.", self.card1)
        l2.setStyleSheet("color: #ddd; font-size: 14px; background: transparent;")
        l2.move(20, 60)
        
        self.content_layout.addWidget(self.card1)
        self.content_layout.addStretch()
        
    def change_theme(self, text):
        if text == "Custom Blue":
            # Glow color, Particle color
            self.content_area.set_custom_colors("#0088ff", "#00ffff")
            self._update_text_color("white")
        elif text == "Custom Purple":
            self.content_area.set_custom_colors("#aa00ff", "#ff00ff")
            self._update_text_color("white")
        elif text == "Light":
            self.content_area.set_theme("Light")
            self._update_text_color("black")
            self.card1.setStyleSheet("background-color: rgba(255, 255, 255, 150); border-radius: 15px; border: 1px solid rgba(0,0,0,20);")
        else:
            self.content_area.set_theme("Dark")
            self._update_text_color("white")
            self.card1.setStyleSheet("background-color: rgba(255, 255, 255, 30); border-radius: 15px; border: 1px solid rgba(255,255,255,50);")

    def _update_text_color(self, color):
        for child in self.card1.children():
            if isinstance(child, QLabel):
                current_style = child.styleSheet()
                # Simple hack replace
                if "color: white" in current_style:
                    child.setStyleSheet(current_style.replace("color: white", f"color: {color}"))
                elif "color: black" in current_style:
                    child.setStyleSheet(current_style.replace("color: black", f"color: {color}"))
                elif "color: #ddd" in current_style: # description
                     child.setStyleSheet(current_style.replace("color: #ddd", f"color: {'#333' if color == 'black' else '#ddd'}"))
                elif "color: #333" in current_style:
                     child.setStyleSheet(current_style.replace("color: #333", f"color: {'#333' if color == 'black' else '#ddd'}"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DemoWindow()
    window.show()
    sys.exit(app.exec())
