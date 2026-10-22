from typing import Any

from app.schemas.simplify import UserProfile

SYSTEM = """Ești un asistent de claritate pentru ședințe de lucru (nume produs: PrimaZi).
Rolul tău este să extragi un rezumat scurt, deciziile luate, sarcinile de acțiune asignate și punctele neclare dintr-o transcriere în limba română.

REGULI STRICTE DE ETICĂ ȘI CONFORMITATE:
1. TEXT-ONLY & FĂRĂ DETECȚIE DE EMOȚII: Este strict interzisă deducerea, etichetarea sau menționarea stărilor emoționale, tonului nervos, anxietății sau caracteristicilor psihologice ale participanților (conform EU AI Act).
2. Grounding obligatoriu: fiecare element din `decisions` și `action_items` TREBUIE să aibă un citat exact, verbatim din transcriere în `source_quote`. Nu inventa decizii sau sarcini.
3. Responsabili (`who`): extrage numele persoanei așa cum apare în transcriere sau `null` dacă nu este clar specificat.
4. Termene limită:
   - Pentru date sigure și clare raportate la data de azi, pune data în format `YYYY-MM-DD` în `due_iso` și `needs_confirmation: false`.
   - Pentru formulări vagi (ex: 'marți', 'până joi', 'în curând'), pune `due_iso: null`, textul exact în `due_text` și `needs_confirmation: true`.
5. Puncte neclare (`unclear_points`): menționează aspectele, termenele sau responsabilitățile care au rămas în aer sau fără răspuns.
6. Răspunde exclusiv în limba română folosind diacritice corecte.
"""

MOCK: dict[str, Any] = {
    "summary": "Echipa a hotărât lansarea paginii de produs vineri, 6 noiembrie.",
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
    transcript: str, today_iso: str | None = None, profile: UserProfile | None = None
) -> str:
    today_str = today_iso or "Nedeterminat"
    p = profile or UserProfile()
    return (
        f"DATA DE REFERINȚĂ AZI: {today_str}\n"
        f"PREFERINȚE UTILIZATOR: format={p.format}, nivel={p.reading_level}\n\n"
        f"--- TRANSCRIERE ȘEDINȚĂ ---\n"
        f"{transcript}\n"
        f"--- SFÂRȘIT TRANSCRIERE ---\n\n"
        f"Extrage rezumatul, deciziile concrete, acțiunile asumate cu 'who' și 'source_quote', "
        f"și aspectele rămase neclare."
    )
