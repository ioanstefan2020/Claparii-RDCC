from typing import Any

from app.prompts.base import (
    BASE_SYSTEM_RO,
    EASY_READ_RULES_RO,
    adapt_block,
    wrap_document,
)
from app.prompts.versions import PROMPT_VERSIONS
from app.schemas.profile_norm import normalize_profile

VERSION = PROMPT_VERSIONS["simplify"]

FEW_SHOT_1 = """Exemplu 1:
<<<DOCUMENT
Luni la 09:00 te prezinți la recepție pentru ecuson și laptop. Până miercuri la 14:00 trimiți buletinul scanat la hr@firma.ro.
DOCUMENT>>>
Răspuns JSON:
{
  "summary": "Începi luni la ora 09:00 la recepție și trebuie să transmiți buletinul la HR până miercuri.",
  "steps": [
    {"n": 1, "text": "Mergi la recepție luni la 09:00 pentru a primi ecusonul și laptopul.", "source_quote": "Luni la 09:00 te prezinți la recepție pentru ecuson și laptop."},
    {"n": 2, "text": "Trimite buletinul scanat la hr@firma.ro până miercuri la ora 14:00.", "source_quote": "Până miercuri la 14:00 trimiți buletinul scanat la hr@firma.ro."}
  ],
  "key_terms": [
    {"term": "HR", "explanation": "Departamentul de resurse umane care se ocupă de actele de angajare."}
  ],
  "questions_to_ask": [
    "Unde anume se află biroul de recepție în clădire?"
  ]
}"""

FEW_SHOT_2 = """Exemplu 2:
<<<DOCUMENT
Pentru decontul de transport, completează fișa F-12 din intranet și atașează bonul fiscal până în ultima zi a lunii.
DOCUMENT>>>
Răspuns JSON:
{
  "summary": "Pentru a primi banii pe transport, completează formularul F-12 și atașează bonul până la finalul lunii.",
  "steps": [
    {"n": 1, "text": "Deschide fișa F-12 din rețeaua internă (intranet) și completează datele.", "source_quote": "completează fișa F-12 din intranet"},
    {"n": 2, "text": "Atașează bonul fiscal și trimite decontul până în ultima zi a lunii.", "source_quote": "atașează bonul fiscal până în ultima zi a lunii"}
  ],
  "key_terms": [
    {"term": "fișa F-12", "explanation": "Formularul pe care îl completezi pentru recuperarea banilor cheltuiți pe drum."},
    {"term": "intranet", "explanation": "Rețeaua internă a companiei, accesibilă doar angajaților."}
  ],
  "questions_to_ask": [
    "Bonul fiscal trebuie scanat sau adus în original la contabilitate?"
  ]
}"""

SYSTEM = f"""{BASE_SYSTEM_RO}

{EASY_READ_RULES_RO}

SARCINĂ SIMPLIFICARE:
Explică documentul pe înțelesul persoanei. Returnează JSON strict conform schemei:
- `summary`: maximum 2 propoziții, ce se cere și când.
- `steps`: listă cu pași clari [{{n, text, source_quote}}]. Începe fiecare pas cu un verb direct. Fiecare pas are obligatoriu `source_quote` exact din document. Dacă documentul nu cere nicio acțiune, lasă `steps` gol și menționează asta în `summary`.
- `key_terms`: listă de termeni sau acronime [{{term, explanation}}].
- `questions_to_ask`: maximum 3 întrebări concrete și politicoase pentru manager.
- REGULĂ DE PERSONALIZARE: În câmpul `summary` și în textul fiecărui pas (`text`), respectă cu prioritate maximă cerințele speciale de stil, formulare sau inserare de cuvinte cerute de utilizator în profilul său.

{FEW_SHOT_1}

{FEW_SHOT_2}"""

MOCK: dict[str, Any] = {
    "summary": "Începi luni la ora 09:00. În prima săptămână ai 3 sarcini principale: ridicarea accesului, completarea fișei de date și instruirea SSM.",
    "steps": [
        {
            "n": 1,
            "text": "Luni la 09:00 mergi la recepția clădirii B și ceri cardul de acces.",
            "source_quote": "Luni, ora 09:00 – Te prezinți la recepția clădirii B",
        },
        {
            "n": 2,
            "text": "Până miercuri, 28 octombrie, completezi formularul F-12 în portalul intern.",
            "source_quote": "Până miercuri, 28 octombrie, trebuie să completezi în portalul intern formularul F-12",
        },
    ],
    "key_terms": [
        {
            "term": "onboarding",
            "explanation": "Primele săptămâni în care te acomodezi cu echipa și înveți sarcinile de lucru.",
        },
        {
            "term": "formularul F-12",
            "explanation": "Formularul intern în care introduci datele tale pentru plata salariului.",
        },
    ],
    "questions_to_ask": [
        "Pot primi instrucțiunile și în format scris, pas cu pas?",
        "Cine este persoana mea de contact la recepție dacă întârzii?",
    ],
}


def build_user(text: str, profile: Any = None) -> str:
    p = normalize_profile(profile)
    adaptation = adapt_block(p)
    doc_wrapped = wrap_document(text)

    return f"""ADAPTĂRI ȘI PREFERINȚE CERUTE PENTRU ACEST UTILIZATOR:
{adaptation}

DOCUMENTUL DE PROCESAT:
{doc_wrapped}

Generează obiectul JSON complet acum, aplicând fidel toate preferințele utilizatorului în textele generate:"""
