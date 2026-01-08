"""
PyQt6 Story Bible Application - Complete UI Implementation
Full replacement of Tkinter/CustomTkinter with native PyQt6.
"""

import os
import logging
import queue
import threading
from pathlib import Path
from typing import Optional, Dict, List

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QLineEdit, QScrollArea, QFrame,
    QSplitter, QMenu, QMessageBox, QInputDialog, QGridLayout,
    QStackedWidget, QTabWidget, QToolButton, QToolTip, QGraphicsDropShadowEffect,
    QAbstractButton, QSizePolicy, QFileDialog
)
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QSize, pyqtSlot, QPoint, QRect, QEvent, 
    QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, pyqtProperty
)
from PyQt6.QtGui import (
    QPixmap, QPainter, QFont, QColor, QPalette, QAction, QTextCursor, 
    QTextBlockUserData, QTextCharFormat, QPainterPath
)

from .theme import QtTheme
from .character.character_widget import CharacterWidget
from .shared import (
    IOSSwitch, ToggleSettingsPopup, TransparentScrollArea, 
    ToolbarSplitButton, DescribeSettingsPopup, DescribeSplitButton,
    GenerateButton, AutoExpandingTextEdit, SmartEditor,
    AudioControlWidget
)
from ..services.prompts import get_bible_prompt
from ..services.tts_engine import get_engine as get_tts_engine
from ..ui.components.main_splitter import MainWorkspaceSplitter


# ============================================================================
# USER DATA FOR COMMENTS
# ============================================================================

class ParagraphData(QTextBlockUserData):
    def __init__(self, comments=None):
        super().__init__()
        self.comments = comments or []

class CharacterComment:
    """
    Represents a comment attached to a specific character range.
    Stores absolute positions within the document.
    """
    def __init__(self, start: int, end: int, text: str, comment: str):
        self.start = start  # Absolute position in document
        self.end = end      # Absolute position in document
        self.text = text    # The selected text at time of comment
        self.comment = comment  # The comment content
    
    def contains_position(self, pos: int) -> bool:
        """Check if position is within this comment range."""
        return self.start <= pos < self.end
    
    def update_positions(self, change_pos: int, delta: int):
        """Update positions when document text changes."""
        if change_pos <= self.start:
            self.start += delta
            self.end += delta
        elif change_pos < self.end:
            self.end += delta
# ============================================================================
# BACKGROUND WIDGET
# ============================================================================

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
            # Project root is 3 levels up from this file
            project_root = Path(__file__).parent.parent.parent
            bg_path = project_root / "assets" / "images" / "backgroundimg.png"
            
            # Fallback to old location
            if not bg_path.exists():
                bg_path = project_root / "src" / "ui" / "assets" / "backgroundimg.png"
            
            if bg_path.exists():
                self.background_pixmap = QPixmap(str(bg_path))
                # logging.info(f"Background image loaded: {bg_path}")
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


# ============================================================================
# TOOLBAR WIDGET
# ============================================================================

class ToolbarWidget(QWidget):
    """
    Global toolbar at top - FULLY TRANSPARENT with glass effect.
    Only borders and glows visible, background image shows through.
    """
    
    action_triggered = pyqtSignal(str, str)  # (action, item)
    home_clicked = pyqtSignal()  # Navigate back to dashboard
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # STRICT TRANSPARENCY
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        
        # Glass effect with subtle translucency
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {QtTheme.BG_SIDEBAR};
                border-bottom: 1px solid {QtTheme.GLASS_BORDER};
            }}
        """)
        self.setFixedHeight(QtTheme.TOOLBAR_HEIGHT)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Create toolbar layout with generous spacing and premium feel."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 6, 16, 12)  # Buttons sit closer to top edge
        layout.setSpacing(10)  # Generous spacing between buttons
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # Anchor buttons to top
        
        # Create action buttons with stretch factors
        self._create_action_buttons(layout)
        
        # Add flexible spacer before status indicators
        layout.addStretch(2)
        
        # Create status indicators
        self._create_status_indicators(layout)
    
    def _create_action_buttons(self, layout):
        """Create action buttons with toggle-based configuration panels."""
        from PyQt6.QtWidgets import QSizePolicy
        
        # Home Button (back to dashboard)
        self.home_btn = QPushButton("⌂")
        self.home_btn.setFixedSize(36, 32)
        self.home_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.home_btn.setToolTip("Back to Dashboard")
        self.home_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                color: {QtTheme.TEXT_MUTED};
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(79, 70, 229, 0.3);
                color: {QtTheme.TEXT_PRIMARY};
            }}
            QPushButton:pressed {{
                background-color: rgba(79, 70, 229, 0.15);
            }}
        """)
        self.home_btn.clicked.connect(self.home_clicked.emit)
        layout.addWidget(self.home_btn)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFixedWidth(1)
        separator.setStyleSheet(f"background-color: rgba(255, 255, 255, 0.1);")
        layout.addWidget(separator)
        
        # Write Button
        self.write_btn = ToolbarSplitButton(
            "Write",
            ["Continue Writing", "Write Scene", "Generate Opening"],
            default_enabled=["Continue Writing"]  # Default only first
        )
        self.write_btn.clicked.connect(self._handle_write_click)
        layout.addWidget(self.write_btn, 2)
        
        # Rewrite Button
        self.rewrite_btn = ToolbarSplitButton(
            "Rewrite",
            ["Show Don't Tell", "Dramatic", "Gritty", "Elegant", "Concise"],
            default_enabled=["Show Don't Tell"]  # Default only first
        )
        self.rewrite_btn.clicked.connect(self._handle_rewrite_click)
        layout.addWidget(self.rewrite_btn, 2)
        
        # Describe Button
        self.describe_btn = ToolbarSplitButton(
            "Describe",
            ["Sight", "Sound", "Smell", "Taste", "Touch", "Metaphor"],
            default_enabled=["Sight", "Sound"]  # Default sensory pair
        )
        self.describe_btn.clicked.connect(self._handle_describe_click)
        layout.addWidget(self.describe_btn, 2)
        
        # More Tools Button
        self.more_tools_btn = ToolbarSplitButton(
            "More Tools",
            ["Visualize", "Twist", "Poem"],
            default_enabled=["Visualize"]  # Default first
        )
        self.more_tools_btn.clicked.connect(self._handle_more_tools_click)
        layout.addWidget(self.more_tools_btn, 2)
        
    def _handle_write_click(self):
        config = self.write_btn.get_config()
        if config:
            payload = ",".join(config)
            self.action_triggered.emit("write", payload)
            
    def _handle_rewrite_click(self):
        config = self.rewrite_btn.get_config()
        if config:
            payload = ",".join(config)
            self.action_triggered.emit("rewrite", payload)
            
    def _handle_describe_click(self):
        config = self.describe_btn.get_config()
        if config:
            payload = ",".join(config)
            self.action_triggered.emit("describe", payload)
            
    def _handle_more_tools_click(self):
        config = self.more_tools_btn.get_config()
        if config:
            payload = ",".join(config)
            self.action_triggered.emit("more_tools", payload)
    
    def _create_status_indicators(self, layout):
        """Create status indicators with premium styling."""
        self.word_count_label = QLabel("Words: 0")
        self.word_count_label.setFont(QtTheme.get_font_ui())
        self.word_count_label.setStyleSheet(f"""
            color: {QtTheme.TEXT_MUTED}; 
            padding: 0 14px;
            font-weight: 500;
            letter-spacing: 0.4px;
        """)
        layout.addWidget(self.word_count_label, 0)
        
        self.save_status_label = QLabel("Saved ✓")
        self.save_status_label.setFont(QtTheme.get_font_ui())
        self.save_status_label.setStyleSheet(f"""
            color: {QtTheme.ACCENT_PRIMARY}; 
            padding: 0 14px;
            font-weight: 500;
            letter-spacing: 0.4px;
        """)
        layout.addWidget(self.save_status_label, 0)
        
        # Icon buttons with premium glass effect
        for text, action in [("📤", "export"), ("?", "help"), ("⚙️", "settings")]:
            btn = QPushButton(text)
            btn.setFixedSize(32, 32)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(255, 255, 255, 10),
                        stop:0.05 rgba(255, 255, 255, 6),
                        stop:1 rgba(255, 255, 255, 4)
                    );
                    border: 1px solid rgba(255, 255, 255, 12);
                    border-radius: 8px;
                    color: {QtTheme.TEXT_MUTED};
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(255, 255, 255, 16),
                        stop:0.05 rgba(255, 255, 255, 12),
                        stop:1 rgba(255, 255, 255, 8)
                    );
                    border: 1px solid rgba(255, 255, 255, 22);
                    color: {QtTheme.TEXT_PRIMARY};
                }}
                QPushButton:pressed {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(255, 255, 255, 6),
                        stop:0.05 rgba(255, 255, 255, 4),
                        stop:1 rgba(255, 255, 255, 2)
                    );
                }}
            """)
            
            # Add subtle shadow (reduced for floating appearance)
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(3)
            shadow.setXOffset(0)
            shadow.setYOffset(1)
            shadow.setColor(QColor(0, 0, 0, 18))
            btn.setGraphicsEffect(shadow)
            
            btn.clicked.connect(lambda checked, a=action: self.action_triggered.emit(a, ""))
            layout.addWidget(btn, 0)
    
    def update_word_count(self, count: int):
        """Update word counter display."""
        self.word_count_label.setText(f"Words: {count}")
    
    def set_save_status(self, saved: bool):
        """Update save status indicator."""
        if saved:
            self.save_status_label.setText("Saved ✓")
            self.save_status_label.setStyleSheet(f"""
                color: {QtTheme.ACCENT_PRIMARY}; 
                padding: 0 14px;
                font-weight: 500;
                letter-spacing: 0.4px;
            """)
        else:
            self.save_status_label.setText("Saving...")
            self.save_status_label.setStyleSheet(f"""
                color: {QtTheme.TEXT_MUTED}; 
                padding: 0 14px;
                font-weight: 500;
                letter-spacing: 0.4px;
            """)


# ============================================================================
# CONTEXTUAL POPUP TOOLBAR
# ============================================================================



class ContextualPopup(QWidget):
    """
    Floating contextual toolbar that appears on text selection.
    Premium Glass UI with smooth animations and pill buttons.
    """
    
    action_triggered = pyqtSignal(str, str)  # (action, text)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Initial State - wider to accommodate better spacing
        self.setFixedSize(680, 72)
        self.setWindowOpacity(0.0)
        
        self._setup_ui()
        
        # Animations
        self.anim_group = QParallelAnimationGroup(self)
        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self.pos_anim = QPropertyAnimation(self, b"pos")
        self.anim_group.addAnimation(self.opacity_anim)
        self.anim_group.addAnimation(self.pos_anim)
        
        self.hide()
        
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        # Add margins to allow shadow to be visible
        layout.setContentsMargins(10, 5, 10, 15)
        layout.setSpacing(0)
        
        # Glass background container
        container = QFrame()
        container.setObjectName("popupContainer")
        container.setStyleSheet(f"""
            QFrame#popupContainer {{
                background-color: rgba(30, 32, 36, 235);
                border: 1px solid rgba(255, 255, 255, 20);
                border-radius: 24px;
            }}
        """)
        
        # Shadow Effect - Gentle lift
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 90))
        container.setGraphicsEffect(shadow)
        
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(16, 10, 16, 10)  # Increased padding
        container_layout.setSpacing(12)  # Increased spacing between buttons
        
        # Tools: Icon + Label
        tools = [
            ("💬 Comment", "comment"),
            ("🗑️ Clear", "clear_comments"),
            ("🔄 Rewrite", "rewrite_context"),
            ("✨ Describe", "describe_context"),
            ("➕ Expand", "expand_context"),
            ("✍️ Quick Edit", "quick_edit")
        ]
        
        for text, action in tools:
            if action == "describe_context":
                # Special Split Button for Describe
                self.describe_btn = DescribeSplitButton()
                self.describe_btn.clicked.connect(self._handle_describe_click)
                container_layout.addWidget(self.describe_btn)
            else:
                btn = QPushButton(text)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                # Soft pill-shaped buttons with subtle interaction
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        color: {QtTheme.TEXT_SECONDARY};
                        border: none;
                        border-radius: 18px;
                        font-size: 13px;
                        font-weight: 600;
                        padding: 8px 14px;
                        min-width: 70px;
                    }}
                    QPushButton:hover {{
                        background-color: rgba(255, 255, 255, 25);
                        color: white;
                    }}
                    QPushButton:pressed {{
                        background-color: rgba(255, 255, 255, 15);
                        padding-top: 9px;
                        padding-bottom: 7px;
                    }}
                """)
                btn.setFont(QtTheme.get_font_ui())
                btn.clicked.connect(lambda checked, a=action: self.action_triggered.emit(a, ""))
                container_layout.addWidget(btn)
            
        layout.addWidget(container)

    def _handle_describe_click(self):
        """Handle describe button click with current toggles."""
        toggles = self.describe_btn.get_config()
        # Convert list to comma-separated string
        payload = ",".join(toggles)
        self.action_triggered.emit("describe_context", payload)


    def show_at(self, pos: QPoint):
        """Show the popup at the specified global position with animation."""
        # 1. Calculate target position (Align center horizontally)
        x = pos.x() - self.width() // 2
        y = pos.y() - self.height() + 10 # Slight overlap/padding correction due to shadow margins
        
        # 2. Smart Boundary Check
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().availableGeometry()
        
        # Horizontal bounds
        if x < 10: x = 10
        if x + self.width() > screen.width() - 10:
            x = screen.width() - self.width() - 10
            
        # Vertical bounds (Flip if too close to top)
        if y < screen.top() + 10:
            # Show below selection
            y = pos.y() + 35 
            
        target_pos = QPoint(x, y)
        start_pos = QPoint(x, y + 10) # Start slightly lower for "float up" effect
        
        # 3. Setup Animation
        self.stop_animations()
        
        self.opacity_anim.setDuration(200)
        self.opacity_anim.setStartValue(0.0)
        self.opacity_anim.setEndValue(1.0)
        self.opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.pos_anim.setDuration(200)
        self.pos_anim.setStartValue(start_pos)
        self.pos_anim.setEndValue(target_pos)
        self.pos_anim.setEasingCurve(QEasingCurve.Type.OutBack) # Slight bounce/alive feel
        
        self.move(start_pos)
        self.show()
        self.anim_group.start()
        
    def animate_hide(self):
        """Smoothly fade out and hide."""
        if not self.isVisible():
            return
            
        self.stop_animations()
        
        self.opacity_anim.setDuration(150)
        self.opacity_anim.setStartValue(self.windowOpacity())
        self.opacity_anim.setEndValue(0.0)
        self.opacity_anim.setEasingCurve(QEasingCurve.Type.InQuad)
        
        # Connect hide to finished signal of opacity animation
        self.opacity_anim.finished.connect(self.hide)
        self.opacity_anim.start()

    def stop_animations(self):
        self.anim_group.stop()
        self.opacity_anim.stop()
        self.pos_anim.stop()
        try:
            self.opacity_anim.finished.disconnect(self.hide)
        except:
            pass


class CommentTooltip(QWidget):
    """
    Premium glass tooltip for comments with animation.
    Only shows when hovering over commented text.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._setup_ui()
        
        # Animations
        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        
        # Initially hidden
        self.hide()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 15) # Bottom margin for shadow
        
        # Glass container with refined styling
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(25, 25, 30, 250);
                border: 1px solid {QtTheme.ACCENT_PRIMARY};
                border-radius: 14px;
            }}
        """)
        
        # Softer shadow for tooltip
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 85))
        container.setGraphicsEffect(shadow)
        
        content_layout = QVBoxLayout(container)
        content_layout.setContentsMargins(16, 13, 16, 13)  # More padding for readability
        
        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setMaximumWidth(300)  # Constrain width for better readability
        self.label.setStyleSheet(f"""
            color: {QtTheme.TEXT_PRIMARY}; 
            border: none; 
            background: transparent;
            line-height: 1.4;
        """)
        self.label.setFont(QtTheme.get_font_content())
        
        content_layout.addWidget(self.label)
        layout.addWidget(container)
        
    def show_text(self, pos: QPoint, text: str):
        """Show tooltip near the cursor position (above the commented text)."""
        self.label.setText(text)
        self.adjustSize()
        
        # Position slightly above and to the right of cursor
        target_x = pos.x() + 10
        target_y = pos.y() - self.height() - 10  # Above cursor
        
        # Bounds check
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().availableGeometry()
        
        # Horizontal bounds
        if target_x < 10:
            target_x = 10
        if target_x + self.width() > screen.right() - 10:
            target_x = screen.right() - self.width() - 10
            
        # Vertical bounds (flip below if too close to top)
        if target_y < screen.top() + 10:
            target_y = pos.y() + 20  # Show below cursor instead
            
        target_pos = QPoint(target_x, target_y)
        self.move(target_pos)
        
        # Stop any ongoing animation
        self.opacity_anim.stop()
        try:
            self.opacity_anim.finished.disconnect(self._finish_hide)
        except:
            pass
        
        # Animate in
        self.setWindowOpacity(0.0)
        self.show()
        
        self.opacity_anim.setDuration(150)
        self.opacity_anim.setStartValue(0.0)
        self.opacity_anim.setEndValue(1.0)
        self.opacity_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.opacity_anim.start()

    def hide_tooltip(self):
        """Hide tooltip with fade out animation."""
        if not self.isVisible():
            return
        self.opacity_anim.stop()
        self.opacity_anim.setDuration(100)
        self.opacity_anim.setStartValue(self.windowOpacity())
        self.opacity_anim.setEndValue(0.0)
        self.opacity_anim.setEasingCurve(QEasingCurve.Type.InQuad)
        self.opacity_anim.finished.connect(self._finish_hide)
        self.opacity_anim.start()
    
    def _finish_hide(self):
        """Called after fade out animation completes."""
        self.hide()
        try:
            self.opacity_anim.finished.disconnect(self._finish_hide)
        except:
            pass




