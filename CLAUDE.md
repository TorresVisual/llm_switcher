# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**llm-switcher** is a Windows system tray app that opens AI/LLM services in a specific Chrome profile. Left-clicking the tray icon shows a dark-themed popup switcher. Single-file Python app compiled to `.exe` via PyInstaller.

## Commands

**Run directly (development):**
```bash
python llm_switcher.py
```

**Build executable:**
```bash
python build.py
# Output: dist/gpt_tray.exe
```

No `requirements.txt` — dependencies (`pystray`, `Pillow`) must be installed manually. `tkinter` is part of the Python standard library.

## Architecture

Everything lives in [llm_switcher.py](llm_switcher.py). No modules or classes.

**Runtime flow:**
1. `main()` locates Chrome via the Windows registry with filesystem fallbacks.
2. Reads `%LOCALAPPDATA%\Google\Chrome\User Data\Local State` → `profile.info_cache` to get all Chrome profiles (`{directory: display_name}`).
3. Loads `config.json` (next to the exe/script). If absent, writes a template and exits — first-run setup.
4. Filters `config.json` to only services with at least one profile directory configured (`active`).
5. Runs pystray detached (background thread) + tkinter mainloop on the main thread. `root.after(0, ...)` bridges tray callbacks to the main thread safely.
6. Left-click tray → `toggle_popup()` — opens or closes the popup window.

**Popup window (`toggle_popup`):**
- `overrideredirect(True)` removes the title bar; `bg=SEP` + `inner.pack(padx=1, pady=1)` creates a 1px border effect.
- A near-transparent full-screen `veil` Toplevel sits behind the popup and closes it on any outside click.
- Each service card uses `outer(bg=color) + mid(bg=CARD, padx=(3,0))` to produce a 3px brand-colored left accent bar without `place()`.
- Hover: `_set_bg(widgets, HOVER)` on `<Enter>` / `<Leave>` bound to all child widgets in each card.
- Positioned bottom-right above the taskbar: `+{sw - w - 14}+{sh - h - 54}`.

**Config (`config.json`):**
```json
{
  "ChatGPT": ["Default"],
  "Claude":  ["Profile 1"],
  "Gemini":  ["Profile 2"]
}
```
Keys are service names (must match `SERVICES` dict). Values are Chrome profile directory names (e.g. `"Default"`, `"Profile 1"`). Multiple directories per service → one card per profile with `"Service · ProfileName"` label.

**Adding a new service:** Add an entry to the `SERVICES` dict at the top: `"Name": ("url", "#hexcolor")`.

## Platform Constraints

- **Windows-only** — uses `winreg` and Chrome paths under `%LOCALAPPDATA%` / `%PROGRAMFILES%`.
- `APP_DIR` resolves to the exe directory when frozen (`sys.frozen`) or the script directory otherwise — `config.json` lives there.

## PyInstaller Config

[llm_switcher.spec](llm_switcher.spec) produces a single-file, windowed (no console) executable. `build/` and `dist/` are git-ignored.
