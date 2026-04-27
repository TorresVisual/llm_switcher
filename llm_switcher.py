"""
LLM Profile Switcher — Windows system tray app.
Left-click the tray icon to open the switcher; right-click for options.

Config: config.json (created automatically on first run)
  Maps each LLM service name → list of Chrome profile directory names.
  Example: {"ChatGPT": ["Default"], "Claude": ["Profile 1"]}
"""
import os
import sys
import json
import subprocess
import winreg
import ctypes
from pathlib import Path
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem, Menu
import tkinter as tk

APP_DIR     = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
CONFIG_PATH = APP_DIR / "config.json"

SERVICES = {
    "ChatGPT":        ("https://chat.openai.com/",     "#10a37f"),
    "Claude":         ("https://claude.ai/",            "#da7756"),
    "Gemini":         ("https://gemini.google.com/",    "#4285f4"),
    "Perplexity":     ("https://www.perplexity.ai/",    "#20b2aa"),
    "GitHub Copilot": ("https://github.com/copilot",    "#7c3aed"),
    "Grok":           ("https://grok.com/",             "#9ca3af"),
    "WolframAlpha":   ("https://www.wolframalpha.com/", "#cc2200"),
}

BG     = "#0d0d1b"
CARD   = "#161628"
HOVER  = "#1e1e3a"
HEADER = "#09091a"
FG     = "#ddddf5"
MUTED  = "#5a5a90"
SEP    = "#1e1e38"


# ── ctypes helpers ────────────────────────────────────────────────────────────

class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

def cursor_pos():
    pt = _POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y

def alert(msg):
    ctypes.windll.user32.MessageBoxW(0, msg, "LLM Switcher", 0x10)


# ── Chrome ────────────────────────────────────────────────────────────────────

def find_chrome():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe")
        path, _ = winreg.QueryValueEx(key, "")
        winreg.CloseKey(key)
        if os.path.exists(path):
            return path
    except OSError:
        pass
    for p in [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("ProgramFiles", ""))  / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("ProgramFiles(x86)", "")) / "Google/Chrome/Application/chrome.exe",
    ]:
        if p.exists():
            return str(p)
    return None


def get_chrome_profiles():
    state = (Path(os.environ.get("LOCALAPPDATA", ""))
             / "Google/Chrome/User Data/Local State")
    if not state.exists():
        return {}
    try:
        with open(state, encoding="utf-8") as f:
            cache = json.load(f).get("profile", {}).get("info_cache", {})
        return {d: info.get("name", d) for d, info in cache.items()}
    except Exception:
        return {}


def launch(chrome, profile_dir, url):
    subprocess.Popen(
        [chrome, f"--profile-directory={profile_dir}", url],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


# ── Config ────────────────────────────────────────────────────────────────────

def load_config():
    if not CONFIG_PATH.exists():
        return None
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def write_default_config(chrome_profiles):
    CONFIG_PATH.write_text(json.dumps({
        "_info": (
            "Map LLM service names to Chrome profile directory names. "
            f"Your available Chrome profiles: {list(chrome_profiles.keys())}. "
            f"Valid service names: {list(SERVICES.keys())}."
        ),
        "ChatGPT": [],
        "Claude":  [],
        "Gemini":  [],
    }, indent=2), encoding="utf-8")


# ── Tray icon ─────────────────────────────────────────────────────────────────

def create_tray_icon():
    size = 64
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((2, 2, 62, 62), fill="#4f46e5", outline="#3730a3", width=2)
    nodes = [(32, 13), (15, 47), (49, 47)]
    for i, a in enumerate(nodes):
        for b in nodes[i + 1:]:
            draw.line([a, b], fill=(255, 255, 255, 140), width=2)
    for x, y in nodes:
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill="white")
    return img


# ── Popup window ──────────────────────────────────────────────────────────────

def _set_bg(widgets, color):
    for w in widgets:
        try:
            w.config(bg=color)
        except Exception:
            pass


_popup = [None]


