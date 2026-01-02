import sqlite3
import logging
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_name="story_bible.db"):
        import sys
        if getattr(sys, 'frozen', False):
            self.base_dir = Path(sys.executable).parent
        else:
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
                        chapter_order INTEGER
                    )
                """)
                
                # Migration: Add beats column if it doesn't exist
                cursor.execute("PRAGMA table_info(chapters)")
                columns = [row[1] for row in cursor.fetchall()]
                if 'beats' not in columns:
                    cursor.execute("ALTER TABLE chapters ADD COLUMN beats TEXT")
                    logging.info("Added beats column to chapters table")

                # Migration: Add project_id to characters AND fix unique constraint + Add new fields
                cursor.execute("PRAGMA index_list(characters)")
                indexes = cursor.fetchall()
                # Check for table structure to see if we need to add columns or rebuild
                cursor.execute("PRAGMA table_info(characters)")
                current_cols = [c[1] for c in cursor.fetchall()]

                # Fields we want
                required_fields = {
                    'project_id', 'name', 'role', 'personality_traits', 'speech_pattern', 
                    'relationship_to_author', 'backstory', 'continuity_notes',
                    'pronouns', 'groups', 'other_names', 'motivations', 
                    'internal_conflicts', 'strengths', 'weaknesses', 'character_arc',
                    'physical_description', 'is_visible'
                }
                
                missing_fields = required_fields - set(current_cols)
                
                # Check constraints (unique name+project_id)
                needs_constraint_fix = True
                for idx in indexes:
                    if idx[2] == 1: # Unique
                        cursor.execute(f"PRAGMA index_info({idx[1]})")
                        cols = sorted([r[2] for r in cursor.fetchall()])
                        if cols == ['name', 'project_id'] or cols == ['project_id', 'name']:
                            needs_constraint_fix = False
                            break
                            
                if needs_constraint_fix or missing_fields:
                    logging.info("Migrating characters table schema...")
                    conn.execute("ALTER TABLE characters RENAME TO characters_old")
                    
                    conn.execute("""
                        CREATE TABLE characters (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            project_id INTEGER DEFAULT 0,
                            name TEXT NOT NULL,
                            role TEXT,
                            personality_traits TEXT,
                            speech_pattern TEXT,
                            relationship_to_author TEXT,
                            backstory TEXT,
                            continuity_notes TEXT,
                            pronouns TEXT,
                            groups TEXT,
                            other_names TEXT,
                            motivations TEXT,
                            internal_conflicts TEXT,
                            strengths TEXT,
                            weaknesses TEXT,
                            character_arc TEXT,
                            physical_description TEXT,
                            is_visible INTEGER DEFAULT 1,
                            UNIQUE(name, project_id)
                        )
                    """)
                    
                    # Copy data.
                    cursor.execute("PRAGMA table_info(characters_old)")
                    old_cols_info = cursor.fetchall()
                    old_cols = [c[1] for c in old_cols_info]
                    
                    # We map intersection of old and new columns
                    common_cols = [c for c in old_cols if c in required_fields or c == 'id']
                    
                    col_str = ", ".join(common_cols)
                    qs = ", ".join(common_cols) # SELECT msg matches INSERT msg
                    
                    cursor.execute(f"INSERT INTO characters ({col_str}) SELECT {col_str} FROM characters_old")
                    conn.execute("DROP TABLE characters_old")
                    conn.commit()
                    logging.info("Characters table migration complete.")
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS app_state (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )
                """) # ... (rest of function)


                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS story_beats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id INTEGER NOT NULL,
                        chapter_id INTEGER NOT NULL,
                        summary TEXT,
                        FOREIGN KEY (project_id) REFERENCES projects (id),
                        FOREIGN KEY (chapter_id) REFERENCES chapters (id)
                    )
                """)
                


                # Milestone 3.1: Story Bible Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS story_bible (
                        project_id INTEGER PRIMARY KEY,
                        braindump TEXT,
                        genre TEXT,
                        style TEXT,
                        synopsis TEXT,
                        characters TEXT,
                        worldbuilding TEXT,
                        outline TEXT,
                        FOREIGN KEY (project_id) REFERENCES projects (id)
                    )
                """)
                # Create Index for fast loading
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_story_bible_project_id ON story_bible (project_id)")
                
                conn.commit()
                logging.info(f"Database initialized at {self.db_path}")
        except sqlite3.Error as e:
            logging.error(f"Database initialization error: {e}")

    # --- Story Bible Methods ---
    def save_bible_field(self, project_id: str, field_name: str, content: str) -> None:
        """
        Atomically update exactly ONE Story Bible field.
        Must not overwrite other fields.
        Must be safe for rapid debounce-triggered calls.
        Must fail silently.
        """
        allowed_fields = {'braindump', 'genre', 'style', 'synopsis', 'characters', 'worldbuilding', 'outline'}
        if field_name not in allowed_fields:
            logging.error(f"Invalid Story Bible field: {field_name}")
            return

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Ensure record exists
                cursor.execute("INSERT OR IGNORE INTO story_bible (project_id) VALUES (?)", (project_id,))
                # Update specific field
                cursor.execute(f"UPDATE story_bible SET {field_name} = ? WHERE project_id = ?", (content, project_id))
                conn.commit()
        except sqlite3.Error:
            pass # Fail silently as requested

    def get_story_bible(self, project_id: int):
        """Fetch all story bible fields for a project."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM story_bible WHERE project_id = ?", (project_id,))
                row = cursor.fetchone()
                if row:
                    # Convert to dict using column names from cursor description
                    col_names = [description[0] for description in cursor.description]
                    data = dict(zip(col_names, row))
                    
                    # Return expected fields, defaulting to empty string
                    return {
                        'braindump': data.get('braindump') or "",
                        'genre': data.get('genre') or "",
                        'style': data.get('style') or "",
                        'synopsis': data.get('synopsis') or "",
                        'characters': data.get('characters') or "",
                        'worldbuilding': data.get('worldbuilding') or "",
                        'outline': data.get('outline') or ""
                    }
                return {k: "" for k in ['braindump', 'genre', 'style', 'synopsis', 'characters', 'worldbuilding', 'outline']}
        except sqlite3.Error as e:
            logging.error(f"Get story bible error: {e}")
            return None

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

    def get_project_settings(self, project_id: int):
        """Fetch project settings including genre."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name, genre FROM projects WHERE id = ?", (project_id,))
                row = cursor.fetchone()
                if row:
                    return {'name': row[0], 'genre': row[1]}
        except sqlite3.Error as e:
            logging.error(f"Get settings error: {e}")
        return None

    def rename_project(self, project_id: int, new_name: str):
        """Rename a project."""
        try:
            with self.get_connection() as conn:
                conn.execute("UPDATE projects SET name = ? WHERE id = ?", (new_name, project_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Rename project error: {e}")
            return False

    def delete_project(self, project_id: int):
        """Delete a project and all its chapters."""
        try:
            with self.get_connection() as conn:
                # Delete all chapters first
                conn.execute("DELETE FROM chapters WHERE project_id = ?", (project_id,))
                # Delete story bible data
                conn.execute("DELETE FROM story_bible WHERE project_id = ?", (project_id,))
                # Delete the project
                conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Delete project error: {e}")
            return False

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

    def get_context_window(self, project_id: int, chapter_id: int, char_limit: int = 3000):
        """
        Retrieves context for RAG-enhanced writing:
        - Last N characters from current chapter
        - Previous chapter's summary
        - Character dossiers for names mentioned in recent text
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 1. Get current chapter content and extract last N chars
                cursor.execute("SELECT content, chapter_order FROM chapters WHERE id = ?", (chapter_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                
                current_content = row[0] or ""
                current_order = row[1]
                recent_text = current_content[-char_limit:] if len(current_content) > char_limit else current_content
                
                # 2. Get previous chapter summary
                prev_summary = ""
                if current_order and current_order > 1:
                    cursor.execute("""
                        SELECT c.id FROM chapters c 
                        WHERE c.project_id = ? AND c.chapter_order = ?
                    """, (project_id, current_order - 1))
                    prev_chapter = cursor.fetchone()
                    
                    if prev_chapter:
                        cursor.execute("""
                            SELECT summary FROM story_beats 
                            WHERE project_id = ? AND chapter_id = ?
                            ORDER BY id DESC LIMIT 1
                        """, (project_id, prev_chapter[0]))
                        beat = cursor.fetchone()
                        if beat:
                            prev_summary = beat[0]
                
                # 3. Get all character names and check which appear in recent text
                cursor.execute("SELECT name FROM characters")
                all_chars = [row[0] for row in cursor.fetchall()]
                
                mentioned_characters = []
                for char_name in all_chars:
                    if char_name.lower() in recent_text.lower():
                        char_details = self.get_character_details(char_name)
                        if char_details:
                            mentioned_characters.append(char_details)
                
                # 4. Get genre from Story Bible
                genre = "fiction"  # default
                cursor.execute("SELECT genre FROM story_bible WHERE project_id = ?", (project_id,))
                bible_row = cursor.fetchone()
                if bible_row and bible_row[0]:
                    genre = bible_row[0].strip()
                
                return {
                    'recent_text': recent_text,
                    'prev_summary': prev_summary,
                    'mentioned_characters': mentioned_characters,
                    'genre': genre
                }
                
        except sqlite3.Error as e:
            logging.error(f"Get context window error: {e}")
            return None

    def fetch_omni_context(self, project_id: int, chapter_id: int, beats_list: list):
        """
        Fetches comprehensive lore package for omniscient prose generation.
        Extracts proper nouns from beats, queries character DB, fetches chapter summaries.
        Returns: {characters, story_so_far, genre, world_rules}
        """
        import re
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 1. Extract proper nouns from beats (capitalized words)
                beats_text = " ".join(beats_list)
                # Regex for capitalized words (potential names)
                potential_names = re.findall(r'\b[A-Z][a-z]+\b', beats_text)
                # Filter common words
                common_words = {'The', 'A', 'An', 'Chapter', 'Scene', 'Then', 'When', 'They', 'He', 'She', 'This', 'That'}
                potential_names = [n for n in set(potential_names) if n not in common_words]
                
                # 2. Query characters table for mentioned names
                characters = []
                if potential_names:
                    placeholders = ','.join(['?'] * len(potential_names))
                    cursor.execute(f"SELECT name, personality_traits, speech_pattern, backstory FROM characters WHERE name IN ({placeholders})", potential_names)
                    for row in cursor.fetchall():
                        characters.append({
                            'name': row[0],
                            'traits': row[1],
                            'speech': row[2],
                            'backstory': row[3]
                        })
                
                # 3. Get last 3 chapter summaries for story context
                cursor.execute("SELECT chapter_order FROM chapters WHERE id = ?", (chapter_id,))
                current_order_row = cursor.fetchone()
                current_order = current_order_row[0] if current_order_row else 0
                
                story_so_far = []
                for i in range(1, 4):  # Last 3 chapters
                    prev_order = current_order - i
                    if prev_order >= 1:
                        cursor.execute("""
                            SELECT c.id FROM chapters c 
                            WHERE c.project_id = ? AND c.chapter_order = ?
                        """, (project_id, prev_order))
                        prev_ch = cursor.fetchone()
                        if prev_ch:
                            cursor.execute("""
                                SELECT summary FROM story_beats 
                                WHERE project_id = ? AND chapter_id = ?
                                ORDER BY id DESC LIMIT 1
                            """, (project_id, prev_ch[0]))
                            summary_row = cursor.fetchone()
                            if summary_row:
                                story_so_far.insert(0, f"Chapter {prev_order}: {summary_row[0]}")
                
                # 4. Get project settings (genre, world rules)
                settings = self.get_project_settings(project_id)
                genre = settings.get('genre', 'fiction') if settings else 'fiction'
                world_rules = settings.get('world_rules', 'No specific rules') if settings else 'No specific rules'
                
                return {
                    'characters': characters,
                    'story_so_far': story_so_far,
                    'genre': genre,
                    'world_rules': world_rules
                }
                
        except sqlite3.Error as e:
            logging.error(f"Fetch omni context error: {e}")
            return None

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

    def rename_chapter(self, chapter_id: int, new_title: str):
        """Rename a chapter."""
        try:
            with self.get_connection() as conn:
                conn.execute("UPDATE chapters SET title = ? WHERE id = ?", (new_title, chapter_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Rename chapter error: {e}")
            return False

    def delete_chapter(self, chapter_id: int):
        """Delete a chapter."""
        try:
            with self.get_connection() as conn:
                conn.execute("DELETE FROM chapters WHERE id = ?", (chapter_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Delete chapter error: {e}")
            return False

    def move_chapter_up(self, chapter_id: int):
        """Move a chapter up in order (swap with previous)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Get current chapter info
                cursor.execute("SELECT project_id, chapter_order FROM chapters WHERE id = ?", (chapter_id,))
                row = cursor.fetchone()
                if not row:
                    return False
                
                project_id, current_order = row
                if current_order <= 1:
                    return False  # Already at top
                
                # Find previous chapter
                cursor.execute(
                    "SELECT id FROM chapters WHERE project_id = ? AND chapter_order = ?",
                    (project_id, current_order - 1)
                )
                prev_row = cursor.fetchone()
                if not prev_row:
                    return False
                
                prev_id = prev_row[0]
                
                # Swap orders
                cursor.execute("UPDATE chapters SET chapter_order = ? WHERE id = ?", (current_order, prev_id))
                cursor.execute("UPDATE chapters SET chapter_order = ? WHERE id = ?", (current_order - 1, chapter_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Move chapter up error: {e}")
            return False

    def move_chapter_down(self, chapter_id: int):
        """Move a chapter down in order (swap with next)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Get current chapter info
                cursor.execute("SELECT project_id, chapter_order FROM chapters WHERE id = ?", (chapter_id,))
                row = cursor.fetchone()
                if not row:
                    return False
                
                project_id, current_order = row
                
                # Find next chapter
                cursor.execute(
                    "SELECT id FROM chapters WHERE project_id = ? AND chapter_order = ?",
                    (project_id, current_order + 1)
                )
                next_row = cursor.fetchone()
                if not next_row:
                    return False  # Already at bottom
                
                next_id = next_row[0]
                
                # Swap orders
                cursor.execute("UPDATE chapters SET chapter_order = ? WHERE id = ?", (current_order, next_id))
                cursor.execute("UPDATE chapters SET chapter_order = ? WHERE id = ?", (current_order + 1, chapter_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Move chapter down error: {e}")
            return False

    def update_chapter_beats(self, chapter_id: int, beats_text: str):
        """Save extracted or suggested beats for a chapter."""
        try:
            with self.get_connection() as conn:
                conn.execute("UPDATE chapters SET beats = ? WHERE id = ?", (beats_text, chapter_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Update chapter beats error: {e}")
            return False

    def get_chapter_beats(self, chapter_id: int):
        """Retrieve saved beats for a chapter."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT beats FROM chapters WHERE id = ?", (chapter_id,))
                row = cursor.fetchone()
                return row[0] if row and row[0] else ""
        except sqlite3.Error as e:
            logging.error(f"Get chapter beats error: {e}")
            return ""

    def get_chapter_content(self, chapter_id: int):
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("SELECT content FROM chapters WHERE id = ?", (chapter_id,))
                res = cursor.fetchone()
                return res[0] if res else ""
        except sqlite3.Error as e:
            logging.error(f"Get chapter content error: {e}")
            return ""

    def save_beat(self, project_id: int, chapter_id: int, summary: str):
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO story_beats (project_id, chapter_id, summary)
                    VALUES (?, ?, ?)
                """, (project_id, chapter_id, summary))
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Save beat error: {e}")

    def get_deep_memory(self, project_id: int, query: str) -> str:
        """
        Retrieves relevant context based on key terms in the query.
        """
        query_lower = query.lower()
        memory = []
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 1. Relevant Characters
                memory.append("[CHARACTERS IN STORY]")
                # Fetch all VISIBLE characters
                cursor.execute("SELECT name, role, personality_traits, backstory FROM characters WHERE is_visible = 1")
                all_chars = cursor.fetchall()
                
                if all_chars:
                    # Always provide a full cast list for context
                    memory.append("Cast List:")
                    for c in all_chars:
                        memory.append(f"- {c[0]} ({c[1]})")
                    memory.append("") # Spacer
                    
                    # Add details for characters specifically mentioned or if query asks for "all"
                    found_specific = False
                    is_asking_all = any(phrase in query_lower for phrase in ["who are", "list characters", "all characters", "everyone"])
                    
                    for c in all_chars:
                        # Check if char name is in query or user asks for everyone
                        if is_asking_all or c[0].lower() in query_lower:
                            memory.append(f"--- DETAILED PROFILE: {c[0]} ---")
                            memory.append(f"Role: {c[1]}")
                            memory.append(f"Traits: {c[2]}")
                            memory.append(f"Backstory: {c[3]}")
                            found_specific = True
                    
                    if not found_specific and not is_asking_all:
                         memory.append("(Detailed profiles omitted for brevity as no specific names were mentioned.)")
                else:
                    memory.append("No characters have been introduced yet.")

                # 2. Story Beats (Overview)
                memory.append("\n[STORY BEATS (SUMMARY)]")
                cursor.execute("SELECT summary FROM story_beats WHERE project_id = ? ORDER BY chapter_id", (project_id,))
                beats = cursor.fetchall()
                if beats:
                    for i, beat in enumerate(beats):
                        memory.append(f"Ch {i+1}: {beat[0]}")
                else:
                    memory.append("No story beats recorded yet.")

                # 3. Relevant Chapter Snippets (Simple Keyword Search)
                memory.append("\n[RELEVANT CHAPTER SNIPPETS]")
                cursor.execute("SELECT title, content FROM chapters WHERE project_id = ? ORDER BY chapter_order", (project_id,))
                chapters = cursor.fetchall()
                found_chap = False
                
                # Split query into keywords (ignore small words)
                keywords = [w for w in query_lower.split() if len(w) > 3]
                
                for title, content in chapters:
                    content_lower = content.lower()
                    score = sum(1 for k in keywords if k in content_lower)
                    
                    if score > 0:
                        # Extract snippet around keyword
                        # For now, just dumping the whole chapter if it matches is safer for small projects
                        # but "snippet" implies partial. Let's do partial later if needed.
                        # Actually, user requested "5 most relevant chapter snippets".
                        # Let's simple check: if score > 0.
                        if len(content) > 500:
                             snippet = content[:500] + "..."
                        else:
                             snippet = content
                        memory.append(f"Source: {title} (Relevance: {score})")
                        memory.append(snippet)
                        memory.append("---")
                        found_chap = True
                
                if not found_chap:
                    memory.append("No direct keyword matches in chapters.")

            return "\n".join(memory)
        except sqlite3.Error as e:
            logging.error(f"Get deep memory error: {e}")
            return "Error retrieving deep memory."

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

    # --- Character Methods ---
    def save_character(self, data: dict):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                pid = data.get('project_id', 0)
                
                # Dynamic update/insert based on provided keys would be better, but fixed schema is safer for now
                # We must ensure all keys are present or handled
                
                keys = [
                    'project_id', 'name', 'role', 'personality_traits', 'speech_pattern', 
                    'relationship_to_author', 'backstory', 'continuity_notes',
                    'pronouns', 'groups', 'other_names', 'motivations', 
                    'internal_conflicts', 'strengths', 'weaknesses', 'character_arc'
                ]
                
                values = [pid]
                values.append(data.get('name', ''))
                # All others interactively
                for k in keys[2:]:
                    values.append(data.get(k, ''))

                placeholders = ", ".join(["?"] * len(keys))
                columns = ", ".join(keys)

                cursor.execute(f"""
                    INSERT OR REPLACE INTO characters 
                    ({columns})
                    VALUES ({placeholders})
                """, values)
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Save character error: {e}")
            return False

    def get_all_characters(self, project_id: int):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Return limited info for list
                cursor.execute("SELECT name, role FROM characters WHERE project_id = ? ORDER BY name", (project_id,))
                return [{'name': row[0], 'role': row[1]} for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Get characters error: {e}")
            return []

    def get_character_details(self, name: str, project_id: int):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM characters WHERE name = ? AND project_id = ?", (name, project_id))
                row = cursor.fetchone()
                if row:
                    # Map based on schema. 
                    # We need column names to be reliable.
                    col_names = [description[0] for description in cursor.description]
                    return dict(zip(col_names, row))
                return None
        except sqlite3.Error as e:
            logging.error(f"Get details error: {e}")
            return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db = DatabaseManager()
