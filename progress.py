"""One progress line for a long step: stage, bar, percent, elapsed time, estimate, detail.

In a terminal the line is redrawn in place. Without a terminal (a log file, a pipe)
a plain line is printed each time another 10% is reached.
"""

import sys
import time

BAR_WIDTH = 30


def clock(seconds):
    seconds = int(seconds)
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


class Progress:
    def __init__(self, stage, stream=None):
        self.stage = stage
        self.stream = stream or sys.stdout
        self.tty = self.stream.isatty()
        self.started = time.time()
        self.width = 0
        self.last_decile = -1

    def _write(self, text):
        self.stream.write(text)
        self.stream.flush()

    def update(self, fraction, detail=""):
        fraction = min(max(fraction, 0.0), 1.0)
        elapsed = time.time() - self.started
        if fraction >= 0.01:
            left = f"left ~{clock(elapsed * (1 - fraction) / fraction)}"
        else:
            left = "left ..."
        filled = int(BAR_WIDTH * fraction)
        bar = "#" * filled + "-" * (BAR_WIDTH - filled)
        line = f"{self.stage:<13} [{bar}] {fraction * 100:3.0f}%  elapsed {clock(elapsed)}  {left}"
        if detail:
            line += f"  {detail[:50]}"
        if self.tty:
            self._write("\r" + line.ljust(self.width))
            self.width = max(self.width, len(line))
        else:
            decile = int(fraction * 10)
            if decile > self.last_decile:
                self.last_decile = decile
                print(line, file=self.stream)

    def finish(self, message=""):
        text = f"{self.stage} done in {clock(time.time() - self.started)}"
        if message:
            text += f": {message}"
        if self.tty:
            self._write("\r" + text.ljust(self.width) + "\n")
        else:
            print(text, file=self.stream)
