import sqlite3
import logging
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_name="story_bible.db"):
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.db_path = self.base_dir / "data" / db_name
        self.setup_database()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def setup_database(self):
        """Initialize the database schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Create Tables
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS characters (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        role TEXT,
                        personality_traits TEXT,
                        speech_pattern TEXT,
                        relationship_to_author TEXT,
                        backstory TEXT,
                        continuity_notes TEXT
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS projects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        genre TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chapters (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        content TEXT,
                        chapter_order INTEGER,
                        FOREIGN KEY (project_id) REFERENCES projects (id)
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS app_state (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )
                """)
                
                conn.commit()
                logging.info(f"Database initialized at {self.db_path}")
        except sqlite3.Error as e:
            logging.error(f"Database initialization error: {e}")

    # --- Project Methods ---
    def create_project(self, name: str, genre: str = ""):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO projects (name, genre) VALUES (?, ?)", (name, genre))
                project_id = cursor.lastrowid
                conn.commit()
                return project_id
        except sqlite3.Error as e:
            logging.error(f"Create project error: {e}")
            return None

    def get_projects_with_chapters(self):
        """Returns a list of projects, each with a 'chapters' list."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Get Projects
                cursor.execute("SELECT id, name FROM projects ORDER BY created_at DESC")
                projects = [{'id': r[0], 'name': r[1], 'chapters': []} for r in cursor.fetchall()]
                
                # Get Chapters for each
                for p in projects:
                    cursor.execute("SELECT id, title FROM chapters WHERE project_id = ? ORDER BY chapter_order", (p['id'],))
                    p['chapters'] = [{'id': r[0], 'title': r[1]} for r in cursor.fetchall()]
                    
                return projects
        except sqlite3.Error as e:
            logging.error(f"Get projects error: {e}")
            return []

    # --- Chapter Methods ---
    def create_chapter(self, project_id: int, title: str):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Get next order
                cursor.execute("SELECT MAX(chapter_order) FROM chapters WHERE project_id = ?", (project_id,))
                res = cursor.fetchone()[0]
                next_order = 1 if res is None else res + 1
                
                cursor.execute(
                    "INSERT INTO chapters (project_id, title, content, chapter_order) VALUES (?, ?, ?, ?)",
                    (project_id, title, "", next_order)
                )
                chap_id = cursor.lastrowid
                conn.commit()
                return chap_id
        except sqlite3.Error as e:
            logging.error(f"Create chapter error: {e}")
            return None

    def update_chapter_content(self, chapter_id: int, content: str):
        try:
            with self.get_connection() as conn:
                conn.execute("UPDATE chapters SET content = ? WHERE id = ?", (content, chapter_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Update chapter error: {e}")
            return False

    def get_chapter_content(self, chapter_id: int):
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("SELECT content FROM chapters WHERE id = ?", (chapter_id,))
                res = cursor.fetchone()
                return res[0] if res else ""
        except sqlite3.Error as e:
            logging.error(f"Get chapter content error: {e}")
            return ""

    def get_project_memory(self, project_id: int) -> str:
        """
        Aggregates all Characters and Chapters for a project into a single string.
        """
        memory = []
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 1. Characters (Global for now, but contextually relevant)
                memory.append("[CHARACTERS]")
                cursor.execute("SELECT name, role, personality_traits, backstory FROM characters")
                chars = cursor.fetchall()
                if chars:
                    for c in chars:
                        memory.append(f"Name: {c[0]}\nRole: {c[1]}\nTraits: {c[2]}\nBackstory: {c[3]}")
                        memory.append("---")
                else:
                    memory.append("No characters defined.")

                # 2. Project Chapters
                memory.append("\n[STORY CONTENT]")
                cursor.execute("SELECT title, content FROM chapters WHERE project_id = ? ORDER BY chapter_order", (project_id,))
                chapters = cursor.fetchall()
                if chapters:
                    for ch in chapters:
                        memory.append(f"Chapter: {ch[0]}")
                        memory.append(f"{ch[1]}") # Content
                        memory.append("---")
                else:
                    memory.append("No chapters written.")

            return "\n".join(memory)
        except sqlite3.Error as e:
            logging.error(f"Get project memory error: {e}")
            return "Error retrieving project memory."

    # --- State Methods ---
    def save_app_state(self, key: str, value: str):
        try:
            with self.get_connection() as conn:
                conn.execute("INSERT OR REPLACE INTO app_state (key, value) VALUES (?, ?)", (key, str(value)))
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Save state error: {e}")

    def get_app_state(self, key: str):
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("SELECT value FROM app_state WHERE key = ?", (key,))
                res = cursor.fetchone()
                return res[0] if res else None
        except sqlite3.Error as e:
            logging.error(f"Get state error: {e}")
            return None

    # --- Character Methods (Existing) ---
    def save_character(self, data: dict):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO characters 
                    (name, role, personality_traits, speech_pattern, relationship_to_author, backstory)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    data['name'], 
                    data.get('role', ''),
                    data.get('personality_traits', ''),
                    data.get('speech_pattern', ''),
                    data.get('relationship_to_author', ''),
                    data.get('backstory', '')
                ))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Save character error: {e}")
            return False

    def get_all_characters(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM characters ORDER BY name")
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Get characters error: {e}")
            return []

    def get_character_details(self, name: str):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM characters WHERE name = ?", (name,))
                row = cursor.fetchone()
                if row:
                    cols = ['id', 'name', 'role', 'personality_traits', 'speech_pattern', 'relationship_to_author', 'backstory', 'continuity_notes']
                    return dict(zip(cols, row))
                return None
        except sqlite3.Error as e:
            logging.error(f"Get details error: {e}")
            return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db = DatabaseManager()
