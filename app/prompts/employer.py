"""Romanian prompts and mock data for employer document cognitive accessibility analysis.

Enforces responsible-AI principles:
- Strictly evaluates the document's cognitive accessibility, structure, and clarity.
- Scores documents, NEVER candidates, employees, or individuals.
- Grounding: every issue quote must appear verbatim in the input document.
- Functional recommendations mapped to workplace accommodations without diagnoses.
"""
from __future__ import annotations

from typing import Any

SYSTEM: str = """Ești un expert în accesibilitate cognitivă și comunicare incluzivă la locul de muncă (Plain Romanian / Limbaj Clar), conform standardelor europene de accesibilitate a informației.

ROLUL TĂU:
Analizezi documente profesionale (ghiduri de onboarding, anunțuri de recrutare, politici interne, instrucțiuni de lucru) pentru a le crește claritatea și accesibilitatea cognitivă pentru orice nou angajat, inclusiv persoane neurodivergente sau cu dizabilități.

REGULI STRICTE DE RESPONSABILITATE AI:
1. Evaluezi și notezi EXCLUSIV documentul (lungime, jargon, structură, claritate). NU evaluezi, nu etichetezi și nu judeci NICIODATĂ o persoană, un candidat sau un angajat.
2. NU cere, nu deduce și nu menționa diagnostice medicale sau afecțiuni clinice. Toate recomandările sunt măsuri organizaționale funcționale la locul de muncă.
3. GROUNDING OBLIGATORIU: Pentru fiecare problemă identificată în 'issues', câmpul 'quote' TREBUIE să fie un fragment reprodus EXACT, cuvânt cu cuvânt (verbatim) din textul furnizat. Nu inventa și nu parafraza citatul.
4. 'kind' trebuie să fie unul dintre:
   - "jargon": termeni corporatiști, limbaj tehnic neexplicat, acronime neclare (ex: „autonomie operațională”, „KPI-uri”).
   - "long_sentence": fraze excesiv de lungi sau încâlcite ce îngreunează urmărirea ideilor.
   - "missing_deadline": cerințe sau sarcini unde lipsește termenul exact (data/ora) sau este vag formulat.
   - "vague_instruction": instrucțiuni abstracte sau ambigue ce nu specifică acțiunea concretă cerută.
   - "missing_structure": blocuri dense de text fără enumerări sau delimitare clară a etapelor.
5. 'easy_read_ro': O rescriere completă a documentului în format Easy-to-Read (Limbaj Simplificat) în limba română: fraze scurte, diacritice corecte, pași enumerați cu liniuță, date și contacte clar evidențiate.
6. 'adjustment_checklist': 1-3 adaptări recomandate din catalogul standard de bune practici (id-uri valide: plain_language_docs, written_instructions, task_breakdown, extra_time, regular_checkins, advance_agenda, flexible_schedule).

SCHEMA JSON CERUTĂ (răspunde DOAR cu JSON valid conform schemei):
{
  "issues": [
    {
      "kind": "jargon | long_sentence | missing_deadline | vague_instruction | missing_structure",
      "quote": "citat exact din text",
      "fix": "recomandare concretă de formulare în limbaj simplu"
    }
  ],
  "easy_read_ro": "Textul rescris în limbaj ușor de înțeles, structurat clar...",
  "adjustment_checklist": [
    {
      "id": "id_adaptare_din_catalog",
      "title": "Titlul adaptării"
    }
  ]
}
"""


def build_user(text: str, doc_type: str = "onboarding") -> str:
    """Builds user prompt for document accessibility analysis."""
    doc_type_names = {
        "onboarding": "ghid de acomodare / integrare (onboarding)",
        "job_ad": "anunț de angajare / recrutare",
        "policy": "regulament intern / politică organizațională",
        "other": "document de lucru",
    }
    type_ro = doc_type_names.get(doc_type, "document de lucru")

    return f"""Analizează următorul {type_ro} din perspectiva accesibilității cognitive și a clarității instrucțiunilor.

Identifică problemele concrete de jargon, fraze lungi sau ambiguități (cu citate exacte din text), oferă o rescriere în limbaj simplu (easy_read_ro) și recomandă adaptări de lucru potrivite:

--- ÎNCEPUT DOCUMENT ---
{text}
--- SFÂRȘIT DOCUMENT ---
"""


MOCK: dict[str, Any] = {
    "issues": [
        {
            "kind": "jargon",
            "quote": "autonomie operațională",
            "fix": "Spune concret ce sarcini poate rezolva noul coleg singur și unde primește îndrumare.",
        },
        {
            "kind": "vague_instruction",
            "quote": "alinierea la cultura organizațională și la valorile companiei",
            "fix": "Specifică 2-3 exemple practice de colaborare dorite în echipă.",
        },
        {
            "kind": "long_sentence",
            "quote": "În prima lună se așteaptă să atingi nivelul de autonomie operațională prevăzut în planul 30-60-90, în conformitate cu KPI-urile agreate cu managerul, având în vedere alinierea la cultura organizațională și la valorile companiei.",
            "fix": "Împarte fraza în 2 propoziții scurte: una despre obiectivele lunare și una despre modul de lucru în echipă.",
        },
    ],
    "easy_read_ro": (
        "Bine ai venit în echipa Companie Exemplu SRL!\n\n"
        "Ce ai de făcut în prima săptămână:\n"
        "• Luni, ora 09:00: Mergi la recepția clădirii B pentru cardul de acces. Persoana de contact este Mihaela Popescu (HR).\n"
        "• Luni, ora 10:00: Discuție cu managerul tău, Andrei Ionescu. Primești laptopul și conturile de acces.\n"
        "• Până miercuri, 28 octombrie: Completează formularul F-12 și semnează politica SecInfo v3 în portalul intern.\n"
        "• Joi, ora 14:00: Curs online obligatoriu de securitate cibernetică (vei primi link pe e-mail).\n"
        "• Până vineri, 30 octombrie: Parcurge cursul introductiv și trimite un rezumat de o pagină managerului.\n\n"
        "În prima lună:\n"
        "• Vei discuta periodic cu managerul obiectivele stabilite pentru primele 30 de zile.\n\n"
        "Adaptări la locul de muncă:\n"
        "• Dacă ai nevoie de ajustări ale spațiului sau programului de lucru, trimite un e-mail către HR la hr@exemplu.example în primele 14 zile."
    ),
    "adjustment_checklist": [
        {
            "id": "plain_language_docs",
            "title": "Ghiduri și documente în limbaj simplu",
        },
        {
            "id": "written_instructions",
            "title": "Instrucțiuni scrise, pas cu pas",
        },
        {
            "id": "task_breakdown",
            "title": "Segmentarea proiectelor în etape mici și prioritizate",
        },
    ],
}
