"""tests/backend/test_transcribe.py - Contract and functionality tests for /api/transcribe."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.audio.captions import format_timestamp, segments_to_srt, segments_to_vtt
from app.main import app
from app.schemas.transcribe import (
    TranscribeCaptions,
    TranscribeResponseData,
    TranscribeSegment,
)


def test_format_timestamp():
    """Verify timestamp formatting for SRT (comma) and WebVTT (dot)."""
    assert format_timestamp(0.0, delimiter=",") == "00:00:00,000"
    assert format_timestamp(0.0, delimiter=".") == "00:00:00.000"
    assert format_timestamp(4.2, delimiter=",") == "00:00:04,200"
    assert format_timestamp(4.2, delimiter=".") == "00:00:04.200"
    assert format_timestamp(65.123, delimiter=",") == "00:01:05,123"
    assert format_timestamp(3661.045, delimiter=",") == "01:01:01,045"
    # Negative seconds clamped to 0
    assert format_timestamp(-5.0, delimiter=",") == "00:00:00,000"


def test_segments_to_srt_and_vtt():
    """Verify SRT and WebVTT cue construction."""
    segments = [
        TranscribeSegment(start=0.0, end=4.5, text="Prima propoziție."),
        TranscribeSegment(start=4.5, end=9.0, text="A doua propoziție."),
    ]

    srt = segments_to_srt(segments)
    assert srt.startswith("1\n00:00:00,000 --> 00:00:04,500\nPrima propoziție.")
    assert "\n\n2\n00:00:04,500 --> 00:00:09,000\nA doua propoziție." in srt
    assert srt.endswith("\n")

    vtt = segments_to_vtt(segments)
    assert vtt.startswith("WEBVTT\n\n00:00:00.000 --> 00:00:04.500\nPrima propoziție.")
    assert "00:00:04.500 --> 00:00:09.000\nA doua propoziție." in vtt

    # Empty segments
    assert segments_to_srt([]) == ""
    assert segments_to_vtt([]) == "WEBVTT\n\n"


@pytest.mark.anyio
async def test_transcribe_mock_happy_path(monkeypatch):
    """Test successful transcription in mock mode."""
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    dummy_audio = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00data\x00\x00\x00\x00"
    files = {"file": ("meeting.wav", dummy_audio, "audio/wav")}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post("/api/transcribe", files=files)
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        data = body["data"]

        assert data["language"] == "ro"
        assert data["duration_s"] == 15.0
        assert "Bun găsit tuturor" in data["text"]
        assert len(data["segments"]) == 3
        assert data["segments"][0]["text"].startswith("Bun găsit")

        # Verify SRT format
        captions = data["captions"]
        assert captions["srt"].startswith("1\n00:00:00,000 --> 00:00:04,500")
        assert "-->" in captions["srt"]
        assert "," in captions["srt"].split("-->")[0]

        # Verify VTT format
        assert captions["vtt"].startswith("WEBVTT\n\n00:00:00.000 --> 00:00:04.500")
        assert "-->" in captions["vtt"]
        assert "." in captions["vtt"].split("-->")[0]

        assert body["meta"]["provider"] == "mock"


@pytest.mark.anyio
async def test_transcribe_invalid_audio_format():
    """Test rejection of non-audio files."""
    files = {"file": ("document.pdf", b"%PDF-1.4 dummy", "application/pdf")}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post("/api/transcribe", files=files)
        assert resp.status_code == 400
        body = resp.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "invalid_audio_format"


@pytest.mark.anyio
async def test_transcribe_empty_file():
    """Test rejection of empty audio files."""
    files = {"file": ("audio.mp3", b"", "audio/mpeg")}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post("/api/transcribe", files=files)
        assert resp.status_code == 400
        body = resp.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "empty_file"


@pytest.mark.anyio
async def test_transcribe_file_too_large(monkeypatch):
    """Test rejection of oversized files exceeding MAX_FILE_SIZE_BYTES."""
    monkeypatch.setattr("app.routers.transcribe.MAX_FILE_SIZE_BYTES", 100)
    files = {"file": ("large.mp3", b"X" * 150, "audio/mpeg")}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post("/api/transcribe", files=files)
        assert resp.status_code == 400
        body = resp.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "file_too_large"


@pytest.mark.anyio
async def test_transcribe_groq_api_call(monkeypatch):
    """Test Groq Whisper API handling with mocked httpx client."""
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setattr("app.config.settings.GROQ_API_KEY", "mock-groq-key")

    mock_groq_response = {
        "text": "Aceasta este o transcriere demonstrativă.",
        "duration": 5.2,
        "language": "ro",
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 5.2,
                "text": "Aceasta este o transcriere demonstrativă.",
            }
        ],
    }

    class MockResponse:
        status_code = 200
        text = "ok"

        def json(self):
            return mock_groq_response

    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def post(self, *args, **kwargs):
            return MockResponse()

    monkeypatch.setattr("httpx.AsyncClient", MockAsyncClient)

    files = {"file": ("speech.ogg", b"dummy ogg bytes", "audio/ogg")}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post("/api/transcribe", files=files)
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["data"]["text"] == "Aceasta este o transcriere demonstrativă."
        assert body["data"]["duration_s"] == 5.2
        assert body["meta"]["provider"] == "groq"
        assert "Aceasta este o transcriere demonstrativă." in body["data"]["captions"]["srt"]


@pytest.mark.anyio
async def test_transcribe_groq_rate_limited(monkeypatch):
    """Test 429 rate limit handling from Groq Whisper."""
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setattr("app.config.settings.GROQ_API_KEY", "mock-groq-key")

    class MockRateLimitedResponse:
        status_code = 429
        text = "Rate limit reached"

    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def post(self, *args, **kwargs):
            return MockRateLimitedResponse()

    monkeypatch.setattr("httpx.AsyncClient", MockAsyncClient)

    files = {"file": ("speech.mp3", b"dummy mp3 data", "audio/mpeg")}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post("/api/transcribe", files=files)
        assert resp.status_code == 429
        body = resp.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "transcribe_rate_limited"


def test_no_emotion_inference():
    """Ensure TranscribeResponseData schema forbids emotion or speaker personality inferences."""
    allowed_fields = {"language", "duration_s", "text", "segments", "captions"}
    actual_fields = set(TranscribeResponseData.model_fields.keys())
    assert actual_fields == allowed_fields

    segment_fields = set(TranscribeSegment.model_fields.keys())
    assert segment_fields == {"start", "end", "text"}
