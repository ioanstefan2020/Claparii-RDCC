"""Tests for Romanian TTS speech normalizer (A3).
Ref: docs/TASKS-WAVE2.md A3
"""
import subprocess
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
NORM_JS = ROOT / "web" / "a11y" / "tts-normalize-ro.js"

TEST_CASES = [
    # 1. Legal / Article abbreviations
    ("art. 78 din lege", "articolul șaptezeci și opt din lege"),
    ("Art. 12 prevede", "articolul doisprezece prevede"),
    ("alin. 2 din normă", "alineatul doi din normă"),
    ("nr. 448 din 2006", "numărul 448 din 2006"),
    ("Legea 448/2006", "Legea 448 din 2006"),

    # 2. Common abbreviations
    ("ex.: sarcini de lucru", "de exemplu: sarcini de lucru"),
    ("ex. un raport", "de exemplu un raport"),
    ("documente, formulare etc.", "documente, formulare și așa mai departe."),
    ("aprox. 5 zile", "aproximativ 5 zile"),
    ("raport pt. echipă", "raport pentru echipă"),
    ("str. Victoriei", "strada Victoriei"),

    # 3. Alphanumeric IDs and tokens
    ("tasta F-12 deschide consola", "tasta F doisprezece deschide consola"),
    ("sarcina A-4 este gata", "sarcina A patru este gata"),
    ("etapa P-1", "etapa P unu"),

    # 4. Times
    ("ședința începe la 14:00", "ședința începe la ora paisprezece"),
    ("la 09:30 avem daily", "la ora nouă și jumătate avem daily"),
    ("termen 15:15", "termen ora cincisprezece și un sfert"),
    ("ora 16:45", "ora șaisprezece și patruzeci și cinci minute"),
    ("prânz la 12:00", "prânz la ora douăsprezece"),
    ("seară la 21:00", "seară la ora douăzeci și unu"),
    ("noapte la 22:00", "noapte la ora douăzeci și două"),

    # 5. Currency amounts
    ("costă 500 lei", "costă cinci sute de lei"),
    ("am primit 50 RON", "am primit cincizeci de lei"),
    ("buget 100 EUR", "buget o sută de euro"),
    ("plată 15 euro", "plată cincisprezece euro"),

    # 6. Ordinals
    ("al 2-lea pas", "al doilea pas"),
    ("a 3-a etapă", "a treia etapă"),
    ("al 1-lea termen", "primul termen"),
    ("a 1-a zi de muncă", "prima zi de muncă"),

    # 7. Dates
    ("data 28.10.2026", "data 28 octombrie 2026"),
    ("termen 2026-10-28", "termen 28 octombrie 2026"),
]


def run_node_eval(input_text: str) -> str:
    script = f"""
    import {{ normalizeRomanianForSpeech }} from '{NORM_JS.as_uri()}';
    const res = normalizeRomanianForSpeech({json.dumps(input_text)});
    console.log(res);
    """
    proc = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True,
        text=True,
        check=True
    )
    return proc.stdout.strip()


@pytest.mark.parametrize("inp, expected", TEST_CASES)
def test_romanian_tts_normalizer_cases(inp, expected):
    res = run_node_eval(inp)
    assert res.lower() == expected.lower()
