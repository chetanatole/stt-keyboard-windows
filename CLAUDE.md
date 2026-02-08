# CLAUDE.md

## Project Overview

STT Keyboard is a Windows system tray app for local speech-to-text transcription. Users hold the Right Alt key to record, then release to transcribe and type the result into the active application.

## Commands

```bash
# Run in development
.venv\Scripts\activate && python -m mickey.app

# Or use script
scripts\run.bat

# Build .exe (requires PyInstaller)
scripts\build.bat

# Lint
ruff check mickey/
ruff format --check mickey/

# Format
ruff format mickey/

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ -v --cov=mickey --cov-report=term-missing
```

## Architecture

```
app.py (entry)
    └── tray.py (MickeyApp - PyQt6 QSystemTrayIcon)
            ├── hotkey.py (pynput listener thread)
            ├── recorder.py (sounddevice/WASAPI)
            ├── transcriber.py (faster-whisper, pre-loaded before Qt)
            ├── typer.py (Win32 SendInput or keystroke simulation)
            └── indicator.py (PyQt6 floating waveform indicator)
```

**Critical: ctranslate2 must be loaded BEFORE PyQt6** to avoid DLL conflicts that cause segfaults. The model is pre-loaded in `app.py` before importing `tray.py`.

**Threading Pattern**: The pynput hotkey listener runs on a separate thread. Actions are dispatched to the main Qt thread via `QTimer` polling `_pending_start`/`_pending_stop` flags. Transcription results use `pyqtSignal` for thread-safe GUI updates.

**State Machine**: Tray icon shows current state:
- `M` = Ready (idle)
- `R` = Recording (hotkey held)
- `P` = Processing (transcribing)

## Key Components

- **tray.py**: Main app class, PyQt6 QSystemTrayIcon, coordinates all components
- **hotkey.py**: Global Right Alt key listener using pynput
- **recorder.py**: Audio capture using sounddevice (WASAPI on Windows)
- **transcriber.py**: Lazy-loads faster-whisper model, transcribes audio
- **typer.py**: Text insertion with two methods:
  - `sendinput` (default): Win32 SendInput with Unicode events
  - `keystroke`: pynput keystroke simulation
- **indicator.py**: Floating waveform indicator (PyQt6 frameless QWidget)
- **sounds.py**: Bundled mic mute/unmute WAV sounds via winsound
- **permissions.py**: Microphone permission check via sounddevice
- **config.py**: JSON config at `%APPDATA%/stt-keyboard/config.json`

## Git Workflow

**Always use feature branches + PRs. Never commit directly to main.**

```bash
git checkout -b feature/your-feature-name
git add .
git commit -m "Description of changes"
git push -u origin feature/your-feature-name
gh pr create --title "Feature title" --body "Description"
```

## CI

CI runs on push/PR to main:
- `ruff check` and `ruff format --check` for linting
- Tests with coverage reporting (80% minimum on testable modules)
- On PRs: `diff-cover` requires 80% coverage on changed files
- Import verification on Windows runner

## Testing

Tests are in `tests/` using pytest. Coverage configuration is in `pyproject.toml`.

**Testable modules** (80% coverage required):
- config.py, hotkey.py, sounds.py, transcriber.py, typer.py

**Excluded from coverage** (UI/hardware components):
- app.py, indicator.py, tray.py, permissions.py, recorder.py
