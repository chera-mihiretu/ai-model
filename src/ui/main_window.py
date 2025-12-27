import customtkinter as ctk
import tkinter as tk
import threading
import queue
import time
import logging
from .theme_engine import ThemeEngine
from src.ui.character_frame import CharacterFrame
from src.ui.story_bible_view import StoryBibleView
from src.ui.story_bible_drawer import StoryBibleDrawer

# --- CUSTOM COMPONENTS ---

# ============================================================================
# TOOLBAR FRAME - Fixed Global Top Bar
# ============================================================================

class ToolbarFrame(ctk.CTkFrame):
    """
    Global fixed toolbar at top of window.
    Contains:
    - Left: Dropdown buttons (Back, Write, Rewrite, Describe, Brainstorm, More Tools)
    - Right: Status indicators (word count, save status, icons)
    """
    def __init__(self, master, on_action):
        super().__init__(
            master,
            height=ThemeEngine.TOOLBAR_HEIGHT,
            fg_color=ThemeEngine.BG_SIDEBAR,
            corner_radius=0
        )
        self.on_action = on_action
        
        # Prevent height from collapsing
        self.grid_propagate(False)
        
        # Layout: Left section | Spacer | Right section
        self.grid_columnconfigure(1, weight=1)
        
        # Left section
        self.left_section = ctk.CTkFrame(self, fg_color="transparent")
        self.left_section.grid(row=0, column=0, sticky="w", padx=20, pady=10)
        
        self._create_left_buttons()
        
        # Right section
        self.right_section = ctk.CTkFrame(self, fg_color="transparent")
        self.right_section.grid(row=0, column=2, sticky="e", padx=20, pady=10)
        
        self._create_right_indicators()
    
    def _create_left_buttons(self):
        """Create left-aligned dropdown buttons."""
        buttons_config = [
            ("←", "back", None),
            ("Write ▼", "write", ["Continue Writing", "Write Scene", "Generate Opening"]),
            ("Rewrite ▼", "rewrite", ["Show Don't Tell", "Dramatic", "Gritty", "Elegant", "Concise"]),
            ("Describe ▼", "describe", ["Sight", "Sound", "Smell", "Taste", "Touch", "Metaphor"]),
            ("Brainstorm ▼", "brainstorm", ["Character Ideas", "Plot Twists", "Setting Details"]),
            ("More Tools ▼", "more_tools", ["Export", "Import", "Settings"])
        ]
        
        for idx, (text, action, menu_items) in enumerate(buttons_config):
            btn = ctk.CTkButton(
                self.left_section,
                text=text,
                width=100 if idx > 0 else 40,  # Back button is smaller
                height=36,
                fg_color="transparent",
                text_color=ThemeEngine.TEXT_MUTED,
                hover_color=ThemeEngine.BG_HOVER,
                border_width=1,
                border_color=ThemeEngine.BORDER_COLOR,
                corner_radius=8,
                command=lambda a=action, m=menu_items: self._handle_button_click(a, m)
            )
            btn.pack(side="left", padx=4)
            
            # Store reference for menu handling
            if menu_items:
                btn.bind("<Button-1>", lambda e, a=action, m=menu_items, b=btn: self._show_dropdown(e, b, a, m))
    
    def _handle_button_click(self, action, menu_items):
        """Handle button click - either direct action or show menu."""
        if not menu_items:
            self.on_action(action, None)
    
    def _show_dropdown(self, event, button, action, items):
        """Show dropdown menu below button."""
        menu = tk.Menu(self, tearoff=0, bg=ThemeEngine.BG_SIDEBAR, fg=ThemeEngine.TEXT_PRIMARY,
                      activebackground=ThemeEngine.BG_HOVER, activeforeground=ThemeEngine.ACCENT_PRIMARY,
                      bd=0, relief="flat")
        
        for item in items:
            menu.add_command(
                label=item,
                command=lambda a=action, i=item: self.on_action(a, i)
            )
        
        # Show menu below button
        x = button.winfo_rootx()
        y = button.winfo_rooty() + button.winfo_height()
        menu.post(x, y)
    
    def _create_right_indicators(self):
        """Create right-aligned status indicators."""
        # Word counter
        self.word_count_label = ctk.CTkLabel(
            self.right_section,
            text="Words: 0",
            font=ThemeEngine.FONT_UI,
            text_color=ThemeEngine.TEXT_MUTED
        )
        self.word_count_label.pack(side="left", padx=10)
        
        # Save status
        self.save_status = ctk.CTkLabel(
            self.right_section,
            text="Saved ✓",
            font=ThemeEngine.FONT_UI,
            text_color=ThemeEngine.ACCENT_PRIMARY
        )
        self.save_status.pack(side="left", padx=10)
        
        # Export icon
        self.export_btn = ctk.CTkButton(
            self.right_section,
            text="📤",
            width=32,
            height=32,
            fg_color="transparent",
            hover_color=ThemeEngine.BG_HOVER,
            command=lambda: self.on_action("export", None)
        )
        self.export_btn.pack(side="left", padx=4)
        
        # Help icon
        self.help_btn = ctk.CTkButton(
            self.right_section,
            text="?",
            width=32,
            height=32,
            fg_color="transparent",
            hover_color=ThemeEngine.BG_HOVER,
            command=lambda: self.on_action("help", None)
        )
        self.help_btn.pack(side="left", padx=4)
        
        # Settings icon
        self.settings_btn = ctk.CTkButton(
            self.right_section,
            text="⚙️",
            width=32,
            height=32,
            fg_color="transparent",
            hover_color=ThemeEngine.BG_HOVER,
            command=lambda: self.on_action("settings", None)
        )
        self.settings_btn.pack(side="left", padx=4)
    
    def update_word_count(self, count):
        """Update word counter display."""
        self.word_count_label.configure(text=f"Words: {count}")
    
    def set_save_status(self, saved):
        """Update save status indicator."""
        if saved:
            self.save_status.configure(text="Saved ✓", text_color=ThemeEngine.ACCENT_PRIMARY)
        else:
            self.save_status.configure(text="Saving...", text_color=ThemeEngine.TEXT_MUTED)


# ============================================================================
# CENTER SCROLL PANEL - Writing Canvas + Conditional Story Bible
# ============================================================================

