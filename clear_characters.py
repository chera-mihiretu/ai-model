import sqlite3
import os
import sys

def clear_characters():
    # Detect DB path assuming this script is in the project root
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "data", "story_bible.db")
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    print(f"Opening database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current count
        cursor.execute("SELECT COUNT(*) FROM characters")
        initial_count = cursor.fetchone()[0]
        print(f"Current character count: {initial_count}")
        
        if initial_count == 0:
            print("No characters to remove.")
            return

        # Delete all
        cursor.execute("DELETE FROM characters")
        conn.commit()
        
        # Verify
        cursor.execute("SELECT COUNT(*) FROM characters")
        final_count = cursor.fetchone()[0]
        print(f"Deletion complete. Remaining characters: {final_count}")
        
        # Optional: Reset ID counter (SQLite specific)
        # cursor.execute("DELETE FROM sqlite_sequence WHERE name='characters'")
        # conn.commit()
        # print("ID sequence reset.")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    confirm = input("This will DELETE ALL entries in the 'characters' table. Are you sure? (y/n): ")
    if confirm.lower() == 'y':
        clear_characters()
    else:
        print("Operation cancelled.")
