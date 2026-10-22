from typing import Any

from app.prompts.base import (
    BASE_SYSTEM_RO,
    EASY_READ_RULES_RO,
    adapt_block,
    wrap_document,
)
from app.prompts.versions import PROMPT_VERSIONS

VERSION = PROMPT_VERSIONS["meeting"]

SYSTEM = f"""{BASE_SYSTEM_RO}

{EASY_READ_RULES_RO}

SARCINĂ SINTEZĂ ȘEDINȚĂ:
Extrage informațiile esențiale din transcrierea ședinței.
Returnează un obiect JSON cu următoarea structură:
- `summary`: Rezumat clar în maximum 3 propoziții despre ce s-a discutat și concluzionat.
- `decisions`: Listă de decizii luate: [{{text, source_quote}}]. Fiecare decizie trebuie fundamentată pe o frază exactă din transcriere.
- `action_items`: Listă de sarcini stabilite: [{{who, task, due_iso, due_text, needs_confirmation, source_quote}}].
  - `who`: Numele exact al persoanei responsabile sau null dacă nu e numită explicit.
  - `task`: Titlul sarcinii (verb + obiect direct).
  - `due_iso`: Data limită în format YYYY-MM-DD sau null dacă e vagă sau inexistentă.
  - `due_text`: Formularea exactă a termenului din transcriere sau null.
  - `needs_confirmation`: true dacă termenul este vag sau cineva nu a confirmat explicit.
  - `source_quote`: Citatul exact din transcriere (maximum 200 caractere).
- `unclear_points`: Puncte rămase nelămurite sau întrebări fără răspuns (maximum 3).
- REGULĂ DE PERSONALIZARE: În rezumat și în textele deciziilor, respectă cerințele speciale de stil, redactare și inserare de cuvinte cerute de utilizator în profilul său.

Exemplu 1:
Transcrierea: „Ana: Bună tuturor, stabilim ca lansarea să fie pe 15 noiembrie. Mihai, te ocupi de testare până miercuri? Mihai: Da, sigur.”
Ieșire JSON:
{{
  "summary": "Echipa a stabilit data lansării pentru 15 noiembrie. Mihai va finaliza testarea până miercuri.",
  "decisions": [
    {{"text": "Lansarea va avea loc pe 15 noiembrie.", "source_quote": "stabilim ca lansarea să fie pe 15 noiembrie"}}
  ],
  "action_items": [
    {{"who": "Mihai", "task": "Finalizează testarea", "due_iso": null, "due_text": "până miercuri", "needs_confirmation": false, "source_quote": "te ocupi de testare până miercuri"}}
  ],
  "unclear_points": []
}}"""

MOCK: dict[str, Any] = {
    "summary": "Echipa a discutat pregătirea lansării și a alocat sarcinile pentru documentație și testare.",
    "decisions": [
        {
            "text": "Lansăm vineri, 6 noiembrie.",
            "source_quote": "lansăm vineri, 6 noiembrie",
        }
    ],
    "action_items": [
        {
            "who": "Ioana",
            "task": "Integrează textele finale",
            "due_iso": None,
            "due_text": "miercuri",
            "needs_confirmation": True,
            "source_quote": "tu integrezi textele miercuri",
        }
    ],
    "unclear_points": ["Nu e clar cine anunță clientul despre termen."],
}


def build_user(
    transcript: str = "",
    today_iso: str | None = None,
    profile: Any = None,
    text: str = "",
) -> str:
    content = transcript or text
    doc_wrapped = wrap_document(content)
    today_str = today_iso or "Nedeterminat"
    adapt = adapt_block(profile)
    return f"""DATA DE REFERINȚĂ AZI: {today_str}

ADAPTĂRI ȘI PREFERINȚE CERUTE PENTRU ACEST UTILIZATOR:
{adapt}

TRANSCRIERE ȘEDINȚĂ:
{doc_wrapped}

Generează doar JSON-ul cu sinteza ședinței conform instrucțiunilor și preferințelor din profil:"""
