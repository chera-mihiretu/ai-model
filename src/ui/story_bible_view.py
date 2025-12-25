import customtkinter as ctk
import logging
from src.ui.theme_engine import ThemeEngine
from src.ui.character_frame import CharacterFrame

class StoryBibleView(ctk.CTkFrame):
    """
    Story Bible content view - displays one field at a time.
    Replaces the writing canvas when a Bible tab is selected.
    """
    def __init__(self, master, db_manager):
        super().__init__(master, fg_color=ThemeEngine.BG_MAIN, corner_radius=0)
        self.db_manager = db_manager
        self.current_project_id = None
        self.debounce_timers = {}
        
        # Single column layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Characters frame (special case)
        self.character_frame = CharacterFrame(self, db_manager)
        
        # Bible field mapping
        self.field_map = {
            "Braindump": "braindump",
            "Genre": "genre",
            "Style": "style",
            "Synopsis": "synopsis",
            "World Building": "worldbuilding",
            "Outline": "outline"
        }
        
        # Create textbox widgets for each field
        self.text_widgets = {}
        for tab_name, db_field in self.field_map.items():
            txt = ctk.CTkTextbox(
                self,
                wrap="word",
                fg_color=ThemeEngine.BG_INPUT,
                text_color=ThemeEngine.TEXT_PRIMARY,
                border_width=1,
                border_color=ThemeEngine.BORDER_COLOR,
                font=("Inter", 16),
                undo=True
            )
            txt.bind("<KeyRelease>", lambda e, f=db_field: self._schedule_save(f))
            self.text_widgets[tab_name] = txt
        
        # Track current field
        self.current_field = None

    def show_field(self, field_name):
        """Display the specified Bible field or Characters."""
        # Hide all fields and characters
        for widget in self.text_widgets.values():
            widget.grid_forget()
        self.character_frame.grid_forget()
        
        # Show selected content
        if field_name == "Characters":
            self.character_frame.grid(row=0, column=0, sticky="nsew")
            self.character_frame.load_list()
            self.current_field = field_name
        elif field_name in self.text_widgets:
            self.text_widgets[field_name].grid(row=0, column=0, sticky="nsew", padx=40, pady=40)
            self.text_widgets[field_name].focus_set()
            self.current_field = field_name

    def load_project(self, project_id):
        """Load Bible data for the given project."""
        self.current_project_id = project_id
        if not project_id:
            return
        
        data = self.db_manager.get_story_bible(project_id)
        if data:
            for tab_name, db_field in self.field_map.items():
                if tab_name in self.text_widgets:
                    content = data.get(db_field, "")
                    widget = self.text_widgets[tab_name]
                    widget.delete("1.0", "end")
                    widget.insert("1.0", content)

    def _schedule_save(self, field_name):
        """Debounced auto-save for Bible fields."""
        if not self.current_project_id:
            return
        
        if field_name in self.debounce_timers:
            self.after_cancel(self.debounce_timers[field_name])
        
        self.debounce_timers[field_name] = self.after(1000, lambda: self._perform_save(field_name))

    def _perform_save(self, field_name):
        """Save Bible field to database."""
        if not self.current_project_id:
            return
        
        # Find the widget by db field name
        target_widget = None
        for tab, field in self.field_map.items():
            if field == field_name:
                target_widget = self.text_widgets[tab]
                break
        
        if target_widget:
            content = target_widget.get("1.0", "end-1c")
            self.db_manager.save_bible_field(self.current_project_id, field_name, content)
            logging.info(f"Auto-saved Bible field: {field_name}")