# ============================================================================
# PROJECT SIDEBAR
# ============================================================================

class ProjectTreeItem(QWidget):
    """Individual project item in tree."""
    
    clicked = pyqtSignal(int)
    context_menu_requested = pyqtSignal(int, str, QPoint)
    
    def __init__(self, project_id: int, name: str, parent=None):
        super().__init__(parent)
        self.project_id = project_id
        self.project_name = name
        
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: transparent;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 5, 10, 5)
        layout.setSpacing(10)
        
        self.label = QLabel(f"📂 {name}")
        self.label.setStyleSheet(f"""
            color: {QtTheme.TEXT_PRIMARY};
            font-weight: bold;
            font-size: 13px;
        """)
        layout.addWidget(self.label, 1)
        
        add_btn = QPushButton("+")
        add_btn.setFixedSize(20, 20)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {QtTheme.TEXT_MUTED};
                border: none;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {QtTheme.BG_HOVER};
                border-radius: 4px;
            }}
        """)
        add_btn.clicked.connect(lambda: self.clicked.emit(self.project_id))
        layout.addWidget(add_btn)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.context_menu_requested.emit(
                self.project_id,
                self.project_name,
                event.globalPosition().toPoint()
            )
        super().mousePressEvent(event)


class ChapterTreeItem(QPushButton):
    """Individual chapter item in tree."""
    
    context_menu_requested = pyqtSignal(int, str, int, bool, bool, QPoint)
    
    def __init__(self, chapter_id: int, title: str, project_id: int,
                 is_first: bool, is_last: bool, is_active: bool = False, parent=None):
        super().__init__(f"  📄 {title}", parent)
        
        self.chapter_id = chapter_id
        self.chapter_title = title
        self.project_id = project_id
        self.is_first = is_first
        self.is_last = is_last
        self.is_active = is_active
        
        fg_color = QtTheme.BG_HOVER if is_active else "transparent"
        text_color = QtTheme.ACCENT_PRIMARY if is_active else QtTheme.TEXT_MUTED
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {fg_color};
                color: {text_color};
                text-align: left;
                padding: 6px 10px 6px 20px;
                border: none;
                border-radius: 4px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {QtTheme.BG_HOVER};
                color: {QtTheme.TEXT_PRIMARY};
            }}
        """)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.context_menu_requested.emit(
                self.chapter_id,
                self.chapter_title,
                self.project_id,
                self.is_first,
                self.is_last,
                event.globalPosition().toPoint()
            )
            event.accept()
        else:
            super().mousePressEvent(event)


