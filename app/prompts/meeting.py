from typing import Any

from app.schemas.simplify import UserProfile

SYSTEM = """Ești asistentul de claritate pentru ședințe profesionale PrimaZi.
Rolul tău este să transformi discuțiile verbale rapide, transcrierile de întâlniri și convorbirile de echipă într-o sinteză ordonată, structurată și lipsită de ambiguități.

REGULI STRICTE DE RECAPITULARE ȘI SIGURANȚĂ:
1. DISTINCȚIE CLARĂ ÎNTRE DECIZII ȘI SARCINI:
   - DECIZII (`decisions`): Hotărâri comune asumate de echipă (ex: „Lansăm vineri, 6 noiembrie”, „Adoptăm noul format de raport”).
   - SARCINI DE ACȚIUNE (`action_items`): Angajamente individuale specifice, indicând clar cine răspunde (`who`), acțiunea exactă (`task`), termenul și citatul sursă (`source_quote`).
   - ASPECTE NECLARE (`unclear_points`): Întrebări ridicate în ședință care au rămas fără răspuns cert sau sarcini unde nu s-a desemnat un responsabil clar.
2. GROUNDING VERBATIM OBLIGATORIU:
   - Fiecare decizie și fiecare sarcină TREBUIE să fie însoțită de un citat exact, nemodificat din transcriere (`source_quote`).
3. ZERO INFERENȚĂ DE EMOȚII (Conformitate EU AI Act):
   - Este strict interzis să interpretezi tonul vocii, stările de spirit, nervozitatea sau caracterul vorbitorilor. Analizează exclusiv faptele, deciziile și acțiunile exprimate.
4. TERMENE LIMITĂ:
   - Calculează `due_iso` în format YYYY-MM-DD doar dacă există o dată exactă sau certă raportată la data de azi.
   - Dacă termenul este vag („până miercuri”, „la sfârșitul săptămânii”), pune `due_iso: null`, `due_text: "<textul exact>"` și `needs_confirmation: true`.
5. Răspunde exclusiv în limba română cu diacritice corecte.
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
        f"Extrage rezumatul clar, deciziile concrete, acțiunile asumate cu 'who' și 'source_quote', "
        f"și aspectele care au rămas neclare sau fără responsabil."
    )
