"""Video output with ffmpeg: a black picture with the audio, optionally with burned-in subtitles."""

import os
import shutil
import subprocess
import tempfile


def audio_duration(path):
    """Duration in seconds from ffprobe, or None if it cannot be read."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=60, check=True,
        )
        return float(out.stdout.strip())
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def render_video(audio_path, out_path, subtitles_path=None):
    """Write out_path: a black 640x360 video with the audio.

    If subtitles_path is given, its text is burned in, in yellow.
    ffmpeg runs from the subtitles' folder so the filter needs no path escaping.
    """
    duration = audio_duration(audio_path)
    if not duration:
        raise SystemExit("ERROR: ffprobe cannot read the audio duration.")

    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "lavfi", "-i", "color=c=black:size=640x360:rate=1",
           "-i", os.path.abspath(audio_path), "-t", str(duration)]
    tmpdir = None
    if subtitles_path:
        tmpdir = tempfile.mkdtemp(prefix="whisper_subs_")
        shutil.copyfile(subtitles_path, os.path.join(tmpdir, "subs.srt"))
        cmd += ["-vf", "subtitles=subs.srt:force_style='PrimaryColour=&H00FFFF&'"]
    cmd += ["-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac",
            os.path.abspath(out_path)]
    try:
        subprocess.run(cmd, check=True, cwd=tmpdir)
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)