class ProjectSidebar(QWidget):
    """Left sidebar with project tree and Story Bible tabs."""
    
    chapter_selected = pyqtSignal(int, int)  # chapter_id, project_id
    bible_section_clicked = pyqtSignal(str)  # section_name
    trash_clicked = pyqtSignal()
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        
        # Enable transparency and RGBA background rendering
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)  # Keep False, paint manually
        
        self.setProperty("class", "SidebarWidget")
        self.setMinimumWidth(QtTheme.SIDEBAR_WIDTH)
        
        self._setup_ui()
        self.refresh_tree()
    
    def paintEvent(self, event):
        """Paint dark glass background manually."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Paint dark glass overlay
        color = QColor(0, 0, 0, 220)  # 86% black
        painter.fillRect(self.rect(), color)
        
        super().paintEvent(event)
    
    def _setup_ui(self):
        """Create sidebar layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header_widget = QWidget()
        header_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        header_widget.setStyleSheet("background-color: transparent;")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(12, 20, 12, 10)
        
        projects_label = QLabel("PROJECTS")
        projects_label.setFont(QtTheme.get_font_header())
        projects_label.setStyleSheet(f"color: {QtTheme.TEXT_MUTED}; padding: 8px;")
        header_layout.addWidget(projects_label)
        
        add_project_btn = QPushButton("+")
        add_project_btn.setFixedSize(24, 24)
        add_project_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {QtTheme.BORDER_COLOR};
                color: {QtTheme.TEXT_MUTED};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {QtTheme.BG_HOVER};
            }}
        """)
        add_project_btn.clicked.connect(self._create_new_project)
        header_layout.addWidget(add_project_btn)
        
        layout.addWidget(header_widget)
        
        # Scrollable project tree
        self.tree_scroll = TransparentScrollArea()
        
        self.tree_widget = QWidget()
        self.tree_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.tree_widget.setStyleSheet("background-color: transparent;")
        self.tree_layout = QVBoxLayout(self.tree_widget)
        self.tree_layout.setContentsMargins(0, 0, 0, 0)
        self.tree_layout.setSpacing(2)
        self.tree_layout.addStretch()
        
        self.tree_scroll.setWidget(self.tree_widget)
        layout.addWidget(self.tree_scroll, 1)
        
        # Bottom section
        self._create_bottom_section(layout)
    
    def _create_bottom_section(self, parent_layout):
        """Create Story Bible toggle and tabs."""
        bottom_section = QWidget()
        bottom_section.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        bottom_section.setStyleSheet("background-color: transparent;")
        bottom_layout = QVBoxLayout(bottom_section)
        bottom_layout.setContentsMargins(8, 10, 8, 10)
        
        # Story Bible toggle
        self.bible_toggle_btn = QPushButton("📖 Story Bible [>]")
        self.bible_toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {QtTheme.TEXT_MUTED};
                text-align: left;
                padding: 10px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {QtTheme.BG_HOVER};
            }}
        """)
        self.bible_toggle_btn.clicked.connect(self.toggle_bible_tabs)
        bottom_layout.addWidget(self.bible_toggle_btn)
        
        # Bible tabs container
        self.bible_tabs_container = QWidget()
        self.bible_tabs_layout = QVBoxLayout(self.bible_tabs_container)
        self.bible_tabs_layout.setContentsMargins(10, 0, 10, 0)
        self.bible_tabs_layout.setSpacing(1)
        
        bible_sections = [
            ("📝 Braindump", "braindump"),
            ("🎭 Genre", "genre"),
            ("🎨 Style", "style"),
            ("📖 Synopsis", "synopsis"),
            ("👥 Characters", "characters"),
            ("🌍 Worldbuilding", "worldbuilding"),
            ("📋 Outline", "outline")
        ]
        
        for label, section in bible_sections:
            btn = QPushButton(label)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {QtTheme.TEXT_MUTED};
                    text-align: left;
                    padding: 6px 10px;
                    border-radius: 4px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: {QtTheme.BG_HOVER};
                }}
            """)
            btn.clicked.connect(lambda checked, s=section: self.bible_section_clicked.emit(s))
            self.bible_tabs_layout.addWidget(btn)
        
        self.bible_tabs_container.hide()
        bottom_layout.addWidget(self.bible_tabs_container)
        
        # Trash button
        trash_btn = QPushButton("🗑️ Trash")
        trash_btn.setStyleSheet(self.bible_toggle_btn.styleSheet())
        trash_btn.clicked.connect(lambda: self.trash_clicked.emit())
        bottom_layout.addWidget(trash_btn)
        
        parent_layout.addWidget(bottom_section)
    
    def toggle_bible_tabs(self):
        """Toggle Story Bible tabs visibility."""
        if self.bible_tabs_container.isVisible():
            self.bible_tabs_container.hide()
            self.bible_toggle_btn.setText("📖 Story Bible [>]")
        else:
            self.bible_tabs_container.show()
            self.bible_toggle_btn.setText("📖 Story Bible [v]")
    
    def refresh_tree(self, active_chapter_id=None, project_id=None):
        """Refresh project tree display.
        
        Args:
            active_chapter_id: Chapter to highlight as active
            project_id: If provided, only show this project (single-project mode)
        """
        # Clear existing items
        while self.tree_layout.count() > 1:
            item = self.tree_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        projects = self.db_manager.get_projects_with_chapters()
        
        # Filter to single project if specified (editor mode)
        if project_id:
            projects = [p for p in projects if p['id'] == project_id]
        
        if not projects:
            no_projects_label = QLabel("No Projects")
            no_projects_label.setStyleSheet(f"""
                color: {QtTheme.TEXT_MUTED};
                padding: 20px;
                font-style: italic;
            """)
            no_projects_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tree_layout.insertWidget(0, no_projects_label)
            return
        
        for project in projects:
            project_item = ProjectTreeItem(project['id'], project['name'])
            project_item.clicked.connect(lambda pid=project['id']: self._create_new_chapter(pid))
            project_item.context_menu_requested.connect(self._show_project_context_menu)
            self.tree_layout.insertWidget(self.tree_layout.count() - 1, project_item)
            
            for idx, chapter in enumerate(project['chapters']):
                is_active = (chapter['id'] == active_chapter_id)
                is_first = (idx == 0)
                is_last = (idx == len(project['chapters']) - 1)
                
                chapter_item = ChapterTreeItem(
                    chapter['id'],
                    chapter['title'],
                    project['id'],
                    is_first,
                    is_last,
                    is_active
                )
                chapter_item.clicked.connect(
                    lambda checked, cid=chapter['id'], pid=project['id']:
                    self.chapter_selected.emit(cid, pid)
                )
                chapter_item.context_menu_requested.connect(self._show_chapter_context_menu)
                self.tree_layout.insertWidget(self.tree_layout.count() - 1, chapter_item)
    
    def _create_new_project(self):
        """Show dialog to create new project."""
        name, ok = QInputDialog.getText(self, "New Project", "Project Name:")
        if ok and name:
            new_id = self.db_manager.create_project(name)
            if new_id:
                self.db_manager.create_chapter(new_id, "Chapter 1")
                self.refresh_tree()
    
    def _create_new_chapter(self, project_id: int):
        """Show dialog to create new chapter."""
        title, ok = QInputDialog.getText(self, "New Chapter", "Chapter Title:")
        if ok and title:
            self.db_manager.create_chapter(project_id, title)
            self.refresh_tree()
    
    def _show_project_context_menu(self, project_id: int, project_name: str, pos: QPoint):
        """Show context menu for project."""
        menu = QMenu(self)
        rename_action = menu.addAction("Rename")
        menu.addSeparator()
        delete_action = menu.addAction("Delete")
        
        action = menu.exec(pos)
        
        if action == rename_action:
            self._rename_project(project_id, project_name)
        elif action == delete_action:
            self._delete_project(project_id, project_name)
    
    def _show_chapter_context_menu(self, chapter_id: int, chapter_title: str,
                                    project_id: int, is_first: bool, is_last: bool, pos: QPoint):
        """Show context menu for chapter."""
        menu = QMenu(self)
        rename_action = menu.addAction("Rename")
        menu.addSeparator()
        
        move_up_action = None
        move_down_action = None
        
        if not is_first:
            move_up_action = menu.addAction("Move Up ↑")
        if not is_last:
            move_down_action = menu.addAction("Move Down ↓")
        
        if not is_first or not is_last:
            menu.addSeparator()
        
        delete_action = menu.addAction("Delete")
        
        action = menu.exec(pos)
        
        if action == rename_action:
            self._rename_chapter(chapter_id, chapter_title)
        elif action == move_up_action:
            self.db_manager.move_chapter_up(chapter_id)
            self.refresh_tree()
        elif action == move_down_action:
            self.db_manager.move_chapter_down(chapter_id)
            self.refresh_tree()
        elif action == delete_action:
            self._delete_chapter(chapter_id, chapter_title)
    
    def _rename_project(self, project_id: int, current_name: str):
        new_name, ok = QInputDialog.getText(
            self, "Rename Project",
            f"Rename '{current_name}' to:",
            text=current_name
        )
        if ok and new_name and new_name != current_name:
            self.db_manager.rename_project(project_id, new_name)
            self.refresh_tree()
    
    def _rename_chapter(self, chapter_id: int, current_title: str):
        new_title, ok = QInputDialog.getText(
            self, "Rename Chapter",
            f"Rename '{current_title}' to:",
            text=current_title
        )
        if ok and new_title and new_title != current_title:
            self.db_manager.rename_chapter(chapter_id, new_title)
            self.refresh_tree()
    
    def _delete_project(self, project_id: int, project_name: str):
        reply = QMessageBox.question(
            self,
            "Delete Project",
            f"Are you sure you want to delete '{project_name}' and all its chapters?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.db_manager.delete_project(project_id)
            self.refresh_tree()
    
    def _delete_chapter(self, chapter_id: int, chapter_title: str):
        reply = QMessageBox.question(
            self,
            "Delete Chapter",
            f"Are you sure you want to delete '{chapter_title}'?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.db_manager.delete_chapter(chapter_id)
            self.refresh_tree()


# ============================================================================
# CHARACTER MANAGEMENT WIDGET
# ============================================================================

# ============================================================================
# CENTER PANEL - CONTINUOUS SCROLL WITH WRITING CANVAS & STORY BIBLE
# ============================================================================

class CenterPanel(QWidget):
    """
    Center panel - BLACK TINTED GLASS for readability.
    Writing canvas and Story Bible float above background with subtle overlay.
    """
    
    content_changed = pyqtSignal()
    action_requested = pyqtSignal(str)  # action_type
    
    def __init__(self, db_manager, ai_engine=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.ai_engine = ai_engine
        self.current_project_id = None
        self.current_chapter_id = None
        self.story_bible_container = None
        self.bible_section_widgets = {}
        self._last_hovered_block = None
        
        # Character-level comments (replaces block-level)
        self.character_comments: List[CharacterComment] = []
        self._last_hovered_comment: CharacterComment = None
        
        # Contextual Popup
        self.context_popup = ContextualPopup(self)
        self.context_popup.action_triggered.connect(self._handle_context_action)
        
        # Comment Tooltip
        self.comment_tooltip = CommentTooltip(self)
        
        # Generation Lock
        self._active_summaries = set()

        # TTS Engine
        self.tts_engine = get_tts_engine()
        self.current_voice = "neutral"

        
        # TRANSPARENT WITH BLACK OVERLAY for readability
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)  # Keep False, paint manually
        
        self._setup_ui()
    
    def paintEvent(self, event):
        """Paint dark glass background manually."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Paint dark glass overlay - 78% black
        color = QColor(0, 0, 0, 200)
        painter.fillRect(self.rect(), color)
        
        super().paintEvent(event)
    
    def _setup_ui(self):
        """Create center panel UI with black overlay."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Scroll area (transparent)
        self.scroll_area = TransparentScrollArea()
        
        # Content widget (transparent - overlay is on parent)
        self.content_widget = QWidget()
        self.content_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.content_widget.setAutoFillBackground(False)
        self.content_widget.setStyleSheet("background-color: transparent;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(20)
        
        # Writing canvas (always at top)
        self._create_writing_canvas()
        
        self.content_layout.addStretch()
        
        self.scroll_area.setWidget(self.content_widget)
        layout.addWidget(self.scroll_area)
    
    def _create_writing_canvas(self):
        """Create main writing area - FULLY TRANSPARENT."""
        # Document header (transparent)
        header_widget = QWidget()
        header_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        header_widget.setAutoFillBackground(False)
        header_widget.setStyleSheet("background-color: transparent;")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 15)
        
        # Title input (TRANSPARENT - only text visible)
        self.document_title = QLineEdit("Untitled Document")
        self.document_title.setFont(QtTheme.get_font_title())
        self.document_title.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.document_title.setAutoFillBackground(False)
        self.document_title.setStyleSheet(f"""
            QLineEdit {{
                background-color: transparent;
                border: none;
                color: {QtTheme.TEXT_PRIMARY};
                padding: 10px 0px;
            }}
        """)
        header_layout.addWidget(self.document_title, 1)
        
        # Document menu button (transparent, glow on hover)
        doc_menu_btn = QPushButton("⋮")
        doc_menu_btn.setFixedSize(40, 40)
        doc_menu_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {QtTheme.TEXT_MUTED};
                font-size: 20px;
            }}
            QPushButton:hover {{
                background-color: {QtTheme.BG_HOVER};
                border-radius: 4px;
            }}
        """)
        doc_menu_btn.clicked.connect(self._show_document_menu)
        header_layout.addWidget(doc_menu_btn)
        
        self.content_layout.addWidget(header_widget)
        
        # Formatting toolbar (glass effect)
        toolbar_widget = self._create_formatting_toolbar()
        self.content_layout.addWidget(toolbar_widget)
        
        # Audio Controls
        self.audio_controls = AudioControlWidget(self.tts_engine.list_available_voices())
        self.audio_controls.read_clicked.connect(self._handle_read_aloud)
        self.audio_controls.stop_clicked.connect(self._handle_stop_reading)
        self.audio_controls.download_clicked.connect(self._handle_download_mp3)
        self.audio_controls.voice_changed.connect(self._handle_voice_change)
        self.content_layout.addWidget(self.audio_controls)

        
        # Editor textbox (BLACK OVERLAY for readability - text + cursor visible)
        # Using SmartEditor for incremental summarization
        self.editor_textbox = SmartEditor()
        # Connect Smart Signal
        self.editor_textbox.summary_triggered.connect(
            lambda text, cb: self._handle_smart_summary(text, 'chapter', cb)
        )
        
        self.editor_textbox.setFont(QtTheme.get_font_prose())
        self.editor_textbox.setFixedHeight(800)
        
        # TRANSPARENT WITH BLACK OVERLAY
        self.editor_textbox.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.editor_textbox.setAutoFillBackground(False)
        self.editor_textbox.setFrameShape(QFrame.Shape.NoFrame)
        
        self.editor_textbox.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                border: none;
                color: {QtTheme.TEXT_PRIMARY};
                padding: 20px 0px;
                line-height: 1.6;
                selection-background-color: {QtTheme.ACCENT_PRIMARY};
                selection-color: {QtTheme.TEXT_PRIMARY};
            }}
        """)
        
        # BLACK OVERLAY on viewport for readability
        editor_viewport = self.editor_textbox.viewport()
        editor_viewport.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        editor_viewport.setAutoFillBackground(True)  # TRUE to render RGBA
        editor_viewport.setStyleSheet(f"background-color: {QtTheme.OVERLAY_LIGHT};")
        
        self.editor_textbox.textChanged.connect(self.content_changed.emit)
        self.editor_textbox.selectionChanged.connect(self._handle_selection_change)
        
        # Enable mouse tracking for comment tooltips
        self.editor_textbox.viewport().installEventFilter(self)
        self.editor_textbox.viewport().setMouseTracking(True)
        
        self.content_layout.addWidget(self.editor_textbox)
        
        # Action buttons
        actions_widget = self._create_action_buttons()
        self.content_layout.addWidget(actions_widget)
    
    def _handle_read_aloud(self):
        """Start reading current text."""
        text = self.editor_textbox.toPlainText()
        if not text.strip():
            self.audio_controls.set_reading_state(False)
            return
            
        # Get start position from cursor if selection/cursor exists
        cursor = self.editor_textbox.textCursor()
        pos = cursor.position()
        
        # Simple heuristic: If near beginning, read all. If in middle, read from there.
        # But for simpler UX initially, maybe just read from cursor?
        # User requirement: "Determine the current page index... Extract text from the current page forward."
        # Since we have one big editor for chapter, "from cursor forward" works best.
        
        text_to_read = text[pos:] if pos < len(text) else text
        if not text_to_read.strip():
            text_to_read = text # Fallback to start if at end
            
        threading.Thread(target=self._run_tts_thread, args=(text_to_read,), daemon=True).start()

    def _run_tts_thread(self, text):
        """Threaded TTS execution."""
        try:
            voice = self.current_voice
            character_name = None
            
            # Check if using a character voice
            if voice and voice.startswith("Character: "):
                character_name = voice.replace("Character: ", "") 
                # voice = "default" # Or keep as is, engine ignores voice if char_name set
            
            self.tts_engine.tts_read_text(text, voice, character_name=character_name)
        except Exception as e:
            logging.error(f"TTS Error: {e}")
        finally:
            # Update UI safely
            QTimer.singleShot(0, lambda: self.audio_controls.set_reading_state(False))

    def _handle_stop_reading(self):
        """Stop TTS."""
        self.tts_engine.stop()

    def _handle_download_mp3(self):
        """Export chapter to Audio."""
        text = self.editor_textbox.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "Empty Chapter", "Nothing to export.")
            return
            
        path, _ = QFileDialog.getSaveFileName(self, "Save Audio", f"Chapter_{self.current_chapter_id}.wav", "WAV Audio (*.wav)")
        if path:
            self.audio_controls.download_btn.setText("⏳")
            self.audio_controls.download_btn.setEnabled(False)
            
            def run_export():
                out = self.tts_engine.tts_generate_mp3(text, self.current_voice, path)
                QTimer.singleShot(0, lambda: self._on_export_complete(out))
                
            threading.Thread(target=run_export, daemon=True).start()

    def _on_export_complete(self, path):
        self.audio_controls.download_btn.setText("⬇ MP3")
        self.audio_controls.download_btn.setEnabled(True)
        if path:
            QMessageBox.information(self, "Export Complete", f"Audio saved to:\n{path}")
        else:
            QMessageBox.critical(self, "Export Failed", "Could not generate audio file.")

    def _handle_voice_change(self, voice):
        self.current_voice = voice

    def _create_formatting_toolbar(self) -> QWidget:
        """Create formatting toolbar with even distribution."""
        from PyQt6.QtWidgets import QSizePolicy
        
        toolbar = QWidget()
        toolbar.setFixedHeight(60)
        
        # Black tinted glass effect for readability
        toolbar.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        toolbar.setAutoFillBackground(True)  # TRUE to render RGBA background
        toolbar.setStyleSheet(f"""
            background-color: {QtTheme.BG_SIDEBAR};
            border: 1px solid {QtTheme.GLASS_BORDER};
            border-radius: 8px;
        """)
        
        layout = QHBoxLayout(toolbar)
        # Zero horizontal margins for full width distribution
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(6)
        
        buttons = [
            ("↶", "undo"), ("↷", "redo"), ("B", "bold"), ("I", "italic"),
            ("U", "underline"), ("S", "strikethrough"), ("•", "bullet"),
            ("1.", "numbered"), ("Aa", "font"), ("H1", "h1"), ("H2", "h2"), ("H3", "h3")
        ]
        
        for text, action in buttons:
            btn = QPushButton(text)
            # Responsive size policy - expand to fill available space
            btn.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed
            )
            btn.setMinimumHeight(44)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            # Make buttons more visible with better contrast
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(50, 50, 60, 180);
                    color: {QtTheme.TEXT_PRIMARY};
                    border: 1px solid rgba(100, 100, 120, 100);
                    border-radius: 6px;
                    font-size: 16px;
                    font-weight: bold;
                    padding: 2px;
                }}
                QPushButton:hover {{
                    background-color: {QtTheme.ACCENT_PRIMARY};
                    color: white;
                    border: 1px solid {QtTheme.ACCENT_PRIMARY};
                }}
                QPushButton:pressed {{
                    background-color: {QtTheme.ACCENT_HOVER};
                }}
            """)
            btn.clicked.connect(lambda checked, a=action: self._format_action(a))
            # Add with stretch factor for even distribution
            layout.addWidget(btn, 1)
        
        return toolbar
    
    def _create_action_buttons(self) -> QWidget:
        """Create AI action buttons."""
        widget = QWidget()
        widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        widget.setStyleSheet("background-color: transparent;")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 20, 0, 0)
        layout.setSpacing(8)
        
        buttons = [
            ("Generate a Rough Draft", "generate_draft"),
            ("Generate 3 Openings", "generate_openings"),
            ("Chat About an Idea", "chat_idea")
        ]
        
        for text, action in buttons:
            btn = QPushButton(text)
            btn.setMinimumHeight(44)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {QtTheme.ACCENT_SECONDARY};
                    color: {QtTheme.TEXT_PRIMARY};
                    border-radius: 10px;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: {QtTheme.ACCENT_HOVER};
                }}
            """)
            btn.clicked.connect(lambda checked, a=action: self.action_requested.emit(a))
            layout.addWidget(btn)
        
        return widget
    
    def _format_action(self, action: str):
        """Handle formatting actions for the text editor."""
        cursor = self.editor_textbox.textCursor()
        
        if action == "undo":
            self.editor_textbox.undo()
        elif action == "redo":
            self.editor_textbox.redo()
        elif action == "bold":
            fmt = cursor.charFormat()
            fmt.setFontWeight(QFont.Weight.Bold if fmt.fontWeight() != QFont.Weight.Bold else QFont.Weight.Normal)
            cursor.mergeCharFormat(fmt)
            self.editor_textbox.setTextCursor(cursor)
        elif action == "italic":
            fmt = cursor.charFormat()
            fmt.setFontItalic(not fmt.fontItalic())
            cursor.mergeCharFormat(fmt)
            self.editor_textbox.setTextCursor(cursor)
        elif action == "underline":
            fmt = cursor.charFormat()
            fmt.setFontUnderline(not fmt.fontUnderline())
            cursor.mergeCharFormat(fmt)
            self.editor_textbox.setTextCursor(cursor)
        elif action == "strikethrough":
            fmt = cursor.charFormat()
            fmt.setFontStrikeOut(not fmt.fontStrikeOut())
            cursor.mergeCharFormat(fmt)
            self.editor_textbox.setTextCursor(cursor)
        elif action == "bullet":
            # Insert bullet list
            cursor.insertText("• ")
        elif action == "numbered":
            # Insert numbered list
            cursor.insertText("1. ")
        elif action == "h1":
            # Apply H1 formatting
            cursor.select(QTextCursor.SelectionType.LineUnderCursor)
            fmt = cursor.charFormat()
            fmt.setFontPointSize(24)
            fmt.setFontWeight(QFont.Weight.Bold)
            cursor.mergeCharFormat(fmt)
            self.editor_textbox.setTextCursor(cursor)
        elif action == "h2":
            # Apply H2 formatting
            cursor.select(QTextCursor.SelectionType.LineUnderCursor)
            fmt = cursor.charFormat()
            fmt.setFontPointSize(20)
            fmt.setFontWeight(QFont.Weight.Bold)
            cursor.mergeCharFormat(fmt)
            self.editor_textbox.setTextCursor(cursor)
        elif action == "h3":
            # Apply H3 formatting
            cursor.select(QTextCursor.SelectionType.LineUnderCursor)
            fmt = cursor.charFormat()
            fmt.setFontPointSize(16)
            fmt.setFontWeight(QFont.Weight.Bold)
            cursor.mergeCharFormat(fmt)
            self.editor_textbox.setTextCursor(cursor)
        elif action == "font":
            # Font size dialog
            from PyQt6.QtWidgets import QInputDialog
            current_size = cursor.charFormat().fontPointSize()
            if current_size == 0:
                current_size = 12
            size, ok = QInputDialog.getInt(self, "Font Size", "Enter font size:", int(current_size), 8, 72)
            if ok:
                fmt = cursor.charFormat()
                fmt.setFontPointSize(size)
                cursor.mergeCharFormat(fmt)
                self.editor_textbox.setTextCursor(cursor)
        
        # Keep focus on editor
        self.editor_textbox.setFocus()
        # logging.info(f"Format action applied: {action}")
    
    def _show_document_menu(self):
        """Show document options menu."""
        menu = QMenu(self)
        # menu.addAction("Rename", lambda: logging.info("Rename document"))
        # menu.addAction("Export", lambda: logging.info("Export document"))
        menu.addSeparator()
        # menu.addAction("Delete", lambda: logging.info("Delete document"))
        menu.exec(self.sender().mapToGlobal(QPoint(0, 40)))
    
    def create_story_bible_container(self):
        """Create Story Bible sections below writing canvas."""
        if self.story_bible_container:
            return  # Already exists
        
        # Add spacer
        spacer = QWidget()
        spacer.setFixedHeight(80)
        spacer.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        spacer.setStyleSheet("background-color: transparent;")
        self.content_layout.addWidget(spacer)
        
        # Create Story Bible container
        self.story_bible_container = QWidget()
        self.story_bible_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.story_bible_container.setStyleSheet("background-color: transparent;")
        bible_layout = QVBoxLayout(self.story_bible_container)
        bible_layout.setContentsMargins(0, 0, 0, 0)
        bible_layout.setSpacing(QtTheme.CARD_SPACING)
        
        # Story Bible Header
        header_frame = QWidget()
        header_frame.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        header_frame.setStyleSheet("background-color: transparent;")
        header_layout = QVBoxLayout(header_frame)
        
        title_label = QLabel("Story Bible")
        title_label.setFont(QtTheme.get_font_title())
        title_label.setStyleSheet(f"color: {QtTheme.TEXT_PRIMARY};")
        header_layout.addWidget(title_label)
        
        desc_label = QLabel("Build your story world. This context helps the AI write consistently.")
        desc_label.setFont(QtTheme.get_font_ui())
        desc_label.setStyleSheet(f"color: {QtTheme.TEXT_MUTED};")
        header_layout.addWidget(desc_label)
        
        bible_layout.addWidget(header_frame)
        
        # Create 7 Story Bible sections
        sections = [
            ("Braindump", "braindump", "What's your story about? Free-form notes, ideas, themes..."),
            ("Genre", "genre", "e.g., Fantasy, Sci-Fi, Mystery, Romance"),
            ("Style", "style", None),  # Special handling
            ("Synopsis", "synopsis", "Brief overview of your story arc..."),
            ("Characters", "characters", None),  # Special handling
            ("Worldbuilding", "worldbuilding", "Settings, culture, rules, magic systems..."),
            ("Outline", "outline", "Plot structure, key events, timeline...")
        ]
        
        for section_name, section_key, placeholder in sections:
            if section_name == "Style":
                self._create_style_section(bible_layout)
            elif section_name == "Characters":
                self._create_characters_section(bible_layout)
            else:
                self._create_bible_section(bible_layout, section_name, section_key, placeholder)
        
        self.content_layout.addWidget(self.story_bible_container)
    
    def _create_bible_section(self, parent_layout, section_name: str, section_key: str, placeholder: str):
        """Create a Story Bible text section with black tinted glass."""
        # Card container (black tinted glass for readability)
        card = QWidget()
        card.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        card.setAutoFillBackground(True)  # TRUE to render RGBA background
        card.setStyleSheet(f"""
            background-color: {QtTheme.CARD_BG};
            border: 1px solid {QtTheme.GLASS_BORDER};
            border-radius: {QtTheme.CARD_CORNER_RADIUS}px;
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(QtTheme.CARD_PADDING, QtTheme.CARD_PADDING,
                                      QtTheme.CARD_PADDING, QtTheme.CARD_PADDING)
        
        # Header (transparent) - Title + Generate Button
        header_container = QWidget()
        header_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        header_container.setStyleSheet("background-color: transparent;")
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 5)
        
        header = QLabel(section_name)
        header.setFont(QtTheme.get_font_h3())
        header.setStyleSheet(f"color: {QtTheme.TEXT_PRIMARY};")
        header_layout.addWidget(header)
        
        header_layout.addStretch()
        
        gen_btn = GenerateButton()
        gen_btn.clicked.connect(lambda: self._handle_bible_generation(section_key))
        header_layout.addWidget(gen_btn)
        
        card_layout.addWidget(header_container)
        
        # Text input (Auto-expanding card)
        text_input = AutoExpandingTextEdit()
        text_input.setPlaceholderText(placeholder)
        
        # Connect Smart Signal (Incremental Summarization)
        text_input.summary_triggered.connect(
            lambda text, cb: self._handle_smart_summary(text, section_key, cb)
        )
        
        # TRANSPARENT WITH BLACK OVERLAY
        text_input.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        text_input.setAutoFillBackground(False)
        text_input.setFrameShape(QFrame.Shape.NoFrame)
        
        text_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {QtTheme.BG_INPUT};
                border: 1px solid {QtTheme.GLASS_BORDER};
                border-radius: 8px;
                padding: 10px;
                color: {QtTheme.TEXT_PRIMARY};
                selection-background-color: {QtTheme.ACCENT_PRIMARY};
            }}
        """)
        
        # Ensure viewport has black overlay too
        text_viewport = text_input.viewport()
        text_viewport.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        text_viewport.setAutoFillBackground(True)  # TRUE to render RGBA
        text_viewport.setStyleSheet(f"background-color: {QtTheme.BG_INPUT};")
        
        # Connect save handler with logging
        def on_text_changed():
            # logging.info(f"TEXT_CHANGED: {section_key} editor content changed")
            self._on_bible_field_change(section_key)
        
        text_input.textChanged.connect(on_text_changed)
        card_layout.addWidget(text_input)
        
        # Store references
        self.bible_section_widgets[section_key] = {
            'card': card,
            'widget': text_input,
            'gen_btn': gen_btn
        }
        
        parent_layout.addWidget(card)
        
        # Ensure parent layout doesn't restrict height
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
    
    def _create_style_section(self, parent_layout):
        """Create Style selection section with buttons."""
        card = QWidget()
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        card.setStyleSheet(f"""
            background-color: {QtTheme.CARD_BG};
            border: 1px solid {QtTheme.BORDER_COLOR};
            border-radius: {QtTheme.CARD_CORNER_RADIUS}px;
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(QtTheme.CARD_PADDING, QtTheme.CARD_PADDING,
                                      QtTheme.CARD_PADDING, QtTheme.CARD_PADDING)
        
        # Header
        header = QLabel("Style")
        header.setFont(QtTheme.get_font_h3())
        header.setStyleSheet(f"color: {QtTheme.TEXT_PRIMARY};")
        card_layout.addWidget(header)
        
        # Button container
        btn_container = QWidget()
        btn_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        btn_container.setStyleSheet("background-color: transparent;")
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setSpacing(4)
        
        self.style_selection = "Featured Styles"
        self.style_buttons = {}
        
        styles = ["Featured Styles", "Match My Style", "Custom"]
        
        for style in styles:
            btn = QPushButton(style)
            btn.setMinimumHeight(40)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: 2px solid {QtTheme.BORDER_COLOR};
                    color: {QtTheme.TEXT_MUTED};
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    background-color: {QtTheme.BG_HOVER};
                }}
            """)
            btn.clicked.connect(lambda checked, s=style: self._select_style(s))
            btn_layout.addWidget(btn)
            self.style_buttons[style] = btn
        
        card_layout.addWidget(btn_container)
        
        # Store reference
        self.bible_section_widgets['style'] = {
            'card': card,
            'widget': None  # No text widget for style
        }
        
        parent_layout.addWidget(card)
        
        # Set default selection
        self._select_style("Featured Styles")
    
    def _select_style(self, style: str):
        """Handle style button selection."""
        self.style_selection = style
        
        for s, btn in self.style_buttons.items():
            if s == style:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {QtTheme.ACCENT_PRIMARY};
                        border: 2px solid {QtTheme.ACCENT_PRIMARY};
                        color: {QtTheme.TEXT_PRIMARY};
                        border-radius: 6px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        border: 2px solid {QtTheme.BORDER_COLOR};
                        color: {QtTheme.TEXT_MUTED};
                        border-radius: 6px;
                    }}
                    QPushButton:hover {{
                        background-color: {QtTheme.BG_HOVER};
                    }}
                """)
        
        self._on_bible_field_change('style')
    
    def _create_characters_section(self, parent_layout):
        """Create Character Profile section."""
        card = QWidget()
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        card.setStyleSheet(f"""
            background-color: {QtTheme.CARD_BG};
            border: 1px solid {QtTheme.BORDER_COLOR};
            border-radius: {QtTheme.CARD_CORNER_RADIUS}px;
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(QtTheme.CARD_PADDING, QtTheme.CARD_PADDING,
                                      QtTheme.CARD_PADDING, QtTheme.CARD_PADDING)
        
        # Header
        header = QLabel("Characters")
        header.setFont(QtTheme.get_font_h3())
        header.setStyleSheet(f"color: {QtTheme.TEXT_PRIMARY};")
        card_layout.addWidget(header)
        
        # Character widget (pass ai_engine for AI generation features)
        self.character_widget = CharacterWidget(self.db_manager, self.ai_engine, self.tts_engine)
        self.character_widget.voice_updated.connect(lambda: self._load_character_voices(self.current_project_id) if hasattr(self, 'current_project_id') and self.current_project_id else None)
        card_layout.addWidget(self.character_widget)
        
        # Store reference
        self.bible_section_widgets['characters'] = {
            'card': card,
            'widget': self.character_widget
        }
        
        parent_layout.addWidget(card)
    
    def _on_bible_field_change(self, field_name: str):
        """Handle Story Bible field changes."""
        if not self.current_project_id:
            # logging.warning(f"PERSIST: Cannot save {field_name} - no project_id")
            return
        
        # Get field value
        if field_name == 'style':
            value = self.style_selection
        elif field_name in self.bible_section_widgets:
            widget_data = self.bible_section_widgets[field_name]
            if widget_data['widget'] and isinstance(widget_data['widget'], QTextEdit):
                value = widget_data['widget'].toPlainText()
            else:
                # logging.warning(f"PERSIST: Widget for {field_name} is not QTextEdit")
                return
        else:
            # logging.warning(f"PERSIST: Unknown field {field_name}")
            return
        
        # Save to database (debounced in real implementation)
        try:
            # logging.info(f"PERSIST: Saving {field_name} to DB (project={self.current_project_id}, length={len(value)} chars)")
            self.db_manager.save_bible_field(self.current_project_id, field_name, value)
            # logging.info(f"PERSIST: Successfully saved {field_name}")
        except Exception as e:
            logging.error(f"Failed to save {field_name}: {e}")
    
    def _handle_bible_generation(self, section_key: str):
        """
        Handle direct AI generation for a Bible section.
        Bypasses Lore Chat and streams directly into the field.
        """
        if not self.ai_engine or not self.current_project_id:
            return
            
        widget_data = self.bible_section_widgets.get(section_key)
        if not widget_data:
            return
            
        # Find gen_btn (it's in the header layout)
        # We need to find the button to set loading state
        # A better way is to store it in widget_data
        gen_btn = None
        # We'll update the widget_data storage in _create_bible_section
        # For now, let's assume we'll fix _create_bible_section to store it
        gen_btn = widget_data.get('gen_btn')
        if gen_btn:
            gen_btn.set_loading(True)
            
        # Gather Context
        title = self.document_title.text()
        
        # Canvas Content -> Use Summary if available (Context System)
        canvas_content = ""
        if self.current_chapter_id:
             canvas_summary = self.db_manager.get_chapter_summary(self.current_chapter_id)
             if canvas_summary:
                 canvas_content = canvas_summary
             else:
                 canvas_content = self.editor_textbox.toPlainText() # Fallback
        
        # Other Bible sections -> Use Summaries (Context System)
        context_parts = []
        
        # Fetch clean from DB to ensure we get summaries
        bible_data = self.db_manager.get_story_bible(self.current_project_id)
        
        section_mapping = ['braindump', 'genre', 'style', 'synopsis', 'worldbuilding', 'outline']
        for key in section_mapping:
            if key != section_key:
                # Prefer summary, fallback to full
                summary = bible_data.get(f"{key}_summary")
                full = bible_data.get(key)
                text = summary if summary else full
                
                if text and text.strip():
                    context_parts.append(f"[{key.upper()}]:\n{text}")
                    
        bible_context = "\n\n".join(context_parts)
        
        # Characters - Gather from DB
        char_list = []
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name, role, personality_traits FROM characters WHERE project_id = ? AND is_visible = 1", (self.current_project_id,))
                for row in cursor.fetchall():
                    char_list.append(f"- {row[0]} ({row[1]}): {row[2]}")
        except Exception as e:
            logging.error(f"Failed to fetch characters for context: {e}")
            
        characters_text = "\n".join(char_list) if char_list else "No characters defined yet."
        
        # Genre (from section or DB)
        genre = "General Fiction"
        if bible_data.get('genre'):
            genre = bible_data.get('genre')

        # Construct Prompt
        prompt = get_bible_prompt(
            section_key=section_key,
            title=title,
            characters=characters_text,
            bible_context=bible_context,
            canvas_content=canvas_content,
            genre=genre
        )
        
        if not prompt:
            if gen_btn: gen_btn.set_loading(False)
            return

        # Response handling (setup a queue)
        from queue import Queue
        resp_queue = Queue()
        first_token = True
        
        # Capture raw text for context assembly during generation
        rag_context = {}
        if self.current_chapter_id:
             # Need to get robust context
             chap_data = self.db_manager.get_chapter_summary(self.current_chapter_id)
             rag_context['prev_summary'] = chap_data.get('summary_text', '')
             rag_context['recent_summary'] = chap_data.get('recent_chapter_summary', '')
             
        def stream_thread():
            # Pass correct summaries
            self.ai_engine.stream_response(prompt, resp_queue, bible_data=bible_data, rag_context=rag_context)
            
        # UI Update Timer
        timer = QTimer(self)
        
        def update_ui():
            try:
                nonlocal first_token
                while not resp_queue.empty():
                    token = resp_queue.get_nowait()
                    if token == "[[END]]":
                        timer.stop()
                        if gen_btn: gen_btn.set_loading(False)
                        
                        # CRITICAL FIX: Save the generated text to database
                        widget = widget_data['widget']
                        generated_text = widget.toPlainText()
                        # logging.info(f"AI_GEN_COMPLETE: Saving {section_key} to DB (length={len(generated_text)} chars)")
                        self.db_manager.save_bible_field(self.current_project_id, section_key, generated_text)
                        # logging.info(f"AI_GEN_COMPLETE: {section_key} text saved to database")
                        
                        # Mark as dirty for summarization
                        if hasattr(widget, 'is_globally_dirty'):
                            widget.is_globally_dirty = True
                            widget.check_dirty_and_trigger(force=True)
                        
                        return
                    
                    # Insert token into widget
                    widget = widget_data['widget']
                    cursor = widget.textCursor()
                    
                    # If empty, just insert. If content exists, handle divider logic if first token.
                    if first_token:
                        content = widget.toPlainText().strip()
                        if content:
                            cursor.movePosition(QTextCursor.MoveOperation.End)
                            cursor.insertText("\n\n---\n\n")
                        first_token = False
                        
                    cursor.movePosition(QTextCursor.MoveOperation.End)
                    cursor.insertText(token)
                    widget.setTextCursor(cursor)
            except Exception as e:
                logging.error(f"UI update failed: {e}")
                timer.stop()
                if gen_btn: gen_btn.set_loading(False)

        timer.timeout.connect(update_ui)
        timer.start(50)
        
        # Start AI thread
        threading.Thread(target=stream_thread, daemon=True).start()

    def _handle_smart_summary(self, text: str, source_key: str, callback: callable):
        """
        Unified handler for incremental summarization from SmartEditors.
        
        Args:
            text: The full text content of the editor at time of trigger.
            source_key: 'chapter' or a bible tab key (e.g. 'characters').
            callback: Function to call on success (clears dirty flags).
        """
        if not text.strip():
            # If empty, just clear flags
            callback() 
            return

        # GENERATION LOCK: Prevent summaries while AI is generating or if duplicate
        is_generating = False
        if self.parent() and hasattr(self.parent(), 'is_generating'):
             is_generating = self.parent().is_generating
        
        if is_generating:
            # If main AI is running, we skip. 
            # The dirty flag remains set in SmartEditor, so it will retry later 
            # (e.g. on next focus loss or debounce).
            logging.info(f"SmartSummary: Skipping {source_key} (Main AI Generating)")
            return

        if source_key in self._active_summaries:
            logging.info(f"SmartSummary: Skipping {source_key} (Already Active)")
            return

        # Lock
        self._active_summaries.add(source_key)

        # Distinguish source
        if source_key == 'chapter':
            self._process_chapter_summary(text, callback)
        else:
            self._process_section_summary(text, source_key, callback)

    def _process_chapter_summary(self, full_text: str, callback: callable):
        """Logic from old _trigger_chapter_summarization, now event-driven."""
        if not self.current_chapter_id: 
            return # Keep dirty? No, likely just transient state.
            
        chapter_id = self.current_chapter_id
        
        # GUARDRAIL: Check new text count
        current_len = len(full_text)
        chapter_data = self.db_manager.get_chapter_summary(chapter_id)
        last_count = chapter_data.get('last_summarized_char_count', 0)
        
        new_char_count = current_len - last_count
        
        if new_char_count < 50:
             # Not enough new text to bother AI, but we should clear dirty flag 
             # because we essentially "checked" it and decided it's fine.
             callback()
             return

        # Prepare payload
        new_text_chunk = full_text[last_count:]
        recent_chunk = full_text[-1000:]
        
        logging.info(f"SmartSummary: Processing Chapter (New Chars: {new_char_count})...")
        
        def run_summary():
            try:
                # 1. Incremental Summary
                incremental_summary = self.ai_engine.generate_summary(new_text_chunk, mode='incremental')
                
                # 2. Recent Context
                recent_summary = self.ai_engine.generate_summary(recent_chunk, mode='incremental')
                
                current_summary = chapter_data.get('summary_text', "")
                updated_summary = (current_summary + " " + incremental_summary).strip()
                
                # 3. Recompression Check
                summary_tokens = self.ai_engine.count_tokens(updated_summary)
                if summary_tokens > 1600:
                    logging.info(f"SmartSummary: Recompressing Chapter (Tokens: {summary_tokens})...")
                    updated_summary = self.ai_engine.generate_summary(updated_summary, mode='compress')
                
                # 4. Save
                self.db_manager.save_chapter_summary(chapter_id, updated_summary, recent_summary)
                self.db_manager.update_chapter_progress(chapter_id, current_len)
                
                logging.info(f"SmartSummary: Success for Chapter {chapter_id}")
                
                # CRITICAL: Signal success to UI thread to join callback
                # Since we are in a thread, we should interact with UI safely.
                # But the callback is just setting a boolean flag on the widget object, 
                # which is generally safe in Python due to GIL, but strictly we should invoke.
                # For simplicity in this architecture, we call it directly.
                callback()
                
            except Exception as e:
                logging.error(f"SmartSummary Error (Chapter): {e}")
                # DO NOT CALL CALLBACK -> Dirty flag remains -> will retry next time.
            finally:
                self._active_summaries.discard('chapter')

        threading.Thread(target=run_summary, daemon=True).start()

    def _process_section_summary(self, full_text: str, section_key: str, callback: callable):
        """Logic from old _trigger_section_summarization, now event-driven."""
        
        logging.info(f"SmartSummary: Processing Section {section_key}...")
        
        # Capture ID safely for thread
        project_id = self.current_project_id
        if not project_id:
            logging.error(f"SmartSummary: Aborting {section_key} (No Project ID)")
            callback()
            return

        def run_summary():
             # ... (existing code, using project_id instead of self.current_project_id)
            try:
                # 1. Decide Mode
                token_count = self.ai_engine.count_tokens(full_text)
                mode = 'incremental'
                if token_count > 200:
                    mode = 'bible_compress'
                    
                summary = self.ai_engine.generate_summary(full_text, mode=mode)
                
                if summary and "Error" not in summary:
                    # STEP 1: ALWAYS save raw text FIRST (source of truth)
                    logging.info(f"SmartSummary: Saving RAW TEXT for {section_key} ({len(full_text)} chars)")
                    self.db_manager.save_bible_field(project_id, section_key, full_text)
                    
                    # STEP 2: Then save summary
                    logging.info(f"SmartSummary: Saving SUMMARY for {section_key} ({len(summary)} chars)")
                    self.db_manager.save_bible_field(project_id, f"{section_key}_summary", summary)
                    
                    # STEP 3: Verify both were saved
                    verify_text = self.db_manager.get_bible_field(project_id, section_key)
                    verify_summary = self.db_manager.get_bible_field(project_id, f"{section_key}_summary")
                    
                    if not verify_text or len(verify_text) == 0:
                        logging.error(f"FATAL: Raw text for {section_key} is EMPTY after save! This should never happen!")
                    
                    logging.info(f"SmartSummary: ✅ VERIFIED - {section_key} text: {len(verify_text) if verify_text else 0} chars, summary: {len(verify_summary) if verify_summary else 0} chars")
                    logging.info(f"SmartSummary: Success for {section_key}")
                    logging.info(f"SmartSummary: Saved summary: {summary[:200]}..." if len(summary) > 200 else f"SmartSummary: Saved summary: {summary}")
                    callback()
                else:
                    logging.error(f"SmartSummary Failed for {section_key}")
                    
            except Exception as e:
                logging.error(f"SmartSummary Error ({section_key}): {e}")
            finally:
                self._active_summaries.discard(section_key)

        threading.Thread(target=run_summary, daemon=True).start()

    # KEEPING OLD METHODS AS DEPRECATED OR RE-ROUTING IF NEEDED?
    # Actually, we should replace them or ensure they aren't called duplicatively.
    # The old triggers were: _trigger_section_summarization and _trigger_chapter_summarization.
    # We can delete them if we are sure no one else calls them.
    # Checks: _auto_save called _trigger_chapter_summarization.
    # _check_queue called it too.
    # We need to update those call sites or redirect.

    def _trigger_section_summarization(self, section_key: str):
        """DEPRECATED: Use SmartEditor eventing."""
        pass 

    def _trigger_chapter_summarization(self):
        """DEPRECATED: Use SmartEditor eventing."""
        pass

    
    def destroy_story_bible_container(self):
        """Remove Story Bible from center panel."""
        if self.story_bible_container:
            self.story_bible_container.deleteLater()
            self.story_bible_container = None
            self.bible_section_widgets.clear()
    
    def scroll_to_section(self, section_name: str):
        """Scroll to specific Story Bible section."""
        if section_name in self.bible_section_widgets:
            card = self.bible_section_widgets[section_name]['card']
            # Ensure scrollbar visible
            self.scroll_area.ensureWidgetVisible(card)
    
    def load_project(self, project_id: int, chapter_id: Optional[int] = None):
        """Load project data into UI."""
        self.current_project_id = project_id
        self.current_chapter_id = chapter_id
        
        # ALWAYS set project_id on character widget (even if Story Bible not expanded)
        if hasattr(self, 'character_widget') and self.character_widget:
            self.character_widget.set_project_id(project_id)
            # logging.info(f"Set character_widget project_id to {project_id}")
            
        # Load Character Voices
        self._load_character_voices(project_id)
        
        # Load Story Bible data if container exists
    
    def _load_character_voices(self, project_id: int):
        """Load character voices for the project into TTS engine."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name, custom_voice_path FROM characters WHERE project_id = ? AND custom_voice_path IS NOT NULL", (project_id,))
                rows = cursor.fetchall()
                
            if not rows:
                return

            logging.info(f"Loading {len(rows)} character voices for Project {project_id}...")
            
            # Update Voice List in UI
            current_voices = self.tts_engine.list_available_voices()
            
            # Helper to run extraction in background
            def load_voices_task():
                loaded_count = 0
                for name, path in rows:
                    if not path or not os.path.exists(path):
                        continue
                        
                    # Extract/Load embedding
                    latents = self.tts_engine.extract_speaker_embedding(path)
                    if latents:
                        self.tts_engine.character_voice_map[name] = latents
                        loaded_count += 1
                        
                if loaded_count > 0:
                    logging.info(f"Loaded {loaded_count} character voices.")
                    # Update UI on main thread
                    # We need to signal back. 
                    # For simplicity, we can just invoke method if thread-safe or use QTimer
                    pass

            threading.Thread(target=load_voices_task, daemon=True).start()
            
            # Add placeholders to Voice List immediately? 
            # Or wait? 
            # Better to add them to the dropdown so user can select them.
            # Even if embedding isn't quite ready (race condition), prompt them?
            # tts_read_text handles missing map by falling back to default voice.
            
            character_voices = [f"Character: {row[0]}" for row in rows]
            all_voices = current_voices + character_voices
            
            # Update Audio Controls
            if hasattr(self.audio_controls, 'update_voice_list'):
                 QTimer.singleShot(0, lambda: self.audio_controls.update_voice_list(all_voices))
            
        except Exception as e:
            logging.error(f"Failed to load character voices: {e}")
        if self.story_bible_container:
            try:
                # logging.info(f"Loading Story Bible for project {project_id}...")
                bible_data = self.db_manager.get_story_bible(project_id)
                # logging.info(f"Story Bible data retrieved: {list(bible_data.keys()) if bible_data else 'None'}")
                if bible_data:
                    for field in ["braindump", "genre", "synopsis", "worldbuilding", "outline"]:
                        field_data = bible_data.get(field, "")
                        # logging.info(f"LOAD: Field '{field}': {len(field_data) if field_data else 0} characters in DB")
                        
                        # Check if widget exists
                        if field not in self.bible_section_widgets:
                            logging.warning(f"LOAD: No widget found for field '{field}' - skipping")
                            continue
                        
                        widget_data = self.bible_section_widgets[field]
                        widget = widget_data.get('widget')
                        
                        if not widget:
                            logging.warning(f"LOAD: Widget for '{field}' is None - skipping")
                            continue
                        
                        if not isinstance(widget, QTextEdit):
                            logging.warning(f"LOAD: Widget for '{field}' is not QTextEdit (type: {type(widget).__name__}) - skipping")
                            continue
                        
                        # Load the text regardless of whether it's empty or not (to clear old data)
                        # logging.info(f"LOAD: Loading '{field}' text into widget...")
                        
                        # Use SmartEditor specific flag (blockSignals doesn't catch document changes)
                        if hasattr(widget, 'is_loading'):
                            widget.is_loading = True
                        
                        widget.blockSignals(True)
                        widget.setPlainText(field_data if field_data else "")
                        widget.blockSignals(False)
                        
                        if hasattr(widget, 'is_loading'):
                            widget.is_loading = False
                            
                        # FORCE RESIZE: blockSignals(True) prevented auto-resize
                        if hasattr(widget, 'adjust_height'):
                            widget.adjust_height()
                            
                        # logging.info(f"LOAD: Successfully loaded {len(field_data) if field_data else 0} chars into '{field}' widget")
                    
                    # Load style
                    if 'style' in bible_data and bible_data['style']:
                        self._select_style(bible_data['style'])
                    
                    # STARTUP SUMMARY CHECK: Generate summaries for tabs that don't have them
                    # This happens AFTER text is loaded and signals are unblocked
                    for field in ["braindump", "genre", "synopsis", "worldbuilding", "outline"]:
                        if field in self.bible_section_widgets:
                            # Check if we have text but no summary
                            has_text = bible_data.get(field, "").strip()
                            has_summary = bible_data.get(f"{field}_summary", "").strip()
                            
                            if has_text and not has_summary:
                                logging.info(f"Startup: Missing summary for {field}, triggering auto-generation")
                                log_payload = {
                                    "tab_name": field,
                                    "summary_generated": True,
                                    "reason": "Missing summary in DB"
                                }
                                logging.info(f"Summary Condition: {log_payload}")
                                
                                # Mark as dirty and trigger automation
                                widget_data = self.bible_section_widgets[field]
                                widget = widget_data['widget']
                                if hasattr(widget, 'is_globally_dirty'):
                                    widget.is_globally_dirty = True
                                    # Explicitly start timer to trigger pipeline automatically
                                    if hasattr(widget, 'debounce_timer'):
                                        widget.debounce_timer.start(500) # Short delay 
                            elif has_summary:
                                # Log that we are skipping
                                log_payload = {
                                    "tab_name": field,
                                    "summary_generated": False,
                                    "reason": "Summary exists in DB"
                                }
                                logging.info(f"Summary Condition: {log_payload}")
                    
                    # DIAGNOSTIC: Dump entire database contents for verification
                    self.db_manager.dump_story_bible_contents(project_id)
            except Exception as e:
                logging.error(f"Failed to load story bible: {e}")
        
        # Load chapter content
        if chapter_id:
            try:
                content = self.db_manager.get_chapter_content(chapter_id)
                
                # Get chapter title
                title = "Untitled"
                projects = self.db_manager.get_projects_with_chapters()
                for p in projects:
                    if p['id'] == project_id:
                        for ch in p['chapters']:
                            if ch['id'] == chapter_id:
                                title = ch['title']
                                break
                        break
                
                self.document_title.setText(title)
                
                # Block signals for editor load too
                self.editor_textbox.blockSignals(True)
                self.editor_textbox.setPlainText(content if content else "")
                self.editor_textbox.blockSignals(False)
            except Exception as e:
                logging.error(f"Failed to load chapter: {e}")
    
    def get_editor_content(self) -> str:
        """Get current editor content."""
        return self.editor_textbox.toPlainText()
    
    def insert_editor_content(self, text: str):
        """Insert text into editor at cursor position."""
        cursor = self.editor_textbox.textCursor()
        cursor.insertText(text)
        self.editor_textbox.setTextCursor(cursor)
    
    def get_selected_text(self) -> str:
        """Get currently selected text."""
        cursor = self.editor_textbox.textCursor()
        return cursor.selectedText()
    
    def replace_selected_text(self, text: str):
        """Replace currently selected text with new text."""
        cursor = self.editor_textbox.textCursor()
        if cursor.hasSelection():
            cursor.insertText(text)
            self.editor_textbox.setTextCursor(cursor)
        else:
            # Fallback to insert if no selection (though logic should prevent this for Describe)
            cursor.insertText(text)

    # ------------------------------------------------------------------------
    # CONTEXTUAL POPUP LOGIC
    # ------------------------------------------------------------------------

    def _handle_selection_change(self):
        """Show contextual popup when text is selected."""
        cursor = self.editor_textbox.textCursor()
        if cursor.hasSelection() and cursor.selectedText().strip():
            # Get cursor position in viewport coordinates
            rect = self.editor_textbox.cursorRect()
            # Map to global screen coordinates
            viewport = self.editor_textbox.viewport()
            global_pos = viewport.mapToGlobal(rect.topLeft())
            
            # Position popup above selection
            self.context_popup.show_at(global_pos)
        else:
            self.context_popup.animate_hide()

    def _handle_context_action(self, action: str, payload: str):
        """Handle actions from contextual popup."""
        cursor = self.editor_textbox.textCursor()
        text = cursor.selectedText()
        
        if action == "comment":
            if not cursor.hasSelection():
                return
            comment, ok = QInputDialog.getMultiLineText(self, "Add Comment", "Enter your comment:")
            if ok and comment:
                # Character-level comment using selection positions
                start = cursor.selectionStart()
                end = cursor.selectionEnd()
                self._add_character_comment(start, end, text, comment)
        
        elif action == "clear_comments":
            # Clear all comments at current cursor position
            cursor_pos = cursor.position()
            self._clear_comments_at_position(cursor_pos)
        
        elif action == "rewrite_context":
            self.action_requested.emit(f"CONTEXT_REWRITE::{text}")
        
        elif action == "describe_context":
            # Payload contains enabled senses (e.g., "Sight,Sound")
            self.action_requested.emit(f"CONTEXT_DESCRIBE::{text}::{payload}")
            
        elif action == "expand_context":
            self.action_requested.emit(f"CONTEXT_EXPAND::{text}")
            
        elif action == "quick_edit":
            self._open_quick_edit(cursor.block())

    def _add_character_comment(self, start: int, end: int, text: str, comment: str):
        """Add a comment to a specific character range."""
        char_comment = CharacterComment(start, end, text, comment)
        self.character_comments.append(char_comment)
        self._update_comment_highlights()

    def _clear_comments_at_position(self, pos: int):
        """Remove all comments that contain the given position."""
        self.character_comments = [c for c in self.character_comments if not c.contains_position(pos)]
        self._update_comment_highlights()
        self.comment_tooltip.hide_tooltip()
        self._last_hovered_comment = None

    def _update_comment_highlights(self):
        """Update extra selections to highlight all commented ranges."""
        selections = []
        
        for comment in self.character_comments:
            selection = QTextEdit.ExtraSelection()
            
            # Create cursor for this range
            cursor = QTextCursor(self.editor_textbox.document())
            cursor.setPosition(comment.start)
            cursor.setPosition(comment.end, QTextCursor.MoveMode.KeepAnchor)
            
            # Style: subtle background highlight with underline
            fmt = QTextCharFormat()
            bg_color = QColor(QtTheme.ACCENT_PRIMARY)
            bg_color.setAlpha(30)  # Very subtle background
            fmt.setBackground(bg_color)
            
            underline_color = QColor(QtTheme.ACCENT_PRIMARY)
            underline_color.setAlpha(120)
            fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)
            fmt.setUnderlineColor(underline_color)
            
            selection.cursor = cursor
            selection.format = fmt
            selections.append(selection)
        
        self.editor_textbox.setExtraSelections(selections)

    def _get_comment_at_position(self, pos: int) -> CharacterComment:
        """Find a comment that contains the given cursor position."""
        for comment in self.character_comments:
            if comment.contains_position(pos):
                return comment
        return None

    # Legacy block-level functions kept for compatibility
    def _add_comment_to_block(self, block, comment):
        """Add a comment to a paragraph block (legacy)."""
        data = block.userData()
        if not data:
            data = ParagraphData()
            block.setUserData(data)
        data.comments.append(comment)

    def _clear_comments_from_block(self, block):
        """Remove all comments from a paragraph block (legacy)."""
        block.setUserData(None)
        self.comment_tooltip.hide_tooltip()
        if self._last_hovered_block == block:
            self._last_hovered_block = None

    def eventFilter(self, obj, event):
        """Handle tooltip display for character-level comments."""
        if obj == self.editor_textbox.viewport():
            if event.type() == QEvent.Type.MouseMove:
                pos = event.position().toPoint()
                cursor = self.editor_textbox.cursorForPosition(pos)
                cursor_pos = cursor.position()
                
                # Find comment at current cursor position
                hovered_comment = self._get_comment_at_position(cursor_pos)
                
                # If moved to a different comment (or no comment)
                if hovered_comment != self._last_hovered_comment:
                    if self._last_hovered_comment:
                        self.comment_tooltip.hide_tooltip()
                    
                    if hovered_comment:
                        # Show tooltip for this comment
                        tooltip_text = f"<b>Comment on:</b> <i>\"{hovered_comment.text[:30]}{'...' if len(hovered_comment.text) > 30 else ''}\"</i><br><br>{hovered_comment.comment}"
                        self.comment_tooltip.show_text(event.globalPosition().toPoint(), tooltip_text)
                    
                    self._last_hovered_comment = hovered_comment
            
            elif event.type() == QEvent.Type.Leave:
                # Mouse left the viewport
                if self._last_hovered_comment:
                    self.comment_tooltip.hide_tooltip()
                    self._last_hovered_comment = None
                    
        return super().eventFilter(obj, event)

    def _apply_block_underline(self, block):
        """Apply subtle underline to the specified block (legacy - on hover)."""
        cursor = QTextCursor(block)
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        fmt = QTextCharFormat()
        fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)
        
        # Subtle theme-matched color
        c = QColor(QtTheme.ACCENT_PRIMARY)
        c.setAlpha(100)  # More visible underline
        
        fmt.setUnderlineColor(c)
        cursor.mergeCharFormat(fmt)

    def _clear_block_underline(self, block):
        """Clear the underline from the specified block."""
        cursor = QTextCursor(block)
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        fmt = QTextCharFormat()
        fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.NoUnderline)
        cursor.mergeCharFormat(fmt)

    def _open_quick_edit(self, block):
        """Open a mini inline editor for the current paragraph."""
        old_text = block.text()
        new_text, ok = QInputDialog.getMultiLineText(self, "Quick Edit", "Modify paragraph:", old_text)
        if ok and new_text != old_text:
            cursor = QTextCursor(block)
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            # preserve trailing newline if needed? block.text doesn't include it.
            cursor.insertText(new_text)

    def append_text_below_selection(self, text: str):
        """Append text naturally below the current selection/paragraph."""
        cursor = self.editor_textbox.textCursor()
        # Move to end of selection if any
        if cursor.hasSelection():
            cursor.setPosition(cursor.selectionEnd())
        
        cursor.insertBlock() # New paragraph
        cursor.insertText(text)
        self.editor_textbox.setTextCursor(cursor)



