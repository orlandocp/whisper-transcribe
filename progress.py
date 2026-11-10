"""Two progress lines: the total of the measurable work, and the current step.

  Total (decode + transcription)  [#########-----------------]  31%  elapsed ...  left ~...
  3/5 Transcribing                [###-----------------------]  12%  elapsed ...  left ~...

The total only counts steps whose time can be measured as they run: decoding the
audio and transcribing. Its share comes from the speed measured on this run, so it is
shown as "estimating..." until transcription has processed a little audio.
Loading the model and rendering video are not part of the total: they have no
measurable progress before they start.

In a terminal the two lines are redrawn in place, at most twice a second.
Without a terminal, the lines are printed each time the current step reaches a new 10%.
"""

import os
import sys
import time

BAR_WIDTH = 30
REDRAW_SECONDS = 0.5
TOTAL_LABEL = "Total (decode + transcription)"
FORECAST_MIN = 0.02  # do not estimate the total from less than 2% of the audio


def clock(seconds):
    seconds = int(seconds)
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


def _bar(fraction):
    filled = int(BAR_WIDTH * fraction)
    return "#" * filled + "-" * (BAR_WIDTH - filled)


class Monitor:
    def __init__(self, show_total=True, stream=None):
        self.stream = stream or sys.stdout
        self.tty = self.stream.isatty()
        self.show_total = show_total
        if self.tty and os.name == "nt":
            os.system("")  # enables ANSI escape codes in the Windows console
        self.counted_done = 0.0      # seconds of finished steps that count toward the total
        self.total = None            # fraction of the total, or None while estimating
        self.label = ""
        self.has_bar = False
        self.counts = False
        self.forecast = False
        self.fraction = None
        self.finished = False
        self.step_started = time.time()
        self.started = time.time()
        self.widths = [0, 0]
        self.drawn = False
        self.last_draw = 0.0
        self.last_decile = -1

    # ---------------------------------------------------------- public

    def begin_step(self, label, bar=True, counts=False, forecast=False):
        """counts: the step's time is part of the total. forecast: the total is estimated from it."""
        self.label, self.has_bar = label, bar
        self.counts, self.forecast = counts, forecast
        self.fraction = 0.0 if bar else None
        self.finished = False
        self.step_started = time.time()
        self.last_decile = -1
        self._draw(force=True)

    def progress(self, fraction):
        self.fraction = min(max(fraction, 0.0), 1.0)
        if self.forecast:
            self._forecast()
        self._draw()

    def end_step(self):
        if self.counts:
            self.counted_done += time.time() - self.step_started
        if self.forecast:
            self.total = 1.0
        self.fraction = 1.0 if self.has_bar else None
        self.finished = True
        self._draw(force=True)

    def close(self):
        if self.tty:
            self.stream.write("\n")
            self.stream.flush()

    # ---------------------------------------------------------- internals

    def _forecast(self):
        f = self.fraction
        if f < FORECAST_MIN:
            self.total = None
            return
        e = time.time() - self.step_started
        # measured: the total so far, and the time the rest of this step will take at this speed
        self.total = min(1.0, (self.counted_done + e) / (self.counted_done + e / f))

    def _total_row(self):
        if self.total is None:
            return f"{TOTAL_LABEL:<32} estimating..."
        elapsed = self.counted_done + (time.time() - self.step_started if self.counts else 0.0)
        t = self.total
        left = f"left ~{clock(elapsed * (1 - t) / t)}" if t >= 0.01 else "left ..."
        return (f"{TOTAL_LABEL:<32} [{_bar(t)}] {t * 100:3.0f}%  "
                f"elapsed {clock(elapsed)}  {left}")

    def _step_row(self):
        e = time.time() - self.step_started
        if not self.has_bar:
            return f"{self.label:<32} elapsed {clock(e)}"
        if self.finished:
            return f"{self.label:<32} [{_bar(1.0)}] 100%  done in {clock(e)}"
        f = self.fraction
        left = f"left ~{clock(e * (1 - f) / f)}" if f >= 0.01 else "left ..."
        return (f"{self.label:<32} [{_bar(f)}] {f * 100:3.0f}%  "
                f"elapsed {clock(e)}  {left}")

    def _rows(self):
        return [self._total_row(), self._step_row()] if self.show_total else [self._step_row()]

    def _write(self, text):
        self.stream.write(text)
        self.stream.flush()

    def _draw(self, force=False):
        now = time.time()
        if self.tty:
            if not force and now - self.last_draw < REDRAW_SECONDS:
                return
            self.last_draw = now
            rows = self._rows()
            if self.drawn and len(rows) == 2:
                self._write("\x1b[1A")  # move up to the total line
            for i, row in enumerate(rows):
                self.widths[i] = max(self.widths[i], len(row))
                end = "\n" if (i == 0 and len(rows) == 2) else ""
                self._write("\r" + row.ljust(self.widths[i]) + end)
            self.drawn = True
        else:
            decile = int(self.fraction * 10) if self.has_bar and self.fraction is not None else -1
            if force or decile > self.last_decile:
                if decile >= 0:
                    self.last_decile = decile
                for row in self._rows():
                    print(row, file=self.stream)
