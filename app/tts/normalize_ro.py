"""PrimaZi — Romanian Speech Normalizer (Backend Mirror)
Pure Python mirror of web/a11y/tts-normalize-ro.js.
Converts dates, times, currency amounts, legal citations, abbreviations,
alphanumeric IDs, and ordinals into natural spoken Romanian for TTS.

Ref: docs/TASKS-WAVE2.md A8, docs/CONTRACTS-WAVE2.md
"""
import re
from typing import Union

DIGITS_RO = {
    0: "zero",
    1: "unu",
    2: "doi",
    3: "trei",
    4: "patru",
    5: "cinci",
    6: "șase",
    7: "șapte",
    8: "opt",
    9: "nouă",
    10: "zece",
    11: "unsprezece",
    12: "doisprezece",
    13: "treisprezece",
    14: "paisprezece",
    15: "cincisprezece",
    16: "șaisprezece",
    17: "șaptesprezece",
    18: "optsprezece",
    19: "nouăsprezece",
    20: "douăzeci",
    30: "treizeci",
    40: "patruzeci",
    50: "cincizeci",
    60: "șaizeci",
    70: "șaptezeci",
    80: "optzeci",
    90: "nouăzeci",
}

HUNDREDS_RO = {
    100: "o sută",
    200: "două sute",
    300: "trei sute",
    400: "patru sute",
    500: "cinci sute",
    600: "șase sute",
    700: "șapte sute",
    800: "opt sute",
    900: "nouă sute",
}

MONTHS_RO = {
    "01": "ianuarie", "1": "ianuarie", "ian": "ianuarie",
    "02": "februarie", "2": "februarie", "feb": "februarie",
    "03": "martie", "3": "martie", "mar": "martie",
    "04": "aprilie", "4": "aprilie", "apr": "aprilie",
    "05": "mai", "5": "mai",
    "06": "iunie", "6": "iunie", "iun": "iunie",
    "07": "iulie", "7": "iulie", "iul": "iulie",
    "08": "august", "8": "august", "aug": "august",
    "09": "septembrie", "9": "septembrie", "sep": "septembrie", "sept": "septembrie",
    "10": "octombrie", "oct": "octombrie",
    "11": "noiembrie", "nov": "noiembrie",
    "12": "decembrie", "dec": "decembrie",
}