# ============================================================================
# RIGHT PANEL - ASSISTANT
# ============================================================================

class AssistantPanel(QWidget):
    """Right panel - Glass sidebar with AI chat."""
    
    chat_sent = pyqtSignal(str)  # query
    insert_requested = pyqtSignal(str)  # text to insert
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Glass sidebar effect
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        
        self.setProperty("class", "SidebarWidget")
        self.setMinimumWidth(QtTheme.ASSISTANT_WIDTH)
        
        self._setup_ui()
    
    def paintEvent(self, event):
        """Paint dark glass background manually."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(0, 0, 0, 220)
        painter.fillRect(self.rect(), color)
        border_color = QColor(255, 255, 255, 26)
        painter.setPen(border_color)
        painter.drawLine(0, 0, 0, self.height())
        super().paintEvent(event)
    
    def _setup_ui(self):
        """Create assistant panel UI with ScrollArea for bubbles."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. Chat Area (ScrollArea)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")
        
        # Container for messages
        self.chat_container = QWidget()
        self.chat_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(10, 10, 10, 10)
        self.chat_layout.setSpacing(15)
        self.chat_layout.addStretch() # Push messages to bottom initially? No, top.
        
        self.scroll_area.setWidget(self.chat_container)
        layout.addWidget(self.scroll_area, 1)
        
        # 2. Input Area
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(10, 10, 10, 10)
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask about lore...")
        self.chat_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {QtTheme.BG_INPUT};
                border: 1px solid {QtTheme.GLASS_BORDER};
                border-radius: 8px;
                padding: 10px;
                color: {QtTheme.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border: 1px solid {QtTheme.ACCENT_PRIMARY};
                background-color: rgba(15, 18, 22, 0.50);
            }}
        """)
        self.chat_input.returnPressed.connect(self._send_chat)
        input_layout.addWidget(self.chat_input)
        
        layout.addWidget(input_container)

    def _send_chat(self):
        query = self.chat_input.text().strip()
        if query:
            self.add_message(query, "user")
            self.chat_sent.emit(query)
            self.chat_input.clear()

    def add_message(self, text: str, sender: str):
        """Add a message bubble to the chat."""
        # Create container for bubble to handle alignment
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        
        bubble = QFrame()
        bubble.setProperty("class", "MessageBubble")
        
        if sender == "user":
            bubble.setStyleSheet(f"""
                QFrame {{
                    background-color: {QtTheme.ACCENT_PRIMARY};
                    border-radius: 12px;
                    border-bottom-right-radius: 2px;
                    padding: 10px;
                }}
            """)
            row_layout.addStretch()
            row_layout.addWidget(bubble, 8) 
        else:
            bubble.setStyleSheet(f"""
                QFrame {{
                    background-color: {QtTheme.BG_HOVER};
                    border: 1px solid {QtTheme.GLASS_BORDER};
                    border-radius: 12px;
                    border-bottom-left-radius: 2px;
                    padding: 10px;
                }}
            """)
            row_layout.addWidget(bubble, 8)
            row_layout.addStretch()

        # Bubble content
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(5, 5, 5, 5)
        
        msg_label = QLabel(text)
        msg_label.setWordWrap(True)
        msg_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        msg_label.setStyleSheet("border: none; background: transparent; color: white;")
        msg_label.setFont(QtTheme.get_font_ui())
        bubble_layout.addWidget(msg_label)
        
        # Add Insert Button for AI
        if sender == "assistant":
            # Add separator
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setStyleSheet(f"color: {QtTheme.GLASS_BORDER};")
            bubble_layout.addWidget(line)
            
            insert_btn = QPushButton("Insert to Editor")
            insert_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            insert_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {QtTheme.ACCENT_SECONDARY};
                    border: none;
                    text-align: left;
                    font-weight: bold;
                    padding: 5px;
                }}
                QPushButton:hover {{
                    color: white;
                }}
            """)
            insert_btn.clicked.connect(lambda: self.insert_requested.emit(text))
            bubble_layout.addWidget(insert_btn)

        # Add to main layout (remove stretch at bottom first if exists)
        # We used setSpacing, so no stretch needed really.
        # But to keep items at top, we need a stretch at the VERY END of chat_layout.
        
        # Remove the last item (stretch) if it exists, add widget, then add stretch back?
        # Simpler: Just add widget. The layout will fill top to bottom.
        # To align to top, we added addStretch() in setup. 
        # We should insert BEFORE the stretch.
        
        count = self.chat_layout.count()
        if count > 0:
            # Assuming last item is stretch
            self.chat_layout.insertWidget(count - 1, row_widget)
        else:
            self.chat_layout.addWidget(row_widget)
        
        # Auto scroll
        QTimer.singleShot(100, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        sb = self.scroll_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def append_message(self, text: str):
        # Fallback for old calls - treat as AI message
        # But streaming might call this repeatedly?
        # We need to handle streaming. 
        # Ideally StoryBibleApp buffers text and calls add_message once.
        pass


# ============================================================================
# DASHBOARD / HOME VIEW
# ============================================================================

class ProjectCard(QFrame):
    """
    Premium floating glass card for dashboard projects.
    Displays project title, snippet, and metadata with luxurious hover interactions.
    """
    
    clicked = pyqtSignal(int)  # project_id
    rename_requested = pyqtSignal(int, str)  # project_id, current_title
    delete_requested = pyqtSignal(int, str)  # project_id, title (for confirmation)
    duplicate_requested = pyqtSignal(int)  # project_id
    export_requested = pyqtSignal(int)  # project_id
    
    def __init__(self, project_id: int, title: str, snippet: str = "", 
                 word_count: int = 0, last_modified: str = "", parent=None):
        super().__init__(parent)
        self.project_id = project_id
        self.project_title = title
        self._hovered = False
        self._pressed = False
        self._base_pos = None
        
        self.setFixedSize(300, 195)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        self._setup_ui(title, snippet, word_count, last_modified)
        self._setup_animations()
        self._apply_style()
    
    def _setup_ui(self, title: str, snippet: str, word_count: int, last_modified: str):
        """Create refined card content with clear visual hierarchy."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 22)
        layout.setSpacing(10)
        
        # Title - clear and confident
        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.DemiBold))
        self.title_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.95);
            background: transparent;
        """)
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)
        
        # Snippet - muted and supportive
        if snippet:
            snippet_text = snippet[:85] + "..." if len(snippet) > 85 else snippet
        else:
            snippet_text = "Your story awaits..."
        
        self.snippet_label = QLabel(snippet_text)
        self.snippet_label.setFont(QFont("Segoe UI", 11))
        self.snippet_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.5);
            background: transparent;
        """)
        self.snippet_label.setWordWrap(True)
        self.snippet_label.setMaximumHeight(48)
        layout.addWidget(self.snippet_label, 1)
        
        layout.addSpacing(4)
        
        # Subtle divider
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background: rgba(255, 255, 255, 0.06);")
        layout.addWidget(divider)
        
        # Metadata - tertiary importance
        meta_widget = QWidget()
        meta_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        meta_layout = QHBoxLayout(meta_widget)
        meta_layout.setContentsMargins(0, 8, 0, 0)
        meta_layout.setSpacing(14)
        
        meta_style = "color: rgba(255, 255, 255, 0.35); background: transparent;"
        meta_font = QFont("Segoe UI", 10)
        
        if word_count > 0:
            word_label = QLabel(f"◆ {word_count:,} words")
            word_label.setFont(meta_font)
            word_label.setStyleSheet(meta_style)
            meta_layout.addWidget(word_label)
        
        if last_modified:
            date_label = QLabel(f"◇ {last_modified}")
            date_label.setFont(meta_font)
            date_label.setStyleSheet(meta_style)
            meta_layout.addWidget(date_label)
        
        meta_layout.addStretch()
        layout.addWidget(meta_widget)
    
    def _setup_animations(self):
        """Setup VERY STRONG shadows and Y-axis movement."""
        self._base_y = None
        self._hover_lift = 8  # Pixels to move UP on hover
        
        # VERY STRONG shadow - impossible to miss
        self.shadow_effect = QGraphicsDropShadowEffect(self)
        self.shadow_effect.setBlurRadius(35)
        self.shadow_effect.setXOffset(0)
        self.shadow_effect.setYOffset(18)
        self.shadow_effect.setColor(QColor(0, 0, 0, 200))  # 78% opacity - VERY dark
        self.setGraphicsEffect(self.shadow_effect)
    
    def _apply_style(self):
        """Apply elevated card with strong contrast."""
        self.setStyleSheet("""
            ProjectCard {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(75, 75, 95, 255),
                    stop:0.05 rgba(65, 65, 82, 255),
                    stop:1 rgba(45, 45, 60, 255)
                );
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-top: 2px solid rgba(255, 255, 255, 0.35);
                border-radius: 14px;
            }
        """)
    
    def _apply_hover_style(self):
        """Apply brighter hover state."""
        self.setStyleSheet("""
            ProjectCard {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(95, 92, 125, 255),
                    stop:0.05 rgba(82, 78, 108, 255),
                    stop:1 rgba(60, 56, 82, 255)
                );
                border: 1px solid rgba(160, 150, 230, 0.5);
                border-top: 2px solid rgba(200, 190, 255, 0.7);
                border-radius: 14px;
            }
        """)
    
    def _apply_pressed_style(self):
        """Apply pressed state."""
        self.setStyleSheet("""
            ProjectCard {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(70, 68, 90, 255),
                    stop:1 rgba(48, 46, 65, 255)
                );
                border: 1px solid rgba(160, 150, 230, 0.6);
                border-radius: 14px;
            }
        """)
    
    def enterEvent(self, event):
        """Hover - card moves UP and shadow expands."""
        self._hovered = True
        self._apply_hover_style()
        
        # Store base position and move card UP
        if self._base_y is None:
            self._base_y = self.y()
        self.move(self.x(), self._base_y - self._hover_lift)
        
        # Expand shadow dramatically
        self.shadow_effect.setBlurRadius(50)
        self.shadow_effect.setYOffset(28)
        self.shadow_effect.setColor(QColor(0, 0, 0, 220))
        
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Leave - card moves back DOWN."""
        self._hovered = False
        self._apply_style()
        
        # Move card back to original position
        if self._base_y is not None:
            self.move(self.x(), self._base_y)
        
        # Reset shadow
        self.shadow_effect.setBlurRadius(35)
        self.shadow_effect.setYOffset(18)
        self.shadow_effect.setColor(QColor(0, 0, 0, 200))
        
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """Press - card pushes down."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            self._apply_pressed_style()
            
            # Push down effect
            if self._base_y is not None:
                self.move(self.x(), self._base_y + 2)
            self.shadow_effect.setYOffset(8)
            self.shadow_effect.setBlurRadius(20)
            self.shadow_effect.setColor(QColor(0, 0, 0, 160))
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Release - spring back and emit click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = False
            if self._hovered:
                self._apply_hover_style()
                if self._base_y is not None:
                    self.move(self.x(), self._base_y - self._hover_lift)
                self.shadow_effect.setYOffset(28)
                self.shadow_effect.setBlurRadius(50)
                self.shadow_effect.setColor(QColor(0, 0, 0, 220))
            else:
                self._apply_style()
                if self._base_y is not None:
                    self.move(self.x(), self._base_y)
                self.shadow_effect.setYOffset(18)
                self.shadow_effect.setBlurRadius(35)
                self.shadow_effect.setColor(QColor(0, 0, 0, 200))
            self.clicked.emit(self.project_id)
        super().mouseReleaseEvent(event)
    
    def _show_context_menu(self, pos):
        """Show right-click context menu with project actions."""
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: rgba(25, 25, 30, 250);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 10px;
                padding: 6px;
            }}
            QMenu::item {{
                background-color: transparent;
                color: {QtTheme.TEXT_PRIMARY};
                padding: 10px 24px;
                border-radius: 6px;
                font-size: 13px;
            }}
            QMenu::item:selected {{
                background-color: rgba(79, 70, 229, 0.3);
            }}
            QMenu::separator {{
                height: 1px;
                background-color: rgba(255, 255, 255, 0.08);
                margin: 4px 12px;
            }}
        """)
        
        # Open action
        open_action = menu.addAction("📂  Open")
        open_action.triggered.connect(lambda: self.clicked.emit(self.project_id))
        
        menu.addSeparator()
        
        # Rename action
        rename_action = menu.addAction("✏️  Rename")
        rename_action.triggered.connect(lambda: self.rename_requested.emit(self.project_id, self.project_title))
        
        # Duplicate action
        duplicate_action = menu.addAction("📋  Duplicate")
        duplicate_action.triggered.connect(lambda: self.duplicate_requested.emit(self.project_id))
        
        # Export action
        export_action = menu.addAction("📤  Export")
        export_action.triggered.connect(lambda: self.export_requested.emit(self.project_id))
        
        menu.addSeparator()
        
        # Delete action (with warning color)
        delete_action = menu.addAction("🗑️  Delete")
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.project_id, self.project_title))
        
        # Show menu at cursor position
        menu.exec(self.mapToGlobal(pos))


