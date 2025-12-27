import customtkinter as ctk
from src.ui.theme_engine import ThemeEngine

class AutoExpandingTextbox(ctk.CTkTextbox):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        # Use add='+' to ensure we don't overwrite internal bindings
        self.bind("<KeyRelease>", self.update_height, add='+')
        self.min_height = kwargs.get('height', 100)
    
    def update_height(self, event=None):
        try:
            # Access underlying tk widget for accurate line counting (including soft wraps)
            if hasattr(self, '_textbox'):
                # 'displaylines' counts visual lines taking wrap into account
                # Check if widget is mapped/visible to get accurate info, otherwise fall back
                num_lines = int(self._textbox.count("1.0", "end", "displaylines")[0])
            else:
                # Fallback to simple newline count
                content = self.get("1.0", "end-1c")
                num_lines = content.count('\n') + 1
            
            # Additional padding calculation
            # 20px is rough line height for default font approx. Adjust if needed.
            # Using 28px per line to be safe + padding
            line_height = 24
            padding = 20
            
            new_height = max(self.min_height, num_lines * line_height + padding)
            
            # Only configure if changed to avoid loops/flicker
            if self._current_height != new_height:
                self.configure(height=new_height)
                self._current_height = new_height
                
        except Exception as e:
            # Fallback in case of error (e.g. methods not available)
            pass

    @property
    def _current_height(self):
        return getattr(self, '_cached_height', 0)
    
    @_current_height.setter
    def _current_height(self, value):
        self._cached_height = value

