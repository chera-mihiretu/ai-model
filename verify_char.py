import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path.cwd()))

from src.database.db_manager import DatabaseManager

def test_migration_and_crud():
    print(">>> 1. Initializing Database (should trigger migration if needed)...")
    db = DatabaseManager("test_character_feature.db")
    
    # Check schema
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(characters)")
        cols = [c[1] for c in cursor.fetchall()]
        print(f"Columns found: {cols}")
        
        required = ['pronouns', 'motivations', 'internal_conflicts']
        missing = [r for r in required if r not in cols]
        if missing:
            print(f"FAILED: Missing columns: {missing}")
            sys.exit(1)
        else:
            print("SUCCESS: Schema migration verified.")

    print("\n>>> 2. Testing Save Character (New Fields)...")
    # Simulate saving a character with new fields
    char_data = {
        'project_id': 1,
        'name': 'TestHero',
        'role': 'Protagonist',
        'pronouns': 'She/Her',
        'motivations': 'To save the world\nand eat pizza',
        'backstory': 'Long ago...'
    }
    
    success = db.save_character(char_data)
    if not success:
        print("FAILED: save_character returned False")
        sys.exit(1)
    print("SUCCESS: Character saved.")

    print("\n>>> 3. Testing Load Character...")
    loaded = db.get_character_details('TestHero', 1)
    if not loaded:
        print("FAILED: Could not load character")
        sys.exit(1)
        
    print(f"Loaded: Name={loaded.get('name')}, Pronouns={loaded.get('pronouns')}")
    print(f"Motivations:\n{loaded.get('motivations')}")
    
    if loaded.get('pronouns') == 'She/Her' and "pizza" in loaded.get('motivations'):
        print("SUCCESS: Data persisted correctly.")
    else:
        print("FAILED: Data mismatch.")
        sys.exit(1)

    print("\n>>> 4. Testing EDIT Character (Update)...")
    # Simulate editing the existing character
    loaded['motivations'] += "\nAnd finish the code."
    loaded['pronouns'] = "They/Them" # Changed
    
    success = db.save_character(loaded)
    if not success:
         print("FAILED: Could not save update")
         sys.exit(1)
         
    updated = db.get_character_details('TestHero', 1)
    if updated.get('pronouns') == "They/Them" and "finish the code" in updated.get('motivations'):
        print("SUCCESS: Character updated correctly.")
    else:
        print(f"FAILED: Update mismatch. Got: {updated.get('pronouns')}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        if os.path.exists("data/test_character_feature.db"):
            os.remove("data/test_character_feature.db")
        test_migration_and_crud()
    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
