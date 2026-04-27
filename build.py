import shutil
import subprocess
import sys
import os
from pathlib import Path

# --- CONFIG ---
APP_NAME = "llm_switcher"
ICON_FILE = "llm_switcher.ico"
CONFIG_FILE = "config.json"

BASE_DIR = Path(__file__).parent
DIST_DIR = BASE_DIR / "dist"
BUILD_DIR = BASE_DIR / "build"
SPEC_FILE = BASE_DIR / f"{APP_NAME}.spec"

START_MENU_DIR = Path(r"C:\Users\Moritz\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Torres")

EXE_PATH = DIST_DIR / f"{APP_NAME}.exe"

# --- CLEAN ---
print("Cleaning old build...")
for path in [DIST_DIR, BUILD_DIR]:
    if path.exists():
        shutil.rmtree(path)
        
if SPEC_FILE.exists():
    SPEC_FILE.unlink()

# --- TCL/TK FIX ---
python_home = Path(sys.executable).parent
tcl_dir = python_home / "tcl" / "tcl8.6"
tk_dir = python_home / "tcl" / "tk8.6"

if not tcl_dir.exists() or not tk_dir.exists():
    # Fallback if tcl8.6/tk8.6 are not the exact names
    tcl_base = python_home / "tcl"
    if tcl_base.exists():
        tcl_dir = next(tcl_base.glob("tcl*"), tcl_dir)
        tk_dir = next(tcl_base.glob("tk*"), tk_dir)

print(f"Using Tcl from: {tcl_dir}")
print(f"Using Tk from: {tk_dir}")

os.environ["TCL_LIBRARY"] = str(tcl_dir)
os.environ["TK_LIBRARY"] = str(tk_dir)

print("Building executable...")
subprocess.run([
    sys.executable, "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    "--onefile",
    "--windowed",
    f"--name={APP_NAME}",
    f"--icon={ICON_FILE}",
    
    # Explicitly add Tcl/Tk data to satisfy the runtime hook
    # In --onefile, we put them in the root of the temp folder
    f"--add-data={tcl_dir};_tcl_data",
    f"--add-data={tk_dir};_tk_data",
    
    f"{APP_NAME}.py"
], check=True)

# --- COPY CONFIG --- 
print("Copying config.json...")

if not Path(CONFIG_FILE).exists():
    raise FileNotFoundError("config.json not found")

shutil.copy(CONFIG_FILE, DIST_DIR / CONFIG_FILE)

# --- CREATE SHORTCUT ---
print("Creating shortcut...")

import win32com.client  # requires pywin32

shell = win32com.client.Dispatch("WScript.Shell")
shortcut = shell.CreateShortCut(str(BASE_DIR / f"{APP_NAME}.lnk"))

shortcut.TargetPath = str(EXE_PATH.resolve())
shortcut.WorkingDirectory = str(DIST_DIR.parent.resolve())
shortcut.IconLocation = str(EXE_PATH.resolve())
shortcut.save()

# --- MOVE TO START MENU ---
print("Moving shortcut to Start Menu...")

START_MENU_DIR.mkdir(parents=True, exist_ok=True)

shutil.copy(
    BASE_DIR / f"{APP_NAME}.lnk",
    START_MENU_DIR / f"{APP_NAME}.lnk"
)

(Path(BASE_DIR / f"{APP_NAME}.lnk")).unlink(missing_ok=True)

print("Build complete!")
