import customtkinter as ctk
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path.cwd()))

from src.ui.character_frame import CharacterFrame
from src.database.db_manager import DatabaseManager

class MockDB:
    def get_all_characters(self, pid):
        return [{'name': 'Test Char'}]
    def get_character_details(self, name, pid):
        return {'name': 'Test Char', 'pronouns': 'They/Them', 'motivations': 'To debug'}
    def save_character(self, data):
        print(f"SAVING: {data}")
        return True

def main():
    app = ctk.CTk()
    app.geometry("1000x800")
    
    # Use real DB if available to match user env, else mock
    if os.path.exists("data/story_bible.db"):
        db = DatabaseManager("story_bible.db")
        print("Using REAL DB")
    else:
        db = MockDB()
        print("Using MOCK DB")

    frame = CharacterFrame(app, db)
    frame.project_id = 1
    frame.pack(fill="both", expand=True)

    # Load list
    frame.load_list()

    app.mainloop()

if __name__ == "__main__":
    main()
