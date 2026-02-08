# STT Keyboard for Windows

A Windows system tray app for local speech-to-text transcription. Hold a key, speak, and your words are typed into any application.

**100% local. No cloud. No API keys. Your voice never leaves your PC.**

![Windows](https://img.shields.io/badge/Windows-10%2B-blue)
![Python](https://img.shields.io/badge/Python-3.12-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- **Hold-to-talk** - Hold `Right Alt` key to record, release to transcribe
- **Local processing** - Powered by [faster-whisper](https://github.com/SYSTRAN/faster-whisper), runs entirely on your PC
- **Works anywhere** - Transcribed text is typed directly into the active application
- **Visual feedback** - Floating indicator with audio-reactive waveform
- **Audio feedback** - Start/stop sounds confirm recording state
- **Fast** - Transcription typically completes in 1-2 seconds

## Installation

### Download (Recommended)

1. Download the latest release from the [Releases page](https://github.com/chetanatole/stt-keyboard-windows/releases)
2. Unzip and run `STT Keyboard.exe`

### From Source

```bash
git clone https://github.com/chetanatole/stt-keyboard-windows.git
cd stt-keyboard-windows
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -e .
python -m mickey.app
```

> **Important:** Python 3.12 is required. Python 3.13+ has compatibility issues with ctranslate2.

### Build .exe

```bash
.venv\Scripts\activate
pip install pyinstaller
pyinstaller stt-keyboard.spec
# Output: dist\STT Keyboard.exe
```

## Usage

1. Launch **STT Keyboard** - look for **M** in the system tray
2. **Hold `Right Alt`** to record (you'll see a floating indicator)
3. **Release** to transcribe and type

### Visual Indicator

When recording, a floating pill appears at the bottom of your screen:
- **White waveform** - Recording (responds to your voice)
- **Orange waveform** - Processing transcription

### System Tray Status

- **M** - Ready
- **R** - Recording
- **P** - Processing

## Configuration

Settings are stored at `%APPDATA%\stt-keyboard\config.json`:

```json
{
  "model_size": "small",
  "language": "en",
  "sample_rate": 16000,
  "channels": 1,
  "compute_type": "int8",
  "play_sounds": true,
  "input_device": null,
  "initial_prompt": "Transcription of voice dictation for emails, messages, code comments, and notes. Uses proper punctuation, capitalization, and natural sentence structure.",
  "text_input_method": "sendinput"
}
```

You can also configure via the system tray menu:
- **Input Device** - Select microphone
- **Text Input Method** - Choose between SendInput (default) or Keystroke simulation
- **Edit Transcription Prompt** - Add context for better accuracy (e.g., technical terms)
- **Play Sounds** - Toggle audio feedback

## Text Input Methods

| Method | Description | Best For |
|--------|-------------|----------|
| **SendInput** (default) | Win32 Unicode input via SendInput API | Most applications |
| **Keystroke** | Simulates keystrokes via pynput | Fallback if SendInput doesn't work in a specific app |

## First Run

The first transcription downloads the Whisper model (~244MB) to `%USERPROFILE%\.cache\huggingface\`. Subsequent runs are instant.

## Tech Stack

| Component | Library |
|-----------|---------|
| System tray | [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) |
| Hotkey | [pynput](https://github.com/moses-palmer/pynput) |
| Audio recording | [sounddevice](https://python-sounddevice.readthedocs.io/) |
| Transcription | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) |
| Visual indicator | PyQt6 |

## Requirements

- Windows 10 or later
- Python 3.12 (for running from source)
- ~500MB disk space (app + model)
- Microphone

## Contributing

Contributions welcome! Please use feature branches and PRs.

```bash
git checkout -b feature/your-feature
# make changes
git push -u origin feature/your-feature
gh pr create
```

## License

MIT - see [LICENSE](LICENSE)
