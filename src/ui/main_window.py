import customtkinter as ctk
import threading
import queue
import time
from .theme_engine import ThemeEngine

# --- CUSTOM COMPONENTS ---

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
    """
    Left Column: Premium Editorial Navigator (260px)
    """
    def __init__(self, master, db_manager, on_nav_select, on_chapter_select):
        super().__init__(master, width=ThemeEngine.SIDEBAR_WIDTH, corner_radius=0, fg_color=ThemeEngine.BG_SIDEBAR)
        self.db_manager = db_manager
        self.on_nav_select = on_nav_select
        self.on_chapter_select = on_chapter_select
        self.nav_buttons = {}
        
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
        
        # 4. Status Bar (Bottom)
        self.status_label = ctk.CTkLabel(
            self,
            text="v1.9 Ultimate",
            font=("Inter", 10),
            text_color=ThemeEngine.TEXT_MUTED,
            anchor="w"
        )
        self.status_label.grid(row=4, column=0, sticky="ew", padx=20, pady=15)

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
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.grid(row=3, column=0, sticky="ew", padx=8, pady=10)
        
        buttons = [
            ("📝 Writing", "Writing"), 
            ("👥 Characters", "Characters"),
            ("⚙️ Settings", "Settings")
        ]
        
        for text, key in buttons:
            btn = SidebarButton(
                nav_frame,
                text=text,
                command=lambda k=key: self.select_nav(k)
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[key] = btn

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
            
            add_chap = ctk.CTkButton(
                p_frame, text="+", width=20, height=20, 
                fg_color="transparent", text_color=ThemeEngine.TEXT_MUTED,
                hover_color=ThemeEngine.BG_HOVER,
                command=lambda pid=p['id']: self.create_new_chapter(pid)
            )
            add_chap.pack(side="right", padx=10)
            
            # Chapters
            for ch in p['chapters']:
                is_active = (ch['id'] == active_chapter_id)
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


class EditorFrame(ctk.CTkFrame):
    """
    Center Column: Zen Writing Mode (750px)
    """
    def __init__(self, master, on_send_instruction):
        super().__init__(master, corner_radius=0, fg_color=ThemeEngine.BG_MAIN)
        self.on_send_instruction = on_send_instruction
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) 
        
        # 1. Header (Breadcrumbs)
        self._create_header()
        
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
            spacing3=10 # Line spacing 1.6 approx
        )
        self.textbox.grid(row=0, column=1, sticky="nsew", pady=(60, 20)) 
        self.textbox.bind("<KeyRelease>", self.on_text_change)
        
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
        self.breadcrumb.pack(pady=10)
        
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
            # Return 'break' to stop any default event handling if invoked via key binding
            return 'break'

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



class CharacterFrame(ctk.CTkFrame):
    def __init__(self, master, db_manager):
        super().__init__(master, corner_radius=0, fg_color=ThemeEngine.BG_MAIN)
        self.db_manager = db_manager
        
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
        chars = self.db_manager.get_all_characters()
        for name in chars:
            ctk.CTkButton(self.char_scroll, text=name, fg_color="transparent", text_color=ThemeEngine.TEXT_PRIMARY, anchor="w", command=lambda n=name: self.load_details(n)).pack(fill="x", pady=2)

    def load_details(self, name):
        details = self.db_manager.get_character_details(name)
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
        data = {}
        for key, widget in self.entries.items():
            if isinstance(widget, ctk.CTkEntry): data[key] = widget.get()
            elif isinstance(widget, ctk.CTkTextbox): data[key] = widget.get("1.0", "end-1c")
        if data.get("name"):
            self.db_manager.save_character(data)
            self.load_list()


class SettingsFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=ThemeEngine.BG_MAIN)
        ctk.CTkLabel(self, text="Settings", font=("Georgia", 24)).pack(pady=40)
        ctk.CTkLabel(self, text="Coming Soon...", text_color=ThemeEngine.TEXT_MUTED).pack()


