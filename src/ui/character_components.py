"""
Sudowrite-style Character Profile Components
Expandable cards with multiple trait fields and auto-expanding inputs.
"""

import logging
import queue
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QScrollArea, QFrame, QInputDialog, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont

from .qt_theme import QtTheme


# ============================================================================
# AUTO-EXPANDING TEXT EDIT
# ============================================================================

class AutoExpandingTextEdit(QTextEdit):
    """Text edit that automatically expands vertically without internal scrolling."""
    
    contentChanged = pyqtSignal()
    
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setMinimumHeight(60)
        self.setMaximumHeight(500)
        
        # Connect to auto-resize
        self.textChanged.connect(self._adjust_height)
        self.textChanged.connect(self.contentChanged.emit)
        
        # Glass styling
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        self.setFrameShape(QFrame.Shape.NoFrame)
        
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: rgba(30, 35, 45, 120);
                border: 1px solid rgba(100, 100, 120, 80);
                border-radius: 6px;
                padding: 10px;
                color: {QtTheme.TEXT_PRIMARY};
                font-size: 14px;
                line-height: 1.5;
            }}
            QTextEdit:focus {{
                border: 1px solid {QtTheme.ACCENT_PRIMARY};
                background-color: rgba(30, 35, 45, 150);
            }}
        """)
        
        # Ensure viewport is transparent
        viewport = self.viewport()
        viewport.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        viewport.setAutoFillBackground(False)
        
        # Initial height adjustment
        self._adjust_height()
    
    def _adjust_height(self):
        """Adjust height based on content."""
        doc_height = self.document().size().height()
        new_height = int(doc_height) + 20  # Add padding
        new_height = max(60, min(500, new_height))
        self.setFixedHeight(new_height)


# ============================================================================
# CHARACTER PROFILE CARD
# ============================================================================

class CharacterProfileCard(QWidget):
    """Expandable character card with multiple trait fields (Sudowrite-style)."""
    
    character_updated = pyqtSignal(int, str, object)  # character_id, field, value
    character_deleted = pyqtSignal(int)  # character_id
    
    def __init__(self, db_manager, character_data, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.character_id = character_data.get('id')
        self.character_data = character_data
        self.is_expanded = True
        self.trait_widgets = {}
        self.custom_traits = []
        self.available_traits = []  # Hidden predefined traits that can be added
        self.shown_trait_containers = {}  # Track which trait containers are visible
        self.three_col_layout = None  # Three-column layout for compact fields
        
        # Glass card styling
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Create character card UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Card container
        self.card_widget = QWidget()
        self.card_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.card_widget.setAutoFillBackground(True)
        self.card_widget.setStyleSheet(f"""
            background-color: {QtTheme.CARD_BG};
            border: 1px solid {QtTheme.GLASS_BORDER};
            border-radius: 12px;
        """)
        
        card_layout = QVBoxLayout(self.card_widget)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)
        
        # Header
        self.header = self._create_header()
        card_layout.addWidget(self.header)
        
        # Collapsible content
        self.content_widget = QWidget()
        self.content_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.content_widget.setStyleSheet("background-color: transparent;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(20, 10, 20, 20)
        self.content_layout.setSpacing(15)
        
        # Add trait fields
        self._create_trait_fields()
        
        # Add Trait button - styled like Sudowrite
        add_trait_btn = QPushButton("+ Add Trait")
        add_trait_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_trait_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {QtTheme.ACCENT_PRIMARY};
                border: 1px solid {QtTheme.ACCENT_PRIMARY};
                border-radius: 6px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: 500;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: rgba(79, 70, 229, 20);
            }}
            QPushButton:pressed {{
                background-color: rgba(79, 70, 229, 40);
            }}
        """)
        add_trait_btn.clicked.connect(self._add_custom_trait)
        self.content_layout.addWidget(add_trait_btn)
        
        card_layout.addWidget(self.content_widget)
        main_layout.addWidget(self.card_widget)
    
    def _create_header(self) -> QWidget:
        """Create collapsible card header with role dropdown and visibility toggle."""
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet(f"""
            background-color: rgba(40, 45, 55, 100);
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
            border-bottom: 1px solid {QtTheme.GLASS_BORDER};
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(15, 8, 15, 8)
        layout.setSpacing(12)
        
        # Drag handle (6 dots) - more subtle
        drag_handle = QLabel("⋮⋮")
        drag_handle.setStyleSheet(f"color: {QtTheme.TEXT_MUTED}; font-size: 16px; padding: 0 5px;")
        drag_handle.setFixedWidth(20)
        drag_handle.setCursor(Qt.CursorShape.SizeAllCursor)
        layout.addWidget(drag_handle)
        
        # Expand/collapse arrow (moved left, before name)
        self.expand_icon = QLabel("▼")
        self.expand_icon.setStyleSheet(f"color: {QtTheme.TEXT_MUTED}; font-size: 12px;")
        self.expand_icon.setFixedWidth(20)
        self.expand_icon.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.expand_icon)
        
        # Character name (bigger, bolder)
        name = self.character_data.get('name', 'Unnamed Character')
        self.name_label = QLabel(name)
        self.name_label.setFont(QtTheme.get_font_header())
        self.name_label.setStyleSheet(f"color: {QtTheme.TEXT_PRIMARY}; font-weight: 600;")
        layout.addWidget(self.name_label)
        
        # Role dropdown (more compact)
        self.role_dropdown = QComboBox()
        self.role_dropdown.addItems([
            "Protagonist", "Antagonist", "Supporting", "Minor", 
            "Mentor", "Love Interest", "Sidekick", "Other"
        ])
        role = self.character_data.get('role', '')
        if role:
            index = self.role_dropdown.findText(role)
            if index >= 0:
                self.role_dropdown.setCurrentIndex(index)
            else:
                self.role_dropdown.addItem(role)
                self.role_dropdown.setCurrentText(role)
        
        self.role_dropdown.setStyleSheet(f"""
            QComboBox {{
                background-color: rgba(30, 35, 45, 120);
                color: {QtTheme.TEXT_MUTED};
                border: 1px solid rgba(100, 100, 120, 60);
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 13px;
                min-width: 100px;
                max-width: 140px;
            }}
            QComboBox:hover {{
                border: 1px solid {QtTheme.ACCENT_PRIMARY};
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 5px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {QtTheme.TEXT_MUTED};
                margin-right: 5px;
            }}
            QComboBox QAbstractItemView {{
                background-color: rgba(30, 35, 45, 240);
                color: {QtTheme.TEXT_PRIMARY};
                border: 1px solid {QtTheme.ACCENT_PRIMARY};
                selection-background-color: {QtTheme.ACCENT_PRIMARY};
            }}
        """)
        self.role_dropdown.currentTextChanged.connect(
            lambda text: self._on_role_changed(text)
        )
        self.role_dropdown.setEditable(True)
        layout.addWidget(self.role_dropdown)
        
        # Spacer to push right-side icons
        layout.addStretch()
        
        # Visibility toggle (eye icon) - Toggle button style
        self.visibility_btn = QPushButton()
        self.visibility_btn.setFixedSize(80, 36)
        self.visibility_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.visibility_btn.setCheckable(True)
        # Use is_visible from DB, default to 1 (True)
        is_visible = self.character_data.get('is_visible', 1)
        self.visibility_btn.setChecked(bool(is_visible))
        self.visibility_btn.setToolTip("Toggle visibility to AI")
        self._update_visibility_button_style()
        self.visibility_btn.clicked.connect(self._toggle_visibility)
        layout.addWidget(self.visibility_btn)
        
        # Archive button - More visible with background
        archive_btn = QPushButton("🗄")
        archive_btn.setFixedSize(40, 36)
        archive_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        archive_btn.setToolTip("Archive character")
        archive_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(60, 65, 75, 150);
                color: {QtTheme.TEXT_PRIMARY};
                border: 1px solid rgba(100, 100, 120, 80);
                font-size: 16px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: rgba(79, 70, 229, 120);
                border: 1px solid {QtTheme.ACCENT_PRIMARY};
                color: white;
            }}
        """)
        layout.addWidget(archive_btn)
        
        # Delete button - More visible with red hover
        delete_btn = QPushButton("🗑")
        delete_btn.setFixedSize(40, 36)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setToolTip("Delete character")
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(60, 65, 75, 150);
                color: {QtTheme.TEXT_PRIMARY};
                border: 1px solid rgba(100, 100, 120, 80);
                font-size: 16px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: rgba(239, 68, 68, 120);
                border: 1px solid #EF4444;
                color: white;
            }}
        """)
        delete_btn.clicked.connect(self._delete_character)
        layout.addWidget(delete_btn)
        
        # Three-dot menu - More visible
        menu_btn = QPushButton("⋯")
        menu_btn.setFixedSize(40, 36)
        menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        menu_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(60, 65, 75, 150);
                color: {QtTheme.TEXT_PRIMARY};
                border: 1px solid rgba(100, 100, 120, 80);
                font-size: 20px;
                font-weight: bold;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: rgba(79, 70, 229, 120);
                border: 1px solid {QtTheme.ACCENT_PRIMARY};
                color: white;
            }}
        """)
        layout.addWidget(menu_btn)
        
        # Make header clickable to toggle (except for interactive elements)
        def toggle_on_click(event):
            # Check if click was on name label or drag handle or expand icon
            clicked_widget = header.childAt(event.pos())
            if clicked_widget in [self.name_label, drag_handle, self.expand_icon] or clicked_widget is None:
                self._toggle_expand()
        
        header.mousePressEvent = toggle_on_click
        
        return header
    
    def _create_trait_fields(self):
        """Create predefined trait fields (show compact fields by default)."""
        # Define all available traits
        self.available_traits = [
            ('pronouns', 'Pronouns', True),  # True = compact field
            ('groups', 'Groups', True),
            ('other_names', 'Other Names', True),
            ('personality_traits', 'Personality', False),  # False = full-width field
            ('backstory', 'Background', False),
            ('physical_description', 'Physical Description', False),
            ('speech_pattern', 'Dialogue Style', False),
            ('motivations', 'Motivations', False),
            ('internal_conflicts', 'Internal Conflicts', False),
            ('strengths', 'Strengths', False),
            ('weaknesses', 'Weaknesses', False),
            ('character_arc', 'Character Arc', False),
        ]
        
        # ALWAYS show the three compact fields (pronouns, groups, other_names) by default
        compact_fields_to_show = [('pronouns', 'Pronouns', True), ('groups', 'Groups', True), ('other_names', 'Other Names', True)]
        for field_name, label, is_compact in compact_fields_to_show:
            value = self.character_data.get(field_name, '')
            # Remove from available_traits list
            if (field_name, label, is_compact) in self.available_traits:
                self.available_traits.remove((field_name, label, is_compact))
            # Show the field (even if empty)
            self._show_trait_field(field_name, label, value, is_compact)
        
        # Load existing trait values for OTHER traits (not the compact ones)
        for field_name, label, is_compact in self.available_traits[:]:
            value = self.character_data.get(field_name, '')
            if value:  # Only show non-compact traits that have data
                self.available_traits.remove((field_name, label, is_compact))
                self._show_trait_field(field_name, label, value, is_compact)
    
    def _show_trait_field(self, field_name, label, value="", is_compact=False):
        """Show a trait field (either compact or full-width)."""
        if is_compact:
            # For compact fields (pronouns, groups, other_names), we need to group them
            # Check if we already have a three-column container
            if not hasattr(self, 'three_col_layout') or self.three_col_layout is None:
                three_col_container = QWidget()
                three_col_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
                three_col_container.setStyleSheet("background-color: transparent;")
                self.three_col_layout = QHBoxLayout(three_col_container)
                self.three_col_layout.setContentsMargins(0, 0, 0, 0)
                self.three_col_layout.setSpacing(15)
                # Insert at the top (before other traits)
                self.content_layout.insertWidget(0, three_col_container)
            
            field_container = self._create_compact_field(field_name, label, value)
            self.three_col_layout.addWidget(field_container, 1)
            self.shown_trait_containers[field_name] = field_container
        else:
            # Full-width field
            container = QWidget()
            container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            container.setStyleSheet("background-color: transparent;")
            layout = QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(6)
            
            # Label
            label_widget = QLabel(label)
            label_widget.setStyleSheet(f"""
                color: {QtTheme.TEXT_MUTED};
                font-size: 12px;
                font-weight: 500;
            """)
            layout.addWidget(label_widget)
            
            # Auto-expanding text input
            text_edit = AutoExpandingTextEdit(placeholder=f"")
            text_edit.setPlainText(value or "")
            text_edit.contentChanged.connect(
                lambda fn=field_name, te=text_edit: self._on_trait_changed(fn, te)
            )
            layout.addWidget(text_edit)
            
            self.trait_widgets[field_name] = text_edit
            # Insert before the "+ Add Trait" button
            self.content_layout.insertWidget(self.content_layout.count() - 1, container)
            self.shown_trait_containers[field_name] = container
    
    def _create_compact_field(self, field_name, label, value=""):
        """Create a compact field for three-column layout."""
        container = QWidget()
        container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        container.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        # Label - simpler styling like Sudowrite
        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"""
            color: {QtTheme.TEXT_MUTED};
            font-size: 12px;
            font-weight: 500;
        """)
        layout.addWidget(label_widget)
        
        # Compact text input
        text_edit = AutoExpandingTextEdit(placeholder=f"")
        text_edit.setPlainText(value or "")
        text_edit.setMinimumHeight(40)
        text_edit.setMaximumHeight(100)
        text_edit.contentChanged.connect(
            lambda fn=field_name, te=text_edit: self._on_trait_changed(fn, te)
        )
        layout.addWidget(text_edit)
        
        self.trait_widgets[field_name] = text_edit
        return container
    
    def _add_custom_trait(self):
        """Add a trait from available predefined traits or create a custom one."""
        if not self.available_traits:
            # No predefined traits left, ask for custom trait
            trait_name, ok = QInputDialog.getText(
                self, "Add Custom Trait", "Trait name:"
            )
            
            if ok and trait_name:
                field_name = f"custom_{len(self.custom_traits)}"
                self.custom_traits.append((field_name, trait_name))
                self._show_trait_field(field_name, trait_name, "", False)
        else:
            # Show dialog to select from available predefined traits
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Add Trait")
            dialog.setModal(True)
            dialog.setMinimumWidth(300)
            dialog.setStyleSheet(f"""
                QDialog {{
                    background-color: {QtTheme.BG_MAIN};
                    border: 1px solid {QtTheme.GLASS_BORDER};
                    border-radius: 8px;
                }}
            """)
            
            layout = QVBoxLayout(dialog)
            
            # Instructions
            instructions = QLabel("Select a trait to add, or create a custom trait:")
            instructions.setStyleSheet(f"color: {QtTheme.TEXT_MUTED}; font-size: 13px; padding: 5px;")
            instructions.setWordWrap(True)
            layout.addWidget(instructions)
            
            # List of available traits
            trait_list = QListWidget()
            trait_list.setStyleSheet(f"""
                QListWidget {{
                    background-color: {QtTheme.BG_INPUT};
                    color: {QtTheme.TEXT_PRIMARY};
                    border: 1px solid {QtTheme.GLASS_BORDER};
                    border-radius: 6px;
                    padding: 5px;
                }}
                QListWidget::item {{
                    padding: 8px;
                    border-radius: 4px;
                }}
                QListWidget::item:hover {{
                    background-color: {QtTheme.BG_HOVER};
                }}
                QListWidget::item:selected {{
                    background-color: {QtTheme.ACCENT_PRIMARY};
                    color: white;
                }}
            """)
            
            for field_name, label, is_compact in self.available_traits:
                trait_list.addItem(label)
            
            layout.addWidget(trait_list)
            
            # Buttons
            button_layout = QHBoxLayout()
            
            custom_btn = QPushButton("Custom Trait")
            custom_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {QtTheme.TEXT_MUTED};
                    border: 1px solid {QtTheme.GLASS_BORDER};
                    border-radius: 6px;
                    padding: 8px 16px;
                }}
                QPushButton:hover {{
                    background-color: {QtTheme.BG_HOVER};
                }}
            """)
            
            add_btn = QPushButton("Add")
            add_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {QtTheme.ACCENT_PRIMARY};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 20px;
                }}
                QPushButton:hover {{
                    background-color: {QtTheme.ACCENT_HOVER};
                }}
            """)
            
            cancel_btn = QPushButton("Cancel")
            cancel_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {QtTheme.TEXT_MUTED};
                    border: 1px solid {QtTheme.GLASS_BORDER};
                    border-radius: 6px;
                    padding: 8px 16px;
                }}
                QPushButton:hover {{
                    background-color: {QtTheme.BG_HOVER};
                }}
            """)
            
            button_layout.addWidget(custom_btn)
            button_layout.addStretch()
            button_layout.addWidget(cancel_btn)
            button_layout.addWidget(add_btn)
            layout.addLayout(button_layout)
            
            # Connect buttons
            selected_trait = None
            
            def on_add():
                nonlocal selected_trait
                current_item = trait_list.currentItem()
                if current_item:
                    selected_trait = current_item.text()
                    dialog.accept()
            
            def on_custom():
                dialog.reject()
                # Ask for custom trait name
                trait_name, ok = QInputDialog.getText(
                    self, "Add Custom Trait", "Trait name:"
                )
                if ok and trait_name:
                    field_name = f"custom_{len(self.custom_traits)}"
                    self.custom_traits.append((field_name, trait_name))
                    self._show_trait_field(field_name, trait_name, "", False)
            
            add_btn.clicked.connect(on_add)
            custom_btn.clicked.connect(on_custom)
            cancel_btn.clicked.connect(dialog.reject)
            trait_list.itemDoubleClicked.connect(on_add)
            
            if dialog.exec() == QDialog.DialogCode.Accepted and selected_trait:
                # Find the selected trait in available_traits
                for field_name, label, is_compact in self.available_traits[:]:
                    if label == selected_trait:
                        self.available_traits.remove((field_name, label, is_compact))
                        self._show_trait_field(field_name, label, "", is_compact)
                        break
    
    def _on_trait_changed(self, field_name, text_edit):
        """Handle trait content change."""
        value = text_edit.toPlainText()
        self.character_updated.emit(self.character_id, field_name, value)
        
        # Auto-save to database
        try:
            with self.db_manager.get_connection() as conn:
                # Check if field exists in database
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(characters)")
                columns = [row[1] for row in cursor.fetchall()]
                
                if field_name in columns:
                    conn.execute(
                        f"UPDATE characters SET {field_name} = ? WHERE id = ?",
                        (value, self.character_id)
                    )
                    logging.info(f"Auto-saved {field_name} for character {self.character_id}")
                    
                    # Update local data
                    self.character_data[field_name] = value
                    
                    # Update header if name or role changed
                    if field_name == 'name':
                        self.name_label.setText(value)
                    elif field_name == 'role':
                        # Update dropdown if changed
                        if hasattr(self, 'role_dropdown'):
                            current_text = self.role_dropdown.currentText()
                            if current_text != value:
                                index = self.role_dropdown.findText(value)
                                if index >= 0:
                                    self.role_dropdown.setCurrentIndex(index)
                                else:
                                    self.role_dropdown.addItem(value)
                                    self.role_dropdown.setCurrentText(value)
        except Exception as e:
            logging.error(f"Failed to auto-save trait: {e}")
    
    def _on_role_changed(self, text):
        """Handle role dropdown change."""
        self.character_updated.emit(self.character_id, 'role', text)
        
        # Auto-save to database
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute(
                    "UPDATE characters SET role = ? WHERE id = ?",
                    (text, self.character_id)
                )
                logging.info(f"Auto-saved role for character {self.character_id}: {text}")
                self.character_data['role'] = text
        except Exception as e:
            logging.error(f"Failed to auto-save role: {e}")
    
    def _toggle_expand(self):
        """Toggle card expansion."""
        self.is_expanded = not self.is_expanded
        self.content_widget.setVisible(self.is_expanded)
        self.expand_icon.setText("▼" if self.is_expanded else "▶")
    
    def _update_visibility_button_style(self):
        """Update visibility button appearance based on checked state."""
        is_visible = self.visibility_btn.isChecked()
        if is_visible:
            # Visible to AI - Green/Active style
            self.visibility_btn.setText("👁 ON")
            self.visibility_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(34, 197, 94, 150);
                    color: white;
                    border: 1px solid #22C55E;
                    font-size: 12px;
                    font-weight: 600;
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    background-color: rgba(34, 197, 94, 200);
                    border: 1px solid #16A34A;
                }}
            """)
        else:
            # Hidden from AI - Gray/Inactive style
            self.visibility_btn.setText("👁 OFF")
            self.visibility_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(60, 65, 75, 150);
                    color: {QtTheme.TEXT_MUTED};
                    border: 1px solid rgba(100, 100, 120, 80);
                    font-size: 12px;
                    font-weight: 600;
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    background-color: rgba(80, 85, 95, 150);
                    border: 1px solid rgba(120, 120, 140, 100);
                }}
            """)
    
    def _toggle_visibility(self):
        """Toggle character visibility to AI."""
        is_visible = self.visibility_btn.isChecked()
        self._update_visibility_button_style()
        
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute(
                    "UPDATE characters SET is_visible = ? WHERE id = ?",
                    (1 if is_visible else 0, self.character_id)
                )
                self.character_data['is_visible'] = 1 if is_visible else 0
                logging.info(f"Character {self.character_id} visibility: {is_visible}")
        except Exception as e:
            logging.error(f"Failed to update visibility: {e}")
    
    def _delete_character(self):
        """Delete this character."""
        reply = QMessageBox.question(
            self, "Delete Character",
            f"Are you sure you want to delete '{self.character_data.get('name', 'this character')}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.character_deleted.emit(self.character_id)


# ============================================================================
# AI THREAD
# ============================================================================

class CharacterGenerationThread(QThread):
    finished = pyqtSignal(str)
    
    def __init__(self, ai_engine, prompt, response_queue):
        super().__init__()
        self.ai_engine = ai_engine
        self.prompt = prompt
        self.response_queue = response_queue
    
    def run(self):
        try:
            # Use the AI engine to generate response
            self.ai_engine.stream_response(self.prompt, self.response_queue, "", "")
            
            # Collect the full response
            full_response = ""
            while True:
                try:
                    chunk = self.response_queue.get(timeout=0.1)
                    if chunk == "[[END]]":
                        break
                    full_response += chunk
                except queue.Empty:
                    # If logic is synchronous, we might need to rely on the sentinel.
                    # If we've processed everything and engine is done, we might not get Empty if fast enough, 
                    # but safest is just wait for [[END]]
                    continue
            
            print(f"\n[AI DEBUG] Full Response:\n{full_response}\n")
            self.finished.emit(full_response)
        except Exception as e:
            self.finished.emit(f"ERROR: {str(e)}")


# ============================================================================
# CHARACTER WIDGET (MAIN CONTAINER)
# ============================================================================

class CharacterWidget(QWidget):
    """Sudowrite-style character profile page with expandable cards."""
    
    def __init__(self, db_manager, ai_engine=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.ai_engine = ai_engine
        self.project_id = None
        self.character_cards = []
        self.active_threads = []  # Keep references to prevent GC
        
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: transparent;")
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Create character page UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)
        
        title = QLabel("Characters")
        title.setFont(QtTheme.get_font_title())
        title.setStyleSheet(f"color: {QtTheme.TEXT_PRIMARY};")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Add Character menu button with dropdown
        self.add_btn = QPushButton("+ New Character ▾")
        self.add_btn.setFixedHeight(44)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {QtTheme.ACCENT_PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 24px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {QtTheme.ACCENT_HOVER};
            }}
            QPushButton:pressed {{
                background-color: #3730a3;
            }}
            QPushButton:disabled {{
                background-color: rgba(79, 70, 229, 0.3);
                color: rgba(255, 255, 255, 0.5);
            }}
        """)
        
        # Create menu for character creation options
        from PyQt6.QtWidgets import QMenu
        self.add_menu = QMenu(self)
        self.add_menu.setStyleSheet(f"""
            QMenu {{
                background-color: rgba(30, 35, 45, 240);
                border: 1px solid {QtTheme.ACCENT_PRIMARY};
                border-radius: 8px;
                padding: 8px 0;
            }}
            QMenu::item {{
                padding: 12px 24px;
                color: {QtTheme.TEXT_PRIMARY};
                font-size: 14px;
            }}
            QMenu::item:selected {{
                background-color: {QtTheme.ACCENT_PRIMARY};
            }}
            QMenu::separator {{
                height: 1px;
                background: rgba(100, 100, 120, 80);
                margin: 8px 0;
            }}
        """)
        
        # Menu actions
        blank_action = self.add_menu.addAction("📝 Blank Character")
        blank_action.triggered.connect(self._add_blank_character)
        blank_action.setToolTip("Create an empty character profile to fill manually")
        
        generate_action = self.add_menu.addAction("🤖 Generate from Description")
        generate_action.triggered.connect(self._generate_character_from_description)
        generate_action.setToolTip("AI generates a character from your description")
        
        self.add_menu.addSeparator()
        
        surprise_action = self.add_menu.addAction("✨ Surprise Me!")
        surprise_action.triggered.connect(self._surprise_me_character)
        surprise_action.setToolTip("AI creates a character that fits your story")
        
        self.add_btn.clicked.connect(lambda: self.add_menu.exec(self.add_btn.mapToGlobal(self.add_btn.rect().bottomLeft())))
        header_layout.addWidget(self.add_btn)
        
        layout.addLayout(header_layout)
        
        # Cards container (no scroll area - parent handles scrolling)
        self.cards_container = QWidget()
        self.cards_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.cards_container.setStyleSheet("background-color: transparent;")
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 20, 0, 0)  # Top margin for spacing
        self.cards_layout.setSpacing(20)
        
        # Empty state message (hidden by default)
        self.empty_message = QLabel("No project selected.\n\nPlease select or create a project from the left sidebar to manage characters.")
        self.empty_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_message.setWordWrap(True)
        self.empty_message.setStyleSheet(f"""
            QLabel {{
                color: {QtTheme.TEXT_MUTED};
                font-size: 16px;
                padding: 60px 40px;
            }}
        """)
        self.empty_message.setVisible(False)
        self.cards_layout.addWidget(self.empty_message)
        
        # "No characters yet" message (separate from empty_message)
        self.no_chars_message = QLabel("No characters yet.\n\nClick '+ New Character' to create your first character.")
        self.no_chars_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_chars_message.setWordWrap(True)
        self.no_chars_message.setStyleSheet(f"""
            QLabel {{
                color: {QtTheme.TEXT_MUTED};
                font-size: 16px;
                padding: 60px 40px;
            }}
        """)
        self.no_chars_message.setVisible(False)
        self.cards_layout.addWidget(self.no_chars_message)
        
        self.cards_layout.addStretch()
        
        layout.addWidget(self.cards_container)
    
    def set_project_id(self, project_id):
        """Load characters for a project."""
        logging.info(f"CharacterWidget.set_project_id called with project_id={project_id}")
        self.project_id = project_id
        
        # Enable/disable add button based on whether we have a project
        if self.add_btn:
            self.add_btn.setEnabled(bool(project_id))
        
        self._load_characters()
    
    def _load_characters(self):
        """Load and display character cards."""
        logging.info(f"CharacterWidget._load_characters called with project_id={self.project_id}")
        
        # Clear existing cards
        for card in self.character_cards:
            card.deleteLater()
        self.character_cards.clear()
        
        if not self.project_id:
            logging.warning("CharacterWidget: No project_id set, cannot load characters")
            self.empty_message.setVisible(True)
            self.no_chars_message.setVisible(False)
            return
        
        self.empty_message.setVisible(False)
        
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM characters WHERE project_id = ? ORDER BY id",
                    (self.project_id,)
                )
                rows = cursor.fetchall()
                
                # Get column names to create dictionaries
                col_names = [description[0] for description in cursor.description]
                characters = [dict(zip(col_names, row)) for row in rows]
                
                logging.info(f"CharacterWidget: Found {len(characters)} characters for project {self.project_id}")
                
                # Show/hide "no characters yet" message based on character count
                if len(characters) == 0:
                    self.no_chars_message.setVisible(True)
                else:
                    self.no_chars_message.setVisible(False)
                
                for char_data in characters:
                    logging.info(f"Creating card for character: {char_data.get('name', 'Unknown')}")
                    card = CharacterProfileCard(self.db_manager, char_data)
                    card.character_updated.connect(self._on_character_updated)
                    card.character_deleted.connect(self._on_character_deleted)
                    
                    self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
                    self.character_cards.append(card)
                    
        except Exception as e:
            logging.error(f"Failed to load characters: {e}", exc_info=True)
    
    def _add_blank_character(self):
        """Add a blank character (manual creation)."""
        if not self.project_id:
            QMessageBox.warning(
                self, "No Project Selected",
                "Please select or create a project from the left sidebar before adding characters."
            )
            return
        
        name, ok = QInputDialog.getText(
            self, "New Character", "Character name:"
        )
        
        if ok and name:
            try:
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO characters (project_id, name, role) VALUES (?, ?, ?)",
                        (self.project_id, name, "")
                    )
                    conn.commit()
                    logging.info(f"Created blank character: {name}")
                    self._load_characters()
            except Exception as e:
                logging.error(f"Failed to create character: {e}")
    
    def _generate_character_from_description(self):
        """AI generates a character from user description."""
        if not self.project_id:
            QMessageBox.warning(
                self, "No Project Selected",
                "Please select or create a project from the left sidebar before adding characters."
            )
            return
        
        if not self.ai_engine:
            QMessageBox.warning(
                self, "AI Not Available",
                "AI engine is not available. Please check your configuration."
            )
            return
        
        from PyQt6.QtWidgets import QTextEdit, QDialog, QVBoxLayout, QDialogButtonBox
        
        # Create dialog for multi-line input
        dialog = QDialog(self)
        dialog.setWindowTitle("Generate Character from Description")
        dialog.setMinimumSize(500, 300)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {QtTheme.BG_MAIN};
            }}
        """)
        
        layout = QVBoxLayout(dialog)
        
        # Info label
        info_label = QLabel("Describe the character you want to create:")
        info_label.setStyleSheet(f"color: {QtTheme.TEXT_PRIMARY}; font-size: 14px; margin-bottom: 10px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Text input
        description_input = QTextEdit()
        description_input.setPlaceholderText("Example: A wise old wizard who once served the king but now lives in exile. He's haunted by past decisions and seeks redemption...")
        description_input.setMinimumHeight(150)
        description_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {QtTheme.BG_INPUT};
                border: 1px solid rgba(100, 100, 120, 80);
                border-radius: 6px;
                padding: 12px;
                color: {QtTheme.TEXT_PRIMARY};
                font-size: 14px;
            }}
            QTextEdit:focus {{
                border: 1px solid {QtTheme.ACCENT_PRIMARY};
            }}
        """)
        layout.addWidget(description_input)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.setStyleSheet(f"""
            QPushButton {{
                background-color: {QtTheme.ACCENT_PRIMARY};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {QtTheme.ACCENT_HOVER};
            }}
        """)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            description = description_input.toPlainText().strip()
            if description:
                self._generate_character_with_ai(description)
    
    def _generate_character_with_ai(self, description):
        """Use AI to generate character traits from description."""
        import queue
        
        # Show progress dialog
        progress = QMessageBox(self)
        progress.setWindowTitle("Generating Character")
        progress.setText("AI is creating your character...\n\nThis may take a moment.")
        progress.setStandardButtons(QMessageBox.StandardButton.NoButton)
        progress.setStyleSheet(f"""
            QMessageBox {{
                background-color: {QtTheme.BG_MAIN};
            }}
            QLabel {{
                color: {QtTheme.TEXT_PRIMARY};
                font-size: 14px;
                min-width: 300px;
            }}
        """)
        progress.show()
        
        # Create AI prompt
        prompt = f"""Generate a detailed character profile based on this description:

{description}

Please provide the following information in JSON format:
{{
    "name": "character's full name",
    "role": "protagonist/antagonist/supporting",
    "pronouns": "he/him, she/her, they/them, etc.",
    "personality_traits": "detailed personality description",
    "backstory": "character's background and history",
    "physical_description": "appearance and physical traits",
    "speech_pattern": "how they speak and communicate",
    "motivations": "what drives them",
    "internal_conflicts": "inner struggles and doubts",
    "strengths": "their abilities and positive traits",
    "weaknesses": "flaws and limitations",
    "character_arc": "potential growth trajectory"
}}

Make it creative, detailed, and compelling!
IMPORTANT: Return ONLY the raw JSON. Do not use Markdown code blocks (```json).
Ensure all strings are properly escaped."""
        
        response_queue = queue.Queue()
        
        # Create and track thread
        ai_thread = CharacterGenerationThread(self.ai_engine, prompt, response_queue)
        
        def on_ai_finished(response):
            try:
                progress.close()
                progress.deleteLater()
                
                # Clean up thread reference
                if ai_thread in self.active_threads:
                    self.active_threads.remove(ai_thread)
                
                if response.startswith("ERROR:"):
                    QMessageBox.critical(self, "Error", f"Failed to generate character:\n{response}")
                    return
                
                import json
                import re
                
                try:
                    # Basic cleanup
                    clean_response = response.replace("```json", "").replace("```", "").strip()
                    
                    # Find start of JSON
                    start_idx = clean_response.find('{')
                    if start_idx == -1:
                        raise ValueError("No JSON object found (missing '{')")
                    
                    json_str = clean_response[start_idx:]
                    
                    # Initial attempt
                    try:
                        char_data = json.loads(json_str)
                    except json.JSONDecodeError:
                        # Attempt to fix truncated JSON
                        logging.warning("JSON incomplete, attempting to repair...")
                        
                        repaired = False
                        # Heuristic: try closing quote if last char is not brace or quote
                        attempts = [json_str]
                        
                        if json_str and json_str[-1] not in ['}', '"', ']']:
                             attempts.append(json_str + '"')
                             attempts.append(json_str + '"}')
                             attempts.append(json_str + '"}}')
                        
                        candidates = [json_str] + [json_str + ('}' * i) for i in range(1, 5)]
                        
                        final_candidates = []
                        for c in candidates:
                            final_candidates.append(c)
                            final_candidates.append(c + '"')
                            final_candidates.append(c + '"}')
                        
                        for candidate in final_candidates:
                            try:
                                char_data = json.loads(candidate)
                                repaired = True
                                logging.info(f"Successfully repaired JSON")
                                break
                            except json.JSONDecodeError:
                                continue
                        
                        if not repaired:
                            # Try to cut off at last brace
                            last_brace = json_str.rfind('}')
                            if last_brace != -1:
                                 try:
                                     char_data = json.loads(json_str[:last_brace+1])
                                     repaired = True
                                 except:
                                     pass
                        
                        if not repaired:
                             # Regex fallback
                            logging.warning("JSON repair failed, attempting Regex fallback...")
                            char_data = {}
                            fields = [
                                "name", "role", "pronouns", "personality_traits", "backstory", 
                                "physical_description", "speech_pattern", "motivations", 
                                "internal_conflicts", "strengths", "weaknesses", "character_arc"
                            ]
                            for field in fields:
                                try:
                                    match = re.search(f'"{field}"\s*:\s*"(.*?)(?<!\\\\)"', json_str, re.DOTALL)
                                    if match:
                                        char_data[field] = match.group(1)
                                except:
                                    pass
                            
                            if char_data.get('name'):
                                logging.info("Regex fallback successful")
                            else:
                                raise ValueError("Could not repair malformed JSON")
                    
                    # Create character in database
                    with self.db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO characters (
                                project_id, name, role, pronouns, personality_traits,
                                backstory, physical_description, speech_pattern,
                                motivations, internal_conflicts, strengths, weaknesses, character_arc,
                                physical_description
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            self.project_id,
                            char_data.get('name', 'Generated Character'),
                            char_data.get('role', ''),
                            char_data.get('pronouns', ''),
                            char_data.get('personality_traits', ''),
                            char_data.get('backstory', ''),
                            char_data.get('physical_description', ''),
                            char_data.get('speech_pattern', ''),
                            char_data.get('motivations', ''),
                            char_data.get('internal_conflicts', ''),
                            char_data.get('strengths', ''),
                            char_data.get('weaknesses', ''),
                            char_data.get('character_arc', ''),
                             char_data.get('physical_description', '')
                        ))
                        conn.commit()
                        logging.info(f"Generated character: {char_data.get('name')}")
                        self._load_characters()
                        
                        QMessageBox.information(
                            self, "Success",
                            f"Character '{char_data.get('name')}' has been generated and added!"
                        )
                except Exception as e:
                    logging.error(f"Failed to parse AI response: {e}")
                    QMessageBox.warning(
                        self, "Parsing Error",
                        f"AI generated a response but it couldn't be parsed. Creating blank character instead.\n\nError: {str(e)}"
                    )
                    # Fallback: create blank character
                    self._add_blank_character()
            except Exception as e:
                 logging.error(f"Critical error in on_ai_finished: {e}")
            finally:
                progress.close()
                progress.deleteLater()
        
        ai_thread.finished.connect(on_ai_finished)
        self.active_threads.append(ai_thread)
        ai_thread.start()
    
    def _surprise_me_character(self):
        """AI creates a character based on the story/project context."""
        if not self.project_id:
            QMessageBox.warning(
                self, "No Project Selected",
                "Please select or create a project from the left sidebar before adding characters."
            )
            return
        
        if not self.ai_engine:
            QMessageBox.warning(
                self, "AI Not Available",
                "AI engine is not available. Please check your configuration."
            )
            return
        
        # Get project context
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get project info
                cursor.execute("SELECT * FROM projects WHERE id = ?", (self.project_id,))
                project = cursor.fetchone()
                if project:
                    col_names = [description[0] for description in cursor.description]
                    project_data = dict(zip(col_names, project))
                else:
                    project_data = {}
                
                # Get existing characters
                cursor.execute("SELECT name, role FROM characters WHERE project_id = ? AND is_visible = 1", (self.project_id,))
                existing_chars = cursor.fetchall()
                
                # Get chapters/content
                cursor.execute("SELECT title, content FROM chapters WHERE project_id = ? LIMIT 5", (self.project_id,))
                chapters = cursor.fetchall()
                
            # Get Story Bible Context (using new robust method)
            bible_data = self.db_manager.get_story_bible(self.project_id)
            
        except Exception as e:
            logging.error(f"Failed to get project context: {e}")
            project_data = {}
            existing_chars = []
            chapters = []
            bible_data = {}
        
        # Show progress
        progress = QMessageBox(self)
        progress.setWindowTitle("Surprising You...")
        progress.setText("AI is analyzing your story and creating\na character that would fit perfectly!\n\nThis may take a moment.")
        progress.setStandardButtons(QMessageBox.StandardButton.NoButton)
        progress.setStyleSheet(f"""
            QMessageBox {{
                background-color: {QtTheme.BG_MAIN};
            }}
            QLabel {{
                color: {QtTheme.TEXT_PRIMARY};
                font-size: 14px;
                min-width: 300px;
            }}
        """)
        progress.show()
        
        # Build context including Story Bible
        context = f"Project: {project_data.get('name', 'Untitled')}\n"
        if project_data.get('genre'):
            context += f"Genre: {project_data.get('genre')}\n"
            
        # Add Story Bible info if available
        if bible_data:
            if bible_data.get('braindump'):
                context += f"\nStory Braindump/Notes:\n{bible_data.get('braindump')}\n"
            if bible_data.get('synopsis'):
                context += f"\nSynopsis:\n{bible_data.get('synopsis')}\n"
            if bible_data.get('worldbuilding'):
                context += f"\nWorldbuilding:\n{bible_data.get('worldbuilding')}\n"
        
        if existing_chars:
            context += f"\nExisting characters:\n"
            for char in existing_chars[:10]:
                context += f"- {char[0]} ({char[1]})\n"
        
        if chapters:
            context += f"\nStory excerpts:\n"
            for title, content in chapters:
                if content:
                    excerpt = content[:200] + "..." if len(content) > 200 else content
                    context += f"Chapter: {title}\n{excerpt}\n\n"
        
        prompt = f"""Based on this story context, create a NEW character that would be a great addition:

{context}

Generate a unique, compelling character that fills a gap in the story or adds interesting dynamics. 
Provide the character information in JSON format:

{{
    "name": "character's full name",
    "role": "protagonist/antagonist/supporting",
    "pronouns": "he/him, she/her, they/them, etc.",
    "personality_traits": "detailed personality description",
    "backstory": "character's background and history",
    "physical_description": "appearance and physical traits",
    "speech_pattern": "how they speak and communicate",
    "motivations": "what drives them",
    "internal_conflicts": "inner struggles and doubts",
    "strengths": "their abilities and positive traits",
    "weaknesses": "flaws and limitations",
    "character_arc": "potential growth trajectory"
}}

Be creative and ensure this character complements the existing cast!
    
    IMPORTANT: Return ONLY the raw JSON. Do not use Markdown code blocks (```json).
    Ensure all strings are properly escaped."""
        
        import queue
        response_queue = queue.Queue()
        
        # Use the class-level Thread class
        ai_thread = CharacterGenerationThread(self.ai_engine, prompt, response_queue)
        
        def on_ai_finished(response):
            try:
                progress.close()
                progress.deleteLater()
                
                # Clean up thread reference
                if ai_thread in self.active_threads:
                    self.active_threads.remove(ai_thread)
                
                if response.startswith("ERROR:"):
                    QMessageBox.critical(self, "Error", f"Failed to generate character:\n{response}")
                    return
                
                import json
                import re
                
                try:
                    # Basic cleanup
                    clean_response = response.replace("```json", "").replace("```", "").strip()
                    
                    # Find start of JSON
                    start_idx = clean_response.find('{')
                    if start_idx == -1:
                        raise ValueError("No JSON object found (missing '{')")
                    
                    json_str = clean_response[start_idx:]
                    
                    # Initial attempt
                    try:
                        char_data = json.loads(json_str)
                    except json.JSONDecodeError:
                        # Attempt to fix truncated JSON
                        # Common issues: missing closing quote, missing closing braces
                        logging.warning("JSON incomplete, attempting to repair...")
                        
                        repaired = False
                        # Heuristic: try closing quote if last char is not brace or quote
                        attempts = [json_str]
                        
                        # If it ends with a word character or punctuation (not quote/brace), might need quote
                        if json_str and json_str[-1] not in ['}', '"', ']']:
                             attempts.append(json_str + '"')
                             attempts.append(json_str + '"}')
                             attempts.append(json_str + '"}}')
                        
                        # Try simple brace completions
                        candidates = [json_str] + [json_str + ('}' * i) for i in range(1, 5)]
                        
                        # Combine quote repairs with brace completions
                        final_candidates = []
                        for c in candidates:
                            final_candidates.append(c)
                            final_candidates.append(c + '"')
                            final_candidates.append(c + '"}')
                        
                        # Try all candidates
                        for candidate in final_candidates:
                            try:
                                char_data = json.loads(candidate)
                                repaired = True
                                logging.info(f"Successfully repaired JSON with candidate ending: ...{candidate[-10:]}")
                                break
                            except json.JSONDecodeError:
                                continue
                        
                        if not repaired:
                            # Find the last valid '}' and try to cut off there (handle trailing garbage)
                            last_brace = json_str.rfind('}')
                            if last_brace != -1:
                                 try:
                                     char_data = json.loads(json_str[:last_brace+1])
                                     repaired = True
                                 except:
                                     pass
                        
                        if not repaired:
                            # Final fallback: Regex extraction for severely malformed/truncated output
                            logging.warning("JSON repair failed, attempting Regex fallback extraction...")
                            char_data = {}
                            
                            # Extract standard fields
                            fields = [
                                "name", "role", "pronouns", "personality_traits", "backstory", 
                                "physical_description", "speech_pattern", "motivations", 
                                "internal_conflicts", "strengths", "weaknesses", "character_arc"
                            ]
                            
                            for field in fields:
                                # Look for "field": "value" pattern, robust to newlines and escaped quotes
                                # This regex handles:
                                # 1. "key":
                                # 2. Optional whitespace
                                # 3. "value" (capturing content until next quote)
                                # Note: This is a best-effort fallback.
                                try:
                                    match = re.search(f'"{field}"\s*:\s*"(.*?)(?<!\\\\)"', json_str, re.DOTALL)
                                    if match:
                                        char_data[field] = match.group(1)
                                except:
                                    pass
                            
                            # If we found at least a name, we consider it a success
                            if char_data.get('name'):
                                logging.info("Regex fallback successful")
                            else:
                                logging.error(f"Failed to parse JSON. Raw content:\n{json_str}")
                                raise ValueError("Could not repair malformed JSON and Regex fallback failed.")
    
                    with self.db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO characters (
                                project_id, name, role, pronouns, personality_traits,
                                backstory, physical_description, speech_pattern,
                                motivations, internal_conflicts, strengths, weaknesses, character_arc,
                                physical_description
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            self.project_id,
                            char_data.get('name', 'Surprise Character'),
                            char_data.get('role', ''),
                            char_data.get('pronouns', ''),
                            char_data.get('personality_traits', ''),
                            char_data.get('backstory', ''),
                            char_data.get('physical_description', ''),
                            char_data.get('speech_pattern', ''),
                            char_data.get('motivations', ''),
                            char_data.get('internal_conflicts', ''),
                            char_data.get('strengths', ''),
                            char_data.get('weaknesses', ''),
                            char_data.get('character_arc', ''),
                            char_data.get('physical_description', '')
                        ))
                        conn.commit()
                        logging.info(f"Surprise character generated: {char_data.get('name')}")
                        self._load_characters()
                        
                        QMessageBox.information(
                            self, "Surprise! 🎉",
                            f"Meet '{char_data.get('name')}'!\n\nCharacter saved successfully."
                        )
                except Exception as e:
                    logging.error(f"Failed to parse surprise character: {e}")
                    QMessageBox.warning(
                        self, "Parsing Error",
                        f"AI generated a character but it couldn't be parsed properly.\n\nError: {str(e)}"
                    )
            except Exception as e:
                logging.error(f"Error in on_ai_finished: {e}")
            finally:
                progress.close()
                progress.deleteLater()
        
        ai_thread.finished.connect(on_ai_finished)
        self.active_threads.append(ai_thread)
        ai_thread.start()
    
    def _on_character_updated(self, character_id, field, value):
        """Handle character field update."""
        logging.info(f"Character {character_id} updated: {field} = {value[:50] if value else ''}...")
    
    def _on_character_deleted(self, character_id):
        """Handle character deletion."""
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute("DELETE FROM characters WHERE id = ?", (character_id,))
                conn.commit()
                logging.info(f"Deleted character {character_id}")
                self._load_characters()
        except Exception as e:
            logging.error(f"Failed to delete character: {e}")

