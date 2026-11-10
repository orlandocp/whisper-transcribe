"""ffmpeg work: audio duration, progress-reporting runs, and the video output."""

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


def run_ffmpeg(cmd, duration, on_progress=None, cwd=None):
    """Run an ffmpeg command whose output file is its last argument.

    If duration and on_progress are given, ffmpeg's own progress report is read
    and on_progress(fraction) is called with the exact share of the work done.
    """
    if not (on_progress and duration):
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    else:
        cmd = cmd[:-1] + ["-progress", "pipe:1", "-nostats"] + cmd[-1:]
        proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, encoding="utf-8", errors="replace")
        for line in proc.stdout:
            if line.startswith("out_time_us="):
                try:
                    on_progress(int(line.split("=", 1)[1]) / 1_000_000 / duration)
                except ValueError:
                    pass
        stderr = proc.communicate()[1]
        result = subprocess.CompletedProcess(cmd, proc.returncode, "", stderr)
    if result.returncode != 0:
        raise SystemExit(f"ERROR: ffmpeg failed:\n{(result.stderr or '').strip()}")


def render_video(audio_path, out_path, subtitles_path=None, on_progress=None):
    """Write out_path: a black 640x360 video with the audio.

    If subtitles_path is given, its text is burned in, in yellow. The subtitles are
    copied to a temporary folder and ffmpeg runs there, so file names do not matter.
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
        run_ffmpeg(cmd, duration, on_progress, cwd=tmpdir)
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)
