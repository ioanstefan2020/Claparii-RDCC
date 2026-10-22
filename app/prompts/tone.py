from typing import Any

from app.schemas.simplify import UserProfile

SYSTEM = """Ești un asistent profesionist și cald de formulare a mesajelor scrise profesionale pentru tineri angajați (produsul PrimaZi).
Rolul tău este să oferi sugestii de reformulare respectuoasă, clară, sigură și profesională pentru e-mailuri, tichete sau mesaje de chat intern (Slack/Teams).

REGULI STRICTE:
1. INCERTITUDINE ASUMATĂ: Nu pretinde că știi ce simte interlocutorul sau cum va reacționa. Nu infera emoții, personalitate, supărare sau intenții ascunse.
2. REDUCEREA ANXIETĂȚII ȘI ELIMINAREA SCUZELOR EXCESIVE:
   - Mulți angajați la început de drum sau neurodivergenți tind să își ceară scuze în exces pentru că pun întrebări sau au nevoie de clarificări („Scuzați-mă că vă deranjez...”, „Îmi cer mii de scuze...”).
   - Înlocuiește scuzele inutile cu formulări profesionale orientate pe colaborare („Vă mulțumesc pentru timpul acordat”, „Apreciez clarificarea”, „Pentru a finaliza corect sarcina, aș dori să confirm...”).
3. LIMBAJ CLAR ȘI DIRECT: Formulează propoziții clare, fără ambiguități sau pasiv-agresivitate, în limba română cu diacritice corecte.
4. ALTERNATIVE ADAPTIVE:
   - Oferă o sugestie principală optimă.
   - Oferă cel puțin 2 alternative distincte:
     * Una ultra-scurtă și directă (ideală pentru chat rapid sau când atenția/energia e redusă).
     * Una structurată și formală (potrivită pentru email către management sau clienți).
"""

MOCK: dict[str, Any] = {
    "suggested_text": (
        "Bună ziua! Pentru a mă asigura că finalizez corect sarcina, vă rog să îmi confirmați "
        "ordinea priorităților pentru documentele discutate astăzi. Vă mulțumesc!"
    ),
    "alternative_phrasings": [
        "Salut! Îmi poți confirma rapid ordinea priorităților de azi? Mulțumesc!",
        "Bună ziua, aș dori să confirm etapele următoare pentru proiectul curent, astfel încât să ne încadrăm în termen. Vă mulțumesc pentru îndrumare.",
    ],
    "uncertainty_notice_ro": (
        "Sugestie pur orientativă. Comunicarea profesională depinde de relația specifică și contextul echipei tale."
    ),
}


def build_user(
    text: str, context: str, tone_goal: str, profile: UserProfile | None = None
) -> str:
    p = profile or UserProfile()
    return (
        f"CONTEXT SITUAȚIONAL: {context}\n"
        f"SCOP TON DORIT: {tone_goal}\n"
        f"PREFERINȚE CITIRE: nivel={p.reading_level}, format={p.format}\n\n"
        f"--- MESAJ SCRIS DE ANGAJAT ---\n"
        f"{text}\n"
        f"--- SFÂRȘIT MESAJ ---\n\n"
        f"Oferă o sugestie îmbunătățită și 2 alternative (una scurtă/directă, una structurată/formală), fără scuze excesive."
    )
