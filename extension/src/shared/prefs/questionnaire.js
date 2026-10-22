/**
 * Questionnaire Content & Mapping: Bilingual plain-language comfort questions (owner: p2).
 * Conforms to docs/NEXT-STEPS.md §1 & §2.
 * STRICT RESPONSIBLE AI RULE: Zero medical questions, zero diagnosis words, zero emotion inference.
 */

export const QUESTIONNAIRE_RO = Object.freeze([
  {
    id: "readingPace",
    prompt: "Cum preferi să parcurgi textele de lucru?",
    helpText: "Setăm mărimea fontului și spațierea dintre rânduri pentru confortul tău vizual.",
    options: [
      {
        value: "slow",
        label: "Ritm liniștit",
        description: "Text mai mare, spațiere generoasă între rânduri și litere.",
      },
      {
        value: "medium",
        label: "Ritm standard",
        description: "Dimensiune obișnuită și aranjare clasică a paginii.",
      },
      {
        value: "fast",
        label: "Ritm rapid",
        description: "Format compact, mai mult conținut vizibil dintr-o privire.",
      },
    ],
  },
  {
    id: "textAmount",
    prompt: "Cât de detaliat preferi să fie conținutul afișat?",
    helpText: "Alege nivelul de concentrare al informațiilor pe ecran.",
    options: [
      {
        value: "short",
        label: "Esențial și concis",
        description: "Doar ideile principale, fără detalii secundare sau încărcătură vizuală.",
      },
      {
        value: "medium",
        label: "Echilibrat",
        description: "Rezumat clar însoțit de contextul util de lucru.",
      },
      {
        value: "full",
        label: "Complet și detaliat",
        description: "Toate explicațiile, contextul și materialele de referință.",
      },
    ],
  },
  {
    id: "stepByStep",
    prompt: "Cum preferi să fie structurate instrucțiunile?",
    helpText: "Ajută la urmărirea sarcinilor într-o ordine logică și clară.",
    options: [
      {
        value: true,
        label: "Pași numerotați",
        description: "Ghidare pas cu pas, cu bife de finalizare pentru fiecare acțiune.",
      },
      {
        value: false,
        label: "Paragrafe fluide",
        description: "Text continuu structurat pe secțiuni logice.",
      },
    ],
  },
  {
    id: "visualNoise",
    prompt: "Cum te simți mai confortabil la nivel vizual?",
    helpText: "Putem mări contrastul și folosi un font cu lizibilitate sporită.",
    options: [
      {
        value: "low",
        label: "Fără elemente distractive",
        description: "Contrast ridicat, font foarte clar și eliminarea animațiilor.",
      },
      {
        value: "normal",
        label: "Aspect standard",
        description: "Culori naturale, borduri fine și contrast optim.",
      },
    ],
  },
  {
    id: "sensory",
    prompt: "Ce ambianță de lucru preferi în aplicație?",
    helpText: "Controlăm mișcarea elementelor și animațiile de tranziție.",
    options: [
      {
        value: "quiet",
        label: "Calm și fără animații",
        description: "Fără efecte de mișcare sau tranziții animate.",
      },
      {
        value: "normal",
        label: "Tranziții obișnuite",
        description: "Mișcare lină și feedback vizual standard.",
      },
    ],
  },
  {
    id: "language",
    prompt: "În ce limbă dorești să fie interfața și răspunsurile?",
    helpText: "Poți schimba oricând limba principală de lucru.",
    options: [
      {
        value: "ro",
        label: "Română",
        description: "Interfață și asistență în limba română.",
      },
      {
        value: "en",
        label: "English",
        description: "Interface and responses in English.",
      },
    ],
  },
  {
    id: "timeToDecide",
    prompt: "Cum dorești să fie gestionat timpul de decizie?",
    helpText: "Nu folosim cronometre sau limite de timp care să șteargă datele.",
    options: [
      {
        value: "need-more-time",
        label: "Fără grabă",
        description: "Totul rămâne salvat, cu posibilitatea de a relua oricând în ritmul tău.",
      },
      {
        value: "normal",
        label: "Flux standard",
        description: "Confirmare obișnuită a acțiunilor.",
      },
    ],
  },
]);

export const QUESTIONNAIRE_EN = Object.freeze([
  {
    id: "readingPace",
    prompt: "How do you prefer to read workplace texts?",
    helpText: "We adjust font size and line spacing for your visual comfort.",
    options: [
      {
        value: "slow",
        label: "Gentle pace",
        description: "Larger text, generous spacing between lines and letters.",
      },
      {
        value: "medium",
        label: "Standard pace",
        description: "Regular font size and classic layout.",
      },
      {
        value: "fast",
        label: "Fast pace",
        description: "Compact formatting, more content visible at a glance.",
      },
    ],
  },
  {
    id: "textAmount",
    prompt: "How much detail do you prefer to see?",
    helpText: "Choose the density of information presented on screen.",
    options: [
      {
        value: "short",
        label: "Essential & concise",
        description: "Key points only, with minimal visual clutter.",
      },
      {
        value: "medium",
        label: "Balanced",
        description: "Clear summary accompanied by useful workplace context.",
      },
      {
        value: "full",
        label: "Detailed & thorough",
        description: "Complete explanations, background notes, and reference links.",
      },
    ],
  },
  {
    id: "stepByStep",
    prompt: "How should work instructions be structured?",
    helpText: "Helps you follow workplace tasks in a predictable order.",
    options: [
      {
        value: true,
        label: "Numbered steps",
        description: "Step-by-step guidance with completion checkboxes.",
      },
      {
        value: false,
        label: "Flowing paragraphs",
        description: "Continuous text organized into clear sections.",
      },
    ],
  },
  {
    id: "visualNoise",
    prompt: "What visual presentation feels most comfortable?",
    helpText: "We can enhance contrast and apply a highly legible font.",
    options: [
      {
        value: "low",
        label: "Low distraction",
        description: "Higher contrast, clear readable typography, reduced motion.",
      },
      {
        value: "normal",
        label: "Standard look",
        description: "Soft colors, gentle borders, and standard contrast.",
      },
    ],
  },
  {
    id: "sensory",
    prompt: "What sensory experience do you prefer in the app?",
    helpText: "Controls UI motion and transition effects.",
    options: [
      {
        value: "quiet",
        label: "Quiet & still",
        description: "No decorative motion or sliding transition effects.",
      },
      {
        value: "normal",
        label: "Standard motion",
        description: "Subtle transitions and standard interaction cues.",
      },
    ],
  },
  {
    id: "language",
    prompt: "Which language do you prefer for interface and guidance?",
    helpText: "You can switch your language preference at any time.",
    options: [
      {
        value: "ro",
        label: "Română",
        description: "Romanian interface and guidance.",
      },
      {
        value: "en",
        label: "English",
        description: "English interface and guidance.",
      },
    ],
  },
  {
    id: "timeToDecide",
    prompt: "How would you like decision timing to be handled?",
    helpText: "We never use timers or expiration limits that clear your work.",
    options: [
      {
        value: "need-more-time",
        label: "Unrushed",
        description: "Everything remains preserved; resume at your own pace anytime.",
      },
      {
        value: "normal",
        label: "Standard flow",
        description: "Standard action confirmation.",
      },
    ],
  },
]);

/**
 * Returns the questionnaire array in the requested language.
 *
 * @param {string} [lang="ro"] - "ro" or "en"
 * @returns {Array<object>} List of question objects
 */
export function getQuestionnaire(lang = "ro") {
  if (lang === "en") {
    return QUESTIONNAIRE_EN;
  }
  return QUESTIONNAIRE_RO;
}
