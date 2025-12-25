import customtkinter as ctk
import logging
from src.ui.theme_engine import ThemeEngine

class StoryBibleView(ctk.CTkFrame):
    """
    Full-page Story Bible Content View.
    Replaces the editor when a Bible tab is selected.
    """
    def __init__(self, master, db_manager):
        super().__init__(master, fg_color=ThemeEngine.BG_MAIN, corner_radius=0)
        self.db_manager = db_manager
        self.current_project_id = None
        self.debounce_timers = {}
        
        # Grid layout
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Header (Shows current section name)
        self.header_label = ctk.CTkLabel(
            self, 
            text="Story Bible", 
            font=("Inter", 24, "bold"),
            text_color=ThemeEngine.TEXT_PRIMARY,
            anchor="w"
        )
        self.header_label.grid(row=0, column=0, sticky="ew", padx=40, pady=(40, 20))
        
        # Content Container
        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.grid(row=1, column=0, sticky="nsew", padx=40, pady=(0, 40))
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)
        
        # Map tab names to DB fields
        self.field_map = {
            "Braindump": "braindump",
            "Genre": "genre",
            "Style": "style",
            "Synopsis": "synopsis",
            "Characters": "characters",
            "World": "worldbuilding",
            "Outline": "outline"
        }
        
        self.text_widgets = {}
        
        # Create text widget for EACH field (initialized but hidden)
        for tab_name, db_field in self.field_map.items():
            txt = ctk.CTkTextbox(
                self.content_area,
                wrap="word",
                fg_color=ThemeEngine.BG_INPUT,
                text_color=ThemeEngine.TEXT_PRIMARY,
                border_width=1,
                border_color=ThemeEngine.BORDER_COLOR,
                font=("Inter", 16),
                undo=True
            )
            # Bind autosave
            txt.bind("<KeyRelease>", lambda e, f=db_field: self._schedule_save(f))
            self.text_widgets[tab_name] = txt # Store by Tab Name for easy lookup

    def show_section(self, tab_name):
        """Displays the specified section."""
        # Hide all
        for w in self.text_widgets.values():
            w.grid_forget()
            
        # Update Header
        self.header_label.configure(text=tab_name)
        
        # Show specific
        if tab_name in self.text_widgets:
            widget = self.text_widgets[tab_name]
            widget.grid(row=0, column=0, sticky="nsew")
            widget.focus_set()

    def load_project(self, project_id):
        """Loads Story Bible data for the given project."""
        self.current_project_id = project_id
        if not project_id:
            return

        data = self.db_manager.get_story_bible(project_id)
        if not data:
            return

        # Populate fields
        for tab_name, db_field in self.field_map.items():
            content = data.get(db_field, "")
            widget = self.text_widgets[tab_name]
            
            # Only update if different to avoid cursor jump? 
            # Actually, this is usually called on project load, so full replace is fine.
            # If called while typing, that would be bad. 
            # We assume load_project is called only on switch.
            
            widget.delete("1.0", "end")
            widget.insert("1.0", content)

    def _schedule_save(self, field_name):
        """Debounced save trigger."""
        if not self.current_project_id:
            return

        if field_name in self.debounce_timers:
            self.after_cancel(self.debounce_timers[field_name])
        
        self.debounce_timers[field_name] = self.after(1000, lambda: self._perform_save(field_name))

    def _perform_save(self, field_name):
        """Executes the save."""
        if not self.current_project_id:
            return
            
        # Find widget by field name (reverse lookup)
        # Or just loop
        target_widget = None
        for tab, field in self.field_map.items():
            if field == field_name:
                target_widget = self.text_widgets[tab]
                break
        
        if not target_widget:
            return
            
        content = target_widget.get("1.0", "end-1c")
        self.db_manager.save_bible_field(self.current_project_id, field_name, content)
        logging.info(f"Auto-saved Bible field: {field_name}")
