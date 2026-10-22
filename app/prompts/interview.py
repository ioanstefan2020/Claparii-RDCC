from typing import Any

from app.schemas.simplify import UserProfile

SYSTEM = """Ești un asistent empatic și profesionist pentru pregătirea primului interviu de angajare (produsul PrimaZi).
Ajuți tineri candidați (inclusiv persoane neurodivergente sau cu dizabilități) să se pregătească practic pentru un interviu de angajare pe baza descrierii postului.

REGULI STRICTE:
1. FĂRĂ DIAGNOSTICE: Nu menționa, nu cere și nu deduce diagnostice medicale sau etichete clinice. Orice adaptare recomandată trebuie să fie una funcțională și practică de la locul de muncă (ex: instrucțiuni scrise, timp suplimentar, reducerea zgomotului, agendă trimisă în avans).
2. FĂRĂ EVALUĂRI EMOȚIONALE: Nu judeca emoțiile sau psihologia candidatului. Oferă recomandări practice de comunicare structurată.
3. LIMBAJ CLAR ȘI ACCESIBIL: Folosește limba română clară, cu diacritice corecte, propoziții directe și ton încurajator.
4. RĂSPUNSURI STRICT STRUCTURATE ÎN FORMAT JSON:
   - overview_ro: Sinteză scurtă în limbaj simplu despre specificul rolului și ce caută angajatorul.
   - common_questions: Listă de 2-4 întrebări probabile, de ce sunt puse și cum poate aborda răspunsul fără stres.
   - suggested_adjustments: 2-3 adaptări funcționale din catalog (ex: written_instructions, extra_time, task_breakdown) și argumente practice (talking points) fără dezvăluirea vreunui diagnostic.
   - questions_to_ask_employer: 2-3 întrebări concrete pe care candidatul le poate pune angajatorului pentru a înțelege organizarea echipei.
"""

MOCK: dict[str, Any] = {
    "overview_ro": (
        "Pregătire pentru interviul de angajare. Rolul pune accent pe învățare, atenție la detalii "
        "și comunicare deschisă în echipă. Scopul este să arăți cum lucrezi practic și organizat."
    ),
    "common_questions": [
        {
            "question_ro": "Cum îți organizezi sarcinile zilnice atunci când primești mai multe cerințe în același timp?",
            "why_asked_ro": "Angajatorul dorește să afle dacă ai o metodă structurată de prioritizare și dacă ceri îndrumare când e nevoie.",
            "suggested_approach_ro": (
                "Răspunde calm: menționează că notezi cerințele în scris, ceri clarificări pentru ordinea priorităților "
                "și lucrezi la câte o sarcină pe rând până la finalizare."
            ),
        },
        {
            "question_ro": "Povestește-ne despre o situație în care ai învățat o procedură nouă sau ai folosit o unealtă nouă.",
            "why_asked_ro": "Se urmărește curiozitatea, răbdarea în procesul de învățare și capacitatea de a urmări instrucțiuni.",
            "suggested_approach_ro": (
                "Alege un exemplu concret (un proiect școlar, un curs sau o aplicație nouă). "
                "Explică pe scurt pașii urmați și cum ai verificat că ai rezolvat corect."
            ),
        },
        {
            "question_ro": "Ce faci dacă nu înțelegi pe deplin o instrucțiune primită de la coordonatorul tău?",
            "why_asked_ro": "Echipa vrea să vadă că nu eziți să ceri clarificări înainte de a face presupuneri.",
            "suggested_approach_ro": (
                "Spune deschis că preferi să ceri o reformulare sau un exemplu scris, economisind astfel timpul echipei."
            ),
        },
    ],
    "suggested_adjustments": [
        {
            "id": "written_instructions",
            "title": "Instrucțiuni scrise, pas cu pas",
            "talking_point_ro": (
                "„Lucrez cel mai rapid și precis când cerințele tehnice sau procedurile sunt transmise și în scris, "
                "cu pași bine delimitați.”"
            ),
        },
        {
            "id": "task_breakdown",
            "title": "Împărțirea sarcinilor complexe în etape intermediare",
            "talking_point_ro": (
                "„Mă ajută să confirm împreună cu mentorul etapele intermediare ale sarcinilor mari pentru a valida ritmul de lucru.”"
            ),
        },
    ],
    "questions_to_ask_employer": [
        "Cum arată o zi obișnuită de lucru pentru această poziție în primele săptămâni?",
        "Cum sunt transmise sarcinile zilnice (prin tichete scrise, email sau discuții scurte)?",
        "Există un mentor sau o persoană de contact dedicată pentru îndrumare la început?",
    ],
}


def build_user(
    job_title: str,
    job_description: str,
    profile: UserProfile | None = None,
) -> str:
    p = profile or UserProfile()
    return (
        f"TITLU POST: {job_title}\n"
        f"PREFERINȚE UTILIZATOR: nivel_citire={p.reading_level}, format={p.format}\n\n"
        f"--- DESCRIERE ANUNȚ SAU POST ---\n"
        f"{job_description}\n"
        f"--- SFÂRȘIT DESCRIERE ---\n\n"
        "Generează ghidul practic de pregătire a interviului respectând schema JSON solicitată."
    )
