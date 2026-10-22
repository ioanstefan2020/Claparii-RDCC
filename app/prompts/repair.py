from app.prompts.versions import PROMPT_VERSIONS

VERSION = PROMPT_VERSIONS["repair"]

SYSTEM_REPAIR_RO = """Ești un corector de structură JSON.
Răspunsul anterior a eșuat validarea: {error}.
SARCINĂ: Returnează DOAR un obiect JSON valid care respectă strict schema cerută, corectând erorile de sintaxă sau câmpurile lipsă.
Păstrează toate valorile corecte deja extrase. Nu include text înainte sau după JSON, fără markdown fences."""


def build_repair_user(raw_broken_output: str, error_msg: str) -> str:
    return (
        f"Ieșirea precedentă a eșuat cu eroarea: {error_msg}\n\n"
        f"Conținutul brut de reparat:\n{raw_broken_output}\n\n"
        "Returnează JSON-ul valid corectat acum:"
    )
