"""A single progress bar for one step: step label, bar, percent, elapsed time and time left.

In a terminal the same line is redrawn in place, at most twice a second.
Without a terminal (a log file, a pipe), one plain line is printed at each 10%.
"""

import sys
import time

BAR_WIDTH = 30
REDRAW_SECONDS = 0.5


def clock(seconds):
    seconds = int(seconds)
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


class Progress:
    def __init__(self, label, stream=None):
        self.label = label
        self.stream = stream or sys.stdout
        self.tty = self.stream.isatty()
        self.started = time.time()
        self.last_draw = 0.0
        self.width = 0
        self.last_decile = -1

    def _write(self, text):
        self.stream.write(text)
        self.stream.flush()

    def update(self, fraction):
        fraction = min(max(fraction, 0.0), 1.0)
        now = time.time()
        elapsed = now - self.started
        if self.tty:
            if fraction < 1.0 and now - self.last_draw < REDRAW_SECONDS:
                return
            self.last_draw = now
        else:
            decile = int(fraction * 10)
            if decile <= self.last_decile and fraction < 1.0:
                return
            self.last_decile = decile

        if fraction >= 0.01:
            left = f"left ~{clock(elapsed * (1 - fraction) / fraction)}"
        else:
            left = "left ..."
        filled = int(BAR_WIDTH * fraction)
        bar = "#" * filled + "-" * (BAR_WIDTH - filled)
        line = (f"{self.label:<26} [{bar}] {fraction * 100:3.0f}%  "
                f"elapsed {clock(elapsed)}  {left}")
        if self.tty:
            self._write("\r" + line.ljust(self.width))
            self.width = max(self.width, len(line))
        else:
            print(line, file=self.stream)

    def finish(self, message=""):
        text = f"{self.label} done in {clock(time.time() - self.started)}"
        if message:
            text += f": {message}"
        if self.tty:
            self._write("\r" + text.ljust(self.width) + "\n")
        else:
            print(text, file=self.stream)
