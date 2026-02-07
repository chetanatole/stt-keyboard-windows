# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for STT Keyboard (Windows)."""

import os
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

block_cipher = None

# Collect all data and binaries for key packages
datas = []
binaries = []
hiddenimports = []

# Core app modules
hiddenimports += ['mickey', 'mickey.app', 'mickey.recorder',
                  'mickey.transcriber', 'mickey.typer', 'mickey.hotkey',
                  'mickey.config', 'mickey.sounds', 'mickey.permissions',
                  'mickey.tray']

# pynput for hotkeys and typing
tmp_ret = collect_all('pynput')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
hiddenimports += ['pynput.keyboard._win32', 'pynput.mouse._win32', 'pynput._util.win32']

# sounddevice for audio recording
tmp_ret = collect_all('sounddevice')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# faster-whisper for transcription
tmp_ret = collect_all('faster_whisper')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# ctranslate2 (backend for faster-whisper)
tmp_ret = collect_all('ctranslate2')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# tokenizers (for whisper)
tmp_ret = collect_all('tokenizers')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# huggingface_hub (for model download)
hiddenimports += collect_submodules('huggingface_hub')

# numpy and scipy
tmp_ret = collect_all('numpy')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

tmp_ret = collect_all('scipy')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# PyQt6
hiddenimports += ['PyQt6.QtWidgets', 'PyQt6.QtGui', 'PyQt6.QtCore']

# Include .wav sound files
datas += [('mickey/sounds/*.wav', 'mickey/sounds')]

# Include mickey package
datas += [('mickey', 'mickey')]

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'PIL', 'IPython', 'jupyter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='STT Keyboard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='STT Keyboard',
)
