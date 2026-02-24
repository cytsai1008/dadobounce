# Dadobounce

Say hi to Dado in the Windows system tray!

## Requirements

- Windows

## How to use

1. Download `dadobounce.exe` and run it. If you see any warning, accept it. (You can also build it yourself if you prefer not to use the prebuilt executable.)
2. To start the app automatically when Windows starts:
   - Right-click `dadobounce.exe` and choose **Create shortcut**
   - Press `Win + R`, type `shell:startup`, then press Enter to open the Startup folder
   - Copy (or move) the shortcut into that folder

## Build

### Requirements

- [uv](https://github.com/astral-sh/uv) is required
- Setup virtual environment by using

```bash
uv sync --extra dev
```

### Steps

To build the executable, run:

```bash
uv run pyinstaller dadobounce.spec
```

The output will be at `dist/dadobounce.exe`.