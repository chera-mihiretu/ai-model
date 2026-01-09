from src.database.db_manager import DatabaseManager
import logging

logging.basicConfig(level=logging.INFO)

def test_memory():
    db = DatabaseManager()
    
    # 1. Create a dummy project
    pid = db.create_project("Test Project", "Sci-Fi")
    print(f"Created Project ID: {pid}")
    
    # 2. Add some lore
    db.save_character({
        "name": "Zorg",
        "role": "Alien Overlord",
        "personality_traits": "Ruthless, Hungry",
        "backstory": "Zorg wants to eat all the tacos."
    })
    
    # 3. Add a chapter
    cid = db.create_chapter(pid, "Chapter 1")
    db.update_chapter_content(cid, "Zorg landed his ship. He smelled tacos.")
    
    # 4. Fetch Memory
    print("\n--- FETCHING MEMORY ---")
    memory = db.get_deep_memory(pid, "Zorg")
    print(memory)
    print("-----------------------")
    
    if "Zorg" in memory and "Alien Overlord" in memory and "tacos" in memory:
        print("SUCCESS: Memory contains expected data.")
    else:
        print("FAILURE: Memory missing data.")

if __name__ == "__main__":
    test_memory()