def number_to_words_ro(n: Union[int, str]) -> str:
    """Spoken number in Romanian for integers (0-9999)."""
    try:
        num = int(n)
    except (ValueError, TypeError):
        return str(n)

    if num in DIGITS_RO:
        return DIGITS_RO[num]
    if num < 100:
        tens = (num // 10) * 10
        units = num % 10
        return f"{DIGITS_RO[tens]} și {DIGITS_RO[units]}"
    if num < 1000:
        h = (num // 100) * 100
        rest = num % 100
        h_str = HUNDREDS_RO.get(h, f"{number_to_words_ro(num // 100)} sute")
        return h_str if rest == 0 else f"{h_str} {number_to_words_ro(rest)}"
    return str(num)


def normalize_ro_speech(text: str) -> str:
    """Normalises text for Romanian speech synthesis."""
    if not text or not isinstance(text, str):
        return ""

    res = text

    # 1. Legal / Article abbreviations
    res = re.sub(r"\b[Aa]rt\.\s*(\d+)", lambda m: f"articolul {number_to_words_ro(m.group(1))}", res)
    res = re.sub(r"\b[Aa]lin\.\s*(\d+)", lambda m: f"alineatul {number_to_words_ro(m.group(1))}", res)
    res = re.sub(r"\b[Nn]r\.\s*(\d+)", lambda m: f"numărul {m.group(1)}", res)
    res = re.sub(r"\b[Ll]egea\s*(\d+)/(\d+)", lambda m: f"Legea {m.group(1)} din {m.group(2)}", res)

    # 2. Common abbreviations
    res = re.sub(r"\b[Ee]x\.:", "de exemplu:", res)
    res = re.sub(r"\b[Ee]x\.\s+", "de exemplu ", res)
    res = re.sub(r"\betc\.", "și așa mai departe.", res, flags=re.IGNORECASE)
    res = re.sub(r"\bvs\.", "față de", res, flags=re.IGNORECASE)
    res = re.sub(r"\baprox\.", "aproximativ", res, flags=re.IGNORECASE)
    res = re.sub(r"\bpt\.", "pentru", res, flags=re.IGNORECASE)
    res = re.sub(r"\bstr\.", "strada", res, flags=re.IGNORECASE)

    # 3. Alphanumeric IDs and technical tokens (e.g. F-12, A-4, P-1)
    res = re.sub(
        r"\b([A-Za-z])-(\d+)\b",
        lambda m: f"{m.group(1).upper()} {number_to_words_ro(m.group(2))}",
        res,
    )

    # 4. Time formats: e.g. 14:00, 09:30, 9:15, ora 16:45
    def _format_hour(hour: int) -> str:
        if hour == 1:
            return "unu"
        if hour == 2:
            return "două"
        if hour == 12:
            return "douăsprezece"
        if hour == 21:
            return "douăzeci și unu"
        if hour == 22:
            return "douăzeci și două"
        return number_to_words_ro(hour)

    def _replace_time_00(m: re.Match) -> str:
        hour = int(m.group(1))
        return f"ora {_format_hour(hour)}"

    def _replace_time_min(m: re.Match) -> str:
        hour = int(m.group(1))
        min_val = int(m.group(2))
        hour_words = _format_hour(hour)
        if min_val == 30:
            return f"ora {hour_words} și jumătate"
        if min_val == 15:
            return f"ora {hour_words} și un sfert"
        return f"ora {hour_words} și {number_to_words_ro(min_val)} minute"

    res = re.sub(r"(?:ora\s+)?\b(\d{1,2}):00\b", _replace_time_00, res, flags=re.IGNORECASE)
    res = re.sub(r"(?:ora\s+)?\b(\d{1,2}):(\d{2})\b", _replace_time_min, res, flags=re.IGNORECASE)

    # 5. Dates: e.g. 28.10.2026, 28/10/2026, 2026-10-28
    def _replace_date_dmy(m: re.Match) -> str:
        day = int(m.group(1))
        month = MONTHS_RO.get(m.group(2), m.group(2))
        year = m.group(3)
        return f"{day} {month} {year}"

    def _replace_date_ymd(m: re.Match) -> str:
        year = m.group(1)
        month = MONTHS_RO.get(m.group(2), m.group(2))
        day = int(m.group(3))
        return f"{day} {month} {year}"

    res = re.sub(r"\b(\d{1,2})[\./](\d{1,2})[\./](\d{4})\b", _replace_date_dmy, res)
    res = re.sub(r"\b(\d{4})-(\d{2})-(\d{2})\b", _replace_date_ymd, res)

    # 6. Currency amounts: e.g. 500 lei, 50 RON, 100 EUR, 15 euro
    def _replace_currency_lei(m: re.Match) -> str:
        n = int(m.group(1))
        if n == 1:
            return "un leu"
        mod100 = n % 100
        needs_de = n >= 20 and (mod100 == 0 or mod100 >= 20)
        prep = " de lei" if needs_de else " lei"
        return f"{number_to_words_ro(n)}{prep}"

    def _replace_currency_eur(m: re.Match) -> str:
        n = int(m.group(1))
        if n == 1:
            return "un euro"
        mod100 = n % 100
        needs_de = n >= 20 and (mod100 == 0 or mod100 >= 20)
        prep = " de euro" if needs_de else " euro"
        return f"{number_to_words_ro(n)}{prep}"

    res = re.sub(r"\b(\d+)\s*(?:lei|leu|RON)\b", _replace_currency_lei, res, flags=re.IGNORECASE)
    res = re.sub(r"\b(\d+)\s*(?:EUR|euro)\b", _replace_currency_eur, res, flags=re.IGNORECASE)

    # 7. Ordinals: e.g. al 2-lea, a 3-a, 1-ul
    res = re.sub(r"\bal\s*1-lea\b", "primul", res, flags=re.IGNORECASE)
    res = re.sub(r"\ba\s*1-a\b", "prima", res, flags=re.IGNORECASE)
    res = re.sub(r"\b1-ul\b", "primul", res, flags=re.IGNORECASE)
    res = re.sub(r"\bal\s*2-lea\b", "al doilea", res, flags=re.IGNORECASE)
    res = re.sub(r"\ba\s*2-a\b", "a doua", res, flags=re.IGNORECASE)
    res = re.sub(r"\bal\s*3-lea\b", "al treilea", res, flags=re.IGNORECASE)
    res = re.sub(r"\ba\s*3-a\b", "a treia", res, flags=re.IGNORECASE)
    res = re.sub(r"\bal\s*4-lea\b", "al patrulea", res, flags=re.IGNORECASE)
    res = re.sub(r"\ba\s*4-a\b", "a patra", res, flags=re.IGNORECASE)
    res = re.sub(r"\bal\s*5-lea\b", "al cincilea", res, flags=re.IGNORECASE)
    res = re.sub(r"\ba\s*5-a\b", "a cincea", res, flags=re.IGNORECASE)

    # 8. Clean up extra punctuation/spaces
    res = re.sub(r"\s{2,}", " ", res).strip()

    return res


# Alias to match JavaScript name if needed
normalize_romanian_for_speech = normalize_ro_speech
