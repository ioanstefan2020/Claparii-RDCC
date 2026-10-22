from typing import Any

from app.prompts.base import (
    BASE_SYSTEM_RO,
    EASY_READ_RULES_RO,
    adapt_block,
    wrap_document,
)
from app.prompts.versions import PROMPT_VERSIONS

VERSION = PROMPT_VERSIONS["transform"]

SYSTEM = f"""{BASE_SYSTEM_RO}

{EASY_READ_RULES_RO}

SARCINĂ TRANSFORMARE TEXT:
Transformă documentul primit în funcție de modul cerut:
- `bullets`: extrage o listă de idei/puncte cheie scurte (fiecare ≤ 15 cuvinte). Câmp `items`: listă de stringuri, `text`: null.
- `steps`: pași cronologici numerotați, fiecare începând cu un verb la imperativ. Câmp `items`: listă de stringuri, `text`: null.
- `questions`: 3 întrebări concrete, utile și politicoase pe care utilizatorul le poate adresa pentru clarificare. Câmp `items`: listă de stringuri, `text`: null.
- `glossary`: termeni tehnici sau birocratici din text, explicați simplu în format „Termen: Explicație”. Câmp `items`: listă de stringuri, `text`: null.
- `shorter`: rescriere comprimată la procentul cerut din lungime, păstrând toate termenele, sumele și persoanele. Câmp `text`: string, `items`: null.
- `tldr`: rezumat ultraconcis în 1–2 propoziții esențiale. Câmp `text`: string, `items`: null.
- `easy_read`: rescriere completă conform standardelor Ușor de Citit (propoziții scurte, diacritice, fără jargon). Câmp `text`: string, `items`: null.

REGULĂ IMPORTANTĂ:
Păstrează toate datele concrete: zile, ore, sume de bani, nume de persoane și coduri de documente.
Ieșirea trebuie să fie un obiect JSON valid cu structura:
{{
  "mode": "...",
  "items": ["..."] sau null,
  "text": "..." sau null
}}
"""

MOCKS: dict[str, dict[str, Any]] = {
    "bullets": {
        "mode": "bullets",
        "items": [
            "Luni la 09:00 te prezinți la recepția clădirii B.",
            "Formularul intern F-12 se completează până miercuri, 28 octombrie.",
            "Bugetul alocat pentru echipamente este de 500 EUR.",
        ],
        "text": None,
    },
    "steps": {
        "mode": "steps",
        "items": [
            "1. Mergi la recepția clădirii B luni la ora 09:00.",
            "2. Deschide portalul intern și completează formularul F-12 până miercuri, 28 octombrie.",
            "3. Trimite formularul semnat către departamentul de resurse umane.",
        ],
        "text": None,
    },
    "questions": {
        "mode": "questions",
        "items": [
            "Unde pot găsi datele de autentificare pentru portalul intern?",
            "Cui trebuie să trimit formularul F-12 după completare?",
            "Cine mă poate ajuta dacă am dificultăți tehnice la configurare?",
        ],
        "text": None,
    },
    "glossary": {
        "mode": "glossary",
        "items": [
            "F-12: Formularul intern pentru înregistrarea datelor noului angajat.",
            "SSM: Normele de securitate și sănătate în muncă.",
        ],
        "text": None,
    },
    "shorter": {
        "mode": "shorter",
        "items": None,
        "text": "Prezintă-te luni la 09:00 la recepția clădirii B. Completează formularul F-12 până miercuri, 28 octombrie, și respectă bugetul de 500 EUR.",
    },
    "tldr": {
        "mode": "tldr",
        "items": None,
        "text": "Trebuie să fii prezent luni la ora 09:00 la clădirea B și să completezi formularul F-12 până miercuri, 28 octombrie.",
    },
    "easy_read": {
        "mode": "easy_read",
        "items": None,
        "text": "Luni dimineață mergi la serviciu. La ora 09:00 te așteaptă la recepție în clădirea B. Până miercuri, 28 octombrie, completezi formularul F-12 pe calculator.",
    },
}


def build_user(
    text: str,
    mode: str,
    max_items: int = 6,
    target_pct: int = 40,
    profile: Any = None,
) -> str:
    adapt = adapt_block(profile)
    doc_wrapped = wrap_document(text)
    return f"""MOD CERUT: {mode}
LIMITE: max_items={max_items}, target_pct={target_pct}%

{adapt}

DOCUMENT:
{doc_wrapped}

Generează doar JSON-ul transformat conform cerințelor modului „{mode}”:"""
