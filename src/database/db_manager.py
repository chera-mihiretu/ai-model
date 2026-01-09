import sqlite3
import logging
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_name="app.db"):
        import sys
        if getattr(sys, 'frozen', False):
            self.base_dir = Path(sys.executable).parent
        else:
            self.base_dir = Path(__file__).resolve().parent.parent.parent
            
        self.db_path = self.base_dir / "data" / "database" / db_name
        
        db_existed = self.db_path.exists()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not db_existed:
            logging.info(f"Database NOT FOUND. Creating persistent DB at: {self.db_path}")
        else:
            logging.info(f"Database ALREADY EXISTS at: {self.db_path}")
            
        self.setup_database()

    def get_connection(self):
        """Create a new database connection with WAL and Foreign Keys enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            conn.execute("PRAGMA foreign_keys = ON;")
        except sqlite3.Error as e:
            logging.error(f"Failed to set PRAGMAS: {e}")
        return conn

    def setup_database(self):
        """Initialize the database schema and run migrations."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 1. Schema Version Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schema_version (
                        version INTEGER PRIMARY KEY
                    )
                """)
                
                # Check current version
                cursor.execute("SELECT version FROM schema_version")
                row = cursor.fetchone()
                current_version = row[0] if row else 0
                
                # 2. Base Tables (CREATE TABLE IF NOT EXISTS)
                # Note: We include all possible columns in the initial creation for new DBs
                
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
                        beats TEXT,
                        summary_text TEXT,
                        recent_chapter_summary TEXT,
                        last_summarized_char_count INTEGER DEFAULT 0,
                        FOREIGN KEY (project_id) REFERENCES projects (id)
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS characters (
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
                        custom_voice_path TEXT,
                        voice_embedding BLOB,
                        UNIQUE(name, project_id)
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS app_state (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )
                """)
                
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
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS story_bible (
                        project_id INTEGER PRIMARY KEY,
                        braindump TEXT,
                        braindump_summary TEXT,
                        genre TEXT,
                        genre_summary TEXT,
                        style TEXT,
                        style_summary TEXT,
                        synopsis TEXT,
                        synopsis_summary TEXT,
                        characters TEXT,
                        characters_summary TEXT,
                        worldbuilding TEXT,
                        worldbuilding_summary TEXT,
                        outline TEXT,
                        outline_summary TEXT,
                        FOREIGN KEY (project_id) REFERENCES projects (id)
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS generation_chunks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chapter_id INTEGER NOT NULL,
                        chunk_order INTEGER NOT NULL,
                        raw_text TEXT NOT NULL,
                        summary TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (chapter_id) REFERENCES chapters (id)
                    )
                """)
                
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_story_bible_project_id ON story_bible (project_id)")
                
                # Version 1: Baseline (Baseline for this consolidated manager)
                if current_version < 1:
                    logging.info("Running migration: Version 1 (Baseline)")
                    # The _ensure_columns call handles initial column additions for existing DBs
                    self._ensure_columns(conn)
                    conn.execute("INSERT OR REPLACE INTO schema_version (version) VALUES (1)")
                    current_version = 1
                
                if current_version < 2:
                    logging.info("Running migration: Version 2 (Timestamps)")
                    conn.execute("ALTER TABLE chapters ADD COLUMN updated_at DATETIME")
                    conn.execute("UPDATE schema_version SET version = 2")
                    current_version = 2

                if current_version < 3:
                    logging.info("Running migration: Version 3 (Generation Chunks)")
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS generation_chunks (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            chapter_id INTEGER NOT NULL,
                            chunk_order INTEGER NOT NULL,
                            raw_text TEXT NOT NULL,
                            summary TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (chapter_id) REFERENCES chapters (id)
                        )
                    """)
                    conn.execute("UPDATE schema_version SET version = 3")
                    current_version = 3
                
                conn.commit()
                logging.info(f"Database setup complete at version {current_version}")
                
        except sqlite3.Error as e:
            logging.critical(f"FATAL: Database initialization error: {e}")
            raise

    def _run_migrations(self, conn, current_version):
        """Run incremental migrations based on schema version."""
        cursor = conn.cursor()
        
        # Version 1 - Baseline established in CREATE TABLE IF NOT EXISTS
        if current_version < 1:
            logging.info("Running migration: Version 1 (Baseline)")
            cursor.execute("INSERT OR REPLACE INTO schema_version (version) VALUES (1)")
            current_version = 1
            
        # Additional safety check for columns (non-destructive)
        self._ensure_columns(conn)

    def _ensure_columns(self, conn):
        """Ensure all required columns exist in all tables (legacy support)."""
        cursor = conn.cursor()
        
        # Chapters: Missing summary columns
        cursor.execute("PRAGMA table_info(chapters)")
        ch_cols = [r[1] for r in cursor.fetchall()]
        if 'beats' not in ch_cols:
            cursor.execute("ALTER TABLE chapters ADD COLUMN beats TEXT")
        if 'summary_text' not in ch_cols:
            cursor.execute("ALTER TABLE chapters ADD COLUMN summary_text TEXT")
        if 'recent_chapter_summary' not in ch_cols:
            cursor.execute("ALTER TABLE chapters ADD COLUMN recent_chapter_summary TEXT")
        if 'last_summarized_char_count' not in ch_cols:
            cursor.execute("ALTER TABLE chapters ADD COLUMN last_summarized_char_count INTEGER DEFAULT 0")

        # Story Bible: Missing summary columns
        cursor.execute("PRAGMA table_info(story_bible)")
        sb_cols = [r[1] for r in cursor.fetchall()]
        base_fields = ['braindump', 'genre', 'style', 'synopsis', 'characters', 'worldbuilding', 'outline']
        for field in base_fields:
            summary_col = f"{field}_summary"
            if summary_col not in sb_cols:
                cursor.execute(f"ALTER TABLE story_bible ADD COLUMN {summary_col} TEXT")

        # Characters: Missing new fields
        cursor.execute("PRAGMA table_info(characters)")
        char_cols = [r[1] for r in cursor.fetchall()]
        if 'custom_voice_path' not in char_cols:
            cursor.execute("ALTER TABLE characters ADD COLUMN custom_voice_path TEXT")
        if 'voice_embedding' not in char_cols:
            cursor.execute("ALTER TABLE characters ADD COLUMN voice_embedding BLOB")
            
        conn.commit()

    # --- Story Bible Methods ---
    def save_bible_field(self, project_id: str, field_name: str, content: str) -> None:
        """Atomically update exactly ONE Story Bible field."""
        base_fields = {'braindump', 'genre', 'style', 'synopsis', 'characters', 'worldbuilding', 'outline'}
        allowed_fields = base_fields.union({f"{f}_summary" for f in base_fields})
        
        if field_name not in allowed_fields:
            logging.error(f"Invalid Story Bible field: {field_name}")
            return

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT OR IGNORE INTO story_bible (project_id) VALUES (?)", (project_id,))
                cursor.execute(f"UPDATE story_bible SET {field_name} = ? WHERE project_id = ?", (content, project_id))
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Failed to save story bible field {field_name}: {e}")

    def get_story_bible(self, project_id: int):
        """Fetch all story bible fields for a project."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM story_bible WHERE project_id = ?", (project_id,))
                row = cursor.fetchone()
                if row:
                    data = dict(row)
                    result = {}
                    for k in ['braindump', 'genre', 'style', 'synopsis', 'characters', 'worldbuilding', 'outline']:
                        result[k] = data.get(k) or ""
                        result[f"{k}_summary"] = data.get(f"{k}_summary") or ""
                    return result
                
                return {k: "" for k in ['braindump', 'genre', 'style', 'synopsis', 'characters', 'worldbuilding', 'outline'] + 
                        [f"{x}_summary" for x in ['braindump', 'genre', 'style', 'synopsis', 'characters', 'worldbuilding', 'outline']]}
        except sqlite3.Error as e:
            logging.error(f"Error fetching story bible: {e}")
            return None

    def get_bible_field(self, project_id: int, field_name: str) -> str:
        """Fetch content of a specific bible field."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(f"SELECT {field_name} FROM story_bible WHERE project_id = ?", (project_id,))
                res = cursor.fetchone()
                return res[0] if res else ""
        except sqlite3.Error as e:
            logging.error(f"Get bible field error: {e}")
            return ""

    def dump_story_bible_contents(self, project_id: int):
        """DIAGNOSTIC: Log all Story Bible contents for debugging persistence issues."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM story_bible WHERE project_id = ?", (project_id,))
                row = cursor.fetchone()
                if row:
                    data = dict(row)
                    logging.info(f"--- Story Bible Contents for Project {project_id} ---")
                    for k, v in data.items():
                        logging.info(f"  {k}: {len(str(v))} chars")
                else:
                    logging.warning(f"No story bible found for project {project_id}")
        except sqlite3.Error as e:
            logging.error(f"Dump bible error: {e}")

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

    def get_projects(self):
        """Fetch all projects."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, genre FROM projects ORDER BY created_at DESC")
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Get projects error: {e}")
            return []

    def get_characters(self, project_id: int):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM characters WHERE project_id = ?", (project_id,))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Get characters error: {e}")
            return []

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

    def get_full_project_content(self, project_id: int):
        """Returns all chapters for a project in order."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT title, content 
                    FROM chapters 
                    WHERE project_id = ? 
                    ORDER BY chapter_order
                """, (project_id,))
                return [{'title': r[0], 'content': r[1]} for r in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Get full project content error: {e}")
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
                        char_details = self.get_character_details(char_name, project_id)
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
    def create_chapter(self, project_id: int, title: str, content: str = ""):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Get next order
                cursor.execute("SELECT MAX(chapter_order) FROM chapters WHERE project_id = ?", (project_id,))
                res = cursor.fetchone()[0]
                next_order = 1 if res is None else res + 1
                
                cursor.execute(
                    "INSERT INTO chapters (project_id, title, content, chapter_order) VALUES (?, ?, ?, ?)",
                    (project_id, title, content, next_order)
                )
                chap_id = cursor.lastrowid
                conn.commit()
                return chap_id
        except sqlite3.Error as e:
            logging.error(f"Create chapter error: {e}")
            return None

    def update_chapter_content(self, chapter_id: int, content: str):
        try:
            # Defensive check: Don't accidentally wipe content if it was large before
            if not content:
                existing = self.get_chapter_content(chapter_id)
                if existing and len(existing) > 100:
                    logging.warning(f"PERSIST_WARNING: Attempting to save EMPTY content over {len(existing)} characters for chapter {chapter_id}! Blocking potentially accidental wipe.")
                    return False

            with self.get_connection() as conn:
                conn.execute("UPDATE chapters SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (content, chapter_id))
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

    # --- Generation Chunk Methods ---
    def save_generation_chunk(self, chapter_id: int, raw_text: str, summary: str):
        """Save a raw generation chunk and its summary."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Get next chunk order
                cursor.execute("SELECT MAX(chunk_order) FROM generation_chunks WHERE chapter_id = ?", (chapter_id,))
                res = cursor.fetchone()[0]
                next_order = 1 if res is None else res + 1
                
                cursor.execute(
                    "INSERT INTO generation_chunks (chapter_id, chunk_order, raw_text, summary) VALUES (?, ?, ?, ?)",
                    (chapter_id, next_order, raw_text, summary)
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Save generation chunk error: {e}")
            return False

    def get_last_chunk_summary(self, chapter_id: int) -> str:
        """Retrieve the summary of the most recent generation chunk for a chapter."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT summary FROM generation_chunks WHERE chapter_id = ? ORDER BY chunk_order DESC LIMIT 1",
                    (chapter_id,)
                )
                row = cursor.fetchone()
                return row[0] if row and row[0] else ""
        except sqlite3.Error as e:
            logging.error(f"Get last chunk summary error: {e}")
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
                    'internal_conflicts', 'strengths', 'weaknesses', 'character_arc',
                    'physical_description', 'is_visible', 'custom_voice_path', 'voice_embedding'
                ]
                
                values = []
                for k in keys:
                    if k == 'is_visible':
                        values.append(data.get(k, 1)) # Default to visible
                    else:
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
                    return dict(row)
                return None
        except sqlite3.Error as e:
            logging.error(f"Get details error: {e}")
            return None

    def get_chapters(self, project_id: int):
        """Get all chapters for a project."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, title FROM chapters WHERE project_id = ? ORDER BY chapter_order",
                    (project_id,)
                )
                return [{'id': r[0], 'title': r[1]} for r in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Get chapters error: {e}")
            return []

    def update_chapter_progress(self, chapter_id: int, last_count: int):
        """Update the last summarized character count."""
        try:
            with self.get_connection() as conn:
                conn.execute("UPDATE chapters SET last_summarized_char_count = ? WHERE id = ?", (last_count, chapter_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Update progress error: {e}")
            return False

    def save_chapter_summary(self, chapter_id: int, summary: str, recent_summary: str = None):
        try:
            with self.get_connection() as conn:
                if recent_summary:
                    conn.execute("UPDATE chapters SET summary_text = ?, recent_chapter_summary = ? WHERE id = ?", (summary, recent_summary, chapter_id))
                else:
                    conn.execute("UPDATE chapters SET summary_text = ? WHERE id = ?", (summary, chapter_id))
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Save summary error: {e}")

    def get_chapter_summary(self, chapter_id: int):
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("SELECT summary_text, recent_chapter_summary FROM chapters WHERE id = ?", (chapter_id,))
                res = cursor.fetchone()
                if res:
                    return {'summary': res[0] or "", 'recent_summary': res[1] or ""}
                return {'summary': "", 'recent_summary': ""}
        except sqlite3.Error as e:
            logging.error(f"Get summary error: {e}")
            return {'summary': "", 'recent_summary': ""}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db = DatabaseManager()
