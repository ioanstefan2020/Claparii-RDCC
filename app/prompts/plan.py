from typing import Any

from app.prompts.base import (
    BASE_SYSTEM_RO,
    EASY_READ_RULES_RO,
    adapt_block,
    wrap_document,
)
from app.prompts.versions import PROMPT_VERSIONS

VERSION = PROMPT_VERSIONS["plan"]

SYSTEM = f"""{BASE_SYSTEM_RO}

{EASY_READ_RULES_RO}

SARCINĂ PLANIFICARE & EXTRAGERE SARCINI:
Extrage acțiunile și sarcinile concrete din documentul primit.
Pentru fiecare sarcină identificată, generează un obiect cu proprietățile:
- `id`: identificator scurt (ex: "t1", "t2")
- `title`: titlu concis, care începe obligatoriu cu un VERB la infinitiv sau imperativ (ex: „Trimite raportul săptămânal”, „Instalează certificatul de securitate”).
- `due_iso`: data limită rezolvată în format YYYY-MM-DD sau null dacă nu este specificată o dată clară.
- `due_text`: textul exact din document referitor la termen (ex: „până vineri la ora 16:00”, „în prima săptămână”).
- `needs_confirmation`: true dacă data este vagă („cât mai repede”, „curând”, „până la prânz” fără zi). Nu inventa ore sau date.
- `priority`: "high", "normal", "low". Sarcinile cu termene apropiate sau obligatorii sunt "high".
- `steps`: listă cu 2-4 pași concreți, scurți pentru îndeplinirea sarcinii.
- `source_quote`: citatul EXACT din document care justifică această sarcină (maximum 200 caractere).

Exemplu 1:
Document: „Te rugăm ca până joi, 24 octombrie, să completezi fișa de protecția muncii și să o trimiți semnată la resurse umane.”
Ieșire JSON:
{{
  "tasks": [
    {{
      "id": "t1",
      "title": "Completează și trimite fișa de protecția muncii",
      "due_iso": "2026-10-24",
      "due_text": "până joi, 24 octombrie",
      "needs_confirmation": false,
      "priority": "high",
      "steps": [
        "Descarcă formularul de protecția muncii",
        "Completează datele personale cerute",
        "Semnează documentul și trimite-l prin email la resurse umane"
      ],
      "source_quote": "până joi, 24 octombrie, să completezi fișa de protecția muncii și să o trimiți semnată"
    }}
  ]
}}

Exemplu 2:
Document: „Când ai un moment liber, ar fi bine să saluți echipa pe canalul de Slack #general.”
Ieșire JSON:
{{
  "tasks": [
    {{
      "id": "t2",
      "title": "Prezintă-te echipei pe canalul #general de Slack",
      "due_iso": null,
      "due_text": "când ai un moment liber",
      "needs_confirmation": true,
      "priority": "low",
      "steps": [
        "Deschide aplicația Slack",
        "Intră pe canalul #general",
        "Scrie un mesaj scurt de salut și prezentare"
      ],
      "source_quote": "Când ai un moment liber, ar fi bine să saluți echipa pe canalul de Slack #general"
    }}
  ]
}}
"""

MOCK: dict[str, Any] = {
    "tasks": [
        {
            "id": "t1",
            "title": "Completează formularul F-12",
            "due_iso": "2026-10-28",
            "due_text": "miercuri, 28 octombrie",
            "needs_confirmation": False,
            "priority": "high",
            "steps": [
                "Deschide portalul intern",
                "Completează datele personale și bancare",
            ],
            "source_quote": "Până miercuri, 28 octombrie, trebuie să completezi în portalul intern formularul F-12",
        },
        {
            "id": "t2",
            "title": "Trimite raportul lunar",
            "due_iso": None,
            "due_text": "cât mai repede, până joi la prânz",
            "needs_confirmation": True,
            "priority": "normal",
            "steps": [],
            "source_quote": "până joi la prânz",
        },
    ]
}


def build_user(
    text: str,
    today_iso: str | None = None,
    profile: Any = None,
) -> str:
    today_str = today_iso or "2026-10-22"
    adapt = adapt_block(profile)
    doc_wrapped = wrap_document(text)
    return f"""CONTEXT TEMPORAL:
Astăzi este {today_str}. Rezolvă termenele relative („mâine”, „miercuri”, „săptămâna viitoare”) DOAR față de această dată. Dacă termenul este vag, setează due_iso=null și needs_confirmation=true.

{adapt}

DOCUMENT:
{doc_wrapped}

Generează doar JSON-ul cu sarcinile identificate conform instrucțiunilor:"""
