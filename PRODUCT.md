# STT Keyboard for Windows - Product Overview

## What is STT Keyboard?

STT Keyboard is a Windows system tray application that lets you dictate text anywhere on your PC. Instead of typing, simply hold a key, speak, and your words appear as typed text in any application.

## How It Works

1. **Hold Right Alt key** - Start recording your voice
2. **Speak** - Say what you want to type
3. **Release the key** - Your speech is transcribed and typed automatically

The entire process happens locally on your PC - no internet connection required, no data sent to the cloud.

## Current Features

### Core Functionality
- **Voice-to-text anywhere**: Works in any app - emails, documents, messages, code editors, browsers
- **Local processing**: Uses Whisper AI model running entirely on your device
- **Fast transcription**: Typically 1-2 seconds to process speech after release

### Visual Feedback
- **System tray icon**: Shows current state (M = Ready, R = Recording, P = Processing)
- **Floating indicator**: Dark pill at bottom of screen
  - Appears when recording starts
  - 5-bar waveform animation responds to your voice in real-time
  - White bars while recording, orange while processing

### Audio Feedback
- **Start sound**: Plays when recording begins (mic unmute sound)
- **Stop sound**: Plays when recording ends (mic mute sound)

### Settings (via System Tray Menu)
- **Input Device**: Choose which microphone to use
- **Text Input Method**: Switch between SendInput and Keystroke simulation
- **Transcription Prompt**: Customize the AI prompt for better accuracy with specific terminology
- **Play Sounds**: Toggle audio feedback on/off

## User Experience Flow

```
[Idle] --> Hold Right Alt --> [Recording]
                                  |
                                  | Visual: Floating pill with waveform
                                  | Audio: Start sound plays
                                  |
                              Release key
                                  |
                                  v
                            [Processing]
                                  |
                                  | Visual: Orange waveform animation
                                  | Audio: Stop sound plays
                                  |
                                  v
                          Text typed into app
                                  |
                                  v
                               [Idle]
```

## Requirements

- **Windows 10 or later**: System tray app using PyQt6
- **Microphone**: Required for audio recording
- No special permissions needed (unlike macOS, Windows doesn't require Accessibility permission for global hotkeys or text input)

## Current Limitations

- Windows only (see the macOS version in the stt-keyboard repo)
- Single hotkey (Right Alt) - not customizable
- No way to cancel recording mid-way
- No visual transcript preview before typing
- No editing of transcribed text before insertion
- English-optimized (other languages work but may be less accurate)
- Requires Python 3.12 (3.13+ has ctranslate2 compatibility issues)

## Technical Notes (for context)

- Built with Python
- Uses `faster-whisper` for local AI transcription
- System tray and indicator powered by `PyQt6`
- Hotkey detection via `pynput`
- Audio recording via `sounddevice`
- Text input via Win32 `SendInput` API (Unicode) or `pynput` keystroke simulation
- ctranslate2 must be loaded before PyQt6 to avoid DLL conflicts

---

*Last updated: February 2026*
*Version: 0.1.8*
