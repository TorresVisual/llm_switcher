# LLM Switcher

A Windows system tray app that opens AI/LLM services in a specific Chrome profile with one click.

![tray icon](https://img.shields.io/badge/platform-Windows-blue) ![python](https://img.shields.io/badge/python-3.10%2B-blue)

## What it does

Left-click the tray icon to open a popup switcher. Each card shows a service and which Chrome profile it opens in. Click a card to launch that service directly in the right profile — no manual profile switching.

Supports: **ChatGPT**, **Claude**, **Gemini**, **Perplexity**, **GitHub Copilot**, **Grok**, **WolframAlpha**

## Setup

**1. Install dependencies**

```bash
pip install pystray Pillow
```

**2. Run the app**

```bash
python llm_switcher.py
```

On first run, a `config.json` template is created next to the script and opened automatically. The app will show you your available Chrome profile directory names.

**3. Edit `config.json`**

Map each service to one or more Chrome profile directories:

```json
{
  "ChatGPT": ["Default"],
  "Claude":  ["Profile 1"],
  "Gemini":  ["Profile 2"]
}
```

- Keys must match a supported service name (see list above)
- Values are Chrome profile directory names (e.g. `"Default"`, `"Profile 1"`, `"Profile 3"`)
- Multiple profiles per service → one card per profile in the popup
- Omit a service or leave its list empty to hide it

**4. Restart the app** — the tray icon appears in the system tray.

## Usage

| Action | Result |
|---|---|
| Left-click tray icon | Open/close the switcher popup |
| Click a service card | Launch the URL in that Chrome profile |
| Right-click tray icon | Open Switcher / Edit Config / Exit |
| Click ⚙ Edit Config in popup | Open `config.json` in the default editor |
| Esc or outside click | Close the popup |

## Build executable

```bash
python build.py
```

Output: `dist/gpt_tray.exe` — single file, no console, no installer needed. Place `config.json` in the same directory as the exe.

## Adding a new service

Edit the `SERVICES` dict in [llm_switcher.py](llm_switcher.py):

```python
SERVICES = {
    "MyService": ("https://myservice.com/", "#hexcolor"),
    ...
}
```

Then add it to `config.json` with your profile directories.

## Requirements

- Windows (uses `winreg` and Chrome's `%LOCALAPPDATA%` paths)
- Google Chrome installed
- Python 3.10+ with `pystray` and `Pillow`