class CenterScrollPanel(ctk.CTkScrollableFrame):
    """
    Single continuous vertical scroll containing:
    1. Writing Canvas (ALWAYS at top)
    2. Story Bible Sections (CONDITIONAL below, only when toggled ON)
    
    NO tabs, NO mode switching. Pure vertical scroll.
    """
    def __init__(self, master, db_manager, on_content_change):
        super().__init__(
            master,
            fg_color=ThemeEngine.BG_MAIN,
            scrollbar_button_color=ThemeEngine.BORDER_COLOR,
            scrollbar_button_hover_color=ThemeEngine.ACCENT_PRIMARY,
            corner_radius=0
        )
        
        self.db_manager = db_manager
        self.on_content_change = on_content_change
        self.current_project_id = None
        self.current_chapter_id = None
        self.save_debounce_id = None
        
        # Story Bible state
        self.story_bible_container = None
        self.bible_section_refs = {}  # For scroll anchors
        
        # Configure grid for full width content
        self.grid_columnconfigure(0, weight=1)
        
        # Create content container (fully contained, max width)
        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        
        # ===== SECTION 1: WRITING CANVAS (ALWAYS FIRST) =====
        self._create_writing_canvas()
        
        # Story Bible sections created only when toggled ON
    
    def _create_writing_canvas(self):
        """Create the main writing area (always at top)."""
        # Document Header
        header_frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))
        
        self.document_title = ctk.CTkEntry(
            header_frame,
            height=50,
            fg_color="transparent",
            text_color=ThemeEngine.TEXT_PRIMARY,
            border_width=0,
            font=("Inter", 24, "bold"),
            placeholder_text="Untitled Document"
        )
        self.document_title.pack(side="left", fill="x", expand=True)
        
        # Document menu button (ellipsis)
        self.doc_menu_btn = ctk.CTkButton(
            header_frame,
            text="⋮",
            width=40,
            height=40,
            fg_color="transparent",
            hover_color=ThemeEngine.BG_HOVER,
            text_color=ThemeEngine.TEXT_MUTED,
            font=("Inter", 20),
            command=self._show_document_menu
        )
        self.doc_menu_btn.pack(side="right", padx=10)
        
        # Formatting Toolbar
        self._create_formatting_toolbar()
        
        # Editor Canvas
        self.editor_textbox = ctk.CTkTextbox(
            self.content_container,
            fg_color="transparent",
            text_color=ThemeEngine.TEXT_PRIMARY,
            font=ThemeEngine.FONT_PROSE,
            wrap="word",
            border_width=0,
            height=600,  # Initial height, expands as needed
            undo=True,
            spacing3=10
        )
        self.editor_textbox.pack(fill="both", expand=True, pady=20)
        self.editor_textbox.bind("<KeyRelease>", lambda e: self.on_content_change())
        
        # Action Buttons
        self._create_action_buttons()
    
    def _create_formatting_toolbar(self):
        """Create formatting toolbar with icons."""
        toolbar = ctk.CTkFrame(
            self.content_container,
            height=50,
            fg_color=ThemeEngine.BG_SIDEBAR,
            corner_radius=8
        )
        toolbar.pack(fill="x", pady=(0, 10))
        
        # Formatting buttons
        buttons = [
            ("↶", "undo"),
            ("↷", "redo"),
            ("B", "bold"),
            ("I", "italic"),
            ("U", "underline"),
            ("S", "strikethrough"),
            ("•", "bullet"),
            ("1.", "numbered"),
            ("Aa", "font"),
            ("H1", "h1"),
            ("H2", "h2"),
            ("H3", "h3")
        ]
        
        for text, action in buttons:
            btn = ctk.CTkButton(
                toolbar,
                text=text,
                width=36,
                height=36,
                fg_color="transparent",
                hover_color=ThemeEngine.BG_HOVER,
                text_color=ThemeEngine.TEXT_MUTED,
                font=("Inter", 14, "bold") if text in ["B", "I", "U"] else ("Inter", 14),
                command=lambda a=action: self._format_action(a)
            )
            btn.pack(side="left", padx=2, pady=7)
    
    def _create_action_buttons(self):
        """Create AI action buttons at bottom of editor."""
        btn_container = ctk.CTkFrame(self.content_container, fg_color="transparent")
        btn_container.pack(fill="x", pady=20)
        
        buttons = [
            ("Generate a Rough Draft", "generate_draft"),
            ("Generate 3 Openings", "generate_openings"),
            ("Chat About an Idea", "chat_idea")
        ]
        
        for text, action in buttons:
            btn = ctk.CTkButton(
                btn_container,
                text=text,
                height=44,
                fg_color=ThemeEngine.ACCENT_SECONDARY,
                hover_color=ThemeEngine.ACCENT_HOVER,
                text_color=ThemeEngine.TEXT_PRIMARY,
                corner_radius=10,
                font=("Inter", 14),
                command=lambda a=action: self.on_content_change(action_type=a)
            )
            btn.pack(side="left", expand=True, fill="x", padx=8)
    
    def _format_action(self, action):
        """Handle formatting actions."""
        logging.info(f"Format action: {action}")
        # TODO: Implement rich text formatting
    
    def _show_document_menu(self):
        """Show document options menu."""
        menu = tk.Menu(self, tearoff=0, bg=ThemeEngine.BG_SIDEBAR, fg=ThemeEngine.TEXT_PRIMARY,
                      activebackground=ThemeEngine.BG_HOVER, activeforeground=ThemeEngine.ACCENT_PRIMARY,
                      bd=0)
        menu.add_command(label="Rename", command=lambda: logging.info("Rename document"))
        menu.add_command(label="Export", command=lambda: logging.info("Export document"))
        menu.add_separator()
        menu.add_command(label="Delete", command=lambda: logging.info("Delete document"))
        
        # Show menu at button position
        x = self.doc_menu_btn.winfo_rootx()
        y = self.doc_menu_btn.winfo_rooty() + self.doc_menu_btn.winfo_height()
        menu.post(x, y)
    
    # ============================================================
    # STORY BIBLE - CONDITIONAL CONTENT (BELOW WRITING CANVAS)
    # ============================================================
    
    def create_story_bible_container(self):
        """Create Story Bible sections below writing canvas."""
        if self.story_bible_container:
            return  # Already exists
        
        # Add spacer before Story Bible
        spacer = ctk.CTkFrame(self.content_container, height=80, fg_color="transparent")
        spacer.pack(fill="x")
        
        # Create Story Bible container
        self.story_bible_container = ctk.CTkFrame(
            self.content_container,
            fg_color="transparent"
        )
        self.story_bible_container.pack(fill="both", expand=True)
        
        # Story Bible Header
        header_frame = ctk.CTkFrame(self.story_bible_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            header_frame,
            text="Story Bible",
            font=("Inter", 28, "bold"),
            text_color=ThemeEngine.TEXT_PRIMARY,
            anchor="w"
        ).pack(side="top", anchor="w")
        
        ctk.CTkLabel(
            header_frame,
            text="Build your story world. This context helps the AI write consistently.",
            font=ThemeEngine.FONT_UI,
            text_color=ThemeEngine.TEXT_MUTED,
            anchor="w"
        ).pack(side="top", anchor="w", pady=(5, 0))
        
        # Create 7 Story Bible sections
        sections = [
            ("Braindump", "What's your story about? Free-form notes, ideas, themes..."),
            ("Genre", "e.g., Fantasy, Sci-Fi, Mystery, Romance"),
            ("Style", None),  # Special handling
            ("Synopsis", "Brief overview of your story arc..."),
            ("Characters", "Main characters, their roles, arcs..."),
            ("Worldbuilding", "Settings, culture, rules, magic systems..."),
            ("Outline", "Plot structure, key events, timeline...")
        ]
        
        for section_name, placeholder in sections:
            if section_name == "Style":
                self._create_style_section()
            elif section_name == "Characters":
                self._create_characters_section()
            else:
                self._create_bible_section(section_name, placeholder)
    
    def _create_bible_section(self, section_name, placeholder):
        """Create a Story Bible section with consistent styling."""
        # Section container (for scroll anchor)
        section_container = ctk.CTkFrame(
            self.story_bible_container,
            fg_color=ThemeEngine.CARD_BG,
            corner_radius=ThemeEngine.CARD_CORNER_RADIUS,
            border_width=1,
            border_color=ThemeEngine.BORDER_COLOR
        )
        section_container.pack(fill="x", pady=ThemeEngine.CARD_SPACING)
        
        # Store reference for scroll-to-section
        self.bible_section_refs[section_name.lower()] = section_container
        
        # Section header
        ctk.CTkLabel(
            section_container,
            text=section_name,
            font=("Inter", 16, "bold"),
            text_color=ThemeEngine.TEXT_PRIMARY,
            anchor="w"
        ).pack(anchor="w", padx=ThemeEngine.CARD_PADDING, pady=(ThemeEngine.CARD_PADDING, 10))
        
        # Input field (multiline textarea)
        input_widget = ctk.CTkTextbox(
            section_container,
            height=150,
            fg_color=ThemeEngine.BG_INPUT,
            text_color=ThemeEngine.TEXT_PRIMARY,
            border_width=1,
            border_color=ThemeEngine.BORDER_COLOR,
            corner_radius=8,
            font=ThemeEngine.FONT_UI,
            wrap="word"
        )
        input_widget.pack(fill="x", padx=ThemeEngine.CARD_PADDING, pady=(0, ThemeEngine.CARD_PADDING))
        
        # Bind autosave
        field_name = section_name.lower()
        input_widget.bind("<KeyRelease>", lambda e: self._debounced_save(field_name))
        input_widget.bind("<FocusOut>", lambda e: self._force_save(field_name))
        
        # Store reference
        setattr(self, f"{field_name}_input", input_widget)
    
    def _create_characters_section(self):
        """Create functional Character Profile section using shared CharacterFrame."""
        # Container
        card = ctk.CTkFrame(
            self.story_bible_container,
            fg_color=ThemeEngine.CARD_BG,
            corner_radius=ThemeEngine.CARD_CORNER_RADIUS,
            border_width=1,
            border_color=ThemeEngine.BORDER_COLOR
        )
        card.pack(fill="x", pady=ThemeEngine.CARD_SPACING)
        
        # Scroll anchor
        self.bible_section_refs["characters"] = card
        
        # Header
        ctk.CTkLabel(
            card,
            text="Characters",
            font=("Inter", 16, "bold"),
            text_color=ThemeEngine.TEXT_PRIMARY,
            anchor="w"
        ).pack(anchor="w", padx=ThemeEngine.CARD_PADDING, pady=(ThemeEngine.CARD_PADDING, 10))
        
        # Import CharacterFrame
        # Note: CharacterFrame is already imported at top level
        
        # Create Frame
        self.character_frame = CharacterFrame(card, self.db_manager)
        self.character_frame.pack(fill="x", padx=ThemeEngine.CARD_PADDING, pady=(0, ThemeEngine.CARD_PADDING))
        
        # Set project ID if known
        if self.current_project_id:
            self.character_frame.project_id = self.current_project_id
            self.character_frame.load_list()

    # _add_trait_row, _on_save_character, _refresh_character_list no longer needed here
    # as they are handled inside CharacterFrame. 
    # Validating removal.
    

    
    def _create_style_section(self):
        """Create Style selection section with buttons."""
        card = ctk.CTkFrame(
            self.story_bible_container,
            fg_color=ThemeEngine.CARD_BG,
            corner_radius=ThemeEngine.CARD_CORNER_RADIUS,
            border_width=1,
            border_color=ThemeEngine.BORDER_COLOR
        )
        card.pack(fill="x", pady=ThemeEngine.CARD_SPACING)
        
        # Store reference for scroll anchor
        self.bible_section_refs["style"] = card
        
        # Card header
        ctk.CTkLabel(
            card,
            text="Style",
            font=("Inter", 16, "bold"),
            text_color=ThemeEngine.TEXT_PRIMARY,
            anchor="w"
        ).pack(anchor="w", padx=ThemeEngine.CARD_PADDING, pady=(ThemeEngine.CARD_PADDING, 10))
        
        # Button container
        btn_container = ctk.CTkFrame(card, fg_color="transparent")
        btn_container.pack(fill="x", padx=ThemeEngine.CARD_PADDING, pady=(0, ThemeEngine.CARD_PADDING))
        
        self.style_selection = "Featured Styles"  # Default
        
        styles = ["Featured Styles", "Match My Style", "Custom"]
        self.style_buttons = {}
        
        for style in styles:
            btn = ctk.CTkButton(
                btn_container,
                text=style,
                height=40,
                fg_color="transparent",
                border_width=2,
                border_color=ThemeEngine.BORDER_COLOR,
                text_color=ThemeEngine.TEXT_MUTED,
                hover_color=ThemeEngine.BG_HOVER,
                command=lambda s=style: self._select_style(s)
            )
            btn.pack(side="left", expand=True, fill="x", padx=4)
            self.style_buttons[style] = btn
        
        # Set default selection
        self._select_style("Featured Styles")
    
    def _select_style(self, style):
        """Handle style button selection."""
        self.style_selection = style
        
        # Update button states
        for s, btn in self.style_buttons.items():
            if s == style:
                btn.configure(
                    fg_color=ThemeEngine.ACCENT_PRIMARY,
                    border_color=ThemeEngine.ACCENT_PRIMARY,
                    text_color=ThemeEngine.TEXT_PRIMARY
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    border_color=ThemeEngine.BORDER_COLOR,
                    text_color=ThemeEngine.TEXT_MUTED
                )
        
        self._force_save("style")
    
    def destroy_story_bible_container(self):
        """Remove Story Bible from center panel."""
        if self.story_bible_container:
            self.story_bible_container.destroy()
            self.story_bible_container = None
            self.bible_section_refs.clear()
    
    def scroll_to_section(self, section_name):
        """Scroll to specific Story Bible section."""
        if not self.story_bible_container:
            return  # Story Bible is OFF
        
        section_key = section_name.lower()
        if section_key in self.bible_section_refs:
            widget = self.bible_section_refs[section_key]
            # Force update to get correct positions
            widget.update_idletasks()
            # Get widget's y position relative to scrollable frame
            y_pos = widget.winfo_y()
            # Scroll to position
            self._parent_canvas.yview_moveto(y_pos / self._parent_canvas.winfo_height())
    
    def _debounced_save(self, field_name):
        """Debounce save calls to avoid excessive DB writes."""
        if self.save_debounce_id:
            self.after_cancel(self.save_debounce_id)
        self.save_debounce_id = self.after(500, lambda: self._force_save(field_name))
    
    def _force_save(self, field_name):
        """Immediately save field to database."""
        if not self.current_project_id:
            return
        
        # Get field value
        if field_name == "style":
            value = self.style_selection
        else:
            widget = getattr(self, f"{field_name}_input", None)
            if not widget:
                return
            
            if isinstance(widget, ctk.CTkTextbox):
                value = widget.get("1.0", "end-1c")
            else:
                value = widget.get()
        
        # Save to database
        try:
            # Use save_bible_field for Story Bible fields
            self.db_manager.save_bible_field(self.current_project_id, field_name, value)
            logging.info(f"Saved {field_name}")
        except Exception as e:
            logging.error(f"Failed to save {field_name}: {e}")
    
    def load_project(self, project_id, chapter_id=None):
        """Load project data."""
        self.current_project_id = project_id
        self.current_chapter_id = chapter_id
        
        # Load Story Bible data if container exists
        if self.story_bible_container:
            try:
                # Use get_story_bible to fetch all Story Bible fields
                bible_data = self.db_manager.get_story_bible(project_id)
                if bible_data:
                    # Load all Story Bible fields (Characters handled separately)
                    for field in ["braindump", "genre", "style", "synopsis", 
                                 "worldbuilding", "outline"]:
                        if field in bible_data and bible_data[field]:
                            if field == "style":
                                self._select_style(bible_data[field])
                            else:
                                widget = getattr(self, f"{field}_input", None)
                                if widget:
                                    widget.delete("1.0", "end")
                                    widget.insert("1.0", bible_data[field])
                    
                    # Refresh characters list via Frame
                    if hasattr(self, 'character_frame'):
                        self.character_frame.project_id = project_id
                        self.character_frame.load_list()

            except Exception as e:
                logging.error(f"Failed to load story bible: {e}")
        
        # Load chapter content
        if chapter_id:
            try:
                # Get chapter content using get_chapter_content
                content = self.db_manager.get_chapter_content(chapter_id)
                
                # Get chapter title from projects list
                title = "Untitled"
                projects = self.db_manager.get_projects_with_chapters()
                for p in projects:
                    if p['id'] == project_id:
                        for ch in p['chapters']:
                            if ch['id'] == chapter_id:
                                title = ch['title']
                                break
                        break
                
                # Update document title
                self.document_title.delete(0, "end")
                self.document_title.insert(0, title)
                
                # Update editor content
                self.editor_textbox.delete("1.0", "end")
                if content:
                    self.editor_textbox.insert("1.0", content)
            except Exception as e:
                logging.error(f"Failed to load chapter: {e}")
    
    def get_editor_content(self):
        """Get current editor content."""
        return self.editor_textbox.get("1.0", "end-1c")
    
    def insert_editor_content(self, text, position="insert"):
        """Insert text into editor at specified position."""
        self.editor_textbox.insert(position, text)
        self.editor_textbox.see(position)


