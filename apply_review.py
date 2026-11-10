"""Subtitles from a reviewed transcript.

The reviewed .txt holds the text, one line per segment, as "[h:mm:ss] text".
The raw .srt holds the timing of each segment. This module joins the two:
each raw segment takes the reviewed text whose timestamp is nearest (within
MAX_GAP_SECONDS). Segments with no close reviewed line keep their raw text.
"""

import re

MAX_GAP_SECONDS = 5

TXT_LINE = re.compile(r"\[(\d+):(\d+):(\d+)\]\s*(.*)")
SRT_TIMING = re.compile(r"(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})")


def _seconds(hms):
    h, m, s = hms.split(":")
    return int(h) * 3600 + int(m) * 60 + int(s.split(",")[0])


def read_transcript(path):
    """Return the (seconds, text) pairs of a .txt transcript. Header lines are ignored."""
    entries = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = TXT_LINE.match(line.strip())
            if m:
                h, mi, s, text = m.groups()
                entries.append((int(h) * 3600 + int(mi) * 60 + int(s), text.strip()))
    return entries


def read_srt(path):
    """Return the segments of an .srt file as dicts with start, end, and text."""
    with open(path, encoding="utf-8") as f:
        content = f.read()
    segments = []
    for block in re.split(r"\n\s*\n", content.strip()):
        lines = block.strip().splitlines()
        if len(lines) < 3:
            continue
        m = SRT_TIMING.match(lines[1].strip())
        if not m:
            continue
        start, end = m.groups()
        segments.append({
            "start": start,
            "end": end,
            "start_seconds": _seconds(start),
            "text": " ".join(line.strip() for line in lines[2:]),
        })
    return segments


def join(raw_segments, reviewed_entries):
    """Return (list of (segment, text), reviewed entries that matched no segment)."""
    used = set()
    joined = []
    for seg in raw_segments:
        best_index, best_gap = None, None
        for i, (seconds, _) in enumerate(reviewed_entries):
            if i in used:
                continue
            gap = abs(seconds - seg["start_seconds"])
            if best_gap is None or gap < best_gap:
                best_index, best_gap = i, gap
        if best_index is not None and best_gap <= MAX_GAP_SECONDS:
            used.add(best_index)
            joined.append((seg, reviewed_entries[best_index][1]))
        else:
            joined.append((seg, seg["text"]))
    unmatched = [e for i, e in enumerate(reviewed_entries) if i not in used]
    return joined, unmatched


def write_srt(joined, path):
    with open(path, "w", encoding="utf-8") as f:
        for n, (seg, text) in enumerate(joined, 1):
            f.write(f"{n}\n{seg['start']} --> {seg['end']}\n{text}\n\n")


def changed_lines(raw_path, edited_path):
    """Return (removed, added): entries of the raw transcript and of the edited one that differ."""
    raw = set(read_transcript(raw_path))
    edited = set(read_transcript(edited_path))
    removed = sorted(raw - edited)
    added = sorted(edited - raw)
    return removed, added
