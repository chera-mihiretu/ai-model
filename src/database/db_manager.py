import sqlite3
import logging
import os
import json
import uuid
from pathlib import Path

def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())

class DatabaseManager:
    def __init__(self, db_name="app.db"):
        import sys
        
        # Check for environment variable path first (set by Electron)
        data_path = os.environ.get('EXELSIAS_DATA_PATH')
        
        if data_path:
            # Production: use path provided by Electron
            self.base_dir = Path(data_path).parent
            self.db_path = Path(data_path) / "database" / db_name
        elif getattr(sys, 'frozen', False):
            # Frozen (PyInstaller) without Electron env var
            self.base_dir = Path(sys.executable).parent
            self.db_path = self.base_dir / "data" / "database" / db_name
        else:
            # Development mode
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
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        genre TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chapters (
                        id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
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
                        id TEXT PRIMARY KEY,
                        project_id TEXT DEFAULT '',
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
                        id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        chapter_id TEXT NOT NULL,
                        summary TEXT,
                        FOREIGN KEY (project_id) REFERENCES projects (id),
                        FOREIGN KEY (chapter_id) REFERENCES chapters (id)
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS story_bible (
                        project_id TEXT PRIMARY KEY,
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
                        id TEXT PRIMARY KEY,
                        chapter_id TEXT NOT NULL,
                        chunk_order INTEGER NOT NULL,
                        raw_text TEXT NOT NULL,
                        summary TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (chapter_id) REFERENCES chapters (id)
                    )
                """)
                
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_story_bible_project_id ON story_bible (project_id)")
                
                # Project Summaries - tiered pre-computed summaries for AI context
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS project_summaries (
                        project_id    TEXT NOT NULL,
                        content_type  TEXT NOT NULL,
                        token_tier    INTEGER NOT NULL,
                        summary_text  TEXT DEFAULT '',
                        source_version INTEGER DEFAULT 0,
                        updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (project_id, content_type, token_tier)
                    )
                """)
                
                # Content Versions - tracks staleness of each content type
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS content_versions (
                        project_id   TEXT NOT NULL,
                        content_type TEXT NOT NULL,
                        version      INTEGER DEFAULT 0,
                        PRIMARY KEY (project_id, content_type)
                    )
                """)
                
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
                            id TEXT PRIMARY KEY,
                            chapter_id TEXT NOT NULL,
                            chunk_order INTEGER NOT NULL,
                            raw_text TEXT NOT NULL,
                            summary TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (chapter_id) REFERENCES chapters (id)
                        )
                    """)
                    conn.execute("UPDATE schema_version SET version = 3")
                    current_version = 3
                
                # Version 4: Pseudorite Feature Alignment - World Elements, Series, Scenes
                if current_version < 4:
                    logging.info("Running migration: Version 4 (Pseudorite Features)")
                    
                    # World Building Elements
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS world_elements (
                            id TEXT PRIMARY KEY,
                            project_id TEXT,
                            series_id TEXT,
                            name TEXT NOT NULL,
                            element_type TEXT DEFAULT 'other',
                            description TEXT,
                            sensory_details TEXT,
                            significance TEXT,
                            custom_traits TEXT,
                            source_project_id TEXT,
                            is_visible INTEGER DEFAULT 1,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (project_id) REFERENCES projects (id),
                            FOREIGN KEY (series_id) REFERENCES series (id)
                        )
                    """)
                    
                    # Series Folders
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS series (
                            id TEXT PRIMARY KEY,
                            name TEXT NOT NULL,
                            description TEXT,
                            timeline_data TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Series-Project linking
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS series_projects (
                            series_id TEXT NOT NULL,
                            project_id TEXT NOT NULL,
                            book_order INTEGER DEFAULT 0,
                            PRIMARY KEY (series_id, project_id),
                            FOREIGN KEY (series_id) REFERENCES series (id),
                            FOREIGN KEY (project_id) REFERENCES projects (id)
                        )
                    """)
                    
                    # Character Versions
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS character_versions (
                            id TEXT PRIMARY KEY,
                            character_id TEXT NOT NULL,
                            project_id TEXT NOT NULL,
                            version_notes TEXT,
                            is_canonical INTEGER DEFAULT 0,
                            trait_overrides TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (character_id) REFERENCES characters (id),
                            FOREIGN KEY (project_id) REFERENCES projects (id)
                        )
                    """)
                    
                    # Scenes (for draft tool)
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS scenes (
                            id TEXT PRIMARY KEY,
                            chapter_id TEXT NOT NULL,
                            scene_order INTEGER DEFAULT 0,
                            title TEXT,
                            summary TEXT,
                            content TEXT,
                            pov_character TEXT,
                            location TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (chapter_id) REFERENCES chapters (id)
                        )
                    """)
                    
                    # Chapter-Outline Linking
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS chapter_outline_links (
                            id TEXT PRIMARY KEY,
                            chapter_id TEXT NOT NULL,
                            outline_section TEXT,
                            outline_order INTEGER DEFAULT 0,
                            FOREIGN KEY (chapter_id) REFERENCES chapters (id)
                        )
                    """)
                    
                    # Create indexes
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_world_elements_project ON world_elements (project_id)")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_world_elements_series ON world_elements (series_id)")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_world_elements_type ON world_elements (element_type)")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_scenes_chapter ON scenes (chapter_id)")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_character_versions_char ON character_versions (character_id)")
                    
                    conn.execute("UPDATE schema_version SET version = 4")
                    current_version = 4
                
                # Version 5: Tiered Summarization System
                if current_version < 5:
                    logging.info("Running migration: Version 5 (Tiered Summarization)")
                    
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS project_summaries (
                            project_id    TEXT NOT NULL,
                            content_type  TEXT NOT NULL,
                            token_tier    INTEGER NOT NULL,
                            summary_text  TEXT DEFAULT '',
                            source_version INTEGER DEFAULT 0,
                            updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
                            PRIMARY KEY (project_id, content_type, token_tier)
                        )
                    """)
                    
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS content_versions (
                            project_id   TEXT NOT NULL,
                            content_type TEXT NOT NULL,
                            version      INTEGER DEFAULT 0,
                            PRIMARY KEY (project_id, content_type)
                        )
                    """)
                    
                    conn.execute("UPDATE schema_version SET version = 5")
                    current_version = 5
                
                # Version 6: Recycle Bin
                if current_version < 6:
                    logging.info("Running migration: Version 6 (Recycle Bin)")
                    
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS recycle_bin (
                            id TEXT PRIMARY KEY,
                            item_type TEXT NOT NULL,
                            item_id TEXT NOT NULL,
                            item_data TEXT NOT NULL,
                            deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_recycle_bin_type ON recycle_bin (item_type)")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_recycle_bin_deleted ON recycle_bin (deleted_at)")
                    
                    conn.execute("UPDATE schema_version SET version = 6")
                    current_version = 6
                
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

    # --- Content Version & Summary Methods ---
    
    def increment_content_version(self, project_id: str, content_type: str):
        """Bump the version counter for a content type, marking summaries as stale."""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO content_versions (project_id, content_type, version)
                    VALUES (?, ?, 1)
                    ON CONFLICT(project_id, content_type)
                    DO UPDATE SET version = version + 1
                """, (project_id, content_type))
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Increment content version error: {e}")
    
    def get_content_version(self, project_id: str, content_type: str) -> int:
        """Get the current version number for a content type."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT version FROM content_versions WHERE project_id = ? AND content_type = ?",
                    (project_id, content_type)
                )
                row = cursor.fetchone()
                return row[0] if row else 0
        except sqlite3.Error as e:
            logging.error(f"Get content version error: {e}")
            return 0
    
    def get_summary(self, project_id: str, content_type: str, token_tier: int) -> dict:
        """Get a pre-computed summary for a content type and tier."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT summary_text, source_version FROM project_summaries WHERE project_id = ? AND content_type = ? AND token_tier = ?",
                    (project_id, content_type, token_tier)
                )
                row = cursor.fetchone()
                if row:
                    return {'summary_text': row[0], 'source_version': row[1]}
                return {'summary_text': '', 'source_version': 0}
        except sqlite3.Error as e:
            logging.error(f"Get summary error: {e}")
            return {'summary_text': '', 'source_version': 0}
    
    def save_summary(self, project_id: str, content_type: str, token_tier: int, summary_text: str, source_version: int):
        """Store a pre-computed summary for a content type and tier."""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO project_summaries (project_id, content_type, token_tier, summary_text, source_version, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(project_id, content_type, token_tier)
                    DO UPDATE SET summary_text = ?, source_version = ?, updated_at = CURRENT_TIMESTAMP
                """, (project_id, content_type, token_tier, summary_text, source_version,
                      summary_text, source_version))
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Save summary error: {e}")
    
    def get_raw_content_for_type(self, project_id: str, content_type: str) -> str:
        """Get the full raw content for a content type to be summarized."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if content_type == 'characters':
                    cursor.execute("""
                        SELECT name, role, pronouns, personality_traits, physical_description,
                               backstory, motivations, internal_conflicts, strengths, weaknesses,
                               speech_pattern, character_arc
                        FROM characters
                        WHERE project_id = ? AND is_visible = 1
                    """, (project_id,))
                    rows = cursor.fetchall()
                    if not rows:
                        return ''
                    parts = []
                    for c in rows:
                        name, role, pronouns, traits, physical, backstory, motivations, conflicts, strengths, weaknesses, speech, arc = c
                        lines = [f"CHARACTER: {name}"]
                        if role: lines.append(f"Role: {role}")
                        if pronouns: lines.append(f"Pronouns: {pronouns}")
                        if traits: lines.append(f"Personality: {traits}")
                        if physical: lines.append(f"Appearance: {physical}")
                        if backstory: lines.append(f"Backstory: {backstory}")
                        if motivations: lines.append(f"Motivations: {motivations}")
                        if conflicts: lines.append(f"Internal Conflicts: {conflicts}")
                        if strengths: lines.append(f"Strengths: {strengths}")
                        if weaknesses: lines.append(f"Weaknesses: {weaknesses}")
                        if speech: lines.append(f"Speech: {speech}")
                        if arc: lines.append(f"Arc: {arc}")
                        parts.append("\n".join(lines))
                    return "\n\n".join(parts)
                
                elif content_type == 'world_elements':
                    cursor.execute("""
                        SELECT name, element_type, description, sensory_details, significance
                        FROM world_elements
                        WHERE project_id = ? AND is_visible = 1
                    """, (project_id,))
                    rows = cursor.fetchall()
                    if not rows:
                        return ''
                    parts = []
                    for name, elem_type, description, sensory, significance in rows:
                        lines = [f"{(elem_type or 'element').upper()}: {name}"]
                        if description: lines.append(f"Description: {description}")
                        if sensory: lines.append(f"Sensory: {sensory}")
                        if significance: lines.append(f"Significance: {significance}")
                        parts.append("\n".join(lines))
                    return "\n\n".join(parts)
                
                elif content_type == 'synopsis':
                    cursor.execute("SELECT synopsis FROM story_bible WHERE project_id = ?", (project_id,))
                    row = cursor.fetchone()
                    return (row[0] or '') if row else ''
                
                elif content_type == 'outline':
                    cursor.execute("SELECT outline FROM story_bible WHERE project_id = ?", (project_id,))
                    row = cursor.fetchone()
                    if not row or not row[0]:
                        return ''
                    outline_data = row[0]
                    try:
                        import json
                        chapters = json.loads(outline_data)
                        if isinstance(chapters, list):
                            parts = []
                            for ch in chapters:
                                ch_num = ch.get('chapter_number', '?')
                                ch_title = ch.get('title', 'Untitled')
                                ch_summary = ch.get('summary', '')
                                lines = [f"Chapter {ch_num}: {ch_title}"]
                                if ch_summary: lines.append(ch_summary)
                                parts.append("\n".join(lines))
                            return "\n\n".join(parts)
                    except Exception:
                        pass
                    return outline_data
                
                elif content_type == 'chapters':
                    cursor.execute("""
                        SELECT title, content FROM chapters
                        WHERE project_id = ? ORDER BY chapter_order
                    """, (project_id,))
                    rows = cursor.fetchall()
                    if not rows:
                        return ''
                    parts = []
                    for title, content in rows:
                        if content and content.strip():
                            # Truncate each chapter to prevent extremely long inputs
                            snippet = content[:2000] if len(content) > 2000 else content
                            parts.append(f"CHAPTER: {title}\n{snippet}")
                    return "\n\n".join(parts)
                
                return ''
        except sqlite3.Error as e:
            logging.error(f"Get raw content for type error: {e}")
            return ''
    
    def get_context_health(self, project_id: str) -> dict:
        """
        Check the health/freshness of all summarized context for a project.
        Returns a dict with status for each content type: 'fresh', 'stale', or 'missing'.
        This helps the UI show whether the AI has up-to-date context.
        """
        content_types = ['characters', 'world_elements', 'synopsis', 'outline', 'chapters']
        health = {}
        
        for ctype in content_types:
            current_version = self.get_content_version(project_id, ctype)
            summary_data = self.get_summary(project_id, ctype, 1000)
            summary_text = summary_data.get('summary_text', '')
            summarized_version = summary_data.get('source_version', 0)
            
            # Check if there's any raw content
            raw_content = self.get_raw_content_for_type(project_id, ctype)
            has_content = bool(raw_content and raw_content.strip())
            
            if not has_content:
                health[ctype] = 'empty'  # No content to summarize
            elif not summary_text.strip():
                health[ctype] = 'missing'  # Content exists but no summary
            elif summarized_version < current_version:
                health[ctype] = 'stale'  # Summary exists but is outdated
            else:
                health[ctype] = 'fresh'  # Summary is up-to-date
        
        # Overall status
        statuses = [v for v in health.values() if v != 'empty']
        if not statuses:
            health['overall'] = 'empty'
        elif all(s == 'fresh' for s in statuses):
            health['overall'] = 'fresh'
        elif any(s == 'missing' for s in statuses):
            health['overall'] = 'missing'
        else:
            health['overall'] = 'stale'
        
        return health

    def get_summarized_memory(self, project_id: str, token_tier: int = 1000) -> str:
        """Get pre-computed summaries for all content types, assembled into a context string."""
        memory = []
        for content_type in ['characters', 'world_elements', 'synopsis', 'outline', 'chapters']:
            summary_data = self.get_summary(project_id, content_type, token_tier)
            summary_text = summary_data.get('summary_text', '')
            if summary_text and summary_text.strip():
                label = content_type.upper().replace('_', ' ')
                memory.append(f"[{label}]\n{summary_text}\n")
        
        if not memory:
            # Fallback: if no summaries exist yet, return a trimmed version of deep memory
            logging.info(f"No summaries found for project {project_id}, falling back to raw content")
            return self._get_fallback_memory(project_id)
        
        return "\n".join(memory)
    
    def _get_fallback_memory(self, project_id: str) -> str:
        """Lightweight fallback when no summaries exist yet. Returns truncated raw content."""
        memory = []
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Characters (brief)
                cursor.execute("""
                    SELECT name, role, personality_traits FROM characters
                    WHERE project_id = ? AND is_visible = 1
                """, (project_id,))
                chars = cursor.fetchall()
                if chars:
                    memory.append("[CHARACTERS]")
                    for name, role, traits in chars:
                        line = f"- {name}"
                        if role: line += f" ({role})"
                        if traits: line += f": {traits[:100]}"
                        memory.append(line)
                    memory.append("")
                
                # Synopsis (brief)
                cursor.execute("SELECT synopsis FROM story_bible WHERE project_id = ?", (project_id,))
                row = cursor.fetchone()
                if row and row[0]:
                    memory.append("[SYNOPSIS]")
                    memory.append(row[0][:500] + ("..." if len(row[0]) > 500 else ""))
                    memory.append("")
                
                # Outline (just titles)
                cursor.execute("SELECT outline FROM story_bible WHERE project_id = ?", (project_id,))
                row = cursor.fetchone()
                if row and row[0]:
                    try:
                        import json
                        chapters = json.loads(row[0])
                        if isinstance(chapters, list) and chapters:
                            memory.append("[OUTLINE]")
                            for ch in chapters[:15]:
                                memory.append(f"- Ch {ch.get('chapter_number', '?')}: {ch.get('title', 'Untitled')}")
                            memory.append("")
                    except Exception:
                        pass
                
            return "\n".join(memory)
        except sqlite3.Error as e:
            logging.error(f"Fallback memory error: {e}")
            return ""
    
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
            
            # Mark the relevant summary as stale (only for base fields, not summary fields)
            if field_name in base_fields and project_id:
                if field_name == 'synopsis':
                    self.increment_content_version(str(project_id), 'synopsis')
                elif field_name == 'outline':
                    self.increment_content_version(str(project_id), 'outline')
        except sqlite3.Error as e:
            logging.error(f"Failed to save story bible field {field_name}: {e}")

    def get_story_bible(self, project_id: str):
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

    def get_bible_field(self, project_id: str, field_name: str) -> str:
        """Fetch content of a specific bible field."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(f"SELECT {field_name} FROM story_bible WHERE project_id = ?", (project_id,))
                res = cursor.fetchone()
                return res[0] if res else ""
        except sqlite3.Error as e:
            logging.error(f"Get bible field error: {e}")
            return ""

    def dump_story_bible_contents(self, project_id: str):
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
                project_id = generate_uuid()
                cursor.execute("INSERT INTO projects (id, name, genre) VALUES (?, ?, ?)", (project_id, name, genre))
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

    def get_characters(self, project_id: str):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM characters WHERE project_id = ?", (project_id,))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Get characters error: {e}")
            return []

    def get_project_settings(self, project_id: str):
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

    def rename_project(self, project_id: str, new_name: str):
        """Rename a project."""
        try:
            with self.get_connection() as conn:
                conn.execute("UPDATE projects SET name = ? WHERE id = ?", (new_name, project_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Rename project error: {e}")
            return False

    def delete_project(self, project_id: str):
        """Delete a project and all its related data (full cascade)."""
        try:
            with self.get_connection() as conn:
                # Get all chapter IDs for this project (needed for scene/chunk deletion)
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM chapters WHERE project_id = ?", (project_id,))
                chapter_ids = [row[0] for row in cursor.fetchall()]
                
                # Delete scenes for all chapters in this project
                if chapter_ids:
                    placeholders = ','.join('?' * len(chapter_ids))
                    conn.execute(f"DELETE FROM scenes WHERE chapter_id IN ({placeholders})", chapter_ids)
                    # Delete generation chunks for all chapters
                    conn.execute(f"DELETE FROM generation_chunks WHERE chapter_id IN ({placeholders})", chapter_ids)
                    # Delete chapter outline links
                    conn.execute(f"DELETE FROM chapter_outline_links WHERE chapter_id IN ({placeholders})", chapter_ids)
                
                # Delete story beats (references project_id and chapter_id)
                conn.execute("DELETE FROM story_beats WHERE project_id = ?", (project_id,))
                
                # Delete all chapters
                conn.execute("DELETE FROM chapters WHERE project_id = ?", (project_id,))
                
                # Delete characters for this project
                conn.execute("DELETE FROM characters WHERE project_id = ?", (project_id,))
                
                # Delete character versions for this project
                conn.execute("DELETE FROM character_versions WHERE project_id = ?", (project_id,))
                
                # Delete world elements for this project
                conn.execute("DELETE FROM world_elements WHERE project_id = ?", (project_id,))
                
                # Delete story bible data
                conn.execute("DELETE FROM story_bible WHERE project_id = ?", (project_id,))
                
                # Delete project summaries
                conn.execute("DELETE FROM project_summaries WHERE project_id = ?", (project_id,))
                
                # Delete content versions
                conn.execute("DELETE FROM content_versions WHERE project_id = ?", (project_id,))
                
                # Remove from series_projects junction table
                conn.execute("DELETE FROM series_projects WHERE project_id = ?", (project_id,))
                
                # Finally delete the project itself
                conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
                
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Delete project error: {e}")
            return False

    # ==================== RECYCLE BIN METHODS ====================
    
    def get_full_project_data(self, project_id: str):
        """Get complete project data for recycle bin storage."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get project
                cursor.execute("SELECT id, name, genre, created_at FROM projects WHERE id = ?", (project_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                
                project = {
                    'id': row[0],
                    'name': row[1],
                    'genre': row[2],
                    'created_at': row[3],
                    'chapters': [],
                    'characters': [],
                    'story_bible': None,
                    'world_elements': []
                }
                
                # Get chapters
                cursor.execute("""
                    SELECT id, title, content, chapter_order, beats, summary_text, 
                           recent_chapter_summary, last_summarized_char_count 
                    FROM chapters WHERE project_id = ? ORDER BY chapter_order
                """, (project_id,))
                project['chapters'] = [
                    {
                        'id': r[0], 'title': r[1], 'content': r[2], 'chapter_order': r[3],
                        'beats': r[4], 'summary_text': r[5], 'recent_chapter_summary': r[6],
                        'last_summarized_char_count': r[7]
                    }
                    for r in cursor.fetchall()
                ]
                
                # Get characters
                cursor.execute("""
                    SELECT id, name, role, personality_traits, speech_pattern, backstory,
                           physical_description, pronouns, groups, other_names, motivations,
                           internal_conflicts, strengths, weaknesses, character_arc, is_visible
                    FROM characters WHERE project_id = ?
                """, (project_id,))
                project['characters'] = [
                    {
                        'id': r[0], 'name': r[1], 'role': r[2], 'personality_traits': r[3],
                        'speech_pattern': r[4], 'backstory': r[5], 'physical_description': r[6],
                        'pronouns': r[7], 'groups': r[8], 'other_names': r[9], 'motivations': r[10],
                        'internal_conflicts': r[11], 'strengths': r[12], 'weaknesses': r[13],
                        'character_arc': r[14], 'is_visible': r[15]
                    }
                    for r in cursor.fetchall()
                ]
                
                # Get story bible
                cursor.execute("""
                    SELECT braindump, genre, style, synopsis, worldbuilding, outline
                    FROM story_bible WHERE project_id = ?
                """, (project_id,))
                sb_row = cursor.fetchone()
                if sb_row:
                    project['story_bible'] = {
                        'braindump': sb_row[0], 'genre': sb_row[1], 'style': sb_row[2],
                        'synopsis': sb_row[3], 'worldbuilding': sb_row[4], 'outline': sb_row[5]
                    }
                
                # Get world elements
                cursor.execute("""
                    SELECT id, name, element_type, description, sensory_details, significance, is_visible
                    FROM world_elements WHERE project_id = ?
                """, (project_id,))
                project['world_elements'] = [
                    {
                        'id': r[0], 'name': r[1], 'element_type': r[2], 'description': r[3],
                        'sensory_details': r[4], 'significance': r[5], 'is_visible': r[6]
                    }
                    for r in cursor.fetchall()
                ]
                
                return project
        except sqlite3.Error as e:
            logging.error(f"Get full project data error: {e}")
            return None

    def move_to_recycle_bin(self, item_type: str, item_id: str, item_data: str):
        """Move an item to the recycle bin."""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO recycle_bin (item_type, item_id, item_data)
                    VALUES (?, ?, ?)
                """, (item_type, str(item_id), item_data))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Move to recycle bin error: {e}")
            return False

    def move_project_to_recycle_bin(self, project_id: str):
        """Soft delete a project by moving it to recycle bin."""
        try:
            # Get full project data first
            project_data = self.get_full_project_data(project_id)
            if not project_data:
                return False
            
            # Store in recycle bin
            import json
            if not self.move_to_recycle_bin('project', str(project_id), json.dumps(project_data)):
                return False
            
            # Now hard delete the project (it's backed up in recycle bin)
            return self.delete_project(project_id)
        except Exception as e:
            logging.error(f"Move project to recycle bin error: {e}")
            return False

    def get_recycle_bin_items(self):
        """Get all items in the recycle bin."""
        try:
            import json
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, item_type, item_id, item_data, deleted_at 
                    FROM recycle_bin ORDER BY deleted_at DESC
                """)
                items = []
                for row in cursor.fetchall():
                    try:
                        item_data = json.loads(row[3])
                    except json.JSONDecodeError:
                        item_data = {}
                    items.append({
                        'id': row[0],
                        'item_type': row[1],
                        'item_id': row[2],
                        'item_data': item_data,
                        'deleted_at': row[4]
                    })
                return items
        except sqlite3.Error as e:
            logging.error(f"Get recycle bin items error: {e}")
            return []

    def restore_project_from_data(self, project_data: dict):
        """Restore a project from its saved data."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Recreate project with UUID
                new_project_id = generate_uuid()
                cursor.execute("""
                    INSERT INTO projects (id, name, genre) VALUES (?, ?, ?)
                """, (new_project_id, project_data.get('name', 'Restored Project'), project_data.get('genre', '')))
                
                # Map old chapter IDs to new ones for relationship restoration
                chapter_id_map = {}
                
                # Restore chapters
                for ch in project_data.get('chapters', []):
                    new_chapter_id = generate_uuid()
                    cursor.execute("""
                        INSERT INTO chapters (id, project_id, title, content, chapter_order, beats, 
                                            summary_text, recent_chapter_summary, last_summarized_char_count)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        new_chapter_id, new_project_id, ch.get('title', 'Untitled'), ch.get('content', ''),
                        ch.get('chapter_order', 0), ch.get('beats'), ch.get('summary_text'),
                        ch.get('recent_chapter_summary'), ch.get('last_summarized_char_count', 0)
                    ))
                    chapter_id_map[ch.get('id')] = new_chapter_id
                
                # Restore characters
                for char in project_data.get('characters', []):
                    new_char_id = generate_uuid()
                    cursor.execute("""
                        INSERT INTO characters (id, project_id, name, role, personality_traits, speech_pattern,
                                              backstory, physical_description, pronouns, groups, other_names,
                                              motivations, internal_conflicts, strengths, weaknesses, 
                                              character_arc, is_visible)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        new_char_id, new_project_id, char.get('name', ''), char.get('role', ''),
                        char.get('personality_traits', ''), char.get('speech_pattern', ''),
                        char.get('backstory', ''), char.get('physical_description', ''),
                        char.get('pronouns', ''), char.get('groups', ''), char.get('other_names', ''),
                        char.get('motivations', ''), char.get('internal_conflicts', ''),
                        char.get('strengths', ''), char.get('weaknesses', ''),
                        char.get('character_arc', ''), char.get('is_visible', 1)
                    ))
                
                # Restore story bible
                sb = project_data.get('story_bible')
                if sb:
                    cursor.execute("""
                        INSERT INTO story_bible (project_id, braindump, genre, style, synopsis, worldbuilding, outline)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        new_project_id, sb.get('braindump', ''), sb.get('genre', ''),
                        sb.get('style', ''), sb.get('synopsis', ''), sb.get('worldbuilding', ''),
                        sb.get('outline', '')
                    ))
                
                # Restore world elements
                for we in project_data.get('world_elements', []):
                    new_we_id = generate_uuid()
                    cursor.execute("""
                        INSERT INTO world_elements (id, project_id, name, element_type, description,
                                                   sensory_details, significance, is_visible)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        new_we_id, new_project_id, we.get('name', ''), we.get('element_type', 'other'),
                        we.get('description', ''), we.get('sensory_details', ''),
                        we.get('significance', ''), we.get('is_visible', 1)
                    ))
                
                conn.commit()
                return new_project_id
        except sqlite3.Error as e:
            logging.error(f"Restore project from data error: {e}")
            return None

    def restore_from_recycle_bin(self, recycle_id: str):
        """Restore an item from the recycle bin."""
        try:
            import json
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get the item
                cursor.execute("""
                    SELECT item_type, item_id, item_data FROM recycle_bin WHERE id = ?
                """, (recycle_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                
                item_type, item_id, item_data_str = row
                item_data = json.loads(item_data_str)
                
                result = {'item_type': item_type, 'restored_items': []}
                
                if item_type == 'project':
                    new_id = self.restore_project_from_data(item_data)
                    if new_id:
                        result['restored_items'].append({'type': 'project', 'id': new_id, 'name': item_data.get('name')})
                
                elif item_type == 'folder':
                    # Restore folder structure and all projects inside
                    folder_data = {
                        'id': item_data.get('id'),
                        'name': item_data.get('name'),
                        'created_at': item_data.get('created_at'),
                        'updated_at': item_data.get('updated_at'),
                        'projects': []
                    }
                    
                    # Restore each project in the folder
                    for proj in item_data.get('projects', []):
                        new_id = self.restore_project_from_data(proj)
                        if new_id:
                            folder_data['projects'].append({'id': new_id, 'name': proj.get('name')})
                            result['restored_items'].append({'type': 'project', 'id': new_id, 'name': proj.get('name')})
                    
                    result['folder_data'] = folder_data
                
                elif item_type == 'series':
                    # Restore series structure and all projects inside
                    series_data = {
                        'id': item_data.get('id'),
                        'name': item_data.get('name'),
                        'created_at': item_data.get('created_at'),
                        'updated_at': item_data.get('updated_at'),
                        'projects': []
                    }
                    
                    # Restore each project in the series
                    for proj in item_data.get('projects', []):
                        new_id = self.restore_project_from_data(proj)
                        if new_id:
                            series_data['projects'].append({'id': new_id, 'name': proj.get('name')})
                            result['restored_items'].append({'type': 'project', 'id': new_id, 'name': proj.get('name')})
                    
                    result['series_data'] = series_data
                
                # Remove from recycle bin
                conn.execute("DELETE FROM recycle_bin WHERE id = ?", (recycle_id,))
                conn.commit()
                
                return result
        except Exception as e:
            logging.error(f"Restore from recycle bin error: {e}")
            return None

    def permanent_delete_from_recycle_bin(self, recycle_id: str):
        """Permanently delete an item from the recycle bin."""
        try:
            with self.get_connection() as conn:
                conn.execute("DELETE FROM recycle_bin WHERE id = ?", (recycle_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Permanent delete from recycle bin error: {e}")
            return False

    def empty_recycle_bin(self):
        """Empty the entire recycle bin."""
        try:
            with self.get_connection() as conn:
                conn.execute("DELETE FROM recycle_bin")
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Empty recycle bin error: {e}")
            return False

    # ==================== END RECYCLE BIN METHODS ====================

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

    def get_full_project_content(self, project_id: str):
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

    def get_context_window(self, project_id: str, chapter_id: str, char_limit: int = 3000):
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
                        SELECT c.id, c.summary_text FROM chapters c 
                        WHERE c.project_id = ? AND c.chapter_order = ?
                    """, (project_id, current_order - 1))
                    prev_chapter = cursor.fetchone()
                    
                    if prev_chapter:
                        # First try story_beats (for beat-by-beat mode)
                        cursor.execute("""
                            SELECT summary FROM story_beats 
                            WHERE project_id = ? AND chapter_id = ?
                            ORDER BY id DESC LIMIT 1
                        """, (project_id, prev_chapter[0]))
                        beat = cursor.fetchone()
                        if beat and beat[0]:
                            prev_summary = beat[0]
                        # Fallback to chapter summary_text (for imported chapters)
                        elif prev_chapter[1]:
                            prev_summary = prev_chapter[1]
                
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

    def fetch_omni_context(self, project_id: str, chapter_id: str, beats_list: list):
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
    def create_chapter(self, project_id: str, title: str, content: str = ""):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Get next order
                cursor.execute("SELECT MAX(chapter_order) FROM chapters WHERE project_id = ?", (project_id,))
                res = cursor.fetchone()[0]
                next_order = 1 if res is None else res + 1
                
                chapter_id = generate_uuid()
                cursor.execute(
                    "INSERT INTO chapters (id, project_id, title, content, chapter_order) VALUES (?, ?, ?, ?, ?)",
                    (chapter_id, project_id, title, content, next_order)
                )
                conn.commit()
                return chapter_id
        except sqlite3.Error as e:
            logging.error(f"Create chapter error: {e}")
            return None

    def update_chapter_content(self, chapter_id: str, content: str):
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
                # Note: We do NOT bump content version here because chapter content
                # auto-saves on every keystroke. Chapter summaries are updated lazily
                # when the AI assistant is actually queried.
                return True
        except sqlite3.Error as e:
            logging.error(f"Update chapter error: {e}")
            return False

    def rename_chapter(self, chapter_id: str, new_title: str):
        """Rename a chapter."""
        try:
            with self.get_connection() as conn:
                conn.execute("UPDATE chapters SET title = ? WHERE id = ?", (new_title, chapter_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Rename chapter error: {e}")
            return False

    def delete_chapter(self, chapter_id: str):
        """Delete a chapter."""
        try:
            with self.get_connection() as conn:
                conn.execute("DELETE FROM chapters WHERE id = ?", (chapter_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Delete chapter error: {e}")
            return False

    def move_chapter_up(self, chapter_id: str):
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

    def move_chapter_down(self, chapter_id: str):
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

    def update_chapter_beats(self, chapter_id: str, beats_text: str):
        """Save extracted or suggested beats for a chapter."""
        try:
            with self.get_connection() as conn:
                conn.execute("UPDATE chapters SET beats = ? WHERE id = ?", (beats_text, chapter_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Update chapter beats error: {e}")
            return False

    def get_chapter_beats(self, chapter_id: str):
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
    def save_generation_chunk(self, chapter_id: str, raw_text: str, summary: str):
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

    def get_last_chunk_summary(self, chapter_id: str) -> str:
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

    def get_chapter_content(self, chapter_id: str):
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("SELECT content FROM chapters WHERE id = ?", (chapter_id,))
                res = cursor.fetchone()
                return res[0] if res else ""
        except sqlite3.Error as e:
            logging.error(f"Get chapter content error: {e}")
            return ""

    def save_beat(self, project_id: str, chapter_id: str, summary: str):
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO story_beats (project_id, chapter_id, summary)
                    VALUES (?, ?, ?)
                """, (project_id, chapter_id, summary))
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Save beat error: {e}")

    def get_deep_memory(self, project_id: str, query: str) -> str:
        """
        Retrieves relevant context based on key terms in the query.
        Includes all characters from the project for full context.
        """
        query_lower = query.lower()
        memory = []
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 1. All Characters in this Project
                memory.append("[CHARACTERS IN THIS STORY]")
                # Fetch all VISIBLE characters for THIS PROJECT
                cursor.execute("""
                    SELECT name, role, pronouns, personality_traits, physical_description, 
                           backstory, motivations, internal_conflicts, strengths, weaknesses, 
                           speech_pattern, character_arc 
                    FROM characters 
                    WHERE project_id = ? AND is_visible = 1
                """, (project_id,))
                all_chars = cursor.fetchall()
                
                if all_chars:
                    # Always provide full character details for context
                    memory.append(f"This story has {len(all_chars)} character(s):\n")
                    
                    for c in all_chars:
                        name, role, pronouns, traits, physical, backstory, motivations, conflicts, strengths, weaknesses, speech, arc = c
                        
                        memory.append(f"=== CHARACTER: {name} ===")
                        if role: memory.append(f"Role: {role}")
                        if pronouns: memory.append(f"Pronouns: {pronouns}")
                        if traits: memory.append(f"Personality: {traits}")
                        if physical: memory.append(f"Appearance: {physical}")
                        if backstory: memory.append(f"Backstory: {backstory}")
                        if motivations: memory.append(f"Motivations: {motivations}")
                        if conflicts: memory.append(f"Internal Conflicts: {conflicts}")
                        if strengths: memory.append(f"Strengths: {strengths}")
                        if weaknesses: memory.append(f"Weaknesses: {weaknesses}")
                        if speech: memory.append(f"Speech Pattern: {speech}")
                        if arc: memory.append(f"Character Arc: {arc}")
                        memory.append("")  # Spacer between characters
                else:
                    memory.append("No characters have been created for this project yet.")

                # 2. World Elements in this Project
                memory.append("\n[WORLD ELEMENTS]")
                cursor.execute("""
                    SELECT name, element_type, description, sensory_details, significance 
                    FROM world_elements 
                    WHERE project_id = ? AND is_visible = 1
                """, (project_id,))
                all_elements = cursor.fetchall()
                
                if all_elements:
                    memory.append(f"This story has {len(all_elements)} world element(s):\n")
                    
                    for elem in all_elements:
                        name, elem_type, description, sensory, significance = elem
                        
                        type_labels = {
                            'setting': 'Setting',
                            'location': 'Location', 
                            'event': 'Event',
                            'system': 'System',
                            'item': 'Item',
                            'other': 'Other'
                        }
                        type_label = type_labels.get(elem_type, 'Element')
                        
                        memory.append(f"=== {type_label.upper()}: {name} ===")
                        if description: memory.append(f"Description: {description}")
                        if sensory: memory.append(f"Sensory Details: {sensory}")
                        if significance: memory.append(f"Significance: {significance}")
                        memory.append("")  # Spacer between elements
                else:
                    memory.append("No world elements have been created for this project yet.")

                # 3. Chapter Outline from Story Bible
                memory.append("\n[CHAPTER OUTLINE]")
                cursor.execute("SELECT outline, synopsis FROM story_bible WHERE project_id = ?", (project_id,))
                bible_row = cursor.fetchone()
                
                if bible_row and bible_row[0]:
                    outline_data = bible_row[0]
                    try:
                        import json
                        outline_chapters = json.loads(outline_data)
                        if isinstance(outline_chapters, list) and len(outline_chapters) > 0:
                            memory.append(f"This story has a {len(outline_chapters)}-chapter outline:\n")
                            for ch in outline_chapters:
                                ch_num = ch.get('chapter_number', '?')
                                ch_title = ch.get('title', 'Untitled')
                                ch_summary = ch.get('summary', '')
                                
                                memory.append(f"Chapter {ch_num}: {ch_title}")
                                if ch_summary: memory.append(ch_summary)
                                memory.append("")
                        else:
                            memory.append("Outline exists but has no chapters defined.")
                    except (json.JSONDecodeError, TypeError):
                        # If it's plain text outline (old format)
                        if outline_data.strip():
                            memory.append("Plain text outline:")
                            memory.append(outline_data[:1500] + ("..." if len(outline_data) > 1500 else ""))
                        else:
                            memory.append("No chapter outline created yet.")
                else:
                    memory.append("No chapter outline created yet.")
                
                # Add Synopsis for additional context
                if bible_row and bible_row[1]:
                    synopsis = bible_row[1]
                    memory.append("\n[STORY SYNOPSIS]")
                    memory.append(synopsis[:1000] + ("..." if len(synopsis) > 1000 else ""))

                # 4. Story Beats (Overview)
                memory.append("\n[STORY BEATS (SUMMARY)]")
                cursor.execute("SELECT summary FROM story_beats WHERE project_id = ? ORDER BY chapter_id", (project_id,))
                beats = cursor.fetchall()
                if beats:
                    for i, beat in enumerate(beats):
                        memory.append(f"Ch {i+1}: {beat[0]}")
                else:
                    memory.append("No story beats recorded yet.")

                # 5. Relevant Chapter Snippets (Simple Keyword Search)
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
                character_id = data.get('id')
                
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
                        value = data.get(k, '')
                        # Convert lists/dicts to JSON strings for SQLite compatibility
                        if isinstance(value, (list, dict)):
                            value = json.dumps(value)
                        elif value is None:
                            value = ''
                        values.append(value)

                if character_id:
                    # Update existing character
                    set_clause = ", ".join([f"{k} = ?" for k in keys])
                    values.append(character_id)
                    cursor.execute(f"""
                        UPDATE characters 
                        SET {set_clause}
                        WHERE id = ?
                    """, values)
                    new_id = character_id
                else:
                    # Insert new character with UUID
                    new_id = generate_uuid()
                    placeholders = ", ".join(["?"] * (len(keys) + 1))
                    columns = "id, " + ", ".join(keys)
                    cursor.execute(f"""
                        INSERT INTO characters 
                        ({columns})
                        VALUES ({placeholders})
                    """, [new_id] + values)
                
                conn.commit()
                
                # Mark characters summary as stale
                project_id = data.get('project_id')
                if project_id:
                    self.increment_content_version(str(project_id), 'characters')
                
                return new_id  # Return the character ID (new or existing)
        except sqlite3.Error as e:
            logging.error(f"Save character error: {e}")
            return None

    def delete_character(self, character_id: str):
        """Delete a character by ID."""
        try:
            if not character_id:
                logging.error("Delete character error: No character_id provided")
                return False
            
            logging.info(f"Attempting to delete character with id={character_id}")
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM characters WHERE id = ?", (character_id,))
                conn.commit()
                
                deleted = cursor.rowcount > 0
                logging.info(f"Delete character result: rowcount={cursor.rowcount}, deleted={deleted}")
                return True  # Return True even if no rows affected (character might already be deleted)
        except Exception as e:
            logging.error(f"Delete character error: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return False

    def get_all_characters(self, project_id: str):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Return limited info for list
                cursor.execute("SELECT name, role FROM characters WHERE project_id = ? ORDER BY name", (project_id,))
                return [{'name': row[0], 'role': row[1]} for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Get characters error: {e}")
            return []

    def get_character_details(self, name: str, project_id: str):
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

    def get_chapters(self, project_id: str):
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

    def update_chapter_progress(self, chapter_id: str, last_count: int):
        """Update the last summarized character count."""
        try:
            with self.get_connection() as conn:
                conn.execute("UPDATE chapters SET last_summarized_char_count = ? WHERE id = ?", (last_count, chapter_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Update progress error: {e}")
            return False

    def save_chapter_summary(self, chapter_id: str, summary: str, recent_summary: str = None):
        try:
            with self.get_connection() as conn:
                if recent_summary:
                    conn.execute("UPDATE chapters SET summary_text = ?, recent_chapter_summary = ? WHERE id = ?", (summary, recent_summary, chapter_id))
                else:
                    conn.execute("UPDATE chapters SET summary_text = ? WHERE id = ?", (summary, chapter_id))
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Save summary error: {e}")

    def get_chapter_summary(self, chapter_id: str):
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

    # ==================== WORLD ELEMENTS METHODS ====================
    
    def create_world_element(self, project_id: str, name: str, element_type: str = 'other',
                            description: str = '', sensory_details: str = '',
                            significance: str = '', custom_traits: str = '',
                            series_id: str = None):
        """Create a new world building element."""
        try:
            # Convert any list/dict values to JSON strings
            def to_string(val):
                if isinstance(val, (list, dict)):
                    return json.dumps(val)
                return val if val is not None else ''
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                element_id = generate_uuid()
                cursor.execute("""
                    INSERT INTO world_elements 
                    (id, project_id, series_id, name, element_type, description, 
                     sensory_details, significance, custom_traits, source_project_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (element_id, project_id, series_id, to_string(name), to_string(element_type), 
                      to_string(description), to_string(sensory_details), 
                      to_string(significance), to_string(custom_traits), project_id))
                conn.commit()
                
                # Mark world_elements summary as stale
                if project_id:
                    self.increment_content_version(str(project_id), 'world_elements')
                
                return element_id
        except sqlite3.Error as e:
            logging.error(f"Create world element error: {e}")
            return None
    
    def get_world_elements(self, project_id: str = None, series_id: str = None, 
                          element_type: str = None):
        """Get world elements with optional filtering."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = "SELECT * FROM world_elements WHERE 1=1"
                params = []
                
                if project_id:
                    query += " AND project_id = ?"
                    params.append(project_id)
                if series_id:
                    query += " AND series_id = ?"
                    params.append(series_id)
                if element_type:
                    query += " AND element_type = ?"
                    params.append(element_type)
                
                query += " ORDER BY element_type, name"
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Get world elements error: {e}")
            return []
    
    def update_world_element(self, element_id: str, data: dict):
        """Update a world element."""
        try:
            allowed_fields = ['name', 'element_type', 'description', 'sensory_details',
                            'significance', 'custom_traits', 'is_visible']
            updates = []
            values = []
            
            for field in allowed_fields:
                if field in data:
                    updates.append(f"{field} = ?")
                    values.append(data[field])
            
            if not updates:
                return False
            
            values.append(element_id)
            
            with self.get_connection() as conn:
                # Get project_id before updating so we can mark version stale
                cursor = conn.execute("SELECT project_id FROM world_elements WHERE id = ?", (element_id,))
                row = cursor.fetchone()
                project_id = row[0] if row else None
                
                conn.execute(f"UPDATE world_elements SET {', '.join(updates)} WHERE id = ?", values)
                conn.commit()
                
                # Mark world_elements summary as stale
                if project_id:
                    self.increment_content_version(str(project_id), 'world_elements')
                
                return True
        except sqlite3.Error as e:
            logging.error(f"Update world element error: {e}")
            return False
    
    def delete_world_element(self, element_id: str):
        """Delete a world element."""
        try:
            with self.get_connection() as conn:
                conn.execute("DELETE FROM world_elements WHERE id = ?", (element_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Delete world element error: {e}")
            return False
    
    def get_world_element(self, element_id: str):
        """Get a single world element by ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM world_elements WHERE id = ?", (element_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            logging.error(f"Get world element error: {e}")
            return None

    # ==================== SERIES METHODS ====================
    
    def create_series(self, name: str, description: str = ''):
        """Create a new series folder."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                series_id = generate_uuid()
                cursor.execute(
                    "INSERT INTO series (id, name, description) VALUES (?, ?, ?)",
                    (series_id, name, description)
                )
                conn.commit()
                return series_id
        except sqlite3.Error as e:
            logging.error(f"Create series error: {e}")
            return None
    
    def get_series_list(self):
        """Get all series folders."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM series ORDER BY created_at DESC")
                series_list = []
                for row in cursor.fetchall():
                    series = dict(row)
                    # Get project count
                    cursor.execute(
                        "SELECT COUNT(*) FROM series_projects WHERE series_id = ?",
                        (series['id'],)
                    )
                    series['project_count'] = cursor.fetchone()[0]
                    series_list.append(series)
                return series_list
        except sqlite3.Error as e:
            logging.error(f"Get series list error: {e}")
            return []
    
    def get_series(self, series_id: str):
        """Get a series with its projects."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM series WHERE id = ?", (series_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                
                series = dict(row)
                
                # Get projects in this series
                cursor.execute("""
                    SELECT p.*, sp.book_order 
                    FROM projects p
                    JOIN series_projects sp ON p.id = sp.project_id
                    WHERE sp.series_id = ?
                    ORDER BY sp.book_order
                """, (series_id,))
                series['projects'] = [dict(r) for r in cursor.fetchall()]
                
                return series
        except sqlite3.Error as e:
            logging.error(f"Get series error: {e}")
            return None
    
    def update_series(self, series_id: str, name: str = None, description: str = None,
                     timeline_data: str = None):
        """Update series details."""
        try:
            updates = []
            values = []
            
            if name is not None:
                updates.append("name = ?")
                values.append(name)
            if description is not None:
                updates.append("description = ?")
                values.append(description)
            if timeline_data is not None:
                updates.append("timeline_data = ?")
                values.append(timeline_data)
            
            if not updates:
                return False
            
            values.append(series_id)
            
            with self.get_connection() as conn:
                conn.execute(f"UPDATE series SET {', '.join(updates)} WHERE id = ?", values)
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Update series error: {e}")
            return False
    
    def delete_series(self, series_id: str):
        """Delete a series (projects remain, just unlinked)."""
        try:
            with self.get_connection() as conn:
                conn.execute("DELETE FROM series_projects WHERE series_id = ?", (series_id,))
                conn.execute("DELETE FROM series WHERE id = ?", (series_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Delete series error: {e}")
            return False
    
    def add_project_to_series(self, series_id: str, project_id: str, book_order: int = None):
        """Add a project to a series."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if book_order is None:
                    # Get next order
                    cursor.execute(
                        "SELECT MAX(book_order) FROM series_projects WHERE series_id = ?",
                        (series_id,)
                    )
                    max_order = cursor.fetchone()[0]
                    book_order = 1 if max_order is None else max_order + 1
                
                cursor.execute("""
                    INSERT OR REPLACE INTO series_projects (series_id, project_id, book_order)
                    VALUES (?, ?, ?)
                """, (series_id, project_id, book_order))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Add project to series error: {e}")
            return False
    
    def remove_project_from_series(self, series_id: str, project_id: str):
        """Remove a project from a series."""
        try:
            with self.get_connection() as conn:
                conn.execute(
                    "DELETE FROM series_projects WHERE series_id = ? AND project_id = ?",
                    (series_id, project_id)
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Remove project from series error: {e}")
            return False
    
    def get_series_bible(self, series_id: str):
        """Get merged story bible from all projects in a series."""
        try:
            series = self.get_series(series_id)
            if not series or not series.get('projects'):
                return {}
            
            merged = {
                'braindump': [],
                'genre': [],
                'style': [],
                'synopsis': [],
                'worldbuilding': [],
                'outline': []
            }
            
            for project in series['projects']:
                bible = self.get_story_bible(project['id'])
                if bible:
                    for field in merged.keys():
                        if bible.get(field):
                            merged[field].append({
                                'project_id': project['id'],
                                'project_name': project['name'],
                                'content': bible[field]
                            })
            
            return merged
        except Exception as e:
            logging.error(f"Get series bible error: {e}")
            return {}
    
    def get_series_characters(self, series_id: str):
        """Get all characters from all projects in a series."""
        try:
            series = self.get_series(series_id)
            if not series or not series.get('projects'):
                return []
            
            all_characters = []
            for project in series['projects']:
                chars = self.get_characters(project['id'])
                for char in chars:
                    char['source_project_id'] = project['id']
                    char['source_project_name'] = project['name']
                    all_characters.append(char)
            
            return all_characters
        except Exception as e:
            logging.error(f"Get series characters error: {e}")
            return []
    
    def get_series_world_elements(self, series_id: str):
        """Get all world elements from all projects in a series."""
        try:
            series = self.get_series(series_id)
            if not series or not series.get('projects'):
                return []
            
            all_elements = []
            for project in series['projects']:
                elements = self.get_world_elements(project_id=project['id'])
                for elem in elements:
                    elem['source_project_name'] = project['name']
                    all_elements.append(elem)
            
            # Also get series-level elements
            series_elements = self.get_world_elements(series_id=series_id)
            all_elements.extend(series_elements)
            
            return all_elements
        except Exception as e:
            logging.error(f"Get series world elements error: {e}")
            return []
    
    def get_series_timeline(self, series_id: str):
        """Get the timeline data for a series."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT timeline_data FROM series WHERE id = ?", (series_id,))
                row = cursor.fetchone()
                if row and row[0]:
                    import json
                    return json.loads(row[0])
                return []
        except Exception as e:
            logging.error(f"Get series timeline error: {e}")
            return []
    
    def update_series_timeline(self, series_id: str, timeline_data: list):
        """Update the timeline data for a series."""
        try:
            import json
            with self.get_connection() as conn:
                conn.execute(
                    "UPDATE series SET timeline_data = ? WHERE id = ?",
                    (json.dumps(timeline_data), series_id)
                )
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Update series timeline error: {e}")
            return False

    # ==================== SCENE METHODS ====================
    
    def create_scene(self, chapter_id: str, title: str = '', summary: str = '',
                    pov_character: str = '', location: str = ''):
        """Create a new scene in a chapter."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get next order
                cursor.execute(
                    "SELECT MAX(scene_order) FROM scenes WHERE chapter_id = ?",
                    (chapter_id,)
                )
                max_order = cursor.fetchone()[0]
                next_order = 1 if max_order is None else max_order + 1
                
                scene_id = generate_uuid()
                cursor.execute("""
                    INSERT INTO scenes (id, chapter_id, scene_order, title, summary, pov_character, location)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (scene_id, chapter_id, next_order, title, summary, pov_character, location))
                conn.commit()
                return scene_id
        except sqlite3.Error as e:
            logging.error(f"Create scene error: {e}")
            return None
    
    def get_scenes(self, chapter_id: str):
        """Get all scenes for a chapter."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM scenes WHERE chapter_id = ? ORDER BY scene_order",
                    (chapter_id,)
                )
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Get scenes error: {e}")
            return []
    
    def update_scene(self, scene_id: str, data: dict):
        """Update a scene."""
        try:
            allowed_fields = ['title', 'summary', 'content', 'pov_character', 'location', 'scene_order']
            updates = []
            values = []
            
            for field in allowed_fields:
                if field in data:
                    updates.append(f"{field} = ?")
                    values.append(data[field])
            
            if not updates:
                return False
            
            values.append(scene_id)
            
            with self.get_connection() as conn:
                conn.execute(f"UPDATE scenes SET {', '.join(updates)} WHERE id = ?", values)
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Update scene error: {e}")
            return False
    
    def delete_scene(self, scene_id: str):
        """Delete a scene."""
        try:
            with self.get_connection() as conn:
                conn.execute("DELETE FROM scenes WHERE id = ?", (scene_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Delete scene error: {e}")
            return False
    
    def reorder_scenes(self, chapter_id: str, scene_ids: list):
        """Reorder scenes in a chapter."""
        try:
            with self.get_connection() as conn:
                for order, scene_id in enumerate(scene_ids, 1):
                    conn.execute(
                        "UPDATE scenes SET scene_order = ? WHERE id = ? AND chapter_id = ?",
                        (order, scene_id, chapter_id)
                    )
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Reorder scenes error: {e}")
            return False

    def get_scene_context(self, chapter_id: str):
        """
        Get scene context for a chapter - returns all scenes with their metadata
        (POV character, location, summary) to inject into AI context.
        This allows the AI to be aware of scene structure, similar to Sudowrite.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, scene_order, title, summary, pov_character, location
                    FROM scenes
                    WHERE chapter_id = ?
                    ORDER BY scene_order
                """, (chapter_id,))
                scenes = cursor.fetchall()
                
                if not scenes:
                    return None
                
                scene_list = []
                for s in scenes:
                    scene_data = {
                        'id': s[0],
                        'scene_order': s[1],
                        'title': s[2] or '',
                        'summary': s[3] or '',
                        'pov_character': s[4] or '',
                        'location': s[5] or '',
                    }
                    scene_list.append(scene_data)
                
                # Build a formatted scene context string
                context_parts = []
                for sc in scene_list:
                    parts = []
                    if sc['title']:
                        parts.append(f"Scene: {sc['title']}")
                    if sc['pov_character']:
                        parts.append(f"POV: {sc['pov_character']}")
                    if sc['location']:
                        parts.append(f"Location: {sc['location']}")
                    if sc['summary']:
                        parts.append(f"Summary: {sc['summary']}")
                    if parts:
                        context_parts.append(' | '.join(parts))
                
                return {
                    'scenes': scene_list,
                    'formatted': '\n'.join(context_parts),
                }
        except sqlite3.Error as e:
            logging.error(f"Get scene context error: {e}")
            return None

    def get_project_series_id(self, project_id: str):
        """Get the series ID for a project, if it belongs to one."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT series_id FROM series_projects WHERE project_id = ?",
                    (project_id,)
                )
                row = cursor.fetchone()
                return row[0] if row else None
        except sqlite3.Error as e:
            logging.error(f"Get project series ID error: {e}")
            return None

    def get_series_context_for_project(self, project_id: str):
        """
        If this project belongs to a series, fetch shared characters and worldbuilding
        from sibling projects to provide cross-book context (Sudowrite-style series awareness).
        Returns a formatted string or None if project is not in a series.
        """
        try:
            series_id = self.get_project_series_id(project_id)
            if not series_id:
                return None
            
            series = self.get_series(series_id)
            if not series or not series.get('projects'):
                return None
            
            parts = []
            parts.append(f"Series: {series.get('name', 'Unnamed Series')}")
            if series.get('description'):
                parts.append(f"Description: {series['description']}")
            
            # Get characters from OTHER projects in the series (not current project)
            sibling_chars = []
            sibling_world = []
            for proj in series['projects']:
                if proj['id'] == project_id:
                    continue  # Skip current project
                
                # Characters from sibling
                chars = self.get_characters(proj['id'])
                for c in chars:
                    if c.get('is_visible', 1) != 0:
                        entry = f"- {c['name']}"
                        if c.get('role'): entry += f" ({c['role']})"
                        if c.get('personality_traits'): entry += f": {c['personality_traits'][:100]}"
                        entry += f" [from {proj['name']}]"
                        sibling_chars.append(entry)
                
                # World elements from sibling
                elements = self.get_world_elements(project_id=proj['id'])
                for e in elements:
                    if e.get('is_visible', 1) != 0:
                        entry = f"- {e['name']} ({e.get('element_type', 'other')})"
                        if e.get('description'): entry += f": {e['description'][:80]}"
                        entry += f" [from {proj['name']}]"
                        sibling_world.append(entry)
            
            if sibling_chars:
                parts.append("\nShared Characters from Other Books:")
                parts.extend(sibling_chars[:15])  # Cap to 15 characters
            
            if sibling_world:
                parts.append("\nShared World Elements from Other Books:")
                parts.extend(sibling_world[:10])  # Cap to 10 elements
            
            # Only return if we have meaningful series context
            if sibling_chars or sibling_world:
                return '\n'.join(parts)
            return None
        except Exception as e:
            logging.error(f"Get series context for project error: {e}")
            return None

    # ==================== CHARACTER VERSION METHODS ====================
    
    def create_character_version(self, character_id: str, project_id: str, 
                                 version_notes: str = '', trait_overrides: str = ''):
        """Create a version of a character for a specific project."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                version_id = generate_uuid()
                cursor.execute("""
                    INSERT INTO character_versions 
                    (id, character_id, project_id, version_notes, trait_overrides)
                    VALUES (?, ?, ?, ?, ?)
                """, (version_id, character_id, project_id, version_notes, trait_overrides))
                conn.commit()
                return version_id
        except sqlite3.Error as e:
            logging.error(f"Create character version error: {e}")
            return None
    
    def get_character_versions(self, character_id: str):
        """Get all versions of a character."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT cv.*, p.name as project_name
                    FROM character_versions cv
                    JOIN projects p ON cv.project_id = p.id
                    WHERE cv.character_id = ?
                    ORDER BY cv.created_at
                """, (character_id,))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Get character versions error: {e}")
            return []
    
    def set_canonical_version(self, version_id: str, character_id: str):
        """Set a version as canonical (unsets others)."""
        try:
            with self.get_connection() as conn:
                # Unset all other versions
                conn.execute(
                    "UPDATE character_versions SET is_canonical = 0 WHERE character_id = ?",
                    (character_id,)
                )
                # Set this one
                conn.execute(
                    "UPDATE character_versions SET is_canonical = 1 WHERE id = ?",
                    (version_id,)
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Set canonical version error: {e}")
            return False
    
    def delete_character_version(self, version_id: int):
        """Delete a character version."""
        try:
            with self.get_connection() as conn:
                conn.execute("DELETE FROM character_versions WHERE id = ?", (version_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Delete character version error: {e}")
            return False

    # ==================== CHAPTER OUTLINE LINKING METHODS ====================
    
    def link_chapter_to_outline(self, chapter_id: str, outline_section: str, outline_order: int = 0):
        """Link a chapter to an outline section."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO chapter_outline_links 
                    (chapter_id, outline_section, outline_order)
                    VALUES (?, ?, ?)
                """, (chapter_id, outline_section, outline_order))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Link chapter to outline error: {e}")
            return False
    
    def get_chapter_outline_links(self, project_id: str):
        """Get all chapter-outline links for a project."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT col.*, c.title as chapter_title
                    FROM chapter_outline_links col
                    JOIN chapters c ON col.chapter_id = c.id
                    WHERE c.project_id = ?
                    ORDER BY col.outline_order
                """, (project_id,))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Get chapter outline links error: {e}")
            return []
    
    def unlink_chapter_from_outline(self, chapter_id: str):
        """Remove chapter-outline link."""
        try:
            with self.get_connection() as conn:
                conn.execute("DELETE FROM chapter_outline_links WHERE chapter_id = ?", (chapter_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Unlink chapter error: {e}")
            return False

    # ==================== CSV IMPORT/EXPORT METHODS ====================
    
    def export_characters_csv(self, project_id: str) -> str:
        """Export characters to CSV format."""
        import csv
        import io
        
        try:
            characters = self.get_characters(project_id)
            if not characters:
                return ""
            
            output = io.StringIO()
            fieldnames = ['name', 'role', 'pronouns', 'personality_traits', 
                         'physical_description', 'backstory', 'motivations',
                         'internal_conflicts', 'strengths', 'weaknesses',
                         'speech_pattern', 'character_arc']
            
            writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            
            for char in characters:
                writer.writerow(char)
            
            return output.getvalue()
        except Exception as e:
            logging.error(f"Export characters CSV error: {e}")
            return ""
    
    def import_characters_csv(self, project_id: str, csv_data: str) -> dict:
        """Import characters from CSV format."""
        import csv
        import io
        
        try:
            reader = csv.DictReader(io.StringIO(csv_data))
            imported = 0
            errors = []
            
            for row in reader:
                if not row.get('name'):
                    errors.append(f"Row missing name: {row}")
                    continue
                
                char_data = {
                    'project_id': project_id,
                    'name': row.get('name', ''),
                    'role': row.get('role', ''),
                    'pronouns': row.get('pronouns', ''),
                    'personality_traits': row.get('personality_traits', ''),
                    'physical_description': row.get('physical_description', ''),
                    'backstory': row.get('backstory', ''),
                    'motivations': row.get('motivations', ''),
                    'internal_conflicts': row.get('internal_conflicts', ''),
                    'strengths': row.get('strengths', ''),
                    'weaknesses': row.get('weaknesses', ''),
                    'speech_pattern': row.get('speech_pattern', ''),
                    'character_arc': row.get('character_arc', ''),
                    'is_visible': 1
                }
                
                if self.save_character(char_data):
                    imported += 1
                else:
                    errors.append(f"Failed to save: {row.get('name')}")
            
            return {'imported': imported, 'errors': errors}
        except Exception as e:
            logging.error(f"Import characters CSV error: {e}")
            return {'imported': 0, 'errors': [str(e)]}
    
    def export_world_elements_csv(self, project_id: str) -> str:
        """Export world elements to CSV format."""
        import csv
        import io
        
        try:
            elements = self.get_world_elements(project_id=project_id)
            if not elements:
                return ""
            
            output = io.StringIO()
            fieldnames = ['name', 'element_type', 'description', 'sensory_details',
                         'significance', 'custom_traits']
            
            writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            
            for elem in elements:
                writer.writerow(elem)
            
            return output.getvalue()
        except Exception as e:
            logging.error(f"Export world elements CSV error: {e}")
            return ""
    
    def import_world_elements_csv(self, project_id: str, csv_data: str) -> dict:
        """Import world elements from CSV format."""
        import csv
        import io
        
        try:
            reader = csv.DictReader(io.StringIO(csv_data))
            imported = 0
            errors = []
            
            for row in reader:
                if not row.get('name'):
                    errors.append(f"Row missing name: {row}")
                    continue
                
                element_id = self.create_world_element(
                    project_id=project_id,
                    name=row.get('name', ''),
                    element_type=row.get('element_type', 'other'),
                    description=row.get('description', ''),
                    sensory_details=row.get('sensory_details', ''),
                    significance=row.get('significance', ''),
                    custom_traits=row.get('custom_traits', '')
                )
                
                if element_id:
                    imported += 1
                else:
                    errors.append(f"Failed to save: {row.get('name')}")
            
            return {'imported': imported, 'errors': errors}
        except Exception as e:
            logging.error(f"Import world elements CSV error: {e}")
            return {'imported': 0, 'errors': [str(e)]}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db = DatabaseManager()
