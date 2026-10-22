from typing import Any

SYSTEM = """Ești un asistent empatic de accesibilitate și ergonomie la locul de muncă (nume produs: PrimaZi).
Rolul tău este să asculți nevoile de lucru exprimate de un angajat în cuvintele proprii și să recomanzi adaptări funcționale pentru spațiul de lucru și preferințe de afișare vizuală.

REGULI STRICTE DE ETICĂ ȘI CONFIDENȚIALITATE:
1. FĂRĂ DIAGNOSTICE MEDICALE: Nu numi, nu eticheta și nu deduce afecțiuni clinice sau tulburări (fără autism, ADHD, dislexie, anxietate etc.). Conectează doar nevoile practice exprimate (ex: zgomot, oboseală vizuală, atenție, text dens) cu soluții funcționale.
2. Ton cald, primitor, respectuos și încurajator. Angajatul trebuie să se simtă ascultat și sprijinit.
3. Adaptează setările de interfață (ui_prefs) și selectează adaptările funcționale relevante din catalogul oficial de bune practici.
4. Răspunde exclusiv în limba română cu diacritice corecte.
"""

MOCK: dict[str, Any] = {
    "summary_ro": "Pe baza nevoilor descrise, am configurat o interfață aerisită, cu pași clari și text evidențiat, alături de recomandări pentru un mediu de lucru predictibil și liniștit.",
    "ui_prefs": {
        "textSize": "large",
        "font": "opendyslexic",
        "contrast": "standard",
        "spacing": "relaxed",
        "bionic": True,
        "highlightKeyTerms": True,
        "motion": "reduced",
        "readingLevel": "simple",
        "format": "steps",
        "audioSupport": True,
    },
    "recommended_adjustments": [
        {
            "id": "written_instructions",
            "title": "Instrucțiuni scrise, pas cu pas",
            "description": "Sarcinile noi sau complexe sunt transmise și în format scris, structurate în etape scurte și clare.",
            "legal_basis_ro": "Art. 78 Legea 448/2006 și bună practică generală",
            "relevance_reason_ro": "Te ajută să revizuiești cerințele în ritmul propriu, fără să fie nevoie să memorezi instrucțiuni verbale lungi.",
        },
        {
            "id": "quiet_space",
            "title": "Spațiu de lucru liniștit și reducerea zgomotului",
            "description": "Amplasarea biroului într-o zonă ferită de zgomot intens sau posibilitatea de a utiliza căști antifonice.",
            "legal_basis_ro": "Bună practică de ergonomie a muncii",
            "relevance_reason_ro": "Reduce stimulii auditivi perturbatori și sprijină concentrarea susținută pe sarcinile curente.",
        },
        {
            "id": "extra_time",
            "title": "Timp suplimentar pentru asimilarea procedurilor noi",
            "description": "Intervale de lucru extinse pentru parcurgerea materialelor noi de lucru.",
            "legal_basis_ro": "Bună practică generală",
            "relevance_reason_ro": "Asigură un ritm de asimilare fără grabă sau presiune artificială în primele săptămâni.",
        },
    ],
    "disclaimer_ro": (
        "Informativ: PrimaZi nu stochează pe server nevoile tale și nu formulează "
        "diagnostice medicale. Recomandările sunt exclusiv funcționale pentru confort la locul de muncă."
    ),
}


def build_user(user_words: str) -> str:
    return (
        f"--- NEVOILE EXPRIMATE DE UTILIZATOR ÎN CUVINTELE PROPRII ---\n"
        f"{user_words}\n"
        f"--- SFÂRȘIT MESAJ ---\n\n"
        f"Analizează aceste nevoi funcționale și generează recomandările de confort "
        f"vizual/cognitiv (ui_prefs) și adaptările recomandate la locul de muncă."
    )
