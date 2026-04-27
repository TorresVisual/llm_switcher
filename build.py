import os
import shutil
import subprocess
from pathlib import Path

# --- CONFIG ---
APP_NAME = "llm_switcher"
ICON_FILE = "llm_switcher.ico"
CONFIG_FILE = "config.json"

# Your target Start Menu folder
START_MENU_DIR = Path(r"C:\Users\Moritz\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Torres")

# --- STEP 1: BUILD ---
print("Building with PyInstaller...")
subprocess.run([
    "pyinstaller",
    "--onefile",
    "--windowed",
    f"--icon={ICON_FILE}",
    f"{APP_NAME}.py"
], check=True)

# --- STEP 2: PATHS ---
dist_dir = Path("dist")
dist_exe = dist_dir / f"{APP_NAME}.exe"
shortcut_path = Path(f"{APP_NAME}.lnk")

# --- STEP 3: COPY CONFIG --- 
print("Copying config.json...")
src_config = Path(CONFIG_FILE)

if not src_config.exists(): 
    raise FileNotFoundError(f"{CONFIG_FILE} not found!")

shutil.copy(src_config, dist_dir / CONFIG_FILE)

# --- STEP 4: CREATE SHORTCUT ---
print("Creating shortcut...")

import win32com.client  # requires pywin32

shell = win32com.client.Dispatch("WScript.Shell")
shortcut = shell.CreateShortCut(str(shortcut_path))

shortcut.TargetPath = str(dist_exe.resolve())
shortcut.WorkingDirectory = str(dist_exe.parent.resolve())
shortcut.IconLocation = str(dist_exe.resolve())
shortcut.save()

# --- STEP 5: COPY TO START MENU ---
print("Copying shortcut to Start Menu...")

START_MENU_DIR.mkdir(parents=True, exist_ok=True)
shutil.copy(shortcut_path, START_MENU_DIR / shortcut_path.name)

print("Done.")
