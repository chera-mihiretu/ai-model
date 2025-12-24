import sqlite3
from pathlib import Path

class DBManager:
    """Repository pattern for SQLite database operations."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initializes the database tables."""
        pass
