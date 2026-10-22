/**
 * PrimaZi — Romanian Speech Normalizer (Wave 2)
 * Pure function converting dates, times, currency amounts, legal codes,
 * abbreviations, and ordinals into natural spoken Romanian for TTS.
 * Ref: docs/TASKS-WAVE2.md A3
 */

const DIGITS_RO = {
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
  90: "nouăzeci"
};

const HUNDREDS_RO = {
  100: "o sută",
  200: "două sute",
  300: "trei sute",
  400: "patru sute",
  500: "cinci sute",
  600: "șase sute",
  700: "șapte sute",
  800: "opt sute",
  900: "nouă sute"
};

const MONTHS_RO = {
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
  "12": "decembrie", "dec": "decembrie"
};

/**
 * Spoken number in Romanian for integers (0–9999).
 */
export function numberToWordsRo(n) {
  const num = parseInt(n, 10);
  if (Number.isNaN(num)) return String(n);
  if (DIGITS_RO[num]) return DIGITS_RO[num];
  if (num < 100) {
    const tens = Math.floor(num / 10) * 10;
    const units = num % 10;
    return `${DIGITS_RO[tens]} și ${DIGITS_RO[units]}`;
  }
  if (num < 1000) {
    const h = Math.floor(num / 100) * 100;
    const rest = num % 100;
    const hStr = HUNDREDS_RO[h] || `${numberToWordsRo(Math.floor(num / 100))} sute`;
    return rest === 0 ? hStr : `${hStr} ${numberToWordsRo(rest)}`;
  }
  return String(num);
}

/**
 * Normalises text for Romanian speech synthesis.
 * @param {string} text
 * @returns {string}
 */
export function normalizeRomanianForSpeech(text) {
  if (!text || typeof text !== "string") return "";

  let res = text;

  // 1. Legal / Article abbreviations
  res = res.replace(/\b[Aa]rt\.\s*(\d+)/g, (_, n) => `articolul ${numberToWordsRo(n)}`);
  res = res.replace(/\b[Aa]lin\.\s*(\d+)/g, (_, n) => `alineatul ${numberToWordsRo(n)}`);
  res = res.replace(/\b[Nn]r\.\s*(\d+)/g, (_, n) => `numărul ${n}`);
  res = res.replace(/\b[Ll]egea\s*(\d+)\/(\d+)/g, (_, n, y) => `Legea ${n} din ${y}`);

  // 2. Common abbreviations
  res = res.replace(/\b[Ee]x\.:/g, "de exemplu:");
  res = res.replace(/\b[Ee]x\.\s+/g, "de exemplu ");
  res = res.replace(/\betc\./gi, "și așa mai departe.");
  res = res.replace(/\bvs\./gi, "față de");
  res = res.replace(/\baprox\./gi, "aproximativ");
  res = res.replace(/\bpt\./gi, "pentru");
  res = res.replace(/\bstr\./gi, "strada");

  // 3. Alphanumeric IDs and technical tokens (e.g. F-12, A-4, P-1)
  res = res.replace(/\b([A-Za-z])-(\d+)\b/g, (_, letter, num) => `${letter.toUpperCase()} ${numberToWordsRo(num)}`);

  // 4. Time formats: e.g. 14:00, 09:30, 9:15, ora 16:45
  function formatHourRo(hour) {
    if (hour === 1) return "unu";
    if (hour === 2) return "două";
    if (hour === 12) return "douăsprezece";
    if (hour === 21) return "douăzeci și unu";
    if (hour === 22) return "douăzeci și două";
    return numberToWordsRo(hour);
  }

  res = res.replace(/(?:ora\s+)?\b(\d{1,2}):00\b/gi, (_, h) => {
    const hour = parseInt(h, 10);
    return `ora ${formatHourRo(hour)}`;
  });
  res = res.replace(/(?:ora\s+)?\b(\d{1,2}):(\d{2})\b/gi, (_, h, m) => {
    const hour = parseInt(h, 10);
    const min = parseInt(m, 10);
    const hourWords = formatHourRo(hour);
    if (min === 30) return `ora ${hourWords} și jumătate`;
    if (min === 15) return `ora ${hourWords} și un sfert`;
    return `ora ${hourWords} și ${numberToWordsRo(min)} minute`;
  });

  // 5. Dates: e.g. 28.10.2026, 28/10/2026, 2026-10-28
  res = res.replace(/\b(\d{1,2})[\.\/](\d{1,2})[\.\/](\d{4})\b/g, (_, d, m, y) => {
    const day = parseInt(d, 10);
    const month = MONTHS_RO[m] || m;
    return `${day} ${month} ${y}`;
  });
  res = res.replace(/\b(\d{4})-(\d{2})-(\d{2})\b/g, (_, y, m, d) => {
    const day = parseInt(d, 10);
    const month = MONTHS_RO[m] || m;
    return `${day} ${month} ${y}`;
  });

  // 6. Currency amounts: e.g. 500 lei, 50 RON, 100 EUR, 150 euro
  res = res.replace(/\b(\d+)\s*(?:lei|RON)\b/gi, (_, amount) => {
    const n = parseInt(amount, 10);
    const mod100 = n % 100;
    const needsDe = n >= 20 && (mod100 === 0 || mod100 >= 20);
    const prep = needsDe ? " de lei" : (n === 1 ? " leu" : " lei");
    return `${numberToWordsRo(n)}${prep}`;
  });
  res = res.replace(/\b(\d+)\s*(?:EUR|euro)\b/gi, (_, amount) => {
    const n = parseInt(amount, 10);
    const mod100 = n % 100;
    const needsDe = n >= 20 && (mod100 === 0 || mod100 >= 20);
    const prep = needsDe ? " de euro" : " euro";
    return `${numberToWordsRo(n)}${prep}`;
  });

  // 7. Ordinals: e.g. al 2-lea, a 3-a, 1-ul
  res = res.replace(/\bal\s*1-lea\b/gi, "primul");
  res = res.replace(/\ba\s*1-a\b/gi, "prima");
  res = res.replace(/\bal\s*2-lea\b/gi, "al doilea");
  res = res.replace(/\ba\s*2-a\b/gi, "a doua");
  res = res.replace(/\bal\s*3-lea\b/gi, "al treilea");
  res = res.replace(/\ba\s*3-a\b/gi, "a treia");

  // 8. Clean up extra punctuation/spaces
  res = res.replace(/\s{2,}/g, " ").trim();

  return res;
}
