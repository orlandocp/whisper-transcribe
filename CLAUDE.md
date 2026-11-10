# CLAUDE.md

Guidance for AI coding assistants working on this repository.

## What this is

A command-line tool that transcribes audio locally with faster-whisper, guides
a person through reviewing the transcript, and produces subtitles and a video.
`README.md` is the reference for behavior. Keep it current when behavior changes.

## Rules

- Keep the code and documentation generic. Do not mention any particular case,
  person, organization, or dataset, and do not put names from real recordings
  in code, docs, comments, or tests.
- Do not hardcode paths to recordings or to a user's folders. The program works
  on the folder it is run from. Machine-specific settings (the Python interpreter,
  the model cache) come from environment variables, set in `whisper-transcribe.cmd`.
- Nothing is sent to external services. The tool is offline by design.
- Never overwrite a file a person may have edited. The `(review).txt.bck` and `(review).srt.bck`
  files are the reference for later steps: keep them.
- There is no status file. The current step comes from which files exist and from
  the hashes in `<name>.sha256`. Do not add a separate state file.
- Install packages only into the project's Python environment, never the system Python.
- All code, comments, and messages are in English.
- File names: lowercase with underscores for Python modules, named for what the
  module does (a verb and a noun, or a noun). Keep the existing names unless the
  change requires a new one.

## Working on the code

- Entry point: `whisper_transcribe.py`. Run it with no arguments to exercise the guided flow.
- Test on a short audio clip copied to a scratch folder, never on real recordings.
  A 20-second clip is enough to check each step.
- Commit messages in English, imperative mood, one logical change per commit.
