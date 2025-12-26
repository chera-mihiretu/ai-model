import customtkinter as ctk
from src.ui.theme_engine import ThemeEngine

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
        
        self.char_scroll = ctk.CTkScrollableFrame(self.list_frame, fg_color="transparent")
        self.char_scroll.pack(fill="both", expand=True)
        
        ctk.CTkButton(self.list_frame, text="Refresh", command=self.load_list, fg_color=ThemeEngine.BG_HOVER).pack(pady=10)
        
        # 2. Form Area (Right)
        self.form_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.form_frame.grid(row=0, column=1, sticky="nsew", padx=40, pady=40)
        
        ctk.CTkLabel(self.form_frame, text="Character Profile", font=("Georgia", 24)).pack(pady=(0, 20), anchor="w")
        
        self.entries = {}
        fields = [("Name", "name"), ("Role", "role"), ("Traits", "personality_traits"), ("Speech", "speech_pattern"), ("Relationship", "relationship_to_author")]
        
        for label, key in fields:
            ctk.CTkLabel(self.form_frame, text=label, text_color=ThemeEngine.TEXT_MUTED).pack(anchor="w", pady=(10, 5))
            entry = ctk.CTkEntry(self.form_frame, height=35, corner_radius=6, border_width=1, border_color=ThemeEngine.BORDER_COLOR, fg_color=ThemeEngine.BG_SIDEBAR)
            entry.pack(fill="x")
            self.entries[key] = entry
            
        ctk.CTkLabel(self.form_frame, text="Backstory", text_color=ThemeEngine.TEXT_MUTED).pack(anchor="w", pady=(10, 5))
        self.entries["backstory"] = ctk.CTkTextbox(self.form_frame, height=150, corner_radius=6, border_width=1, border_color=ThemeEngine.BORDER_COLOR, fg_color=ThemeEngine.BG_SIDEBAR)
        self.entries["backstory"].pack(fill="x")
        
        ctk.CTkButton(self.form_frame, text="Save Character", height=40, fg_color=ThemeEngine.ACCENT_PRIMARY, command=self.save_character).pack(pady=30, anchor="e")

    def load_list(self):
        for w in self.char_scroll.winfo_children(): w.destroy()
        if not self.project_id: return
        
        chars = self.db_manager.get_all_characters(self.project_id)
        for name in chars:
            ctk.CTkButton(self.char_scroll, text=name, fg_color="transparent", text_color=ThemeEngine.TEXT_PRIMARY, anchor="w", command=lambda n=name: self.load_details(n)).pack(fill="x", pady=2)

    def load_details(self, name):
        if not self.project_id: return
        details = self.db_manager.get_character_details(name, self.project_id)
        if not details: return
        for key, widget in self.entries.items():
            val = details.get(key, "")
            if isinstance(widget, ctk.CTkEntry):
                widget.delete(0, 'end')
                widget.insert(0, str(val))
            elif isinstance(widget, ctk.CTkTextbox):
                widget.delete("1.0", "end")
                widget.insert("1.0", str(val))

    def save_character(self):
        if not self.project_id: return
        data = {'project_id': self.project_id}
        for key, widget in self.entries.items():
            if isinstance(widget, ctk.CTkEntry): data[key] = widget.get()
            elif isinstance(widget, ctk.CTkTextbox): data[key] = widget.get("1.0", "end-1c")
        if data.get("name"):
            self.db_manager.save_character(data)
            self.load_list()
