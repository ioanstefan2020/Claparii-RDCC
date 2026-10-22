"""app/audio/captions.py - SubRip (SRT) and WebVTT caption generator.

Standards:
- SRT: HH:MM:SS,mmm with comma millisecond delimiter.
- WebVTT: WEBVTT header and HH:MM:SS.mmm with dot millisecond delimiter.
"""

from app.schemas.transcribe import TranscribeSegment


def format_timestamp(seconds: float, delimiter: str = ",") -> str:
    """Format seconds into HH:MM:SS{delim}mmm.

    Args:
        seconds: Time offset in seconds (floats).
        delimiter: Milliseconds delimiter (',' for SRT, '.' for WebVTT).

    Returns:
        Formatted timestamp string.
    """
    if seconds < 0:
        seconds = 0.0

    total_ms = int(round(seconds * 1000))
    hours = total_ms // 3_600_000
    remaining_ms = total_ms % 3_600_000
    minutes = remaining_ms // 60_000
    remaining_ms %= 60_000
    secs = remaining_ms // 1_000
    ms = remaining_ms % 1_000

    return f"{hours:02d}:{minutes:02d}:{secs:02d}{delimiter}{ms:03d}"


def segments_to_srt(segments: list[TranscribeSegment]) -> str:
    """Convert timestamped segments into SubRip (.srt) caption string.

    Format:
    1
    00:00:00,000 --> 00:00:04,200
    Text line...
    """
    if not segments:
        return ""

    cues: list[str] = []
    for idx, seg in enumerate(segments, start=1):
        start_ts = format_timestamp(seg.start, delimiter=",")
        end_ts = format_timestamp(seg.end, delimiter=",")
        text = seg.text.strip()
        cues.append(f"{idx}\n{start_ts} --> {end_ts}\n{text}")

    return "\n\n".join(cues) + "\n"


def segments_to_vtt(segments: list[TranscribeSegment]) -> str:
    """Convert timestamped segments into WebVTT (.vtt) caption string.

    Format:
    WEBVTT

    00:00:00.000 --> 00:00:04.200
    Text line...
    """
    header = "WEBVTT\n\n"
    if not segments:
        return header

    cues: list[str] = []
    for seg in segments:
        start_ts = format_timestamp(seg.start, delimiter=".")
        end_ts = format_timestamp(seg.end, delimiter=".")
        text = seg.text.strip()
        cues.append(f"{start_ts} --> {end_ts}\n{text}")

    return header + "\n\n".join(cues) + "\n"

