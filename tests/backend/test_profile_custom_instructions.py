import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.prompts.base import (
    adapt_block,
    apply_custom_decorations,
    detect_disability_adaptation_hints,
)


def test_apply_custom_decorations_miau_both():
    text = "Primul paragraf de test.\nAl doilea paragraf de test."
    notes = "Vreau cuvantul miau inainte si dupa fiecare paragraf"
    res = apply_custom_decorations(text, notes)
    assert (
        res
        == "miau Primul paragraf de test. miau\nmiau Al doilea paragraf de test. miau"
    )


def test_apply_custom_decorations_miau_after():
    text = "Paragraf unu.\nParagraf doi."
    notes = "adaugă cuvântul miau după fiecare paragraf"
    res = apply_custom_decorations(text, notes)
    assert res == "Paragraf unu. miau\nParagraf doi. miau"


def test_apply_custom_decorations_every_n_words():
    text = "unu doi trei patru cinci sase sapte opt noua zece"
    notes = "inserează cuvântul banana la fiecare 5 cuvinte"
    res = apply_custom_decorations(text, notes)
    assert "banana" in res
    words = res.split()
    assert words[5] == "banana"


def test_detect_disability_adaptation_hints():
    # Memory
    hints_mem = detect_disability_adaptation_hints(
        "uit des, am probleme de memorie si retinere"
    )
    assert any("MEMORIE" in h for h in hints_mem)
    assert any("key_terms" in h for h in hints_mem)

    # Low vision
    hints_vis = detect_disability_adaptation_hints(
        "nu vad bine, am nevoie de font mare si vizibilitate"
    )
    assert any("VEDERE SCĂZUTĂ" in h for h in hints_vis)

    # ADHD / Focus
    hints_adhd = detect_disability_adaptation_hints(
        "ma distrag usor si imi pierd concentrarea"
    )
    assert any("ATENȚIE" in h for h in hints_adhd)

    # Combined in adapt_block
    profile = {
        "needs_notes": "uit des si am memorie slaba, am nevoie de vizibilitate marita"
    }
    block = adapt_block(profile)
    assert "ADAPTĂRI COGNITIVE ȘI DE ACCESIBILITATE DEDUSE DIN NEVOI" in block
    assert "MEMORIE" in block
    assert "VEDERE" in block


@pytest.mark.anyio
async def test_simplify_with_custom_profile_notes(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("LLM_CACHE_DIR", str(tmp_path / "cache"))

    source_text = (
        "Luni, ora 09:00 – Te prezinți la recepția clădirii B. "
        "Până miercuri, 28 octombrie, trebuie să completezi în portalul intern formularul F-12."
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/simplify",
            json={
                "text": source_text,
                "profile": {
                    "reading_level": "simple",
                    "format": "steps",
                    "needs_notes": "Vreau cuvantul miau inainte si dupa fiecare paragraf",
                },
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        # Summary and steps should be decorated with miau
        assert "miau" in data["data"]["summary"].lower()
        for step in data["data"]["steps"]:
            assert "miau" in step["text"].lower()


@pytest.mark.anyio
async def test_transform_rewrite_mode():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/transform",
            json={
                "text": "Luni la 09:00 te prezinți la recepția clădirii B. Până miercuri la 14:00 trimiți documentele.",
                "mode": "rewrite",
                "profile": {
                    "reading_level": "simple",
                    "format": "short_paragraphs",
                    "needs_notes": "cuvantul miau dupa fiecare paragraf",
                },
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["data"]["mode"] == "rewrite"
        assert body["data"]["text"] is not None
        assert "miau" in body["data"]["text"].lower()
