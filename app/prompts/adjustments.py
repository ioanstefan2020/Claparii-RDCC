"""Romanian prompts and mock generators for workplace adjustments draft letters.

Enforces strict responsible-AI principles:
- Functional accommodations only (work environment, tools, schedule, communication).
- Strictly NO medical diagnoses, clinical terms, pathology, or symptom disclosure.
- Respectful, collaborative, and constructive workplace tone.
"""
from __future__ import annotations

from typing import Any

# Responsible-AI deny-list: functional workplace adjustments must NEVER label
# users with medical conditions, clinical terms, or diagnoses.
DENY_LIST_DIAGNOSES: list[str] = [
    "diagnostic",
    "boală",
    "boala",
    "boli",
    "afecțiune",
    "afectiune",
    "afecțiuni",
    "afectiuni",
    "sindrom",
    "pacient",
    "pacientă",
    "medical",
    "medicală",
    "medicale",
    "handicap",
    "dizabilitate",
    "dizabilități",
    "adhd",
    "autism",
    "depresie",
    "anxietate",
    "orb",
    "surd",
    "paralizie",
    "retard",
    "demență",
    "dementa",
    "patologie",
    "clinic",
    "clinică",
]

SYSTEM: str = """Ești un asistent profesionist și empatic specializat în formularea adaptărilor rezonabile și funcționale la locul de muncă (workplace accommodations), în limba română.

ROLUL TĂU:
Ajuți angajatul să formuleze o solicitare clară, constructivă și profesională către angajator, axată exclusiv pe organizarea muncii, mediu de lucru, echipamente și fluxuri de comunicare.

REGULI CRITICE DE RESPONSABILITATE ȘI CONFIDENȚIALITATE (STRICT):
1. NU menționa, sugera sau deduce NICIODATĂ un diagnostic medical, o boală, afecțiune clinică, tulburare sau etichetă de sănătate/dizabilitate.
2. Folosește exclusiv limbaj funcțional, centrat pe sarcini, instrumente și eficiență operațională (ex: „am nevoie de instrucțiuni în scris pentru a urmări cu exactitate pașii”, NU motive medicale).
3. Tonul trebuie să fie constructiv, colaborativ și orientat către succesul reciproc la locul de muncă.
4. Răspunsul TĂU TREBUIE să fie un obiect JSON valid, conform schemei cerute, fără text introductiv sau concluziv în afara JSON-ului.

SCHEMA JSON CERUTĂ:
{
  "subject": "Subiectul e-mailului / mesajului în limba română",
  "body_ro": "Textul complet al mesajului redactat în limba română",
  "checklist": [
    {
      "id": "id-ul adaptării din catalog",
      "title": "Titlul adaptării",
      "why": "Explicație funcțională clară: de ce ajută această măsură la eficiența în muncă"
    }
  ]
}
"""

WHY_MAP: dict[str, str] = {
    "written_instructions": "Oferă claritate și reduce nevoia de memorare imediată a discuțiilor verbale.",
    "extra_time": "Permite asimilarea temeinică a instrumentelor și procedurilor specifice rolului.",
    "quiet_space": "Facilitează concentrarea susținută și reduce oboseala generată de stimulii sonori.",
    "flexible_schedule": "Ajută la gestionarea predictibilă a energiei de lucru și a deplasărilor zilnice.",
    "screen_reader_tools": "Asigură accesul direct și eficient la informațiile din documentele de lucru.",
    "captions_transcripts": "Permite urmărirea completă a deciziilor luate în ședințele de echipă.",
    "plain_language_docs": "Scurtează timpul necesar înțelegerii instrucțiunilor și procedurilor interne.",
    "regular_checkins": "Oferă un cadru structurat pentru clarificarea priorităților și feedback reciproc.",
    "task_breakdown": "Permite planificarea transparentă a etapelor și urmărirea termenelor intermediare.",
    "advance_agenda": "Asigură timpul necesar pentru pregătirea adecvată înainte de întâlniri.",
    "ergonomic_equipment": "Asigură un confort fizic adecvat pentru desfășurarea sarcinilor zilnice.",
    "remote_option": "Reduce solicitarea asociată deplasărilor și sprijină un ritm de lucru echilibrat.",
}


