import sys
import os
import shutil
import platform
import subprocess
from pathlib import Path

def print_header(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def build():
    os_name = platform.system()
    print_header(f"Building Story Bible App for {os_name}")
    
    # 1. Clean previous builds
    print("-> Cleaning previous build artifacts...")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")

    # 2. Run PyInstaller
    print("-> Running PyInstaller with deployment.spec...")
    try:
        subprocess.check_call([sys.executable, "-m", "PyInstaller", "deployment.spec", "--clean", "--noconfirm"])
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Build failed: {e}")
        sys.exit(1)

    # 3. Post-build instructions
    print_header("Build Complete!")
    
    dist_dir = Path("dist") / "StoryBibleApp"
    if os_name == "Darwin": # macOS
        dist_dir = Path("dist") / "StoryBibleApp.app" / "Contents" / "MacOS"

    print(f"Executable location: {dist_dir.resolve()}")
    
    # Check for models
    models_src = Path("models")
    if os_name == "Darwin":
        # macOS apps are bundles, models typically go near the executable or in Resources
        # But for this app, we strictly follow the 'external' requirement.
        # It's safest to tell the user to put 'models' alongside the .app or inside MacOS folder depending on loader
        # Based on config/manager.py:
        # if frozen: base_dir = os.path.dirname(sys.executable)
        # So on mac it will look inside StoryBibleApp.app/Contents/MacOS/models
        models_dest = dist_dir / "models"
    else:
        models_dest = dist_dir / "models"
        
    print(f"\n[IMPORTANT] handling Models:")
    if not models_dest.exists():
        print(f"1. You MUST copy your 'models' directory to:")
        print(f"   {models_dest}")
        print("   (The LLaMA model is huge and not bundled automatically)")
    else:
        print(f"   'models' directory detected at {models_dest}")
        
    print(f"\n2. Launching:")
    if os_name == "Windows":
        print(f"   Run dist\\StoryBibleApp\\StoryBibleApp.exe")
    elif os_name == "Darwin":
        print(f"   Run dist/StoryBibleApp.app")
    else:
        print(f"   Run ./dist/StoryBibleApp/StoryBibleApp")

if __name__ == "__main__":
    build()