# ============================================================================
# SIDEBAR & OTHER COMPONENTS (Continue from original)
# ============================================================================


class SidebarButton(ctk.CTkFrame):
    """
    Custom widget for Sidebar Navigation.
    Features: Hover fade, Active Pill indicator.
    """
    def __init__(self, master, text, command, active=False):
        super().__init__(master, fg_color="transparent", corner_radius=6, height=40)
        self.command = command
        self.is_active = active
        self.text = text
        
        # Layout: [Pill (3px)] [Spacer (12px)] [Text]
        self.grid_columnconfigure(2, weight=1)
        
        # 1. Pill Indicator (Hidden by default)
        self.pill = ctk.CTkFrame(self, width=3, height=20, corner_radius=10, fg_color="transparent")
        self.pill.pack(side="left", padx=(0, 12), pady=10)
        
        # 2. Label
        self.label = ctk.CTkLabel(
            self, 
            text=text, 
            font=ThemeEngine.FONT_UI,
            text_color=ThemeEngine.TEXT_MUTED,
            anchor="w"
        )
        self.label.pack(side="left", fill="both", expand=True, pady=8)
        
        # Events
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.label.bind("<Button-1>", self.on_click)
        
        if active:
            self.set_active(True)

    def on_enter(self, event):
        if not self.is_active:
            self.configure(fg_color=ThemeEngine.BG_HOVER)

    def on_leave(self, event):
        if not self.is_active:
            self.configure(fg_color="transparent")

    def on_click(self, event):
        self.command()

    def set_active(self, active):
        self.is_active = active
        if active:
            self.configure(fg_color=ThemeEngine.BG_HOVER)
            self.pill.configure(fg_color=ThemeEngine.ACCENT_PRIMARY)
            self.label.configure(text_color=ThemeEngine.ACCENT_PRIMARY)
        else:
            self.configure(fg_color="transparent")
            self.pill.configure(fg_color="transparent")
            self.label.configure(text_color=ThemeEngine.TEXT_MUTED)


