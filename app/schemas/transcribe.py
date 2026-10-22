"""app/schemas/transcribe.py - Data schemas for audio transcription endpoint.

Contract (CONTRACTS-WAVE2.md):
- POST /api/transcribe
- Segments with start, end, and verbatim text
- Generated WebVTT and SubRip (SRT) subtitles
"""

from pydantic import BaseModel, ConfigDict, Field


class TranscribeSegment(BaseModel):
    """Timestamped audio transcription segment."""

    model_config = ConfigDict(extra="ignore")

    start: float = Field(..., description="Start timestamp in seconds")
    end: float = Field(..., description="End timestamp in seconds")
    text: str = Field(..., description="Verbatim transcribed speech")


class TranscribeCaptions(BaseModel):
    """Subtitles formatted in standard caption specifications."""

    model_config = ConfigDict(extra="ignore")

    srt: str = Field(..., description="SubRip subtitle format (.srt)")
    vtt: str = Field(..., description="WebVTT subtitle format (.vtt)")


class TranscribeResponseData(BaseModel):
    """Transcription response payload containing text, segments, and captions."""

    model_config = ConfigDict(extra="ignore")

    language: str = Field(default="ro", description="Spoken language code (e.g. ro)")
    duration_s: float = Field(..., description="Total audio duration in seconds")
    text: str = Field(..., description="Full combined transcribed text")
    segments: list[TranscribeSegment] = Field(
        default_factory=list, description="Timestamped transcription segments"
    )
    captions: TranscribeCaptions = Field(
        ..., description="Standard subtitle exports (SRT & VTT)"
    )

