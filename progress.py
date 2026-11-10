"""Live progress in the terminal.

  1/5 Decoding audio: done in 00:00:01        <- finished steps stay on screen
  2/5 Loading model: done in 00:00:05
  Step 3/5: Transcribing                      <- current step
  [#############-----------------]  43%  elapsed 00:00:22  left ~00:00:29

The current step is drawn in two lines that are redrawn in place once per second,
so elapsed and left time keep moving even when no new progress arrives.
Steps with measurable progress show a bar; the others show only elapsed time.
"""

import os
import sys
import threading
import time

BAR_WIDTH = 30
TICK_SECONDS = 1.0
ERASE_LINE = "\r\x1b[2K"   # go to the start of the line and clear it
UP_ONE_LINE = "\x1b[1A"    # move the cursor up one line


def clock(seconds):
    seconds = int(seconds)
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


def _bar(fraction):
    filled = int(BAR_WIDTH * fraction)
    return "#" * filled + "-" * (BAR_WIDTH - filled)


class Monitor:
    def __init__(self, stream=None):
        self.stream = stream or sys.stdout
        if os.name == "nt":
            os.system("")  # enables ANSI escape codes in the Windows console
        self._lock = threading.Lock()
        self._step = None      # dict describing the running step, or None
        self._drawn = False    # True when the cursor is on the detail line of the block
        self._stop = threading.Event()
        self._ticker = threading.Thread(target=self._tick, daemon=True)
        self._ticker.start()

    # ---------------------------------------------------------- public

    def begin_step(self, number, total, name, bar=True):
        with self._lock:
            self._step = {"n": number, "total": total, "name": name, "bar": bar,
                          "started": time.time(), "fraction": 0.0}
            self._render()

    def progress(self, fraction):
        with self._lock:
            if self._step and self._step["bar"]:
                self._step["fraction"] = min(max(fraction, 0.0), 1.0)
                self._render()

    def end_step(self, message=""):
        with self._lock:
            s = self._step
            if s is None:
                return
            elapsed = time.time() - s["started"]
            summary = f"{s['n']}/{s['total']} {s['name']}: done in {clock(elapsed)}"
            if message:
                summary += f" ({message})"
            if self._drawn:
                self._write(UP_ONE_LINE)          # back to the header line
            self._write(ERASE_LINE + summary + "\n")
            self._write(ERASE_LINE)                # clear the old detail line below it
            self._drawn = False                    # the next block starts right here
            self._step = None

    def close(self):
        self._stop.set()
        self._ticker.join(timeout=2)
        with self._lock:
            if self._step is not None:
                self.end_step()

    # ---------------------------------------------------------- internals

    def _tick(self):
        while not self._stop.wait(TICK_SECONDS):
            with self._lock:
                if self._step is not None:
                    self._render()

    def _write(self, text):
        self.stream.write(text)
        self.stream.flush()

    def _rows(self):
        s = self._step
        elapsed = time.time() - s["started"]
        header = f"Step {s['n']}/{s['total']}: {s['name']}"
        if not s["bar"]:
            return header, f"elapsed {clock(elapsed)}"
        f = s["fraction"]
        left = f"left ~{clock(elapsed * (1 - f) / f)}" if f >= 0.01 else "left ..."
        return header, f"[{_bar(f)}] {f * 100:3.0f}%  elapsed {clock(elapsed)}  {left}"

    def _render(self):
        if self._step is None:
            return
        header, detail = self._rows()
        if self._drawn:
            self._write(UP_ONE_LINE)               # up to the header line
        self._write(ERASE_LINE + header + "\n")
        self._write(ERASE_LINE + detail)
        self._drawn = True