class SidebarFrame(ctk.CTkFrame):
    """Left Sidebar: Navigation + Project Tree (250px)."""
    def __init__(self, master, db_manager, on_nav_select, on_chapter_select, on_generate_from_beats=None, on_auto_generate_beats=None):
        super().__init__(master, width=250, fg_color=ThemeEngine.BG_SIDEBAR, corner_radius=0)
        self.db_manager = db_manager
        self.on_nav_select = on_nav_select
        self.on_chapter_select = on_chapter_select
        self.on_generate_from_beats = on_generate_from_beats or (lambda: None)
        self.on_auto_generate_beats = on_auto_generate_beats or (lambda: None)
        self.nav_buttons = {}
        self.current_menu = None  # Track currently open context menu
        
        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Tree expands
        
        # 1. Projects Header
        self._create_header()
        
        # 2. Project Tree
        self.project_tree = ctk.CTkScrollableFrame(
            self, 
            corner_radius=0, 
            fg_color="transparent",
            scrollbar_button_color=ThemeEngine.BORDER_COLOR,
            scrollbar_button_hover_color=ThemeEngine.ACCENT_PRIMARY,
            width=ThemeEngine.SIDEBAR_WIDTH - 10
        )
        self.project_tree.grid(row=2, column=0, sticky="nsew", padx=0, pady=10)
        
        # 3. Nav Section
        self._create_nav_bar()
        
        # Status label moved to left_panel (below Settings)

    def _create_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent", height=50)
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(20, 10))
        
        lbl = ctk.CTkLabel(header, text="PROJECTS", font=ThemeEngine.FONT_HEADER, text_color=ThemeEngine.TEXT_MUTED)
        lbl.pack(side="left", padx=8)
        
        add_btn = ctk.CTkButton(
            header, text="+", width=24, height=24,
            fg_color="transparent", border_width=1, border_color=ThemeEngine.BORDER_COLOR,
            text_color=ThemeEngine.TEXT_MUTED,
            hover_color=ThemeEngine.BG_HOVER,
            command=self.create_new_project_dialog
        )
        add_btn.pack(side="right")

    def _create_nav_bar(self):
        # Nav bar removed - Story Bible and Settings are now separate components in left_panel
        pass

    def select_nav(self, name):
        for k, btn in self.nav_buttons.items():
            btn.set_active(k == name)
        self.on_nav_select(name)

    def refresh_tree(self, active_chapter_id=None):
        for widget in self.project_tree.winfo_children():
            widget.destroy()
            
        projects = self.db_manager.get_projects_with_chapters()
        
        if not projects:
            ctk.CTkLabel(self.project_tree, text="No Projects", text_color=ThemeEngine.TEXT_MUTED).pack(pady=20)
            return

        for p in projects:
            # Project Row
            p_frame = ctk.CTkFrame(self.project_tree, fg_color="transparent")
            p_frame.pack(fill="x", pady=(2, 0))
            
            p_lbl = ctk.CTkLabel(p_frame, text=f"📂 {p['name']}", font=("Inter", 13, "bold"), text_color=ThemeEngine.TEXT_PRIMARY)
            p_lbl.pack(side="left", padx=15, pady=5)
            # Bind right-click for project context menu
            p_lbl.bind("<Button-3>", lambda e, proj=p: self.show_project_context_menu(e, proj['id'], proj['name']))
            
            add_chap = ctk.CTkButton(
                p_frame, text="+", width=20, height=20, 
                fg_color="transparent", text_color=ThemeEngine.TEXT_MUTED,
                hover_color=ThemeEngine.BG_HOVER,
                command=lambda pid=p['id']: self.create_new_chapter(pid)
            )
            add_chap.pack(side="right", padx=10)
            
            # Chapters
            for idx, ch in enumerate(p['chapters']):
                is_active = (ch['id'] == active_chapter_id)
                is_first = (idx == 0)
                is_last = (idx == len(p['chapters']) - 1)
                
                # Subtle highlight for active document
                fg = ThemeEngine.BG_HOVER if is_active else "transparent"
                txt_col = ThemeEngine.ACCENT_PRIMARY if is_active else ThemeEngine.TEXT_MUTED
                
                ch_btn = ctk.CTkButton(
                    self.project_tree,
                    text=f"  📄 {ch['title']}",
                    anchor="w",
                    height=28,
                    fg_color=fg,
                    text_color=txt_col,
                    font=("Inter", 13),
                    hover_color=ThemeEngine.BG_HOVER,
                    command=lambda cid=ch['id'], pid=p['id']: self.on_chapter_select(cid, pid)
                )
                ch_btn.pack(fill="x", padx=(10, 5), pady=1)
                # Bind right-click for chapter context menu
                ch_btn.bind("<Button-3>", lambda e, c=ch, proj=p, f=is_first, l=is_last: 
                    self.show_chapter_context_menu(e, c['id'], c['title'], proj['id'], f, l))
        
        # Chapter Beats UI Removed (Logic preserved for future use)
        


    def update_auto_gen_button(self, has_content):
        """Update button text based on whether chapter has content."""
        # UI Element removed, logic preserved.
        pass

    def create_new_project_dialog(self):
        dialog = ctk.CTkInputDialog(text="Project Name:", title="New Project")
        name = dialog.get_input()
        if name:
            new_id = self.db_manager.create_project(name)
            if new_id:
                self.db_manager.create_chapter(new_id, "Chapter 1")
                self.refresh_tree()

    def create_new_chapter(self, project_id):
        dialog = ctk.CTkInputDialog(text="Chapter Title:", title="New Chapter")
        title = dialog.get_input()
        if title:
            self.db_manager.create_chapter(project_id, title)
            self.refresh_tree()

    # --- Context Menu Methods ---
    def dismiss_current_menu(self):
        """Dismiss any currently open context menu."""
        if self.current_menu:
            try:
                self.current_menu.unpost()
            except:
                pass
            self.current_menu = None
            # Remove the global click handler
            try:
                self.winfo_toplevel().unbind_all("<Button-1>", self._menu_dismiss_id)
            except:
                pass

    def _handle_outside_click(self, event):
        """Handle clicks to dismiss menu if clicking outside."""
        if self.current_menu:
            # Check if the click is outside the menu by checking coordinates
            try:
                # Get menu geometry
                menu_x = self.current_menu.winfo_rootx()
                menu_y = self.current_menu.winfo_rooty()
                menu_width = self.current_menu.winfo_width()
                menu_height = self.current_menu.winfo_height()
                
                # Check if click is outside menu bounds
                if (event.x_root < menu_x or event.x_root > menu_x + menu_width or
                    event.y_root < menu_y or event.y_root > menu_y + menu_height):
                    self.dismiss_current_menu()
            except:
                # If we can't get menu geometry, dismiss it
                self.dismiss_current_menu()

    def show_project_context_menu(self, event, project_id, project_name):
        """Show right-click context menu for project."""
        # Dismiss any existing menu first
        self.dismiss_current_menu()
        
        import tkinter as tk
        menu = tk.Menu(self, tearoff=0, bg=ThemeEngine.BG_SIDEBAR, fg=ThemeEngine.TEXT_PRIMARY, 
                      activebackground=ThemeEngine.BG_HOVER, activeforeground=ThemeEngine.ACCENT_PRIMARY,
                      bd=0)
        
        # Wrap commands to dismiss menu after execution
        def rename_cmd():
            menu.unpost()
            self.current_menu = None
            self.rename_project_dialog(project_id, project_name)
        
        def delete_cmd():
            menu.unpost()
            self.current_menu = None
            self.delete_project_confirm(project_id, project_name)
        
        menu.add_command(label="Rename", command=rename_cmd)
        menu.add_separator()
        menu.add_command(label="Delete", command=delete_cmd)
        
        # Store reference
        self.current_menu = menu
        
        # Post menu
        menu.post(event.x_root, event.y_root)
        
        # Bind global click handler for outside clicks (with small delay to avoid immediate trigger)
        self._menu_dismiss_id = self.winfo_toplevel().bind_all("<Button-1>", self._handle_outside_click, add="+")

    def show_chapter_context_menu(self, event, chapter_id, chapter_title, project_id, is_first, is_last):
        """Show right-click context menu for chapter."""
        # Dismiss any existing menu first
        self.dismiss_current_menu()
        
        import tkinter as tk
        menu = tk.Menu(self, tearoff=0, bg=ThemeEngine.BG_SIDEBAR, fg=ThemeEngine.TEXT_PRIMARY,
                      activebackground=ThemeEngine.BG_HOVER, activeforeground=ThemeEngine.ACCENT_PRIMARY,
                      bd=0)
        
        # Wrap commands to dismiss menu after execution
        def rename_cmd():
            menu.unpost()
            self.current_menu = None
            self.rename_chapter_dialog(chapter_id, chapter_title)
        
        def move_up_cmd():
            menu.unpost()
            self.current_menu = None
            self.move_chapter_up(chapter_id, project_id)
        
        def move_down_cmd():
            menu.unpost()
            self.current_menu = None
            self.move_chapter_down(chapter_id, project_id)
        
        def delete_cmd():
            menu.unpost()
            self.current_menu = None
            self.delete_chapter_confirm(chapter_id, chapter_title)
        
        menu.add_command(label="Rename", command=rename_cmd)
        menu.add_separator()
        if not is_first:
            menu.add_command(label="Move Up ↑", command=move_up_cmd)
        if not is_last:
            menu.add_command(label="Move Down ↓", command=move_down_cmd)
        if not is_first or not is_last:
            menu.add_separator()
        menu.add_command(label="Delete", command=delete_cmd)
        
        # Store reference
        self.current_menu = menu
        
        # Post menu
        menu.post(event.x_root, event.y_root)
        
        # Bind global click handler for outside clicks
        self._menu_dismiss_id = self.winfo_toplevel().bind_all("<Button-1>", self._handle_outside_click, add="+")

    def rename_project_dialog(self, project_id, current_name):
        """Show dialog to rename project."""
        dialog = ctk.CTkInputDialog(text=f"Rename '{current_name}' to:", title="Rename Project")
        new_name = dialog.get_input()
        if new_name and new_name != current_name:
            self.db_manager.rename_project(project_id, new_name)
            self.refresh_tree()

    def rename_chapter_dialog(self, chapter_id, current_title):
        """Show dialog to rename chapter."""
        dialog = ctk.CTkInputDialog(text=f"Rename '{current_title}' to:", title="Rename Chapter")
        new_title = dialog.get_input()
        if new_title and new_title != current_title:
            self.db_manager.rename_chapter(chapter_id, new_title)
            self.refresh_tree()

    def delete_project_confirm(self, project_id, project_name):
        """Show confirmation dialog and delete project."""
        import tkinter.messagebox as messagebox
        result = messagebox.askyesno(
            "Delete Project",
            f"Are you sure you want to delete '{project_name}' and all its chapters?\n\nThis cannot be undone.",
            icon='warning'
        )
        if result:
            self.db_manager.delete_project(project_id)
            self.refresh_tree()

    def delete_chapter_confirm(self, chapter_id, chapter_title):
        """Show confirmation dialog and delete chapter."""
        import tkinter.messagebox as messagebox
        result = messagebox.askyesno(
            "Delete Chapter",
            f"Are you sure you want to delete '{chapter_title}'?\n\nThis cannot be undone.",
            icon='warning'
        )
        if result:
            self.db_manager.delete_chapter(chapter_id)
            self.refresh_tree()

    def move_chapter_up(self, chapter_id, project_id):
        """Move chapter up in order."""
        self.db_manager.move_chapter_up(chapter_id)
        self.refresh_tree()

    def move_chapter_down(self, chapter_id, project_id):
        """Move chapter down in order."""
        self.db_manager.move_chapter_down(chapter_id)
        self.refresh_tree()


