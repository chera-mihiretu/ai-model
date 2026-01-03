
import os
import math
import random
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, Qt, QPoint, QRect
from PyQt6.QtGui import QPainter, QColor, QPixmap, QImage

class AnimatedBackground(QWidget):
    """
    A QWidget that renders a "Living Lava" Background.
    Features:
    - Dead Static Black Rock (Strictly aligned).
    - Living, Irregular Lava Glow (Fast Rise, Slow Decay).
    - Brightness Noise (Flicker) instead of Geometry Jitter.
    - White-Hot Core Bloom.
    """

    # Theme Presets
    THEMES = {
        "Dark": {
            # Deep Magma Edge: Deep Red-Orange
            "glow_edge": QColor(255, 40, 0),    
            # White Hot Core: Bright Orange-White
            "glow_core": QColor(255, 200, 150), 
        },
        "Light": {
            "glow_edge": QColor(255, 140, 0),   # Gold
            "glow_core": QColor(255, 255, 200), # White-Gold
        },
        "Custom": {
            "glow_edge": QColor(0, 0, 255),
            "glow_core": QColor(200, 200, 255),
        }
    }

    def __init__(self, parent=None, theme="Dark"):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAutoFillBackground(False)

        # Assets
        self.rock_texture = QPixmap()
        self.crack_mask = QImage()
        
        # Caches
        self.cache_edge = QPixmap() 
        self.cache_core = QPixmap()
        
        # Paths
        base_path = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(base_path, "assets")
        rock_path = os.path.join(assets_dir, "rock_base.jpg")
        mask_path = os.path.join(assets_dir, "lava_cracks.png")
        
        # Load
        if os.path.exists(rock_path):
            self.rock_texture.load(rock_path)
        if os.path.exists(mask_path):
            if self.crack_mask.load(mask_path):
                self.crack_mask = self.crack_mask.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)

        # Animation State
        self.time = 0.0
        self.pressure = 0.8 # Static "Active" state
        self.cycle_duration = 3.0 
        self.cycle_timer = 0.0
        self.flicker = 1.0 

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_animation)
        self.timer.start(30) # Animation enabled for "glowing dents" effect

        # Theme
        self.current_theme = theme
        self.colors = self.THEMES.get(theme, self.THEMES["Dark"]).copy()
        
        # Init Caches
        self._update_caches()

    def set_theme(self, theme_name):
        if theme_name in self.THEMES:
            self.current_theme = theme_name
            self.colors = self.THEMES[theme_name].copy()
            self._update_caches()
            self.update()

    def set_custom_colors(self, glow_color, particle_color=None):
        self.current_theme = "Custom"
        edge = QColor(glow_color)
        core = QColor(glow_color).lighter(180)
        self.colors = {"glow_edge": edge, "glow_core": core}
        self._update_caches()
        self.update()
        
    def _update_caches(self):
        """Pre-generate Edge and Core glow layers."""
        if self.crack_mask.isNull(): return
        w, h = self.crack_mask.width(), self.crack_mask.height()
        
        # --- Edge Layer ---
        img_edge = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
        img_edge.fill(Qt.GlobalColor.transparent)
        p = QPainter(img_edge)
        p.fillRect(0, 0, w, h, self.colors["glow_edge"])
        p.drawImage(0, 0, self.crack_mask) # Mask
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Multiply) 
        p.fillRect(0, 0, w, h, self.colors["glow_edge"]) # Tint
        p.end()
        self.cache_edge = QPixmap.fromImage(img_edge)
        
        # --- Core Layer ---
        img_core = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
        img_core.fill(Qt.GlobalColor.transparent)
        p = QPainter(img_core)
        p.fillRect(0, 0, w, h, self.colors["glow_core"])
        p.drawImage(0, 0, self.crack_mask) 
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Multiply) 
        p.fillRect(0, 0, w, h, self.colors["glow_core"]) 
        p.end()
        self.cache_core = QPixmap.fromImage(img_core)

    def _update_animation(self):
        dt = 0.033
        self.time += dt
        self.cycle_timer += dt
        
        # --- 1. Irregular Pressure Curve (Fast Rise, Slow Decay) ---
        if self.cycle_timer > self.cycle_duration:
            self.cycle_duration = random.uniform(2.5, 4.0)
            self.cycle_timer = 0.0
        
        progress = self.cycle_timer / self.cycle_duration
        
        if progress < 0.2:
            t = progress / 0.2
            self.pressure = 1.0 - math.pow(1.0 - t, 3.0) 
        else:
            t = (progress - 0.2) / 0.8
            self.pressure = math.pow((1.0 - t), 1.5) 
            
        surge = (math.sin(self.time * 0.5) + 1.0) * 0.1
        self.pressure = max(0.1, min(1.0, self.pressure + surge))
        
        # --- 2. Brightness Noise (Flicker) ---
        if self.pressure > 0.5:
             # High pressure = High turbulence
             self.flicker = random.uniform(0.95, 1.05)
        else:
             self.flicker = 1.0

        self.update() 

    def paintEvent(self, event):
        painter = QPainter()
        if not painter.begin(self): return

        try:
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            rect = self.rect()

            # 1. Base Layer: Rock Texture (STATIC BLACK)
            painter.fillRect(rect, Qt.GlobalColor.black)
            if not self.rock_texture.isNull():
                painter.drawPixmap(rect, self.rock_texture)
                # CRUSH IT (90% Overlay)
                painter.setBrush(QColor(0, 0, 0, 230)) 
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRect(rect)
            else:
                painter.fillRect(rect, Qt.GlobalColor.black)

            if self.cache_edge.isNull(): return

            # 2. Glow Rendering (Strictly Inside Cracks, No Jitter)
            # Use `rect` (0,0) for perfect alignment with Rock
            
            # --- Edge Layer (Deep Base) ---
            # Pressure + Flicker
            base_opacity = (0.3 + (0.5 * self.pressure)) * self.flicker
            
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Screen)
            painter.setOpacity(min(base_opacity, 1.0))
            painter.drawPixmap(rect, self.cache_edge)
            
            # --- Core Layer (White Hot Bloom) ---
            if self.pressure > 0.4:
                core_val = (self.pressure - 0.4) / 0.6
                # Non-linear boost + Flicker
                core_opacity = core_val * core_val * self.flicker
                
                # Standard Screen Pass
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Screen)
                painter.setOpacity(min(core_opacity, 1.0))
                painter.drawPixmap(rect, self.cache_core)
                
                # Additive Bloom Pass
                if core_val > 0.7:
                     bloom_opacity = ((core_val - 0.7) / 0.3) * self.flicker
                     painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
                     painter.setOpacity(min(bloom_opacity, 1.0))
                     painter.drawPixmap(rect, self.cache_core)
                     
            # Reset
            painter.setOpacity(1.0)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        except Exception as e:
            print(f"Paint Error: {e}")
        finally:
            painter.end()

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    window = AnimatedBackground()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
