"""
Shared UI Widgets - Reusable components for the Story Bible UI.
"""
from typing import List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QAbstractButton, QGraphicsDropShadowEffect,
    QTextEdit
)

from PyQt6.QtGui import (
    QPainter, QColor, QPainterPath, QTextBlockUserData
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QPoint, QRectF, QPropertyAnimation, QEasingCurve, pyqtProperty, QTimer
)
from ..theme import QtTheme

class IOSSwitch(QAbstractButton):
    """
    Apple-style toggle switch.
    Smooth sliding animation, rounded pill shape.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(36, 22)
        
        self._thumb_pos = 0.0 # 0.0 = left (off), 1.0 = right (on)
        self._anim = QPropertyAnimation(self, b"thumbPos")
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        self.toggled.connect(self._animate_toggle)

    @pyqtProperty(float)
    def thumbPos(self):
        return self._thumb_pos

    @thumbPos.setter
    def thumbPos(self, pos):
        self._thumb_pos = pos
        self.update()

    def _animate_toggle(self, checked):
        self._anim.stop()
        self._anim.setStartValue(self._thumb_pos)
        self._anim.setEndValue(1.0 if checked else 0.0)
        self._anim.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Track (Background)
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), 11, 11)
        
        if self.isChecked():
            color = QColor(QtTheme.ACCENT_PRIMARY)
        else:
            color = QColor(255, 255, 255, 30)
            
        painter.fillPath(path, color)
        
        if not self.isChecked():
            painter.setPen(QColor(255, 255, 255, 50))
            painter.drawPath(path)
        else:
            painter.setPen(Qt.PenStyle.NoPen)
            
        # Thumb (Circle)
        thumb_dia = 18
        margin = 2
        
        start_x = margin
        end_x = self.width() - thumb_dia - margin
        curr_x = start_x + (end_x - start_x) * self._thumb_pos
        
        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPoint(int(curr_x + thumb_dia/2), int(margin + thumb_dia/2)), int(thumb_dia/2), int(thumb_dia/2))


class ToggleSettingsPopup(QWidget):
    """
    Generic glass panel with Apple-style toggles for toolbar configuration.
    """
    def __init__(self, options: List[str], default_enabled: List[str] = None, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.options = options
        self.default_enabled = default_enabled or options  # Default all ON
        
        # Auto-size based on content
        self.setFixedWidth(220)
        self.setFixedHeight(60 + (len(options) * 40))
        
        self._setup_ui()
        
        # Animation
        self._opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(30, 32, 36, 245);
                border: 1px solid rgba(255, 255, 255, 25);
                border-radius: 16px;
            }}
        """)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 80))
        container.setGraphicsEffect(shadow)
        
        content_layout = QVBoxLayout(container)
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(18, 15, 18, 15)
        
        # Toggles
        self.toggles = {}
        
        for opt in self.options:
            row = QHBoxLayout()
            row.setSpacing(12)
            
            label = QLabel(opt)
            label.setStyleSheet(f"""
                color: {QtTheme.TEXT_PRIMARY}; 
                font-weight: 500;
                font-size: 13px;
            """)
            
            switch = IOSSwitch()
            switch.setChecked(opt in self.default_enabled)
            
            row.addWidget(label)
            row.addStretch()
            row.addWidget(switch)
            
            content_layout.addLayout(row)
            self.toggles[opt] = switch
            
        layout.addWidget(container)
        
    def show_below(self, pos: QPoint):
        self.move(pos)
        self.setWindowOpacity(0.0)
        self.show()
        
        self._opacity_anim.stop()
        self._opacity_anim.setDuration(180)
        self._opacity_anim.setStartValue(0.0)
        self._opacity_anim.setEndValue(1.0)
        self._opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._opacity_anim.start()
        
    def get_active_config(self) -> List[str]:
        return [k for k, v in self.toggles.items() if v.isChecked()]


