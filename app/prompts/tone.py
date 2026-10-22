from typing import Any

from app.schemas.simplify import UserProfile

SYSTEM = """Ești un asistent de formulare a mesajelor scrise profesionale pentru tineri angajați (nume produs: PrimaZi).
Rolul tău este să oferi sugestii de reformulare respectuoasă, clară și profesională pentru e-mailuri sau mesaje de lucru.

REGULI STRICTE:
1. INCERTITUDINE ASUMATĂ: Nu pretinde că știi ce simte interlocutorul sau cum va reacționa. Nu infera emoții, personalitate sau intenții ascunse.
2. Formulează mesaje simple, directe, politicoase în limba română cu diacritice corecte.
3. Include întotdeauna cel puțin două alternative utile (ex. una mai scurtă/directă și una mai formală).
"""

MOCK: dict[str, Any] = {
    "suggested_text": (
        "Bună ziua! Vă rog să mă ajutați cu o scurtă clarificare privind ordinea sarcinilor de azi. Mulțumesc!"
    ),
    "alternative_phrasings": [
        "Salut! Aș avea nevoie de 2 minute pentru a confirma prioritățile pe proiectul curent.",
        "Bună ziua, aș dori să mă asigur că am înțeles corect pașii următori. Îmi puteți confirma ordinea lor?",
    ],
    "uncertainty_notice_ro": (
        "Sugestie pur orientativă. Comunicarea umană depinde de relația cu interlocutorul."
    ),
}


def build_user(
    text: str, context: str, tone_goal: str, profile: UserProfile | None = None
) -> str:
    p = profile or UserProfile()
    return (
        f"CONTEXT: {context}\n"
        f"SCOP TON: {tone_goal}\n"
        f"PREFERINȚE CITIRE: nivel={p.reading_level}\n\n"
        f"--- MESAJ SCRIS DE ANGAJAT ---\n"
        f"{text}\n"
        f"--- SFÂRȘIT MESAJ ---\n\n"
        f"Oferă o sugestie îmbunătățită și 2 alternative scurte, clare și politicoase."
    )
