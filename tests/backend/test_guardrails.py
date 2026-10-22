from app.guardrails import verify_quotes


def test_verify_quotes_keeps_verbatim_quote():
    source = "Luni, ora 09:00 - Te prezinți la recepția clădirii B."
    items = [
        {
            "n": 1,
            "text": "Mergi la recepție.",
            "source_quote": "Luni, ora 09:00 - Te prezinți la recepția clădirii B.",
        }
    ]
    kept, dropped = verify_quotes(items, source, key="source_quote")
    assert len(kept) == 1
    assert len(dropped) == 0
    assert kept[0]["n"] == 1


def test_verify_quotes_whitespace_normalisation():
    source = "Te   prezinți   la\nrecepția   clădirii B."
    items = [{"n": 1, "source_quote": "Te prezinți la recepția clădirii B."}]
    kept, dropped = verify_quotes(items, source, key="source_quote")
    assert len(kept) == 1
    assert len(dropped) == 0


def test_verify_quotes_drops_fabricated_quote():
    source = "Luni, ora 09:00 - Te prezinți la recepție."
    items = [
        {"n": 1, "source_quote": "Luni, ora 09:00 - Te prezinți la recepție."},
        {"n": 2, "source_quote": "Vineri la prânz primești laptopul de serviciu."},
    ]
    kept, dropped = verify_quotes(items, source, key="source_quote")
    assert len(kept) == 1
    assert len(dropped) == 1
    assert kept[0]["n"] == 1
    assert dropped[0]["n"] == 2
