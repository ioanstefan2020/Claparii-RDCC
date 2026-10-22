"""Tests for Romanian TTS speech normalizer and /api/tts endpoint (A8).
Ref: docs/CONTRACTS-WAVE2.md, docs/TASKS-WAVE2.md A8
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.tts.engine import generate_fallback_wav, synthesize_speech
from app.tts.normalize_ro import normalize_ro_speech, number_to_words_ro

NORMALIZER_TEST_CASES = [
    # 1. Legal / Article abbreviations
    ("art. 78 din lege", "articolul șaptezeci și opt din lege"),
    ("Art. 12 prevede", "articolul doisprezece prevede"),
    ("alin. 2 din normă", "alineatul doi din normă"),
    ("nr. 5 este aprobat", "numărul 5 este aprobat"),
    ("nr. 448 din 2006", "numărul 448 din 2006"),
    ("Legea 448/2006", "Legea 448 din 2006"),

    # 2. Common abbreviations
    ("ex.: sarcini de lucru", "de exemplu: sarcini de lucru"),
    ("ex. un raport", "de exemplu un raport"),
    ("documente, formulare etc.", "documente, formulare și așa mai departe."),
    ("aprox. 5 zile", "aproximativ 5 zile"),
    ("vs. opțiunea veche", "față de opțiunea veche"),
    ("raport pt. echipă", "raport pentru echipă"),
    ("str. Victoriei", "strada Victoriei"),

    # 3. Alphanumeric IDs and tokens
    ("tasta F-12 deschide consola", "tasta F doisprezece deschide consola"),
    ("sarcina A-4 este gata", "sarcina A patru este gata"),
    ("etapa P-1", "etapa P unu"),

    # 4. Times
    ("ședința începe la 14:00", "ședința începe la ora paisprezece"),
    ("la 09:30 avem daily", "la ora nouă și jumătate avem daily"),
    ("termen 16:15", "termen ora șaisprezece și un sfert"),
    ("ora 10:45", "ora zece și patruzeci și cinci minute"),
    ("prânz la 12:00", "prânz la ora douăsprezece"),
    ("seară la 21:00", "seară la ora douăzeci și unu"),
    ("noapte la 22:00", "noapte la ora douăzeci și două"),

    # 5. Dates
    ("data 28.10.2026", "data 28 octombrie 2026"),
    ("data 28/10/2026", "data 28 octombrie 2026"),
    ("termen 2026-10-28", "termen 28 octombrie 2026"),

    # 6. Currency amounts
    ("costă 500 lei", "costă cinci sute de lei"),
    ("am primit 50 RON", "am primit cincizeci de lei"),
    ("doar 1 leu", "doar un leu"),
    ("bilet 5 lei", "bilet cinci lei"),
    ("buget 100 EUR", "buget o sută de euro"),
    ("plată 25 euro", "plată douăzeci și cinci de euro"),

    # 7. Ordinals
    ("al 2-lea pas", "al doilea pas"),
    ("a 3-a etapă", "a treia etapă"),
    ("al 1-lea termen", "primul termen"),
    ("a 1-a zi de muncă", "prima zi de muncă"),
]


@pytest.mark.parametrize("inp, expected", NORMALIZER_TEST_CASES)
def test_normalize_ro_speech_cases(inp, expected):
    res = normalize_ro_speech(inp)
    assert res.lower() == expected.lower()


def test_number_to_words_ro():
    assert number_to_words_ro(0) == "zero"
    assert number_to_words_ro(1) == "unu"
    assert number_to_words_ro(14) == "paisprezece"
    assert number_to_words_ro(78) == "șaptezeci și opt"
    assert number_to_words_ro(100) == "o sută"
    assert number_to_words_ro(500) == "cinci sute"


def test_fallback_wav_generator():
    wav = generate_fallback_wav(duration_s=0.2)
    assert isinstance(wav, bytes)
    assert len(wav) > 44
    assert wav[:4] == b"RIFF"
    assert wav[8:12] == b"WAVE"


def test_synthesize_speech_cache():
    import time
    text = f"Testare sinteză vocală în limba română {time.time()}"
    wav1, engine1 = synthesize_speech(text)
    assert wav1[:4] == b"RIFF"
    assert engine1 in ("piper", "fallback-synthesizer")

    # Second call should retrieve from cache
    wav2, engine2 = synthesize_speech(text)
    assert wav2 == wav1
    assert engine2 == "cached"


@pytest.mark.anyio
async def test_tts_endpoint_happy_path():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/tts",
            json={
                "text": "Ședința începe la 14:00 în sala A-4.",
                "voice": "ro-mihai",
                "rate": 1.0,
            },
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "audio/wav"
        assert "X-TTS-Engine" in resp.headers
        assert resp.content[:4] == b"RIFF"


@pytest.mark.anyio
async def test_tts_endpoint_empty_input():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post("/api/tts", json={"text": "   "})
        assert resp.status_code == 400
        data = resp.json()
        assert data["ok"] is False
        assert data["error"]["code"] == "empty_input"


@pytest.mark.anyio
async def test_tts_endpoint_too_long_input():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post("/api/tts", json={"text": "A" * 2001})
        assert resp.status_code == 400
        data = resp.json()
        assert data["ok"] is False
        assert data["error"]["code"] == "too_long"
