import customtkinter as ctk
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path.cwd()))

from src.ui.story_bible_view import StoryBibleView
from src.ui.story_bible_drawer import StoryBibleDrawer
from src.database.db_manager import DatabaseManager

class MockDB:
    def get_all_characters(self, pid):
        return [{'name': 'Test Char', 'role': 'Tester'}]
    def get_character_details(self, name, pid):
        return {'name': 'Test Char', 'pronouns': 'They/Them', 'motivations': 'To debug'}
    def save_character(self, data):
        print(f"SAVING CHAR: {data}")
        return True
    def get_story_bible(self, pid):
        return {'braindump': 'Dump', 'synopsis': 'Syn', 'worldbuilding': 'WB', 'outline': 'Out'}
    def save_bible_field(self, pid, field, content):
        print(f"SAVING BIBLE: {field} -> {content}")

def main():
    ctk.set_appearance_mode("Dark")
    app = ctk.CTk()
    app.geometry("1200x800")
    
    # Use real DB if available to match user env, else mock
    if os.path.exists("data/story_bible.db"):
        db = DatabaseManager("story_bible.db")
        print("Using REAL DB")
    else:
        db = MockDB()
        print("Using MOCK DB")
    
    # Layout
    app.grid_columnconfigure(1, weight=1)
    app.grid_rowconfigure(0, weight=1)
    
    view = StoryBibleView(app, db)
    view.grid(row=0, column=1, sticky="nsew")
    view.current_project_id = 1
    view.character_frame.project_id = 1
    
    def on_tab(name):
        print(f"Selecting tab: {name}")
        view.show_field(name)

    drawer = StoryBibleDrawer(app, on_tab)
    drawer.grid(row=0, column=0, sticky="ns")
    
    # Select first tab
    on_tab("Characters")

    app.mainloop()

if __name__ == "__main__":
    main()