class EditorFrame(ctk.CTkFrame):
    """
    Center Column: Zen Writing Mode (750px)
    """
    def __init__(self, master, on_send_instruction, on_summarize=None):
        super().__init__(master, corner_radius=0, fg_color=ThemeEngine.BG_MAIN)
        self.on_send_instruction = on_send_instruction
        self.on_summarize = on_summarize
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) 
        
        # 1. Header (Breadcrumbs)
        self._create_header()
        
        # Add Summarize Button to Header
        self.shrinkray_btn = ctk.CTkButton(
            self.header,
            text="🧠 Summarize",
            width=80,
            height=24,
            fg_color="transparent",
            border_width=1,
            border_color=ThemeEngine.BORDER_COLOR,
            text_color=ThemeEngine.TEXT_MUTED,
            command=lambda: self.on_summarize() if self.on_summarize else None
        )
        self.shrinkray_btn.pack(side="right", padx=20, pady=10)
        
        # 2. Zen Editor (Centered)
        self.center_container = ctk.CTkFrame(self, fg_color="transparent")
        self.center_container.grid(row=1, column=0, sticky="nsew")
        
        # Grid config for centering (Spacer, Editor, Spacer)
        self.center_container.grid_columnconfigure(0, weight=1)
        self.center_container.grid_columnconfigure(2, weight=1)
        self.center_container.grid_rowconfigure(0, weight=1)
        
        self.textbox = ctk.CTkTextbox(
            self.center_container,
            width=ThemeEngine.EDITOR_WIDTH,
            font=ThemeEngine.FONT_PROSE,
            fg_color="transparent",
            text_color=ThemeEngine.TEXT_PRIMARY,
            wrap="word",
            undo=True,
            spacing3=10
        )
        self.textbox.grid(row=0, column=1, sticky="nsew", pady=(60, 20)) 
        self.textbox.bind("<KeyRelease>", self.on_text_change)
        
        # Bind Right Click
        self._create_context_menu()
        self.textbox.bind("<Button-3>", self.show_context_menu)
        
        # Ghost Text Configuration
        self.textbox.tag_config("ghost_text", foreground="#666666")
        self.ghost_text_indices = None
        
        # Keyboard Shortcuts
        self.textbox.bind("<Alt-w>", self.trigger_write_next)
        self.textbox.bind("<Tab>", self.accept_ghost_text)
        
        # 3. Footer (Input & Status)
        self._create_footer()

    def _create_header(self):
        self.header = ctk.CTkFrame(self, height=40, fg_color="transparent", corner_radius=0)
        self.header.grid(row=0, column=0, sticky="ew")
        
        self.breadcrumb = ctk.CTkLabel(
            self.header, 
            text="Project / Chapter", 
            font=ThemeEngine.FONT_HEADER, 
            text_color=ThemeEngine.TEXT_MUTED
        )
        self.breadcrumb.pack(side="left", padx=20, pady=10)
        
        # Border Bottom
        border = ctk.CTkFrame(self, height=1, fg_color=ThemeEngine.BORDER_COLOR)
        border.grid(row=0, column=0, sticky="ews", pady=(39,0))

    def _create_footer(self):
        self.footer = ctk.CTkFrame(self, height=60, fg_color="transparent")
        self.footer.grid(row=2, column=0, sticky="ew", padx=20, pady=20)
        
        # Mimic Dropdown
        self.mimic_opt = ctk.CTkOptionMenu(
            self.footer, 
            values=["Prose Mode"], 
            width=140, 
            fg_color=ThemeEngine.BG_SIDEBAR,
            button_color=ThemeEngine.BORDER_COLOR,
            text_color=ThemeEngine.TEXT_MUTED
        )
        self.mimic_opt.pack(side="left", padx=(0, 10))
        
        # Input
        self.input_entry = ctk.CTkEntry(
            self.footer, 
            placeholder_text="Write with AI...",
            height=40,
            corner_radius=20,
            border_width=1,
            border_color=ThemeEngine.BORDER_COLOR,
            fg_color=ThemeEngine.BG_SIDEBAR,
            text_color=ThemeEngine.TEXT_PRIMARY
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.input_entry.bind("<Return>", self.send_action)

        # Expand Scene Button
        self.expand_btn = ctk.CTkButton(
            self.footer,
            text="✨ Expand",
            width=80,
            height=40,
            corner_radius=20,
            fg_color=ThemeEngine.ACCENT_SECONDARY,
            hover_color=ThemeEngine.ACCENT_HOVER,
            command=self.expand_action
        )
        self.expand_btn.pack(side="left", padx=(0, 10))
        
        # Send Button
        self.send_btn = ctk.CTkButton(
            self.footer, text="Send", width=70, height=40, corner_radius=20,
            fg_color=ThemeEngine.ACCENT_PRIMARY,
            command=self.send_action
        )
        self.send_btn.pack(side="left")

        # Word Count
        self.word_count_lbl = ctk.CTkLabel(
            self.footer, 
            text="0 words", 
            font=("Inter", 11), 
            text_color=ThemeEngine.TEXT_MUTED
        )
        self.word_count_lbl.pack(side="right", padx=15)

    def _create_context_menu(self):
        """Creates the Nested Right-Click Context Menu."""
        self.context_menu = tk.Menu(self, tearoff=0, bg="#2b2b2b", fg="white", activebackground="#404040", activeforeground="white")
        
        # 1. Describe Sub-Menu
        describe_menu = tk.Menu(self.context_menu, tearoff=0, bg="#2b2b2b", fg="white")
        self.context_menu.add_cascade(label="👁️ Describe", menu=describe_menu)
        
        describe_menu.add_command(label="Sight", command=lambda: self.on_plugin("describe_sight"))
        describe_menu.add_command(label="Sound", command=lambda: self.on_plugin("describe_sound"))
        describe_menu.add_command(label="Smell", command=lambda: self.on_plugin("describe_smell"))
        describe_menu.add_command(label="Taste", command=lambda: self.on_plugin("describe_taste"))
        describe_menu.add_command(label="Touch", command=lambda: self.on_plugin("describe_touch"))
        describe_menu.add_separator()
        describe_menu.add_command(label="Metaphor", command=lambda: self.on_plugin("describe_metaphor"))

        # 2. Rewrite Sub-Menu
        rewrite_menu = tk.Menu(self.context_menu, tearoff=0, bg="#2b2b2b", fg="white")
        self.context_menu.add_cascade(label="🎭 Rewrite", menu=rewrite_menu)
        
        rewrite_menu.add_command(label="Show Don't Tell", command=lambda: self.on_plugin("rewrite_show_dont_tell"))
        rewrite_menu.add_command(label="Dramatic", command=lambda: self.on_plugin("rewrite_dramatic"))
        rewrite_menu.add_command(label="Gritty", command=lambda: self.on_plugin("rewrite_gritty"))
        rewrite_menu.add_command(label="Elegant", command=lambda: self.on_plugin("rewrite_elegant"))
        rewrite_menu.add_command(label="Concise", command=lambda: self.on_plugin("rewrite_concise"))

    def show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def on_plugin(self, plugin_type):
        """Trigger AI Plugin via callback."""
        try:
            selection = self.textbox.get("sel.first", "sel.last")
            if selection:
                self.on_send_instruction(f"PLUGIN::{plugin_type}::{selection}")
        except:
             pass # No selection

    def expand_action(self):
        """Triggers the expansion of the scene."""
        self.on_send_instruction("PLUGIN::expand_scene::")

    def load_content(self, title, content):
        self.breadcrumb.configure(text=f"{title}")
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", content)
        self.update_counts()

    def get_content(self):
        return self.textbox.get("1.0", "end-1c")

    def on_text_change(self, event=None):
        self.update_counts()

    def update_counts(self):
        text = self.get_content()
        words = len(text.split())
        self.word_count_lbl.configure(text=f"{words} words")
        
    def insert_token(self, token):
        self.textbox.insert("insert", token)
        self.textbox.see("insert")
        self.update_counts()

    def send_action(self, event=None):
        prompt = self.input_entry.get().strip()
        if prompt:
            self.on_send_instruction(prompt)
            self.input_entry.delete(0, 'end')
            return 'break'

    def get_selection_indices(self):
        """Returns the start and end indices of the current selection."""
        try:
            return self.textbox.tag_ranges("sel")
        except:
            return None

    def replace_section(self, indices, new_text):
        """Replaces text at the given indices with new_text."""
        if indices and len(indices) == 2:
            start, end = indices
            self.textbox.delete(start, end)
            self.textbox.insert(start, new_text)
            self.update_counts()

    def trigger_write_next(self, event=None):
        """Triggered by Alt+W - requests RAG-enhanced AI writing."""
        self.on_send_instruction("WRITE_NEXT")
        return "break"

    def accept_ghost_text(self, event=None):
        """Triggered by Tab - accepts ghost text and makes it permanent."""
        if self.ghost_text_indices:
            # Remove ghost_text tag to make it permanent
            start, end = self.ghost_text_indices
            self.textbox.tag_remove("ghost_text", start, end)
            self.ghost_text_indices = None
            return "break"
        # If no ghost text, allow Tab to pass through normally
        return None

    def insert_ghost_token(self, token):
        """Inserts a token with ghost_text styling."""
        if not self.ghost_text_indices:
            # First token - mark starting position
            start = self.textbox.index("insert")
            self.textbox.insert("insert", token, "ghost_text")
            end = self.textbox.index("insert")
            self.ghost_text_indices = (start, end)
        else:
            # Subsequent tokens - extend the range
            self.textbox.insert("insert", token, "ghost_text")
            start, _ = self.ghost_text_indices
            end = self.textbox.index("insert")
            self.ghost_text_indices = (start, end)

    def set_generating(self, is_gen):
        if is_gen:
            self.send_btn.configure(state="disabled", text="Thinking...")
            self.input_entry.configure(state="disabled")
        else:
            self.send_btn.configure(state="normal", text="Send")
            self.input_entry.configure(state="normal")
            
    def update_mimic_options(self, options):
        self.mimic_opt.configure(values=options)

    def get_mimic_selection(self):
        return self.mimic_opt.get()






class SettingsFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=ThemeEngine.BG_MAIN)
        ctk.CTkLabel(self, text="Settings", font=("Georgia", 24)).pack(pady=40)
        ctk.CTkLabel(self, text="Coming Soon...", text_color=ThemeEngine.TEXT_MUTED).pack()


class AssistantPanel(ctk.CTkTabview):
    """
    Right Sidebar: Lore Assistant & Sensory Lab.
    """
    def __init__(self, master, on_request_lore):
        super().__init__(master, width=ThemeEngine.ASSISTANT_WIDTH, corner_radius=0, fg_color=ThemeEngine.BG_MAIN)
        self.on_request_lore = on_request_lore
        
        # Create Tabs
        self.add("Lore Chat")
        self.add("Sensory Lab")
        
        # --- TAB 1: LORE CHAT ---
        self.tab("Lore Chat").grid_columnconfigure(0, weight=1)
        self.tab("Lore Chat").grid_rowconfigure(0, weight=1)
        
        # Chat History
        self.chat_history = ctk.CTkTextbox(
            self.tab("Lore Chat"),
            font=ThemeEngine.FONT_UI,
            fg_color="transparent",
            text_color=ThemeEngine.TEXT_PRIMARY,
            wrap="word",
            state="disabled"
        )
        self.chat_history.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Input Area (Chat)
        self.chat_input = ctk.CTkEntry(
            self.tab("Lore Chat"),
            placeholder_text="Ask about lore...",
            fg_color=ThemeEngine.BG_MAIN
        )
        self.chat_input.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.chat_input.bind("<Return>", self.send_chat_action)
        
        # Empty State
        self.empty_state_lbl = ctk.CTkLabel(
            self.tab("Lore Chat"), 
            text="Ask anything about\nyour story world.",
            font=ThemeEngine.FONT_UI,
            text_color=ThemeEngine.TEXT_MUTED
        )
        # Initially visible
        self.empty_state_lbl.place(relx=0.5, rely=0.4, anchor="center")

        # --- TAB 2: SENSORY LAB ---
        self.tab("Sensory Lab").grid_columnconfigure(0, weight=1)
        
        # Header
        ctk.CTkLabel(self.tab("Sensory Lab"), text="Brainstorm Atmosphere", font=ThemeEngine.FONT_H3).pack(pady=10)
        
        # Input
        self.sensory_input = ctk.CTkEntry(
            self.tab("Sensory Lab"), 
            placeholder_text="E.g., A rainy street at night...",
            fg_color=ThemeEngine.BG_MAIN
        )
        self.sensory_input.pack(fill="x", padx=10, pady=5)
        self.sensory_input.bind("<Return>", self.send_sensory_action)
        
        # Button
        ctk.CTkButton(
            self.tab("Sensory Lab"),
            text="Generate Details",
            fg_color=ThemeEngine.ACCENT_SECONDARY,
            command=self.send_sensory_action
        ).pack(pady=5)
        
        # Output Area
        self.sensory_output = ctk.CTkTextbox(
            self.tab("Sensory Lab"),
            font=ThemeEngine.FONT_UI,
            fg_color="transparent", 
            wrap="word",
            height=300
        )
        self.sensory_output.pack(fill="both", expand=True, padx=10, pady=10)

    def send_chat_action(self, event=None):
        query = self.chat_input.get().strip()
        if query:
            self.on_request_lore(query)
            self.chat_input.delete(0, 'end')
            
    def send_sensory_action(self, event=None):
        setting = self.sensory_input.get().strip()
        if setting:
             self.on_request_lore(f"SENSORY::{setting}")
             self.sensory_input.delete(0, 'end')
             self.sensory_output.delete("1.0", "end")
             self.sensory_output.insert("end", "Generating sensory details...\n\n")

    def show_replacement_options(self, on_replace_callback):
        """Shows Replace buttons instead of Chat Input."""
        self.chat_input.grid_forget()
        
        self.replace_frame = ctk.CTkFrame(self.tab("Lore Chat"), fg_color="transparent")
        self.replace_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(self.replace_frame, text="Select Variation:", font=("Inter", 12, "bold")).pack(side="top", pady=(0, 5))
        
        btn_frame = ctk.CTkFrame(self.replace_frame, fg_color="transparent")
        btn_frame.pack(side="top")
        
        ctk.CTkButton(btn_frame, text="1", width=40, command=lambda: on_replace_callback(0)).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="2", width=40, command=lambda: on_replace_callback(1)).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="3", width=40, command=lambda: on_replace_callback(2)).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="Cancel", width=60, fg_color=ThemeEngine.BG_HOVER, command=lambda: on_replace_callback(-1)).pack(side="left", padx=10)

    def hide_replacement_options(self):
        """Restores Chat Input."""
        if hasattr(self, 'replace_frame'):
            self.replace_frame.destroy()
        self.chat_input.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

    def append_log(self, text):
        self.empty_state_lbl.place_forget()
        self.chat_history.configure(state="normal")
        self.chat_history.insert("end", text)
        self.chat_history.configure(state="disabled")
        self.chat_history.see("end")

    def append_sensory(self, text):
        self.sensory_output.insert("end", text)
        self.sensory_output.see("end")

    def clear_log(self):
        self.chat_history.configure(state="normal")
        self.chat_history.delete("1.0", "end")
        self.chat_history.configure(state="disabled")
        self.empty_state_lbl.place(relx=0.5, rely=0.4, anchor="center")
        self.sensory_output.delete("1.0", "end")

    def set_thinking(self, is_thinking):
        pass # Optional loading state





