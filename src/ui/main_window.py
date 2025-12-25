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
            ("📖 Story Bible", "StoryBible"),
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
        self.is_bible_open = False # Animation State
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
        self.sidebar = SidebarFrame(self, db_manager, self.nav_select, self.load_chapter, self.on_generate_from_beats, self.on_auto_generate_beats)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Col 1: Center Area (Swappable)
        self.center_area = ctk.CTkFrame(self, fg_color=ThemeEngine.BG_MAIN, corner_radius=0)
        self.center_area.grid(row=0, column=1, sticky="nsew")
        self.center_area.grid_rowconfigure(0, weight=1)
        self.center_area.grid_columnconfigure(0, weight=1)
        
        # Pages for Center Area
        self.pages = {}
        # Pass manual_summarize callback
        self.editor = EditorFrame(self.center_area, self.on_editor_instruction, self.manual_summarize)
        self.pages["Writing"] = self.editor
        
        self.settings_page = SettingsFrame(self.center_area)
        self.pages["Settings"] = self.settings_page
        
        # Story Bible View (Hidden by default)
        self.bible_view = StoryBibleView(self.center_area, db_manager)
        
        # Story Bible Drawer (Left-side navigation, hidden initially)
        self.bible_drawer = StoryBibleDrawer(self, on_tab_select=self.show_bible_field)
        # Place on left edge, off-screen initially
        # Will slide from rely=1.0 to rely=0.5 when toggled
        
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
        """Toggle drawer visibility with slide animation."""
        if self.is_bible_open:
            # Slide down and hide
            self.animate_drawer(0.5, 1.0)
            self.is_bible_open = False
        else:
            # Show and slide up
            self.bible_drawer.place(relx=0, rely=1.0, anchor="sw", relheight=0.5)
            self.bible_drawer.tkraise()
            self.animate_drawer(1.0, 0.5)
            self.is_bible_open = True

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
             content = self.editor.get_content()
             if content:
                 self.target_panel = 'assistant'
                 self.is_generating = True
                 self.assistant.append_log("Generating Summary...\n")
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
            current_text = self.editor.get_content()
            self.editor.set_generating(True)
            
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
                     self.current_selection_indices = self.editor.get_selection_indices()

                if plugin_type == 'expand_scene':
                    # Special handling for expansion
                    prompt = "" # Prompt is implicit
                else:
                    # For rewrite/describe, prompt is the text to act on
                    prompt = selection_text
            
            else:
                # Normal writing instruction
                selection = self.editor.get_mimic_selection()
                if selection.startswith("Mimic: "):
                    char_name = selection.replace("Mimic: ", "")
                    char_context = self.db_manager.get_character_details(char_name)

        elif target == 'assistant':
             # Check for Sensory Lab
             if prompt.startswith("SENSORY::"):
                 self.target_panel = 'sensory'
                 plugin_type = "sensory_lab"
                 prompt = prompt.replace("SENSORY::", "")
             else:
                 # Lore Assistant Mode (Deep Search)
                 self.assistant.set_thinking(True)
                 self.assistant.append_log(f"AI: ")
            
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
        threading.Thread(
            target=self._ai_thread,
            args=(prompt, target, current_text, char_context, project_memory, project_name, plugin_type),
            daemon=True
        ).start()

    def _ai_thread(self, prompt, target, context, char_context, memory, project_name, plugin_type=None):
        try:
            if target == 'editor':
                if plugin_type == 'expand_scene':
                    self.ai_engine.expand_scene(context, self.response_queue)
                elif plugin_type:
                    # Specialized plugin generation (Describe/Rewrite)
                    self.ai_engine.generate_plugin_response(prompt, plugin_type, self.response_queue, context_data)
                else:
                    # Normal Prose
                    self.ai_engine.stream_response(prompt, self.response_queue, "", context, char_context)
                    
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
                    self.editor.set_generating(False)
                    self.assistant.set_thinking(False)
                    if self.target_panel == 'assistant':
                        self.assistant.append_log("\n\n")
                        # Trigger Prose Cards ONLY for editor-based plugins, not lore chat
                        # (Replacement UI is only for right-click context menu operations on selected editor text)
                            
                    elif self.target_panel == 'sensory':
                        self.assistant.append_sensory("\n\n")
                else:
                    if self.target_panel == 'editor':
                        self.editor.insert_token(token)
                    elif self.target_panel == 'editor_ghost':
                        self.editor.insert_ghost_token(token)
                    elif self.target_panel == 'assistant':
                        self.assistant.append_log(token)
                    elif self.target_panel == 'sensory':
                        self.assistant.append_sensory(token)
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
            self.assistant.show_replacement_options(self.on_replace_selected)
        else:
            self.assistant.append_log("\n[System: Could not parse variations.]")

    def on_replace_selected(self, index):
        """Callback from Assistant Panel."""
        try:
            if index >= 0 and index < len(self.current_variations):
                new_text = self.current_variations[index]
                if self.current_selection_indices:
                    self.editor.replace_section(self.current_selection_indices, new_text)
                    self.assistant.append_log(f"\n[System: Applied Variation {index+1}]")
            else:
                self.assistant.append_log("\n[System: Cancelled replacement.]")
        except Exception as e:
            logging.error(f"Replacement error: {e}")
            self.assistant.append_log(f"\n[Error: {e}]")
        
        self.assistant.hide_replacement_options()
        self.current_plugin_type = None
        self.accumulated_response = ""
        self.current_selection_indices = None

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
        self.editor.set_generating(True)
        
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
        prose = self.editor.get_content().strip()
        
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