class ToolbarSplitButton(QWidget):
    """
    Generic split button for toolbar actions with toggle config panel.
    [ Label | ▼ ]
    """
    clicked = pyqtSignal()
    
    def __init__(self, label: str, options: List[str], default_enabled: List[str] = None, parent=None):
        super().__init__(parent)
        self.label = label
        self.options = options
        self.default_enabled = default_enabled
        
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)  # Very tight for seamless split button
        
        # Settings Popup
        self.settings_popup = ToggleSettingsPopup(self.options, self.default_enabled, self)
        
        # Main Button
        self.main_btn = QPushButton(self.label)
        self.main_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.main_btn.clicked.connect(self.clicked.emit)
        
        # Arrow Button
        self.arrow_btn = QPushButton("▼")
        self.arrow_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.arrow_btn.setFixedWidth(32)
        self.arrow_btn.clicked.connect(self._show_settings)
        
        base_style = f"""
            QPushButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 12),
                    stop:0.05 rgba(255, 255, 255, 8),
                    stop:1 rgba(255, 255, 255, 6)
                );
                border: 1px solid rgba(255, 255, 255, 15);
                color: {QtTheme.TEXT_SECONDARY};
                padding: 7px 14px;
                min-height: 32px;
                font-weight: 500;
                font-size: 13px;
                letter-spacing: 0.4px;
            }}
            QPushButton:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 18),
                    stop:0.05 rgba(255, 255, 255, 14),
                    stop:1 rgba(255, 255, 255, 10)
                );
                border: 1px solid rgba(255, 255, 255, 25);
                color: {QtTheme.TEXT_PRIMARY};
            }}
            QPushButton:pressed {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 8),
                    stop:0.05 rgba(255, 255, 255, 6),
                    stop:1 rgba(255, 255, 255, 4)
                );
                border: 1px solid rgba(255, 255, 255, 12);
                padding-top: 8px;
                padding-bottom: 6px;
            }}
        """
        
        self.main_btn.setStyleSheet(base_style + "QPushButton { border-top-right-radius: 0; border-bottom-right-radius: 0; }")
        self.arrow_btn.setStyleSheet(base_style + "QPushButton { border-top-left-radius: 0; border-bottom-left-radius: 0; font-size: 10px; }")
        
        layout.addWidget(self.main_btn, 1)
        layout.addWidget(self.arrow_btn)

    def _show_settings(self):
        """Show the toggle config panel below the arrow button."""
        pos = self.arrow_btn.mapToGlobal(QPoint(0, self.arrow_btn.height() + 5))
        self.settings_popup.show_below(pos)

    def get_config(self) -> List[str]:
        return self.settings_popup.get_active_config()


class DescribeSettingsPopup(QWidget):
    """
    Glass panel with Apple-style toggles for Describe configuration.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setFixedSize(200, 260)
        
        self._setup_ui()
        
        # Animation
        self._opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(30, 32, 36, 245);
                border: 1px solid rgba(255, 255, 255, 25);
                border-radius: 16px;
            }}
        """)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 80))
        container.setGraphicsEffect(shadow)
        
        content_layout = QVBoxLayout(container)
        content_layout.setSpacing(12)
        content_layout.setContentsMargins(15, 15, 15, 15)
        
        # Toggles
        self.toggles = {}
        options = ["Sight", "Smell", "Taste", "Sound", "Touch", "Metaphor"]
        
        for opt in options:
            row = QHBoxLayout()
            label = QLabel(opt)
            label.setStyleSheet(f"color: {QtTheme.TEXT_PRIMARY}; font-weight: 500;")
            
            switch = IOSSwitch()
            switch.setChecked(True)
            
            row.addWidget(label)
            row.addStretch()
            row.addWidget(switch)
            
            content_layout.addLayout(row)
            self.toggles[opt] = switch
            
        layout.addWidget(container)
        
    def show_below(self, pos: QPoint):
        self.move(pos)
        self.setWindowOpacity(0.0)
        self.show()
        
        self._opacity_anim.stop()
        self._opacity_anim.setDuration(150)
        self._opacity_anim.setStartValue(0.0)
        self._opacity_anim.setEndValue(1.0)
        self._opacity_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._opacity_anim.start()
        
    def get_active_config(self) -> List[str]:
        return [k for k, v in self.toggles.items() if v.isChecked()]


class DescribeSplitButton(QWidget):
    """
    Split button for Describe action.
    [ ✨ Describe | v ]
    """
    clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(130, 32)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1) # Tiny gap for separator feel
        
        # Settings Popup
        self.settings_popup = DescribeSettingsPopup(self)
        
        # Main Button
        self.main_btn = QPushButton("✨ Describe")
        self.main_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.main_btn.clicked.connect(self.clicked.emit)
        
        # Arrow Button
        self.arrow_btn = QPushButton("▼")
        self.arrow_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.arrow_btn.setFixedWidth(24)
        self.arrow_btn.clicked.connect(self._show_settings)
        
        # Styles
        base_style = f"""
            QPushButton {{
                background: transparent;
                color: {QtTheme.TEXT_SECONDARY};
                border: none;
                font-weight: 600;
                padding: 4px 8px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 25);
                color: white;
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 255, 255, 15);
            }}
        """
        
        self.main_btn.setStyleSheet(base_style + "border-top-left-radius: 16px; border-bottom-left-radius: 16px;")
        self.arrow_btn.setStyleSheet(base_style + f"""
            font-size: 8px; 
            padding-top: 6px;
            border-top-right-radius: 16px; 
            border-bottom-right-radius: 16px;
        """)
        
        layout.addWidget(self.main_btn)
        layout.addWidget(self.arrow_btn)
        
    def _show_settings(self):
        # Position popup below the button
        global_pos = self.mapToGlobal(QPoint(0, self.height() + 5))
        self.settings_popup.show_below(global_pos)

    def get_config(self):
        return self.settings_popup.get_active_config()


