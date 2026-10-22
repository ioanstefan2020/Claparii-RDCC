/**
 * PrimaZi — Glossary & Difficult Terms Engine (Wave 2)
 * Keyboard-navigable accessible term explanations and dictionary lookup.
 * Ref: docs/SETTINGS-SPEC.md §2, docs/TASKS-WAVE2.md A6
 */

const termStore = new Map();

export function registerGlossaryTerms(terms = []) {
  if (!Array.isArray(terms)) return;
  terms.forEach(item => {
    if (item && item.term && item.explanation) {
      termStore.set(item.term.toLowerCase().trim(), item.explanation);
    }
  });
}

export function lookupTerm(term) {
  if (!term || typeof term !== "string") return null;
  return termStore.get(term.toLowerCase().trim()) || null;
}

export function getAllTerms() {
  return Array.from(termStore.entries()).map(([term, explanation]) => ({ term, explanation }));
}

export function clearGlossary() {
  termStore.clear();
}
