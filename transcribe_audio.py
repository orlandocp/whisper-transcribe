"""Speech-to-text with faster-whisper: an audio file in, timed text segments out.

Nothing is written here. The caller decides where results go.
"""

import os
import shutil
import subprocess
import tempfile

from render_video import audio_duration

CHUNK_SECONDS = 10 * 60  # long audio is processed in blocks to bound memory use

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

    device, compute_type = pick_device()
    log(f"Loading model '{model_name}' on {device} ({compute_type})...")
    cached = cached_model_path(model_name)
    if cached:
        log(f"Model found in the local cache: {cached}")
    else:
        log("Model not in the local cache: downloading it now (about 1.5 GB, only once).")
    model = WhisperModel(model_name, device=device, compute_type=compute_type)

    def run(path):
        segments, info = model.transcribe(
            path,
            language=language,
            beam_size=5,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
            condition_on_previous_text=False,
        )
        return segments, info

    duration = audio_duration(audio_path)
    result = []
    detected = None

    if not duration or duration <= CHUNK_SECONDS:
        segments, info = run(audio_path)
        detected = info
        for s in segments:
            result.append((s.start, s.end, s.text.strip()))
    else:
        blocks = int(duration // CHUNK_SECONDS) + (1 if duration % CHUNK_SECONDS else 0)
        log(f"Long recording: {blocks} blocks of 10 minutes.")
        tmpdir = tempfile.mkdtemp(prefix="whisper_blocks_")
        try:
            for i in range(blocks):
                offset = i * CHUNK_SECONDS
                block = os.path.join(tmpdir, f"block_{i:03d}.wav")
                subprocess.run(
                    ["ffmpeg", "-y", "-loglevel", "error", "-i", audio_path,
                     "-ss", str(offset), "-t", str(CHUNK_SECONDS),
                     "-ar", "16000", "-ac", "1", block],
                    check=True,
                )
                segments, info = run(block)
                if detected is None:
                    detected = info
                log(f"  block {i + 1}/{blocks} (starts at {offset // 60} min)")
                for s in segments:
                    result.append((s.start + offset, s.end + offset, s.text.strip()))
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    result = [seg for seg in result if seg[2]]
    info = {
        "language": detected.language if detected else language,
        "language_probability": round(detected.language_probability, 2) if detected else None,
        "device": device,
        "compute_type": compute_type,
    }
    return result, info
