"""Provenance: a plain-text record of what was done to each audio file.

For each audio "name.m4a" the record is "name.sha256", one line per event.
It has no state logic. The program reads it only to check hashes:
  - whether the audio is still the file that was transcribed;
  - whether the reviewed transcript is still the one that produced the subtitles.
"""

import datetime
import hashlib
import os
import re
import subprocess

HASH_PATTERN = re.compile(r"\b([0-9a-f]{64})\b")


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def record_path(base):
    return base + ".sha256"


def append_event(base, event, **fields):
    """Append one line: UTC time, event name, then key=value pairs."""
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    parts = [stamp, event] + [f"{k}={v}" for k, v in fields.items()]
    with open(record_path(base), "a", encoding="utf-8") as f:
        f.write("  ".join(parts) + "\n")


def events(base):
    """Return the record as a list of lines, oldest first. Empty if there is none."""
    path = record_path(base)
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f if line.strip()]


def last_value(base, event, key):
    """Return the value of key in the most recent line for event, or None."""
    for line in reversed(events(base)):
        fields = line.split("  ")
        if len(fields) < 2 or fields[1] != event:
            continue
        m = re.search(rf"\b{re.escape(key)}=(\S+)", line)
        if m:
            return m.group(1)
    return None


def tool_version(repo_dir):
    """Short git commit of this program, or 'unversioned'."""
    try:
        out = subprocess.run(["git", "-C", repo_dir, "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, check=True, timeout=10)
        return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unversioned"
