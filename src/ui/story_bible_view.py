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
        logging.info(f"[DEBUG INIT] StoryBibleView initialized. Instance ID: {id(self)}")
        
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
            # Store field info on widget to avoid lambda closure issues
            txt._db_field = db_field
            txt._tab_name = tab_name
            # Bind to handler that retrieves field from widget
            txt.bind("<KeyRelease>", self._on_text_change)
            self.text_widgets[tab_name] = txt
        
        # Track current field
        self.current_field = None

    def show_field(self, field_name):
        """Display the specified Bible field or Characters."""
        # Save current field immediately before switching
        if self.current_field and self.current_field != "Characters":
            self._force_save_current()
        
        # Hide all fields and characters
        for widget in self.text_widgets.values():
            widget.grid_forget()
        self.character_frame.grid_forget()
        
        # Show selected content
        if field_name == "Characters":
            self.character_frame.grid(row=0, column=0, sticky="nsew")
            self.character_frame.load_list()
            self.current_field = field_name
            logging.info(f"[DEBUG SHOW] Switched to Characters")
        elif field_name in self.text_widgets:
            widget_to_show = self.text_widgets[field_name]
            # Use safe getter for logging too, to avoid confusing '1' logs
            current_content = self._get_safe_content(widget_to_show)
            content_len = len(current_content) if current_content is not None else "None"
            logging.info(f"[DEBUG SHOW] Switching to '{field_name}', Widget ID: {id(widget_to_show)}, Current content: '{current_content}', Length: {content_len}")
            widget_to_show.grid(row=0, column=0, sticky="nsew", padx=40, pady=40)
            widget_to_show.focus_set()
            self.current_field = field_name
    
    def _get_safe_content(self, widget):
        """
        Helper to safely get content from a CTkTextbox.
        CRITICAL FIX: Always bypass CTk wrapper and use inner _textbox if available.
        Also safeguards against the '1' return code bug.
        """
        content = ""
        try:
            # Plan A: Use the internal Tkinter Text widget directly (Most reliable)
            if hasattr(widget, '_textbox'):
                content = widget._textbox.get("1.0", "end-1c")
            # Plan B: Fallback to wrapper get() if _textbox is missing (Unlikely)
            else:
                logging.warning(f"Widget {widget} has no _textbox attribute. Using wrapper.get()")
                content = widget.get("1.0", "end-1c")
            
            # --- EMERGENCY VALIDATION SHOULD '1' APPEAR ---
            # Check for "1", "1\n", "1 ", etc.
            if str(content).strip() == "1":
                logging.warning(f"[BLOCKED BUG] Widget returned exactly '1' (stripped). Ignoring this save to protect data. Widget: {widget}")
                return None  # Return None to signal invalid read
                
        except Exception as e:
            logging.error(f"Error getting text content: {e}")
            return None
            
        return content

    def force_save_current(self):
        """Immediately save the current field using the active widget (source of truth). Public wrapper."""
        self._force_save_current()

    def _force_save_current(self):
        """Immediately save the current field using the active widget."""
        if not self.current_project_id or not self.current_field:
            return
        
        # Cancel pending debounced save
        db_field = self.field_map.get(self.current_field)
        if db_field and db_field in self.debounce_timers:
            self.after_cancel(self.debounce_timers[db_field])
        
        # DIRECT LOOKUP instead of visibility check
        # This allows saving even if the view is hidden (e.g. user just switched to Editor)
        visible_widget = None
        if self.current_field in self.text_widgets:
            visible_widget = self.text_widgets[self.current_field]

        if visible_widget:
            try:
                content = self._get_safe_content(visible_widget)
                if content is None:
                    logging.warning(f"[FORCE SAVE SKIPPED] Content was invalid (None/1). Field: {self.current_field}")
                    return

                logging.info(f"[FORCE SAVE] Field: {self.current_field} | Content: '{content}'")
                
                db_field = self.field_map[self.current_field]
                self.db_manager.save_bible_field(self.current_project_id, db_field, content)
            except Exception as e:
                logging.error(f"Force save failed: {e}")

    def load_project(self, project_id):
        """Load Bible data for the given project."""
        # 1. Save any pending changes before we potentially wipe them
        if self.current_project_id:
             self._force_save_current()

        # 2. If it's the same project, DON'T reload (preserves unsaved typing/state)
        # This prevents the "Zombie 1" bug where old DB data overwrites new typing
        if self.current_project_id == project_id:
            logging.info(f"[LOAD SKIPPED] Project {project_id} already loaded. Preserving widget state.")
            return

        self.current_project_id = project_id
        
        # Update Character Frame Project ID
        if hasattr(self, 'character_frame'):
            self.character_frame.project_id = project_id
            # If characters are currently visible, reload list
            if self.current_field == "Characters":
                self.character_frame.load_list()

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
    
    
    def _on_text_change(self, event):
        """Handler for text change events - retrieves field from widget."""
        widget = event.widget
        # We need to map the inner widget (source of event) back to the wrapper stored in text_widgets
        # Check against inner textboxes
        found_field = None
        source_wrapper = None
        
        if hasattr(widget, '_db_field'):
            # It's the wrapper itself
            found_field = widget._db_field
            source_wrapper = widget
        else:
            # It's likely the inner widget, find parent wrapper
            for wrapper in self.text_widgets.values():
                if hasattr(wrapper, '_textbox') and str(wrapper._textbox) == str(widget):
                    found_field = wrapper._db_field
                    source_wrapper = wrapper
                    break
        
        if found_field and source_wrapper:
            self._schedule_save(found_field, source_widget=source_wrapper)

    def _schedule_save(self, field_name, source_widget=None):
        """Debounced auto-save for Bible fields."""
        if not self.current_project_id:
            return
        
        if field_name in self.debounce_timers:
            self.after_cancel(self.debounce_timers[field_name])
        
        # Pass widget to perform_save
        self.debounce_timers[field_name] = self.after(1000, lambda: self._perform_save(field_name, source_widget))

    def _perform_save(self, field_name, source_widget=None):
        """Save Bible field to database."""
        if not self.current_project_id:
            return
        
        # Use source_widget if provided (most reliable), otherwise fallback to lookup
        target_widget = source_widget
        
        if not target_widget:
            for tab, field in self.field_map.items():
                if field == field_name:
                    target_widget = self.text_widgets[tab]
                    break
        
        if target_widget:
            content = self._get_safe_content(target_widget)
            if content is None:
                logging.warning(f"[AUTO SAVE SKIPPED] Content was invalid (None/1). Field: {field_name}")
                return

            logging.info(f"[AUTO SAVE] Field: {field_name} | Content: '{content}'")
            self.db_manager.save_bible_field(self.current_project_id, field_name, content)