class ActionCard(QFrame):
    """
    Premium floating glass action card for New Project and Import Project.
    More prominent than regular cards with subtle accent glow.
    """
    
    clicked = pyqtSignal()
    
    def __init__(self, card_type: str = "new", parent=None):
        """
        Args:
            card_type: "new" for New Project, "import" for Import Project
        """
        super().__init__(parent)
        self.card_type = card_type
        self._hovered = False
        self._pressed = False
        
        self.setFixedSize(300, 195)  # Match ProjectCard size
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._setup_ui()
        self._setup_animations()
        self._apply_style()
    
    def _setup_ui(self):
        """Create refined action card with clear visual hierarchy."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 28, 26, 24)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Icon with soft glow effect
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setFixedSize(52, 52)
        
        if self.card_type == "new":
            self.icon_label.setText("✦")
            self.icon_label.setFont(QFont("Segoe UI Symbol", 28))
            self.icon_label.setStyleSheet("""
                color: rgba(167, 139, 250, 0.9);
                background: transparent;
            """)
            title_text = "New Project"
            subtitle_text = "Start something beautiful"
            self._accent_color = (147, 120, 230)  # Soft purple
        else:
            self.icon_label.setText("↓")
            self.icon_label.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
            self.icon_label.setStyleSheet("""
                color: rgba(100, 160, 240, 0.9);
                background: transparent;
            """)
            title_text = "Import Project"
            subtitle_text = "Continue your work"
            self._accent_color = (90, 145, 220)  # Soft blue
        
        layout.addWidget(self.icon_label, 0, Qt.AlignmentFlag.AlignCenter)
        
        layout.addSpacing(2)
        
        # Title - primary emphasis
        self.title_label = QLabel(title_text)
        self.title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.DemiBold))
        self.title_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.95);
            background: transparent;
        """)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Subtitle - muted
        self.subtitle_label = QLabel(subtitle_text)
        self.subtitle_label.setFont(QFont("Segoe UI", 11))
        self.subtitle_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.45);
            background: transparent;
        """)
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.subtitle_label)
    
    def _setup_animations(self):
        """Setup VERY STRONG shadows and Y-axis movement."""
        self._base_y = None
        self._hover_lift = 8  # Pixels to move UP on hover
        
        # VERY STRONG accent-tinted shadow
        self.shadow_effect = QGraphicsDropShadowEffect(self)
        self.shadow_effect.setBlurRadius(35)
        self.shadow_effect.setXOffset(0)
        self.shadow_effect.setYOffset(18)
        
        r, g, b = self._accent_color
        self.shadow_effect.setColor(QColor(r // 2, g // 2, b // 2, 180))
        self.setGraphicsEffect(self.shadow_effect)
    
    def _apply_style(self):
        """Apply elevated card with accent border."""
        r, g, b = self._accent_color
        self.setStyleSheet(f"""
            ActionCard {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(72, 68, 95, 255),
                    stop:0.05 rgba(62, 58, 82, 255),
                    stop:1 rgba(45, 42, 62, 255)
                );
                border: 1px solid rgba({r}, {g}, {b}, 0.3);
                border-top: 2px solid rgba({r}, {g}, {b}, 0.55);
                border-radius: 14px;
            }}
        """)
    
    def _apply_hover_style(self):
        """Apply brighter hover state."""
        r, g, b = self._accent_color
        self.setStyleSheet(f"""
            ActionCard {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(92, 88, 120, 255),
                    stop:0.05 rgba(78, 74, 105, 255),
                    stop:1 rgba(58, 55, 80, 255)
                );
                border: 1px solid rgba({r}, {g}, {b}, 0.6);
                border-top: 2px solid rgba({r}, {g}, {b}, 0.85);
                border-radius: 14px;
            }}
        """)
    
    def _apply_pressed_style(self):
        """Apply pressed state."""
        r, g, b = self._accent_color
        self.setStyleSheet(f"""
            ActionCard {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(68, 65, 88, 255),
                    stop:1 rgba(48, 45, 65, 255)
                );
                border: 1px solid rgba({r}, {g}, {b}, 0.65);
                border-radius: 14px;
            }}
        """)
    
    def enterEvent(self, event):
        """Hover - card moves UP and shadow expands."""
        self._hovered = True
        self._apply_hover_style()
        
        # Store base position and move card UP
        if self._base_y is None:
            self._base_y = self.y()
        self.move(self.x(), self._base_y - self._hover_lift)
        
        # Expand shadow dramatically
        r, g, b = self._accent_color
        self.shadow_effect.setBlurRadius(50)
        self.shadow_effect.setYOffset(28)
        self.shadow_effect.setColor(QColor(r // 2, g // 2, b // 2, 210))
        
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Leave - card moves back DOWN."""
        self._hovered = False
        self._apply_style()
        
        # Move card back to original position
        if self._base_y is not None:
            self.move(self.x(), self._base_y)
        
        # Reset shadow
        r, g, b = self._accent_color
        self.shadow_effect.setBlurRadius(35)
        self.shadow_effect.setYOffset(18)
        self.shadow_effect.setColor(QColor(r // 2, g // 2, b // 2, 180))
        
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """Press - card pushes down."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            self._apply_pressed_style()
            
            # Push down effect
            if self._base_y is not None:
                self.move(self.x(), self._base_y + 2)
            r, g, b = self._accent_color
            self.shadow_effect.setYOffset(8)
            self.shadow_effect.setBlurRadius(20)
            self.shadow_effect.setColor(QColor(r // 3, g // 3, b // 3, 140))
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Release - spring back and emit click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = False
            r, g, b = self._accent_color
            if self._hovered:
                self._apply_hover_style()
                if self._base_y is not None:
                    self.move(self.x(), self._base_y - self._hover_lift)
                self.shadow_effect.setYOffset(28)
                self.shadow_effect.setBlurRadius(50)
                self.shadow_effect.setColor(QColor(r // 2, g // 2, b // 2, 210))
            else:
                self._apply_style()
                if self._base_y is not None:
                    self.move(self.x(), self._base_y)
                self.shadow_effect.setYOffset(18)
                self.shadow_effect.setBlurRadius(35)
                self.shadow_effect.setColor(QColor(r // 2, g // 2, b // 2, 180))
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class DashboardHeader(QWidget):
    """
    Dashboard header with title and global action buttons.
    """
    
    new_project_clicked = pyqtSignal()
    import_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(80)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 10)
        
        # Left: Title
        title = QLabel("My Stories")
        title.setFont(QFont("Inter", 24, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {QtTheme.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Right: Action buttons
        btn_style = f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                color: {QtTheme.TEXT_SECONDARY};
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(79, 70, 229, 0.4);
                color: {QtTheme.TEXT_PRIMARY};
            }}
            QPushButton:pressed {{
                background-color: rgba(79, 70, 229, 0.2);
            }}
        """
        
        new_btn = QPushButton("＋ New Project")
        new_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {QtTheme.ACCENT_PRIMARY};
                border: none;
                border-radius: 10px;
                color: white;
                padding: 10px 22px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {QtTheme.ACCENT_HOVER};
            }}
            QPushButton:pressed {{
                background-color: #3730a3;
            }}
        """)
        new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_btn.clicked.connect(self.new_project_clicked.emit)
        layout.addWidget(new_btn)
        
        import_btn = QPushButton("⤓ Import")
        import_btn.setStyleSheet(btn_style)
        import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        import_btn.clicked.connect(self.import_clicked.emit)
        layout.addWidget(import_btn)
        
        settings_btn = QPushButton("⚙")
        settings_btn.setFixedSize(42, 42)
        settings_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                color: {QtTheme.TEXT_MUTED};
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
                color: {QtTheme.TEXT_PRIMARY};
            }}
        """)
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(settings_btn)