class CharacterFrame(ctk.CTkFrame):
    def __init__(self, master, db_manager):
        super().__init__(master, corner_radius=0, fg_color=ThemeEngine.BG_MAIN)
        self.db_manager = db_manager
        self.project_id = None
        
        self.grid_columnconfigure(0, weight=1) # List
        self.grid_columnconfigure(1, weight=3) # Form
        self.grid_rowconfigure(0, weight=1)
        
        # 1. List Area (Left)
        self.list_frame = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color=ThemeEngine.BG_SIDEBAR)
        self.list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 1))
        
        ctk.CTkLabel(self.list_frame, text="CHARACTERS", font=ThemeEngine.FONT_HEADER, text_color=ThemeEngine.TEXT_MUTED).pack(pady=20)
        
        # Add Character Button
        ctk.CTkButton(self.list_frame, text="+ Add Character", command=self.add_character, fg_color=ThemeEngine.ACCENT_PRIMARY).pack(pady=(0, 10), padx=20, fill="x")
        
        self.char_scroll = ctk.CTkScrollableFrame(self.list_frame, fg_color="transparent")
        self.char_scroll.pack(fill="both", expand=True)
        
        ctk.CTkButton(self.list_frame, text="Refresh", command=self.load_list, fg_color=ThemeEngine.BG_HOVER).pack(pady=10)
        
        # 2. Form Area (Right)
        self.form_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.form_frame.grid(row=0, column=1, sticky="nsew", padx=40, pady=40)
        
        ctk.CTkLabel(self.form_frame, text="Character Profile", font=("Georgia", 24)).pack(pady=(0, 20), anchor="w")
        
        self.entries = {}
        
        # --- Header ---
        ctk.CTkLabel(self.form_frame, text="Name", text_color=ThemeEngine.TEXT_MUTED).pack(anchor="w", pady=(10, 5))
        self.entries['name'] = ctk.CTkEntry(self.form_frame, height=35, corner_radius=6, border_width=1, border_color=ThemeEngine.BORDER_COLOR, fg_color=ThemeEngine.BG_SIDEBAR)
        self.entries['name'].pack(fill="x")

        # --- Row 1: Pronouns, Groups, Other Names ---
        row1 = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        row1.pack(fill="x", pady=10)
        
        fields_r1 = [("Pronouns", "pronouns"), ("Groups", "groups"), ("Other Names", "other_names")]
        for i, (label, key) in enumerate(fields_r1):
            f = ctk.CTkFrame(row1, fg_color="transparent")
            f.pack(side="left", fill="x", expand=True, padx=(0 if i==0 else 10, 0))
            ctk.CTkLabel(f, text=label, text_color=ThemeEngine.TEXT_MUTED).pack(anchor="w", pady=(0, 5))
            entry = ctk.CTkEntry(f, height=35, corner_radius=6, border_width=1, border_color=ThemeEngine.BORDER_COLOR, fg_color=ThemeEngine.BG_SIDEBAR)
            entry.pack(fill="x")
            self.entries[key] = entry

        # --- Full Width Fields ---
        # Role/Occupation maps to 'role'
        ctk.CTkLabel(self.form_frame, text="Role / Occupation", text_color=ThemeEngine.TEXT_MUTED).pack(anchor="w", pady=(10, 5))
        self.entries['role'] = ctk.CTkEntry(self.form_frame, height=35, corner_radius=6, border_width=1, border_color=ThemeEngine.BORDER_COLOR, fg_color=ThemeEngine.BG_SIDEBAR)
        self.entries['role'].pack(fill="x")

        # Text Areas
        text_areas = [
            ("Personality", "personality_traits"),
            ("Motivations", "motivations"),
            ("Internal Conflicts", "internal_conflicts"),
            ("Strengths", "strengths"),
            ("Weaknesses", "weaknesses"),
            ("Character Arc", "character_arc"),
            ("Notes / Backstory", "backstory") # Renamed/Mapped
        ]

        for label, key in text_areas:
            ctk.CTkLabel(self.form_frame, text=label, text_color=ThemeEngine.TEXT_MUTED).pack(anchor="w", pady=(15, 5))
            txt = AutoExpandingTextbox(self.form_frame, height=80, corner_radius=6, border_width=1, border_color=ThemeEngine.BORDER_COLOR, fg_color=ThemeEngine.BG_SIDEBAR, wrap="word")
            txt.pack(fill="x")
            self.entries[key] = txt

        ctk.CTkButton(self.form_frame, text="Save Character", height=40, fg_color=ThemeEngine.ACCENT_PRIMARY, command=self.save_character).pack(pady=30, anchor="e")

    def add_character(self):
        # Clear all fields to allow entering a new character
        for widget in self.entries.values():
            if isinstance(widget, ctk.CTkEntry):
                widget.delete(0, 'end')
            elif isinstance(widget, (ctk.CTkTextbox, AutoExpandingTextbox)):
                widget.delete("1.0", "end")
                if hasattr(widget, 'update_height'):
                    widget.update_height()
        
        # Give focus to name
        self.entries['name'].focus_set()

    def load_list(self):
        for w in self.char_scroll.winfo_children(): w.destroy()
        if not self.project_id: return
        
        chars = self.db_manager.get_all_characters(self.project_id)
        for c in chars:
            name = c['name']
            ctk.CTkButton(self.char_scroll, text=name, fg_color="transparent", text_color=ThemeEngine.TEXT_PRIMARY, anchor="w", command=lambda n=name: self.load_details(n)).pack(fill="x", pady=2)

    def load_details(self, name):
        if not self.project_id: return
        details = self.db_manager.get_character_details(name, self.project_id)
        if not details: return
        
        for key, widget in self.entries.items():
            val = details.get(key, "")
            if val is None: val = ""
            
            # Ensure widget is editable just in case
            if hasattr(widget, 'configure'):
                try:
                    widget.configure(state="normal")
                except: pass

            if isinstance(widget, ctk.CTkEntry):
                widget.delete(0, 'end')
                widget.insert(0, str(val))
            elif isinstance(widget, (ctk.CTkTextbox, AutoExpandingTextbox)):
                widget.delete("1.0", "end")
                widget.insert("1.0", str(val))
                if hasattr(widget, 'update_height'):
                    # Force update height after content change
                    widget.update_height()

    def save_character(self):
        if not self.project_id: return
        data = {'project_id': self.project_id}
        for key, widget in self.entries.items():
            if isinstance(widget, ctk.CTkEntry): data[key] = widget.get()
            elif isinstance(widget, ctk.CTkTextbox): data[key] = widget.get("1.0", "end-1c")
            
        if data.get("name"):
            self.db_manager.save_character(data)
            self.load_list()