class AssistantPanel(ctk.CTkFrame):
    """
    Right Column: Assistant / Chat (300px)
    """
    def __init__(self, master, on_send_instruction):
        super().__init__(master, width=ThemeEngine.ASSISTANT_WIDTH, corner_radius=0, fg_color=ThemeEngine.BG_MAIN)
        self.on_send_instruction = on_send_instruction
        
        # Border Left
        border = ctk.CTkFrame(self, width=1, fg_color=ThemeEngine.BORDER_COLOR)
        border.pack(side="left", fill="y")
        
        # Container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        
        # Empty State
        self.empty_state_lbl = ctk.CTkLabel(
            self.container,
            text="Start a conversation\n\nAsk questions about your project,\nget writing suggestions,\nor paste long text for analysis.",
            font=("Inter", 13),
            text_color=ThemeEngine.TEXT_MUTED,
            justify="center"
        )
        self.empty_state_lbl.pack(pady=(100, 20))
        
        # Chat History (Placeholder for now, could be a scrollable frame)
        self.chat_history = ctk.CTkTextbox(
            self.container, 
            fg_color="transparent", 
            text_color=ThemeEngine.TEXT_MUTED, 
            font=("Inter", 13),
            wrap="word",
            state="disabled"
        )
        # For now, hiding history until interaction
        # self.chat_history.pack(fill="both", expand=True, pady=(0, 20))
        
        # Input Area (Bottom)
        self.input_entry = ctk.CTkEntry(
            self.container,
            placeholder_text="Ask AI...",
            height=40,
            corner_radius=20,
            border_width=1,
            border_color=ThemeEngine.BORDER_COLOR,
            fg_color=ThemeEngine.BG_SIDEBAR,
            text_color=ThemeEngine.TEXT_PRIMARY
        )
        self.input_entry.pack(side="bottom", fill="x", pady=(20, 0))
        self.input_entry.bind("<Return>", lambda e: self.send_action())

    def send_action(self):
        prompt = self.input_entry.get().strip()
        if prompt:
            self.on_send_instruction(prompt)
            self.input_entry.delete(0, 'end')
            # Hide empty state, show log
            self.empty_state_lbl.pack_forget()
            self.chat_history.pack(fill="both", expand=True, pady=(0, 20), side="top")
            self.append_log(f"You: {prompt}\n")

    def append_log(self, text):
        self.chat_history.configure(state="normal")
        self.chat_history.insert("end", text)
        self.chat_history.configure(state="disabled")
        self.chat_history.see("end")
        
    def set_thinking(self, is_thinking):
        if is_thinking:
            self.input_entry.configure(placeholder_text="AI Thinking...", state="disabled")
        else:
            self.input_entry.configure(placeholder_text="Ask AI...", state="normal")


    def clear_log(self):
        self.chat_history.configure(state="normal")
        self.chat_history.delete("1.0", "end")
        self.chat_history.configure(state="disabled")
        # Pack back the empty state
        self.chat_history.pack_forget()
        self.empty_state_lbl.pack(pady=(100, 20))


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
        self.title("Story Bible Pro")
        self.geometry("1400x900")
        self.configure(fg_color=ThemeEngine.BG_MAIN)
        
        # Grid Layout (3 Columns)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Col 0: Sidebar
        self.sidebar = SidebarFrame(self, db_manager, self.nav_select, self.load_chapter)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Col 1: Center Area (Swappable)
        self.center_area = ctk.CTkFrame(self, fg_color=ThemeEngine.BG_MAIN, corner_radius=0)
        self.center_area.grid(row=0, column=1, sticky="nsew")
        self.center_area.grid_rowconfigure(0, weight=1)
        self.center_area.grid_columnconfigure(0, weight=1)
        
        # Pages for Center Area
        self.pages = {}
        self.editor = EditorFrame(self.center_area, lambda p: self.handle_ai_request(p, 'editor'))
        self.pages["Writing"] = self.editor
        
        self.char_page = CharacterFrame(self.center_area, db_manager)
        self.pages["Characters"] = self.char_page
        
        self.settings_page = SettingsFrame(self.center_area)
        self.pages["Settings"] = self.settings_page
        
        # Show default
        self.pages["Writing"].grid(row=0, column=0, sticky="nsew")
        
        # Col 2: Assistant (Always visible)
        self.assistant = AssistantPanel(self, lambda p: self.handle_ai_request(p, 'assistant'))
        self.assistant.grid(row=0, column=2, sticky="nsew")

        # Load Data
        self.sidebar.select_nav("Writing")
        self.load_session()
        self.update_mimic_list()
        
        # Event Loops
        self.after(100, self.check_queue)
        self.after(30000, self.auto_save_loop)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def nav_select(self, name):
        # Swap Center Page
        for page in self.pages.values():
            page.grid_forget()
        
        if name in self.pages:
            self.pages[name].grid(row=0, column=0, sticky="nsew")
            
        if name == "Characters":
            self.char_page.load_list()
        elif name == "Writing":
            self.update_mimic_list()

    def handle_ai_request(self, prompt, target):
        if self.is_generating: return
        
        self.target_panel = target
        current_text = ""
        char_context = None
        project_memory = ""
        project_name = "Current Project"
        
        if target == 'editor':
            # Writing Mode
            current_text = self.editor.get_content()
            self.editor.set_generating(True)
            selection = self.editor.get_mimic_selection()
            if selection.startswith("Mimic: "):
                char_name = selection.replace("Mimic: ", "")
                char_context = self.db_manager.get_character_details(char_name)

        elif target == 'assistant':
            # Lore Assistant Mode (Deep Search)
            self.assistant.set_thinking(True)
            self.assistant.append_log(f"AI: ")
            
            if self.current_project_id:
                # Get Project Name
                # Small optimization: could cache this
                projects = self.db_manager.get_projects_with_chapters()
                for p in projects:
                    if p['id'] == self.current_project_id:
                        project_name = p['name']
                        break
                
                # Fetch DEEP Memory based on prompt query
                project_memory = self.db_manager.get_deep_memory(self.current_project_id, prompt)
            else:
                project_memory = "No project selected."

        self.is_generating = True
        threading.Thread(
            target=self._ai_thread,
            args=(prompt, target, current_text, char_context, project_memory, project_name),
            daemon=True
        ).start()

    def _ai_thread(self, prompt, target, context, char_context, memory, project_name):
        try:
            if target == 'editor':
                self.ai_engine.stream_response(prompt, self.response_queue, "", context, char_context)
                
                # After writing, trigger beat summary update if content is substantial (simple heuristic)
                if len(context) > 100 and self.current_project_id and self.current_chapter_id:
                     # Fire and forget summary update
                     threading.Thread(target=self._update_beat_summary, args=(context,), daemon=True).start()

            elif target == 'assistant':
                self.ai_engine.ask_lore_assistant(prompt, self.response_queue, memory, project_name)
        except Exception as e:
            self.response_queue.put(f"Error: {e}")
            self.response_queue.put("[[END]]")

    def _update_beat_summary(self, text):
        """Background task to generate and save story beat."""
        summary = self.ai_engine.generate_beat_summary(text)
        if summary and self.current_project_id and self.current_chapter_id:
            self.db_manager.save_beat(self.current_project_id, self.current_chapter_id, summary)
            print(f"[DEBUG] Beat saved for Ch {self.current_chapter_id}: {summary}")

    def check_queue(self):
        try:
            while True:
                token = self.response_queue.get_nowait()
                if token == "[[END]]":
                    self.is_generating = False
                    self.editor.set_generating(False)
                    self.assistant.set_thinking(False)
                    if self.target_panel == 'assistant':
                        self.assistant.append_log("\n\n")
                else:
                    if self.target_panel == 'editor':
                        self.editor.insert_token(token)
                    elif self.target_panel == 'assistant':
                        self.assistant.append_log(token)
        except queue.Empty: pass
        finally: self.after(50, self.check_queue)

    def load_chapter(self, chapter_id, project_id):
        self.save_current()
        
        # Clear Assistant if switching projects
        if self.current_project_id != project_id:
            self.assistant.clear_log()
            
        content = self.db_manager.get_chapter_content(chapter_id)
        
        title = "Unknown"
        projects = self.db_manager.get_projects_with_chapters()
        for p in projects:
            if p['id'] == project_id:
                for c in p['chapters']:
                    if c['id'] == chapter_id:
                        title = f"{p['name']} / {c['title']}"
                        break
        
        self.current_project_id = project_id
        self.current_chapter_id = chapter_id
        
        self.editor.load_content(title, content)
        self.sidebar.refresh_tree(active_chapter_id=chapter_id)
        # Ensure we switch back to writing view
        self.sidebar.select_nav("Writing")

    def save_current(self):
        if self.current_chapter_id:
            text = self.editor.get_content()
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
        chars = self.db_manager.get_all_characters()
        options = ["Prose Mode"] + [f"Mimic: {name}" for name in chars]
        self.editor.update_mimic_options(options)

    def on_close(self):
        self.save_current()
        if self.current_project_id:
            self.db_manager.save_app_state("last_project_id", self.current_project_id)
        if self.current_chapter_id:
            self.db_manager.save_app_state("last_chapter_id", self.current_chapter_id)
        if hasattr(self.ai_engine, "unload_model"):
            self.ai_engine.unload_model()
        self.destroy()