def toggle_popup(root, chrome, active, profiles, click_xy):
    # Toggle: if already open, close it
    if _popup[0] is not None:
        try:
            _popup[0].destroy()
        except tk.TclError:
            pass
        _popup[0] = None
        return

    win = tk.Toplevel(root)
    win.withdraw()                  # hide until positioned to avoid top-left flash
    _popup[0] = win
    win.overrideredirect(True)
    win.configure(bg=SEP)           # SEP bleeds through 1px padding as border
    win.attributes("-topmost", True)
    win.resizable(False, False)

    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()

    def close(*_):
        _popup[0] = None
        for w in (win, veil):
            try:
                w.destroy()
            except Exception:
                pass

    # Transparent full-screen overlay catches outside clicks
    veil = tk.Toplevel(root)
    veil.overrideredirect(True)
    veil.attributes("-alpha", 0.01)
    veil.geometry(f"{sw}x{sh}+0+0")
    veil.attributes("-topmost", True)
    veil.bind("<Button-1>", close)
    win.bind("<Escape>", close)

    # ── Outer container (1px inset = visible SEP border) ──────────────────────
    body = tk.Frame(win, bg=BG)
    body.pack(padx=1, pady=1)

    # Enforce minimum width
    tk.Frame(body, bg=BG, width=264, height=0).pack()

    # ── Header ────────────────────────────────────────────────────────────────
    hdr = tk.Frame(body, bg=HEADER)
    hdr.pack(fill="x")

    tk.Label(hdr, text="  LLM Switcher", bg=HEADER, fg=FG,
             font=("Segoe UI", 11, "bold"), anchor="w"
             ).pack(side="left", pady=11)

    x_btn = tk.Label(hdr, text="×", bg=HEADER, fg=MUTED,
                     font=("Segoe UI", 16), cursor="hand2", padx=14)
    x_btn.pack(side="right", pady=6)
    x_btn.bind("<Button-1>", close)
    x_btn.bind("<Enter>", lambda e: x_btn.config(fg=FG))
    x_btn.bind("<Leave>", lambda e: x_btn.config(fg=MUTED))

    tk.Frame(body, bg=SEP, height=1).pack(fill="x")

    # ── Cards ─────────────────────────────────────────────────────────────────
    cards_frame = tk.Frame(body, bg=BG, padx=10, pady=8)
    cards_frame.pack(fill="x")

    for svc, prof_dirs in active.items():
        if svc not in SERVICES:
            continue
        url, color = SERVICES[svc]

        for prof_dir in prof_dirs:
            prof_label = profiles.get(prof_dir, prof_dir)

            # Outer: brand color (shows as 4px left accent via inner padx offset)
            outer = tk.Frame(cards_frame, bg=color, cursor="hand2")
            outer.pack(fill="x", pady=3)

            mid = tk.Frame(outer, bg=CARD)
            mid.pack(fill="x", padx=(4, 0))

            row = tk.Frame(mid, bg=CARD)
            row.pack(fill="x", padx=12, pady=10)

            # Left: stacked name + profile
            text = tk.Frame(row, bg=CARD)
            text.pack(side="left", fill="x", expand=True)

            name_lbl = tk.Label(text, text=svc, fg=FG, bg=CARD,
                                font=("Segoe UI", 10, "bold"), anchor="w")
            name_lbl.pack(fill="x")

            prof_lbl = tk.Label(text, text=prof_label, fg=MUTED, bg=CARD,
                                font=("Segoe UI", 8), anchor="w")
            prof_lbl.pack(fill="x")

            # Right: chevron
            arrow = tk.Label(row, text="›", fg=MUTED, bg=CARD,
                             font=("Segoe UI", 16))
            arrow.pack(side="right", padx=(8, 0))

            hoverable = [mid, row, text, name_lbl, prof_lbl, arrow]

            def click_fn(d=prof_dir, u=url):
                close()
                launch(chrome, d, u)

            def on_enter(_e, ws=hoverable, arr=arrow, c=color):
                _set_bg(ws, HOVER)
                arr.config(fg=c)

            def on_leave(_e, ws=hoverable, arr=arrow):
                _set_bg(ws, CARD)
                arr.config(fg=MUTED)

            for w in hoverable:
                w.bind("<Button-1>", lambda e, fn=click_fn: fn())
                w.bind("<Enter>",    on_enter)
                w.bind("<Leave>",    on_leave)

    # ── Footer ────────────────────────────────────────────────────────────────
    tk.Frame(body, bg=SEP, height=1).pack(fill="x")

    def open_cfg():
        close()
        os.startfile(str(CONFIG_PATH))

    tk.Button(body, text="⚙  Edit Config", command=open_cfg,
              bg=HEADER, fg=MUTED, relief="flat", font=("Segoe UI", 8),
              activebackground=CARD, activeforeground=FG,
              cursor="hand2", bd=0, padx=12, pady=9).pack(fill="x")

    # ── Position: above click point, horizontally centered on it ──────────────
    win.update_idletasks()
    pw = win.winfo_reqwidth()
    ph = win.winfo_reqheight()
    cx, cy = click_xy
    x = max(0, min(cx - pw // 2, sw - pw))
    y = cy - ph - 8
    win.geometry(f"+{x}+{y}")
    win.deiconify()

    veil.lift()
    win.lift()
    win.focus_force()


# ── Bootstrap ─────────────────────────────────────────────────────────────────

def main():
    chrome = find_chrome()
    if not chrome:
        alert("Chrome not found.")
        sys.exit(1)

    chrome_profiles = get_chrome_profiles()
    if not chrome_profiles:
        alert("No Chrome profiles found.")
        sys.exit(1)

    config = load_config()
    if config is None:
        write_default_config(chrome_profiles)
        lines = "\n".join(f"  {d}  →  {n}" for d, n in chrome_profiles.items())
        alert(
            f"Config created:\n{CONFIG_PATH}\n\n"
            f"Your Chrome profiles:\n{lines}\n\n"
            "Edit config.json to map services to profiles, then restart."
        )
        os.startfile(str(CONFIG_PATH))
        sys.exit(0)

    active = {
        k: v for k, v in config.items()
        if not k.startswith("_") and isinstance(v, list) and v
    }
    if not active:
        alert(f"No services configured.\n\nEdit:\n{CONFIG_PATH}")
        os.startfile(str(CONFIG_PATH))
        sys.exit(1)

    root = tk.Tk()
    root.withdraw()

    def on_click(_icon, _item):
        pos = cursor_pos()          # capture immediately on pystray thread
        root.after(0, lambda: toggle_popup(root, chrome, active, chrome_profiles, pos))

    def on_exit(icon, _item):
        icon.stop()
        root.after(0, root.quit)

    tray = pystray.Icon(
        "LLM Switcher",
        create_tray_icon(),
        "LLM Switcher",
        Menu(
            MenuItem("Open Switcher", on_click, default=True),
            Menu.SEPARATOR,
            MenuItem("Edit Config", lambda i, it: os.startfile(str(CONFIG_PATH))),
            MenuItem("Exit",        on_exit),
        ),
    )
    tray.run_detached()
    root.mainloop()


if __name__ == "__main__":
    main()