class EmptyStatePlaceholder(QWidget):
    """
    Shown when no projects exist - friendly welcome message with dual CTAs.
    """
    
    new_project_clicked = pyqtSignal()
    import_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(24)
        
        # Icon/Illustration placeholder
        icon_label = QLabel("✨")
        icon_label.setFont(QFont("Segoe UI Emoji", 64))
        icon_label.setStyleSheet(f"color: {QtTheme.ACCENT_PRIMARY}; background: transparent;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # Title
        title = QLabel("Your writing journey starts here")
        title.setFont(QFont("Inter", 24, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {QtTheme.TEXT_PRIMARY}; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Create a new project or import existing work to begin")
        subtitle.setFont(QFont("Inter", 14))
        subtitle.setStyleSheet(f"color: {QtTheme.TEXT_MUTED}; background: transparent;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # Buttons container
        btn_container = QWidget()
        btn_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_layout.setSpacing(16)
        
        # New Project Button (primary)
        new_btn = QPushButton("✦  New Project")
        new_btn.setFixedSize(180, 50)
        new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {QtTheme.ACCENT_PRIMARY};
                border: none;
                border-radius: 12px;
                color: white;
                font-size: 15px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {QtTheme.ACCENT_HOVER};
            }}
            QPushButton:pressed {{
                background-color: #3730a3;
            }}
        """)
        new_btn.clicked.connect(self.new_project_clicked.emit)
        btn_layout.addWidget(new_btn)
        
        # Import Button (secondary)
        import_btn = QPushButton("⤓  Import Project")
        import_btn.setFixedSize(180, 50)
        import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        import_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 12px;
                color: {QtTheme.TEXT_SECONDARY};
                font-size: 15px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(139, 92, 246, 0.4);
                color: {QtTheme.TEXT_PRIMARY};
            }}
            QPushButton:pressed {{
                background-color: rgba(139, 92, 246, 0.2);
            }}
        """)
        import_btn.clicked.connect(self.import_clicked.emit)
        btn_layout.addWidget(import_btn)
        
        layout.addWidget(btn_container)
        
        # Hint text
        hint = QLabel("Supports .txt, .md, and .docx files")
        hint.setFont(QFont("Inter", 11))
        hint.setStyleSheet(f"color: {QtTheme.TEXT_MUTED}; background: transparent;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)


class FlowLayout(QVBoxLayout):
    """
    Custom layout that wraps items horizontally like a flow layout.
    Uses a grid approach with dynamic column count.
    """
    pass  # We'll use QGridLayout with dynamic columns instead


class DashboardView(QWidget):
    """
    Main dashboard/home view with responsive project grid.
    Features action cards for New/Import and existing project cards with context menus.
    """
    
    project_selected = pyqtSignal(int)  # project_id
    new_project_requested = pyqtSignal()
    import_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    rename_project_requested = pyqtSignal(int, str)  # project_id, current_title
    delete_project_requested = pyqtSignal(int, str)  # project_id, title
    duplicate_project_requested = pyqtSignal(int)  # project_id
    export_project_requested = pyqtSignal(int)  # project_id
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.project_cards = []
        self.action_cards = []  # New/Import cards
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        
        self._setup_ui()
    
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        self.header = DashboardHeader()
        self.header.new_project_clicked.connect(self.new_project_requested.emit)
        self.header.import_clicked.connect(self.import_requested.emit)
        self.header.settings_clicked.connect(self.settings_requested.emit)
        main_layout.addWidget(self.header)
        
        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll.viewport().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        scroll.viewport().setStyleSheet("background: transparent;")
        
        # Content container - this will be centered
        self.content_widget = QWidget()
        self.content_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(60, 60, 60, 60)  # Generous margins
        self.content_layout.setSpacing(0)
        
        # Top spacer for vertical centering (flexible)
        self.content_layout.addStretch(1)
        
        # Center container - holds the grid, horizontally centered
        center_container = QWidget()
        center_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        center_layout = QHBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)
        
        # Left spacer for horizontal centering
        center_layout.addStretch(1)
        
        # Grid container for cards - MUST have large margins for shadows + hover lift
        self.grid_widget = QWidget()
        self.grid_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(40)  # More space between cards for shadows
        # CRITICAL: Large margins for shadow visibility AND hover lift movement
        self.grid_layout.setContentsMargins(50, 50, 50, 50)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        center_layout.addWidget(self.grid_widget)
        
        # Right spacer for horizontal centering
        center_layout.addStretch(1)
        
        self.content_layout.addWidget(center_container)
        
        # Empty state placeholder (also centered)
        self.empty_state = EmptyStatePlaceholder()
        self.empty_state.new_project_clicked.connect(self.new_project_requested.emit)
        self.empty_state.import_clicked.connect(self.import_requested.emit)
        self.content_layout.addWidget(self.empty_state, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Bottom spacer for vertical centering (flexible, slightly larger for upper-middle feel)
        self.content_layout.addStretch(2)
        
        scroll.setWidget(self.content_widget)
        main_layout.addWidget(scroll, 1)
    
    def paintEvent(self, event):
        """Paint dark background for card contrast."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Darker background = more visible card elevation
        color = QColor(18, 18, 24, 240)  # Very dark, slight transparency
        painter.fillRect(self.rect(), color)
        super().paintEvent(event)
    
    def load_projects(self):
        """Load and display all projects from database."""
        # Clear existing project cards
        for card in self.project_cards:
            card.deleteLater()
        self.project_cards.clear()
        
        # Clear action cards
        for card in self.action_cards:
            card.deleteLater()
        self.action_cards.clear()
        
        # Clear grid layout
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Fetch projects using the correct method name
        projects = self.db_manager.get_projects_with_chapters() if self.db_manager else []
        
        # Always show grid (action cards are always present)
        self.empty_state.hide()
        self.grid_widget.show()
        
        # Arrange cards (action cards + project cards)
        self._arrange_cards(projects)
    
    def _arrange_cards(self, projects):
        """Arrange action cards and project cards in a responsive grid."""
        # Card dimensions
        card_width = 300
        card_spacing = 40  # Match grid spacing
        available_width = self.width() - 220  # Account for all margins
        
        # Calculate columns (max 4 for visual balance)
        cols = min(4, max(1, (available_width + card_spacing) // (card_width + card_spacing)))
        
        card_index = 0  # Global index for grid position
        
        # === ACTION CARDS (always first) ===
        # New Project card
        new_card = ActionCard(card_type="new")
        new_card.clicked.connect(self.new_project_requested.emit)
        row, col = card_index // cols, card_index % cols
        self.grid_layout.addWidget(new_card, row, col)
        self.action_cards.append(new_card)
        QTimer.singleShot(50 * card_index, lambda c=new_card: self._animate_card_in(c))
        card_index += 1
        
        # Import Project card
        import_card = ActionCard(card_type="import")
        import_card.clicked.connect(self.import_requested.emit)
        row, col = card_index // cols, card_index % cols
        self.grid_layout.addWidget(import_card, row, col)
        self.action_cards.append(import_card)
        QTimer.singleShot(50 * card_index, lambda c=import_card: self._animate_card_in(c))
        card_index += 1
        
        # === PROJECT CARDS ===
        for project in projects:
            row, col = card_index // cols, card_index % cols
            
            # Extract project data
            project_id = project.get('id', project.get('project_id', 0))
            title = project.get('name', project.get('title', 'Untitled'))
            snippet = project.get('snippet', project.get('description', ''))
            word_count = project.get('word_count', 0)
            last_modified = project.get('updated_at', project.get('last_modified', ''))
            
            # Format date if present
            if last_modified and isinstance(last_modified, str) and len(last_modified) > 10:
                last_modified = last_modified[:10]
            
            card = ProjectCard(
                project_id=project_id,
                title=title,
                snippet=snippet,
                word_count=word_count,
                last_modified=last_modified
            )
            # Connect signals
            card.clicked.connect(self.project_selected.emit)
            card.rename_requested.connect(self.rename_project_requested.emit)
            card.delete_requested.connect(self.delete_project_requested.emit)
            card.duplicate_requested.connect(self.duplicate_project_requested.emit)
            card.export_requested.connect(self.export_project_requested.emit)
            
            self.grid_layout.addWidget(card, row, col)
            self.project_cards.append(card)
            
            # Animate card entrance with stagger
            QTimer.singleShot(50 * card_index, lambda c=card: self._animate_card_in(c))
            card_index += 1
    
    def _animate_card_in(self, card):
        """Animate a single card fading in."""
        try:
            # Check if card still exists (may have been deleted during resize)
            from PyQt6 import sip
            if sip.isdeleted(card):
                return
        except (RuntimeError, ImportError):
            # Card was deleted or sip not available - skip animation
            try:
                # Fallback check - try accessing a property
                _ = card.isVisible()
            except RuntimeError:
                return
        
        try:
            anim = QPropertyAnimation(card, b"windowOpacity")
            anim.setDuration(200)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.Type.OutQuad)
            anim.start()
            # Keep reference to prevent garbage collection
            card._fade_anim = anim
        except RuntimeError:
            # Card was deleted between check and animation - ignore
            pass
    
    def resizeEvent(self, event):
        """Handle resize - rearrange grid."""
        super().resizeEvent(event)
        # Debounce resize handling
        if hasattr(self, '_resize_timer'):
            self._resize_timer.stop()
        else:
            self._resize_timer = QTimer()
            self._resize_timer.setSingleShot(True)
            self._resize_timer.timeout.connect(self.load_projects)
        self._resize_timer.start(100)


# ============================================================================
# MAIN APPLICATION WINDOW
# ============================================================================

class StoryBibleApp(QMainWindow):
    """
    Main application window - complete PyQt6 implementation.
    NO Tkinter/CustomTkinter dependencies.
    """
    
    def __init__(self, ai_engine, db_manager):
        super().__init__()
        
        self.ai_engine = ai_engine
        self.db_manager = db_manager
        
        self.current_project_id = None
        self.current_chapter_id = None
        self.is_generating = False
        self.response_queue = queue.Queue()
        self.target_panel = None
        self.current_ai_response_text = ""
        
        self._setup_window()
        self._create_ui()
        self._connect_signals()
        self._start_timers()
        
        self.load_session()
    
    def _setup_window(self):
        """Configure main window for GLASS UI with transparency."""
        self.setWindowTitle("Story Bible Pro - AI Writing Assistant")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Enable transparency support
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)  # Main window paints background
        
        self.setPalette(QtTheme.create_dark_palette())
        self.setStyleSheet(QtTheme.get_global_stylesheet())
    
    def _create_ui(self):
        """Create the main UI structure with Dashboard + Editor views."""
        # Background widget as central widget
        self.background_widget = BackgroundWidget()
        self.setCentralWidget(self.background_widget)
        
        # Main layout
        main_layout = QVBoxLayout(self.background_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Toolbar (fixed at top) - hidden on dashboard
        self.toolbar = ToolbarWidget()
        main_layout.addWidget(self.toolbar)
        
        # Stacked widget for view switching (Dashboard vs Editor)
        self.view_stack = QStackedWidget()
        self.view_stack.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # =====================
        # VIEW 0: DASHBOARD
        # =====================
        self.dashboard_view = DashboardView(self.db_manager)
        self.dashboard_view.project_selected.connect(self._open_project)
        self.dashboard_view.new_project_requested.connect(self._create_new_project)
        self.dashboard_view.import_requested.connect(self._show_import_dialog)
        self.dashboard_view.settings_requested.connect(self._show_settings)
        # Context menu actions
        self.dashboard_view.rename_project_requested.connect(self._rename_project)
        self.dashboard_view.delete_project_requested.connect(self._delete_project_with_confirm)
        self.dashboard_view.duplicate_project_requested.connect(self._duplicate_project)
        self.dashboard_view.export_project_requested.connect(self._export_project)
        self.view_stack.addWidget(self.dashboard_view)
        
        # =====================
        # VIEW 1: EDITOR (3-column layout)
        # =====================
        self.editor_view = QWidget()
        self.editor_view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.editor_view.setAutoFillBackground(False)
        self.editor_view.setStyleSheet("background-color: transparent;")
        editor_layout = QHBoxLayout(self.editor_view)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)
        
        # Editor Panels (Left, Center, Right)
        self.left_panel = ProjectSidebar(self.db_manager)
        self.center_panel = CenterPanel(self.db_manager, self.ai_engine)
        self.right_panel = AssistantPanel()
        
        # Splitter Layout
        self.main_splitter = MainWorkspaceSplitter(self.left_panel, self.center_panel, self.right_panel)
        self.editor_view.layout().addWidget(self.main_splitter)
        
        self.view_stack.addWidget(self.editor_view)
        
        main_layout.addWidget(self.view_stack, 1)
        
        # Start on dashboard
        self._show_dashboard()
    
    def _connect_signals(self):
        """Connect signals and slots."""
        self.toolbar.action_triggered.connect(self._handle_toolbar_action)
        self.toolbar.home_clicked.connect(self._go_back_to_dashboard)
        self.left_panel.chapter_selected.connect(self._load_chapter)
        self.left_panel.bible_section_clicked.connect(self._scroll_to_bible_section)
        self.left_panel.trash_clicked.connect(self._show_trash)
        self.center_panel.content_changed.connect(self._on_content_change)
        self.center_panel.action_requested.connect(self._handle_action)
        self.right_panel.chat_sent.connect(self._handle_chat)
        self.right_panel.insert_requested.connect(self.insert_text_to_editor)
    
    def insert_text_to_editor(self, text):
        if hasattr(self, 'last_action_type') and self.last_action_type == 'expand':
            self.center_panel.append_text_below_selection(text)
        else:
            self.center_panel.replace_selected_text(text)
        
    def _start_timers(self):
        """Start background timers."""
        # Queue checker
        self.queue_timer = QTimer()
        self.queue_timer.timeout.connect(self._check_queue)
        self.queue_timer.start(50)
        
        # Auto-save
        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self._auto_save)
        self.save_timer.start(30000)
    
    # ========================================================================
    # SLOT IMPLEMENTATIONS
    # ========================================================================
    
    @pyqtSlot(str, str)
    def _handle_toolbar_action(self, action: str, item: str):
        """Handle toolbar button actions."""
        # logging.info(f"Toolbar action: {action} - {item}")
        
        if action == "write":
            # Handle Write Modes
            mode = item # "Auto", "Guided", "Tone Shift", etc.
            
            # 1. Get Context (Selected text or last paragraph)
            context = self.center_panel.get_selected_text()
            if not context:
               context = self.center_panel.get_editor_content() # Fallback to all content or last para logic handled in thread
            
            # 2. Construct Prompt
            prompt = f"WRITE_WITH_MODE::{mode}::{context}"
            
            # 3. Send to LORE CHAT (Assistant), NOT Editor
            # Requirement: "Displays the generated response in Lore Chat... The response appears with an Insert button"
            self._handle_ai_request(prompt, 'assistant')

        elif action == "rewrite":
            self._handle_ai_request(f"PLUGIN::rewrite_{item.lower().replace(' ', '_')}::", 'editor')
        elif action == "describe":
            # 1. Validation: Require selection
            selected_text = self.center_panel.get_selected_text()
            if not selected_text.strip():
                # Non-blocking warning as requested
                QMessageBox.warning(self, "Selection Required", "Please select text to describe.")
                return

            # 2. Parse Active Senses from item payload (comma-separated)
            # item contains something like "Sight,Sound,Touch"
            active_senses = [sense.strip() for sense in item.split(",")] if item else []
            
            # 3. Construct Prompt
            prompt = f"DESCRIBE::{selected_text}"
            if active_senses:
                prompt += f"::SENSES::{','.join(active_senses)}"
            
            self._handle_ai_request(prompt, 'assistant')

        elif action == "more_tools":
            # 1. Validation: Require selection
            selected_text = self.center_panel.get_selected_text()
            if not selected_text.strip():
                # Non-blocking warning
                QMessageBox.warning(self, "Selection Required", "Please select text first.")
                return

            if item == "Visualize":
                # Dummy action - Direct message to Lore Chat (Assistant)
                # Since we want it to look like an AI response, we can add it directly.
                self.right_panel.add_message("Visualize is not implemented yet.", "assistant")
            elif item == "Twist":
                prompt = f"TRANSFORM::TWIST::{selected_text}"
                self._handle_ai_request(prompt, 'assistant')
            elif item == "Poem":
                prompt = f"TRANSFORM::POEM::{selected_text}"
                self._handle_ai_request(prompt, 'assistant')
            elif item == "export":
                self._export_document()

        elif action == "brainstorm":
            self._handle_ai_request(f"Brainstorm: {item}", 'assistant')
        elif action == "export":
            self._export_document()
        elif action == "help":
            self._show_help()
        elif action == "settings":
            # logging.info("Settings clicked")
            pass
    
    @pyqtSlot(int, int)
    def _load_chapter(self, chapter_id: int, project_id: int):
        """Load chapter into center panel."""
        self.current_chapter_id = chapter_id
        self.current_project_id = project_id
        
        self.center_panel.load_project(project_id, chapter_id)
        self._on_content_change()
        
        self.left_panel.refresh_tree(chapter_id, project_id=project_id)
    
    @pyqtSlot(str)
    def _scroll_to_bible_section(self, section: str):
        """Scroll to Story Bible section."""
        if not self.center_panel.story_bible_container:
            # Bible not open - create it
            self.center_panel.create_story_bible_container()
            if self.current_project_id:
                self.center_panel.load_project(self.current_project_id, self.current_chapter_id)
        
        self.center_panel.scroll_to_section(section)
    
    @pyqtSlot()
    def _show_trash(self):
        """Show trash/deleted items."""
        # logging.info("Show trash clicked")
    
    @pyqtSlot()
    def _on_content_change(self):
        """Handle content changes."""
        try:
            text = self.center_panel.get_editor_content()
            word_count = len(text.split())
            self.toolbar.update_word_count(word_count)
        except:
            pass
    
    @pyqtSlot(str)
    def _handle_action(self, action: str):
        """Handle action button clicks."""
        if action == "generate_draft":
            self._handle_ai_request("Generate a rough draft of this chapter", 'editor')
        elif action == "generate_openings":
            self._handle_ai_request("Generate 3 different opening paragraphs", 'editor')
        elif action == "chat_idea":
            self.right_panel.chat_input.setFocus()
        elif action.startswith("CONTEXT_"):
            # Set action type for insertion logic
            if "REWRITE" in action: self.last_action_type = "rewrite"
            elif "DESCRIBE" in action: self.last_action_type = "describe"
            elif "EXPAND" in action: self.last_action_type = "expand"
            else: self.last_action_type = "other"
            
            # Note: For DESCRIBE, action contains "CONTEXT_DESCRIBE::text::senses"
            self._handle_ai_request(action, 'assistant')
    
    @pyqtSlot(str)
    def _handle_chat(self, query: str):
        """Handle chat query."""
        self._handle_ai_request(query, 'assistant')
    
    @pyqtSlot()
    def _check_queue(self):
        """Check AI response queue for tokens."""
        try:
            while True:
                token = self.response_queue.get_nowait()
                if token == "[[END]]":
                    self.is_generating = False
                    self.toolbar.set_save_status(True)
                    
                    # If target was assistant, finalize the message bubble
                    if self.target_panel == 'assistant':
                        # Clean up formatting if needed
                        final_text = self.current_ai_response_text.strip()
                        if final_text:
                            self.right_panel.add_message(final_text, "assistant")
                        # Reset for next time
                        self.current_ai_response_text = ""
                    elif self.target_panel == 'editor':
                        # TRIGGER PIPELINE: Immediate Summarization for Canvas
                        # Force check (since we just generated text)
                        # We notify SmartEditor that AI finished so it can start debounce
                        if hasattr(self.center_panel.editor_textbox, 'handle_ai_completion'):
                            self.center_panel.editor_textbox.handle_ai_completion()
                        else:
                             # Fallback if for some reason it's not smart
                            pass
                    
                else:
                    if self.target_panel == 'editor':
                        self.center_panel.insert_editor_content(token)
                    elif self.target_panel == 'assistant':
                        # Accumulate tokens
                        self.current_ai_response_text += token
                        # We don't stream directly to UI anymore to allow bubble creation at end?
                        # Or we could update a "streaming" bubble.
                        # For "clear separation", buffering and showing at end is safest for now.
                        # User wants "answers given... merging... add insert button after EACH response".
                        pass
        except queue.Empty:
            pass

    
    @pyqtSlot()
    def _auto_save(self):
        """Auto-save current content."""
        if self.current_chapter_id:
            text = self.center_panel.get_editor_content()
            self.db_manager.update_chapter_content(self.current_chapter_id, text)
            # No need to manually trigger summarization; 
            # SmartEditor handles it on focus loss/debounce.
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _handle_ai_request(self, prompt: str, target: str):
        """Handle AI generation request."""
        if self.is_generating:
            return
        
        self.is_generating = True
        self.target_panel = target
        self.toolbar.set_save_status(False)
        
        current_text = self.center_panel.get_editor_content() if target == 'editor' else ""
        
        threading.Thread(
            target=self._ai_thread,
            args=(prompt, target, current_text),
            daemon=True
        ).start()
    
    def _ai_thread(self, prompt: str, target: str, context: str):
        """AI generation thread."""
        try:
            if prompt.startswith("WRITE_WITH_MODE::"):
                # Handle Write Button modes
                mode = prompt.split("::")[1]
                instruction = "Continue the story naturally."
                style = None
                
                if mode == "Guided":
                    instruction = "Continue the story, guiding the narrative towards a resolution."
                elif mode == "Tone Shift":
                    instruction = "Continue the story but shift the tone to be more dramatic and intense."
                elif mode == "Auto":
                    instruction = "Continue the story naturally from the current text."
                
                # Strict Output Rule enforcement
                instruction += " Output ONLY the generated story text. No headers, no preambles, no 'Here is the text'."
                
                self.ai_engine.stream_response(
                    instruction, 
                    self.response_queue, 
                    current_text=context,
                    style=style
                )
            
            elif prompt.startswith("DESCRIBE::"):
                # Handle Describe request
                parts = prompt.split("::SENSES::")
                text_to_describe = parts[0].replace("DESCRIBE::", "")
                active_senses = parts[1].split(",") if len(parts) > 1 else []
                
                instruction = "Rewrite the provided text adding rich sensory details."
                if active_senses:
                    instruction += f" Focus strictly on: {', '.join(active_senses)}."
                else:
                    instruction += " Use a neutral, descriptive style."
                
                instruction += " Output ONLY the rewritten text. Do not include original text if not part of the rewrite."
                
                self.ai_engine.stream_response(
                    instruction,
                    self.response_queue,
                    current_text=text_to_describe
                )

            elif prompt.startswith("TRANSFORM::"):
                # Handle More Tools requests
                parts = prompt.split("::")
                # parts[0] = TRANSFORM, parts[1] = TYPE, parts[2] = TEXT
                t_type = parts[1]
                text_to_transform = parts[2]
                
                instruction = ""
                if t_type == "TWIST":
                    instruction = "Rewrite the provided text with a creative narrative twist, change of perspective, or unexpected shift."
                elif t_type == "POEM":
                    instruction = "Rewrite the provided text as a poem."
                
                instruction += " Output ONLY the transformed text. No headers, no explanations."
                
                self.ai_engine.stream_response(
                    instruction,
                    self.response_queue,
                    current_text=text_to_transform
                )

            elif prompt.startswith("CONTEXT_REWRITE::"):
                text = prompt.split("::", 1)[1]
                instruction = "Rewrite the following text with a random new literary style while preserving its original meaning. Output ONLY the rewritten text. NO headers."
                self.ai_engine.stream_response(instruction, self.response_queue, current_text=text)

            elif prompt.startswith("CONTEXT_DESCRIBE::"):
                text = prompt.split("::", 1)[1]
                instruction = "Expand the following text with vivid sensory details (sight, sound, smell, taste, touch) and metaphors. Output ONLY the descriptive expansion. NO headers."
                self.ai_engine.stream_response(instruction, self.response_queue, current_text=text)

            elif prompt.startswith("CONTEXT_EXPAND::"):
                text = prompt.split("::", 1)[1]
                instruction = "Naturally expand the following paragraph by adding a few more sentences that follow the same tone and direction. Output ONLY the expansion text. NO headers."
                self.ai_engine.stream_response(instruction, self.response_queue, current_text=text)

            elif target == 'editor':
                self.ai_engine.stream_response(prompt, self.response_queue, "", context)
            elif target == 'assistant':
                project_memory = ""
                if self.current_project_id:
                    project_memory = self.db_manager.get_deep_memory(self.current_project_id, prompt)
                self.ai_engine.ask_lore_assistant(prompt, self.response_queue, project_memory, "Current Project")
        except Exception as e:
            self.response_queue.put(f"Error: {e}")
            self.response_queue.put("[[END]]")
    
    def _export_document(self):
        """Export entire book to PDF with chapter bookmarks."""
        if not self.current_project_id:
            QMessageBox.warning(self, "Export", "No project selected.")
            return

        # Get project info
        project_settings = self.db_manager.get_project_settings(self.current_project_id)
        project_name = project_settings.get('name', 'My_Story') if project_settings else 'My_Story'
        
        # Select save location
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Book to PDF", 
            f"{project_name}.pdf", 
            "PDF Files (*.pdf)"
        )
        
        if not file_path:
            return

        try:
            from fpdf import FPDF
            
            # Fetch content
            chapters = self.db_manager.get_full_project_content(self.current_project_id)
            if not chapters:
                QMessageBox.warning(self, "Export", "The project has no chapters to export.")
                return

            # Add Unicode Font
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            
            # Try to load a Unicode font
            import os
            font_path = "/usr/share/fonts/TTF/DejaVuSans.ttf"
            font_name = "Helvetica" # Fallback
            
            if os.path.exists(font_path):
                try:
                    pdf.add_font("DejaVu", "", font_path)
                    font_name = "DejaVu"
                    logging.info("PDF Export: Using Unicode font 'DejaVu'")
                except Exception as e:
                    logging.error(f"Failed to load Unicode font: {e}")
            
            # Add Title Page
            pdf.add_page()
            pdf.set_font(font_name, "", 24)
            pdf.ln(80)
            
            # Use 'effective_page_width' logic manually for centering if needed, but cell(0) works for full width
            pdf.cell(0, 20, project_name, align="C")
            pdf.ln(20)
            pdf.set_font(font_name, "", 14)
            pdf.cell(0, 10, "Generated by Story Bible Pro", align="C")
            
            # Add Chapters
            for chapter in chapters:
                title = chapter.get('title', 'Untitled Chapter')
                content = chapter.get('content', '')
                
                pdf.add_page()
                
                pdf.add_page()
                
                # Create Bookmark (Outline Item)
                pdf.set_font(font_name, "", 18)
                pdf.start_section(title)
                
                # Render Title
                pdf.cell(0, 15, title, ln=True, align="L")
                pdf.ln(5)
                
                # Content
                pdf.set_font(font_name, "", 12)
                # Ensure content is string and not empty
                text = str(content) if content else ""
                
                # fpdf2 handles basic UTF-8 better if we use standard fonts with multi_cell
                # but to be safe with smart quotes etc., we can do a simple replacement
                text = text.replace('\u201c', '"').replace('\u201d', '"')
                text = text.replace('\u2018', "'").replace('\u2019', "'")
                text = text.replace('\u2014', '--')
                
                # Output content
                pdf.multi_cell(0, 7, text)
            
            # Save PDF
            pdf.output(file_path)
            
            QMessageBox.information(self, "Export", f"Book exported successfully to:\n{file_path}")
            # logging.info(f"Project {self.current_project_id} exported to {file_path}")
            
        except Exception as e:
            logging.error(f"Failed to export PDF: {e}")
            QMessageBox.critical(self, "Export Error", f"Failed to generate PDF:\n{str(e)}")
    
    def _show_help(self):
        """Show help dialog."""
        QMessageBox.information(self, "Help", "Story Bible Pro - AI Writing Assistant")
    
    # ========================================================================
    # DASHBOARD / VIEW NAVIGATION
    # ========================================================================
    
    def _show_dashboard(self):
        """Switch to dashboard view."""
        self.toolbar.hide()
        self.dashboard_view.load_projects()
        self.view_stack.setCurrentIndex(0)
    
    def _show_editor(self):
        """Switch to editor view."""
        self.toolbar.show()
        self.view_stack.setCurrentIndex(1)
    
    def _open_project(self, project_id: int):
        """Open a project from dashboard."""
        # Save layout before switching
        if hasattr(self, 'main_splitter'):
            self.main_splitter.save_sizes()
            
        self.current_project_id = project_id
        
        # Refresh sidebar tree - show only this project
        self.left_panel.refresh_tree(project_id=project_id)
        
        # Load first chapter if exists
        chapters = self.db_manager.get_chapters(project_id)
        if chapters:
            first_chapter = chapters[0]
            chapter_id = first_chapter.get('id', first_chapter.get('chapter_id'))
            self._load_chapter(chapter_id, project_id)
        else:
            # No chapters - just load project data in center panel
            self.center_panel.load_project(project_id)
        
        # Transition to editor
        self._show_editor()
    
    def _create_new_project(self):
        """Create a new project from dashboard."""
        name, ok = QInputDialog.getText(self, "New Project", "Project name:")
        if ok and name.strip():
            project_id = self.db_manager.create_project(name.strip())
            if project_id:
                # Create default chapter
                chapter_id = self.db_manager.create_chapter(project_id, "Chapter 1")
                self._open_project(project_id)
    
    def _show_import_dialog(self):
        """Show import dialog and import document with chapter detection."""
        from PyQt6.QtWidgets import QFileDialog, QInputDialog
        from src.domain.usecases.import_parser import ImportParser
        
        # Select file
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Document", "", 
            "Text Files (*.txt);;Markdown (*.md);;All Files (*)"
        )
        if not file_path:
            return
        
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Detect chapters
            chapters = ImportParser.detect_chapters(content)
            
            # Ask for project name
            import os
            default_name = os.path.splitext(os.path.basename(file_path))[0]
            project_name, ok = QInputDialog.getText(
                self, 
                "Import Project", 
                f"Project name (detected {len(chapters)} chapter(s)):",
                text=default_name
            )
            
            if not ok or not project_name.strip():
                return
            
            # Create project
            project_id = self.db_manager.create_project(project_name.strip())
            if not project_id:
                QMessageBox.warning(self, "Import Failed", "Could not create project.")
                return
            
            # Create chapters
            for idx, chapter_data in enumerate(chapters):
                title = ImportParser.clean_chapter_title(chapter_data['title'])
                chapter_id = self.db_manager.create_chapter(project_id, title)
                if chapter_id:
                    self.db_manager.update_chapter_content(chapter_id, chapter_data['content'])
            
            # Open the imported project
            self._open_project(project_id)
            
            # logging.info(f"Imported {len(chapters)} chapters from {file_path}")
            
        except Exception as e:
            logging.error(f"Import failed: {e}")
            QMessageBox.warning(self, "Import Failed", f"Error importing file: {str(e)}")
    
    def _show_settings(self):
        """Show settings dialog."""
        QMessageBox.information(self, "Settings", "Settings panel coming soon!")
    
    def _rename_project(self, project_id: int, current_title: str):
        """Rename a project from dashboard context menu."""
        new_name, ok = QInputDialog.getText(
            self, 
            "Rename Project", 
            "New project name:",
            text=current_title
        )
        if ok and new_name.strip() and new_name.strip() != current_title:
            if self.db_manager.rename_project(project_id, new_name.strip()):
                self.dashboard_view.load_projects()
    
    def _delete_project_with_confirm(self, project_id: int, title: str):
        """Delete a project with confirmation dialog."""
        reply = QMessageBox.question(
            self,
            "Delete Project",
            f"Are you sure you want to delete \"{title}\"?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_manager.delete_project(project_id):
                # Clear current project if it was deleted
                if self.current_project_id == project_id:
                    self.current_project_id = None
                    self.current_chapter_id = None
                self.dashboard_view.load_projects()
    
    def _duplicate_project(self, project_id: int):
        """Duplicate a project with all its chapters."""
        try:
            # Get original project
            settings = self.db_manager.get_project_settings(project_id)
            if not settings:
                QMessageBox.warning(self, "Duplicate Failed", "Could not find project.")
                return
            
            # Create new project with copied name
            new_name = f"{settings.get('name', 'Untitled')} (Copy)"
            new_project_id = self.db_manager.create_project(new_name, settings.get('genre', ''))
            
            if not new_project_id:
                QMessageBox.warning(self, "Duplicate Failed", "Could not create duplicate project.")
                return
            
            # Copy chapters
            chapters = self.db_manager.get_full_project_content(project_id)
            for chapter in chapters:
                chapter_id = self.db_manager.create_chapter(new_project_id, chapter.get('title', 'Untitled'))
                if chapter_id:
                    self.db_manager.update_chapter_content(chapter_id, chapter.get('content', ''))
            
            # Copy story bible if exists
            bible = self.db_manager.get_story_bible(project_id)
            if bible:
                for field, value in bible.items():
                    if value:
                        self.db_manager.save_bible_field(new_project_id, field, value)
            
            # Refresh dashboard
            self.dashboard_view.load_projects()
            # logging.info(f"Duplicated project {project_id} as {new_project_id}")
            
        except Exception as e:
            logging.error(f"Duplicate project failed: {e}")
            QMessageBox.warning(self, "Duplicate Failed", f"Error duplicating project: {str(e)}")
    
    def _export_project(self, project_id: int):
        """Export a specific project to PDF."""
        # Temporarily store current project id
        original_project_id = self.current_project_id
        self.current_project_id = project_id
        
        # Use existing export method
        self._export_document()
        
        # Restore original project id
        self.current_project_id = original_project_id
    
    def _go_back_to_dashboard(self):
        """Navigate back to dashboard from editor."""
        # Auto-save current work
        if self.current_chapter_id:
            text = self.center_panel.get_editor_content()
            self.db_manager.update_chapter_content(self.current_chapter_id, text)
        
        self._show_dashboard()
    
    def load_session(self):
        """Initialize app - always start on the home/dashboard page."""
        # Always start on the dashboard (home page)
        self._show_dashboard()
    
    def closeEvent(self, event):
        """Handle window close event - FORCE SAVE ALL DATA."""
        # logging.info("PERSIST: Application closing - forcing save of all content")
        
        # Save Writing Canvas content
        if self.current_chapter_id:
            text = self.center_panel.get_editor_content()
            # logging.info(f"PERSIST: Saving Writing Canvas (chapter={self.current_chapter_id}, length={len(text)} chars)")
            self.db_manager.update_chapter_content(self.current_chapter_id, text)
            # logging.info(f"PERSIST: Writing Canvas saved")
        
        # CRITICAL: Force save all Story Bible tabs
        if self.current_project_id and hasattr(self.center_panel, 'bible_section_widgets'):
            # logging.info(f"PERSIST: Force-saving all Story Bible tabs for project {self.current_project_id}")
            for field_name, widget_data in self.center_panel.bible_section_widgets.items():
                if widget_data and widget_data.get('widget'):
                    widget = widget_data['widget']
                    if isinstance(widget, QTextEdit):
                        text = widget.toPlainText()
                        # logging.info(f"PERSIST: Saving {field_name} (length={len(text)} chars)")
                        self.db_manager.save_bible_field(self.current_project_id, field_name, text)
                        # logging.info(f"PERSIST: {field_name} saved")
        
        # Save session state
        if self.current_project_id:
            self.db_manager.save_app_state("last_project_id", self.current_project_id)
        if self.current_chapter_id:
            self.db_manager.save_app_state("last_chapter_id", self.current_chapter_id)
        
        # Cleanup
        if hasattr(self.ai_engine, "unload_model"):
            self.ai_engine.unload_model()
        
        # Save Layout Sizes
        if hasattr(self, 'main_splitter'):
            self.main_splitter.save_sizes()
        
        # logging.info("PERSIST: All data saved, closing application")
        event.accept()