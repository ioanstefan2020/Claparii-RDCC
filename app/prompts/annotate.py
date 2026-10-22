from typing import Any

from app.prompts.base import BASE_SYSTEM_RO, wrap_document
from app.prompts.versions import PROMPT_VERSIONS

VERSION = PROMPT_VERSIONS["annotate"]

SYSTEM = f"""{BASE_SYSTEM_RO}

SARCINĂ ADNOTARE & SALIENȚĂ SEMANTICĂ:
Analizează textul și identifică elemente semantice și pragmatice de comunicare.

1. HIGHLIGHTS SEMANTICE (`highlights`):
Extrage secvențe scurte din text în următoarele categorii:
- `action`: verbe de acțiune directă / obligații (ex: „trimite”, „completează”, „prezintă-te”).
- `person`: nume de persoane sau roluri specifice (ex: „Elena”, „Radu”, „People Operations”).
- `warning`: atenționări sau cerințe stricte (ex: „obligatoriu”, „fără întârziere”).
- `term`: acronime sau termeni tehnici/birocratici (ex: „SSM”, „F-12”, „Jira”).
Pentru fiecare: {{start, end, category, text}}. Asigură-te că `text` este exact porțiunea textului de la indexul start la end.

2. GLOSAR (`glossary`):
Pentru fiecare `term` identificat, oferă o explicație simplă de o frază: {{term, explanation}}.

3. NOTE DE TON ȘI PRAGMATICĂ (`annotations`):
Marchează DOAR dacă în text există un indiciu LINGVISTIC clar:
- `indirect_request`: cerere politicoasă formulată indirect (ex: „ar fi frumos să...”, „dacă ai timp...” – explică ce se așteaptă de fapt).
- `figurative`: expresie figurată sau idiom românesc – explică sensul propriu pe scurt.
- `urgency`: urgență sugerată implicit.
- `joke`: glumă (eticheta obligatoriu conține „posibilă glumă — nesigur”).
- `irony`: ironie/sarcasm (eticheta obligatoriu conține „posibilă ironie — nesigur”).
- `softener`: formulare de atenuare care nu anulează sarcina.
Pentru fiecare notă: {{start, end, kind, evidence_quote, note_ro, confidence: "low" | "medium"}}. NICIODATĂ nu folosi "high". Dacă nu există indicii clare de ton, lasă `annotations` listă goală [].
"""

MOCK: dict[str, Any] = {
    "highlights": [
        {"start": 0, "end": 6, "category": "deadline", "text": "Marți"},
        {"start": 10, "end": 19, "category": "deadline", "text": "ora 11:00"},
        {"start": 35, "end": 55, "category": "action", "text": "sesiune introductivă"},
        {"start": 60, "end": 64, "category": "person", "text": "Radu"},
        {"start": 70, "end": 80, "category": "action", "text": "configurezi"},
        {"start": 90, "end": 93, "category": "term", "text": "VPN"},
        {"start": 95, "end": 99, "category": "term", "text": "Jira"},
    ],
    "annotations": [
        {
            "start": 0,
            "end": 40,
            "kind": "indirect_request",
            "evidence_quote": "Ar fi frumos să arunci o privire pe document",
            "note_ro": "(cerere politicoasă: se așteaptă să citești documentul)",
            "confidence": "medium",
        }
    ],
    "glossary": [
        {"term": "VPN", "explanation": "Conexiune securizată la rețeaua companiei."},
        {
            "term": "Jira",
            "explanation": "Aplicație unde sunt organizate și urmărite sarcinile echipei.",
        },
    ],
}


def build_user(text: str, layers: list[str]) -> str:
    doc_wrapped = wrap_document(text)
    layer_str = ", ".join(layers)
    return f"""STRATURI CERUTE: {layer_str}

DOCUMENT:
{doc_wrapped}

Generează adnotările JSON:"""