def build_user(
    items: list[dict[str, Any]],
    context: str = "onboarding",
    employer_name: str | None = None,
    tone: str = "friendly",
) -> str:
    """Builds the user prompt guiding the LLM to draft the accommodation request."""
    context_desc = {
        "interview": "pregătirea pentru un interviu de angajare",
        "onboarding": "primele săptămâni la noul loc de muncă (perioada de integrare/onboarding)",
        "ongoing": "activitatea curentă la locul de muncă",
    }.get(context, "integrarea la locul de muncă")

    tone_desc = {
        "formal": "formal, oficial și politicos",
        "friendly": "prietenos, cald și cooperant",
    }.get(tone, "profesional și cooperant")

    employer_str = employer_name if employer_name else "nespecificat"

    adaptations_lines = []
    for item in items:
        item_id = item.get("id", "")
        title = item.get("title", "")
        desc = item.get("description", "")
        example = item.get("example_request", "")
        adaptations_lines.append(
            f"- [{item_id}] {title}: {desc} (Model solicitare: „{example}”)"
        )
    adaptations_block = "\n".join(adaptations_lines)

    return f"""Generează o propunere structurată de solicitare a adaptărilor de lucru pe baza următorilor parametri:

Context: {context_desc}
Ton: {tone_desc}
Angajator / Companie: {employer_str}

Adaptări selectate din catalog:
{adaptations_block}

Cerințe:
1. Subiect concis și adecvat pentru context.
2. Corp de mesaj structurat (salut, descrierea măsurilor practice solicitate și beneficiul lor pentru munca de zi cu zi, propunere de discuție scurtă, încheiere).
3. Checklist cu fiecare adaptare selectată, conținând 'id', 'title' și 'why' (motivație funcțională).
4. Respectă cu strictețe regula: FĂRĂ termeni medicali sau diagnostice.
"""


def build_mock(
    items: list[dict[str, Any]],
    context: str = "onboarding",
    employer_name: str | None = None,
    tone: str = "friendly",
) -> dict[str, Any]:
    """Generates deterministic mock data tailored to the request parameters."""
    if context == "interview":
        subject = "Confirmare interviu și adaptări pentru desfășurarea întâlnirii"
        context_phrase = "în cadrul interviului"
    elif context == "ongoing":
        subject = "Propunere de adaptări funcționale pentru organizarea activității"
        context_phrase = "în desfășurarea activităților curente"
    else:
        subject = "Solicitare de adaptări funcționale în perioada de acomodare"
        context_phrase = "în primele săptămâni de la începerea activității"

    if employer_name:
        greeting = (
            f"Stimate/Stimată reprezentant(ă) {employer_name},"
            if tone == "formal"
            else f"Bună ziua, echipa {employer_name},"
        )
    else:
        greeting = "Stimate/Stimată manager," if tone == "formal" else "Bună ziua,"

    closing = (
        "Cu stimă și respect,\nEchipa"
        if tone == "formal"
        else "Cu drag și deschidere,\nEchipa"
    )

    item_titles = [it.get("title", "") for it in items if it.get("title")]
    titles_summary = ", ".join(item_titles) if item_titles else "adaptările agreate"

    body_ro = (
        f"{greeting}\n\n"
        f"Vă scriu pentru a vă prezenta câteva adaptări practice care mă vor sprijini "
        f"să lucrez cu randament și eficiență {context_phrase}: {titles_summary}.\n\n"
        f"Aceste ajustări organizatorice contribuie la claritatea sarcinilor și la o colaborare "
        f"cât mai bună în cadrul echipei. Vă mulțumesc pentru sprijin și rămân la dispoziție "
        f"pentru a agrea detaliile optime de implementare.\n\n"
        f"{closing}"
    )

    checklist = []
    for it in items:
        it_id = it.get("id", "")
        it_title = it.get("title", "")
        why = WHY_MAP.get(
            it_id,
            f"Sprijină autonomia și eficiența în realizarea sarcinilor prin {it_title.lower()}.",
        )
        checklist.append({"id": it_id, "title": it_title, "why": why})

    return {
        "subject": subject,
        "body_ro": body_ro,
        "checklist": checklist,
    }


MOCK: dict[str, Any] = {
    "subject": "Solicitare de adaptări în primele săptămâni",
    "body_ro": (
        "Bună ziua,\n\n"
        "Aș dori să discutăm câteva adaptări care mă ajută să lucrez eficient: "
        "instrucțiuni scrise, timp suplimentar la sarcini noi.\n\n"
        "Vă mulțumesc pentru colaborare,\n"
        "Echipa"
    ),
    "checklist": [
        {
            "id": "written_instructions",
            "title": "Instrucțiuni scrise, pas cu pas",
            "why": "Reduce nevoia de a reține informații spuse oral.",
        },
        {
            "id": "extra_time",
            "title": "Timp suplimentar pentru asimilarea procedurilor noi",
            "why": "Permite asimilarea temeinică a instrumentelor și procedurilor specifice rolului.",
        },
    ],
}
