# Troubleshooting Guide

This guide helps you diagnose issues with STT Keyboard and collect information for bug reports.

## App is Stuck/Frozen

If the app becomes unresponsive (e.g., stuck showing "R" in the system tray), follow these steps to collect diagnostic information before force-quitting.

### Step 1: Open Task Manager

Press `Ctrl + Shift + Esc` to open Task Manager.

### Step 2: Find the Process

If using the built `.exe`, look for **"STT Keyboard"** in the process list. If running from source, look for **"Python"**.

Note the **PID** (enable the PID column via View > Select Columns if needed).

Alternatively, open Command Prompt or PowerShell and run:
```cmd
:: If using the built .exe
tasklist | findstr "STT Keyboard"

:: If running from source
tasklist | findstr python
```

### Step 3: Force Quit (if needed)

In Task Manager, right-click the process and select "End task".

Or from Command Prompt:
```cmd
taskkill /PID <PID> /F
```

### Step 4: Check the Log File

The app writes logs to:
```
%LOCALAPPDATA%\STTKeyboard\Logs\app.log
```

Open it with:
```cmd
notepad %LOCALAPPDATA%\STTKeyboard\Logs\app.log
```

Look at the last few lines to see what the app was doing when it froze.

### Step 5: Get System Information

Run these commands and save the output:
```cmd
:: Windows version
ver

:: Python version
python --version
```

## Reporting an Issue

When [creating a GitHub issue](https://github.com/chetanatole/stt-keyboard-windows/issues/new), please include:

### Required Information

1. **What happened?**
   - What were you doing when the issue occurred?
   - What state was the tray icon in? (`M` = Ready, `R` = Recording, `P` = Processing)

2. **Log file** (if available)
   - Attach or paste the last 20-30 lines of `%LOCALAPPDATA%\STTKeyboard\Logs\app.log`

3. **System information**
   - Windows version (from `ver` or Settings > System > About)
   - Python version (from `python --version`)

### Issue Template

```markdown
## Description
[Describe what happened]

## Steps to Reproduce
1. [First step]
2. [Second step]
3. [...]

## Expected Behavior
[What should have happened]

## Actual Behavior
[What actually happened]

## Tray Icon State
- [ ] M (Ready)
- [ ] R (Recording)
- [ ] P (Processing)

## System Information
- Windows: [version]
- Python: [version]
- STT Keyboard: [version or commit]

## Attachments
- [ ] app.log (last 20-30 lines)
```

## Common Issues

### Text is not being typed (SendInput method)

**Symptoms:** Transcription completes (log shows "Transcription complete: N chars") but no text appears in the target application.

**Cause:** Some applications may not accept SendInput Unicode events.

**Solution:**
1. Right-click the system tray icon
2. Select "Text Input Method"
3. Switch to "Keystroke"

### Text triggers keyboard shortcuts

**Symptoms:** Transcribed text triggers actions in apps (e.g., "M" mutes YouTube, "." opens github.dev).

**Cause:** The Keystroke input method sends keystrokes that apps interpret as shortcuts.

**Solution:**
1. Right-click the system tray icon
2. Select "Text Input Method"
3. Switch to "SendInput" (the default)

### App crashes on startup (segfault)

**Symptoms:** App immediately closes or shows a segfault error.

**Cause:** DLL conflict between ctranslate2 and PyQt6, or incompatible Python version.

**Solution:**
1. Ensure you are using **Python 3.12** (not 3.13 or 3.14)
2. If running from source, verify with: `python --version`
3. If using the .exe, download the [latest release](https://github.com/chetanatole/stt-keyboard-windows/releases/latest)

### "STT Keyboard is already running"

**Symptoms:** App shows this message and exits.

**Cause:** Another instance of STT Keyboard is already running.

**Solution:**
1. Check the system tray for an existing instance
2. If none visible, open Task Manager and end any "STT Keyboard" (or "Python" if running from source) processes
3. Try launching again

### Microphone not detected

**Symptoms:** Recording fails or captures no audio.

**Solution:**
1. Check Windows Settings > System > Sound > Input
2. Ensure your microphone is enabled and set as default
3. Right-click the tray icon and select a specific input device
4. If microphone access is blocked, go to Settings > Privacy > Microphone and enable access

### Model download is slow

**Symptoms:** First transcription takes a very long time.

**Cause:** Whisper model is being downloaded (~244MB for "small" model).

**Solution:** Wait for the download to complete. The model is cached at `%USERPROFILE%\.cache\huggingface\` and subsequent runs will be fast.

## Reading the Log File

If you're technically inclined, here's what to look for in the log:

### Normal Operation
```
INFO - stt-keyboard.tray - Starting recording
INFO - stt-keyboard.tray - Stopping recording
DEBUG - stt-keyboard.tray - Recorded 32256 audio samples
INFO - stt-keyboard.tray - Starting transcription
INFO - stt-keyboard.tray - Transcription complete: 20 chars
DEBUG - stt-keyboard.tray - Typing text via sendinput
INFO - stt-keyboard.tray - Text typed successfully
```

### Signs of Issues
```
ERROR - stt-keyboard.tray - Transcription failed: ...
ERROR - stt-keyboard.tray - Failed to type text: ...
WARNING - stt-keyboard.app - Attempted to start second instance, exiting
ERROR - stt-keyboard.recorder - Failed to start recording: ...
```
