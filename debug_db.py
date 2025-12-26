import sqlite3
import os

db_path = "/home/sabona/Desktop/DesktopApp/data/story_bible.db"

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM story_bible")
    rows = cursor.fetchall()
    print("Story Bible Entries:")
    for row in rows:
        print(row)
    
    cursor.execute("PRAGMA table_info(story_bible)")
    cols = cursor.fetchall()
    print("\nColumns:")
    for col in cols:
        print(col)
    conn.close()
