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
    QStackedWidget, QTabWidget, QToolButton
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize, pyqtSlot, QPoint
from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor, QPalette, QAction, QTextCursor

from .qt_theme import QtTheme
from .character_components import CharacterWidget


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
            current_dir = Path(__file__).parent
            bg_path = current_dir / "assets" / "backgroundimg.png"
            
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


# ============================================================================
# TOOLBAR WIDGET
# ============================================================================

class ToolbarWidget(QWidget):
    """
    Global toolbar at top - FULLY TRANSPARENT with glass effect.
    Only borders and glows visible, background image shows through.
    """
    
    action_triggered = pyqtSignal(str, str)  # (action, item)
    
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
        """Create toolbar layout with full-width even distribution."""
        layout = QHBoxLayout(self)
        # Zero horizontal margins for true full-width
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(8)
        
        # Create action buttons with stretch factors
        self._create_action_buttons(layout)
        
        # Add flexible spacer before status indicators
        layout.addStretch(2)
        
        # Create status indicators
        self._create_status_indicators(layout)
    
    def _create_action_buttons(self, layout):
        """Create action buttons with even distribution."""
        from PyQt6.QtWidgets import QSizePolicy
        
        buttons = [
            ("←", "back", None),
            ("Write ▼", "write", ["Continue Writing", "Write Scene", "Generate Opening"]),
            ("Rewrite ▼", "rewrite", ["Show Don't Tell", "Dramatic", "Gritty", "Elegant", "Concise"]),
            ("Describe ▼", "describe", ["Sight", "Sound", "Smell", "Taste", "Touch", "Metaphor"]),
            ("Brainstorm ▼", "brainstorm", ["Character Ideas", "Plot Twists", "Setting Details"]),
            ("More Tools ▼", "more_tools", ["Export", "Import", "Settings"])
        ]
        
        for text, action, menu_items in buttons:
            if action == "write":
                self.write_btn = QToolButton()
                self.write_btn.setText("Write: Auto")
                self.write_btn.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
                self.write_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                self.write_btn.setStyleSheet(f"""
                    QToolButton {{
                        background-color: transparent;
                        border: 1px solid {QtTheme.BORDER_COLOR};
                        color: {QtTheme.TEXT_MUTED};
                        border-radius: 8px;
                        padding: 8px 12px;
                        min-height: 36px;
                    }}
                    QToolButton:hover {{
                        background-color: {QtTheme.BG_HOVER};
                        color: {QtTheme.TEXT_PRIMARY};
                    }}
                    QToolButton::menu-button {{
                        border-left: 1px solid {QtTheme.BORDER_COLOR};
                        width: 20px;
                        border-top-right-radius: 8px;
                        border-bottom-right-radius: 8px;
                    }}
                """)
                
                menu = QMenu(self)
                menu.setStyleSheet(QtTheme.get_global_stylesheet())
                
                self._current_write_mode = "Auto"
                
                for item in menu_items:
                    menu_action = menu.addAction(item)
                    if item == "Write Settings":
                        menu_action.triggered.connect(lambda checked: self.action_triggered.emit("settings", "write"))
                    else:
                        menu_action.triggered.connect(lambda checked, m=item: self._set_write_mode(m))
                
                self.write_btn.setMenu(menu)
                self.write_btn.clicked.connect(lambda: self.action_triggered.emit("write", self._current_write_mode))
                layout.addWidget(self.write_btn, 2)
            
            elif action == "describe":
                self.describe_btn = QToolButton()
                self.describe_btn.setText("Describe")
                self.describe_btn.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
                self.describe_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                self.describe_btn.setStyleSheet(self.write_btn.styleSheet()) # Reuse style
                
                menu = QMenu(self)
                menu.setStyleSheet(QtTheme.get_global_stylesheet())
                
                self.sense_actions = {}
                self.sense_actions = {}
                from PyQt6.QtWidgets import QWidgetAction, QCheckBox
                
                for item in menu_items:
                    # Create custom widget action for toggle button
                    widget_action = QWidgetAction(menu)
                    
                    # Create container widget
                    container = QWidget()
                    container_layout = QHBoxLayout(container)
                    container_layout.setContentsMargins(10, 5, 20, 5) # Indent for alignment
                    
                    # Label
                    label = QLabel(item)
                    label.setStyleSheet(f"color: {QtTheme.TEXT_PRIMARY}; font-size: 14px;")
                    
                    # Toggle Checkbox (styled as simply as possible for now)
                    checkbox = QCheckBox()
                    checkbox.setStyleSheet(f"""
                        QCheckBox::indicator {{
                            width: 18px;
                            height: 18px;
                            border: 1px solid {QtTheme.BORDER_COLOR};
                            border-radius: 4px;
                            background: transparent;
                        }}
                        QCheckBox::indicator:checked {{
                            background: {QtTheme.ACCENT_PRIMARY};
                            border: 1px solid {QtTheme.ACCENT_PRIMARY};
                        }}
                    """)
                    
                    container_layout.addWidget(label)
                    container_layout.addStretch()
                    container_layout.addWidget(checkbox)
                    
                    widget_action.setDefaultWidget(container)
                    menu.addAction(widget_action)
                    
                    # Store action and logic
                    self.sense_actions[item] = checkbox # Store checkbox directly for easy access
                    checkbox.toggled.connect(self._update_describe_visuals)
                    
                    # HACK: Prevent menu closing on internal widget click? 
                    # Actually QAction triggered usually closes it.
                    # QCheckBox click might not close menu if handled inside widget.
                
                self.describe_btn.setMenu(menu)
                self.describe_btn.clicked.connect(lambda: self.action_triggered.emit("describe", "current"))
                layout.addWidget(self.describe_btn, 2)

            else:
                 # Hidden buttons logic if we were to show them
                 pass
                 
    def _set_write_mode(self, mode: str):
        self._current_write_mode = mode
        self.write_btn.setText(f"Write: {mode}")

    def _update_describe_visuals(self):
        """Update Describe button visuals based on active toggles."""
        # Visual feedback for active toggles can be added here
        pass
            
    def get_active_senses(self) -> List[str]:
        """Get list of active sensory toggles."""
        if not hasattr(self, 'sense_actions'):
            return []
        return [sense for sense, checkbox in self.sense_actions.items() if checkbox.isChecked()]
    
    def _create_status_indicators(self, layout):
        """Create status indicators with fixed positioning."""
        self.word_count_label = QLabel("Words: 0")
        self.word_count_label.setFont(QtTheme.get_font_ui())
        self.word_count_label.setStyleSheet(f"color: {QtTheme.TEXT_MUTED}; padding: 0 8px;")
        layout.addWidget(self.word_count_label, 0)  # No stretch - fixed size
        
        self.save_status_label = QLabel("Saved ✓")
        self.save_status_label.setFont(QtTheme.get_font_ui())
        self.save_status_label.setStyleSheet(f"color: {QtTheme.ACCENT_PRIMARY}; padding: 0 8px;")
        layout.addWidget(self.save_status_label, 0)  # No stretch - fixed size
        
        for text, action in [("📤", "export"), ("?", "help"), ("⚙️", "settings")]:
            btn = QPushButton(text)
            btn.setFixedSize(32, 32)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    color: {QtTheme.TEXT_MUTED};
                }}
                QPushButton:hover {{
                    background-color: {QtTheme.BG_HOVER};
                    border-radius: 4px;
                }}
            """)
            btn.clicked.connect(lambda checked, a=action: self.action_triggered.emit(a, ""))
            layout.addWidget(btn)
    
    def update_word_count(self, count: int):
        """Update word counter display."""
        self.word_count_label.setText(f"Words: {count}")
    
    def set_save_status(self, saved: bool):
        """Update save status indicator."""
        if saved:
            self.save_status_label.setText("Saved ✓")
            self.save_status_label.setStyleSheet(f"color: {QtTheme.ACCENT_PRIMARY};")
        else:
            self.save_status_label.setText("Saving...")
            self.save_status_label.setStyleSheet(f"color: {QtTheme.TEXT_MUTED};")


# ============================================================================
# TRANSPARENT SCROLL AREA
# ============================================================================

class TransparentScrollArea(QScrollArea):
    """
    Scroll area with STRICT TRANSPARENCY.
    Shows background image through all layers.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # STRICT TRANSPARENCY
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
        
        # Ensure viewport is transparent
        viewport = self.viewport()
        viewport.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        viewport.setAutoFillBackground(False)
        viewport.setStyleSheet("background-color: transparent;")


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
    
    def refresh_tree(self, active_chapter_id=None):
        """Refresh project tree display."""
        # Clear existing items
        while self.tree_layout.count() > 1:
            item = self.tree_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        projects = self.db_manager.get_projects_with_chapters()
        
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
        
        # Editor textbox (BLACK OVERLAY for readability - text + cursor visible)
        self.editor_textbox = QTextEdit()
        self.editor_textbox.setFont(QtTheme.get_font_prose())
        self.editor_textbox.setMinimumHeight(600)
        
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
        self.content_layout.addWidget(self.editor_textbox)
        
        # Action buttons
        actions_widget = self._create_action_buttons()
        self.content_layout.addWidget(actions_widget)
    
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
        logging.info(f"Format action applied: {action}")
    
    def _show_document_menu(self):
        """Show document options menu."""
        menu = QMenu(self)
        menu.addAction("Rename", lambda: logging.info("Rename document"))
        menu.addAction("Export", lambda: logging.info("Export document"))
        menu.addSeparator()
        menu.addAction("Delete", lambda: logging.info("Delete document"))
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
        
        # Header (transparent)
        header = QLabel(section_name)
        header.setFont(QtTheme.get_font_h3())
        header.setStyleSheet(f"color: {QtTheme.TEXT_PRIMARY}; background-color: transparent;")
        card_layout.addWidget(header)
        
        # Text input (black tinted glass)
        text_input = QTextEdit()
        text_input.setPlaceholderText(placeholder)
        text_input.setMinimumHeight(150)
        
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
        
        text_input.textChanged.connect(lambda: self._on_bible_field_change(section_key))
        card_layout.addWidget(text_input)
        
        # Store references
        self.bible_section_widgets[section_key] = {
            'card': card,
            'widget': text_input
        }
        
        parent_layout.addWidget(card)
    
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
        self.character_widget = CharacterWidget(self.db_manager, self.ai_engine)
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
            return
        
        # Get field value
        if field_name == 'style':
            value = self.style_selection
        elif field_name in self.bible_section_widgets:
            widget_data = self.bible_section_widgets[field_name]
            if widget_data['widget'] and isinstance(widget_data['widget'], QTextEdit):
                value = widget_data['widget'].toPlainText()
            else:
                return
        else:
            return
        
        # Save to database (debounced in real implementation)
        try:
            self.db_manager.save_bible_field(self.current_project_id, field_name, value)
        except Exception as e:
            logging.error(f"Failed to save {field_name}: {e}")
    
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
            logging.info(f"Set character_widget project_id to {project_id}")
        
        # Load Story Bible data if container exists
        if self.story_bible_container:
            try:
                bible_data = self.db_manager.get_story_bible(project_id)
                if bible_data:
                    for field in ["braindump", "genre", "synopsis", "worldbuilding", "outline"]:
                        if field in bible_data and bible_data[field]:
                            if field in self.bible_section_widgets:
                                widget_data = self.bible_section_widgets[field]
                                if isinstance(widget_data['widget'], QTextEdit):
                                    widget_data['widget'].setPlainText(bible_data[field])
                    
                    # Load style
                    if 'style' in bible_data and bible_data['style']:
                        self._select_style(bible_data['style'])
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
                self.editor_textbox.setPlainText(content if content else "")
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
        """Create the main UI structure."""
        # Background widget as central widget
        self.background_widget = BackgroundWidget()
        self.setCentralWidget(self.background_widget)
        
        # Main layout
        main_layout = QVBoxLayout(self.background_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Toolbar (fixed at top)
        self.toolbar = ToolbarWidget()
        main_layout.addWidget(self.toolbar)
        
        # Content area (3-column layout) - TRANSPARENT
        content_widget = QWidget()
        content_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        content_widget.setAutoFillBackground(False)
        content_widget.setStyleSheet("background-color: transparent;")
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Left panel (sidebar)
        self.left_panel = ProjectSidebar(self.db_manager)
        content_layout.addWidget(self.left_panel, 18)
        
        # Center panel (writing area) - pass ai_engine for character generation
        self.center_panel = CenterPanel(self.db_manager, self.ai_engine)
        content_layout.addWidget(self.center_panel, 60)
        
        # Right panel (assistant)
        self.right_panel = AssistantPanel()
        content_layout.addWidget(self.right_panel, 22)
        
        main_layout.addWidget(content_widget)
    
    def _connect_signals(self):
        """Connect signals and slots."""
        self.toolbar.action_triggered.connect(self._handle_toolbar_action)
        self.left_panel.chapter_selected.connect(self._load_chapter)
        self.left_panel.bible_section_clicked.connect(self._scroll_to_bible_section)
        self.left_panel.trash_clicked.connect(self._show_trash)
        self.center_panel.content_changed.connect(self._on_content_change)
        self.center_panel.action_requested.connect(self._handle_action)
        self.right_panel.chat_sent.connect(self._handle_chat)
        self.right_panel.insert_requested.connect(self.insert_text_to_editor)
    
    def insert_text_to_editor(self, text):
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
        logging.info(f"Toolbar action: {action} - {item}")
        
        if action == "write":
            if item == "Continue Writing":
                self._handle_ai_request("Continue writing from where I left off", 'editor')
            elif item == "Write Scene":
                self._handle_ai_request("Write a new scene", 'editor')
            elif item == "Generate Opening":
                self._handle_ai_request("Generate an opening paragraph", 'editor')
        elif action == "rewrite":
            self._handle_ai_request(f"PLUGIN::rewrite_{item.lower().replace(' ', '_')}::", 'editor')
        elif action == "describe":
            # 1. Validation: Require selection
            selected_text = self.center_panel.get_selected_text()
            if not selected_text.strip():
                # Non-blocking warning as requested
                QMessageBox.warning(self, "Selection Required", "Please select text to describe.")
                return

            # 2. Collect Active Senses
            active_senses = self.toolbar.get_active_senses()
            
            # 3. Construct Prompt
            prompt = f"DESCRIBE::{selected_text}"
            if active_senses:
                prompt += f"::SENSES::{','.join(active_senses)}"
            
            self._handle_ai_request(prompt, 'assistant')

        elif action == "brainstorm":
            self._handle_ai_request(f"Brainstorm: {item}", 'assistant')
        elif action == "export":
            self._export_document()
        elif action == "help":
            self._show_help()
        elif action == "settings":
            logging.info("Settings clicked")
    
    @pyqtSlot(int, int)
    def _load_chapter(self, chapter_id: int, project_id: int):
        """Load chapter into center panel."""
        self.current_chapter_id = chapter_id
        self.current_project_id = project_id
        
        self.center_panel.load_project(project_id, chapter_id)
        self._on_content_change()
        
        self.left_panel.refresh_tree(chapter_id)
    
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
        logging.info("Show trash clicked")
    
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
        """Export current document."""
        logging.info("Export document")
    
    def _show_help(self):
        """Show help dialog."""
        QMessageBox.information(self, "Help", "Story Bible Pro - AI Writing Assistant")
    
    def load_session(self):
        """Load last session from database."""
        last_pid = self.db_manager.get_app_state("last_project_id")
        last_cid = self.db_manager.get_app_state("last_chapter_id")
        
        if last_cid and last_pid:
            try:
                self._load_chapter(int(last_cid), int(last_pid))
            except:
                pass
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.current_chapter_id:
            text = self.center_panel.get_editor_content()
            self.db_manager.update_chapter_content(self.current_chapter_id, text)
        
        if self.current_project_id:
            self.db_manager.save_app_state("last_project_id", self.current_project_id)
        if self.current_chapter_id:
            self.db_manager.save_app_state("last_chapter_id", self.current_chapter_id)
        
        if hasattr(self.ai_engine, "unload_model"):
            self.ai_engine.unload_model()
        
        event.accept()


