"""PrimaZi — Server TTS Engine
Supports local Piper execution (ro_RO-mihai-medium) when installed,
with an offline zero-dependency PCM WAV fallback synthesizer.
Includes SHA-256 caching in temporary storage.

Ref: docs/TASKS-WAVE2.md A8, docs/CONTRACTS-WAVE2.md
"""
import hashlib
import io
import logging
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
from typing import Optional, Tuple
import wave

logger = logging.getLogger("primazi.tts")

CACHE_DIR = Path(tempfile.gettempdir()) / "primazi_tts_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_piper_model_path() -> Optional[Path]:
    """Locates the Piper Romanian voice model if present."""
    custom_path = os.getenv("PIPER_MODEL_PATH")
    if custom_path and Path(custom_path).is_file():
        return Path(custom_path)

    standard_paths = [
        Path("models/ro_RO-mihai-medium.onnx"),
        Path.home() / ".local/share/piper-voices/ro/ro_RO/mihai/medium/ro_RO-mihai-medium.onnx",
        Path("/usr/share/piper-voices/ro_RO-mihai-medium.onnx"),
    ]
    for p in standard_paths:
        if p.is_file():
            return p
    return None


def generate_fallback_wav(duration_s: float = 0.5, freq: float = 440.0) -> bytes:
    """Generates a minimal valid PCM 16-bit 16000Hz mono WAV audio file.
    Used when Piper binary or voice models are not present on the host.
    """
    sample_rate = 16000
    num_samples = int(sample_rate * duration_s)
    buf = io.BytesIO()

    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        fade_samples = max(1, int(sample_rate * 0.05))
        samples = []
        for i in range(num_samples):
            # Smooth attack and release envelope to prevent clicks
            if i < fade_samples:
                env = i / fade_samples
            elif i > num_samples - fade_samples:
                env = (num_samples - i) / fade_samples
            else:
                env = 1.0

            val = int(32767.0 * 0.25 * env * math.sin(2.0 * math.pi * freq * (i / sample_rate)))
            samples.append(struct.pack("<h", val))

        wav_file.writeframes(b"".join(samples))

    return buf.getvalue()


def synthesize_speech(
    text: str,
    voice: str = "ro-mihai",
    rate: float = 1.0,
) -> Tuple[bytes, str]:
    """Synthesizes Romanian text into audio WAV bytes.
    Checks SHA-256 cache first. If cache miss, invokes Piper if available,
    otherwise falls back to the internal synthesizer.

    Returns:
        Tuple[bytes, str]: (wav_bytes, engine_name)
    """
    # 1. Check cache
    cache_key = hashlib.sha256(f"{text}:{voice}:{rate:.2f}".encode("utf-8")).hexdigest()
    cached_file = CACHE_DIR / f"{cache_key}.wav"
    if cached_file.is_file() and cached_file.stat().st_size > 44:
        try:
            return cached_file.read_bytes(), "cached"
        except Exception as e:
            logger.warning(f"Failed to read cache file {cached_file}: {e}")

    # 2. Check for Piper executable and voice model
    piper_bin = shutil.which("piper")
    model_path = get_piper_model_path()

    if piper_bin and model_path:
        out_temp = CACHE_DIR / f"temp_{cache_key}.wav"
        try:
            cmd = [
                piper_bin,
                "--model", str(model_path),
                "--output_file", str(out_temp),
            ]
            if rate != 1.0:
                length_scale = round(1.0 / max(0.5, min(2.0, rate)), 2)
                cmd.extend(["--length-scale", str(length_scale)])

            subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                capture_output=True,
                check=True,
                timeout=10,
            )
            if out_temp.is_file() and out_temp.stat().st_size > 44:
                wav_bytes = out_temp.read_bytes()
                out_temp.replace(cached_file)
                return wav_bytes, "piper"
        except Exception as exc:
            logger.warning(f"Piper execution failed ({exc}); falling back to synthesizer.")
        finally:
            if out_temp.exists():
                try:
                    out_temp.unlink()
                except OSError:
                    pass

    # 3. Fallback Synthesizer
    duration = min(max(0.4, len(text) * 0.04), 2.5)
    wav_bytes = generate_fallback_wav(duration_s=duration)

    try:
        cached_file.write_bytes(wav_bytes)
    except Exception as e:
        logger.warning(f"Failed to write cache file {cached_file}: {e}")

    return wav_bytes, "fallback-synthesizer"

