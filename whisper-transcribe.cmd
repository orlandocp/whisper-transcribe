@echo off
rem Runs whisper_transcribe.py with the Python that has faster-whisper installed.
rem Override the interpreter with WHISPER_PYTHON, and the model cache with HF_HOME.
if not defined WHISPER_PYTHON set "WHISPER_PYTHON=D:\venv-whisper\Scripts\python.exe"
if not defined HF_HOME set "HF_HOME=D:\huggingface-cache"
set "HF_HUB_DISABLE_XET=1"
"%WHISPER_PYTHON%" "%~dp0whisper_transcribe.py" %*