class TransparentScrollArea(QScrollArea):
    """
    Scroll area with STRICT TRANSPARENCY.
    Shows background image through all layers.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
        """)
        viewport = self.viewport()
        viewport.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        viewport.setAutoFillBackground(False)
        viewport.setStyleSheet("background-color: transparent;")


class SmartEditor(QTextEdit):
    """
    Enhanced QTextEdit with dirty tracking and incremental summarization triggers.
    - Tracks 'dirty' state per block (paragraph).
    - Triggers summary on FocusOut or Debounce Timeout.
    - Emits 'summary_triggered(new_text, callback)'.
    """
    summary_triggered = pyqtSignal(str, object)  # text, callback_function

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_globally_dirty = False
        self.is_loading = False # Flag to ignore programmatic changes
        self._dirty_blocks = set() # Set of block numbers (int)
        
        # Debounce Timer (2 seconds)
        self.debounce_timer = QTimer(self)
        self.debounce_timer.setInterval(2000)
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self._on_debounce_timeout)
        
        self.document().contentsChange.connect(self._on_contents_change)

    def _on_contents_change(self, position, charsRemoved, charsAdded):
        """Mark changed blocks as dirty."""
        if self.is_loading:
            return

        self.is_globally_dirty = True
        
        # Identify affected block(s)
        cursor = self.textCursor()
        cursor.setPosition(position)
        block = cursor.block()
        
        # Minimal dirty tracking: just mark the block containing the change
        # In a real rigorous implementation, we'd track ranges, but block-level is good for prose.
        self._dirty_blocks.add(block.blockNumber())
        
        # Reset debounce
        self.debounce_timer.start()

    def focusOutEvent(self, event):
        """Trigger summary on focus loss."""
        super().focusOutEvent(event)
        if self.is_globally_dirty:
            self.check_dirty_and_trigger()

    def _on_debounce_timeout(self):
        """Trigger summary after pause."""
        if self.is_globally_dirty:
            self.check_dirty_and_trigger()

    def check_dirty_and_trigger(self, force=False):
        """Consolidates dirty text and emits signal."""
        if not self.is_globally_dirty and not force:
            return

        # Gather dirty text
        # Simplification: For now, we send the *whole* new text 
        # that corresponds to the dirty edits. 
        # Optimization: We could instruct the App to only summarize the specific dirty blocks.
        # But for the current pipeline (which generates incremental summaries from NEW text), 
        # we need to decide what to send.
        
        # The App's pipeline expects "New Raw Text" to be identified by diffing length?
        # OR we can send the full text and let the pipeline decide based on last_summarized_char_count.
        # Given the "Strict Guardrails" in app.py, it uses `last_summarized_char_count`.
        # So providing the FULL current text is correct, and the pipeline will slice it.
        
        full_text = self.toPlainText()
        
        # Callback to clear dirty state if summary succeeds
        def on_success():
            self.is_globally_dirty = False
            self._dirty_blocks.clear()
            
        self.summary_triggered.emit(full_text, on_success)

    def handle_ai_completion(self):
        """
        Called when AI finishes generating text into this editor.
        Immediate trigger or force debounce start.
        """
        self.is_globally_dirty = True
        # For AI text, we might want to summarize sooner?
        # Or just let the debounce handle it.
        # Let's force a check immediately to keep UI in sync?
        # User feedback suggested: "Consider automatically marking AI... and trigger immediate"
        self.debounce_timer.start(500) # Short debounce for AI completion


class AutoExpandingTextEdit(SmartEditor):
    """
    QTextEdit that grows vertically to fit its content.
    Prevents internal scrollbars and forces parent containers to expand.
    Inherits SmartEditor capabilities.
    """
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent) # Initialize SmartEditor
        self.setParent(parent) # Ensure parent is set if passed down

        self.setPlaceholderText(placeholder)
        
        # Disable internal scrollbars
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Force wrap
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        
        # Connect growth signal
        self.textChanged.connect(self.adjust_height)
        
        # Minimum height
        self.setMinimumHeight(150)
        
        # Initial adjustment
        self.adjust_height()
        
    def showEvent(self, event):
        """Ensure height is adjusted when widget becomes visible."""
        super().showEvent(event)
        self.adjust_height()

    def resizeEvent(self, event):
        """Adjust height on resize."""
        super().resizeEvent(event)
        self.adjust_height()

    def adjust_height(self):
        """Update height based on document content."""
        doc = self.document()
        
        # KEY FIX: Force layout to respect current width
        if self.width() > 0:
            doc.setTextWidth(self.width())
            
        # Use precise height from document layout
        doc_height = doc.size().height()
        
        # Add padding/margins
        margins = self.contentsMargins()
        final_height = int(doc_height + margins.top() + margins.bottom() + 30) # Padding buffer
        
        self.setFixedHeight(max(150, final_height))
        
    def sizeHint(self):
        """Standard size hint for layouts."""
        hint = super().sizeHint()
        doc_height = int(self.document().documentLayout().documentSize().height())
        hint.setHeight(max(150, doc_height + 30))
        return hint
