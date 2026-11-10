# whisper-transcribe — guided local transcription

Transcribes audio on your own computer with [faster-whisper](https://github.com/SYSTRAN/faster-whisper).
Nothing is uploaded: the audio never leaves the machine.

You run one command, `whisper-transcribe`, in a folder that holds an audio file.
The program tells you what to do next. You do not need to remember any option.

## Requirements

- Windows, with Python 3.12. The wrapper script `whisper-transcribe.cmd` is written for Windows.
- `ffmpeg` and `ffprobe` on the `PATH`.
- The Python package `faster-whisper`, and optionally `torch` with CUDA for GPU use.
- No GPU is required. Without one, the program runs on the CPU, which is slower.

## Setup

Clone the repository and create a Python environment for it:

```powershell
git clone <REPOSITORY-URL> whisper-transcribe
py -3.12 -m venv D:\venv-whisper
D:\venv-whisper\Scripts\python -m pip install faster-whisper
```

For GPU use, install a CUDA build of `torch` into the same environment.

The wrapper reads two settings from environment variables. If they are not set, it uses these defaults:

| Variable | Default | Purpose |
|---|---|---|
| `WHISPER_PYTHON` | `D:\venv-whisper\Scripts\python.exe` | Python that has faster-whisper |
| `HF_HOME` | `D:\huggingface-cache` | where the model files are cached |

The first time a model is used, it is downloaded (about 1.5 GB for `large-v3-turbo`).
After that, the program works offline.

To run `whisper-transcribe` from any folder, double-click `add-to-path.cmd` in the repository folder.
It adds the folder to your user `PATH`. Open a new terminal afterwards.

## Use

Open a terminal in the folder that holds the audio file, and run:

```powershell
whisper-transcribe
```

Supported audio: `.m4a`, `.mp3`, `.wav`, `.ogg`, `.opus`, `.aac`, `.flac`.
If the folder has more than one audio file, the program asks which one to use.

The program then works in steps. Each time you run it, it checks which files exist next to the audio and continues from there.

1. **Transcribe.** It asks which model to use (Enter keeps `large-v3-turbo`). It creates the transcript, the automatic subtitles, and a review video that shows those subtitles.
2. **Review.** Correct `<name> (review).txt` by listening to the audio. Run `whisper-transcribe` again. It shows every change and asks you to confirm.
   If you did not change anything, it asks you to confirm that the automatic transcript is official as it is.
   Then it creates the subtitles.
3. **Video.** It offers to render the video with the subtitles burned in.

Run it again at any time. If the transcript or the audio changed since the last run, it tells you.

### Model choice

| Model | Speed | Accuracy |
|---|---|---|
| `large-v3-turbo` (default) | faster | close to `large-v3` |
| `large-v3` | slower | the most accurate of the two |

## Files

For an audio file named `<name>.m4a`, the program creates these files in the same folder:

| File | Created | Meaning |
|---|---|---|
| `<name> (review).txt.bck` | transcribe | copy of the transcript before review. Do not edit it. |
| `<name> (review).srt.bck` | transcribe | copy of the subtitles before review. Keeps the timing. |
| `<name> (review).txt` | transcribe | the transcript you correct by hand. Exists only while reviewing. |
| `<name> (review).mp4` | transcribe | video with the audio and the automatic subtitles, for review |
| `<name>.txt` | review | the official transcript: your reviewed text |
| `<name>.srt` | review | the official subtitles, made from your reviewed text |
| `<name>.mp4` | review or later | the official video, with the subtitles burned in |
| `<name>.sha256` | every step | plain-text record: hashes, model, date, and the steps run |

The name says the stage: `(review)` means the file is still being reviewed. A name without
`(review)` is official. Confirming the review renames `(review).txt` to `<name>.txt`.
To correct an official transcript, run the program and choose to reopen the review: it creates
`(review).txt` again as a copy of the official one.

### Progress

The terminal shows the steps as they finish, and the current step below them:

```
1/5 Decoding audio: done in 00:00:01
2/5 Loading model: done in 00:00:05
Step 3/5: Transcribing
[#############-----------------]  43%  elapsed 00:00:22  left ~00:00:29
```

The current step's bar shows real progress where it can be measured: decoding, transcribing and
rendering video. Loading the model and writing files show only elapsed time. The time left is
estimated from the speed measured so far in that step. Elapsed and left time update every second.

This needs a terminal that redraws in place, such as Windows Terminal or the classic console.

### Model choice

| Model | Speed | Accuracy |
|---|---|---|
| `large-v3-turbo` (default) | faster | close to `large-v3` |
| `large-v3` | slower | the most accurate of the two |

## Files

For an audio file named `<name>.m4a`, the program creates these files in the same folder:

| File | Created | Meaning |
|---|---|---|
| `<name> (review).txt.bck` | transcribe | copy of the transcript before review. Do not edit it. |
| `<name> (review).srt.bck` | transcribe | copy of the subtitles before review. Keeps the timing. |
| `<name> (review).txt` | transcribe | the transcript you correct by hand. Exists only while reviewing. |
| `<name> (review).mp4` | transcribe | video with the audio and the automatic subtitles, for review |
| `<name>.txt` | review | the official transcript: your reviewed text |
| `<name>.srt` | review | the official subtitles, made from your reviewed text |
| `<name>.mp4` | review or later | the official video, with the subtitles burned in |
| `<name>.sha256` | every step | plain-text record: hashes, model, date, and the steps run |

The name says the stage: `(review)` means the file is still being reviewed. A name without
`(review)` is official. Confirming the review renames `(review).txt` to `<name>.txt`.
To correct an official transcript, run the program and choose to reopen the review: it creates
`(review).txt` again as a copy of the official one.

### Progress

Two lines show the work:

- **Total (decode + transcription)**: the measurable work of the whole run. Its share is
  estimated from the speed measured on this run, so it reads "estimating..." until transcription
  has processed a little audio.
- **The current step**: its own bar when it has measurable progress (decoding, transcribing,
  rendering video). Loading the model shows only its elapsed time, because it has no measurable progress.

Loading the model and rendering video are not part of the total.

### Model choice

| Model | Speed | Accuracy |
|---|---|---|
| `large-v3-turbo` (default) | faster | close to `large-v3` |
| `large-v3` | slower | the most accurate of the two |

## Files

For an audio file named `<name>.m4a`, the program creates these files in the same folder:

| File | Created | Meaning |
|---|---|---|
| `<name> (review).txt.bck` | transcribe | copy of the transcript before review. Do not edit it. |
| `<name> (review).srt.bck` | transcribe | copy of the subtitles before review. Keeps the timing. |
| `<name> (review).txt` | transcribe | the transcript you correct by hand. Exists only while reviewing. |
| `<name> (review).mp4` | transcribe | video with the audio and the automatic subtitles, for review |
| `<name>.txt` | review | the official transcript: your reviewed text |
| `<name>.srt` | review | the official subtitles, made from your reviewed text |
| `<name>.mp4` | review or later | the official video, with the subtitles burned in |
| `<name>.sha256` | every step | plain-text record: hashes, model, date, and the steps run |

The name says the stage: `(review)` means the file is still being reviewed. A name without
`(review)` is official. Confirming the review renames `(review).txt` to `<name>.txt`.
To correct an official transcript, run the program and choose to reopen the review: it creates
`(review).txt` again as a copy of the official one.

### Progress

Each long step shows a bar with its own exact progress: decoding the audio, transcribing,
and rendering video. Loading the model has no progress information, so it shows only the time.
The whole recording is transcribed in one pass, so the bar is continuous.

There is no status file. The program knows the step from which files exist and from `<name>.sha256`:
a `subtitles` entry there means a review was confirmed.

### What the record contains

`<name>.sha256` has one line per step, for example:

```
2026-11-10 13:42:12 UTC  transcribed  audio_sha256=…  model=large-v3-turbo  language=es  device=cuda  compute=int8  faster_whisper=1.2.1  program=<commit>
2026-11-10 13:42:20 UTC  subtitles    txt_sha256=…  srt_sha256=…  changed_lines=3  unchanged_confirmed=no  unmatched=0
```

It is for anyone who needs to know how a transcript was produced: which audio file (by hash),
which model, which version of the program, and whether the reviewed text was confirmed.

## How the review is matched to the subtitles

The subtitles keep the timing of the automatic transcript. For each subtitle segment, the program takes the reviewed line whose `[h:mm:ss]` is nearest, within 5 seconds.
If a reviewed line matches no segment, the program lists it and does not use it.
So keep the timestamp at the start of each line, and do not add or move lines in time.

## Project layout

```
whisper_transcribe.py   the guided program: the only entry point
transcribe_audio.py     speech to text with faster-whisper
apply_review.py         reviewed transcript + timing to subtitles
render_video.py         black video with audio, optionally with subtitles
provenance.py           hashes and the <name>.sha256 record
whisper-transcribe.cmd  Windows wrapper: sets environment variables, runs the program
add-to-path.cmd         double-click once: adds this folder to the user PATH
progress.py             one progress line per step: stage, bar, percent, time left
CLAUDE.md               guidance for AI assistants working on this code
```

## License

Not yet chosen.
