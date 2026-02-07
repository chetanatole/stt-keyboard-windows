@echo off
call .venv\Scripts\activate
pyinstaller stt-keyboard.spec
