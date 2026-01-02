import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'story_bible.db')

def check_db():
    print(f"Checking DB at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check Schema (Column Order)
    print("\n--- TABLE INFO ---")
    cursor.execute("PRAGMA table_info(story_bible)")
    columns = cursor.fetchall()
    for col in columns:
        print(col)
        
    # Check Data
    print("\n--- RAW DATA ---")
    cursor.execute("SELECT * FROM story_bible")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
        
    conn.close()

if __name__ == "__main__":
    check_db()
