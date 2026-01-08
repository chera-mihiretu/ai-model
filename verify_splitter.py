import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QWidget, QLabel
from PyQt6.QtCore import QSettings

# Setup path
sys.path.append(os.getcwd())
from src.ui.components.main_splitter import MainWorkspaceSplitter

def run_verification():
    print("restarting app instance...")
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
        
    app.setOrganizationName("StoryBible")
    app.setApplicationName("StoryBible Pro")
    
    # 1. Clear existing settings for clear test
    settings = QSettings()
    settings.remove("layout/splitter_sizes")
    print("Cleared QSettings 'layout/splitter_sizes'")
    
    # 2. Create Splitter
    left = QWidget()
    left.setStyleSheet("background: red;")
    mid = QWidget()
    mid.setStyleSheet("background: green;")
    right = QWidget()
    right.setStyleSheet("background: blue;")
    
    splitter = MainWorkspaceSplitter(left, mid, right)
    splitter.resize(1450, 800)
    splitter.show()
    
    # 3. Verify Default Sizes (approximate, since it depends on total width)
    # Default Set: [300, 800, 350] -> Total 1450.
    # Since we resized to 1450, we expect close to [300, 800, 350]
    sizes = splitter.sizes()
    print(f"Initial Sizes: {sizes}")
    
    # Allow event loop to process (load_sizes is deferred)
    app.processEvents()
    # Again
    import time
    time.sleep(0.1)
    app.processEvents()
    
    sizes = splitter.sizes()
    print(f"Sizes after load (defaults): {sizes}")
    
    # 4. Modify Sizes
    new_sizes = [250, 950, 250]
    splitter.setSizes(new_sizes)
    print(f"Set new sizes: {new_sizes}")
    app.processEvents() # trigger save debounce?
    
    # Manually trigger save to avoid waiting for debounce
    splitter.save_sizes()
    print("Manually stuck save_sizes()")
    
    # 5. Check Persistence
    saved_val = settings.value("layout/splitter_sizes")
    print(f"Saved QSettings Value: {saved_val}")
    
    saved_list = [int(x) for x in saved_val] if saved_val else []
    
    if saved_list == splitter.sizes():
        print("PASS: Persistence Verified (Saved matches Current)")
    else:
        print(f"FAIL: Persistence Mismatch. Saved: {saved_list}, Current: {splitter.sizes()}")
        
    # 6. Verify Minimum Widths
    # Try to shrink left below 200
    splitter.setSizes([100, 1100, 250])
    app.processEvents()
    final_sizes = splitter.sizes()
    print(f"After shrinking Left to 100: {final_sizes}")
    if final_sizes[0] >= 200:
        print("PASS: Left Panel Minimum Width Enforced")
    else:
        print(f"FAIL: Left Panel shrank to {final_sizes[0]}")
        
    print("Verification Complete.")
    # sys.exit(0)

if __name__ == "__main__":
    run_verification()