class StoryBibleUI(ctk.CTk):
    def __init__(self, ai_engine, db_manager):
        super().__init__()
        self.ai_engine = ai_engine
        self.db_manager = db_manager
        
        self.current_project_id = None
        self.current_chapter_id = None
        self.is_generating = False
        self.response_queue = queue.Queue()
        self.target_panel = None  # 'editor' or 'assistant'
        
        # Setup Window
        ctk.set_appearance_mode("Dark")
        self.title("Story Bible Pro - Sudowrite Style")
        self.geometry("1600x1000")
        self.configure(fg_color=ThemeEngine.BG_MAIN)
        
        # ============================================================
        # NEW SUDOWRITE-STYLE LAYOUT
        # ============================================================
        
        # Grid Layout: 2 rows (toolbar, content) x 3 columns (left, center, right)
        self.grid_rowconfigure(0, weight=0)  # Toolbar row (fixed height)
        self.grid_rowconfigure(1, weight=1)  # Content row (expandable)
        self.grid_columnconfigure(0, weight=0, minsize=280)  # Left panel (18-20%)
        self.grid_columnconfigure(1, weight=1)  # Center panel (60%)
        self.grid_columnconfigure(2, weight=0, minsize=360)  # Right panel (22-25%)
        
        # ===== ROW 0: FIXED GLOBAL TOOLBAR =====
        self.toolbar = ToolbarFrame(self, self.handle_toolbar_action)
        self.toolbar.grid(row=0, column=0, columnspan=3, sticky="ew")
        
        # ===== ROW 1, COL 0: LEFT PANEL (Project Navigation) =====
        self.left_panel = ctk.CTkFrame(
            self,
            fg_color=ThemeEngine.BG_SIDEBAR,
            corner_radius=0
        )
        self.left_panel.grid(row=1, column=0, sticky="nsew")
        self.left_panel.grid_rowconfigure(0, weight=1)  # Project tree expands
        self.left_panel.grid_rowconfigure(1, weight=0)  # Bottom section fixed
        
        # Simplified sidebar (no Story Bible tabs)
        self.sidebar = SidebarFrame(
            self.left_panel,
            db_manager,
            self.nav_select,
            self.load_chapter,
            None,  # on_generate_from_beats removed
            None   # on_auto_generate_beats removed
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        
        # Bottom section (Story Bible toggle + Tabs + Trash)
        self.bottom_section = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.bottom_section.grid(row=1, column=0, sticky="ew", padx=8, pady=10)
        
        # Story Bible toggle button (collapsed by default)
        self.is_bible_open = False  # Story Bible starts CLOSED
        self.bible_toggle_btn = ctk.CTkButton(
            self.bottom_section,
            text="📖 Story Bible [>]",
            fg_color="transparent",
            text_color=ThemeEngine.TEXT_MUTED,
            hover_color=ThemeEngine.BG_HOVER,
            anchor="w",
            height=36,
            command=self.toggle_story_bible
        )
        self.bible_toggle_btn.pack(fill="x", padx=10, pady=5)
        
        # Story Bible tabs container (hidden by default)
        self.bible_tabs_container = ctk.CTkFrame(self.bottom_section, fg_color="transparent")
        self.bible_tabs_container.pack(fill="x", padx=10)
        self.bible_tabs_container.pack_forget()  # Hide initially
        
        # Create 7 tabs
        bible_tabs = [
            ("📝 Braindump", "braindump"),
            ("🎭 Genre", "genre"),
            ("🎨 Style", "style"),
            ("📖 Synopsis", "synopsis"),
            ("👥 Characters", "characters"),
            ("🌍 Worldbuilding", "worldbuilding"),
            ("📋 Outline", "outline")
        ]
        
        for label, section in bible_tabs:
            tab_btn = ctk.CTkButton(
                self.bible_tabs_container,
                text=label,
                fg_color="transparent",
                text_color=ThemeEngine.TEXT_MUTED,
                hover_color=ThemeEngine.BG_HOVER,
                anchor="w",
                height=28,
                font=("Inter", 12),
                command=lambda s=section: self.scroll_to_bible_section(s)
            )
            tab_btn.pack(fill="x", pady=1)
        
        # Trash button (below tabs)
        self.trash_btn = ctk.CTkButton(
            self.bottom_section,
            text="🗑️ Trash",
            fg_color="transparent",
            text_color=ThemeEngine.TEXT_MUTED,
            hover_color=ThemeEngine.BG_HOVER,
            anchor="w",
            height=32,
            command=self.show_trash
        )
        self.trash_btn.pack(fill="x", padx=10, pady=(10, 2))
        
        # ===== ROW 1, COL 1: CENTER PANEL (Continuous Scroll) =====
        self.center_panel = CenterScrollPanel(
            self,
            db_manager,
            self.on_content_change
        )
        self.center_panel.grid(row=1, column=1, sticky="nsew")
        
        # ===== ROW 1, COL 2: RIGHT PANEL (AI Chat) =====
        self.chat_panel = AssistantPanel(
            self,
            lambda p: self.handle_ai_request(p, 'assistant')
        )
        self.chat_panel.grid(row=1, column=2, sticky="nsew")
        
        # ============================================================
        # INITIALIZATION
        # ============================================================
        self.load_session()
        
        # Event Loops
        self.after(100, self.check_queue)
        self.after(30000, self.auto_save_loop)
        self.protocol("WM_DELETE_WINDOW", self.on_close)


    # ============================================================
    # STORY BIBLE TOGGLE & TAB NAVIGATION
    # ============================================================
    
    def toggle_story_bible(self):
        """Toggle Story Bible ON/OFF."""
        self.is_bible_open = not self.is_bible_open
        
        if self.is_bible_open:
            # OPEN: Show tabs and create Bible content
            self.bible_tabs_container.pack(fill="x", padx=10)
            self.bible_toggle_btn.configure(
                text="📖 Story Bible [v]",
                text_color=ThemeEngine.ACCENT_PRIMARY
            )
            # Create Story Bible container in center panel
            self.center_panel.create_story_bible_container()
            # Load current project data into Story Bible
            if self.current_project_id:
                self.center_panel.load_project(self.current_project_id, self.current_chapter_id)
        else:
            # CLOSED: Hide tabs and destroy Bible content
            self.bible_tabs_container.pack_forget()
            self.bible_toggle_btn.configure(
                text="📖 Story Bible [>]",
                text_color=ThemeEngine.TEXT_MUTED
            )
            # Destroy Story Bible container in center panel
            self.center_panel.destroy_story_bible_container()
    
    def scroll_to_bible_section(self, section_name):
        """Scroll center panel to a specific Story Bible section."""
        if not self.is_bible_open:
            # If Bible is closed, open it first
            self.toggle_story_bible()
        
        # Scroll to the section
        self.center_panel.scroll_to_section(section_name)


    # ============================================================
    # NEW METHOD HANDLERS FOR SUDOWRITE-STYLE UI
    # ============================================================
    
    def handle_toolbar_action(self, action, item):
        """Handle toolbar button and menu actions."""
        logging.info(f"Toolbar action: {action} - {item}")
        
        if action == "back":
            # Navigate back in history (if implemented)
            pass
        elif action == "write":
            # Handle write menu items
            if item == "Continue Writing":
                self.handle_ai_request("Continue writing from where I left off", 'editor')
            elif item == "Write Scene":
                self.handle_ai_request("Write a new scene", 'editor')
            elif item == "Generate Opening":
                self.handle_ai_request("Generate an opening paragraph", 'editor')
        elif action == "rewrite":
            # Handle rewrite styles
            self.handle_ai_request(f"PLUGIN::rewrite_{item.lower().replace(' ', '_')}::", 'editor')
        elif action == "describe":
            # Handle describe senses
            self.handle_ai_request(f"PLUGIN::describe_{item.lower()}::", 'editor')
        elif action == "brainstorm":
            # Send to chat panel
            self.handle_ai_request(f"Brainstorm: {item}", 'assistant')
        elif action == "more_tools":
            if item == "Export":
                self.export_document()
            elif item == "Import":
                self.import_document()
            elif item == "Settings":
                # Show settings dialog
                logging.info("Settings clicked")
        elif action == "export":
            self.export_document()
        elif action == "help":
            self.show_help()
        elif action == "settings":
            logging.info("Settings clicked")
    
    def on_content_change(self, action_type=None):
        """Handle content changes in center panel."""
        # Update word count
        try:
            content = self.center_panel.get_editor_content()
            word_count = len(content.split())
            self.toolbar.update_word_count(word_count)
        except:
            pass
        
        # Handle action button clicks
        if action_type:
            if action_type == "generate_draft":
                self.handle_ai_request("Generate a rough draft of this chapter", 'editor')
            elif action_type == "generate_openings":
                self.handle_ai_request("Generate 3 different opening paragraphs", 'editor')
            elif action_type == "chat_idea":
                # Switch to chat panel - use correct tab name
                try:
                    # AssistantPanel uses "Assistant" as tab name, not "Chat"
                    self.chat_panel.chat_input.focus()
                except:
                    pass
    
    def load_chapter(self, chapter_id, project_id):
        """Load a chapter into the center panel."""
        self.current_chapter_id = chapter_id
        self.current_project_id = project_id
        
        # Load into continuous scroll panel
        self.center_panel.load_project(project_id, chapter_id)
        
        # Update word count
        self.on_content_change()
        
        # Refresh sidebar to show active chapter
        self.sidebar.refresh_tree(chapter_id)
    
    def nav_select(self, name):
        """Handle navigation (simplified for new layout)."""
        # In Sudowrite style, we don't swap pages
        # Story Bible is always visible at top of center panel
        logging.info(f"Nav select: {name}")
    
    def show_trash(self):
        """Show trash/deleted items."""
        logging.info("Show trash clicked")
        # TODO: Implement trash view
    
    def export_document(self):
        """Export current document."""
        logging.info("Export document")
        # TODO: Implement export
    
    def import_document(self):
        """Import a document."""
        logging.info("Import document")
        # TODO: Implement import
    
    def show_help(self):
        """Show help dialog."""
        logging.info("Show help")
        # TODO: Implement help dialog


    # ============================================================
    # OLD METHODS (TO BE REMOVED OR UPDATED)
    # ============================================================

    def animate_drawer(self, start_y, target_y, step=0.08):
        """Slide drawer vertically on left edge."""
        current_y = start_y
        
        if start_y > target_y: # Sliding up
            current_y -= step
            if current_y <= target_y:
                current_y = target_y
                self.bible_drawer.place(relx=0, rely=current_y, anchor="sw", relheight=0.5)
                return
        else: # Sliding down
            current_y += step
            if current_y >= target_y:
                current_y = target_y
                if target_y >= 1.0:
                    self.bible_drawer.place_forget() # Hide when off-screen
                else:
                    self.bible_drawer.place(relx=0, rely=current_y, anchor="sw", relheight=0.5)
                return

        self.bible_drawer.place(relx=0, rely=current_y, anchor="sw", relheight=0.5)
        self.after(10, lambda: self.animate_drawer(current_y, target_y, step))

    def toggle_story_bible_anim(self):
        """Toggle Story Bible tabs visibility (slide up/down)."""
        if self.is_bible_open:
            # Hide tabs
            self.bible_tabs_container.grid_remove()
            self.is_bible_open = False
            # Update button visual state
            self.bible_toggle_btn.configure(fg_color="transparent", text_color=ThemeEngine.TEXT_MUTED)
        else:
            # Show tabs
            self.bible_tabs_container.grid()
            self.is_bible_open = True
            # Update button visual state
            self.bible_toggle_btn.configure(fg_color=ThemeEngine.BG_HOVER, text_color=ThemeEngine.ACCENT_PRIMARY)

    def show_bible_field(self, field_name):
        """Display selected Bible field in center area (replaces editor)."""
        # Hide editor and other pages
        for page in self.pages.values():
            page.grid_forget()
        
        # Show Bible view
        self.bible_view.grid(row=0, column=0, sticky="nsew")
        
        # Load project data if needed
        if self.current_project_id:
            self.bible_view.load_project(self.current_project_id)
        
        # Show specific field
        self.bible_view.show_field(field_name)

    def nav_select(self, name):
        """Handle navigation between pages."""
        if name == "StoryBible":
            self.toggle_story_bible_anim()
            return

        # Close drawer if navigating to other pages
        if self.is_bible_open:
            self.toggle_story_bible_anim()
        
        # Force save current Bible field before hiding
        if hasattr(self.bible_view, '_force_save_current'):
            self.bible_view._force_save_current()
        
        # Hide Bible view and restore normal page
        self.bible_view.grid_forget()
            
        for page in self.pages.values():
            page.grid_forget()
        
        if name in self.pages:
            self.pages[name].grid(row=0, column=0, sticky="nsew")
            
        if name == "Writing":
            self.update_mimic_list()

    def on_editor_instruction(self, prompt):
        self.handle_ai_request(prompt, 'editor')

    def manual_summarize(self):
        """Force a summary update for the current chapter."""
        if self.current_project_id and self.current_chapter_id:
             content = self.center_panel.get_editor_content()
             if content:
                 self.target_panel = 'assistant'
                 self.is_generating = True
                 self.chat_panel.append_log("Generating Summary...\n")
                 threading.Thread(target=self._update_beat_summary, args=(content, True), daemon=True).start()

    def handle_ai_request(self, prompt, target):
        if self.is_generating: return
        
        self.target_panel = target
        current_text = ""
        char_context = None
        project_memory = ""
        project_name = "Current Project"
        context_data = {}
        
        # --- ROUTING LOGIC ---
        plugin_type = None
        self.accumulated_response = ""
        self.current_variations = []
        
        if target == 'editor':
            # Story Bible autosave is handled automatically in CenterScrollPanel
            current_text = self.center_panel.get_editor_content()
            self.toolbar.set_save_status(False)  # Show "Saving..."
            
            # Check for WRITE_NEXT (Alt+W RAG-Enhanced Writing)
            if prompt == "WRITE_NEXT":
                if self.current_project_id and self.current_chapter_id:
                    rag_context = self.db_manager.get_context_window(
                        self.current_project_id, 
                        self.current_chapter_id,
                        char_limit=3000
                    )
                    if rag_context:
                        self.is_generating = True
                        self.target_panel = 'editor_ghost'
                        threading.Thread(
                            target=self._write_next_thread,
                            args=(current_text, rag_context),
                            daemon=True
                        ).start()
                        return
            
            # Check for Plugins
            if prompt.startswith("PLUGIN::"):
                parts = prompt.split("::")
                plugin_type = parts[1]
                # If selection exists, it's in parts[2], else empty
                selection_text = parts[2] if len(parts) > 2 else ""
                
                # Fetch Context Data (Genre)
                if self.current_project_id:
                    settings = self.db_manager.get_project_settings(self.current_project_id)
                    if settings:
                         context_data['genre'] = settings['genre']
                
                # Store Logic for Replacement
                self.current_plugin_type = plugin_type
                if plugin_type != 'expand_scene':
                     # TODO: Implement get_selection_indices in CenterScrollPanel
                     # self.current_selection_indices = self.center_panel.editor_textbox.tag_ranges("sel")
                     pass  # Placeholder for selection indices

                if plugin_type == 'expand_scene':
                    # Special handling for expansion
                    prompt = "" # Prompt is implicit
                else:
                    # For rewrite/describe, prompt is the text to act on
                    prompt = selection_text
            
            else:
                # Normal writing instruction
                # TODO: Implement mimic feature in new UI
                # selection = self.editor.get_mimic_selection()
                selection = "Prose Mode"  # Default for now
                if selection.startswith("Mimic: "):
                    char_name = selection.replace("Mimic: ", "")
                    char_context = self.db_manager.get_character_details(char_name)

            # Fetch full Story Bible context (Genre & Style)
            # We prefer Story Bible data because it is user-editable in the tabs
            if self.current_project_id:
                bible_data = self.db_manager.get_story_bible(self.current_project_id)
                if bible_data:
                    # Prefer Bible Genre over Project Settings (if available)
                    if bible_data.get('genre'):
                        context_data['genre'] = bible_data['genre']
                    # Get Style
                    if bible_data.get('style'):
                        context_data['style'] = bible_data['style']
                    # Get Synopsis
                    if bible_data.get('synopsis'):
                        context_data['synopsis'] = bible_data['synopsis']
                    # Get Worldbuilding
                    if bible_data.get('worldbuilding'):
                        context_data['worldbuilding'] = bible_data['worldbuilding']
                    # Get Outline
                    if bible_data.get('outline'):
                        context_data['outline'] = bible_data['outline']
                
                # Fallback: If still no genre, try project settings (static)
                if 'genre' not in context_data:
                    settings = self.db_manager.get_project_settings(self.current_project_id)
                    if settings and settings.get('genre'):
                        context_data['genre'] = settings['genre']

        elif target == 'assistant':
             # Check for Sensory Lab
             if prompt.startswith("SENSORY::"):
                 self.target_panel = 'sensory'
                 plugin_type = "sensory_lab"
                 prompt = prompt.replace("SENSORY::", "")
             else:
                 # Lore Assistant Mode (Deep Search)
                 self.chat_panel.set_thinking(True)
                 self.chat_panel.append_log(f"AI: ")
            
                 if self.current_project_id:
                    # Get Project Name
                    projects = self.db_manager.get_projects_with_chapters()
                    for p in projects:
                        if p['id'] == self.current_project_id:
                            project_name = p['name']
                            break
                    project_memory = self.db_manager.get_deep_memory(self.current_project_id, prompt)
                 else:
                    project_memory = "No project selected."

        self.is_generating = True
        # Extract context
        genre_context = context_data.get('genre', None)
        style_context = context_data.get('style', None)
        synopsis_context = context_data.get('synopsis', None)
        world_context = context_data.get('worldbuilding', None)
        outline_context = context_data.get('outline', None)
        
        threading.Thread(
            target=self._ai_thread,
            args=(prompt, target, current_text, char_context, project_memory, project_name, plugin_type, genre_context, style_context, synopsis_context, world_context, outline_context),
            daemon=True
        ).start()

    def _ai_thread(self, prompt, target, context, char_context, memory, project_name, plugin_type=None, genre=None, style=None, synopsis=None, worldbuilding=None, outline=None):
        try:
            if target == 'editor':
                if plugin_type == 'expand_scene':
                    self.ai_engine.expand_scene(context, self.response_queue)
                elif plugin_type:
                    # Specialized plugin generation (Describe/Rewrite)
                    ctx = {'genre': genre} # Style not strictly needed for plugins yet, but genre is
                    self.ai_engine.generate_plugin_response(prompt, plugin_type, self.response_queue, ctx)
                else:
                    # Normal Prose
                    self.ai_engine.stream_response(prompt, self.response_queue, "", context, char_context, genre=genre, style=style, synopsis=synopsis, worldbuilding=worldbuilding, outline=outline)
                    
                    if len(context) > 100 and self.current_project_id and self.current_chapter_id:
                         threading.Thread(target=self._update_beat_summary, args=(context,), daemon=True).start()

            elif target == 'assistant':
                if plugin_type == 'sensory_lab':
                    self.ai_engine.generate_plugin_response(prompt, 'sensory_lab', self.response_queue)
                else:
                    self.ai_engine.ask_lore_assistant(prompt, self.response_queue, memory, project_name)
                    
        except Exception as e:
            self.response_queue.put(f"Error: {e}")
            self.response_queue.put("[[END]]")

    def _write_next_thread(self, current_text, rag_context):
        """Special thread for RAG-enhanced writing (Alt+W)."""
        try:
            self.ai_engine.stream_response(
                instruction="",
                response_queue=self.response_queue,
                current_text=current_text,
                rag_context=rag_context
            )
        except Exception as e:
            self.response_queue.put(f"Error: {e}")
            self.response_queue.put("[[END]]")

    def _update_beat_summary(self, text, show_output=False):
        """Background task to generate and save story beat."""
        summary = self.ai_engine.generate_beat_summary(text)
        if summary and self.current_project_id and self.current_chapter_id:
            self.db_manager.save_beat(self.current_project_id, self.current_chapter_id, summary)
            print(f"[DEBUG] Beat saved for Ch {self.current_chapter_id}: {summary}")
            
            if show_output:
                self.response_queue.put(f"**Chapter Summary:**\n{summary}")
                self.response_queue.put("[[END]]")

    def check_queue(self):
        try:
            while True:
                token = self.response_queue.get_nowait()
                if token == "[[END]]":
                    self.is_generating = False
                    # Show "Saved" in toolbar
                    self.toolbar.set_save_status(True)
                    self.chat_panel.set_thinking(False)
                    if self.target_panel == 'assistant':
                        self.chat_panel.append_log("\n\n")
                        # Trigger Prose Cards ONLY for editor-based plugins, not lore chat
                        # (Replacement UI is only for right-click context menu operations on selected editor text)
                            
                    elif self.target_panel == 'sensory':
                        self.chat_panel.append_sensory("\n\n")
                else:
                    if self.target_panel == 'editor':
                        self.center_panel.insert_editor_content(token)
                    elif self.target_panel == 'editor_ghost':
                        # TODO: Implement ghost text in CenterScrollPanel
                        # self.editor.insert_ghost_token(token)
                        pass  # Skip ghost text for now
                    elif self.target_panel == 'assistant':
                        self.chat_panel.append_log(token)
                    elif self.target_panel == 'sensory':
                        self.chat_panel.append_sensory(token)
        except queue.Empty: pass
        finally: self.after(50, self.check_queue)

    def trigger_replacement_ui(self):
        """Parses response and shows replacement options."""
        # Simple parsing by "---" separator
        raw_text = self.accumulated_response
        # Remove any system prompts/artifacts if leaks (basic clean)
        cleaned = raw_text.replace("Here are 3 variations:", "").strip()
        
        self.current_variations = [v.strip() for v in cleaned.split("---") if v.strip()]
        
        if self.current_variations:
            logging.info(f"Parsed {len(self.current_variations)} variations.")
            self.chat_panel.show_replacement_options(self.on_replace_selected)
        else:
            self.chat_panel.append_log("\n[System: Could not parse variations.]")

    def on_replace_selected(self, index):
        """Callback from Assistant Panel."""
        try:
            if index >= 0 and index < len(self.current_variations):
                new_text = self.current_variations[index]
                if self.current_selection_indices:
                    # TODO: Implement text replacement in CenterScrollPanel
                    # self.editor.replace_section(self.current_selection_indices, new_text)
                    pass  # Skip for now
                    self.chat_panel.append_log(f"\n[System: Applied Variation {index+1}]")
            else:
                self.chat_panel.append_log("\n[System: Cancelled replacement.]")
        except Exception as e:
            logging.error(f"Replacement error: {e}")
            self.chat_panel.append_log(f"\n[Error: {e}]")
        
        self.chat_panel.hide_replacement_options()
        self.current_plugin_type = None
        self.accumulated_response = ""
        self.current_selection_indices = None



    def on_generate_from_beats(self):
        """Triggered by Generate Full Scene button."""
        if not self.current_project_id or not self.current_chapter_id:
            return
        
        # beats_text = self.sidebar.beats_textbox.get("1.0", "end").strip()
        beats_text = ""
        # beats_list = [l.strip() for l in beats_text.split("\n") if l.strip() and "Enter" not in l]
        beats_list = []
        
        if not beats_list:
            return
        
        lore_package = self.db_manager.fetch_omni_context(self.current_project_id, self.current_chapter_id, beats_list)
        if not lore_package:
            return
        
        is_valid, conflict_msg = self.ai_engine.check_continuity(beats_list, lore_package)
        
        if not is_valid:
            from tkinter import messagebox
            proceed = messagebox.askyesno("⚠️ Continuity Conflict", f"{conflict_msg}\n\nProceed?")
            if not proceed:
                return
        
        self.is_generating = True
        self.target_panel = 'editor'
        self.toolbar.set_save_status(False)  # Show "Saving..."
        
        threading.Thread(target=self._generate_prose_thread, args=(beats_list, lore_package), daemon=True).start()

    def _generate_prose_thread(self, beats, lore_package):
        try:
            self.ai_engine.generate_omniscient_prose(beats, lore_package, self.response_queue)
        except Exception as e:
            self.response_queue.put(f"Error: {e}")
            self.response_queue.put("[[END]]")

    def on_auto_generate_beats(self):
        """Smart button: Extract beats from prose OR suggest beats for new chapter."""
        if not self.current_chapter_id:
            return
        
        # Check if editor has content
        prose = self.center_panel.get_editor_content().strip()
        
        if len(prose) > 100:
            # Extract beats from existing prose
            beats = self.ai_engine.generate_beats_from_prose(prose)
            # self.sidebar.beats_textbox.delete("1.0", "end")
            # self.sidebar.beats_textbox.insert("1.0", beats)
            # Save to database
            self.db_manager.update_chapter_beats(self.current_chapter_id, beats)
            logging.info(f"Extracted {len(beats.splitlines())} beats from prose")
        else:
            # Suggest beats for new chapter
            if not self.current_project_id:
                return
            
            # Get previous chapter beats
            prev_beats = ""
            if self.current_chapter_id:
                # Find previous chapter
                chapters = self.db_manager.get_projects_with_chapters()
                for p in chapters:
                    if p['id'] == self.current_project_id:
                        ch_list = [(c['id'], idx) for idx, c in enumerate(p['chapters'])]
                        for cid, idx in ch_list:
                            if cid == self.current_chapter_id and idx > 0:
                                prev_id = p['chapters'][idx - 1]['id']
                                prev_beats = self.db_manager.get_chapter_beats(prev_id)
                                break
            
            # Fetch lore package
            lore_package = self.db_manager.fetch_omni_context(self.current_project_id, self.current_chapter_id, [])
            if not lore_package:
               lore_package = {'characters': [], 'story_so_far': [], 'genre': 'fiction', 'world_rules': ''}
            
            # Generate suggestions
            suggested_beats = self.ai_engine.suggest_next_beats(prev_beats, lore_package)
            # self.sidebar.beats_textbox.delete("1.0", "end")
            # self.sidebar.beats_textbox.insert("1.0", suggested_beats)
            # Save to database
            self.db_manager.update_chapter_beats(self.current_chapter_id, suggested_beats)
            logging.info(f"Suggested beats for new chapter")

    def save_current(self):
        if self.current_chapter_id:
            text = self.center_panel.get_editor_content()
            self.db_manager.update_chapter_content(self.current_chapter_id, text)

    def auto_save_loop(self):
        self.save_current()
        self.after(30000, self.auto_save_loop)

    def load_session(self):
        self.sidebar.refresh_tree()
        last_pid = self.db_manager.get_app_state("last_project_id")
        last_cid = self.db_manager.get_app_state("last_chapter_id")
        if last_cid and last_pid:
            try:
                self.load_chapter(int(last_cid), int(last_pid))
            except: pass

    def update_mimic_list(self):
        pid = self.current_project_id if self.current_project_id else 0
        chars = self.db_manager.get_all_characters(pid)
        options = ["Prose Mode"] + [f"Mimic: {name}" for name in chars]
        # TODO: Implement mimic options in new UI
        # self.editor.update_mimic_options(options)
        pass  # Skip for now

    def on_close(self):
        self.save_current()
        if self.current_project_id:
            self.db_manager.save_app_state("last_project_id", self.current_project_id)
        if self.current_chapter_id:
            self.db_manager.save_app_state("last_chapter_id", self.current_chapter_id)
        if hasattr(self.ai_engine, "unload_model"):
            self.ai_engine.unload_model()
        self.destroy()




