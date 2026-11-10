"""Speech to text with faster-whisper: an audio file in, timed text segments out.

The audio is decoded once to 16 kHz mono and transcribed as a whole, so the
progress bar covers the entire recording. Nothing is written except a temporary
decoded copy, which is removed afterwards.
"""

import os
import shutil
import tempfile
import time

from progress import Progress, clock
from render_video import audio_duration, run_ffmpeg

MODELS = {
    "large-v3-turbo": "faster, close to large-v3 quality",
    "large-v3": "most accurate, slower",
}
DEFAULT_MODEL = "large-v3-turbo"


def pick_device():
    """Return (device, compute_type) for this machine. The model is not chosen here."""
    try:
        import torch
        if torch.cuda.is_available():
            vram = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
            # float16 needs a few GB of VRAM; int8 fits in smaller cards
            return "cuda", ("float16" if vram >= 6 else "int8")
    except ImportError:
        pass
    except Exception:  # broken driver or CUDA install: fall back to CPU
        pass
    return "cpu", "int8"


def cached_model_path(model_name):
    """Local path of the model if it is already downloaded, otherwise None. Never downloads."""
    try:
        from faster_whisper.utils import download_model
        return download_model(model_name, local_files_only=True)
    except Exception:
        return None


def transcribe_audio(audio_path, model_name, language, log=print):
    """Return (segments, info). segments is a list of (start_seconds, end_seconds, text)."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise SystemExit("ERROR: faster-whisper is not installed in this Python. See README, Setup.")

    duration = audio_duration(audio_path)
    workdir = tempfile.mkdtemp(prefix="whisper_")
    try:
        wav = os.path.join(workdir, "audio_16k.wav")
        decode = Progress("1/5 Decoding audio")
        run_ffmpeg(["ffmpeg", "-y", "-loglevel", "error", "-i", audio_path,
                    "-ar", "16000", "-ac", "1", wav],
                   duration, decode.update)
        decode.finish()

        device, compute_type = pick_device()
        cached = cached_model_path(model_name)
        where = "found in the local cache" if cached else "NOT in the local cache: downloading (about 1.5 GB, once)"
        log(f"Model '{model_name}' on {device} ({compute_type}): {where}")
        if cached:
            log(f"  {cached}")
        started = time.time()
        model = WhisperModel(model_name, device=device, compute_type=compute_type)
        log(f"Model loaded in {clock(time.time() - started)}")

        segments, info = model.transcribe(
            wav,
            language=language,
            beam_size=5,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
            condition_on_previous_text=False,
        )
        total = info.duration or duration or 0
        bar = Progress("3/5 Transcribing")
        result = []
        for s in segments:
            text = s.text.strip()
            if text:
                result.append((s.start, s.end, text))
            if total:
                bar.update(s.end / total)
        bar.finish(f"{len(result)} segments")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    return result, {
        "language": info.language,
        "language_probability": round(info.language_probability, 2),
        "device": device,
        "compute_type": compute_type,
    }
