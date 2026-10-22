from typing import Any

from app.prompts.base import BASE_SYSTEM_RO

VERSION = "2.0"

SYSTEM = f"""{BASE_SYSTEM_RO}

SARCINĂ DESCRIERE IMAGINE PENTRU ACCESIBILITATE:
Rolul tău este să descrii imaginea pentru o persoană cu deficiențe de vedere sau care dorește să înțeleagă conținutul vizual la serviciu.
În funcție de `purpose`:
- `alt_text`: o descriere clară, concisă (1-3 fraze) a elementelor vizuale esențiale.
- `read_text`: extragerea textului lizibil vizibil în imagine și descrierea aranjamentului.
- `chart`: explicarea tipului de grafic, axelor, tendinței generale și valorilor cheie.
- `document`: descrierea tipului de formular/document, antetului și secțiunilor principale.

REGULI OBLIGATORII:
1. Răspunde strict în limba română cu diacritice corecte.
2. Nu inventa informații care nu se văd clar.
3. Menționează explicit în `confidence_note` că utilizatorul trebuie să verifice datele importante.
4. Returnează strict un obiect JSON:
{{
  "description_ro": "...",
  "text_found": "..." sau null,
  "confidence_note": "Descriere generată de AI — verifică datele sau textul important cu o persoană de sprijin."
}}
"""

MOCK_DESCRIPTIONS: dict[str, dict[str, Any]] = {
    "alt_text": {
        "description_ro": "Imaginea prezintă un spațiu de birou modern, cu birouri de lucru, monitoare și iluminare naturală. În fundal se observă o zonă comună de relaxare.",
        "text_found": None,
        "confidence_note": "Descriere generată de AI — verifică detaliile specifice dacă sunt critice.",
    },
    "read_text": {
        "description_ro": "Document tipărit ce conține instrucțiuni introductive de serviciu.",
        "text_found": "PROGRAM DE LUCRU: Luni-Vineri 09:00 - 17:30. Pauză de masă: 13:00 - 14:00.",
        "confidence_note": "Text extras automat din imagine — verifică datele cu o persoană de contact.",
    },
    "chart": {
        "description_ro": "Grafic cu bare verticale reprezentând progresul săptămânal al sarcinilor finalizate de echipă. Barele indică o creștere constantă spre finalul lunii.",
        "text_found": "Săptămâna 1: 12 sarcini, Săptămâna 2: 18 sarcini, Săptămâna 3: 25 sarcini.",
        "confidence_note": "Interpretare grafică automată — verifică valorile exacte din tabelul sursă.",
    },
    "document": {
        "description_ro": "Formular administrativ intern cu antetul companiei, cuprinzând câmpuri pentru nume, funcție, departament și dată.",
        "text_found": "FORMULAR INTERN F-12 / DATE ANGAJAT NOU",
        "confidence_note": "Descriere automată a formularului — verifică cerințele specifice la HR.",
    },
}
