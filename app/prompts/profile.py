from typing import Any

SYSTEM = """Ești un asistent empatic de accesibilitate și ergonomie la locul de muncă (nume produs: PrimaZi).
Rolul tău este să asculți nevoile de lucru exprimate de un angajat în cuvintele proprii și să recomanzi adaptări funcționale pentru spațiul de lucru și preferințe de afișare vizuală.

REGULI STRICTE DE ETICĂ ȘI CONFIDENȚIALITATE:
1. FĂRĂ DIAGNOSTICE MEDICALE: Nu numi, nu eticheta și nu deduce afecțiuni clinice sau tulburări (fără autism, ADHD, dislexie, anxietate etc.). Conectează doar nevoile practice exprimate (ex: zgomot, oboseală vizuală, atenție, text dens) cu soluții funcționale.
2. Ton cald, primitor, respectuos și încurajator. Angajatul trebuie să se simtă ascultat și sprijinit.
3. Configurează dicționarul de setări (settings) folosind cheile din docs/settings.schema.json, oferă o listă de motive (reasons cu cheie și motiv în română), o listă de adaptări la locul de muncă (adaptations cu ID-uri din catalog), plus compatibilitate veche (ui_prefs, recommended_adjustments).
4. Răspunde exclusiv în limba română cu diacritice corecte.
"""

MOCK: dict[str, Any] = {
    "summary_ro": (
        "Pe baza nevoilor descrise, am configurat o interfață adaptată confortului tău: "
        "format structurat în pași, font clar și contrast odihnitor, alături de adaptări "
        "pentru un mediu de lucru predictibil și eficient."
    ),
    "settings": {
        "version": 2,
        "theme": "amber",
        "font_family": "atkinson",
        "font_scale": 125,
        "line_height": 1.7,
        "letter_spacing": 0.03,
        "word_spacing": 0.06,
        "paragraph_spacing": 1.2,
        "measure": 68,
        "font_weight": 400,
        "link_style": "underline-always",
        "saturation": 100,
        "color_vision": "none",
        "focus_ring": "normal",
        "cursor_size": "normal",
        "dim_overlay": 15,
        "reduce_motion": "auto",
        "reduce_transparency": False,
        "focus_level": 0,
        "density": "comfortable",
        "layout": "overview",
        "sidebar": "expanded",
        "summary_first": True,
        "chunk_size": "all",
        "progressive_disclosure": False,
        "glossary_inline": "hover/tap",
        "reading_ruler": "off",
        "ruler_height": 32,
        "ruler_color": "rgba(255, 235, 59, 0.25)",
        "focus_paragraph": False,
        "bionic": False,
        "reading_level": "simple",
        "format": "steps",
        "tone_notes": "off",
        "break_reminders": "off",
        "confirm_actions": True,
        "calm_mode": False,
        "tts_engine": "auto",
        "tts_voice": "auto",
        "tts_rate": 0.95,
        "tts_pitch": 1.0,
        "tts_volume": 1.0,
        "tts_pause_ms": 350,
        "tts_follow": "sentence",
        "tts_autoread": "off",
        "tts_spoken_numbers": True,
        "captions_default": True,
        "transcript_always": True,
        "visual_alerts": True,
        "vibration_alerts": False,
        "sound_effects": "off",
        "highlight_mode": "light",
        "highlight_categories": ["action", "deadline", "warning"],
        "highlight_style": "combo",
        "highlight_scale": 110,
        "highlight_palette": "multi",
        "target_size": 48,
        "target_gap": 12,
        "keyboard_shortcuts": True,
        "single_key_shortcuts": False,
        "voice_commands": False,
        "tooltips_on_focus_click": True,
        "no_drag": True,
        "sr_mode": False,
        "announce_level": "polite",
        "describe_images": "ask",
        "magnify_focus": False,
        "ui_language": "ro",
        # Aliases
        "scale": 125,
        "font": "atkinson",
        "contrast": "standard",
        "spacing": "standard",
        "focus": 0,
        "cursor": "normal",
        "screen_reader": False,
        "simple_mode": True,
    },
    "reasons": [
        {
            "key": "theme",
            "reason_ro": "Temă caldă amber pentru a reduce oboseala ochilor și strălucirea ecranului.",
        },
        {
            "key": "dim_overlay",
            "reason_ro": "Atenuare a intensității luminii pentru confort la expunere prelungită.",
        },
        {
            "key": "format",
            "reason_ro": "Organizare în pași clari pentru a urmări ușor sarcinile de lucru.",
        },
        {
            "key": "font_scale",
            "reason_ro": "Dimensiune mărită a textului la 125% pentru citire relaxată.",
        },
    ],
    "adaptations": ["written_instructions", "quiet_space", "extra_time"],
    "ui_prefs": {
        "textSize": "large",
        "font": "atkinson",
        "contrast": "standard",
        "spacing": "relaxed",
        "bionic": False,
        "highlightKeyTerms": True,
        "motion": "standard",
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


def build_user(user_words: str, chips: list[str] | None = None) -> str:
    chips_section = ""
    if chips:
        chips_str = ", ".join(chips)
        chips_section = f"\nEtichete de preferințe selectate: {chips_str}\n"

    return (
        f"--- NEVOILE EXPRIMATE DE UTILIZATOR ÎN CUVINTELE PROPRII ---\n"
        f"{user_words}{chips_section}\n"
        f"--- SFÂRȘIT MESAJ ---\n\n"
        f"Analizează aceste nevoi funcționale și generează recomandările conforme "
        f"cu specificația Wave 2: dicționarul de setări (settings), lista de motive "
        f"(reasons cu cheie și motiv în română), lista identificatorilor de adaptare "
        f"(adaptations) și setările vechi compatibile (ui_prefs, recommended_adjustments)."
    )
