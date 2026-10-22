# LIMITS — Asumarea Onestă a Limitelor Produsului (PrimaZi)

Acest document descrie clar și onest ce **face**, ce **NU face** și unde poate **greși** sistemul PrimaZi.
*Principiul nostru de bază: Este mai important să semnalăm o incertitudine decât să inventăm o informație falsă (Zero Hallucination).*

---

## 1. Ce NU face produsul (Non-Goals Asumate)

1. **NU oferă consultanță juridică sau medicală:**
   - Catalogul de adaptări și extragerea obligațiilor au rol pur orientativ de bune practici la locul de muncă.
   - Textul generat include avertismentul legal: *„Informativ, nu reprezintă consultanță juridică.”*
2. **NU deduce și NU stochează diagnostice medicale sau etichete clinice:**
   - Respectăm cu strictețe Art. 9 GDPR (categorii speciale de date) și etica Responsible AI.
   - Orice adaptare este funcțională (ex: instrucțiuni scrise, program flexibil), fără a forța angajatul să-și divulge diagnosticul.
3. **NU deduce starea emoțională a angajatului (EU AI Act):**
   - Transcrierile și mesajele sunt analizate exclusiv textual. Nu folosim biometrie vocală sau analiză facială pentru a „ghici” emoții.
4. **NU trimite mesaje sau e-mailuri automat:**
   - Sistemul generează ciorne și propuneri de formulare. Decizia finală și acțiunea de trimitere aparțin 100% omului.
5. **NU execută macro-uri sau cod din fișiere:**
   - Documentele încărcate (.docx, .pdf, .eml) sunt procesate pasiv ca fluxuri de date text; componentele executabile (ex: `vbaProject.bin`) sunt ignorate complet.

---

## 2. Unde poate greși sistemul și cum semnalizăm (Margini de Eroare)

| Situație / Limitare | Ce se întâmplă | Soluția / Semnalizarea în UI |
|---|---|---|
| **Termen limită ambiguu** (ex. „cât mai repede”, „până joi”) | Sistemul **nu inventează** o dată calendaristică. | Setează `date: null` și emite avertizarea `UNCERTAIN_DATE` cu insignă galbenă „Necesită confirmare”. |
| **Citat absent din documentul original** | Dacă modelul parafrazează în loc să citeze exact. | Filtrul `verify_quotes` marchează `quote_found: false` și emite o avertizare transparentă. |
| **PDF scanat fără strat de text (doar imagine)** | Parserul PDF nu găsește caractere de text selectabile. | Emite eroare clară în limbaj simplu: *„Fișierul PDF este o imagine scanată. Lipește textul manual sau folosește un document cu text selectabil.”* |
| **Sinteza vocală (TTS) în limba română** | Dacă utilizatorul nu are instalată vocea `ro-RO` în Windows/Linux/macOS. | Browserul poate citi cu accent sau nu are voce disponibilă; interfața rămâne 100% completă și lizibilă textual. |
| **Recunoașterea vocală live** | Web Speech API este nativă doar pe browsere moderne Chromium. | Fallback-ul principal garantat este lipirea directă a textului sau a transcrierii. |

---

## 3. Ce a fost testat riguros (Dovezi Verificabile)

- **Suita de teste automate:** 234 teste trecute cu succes în `./scripts/check.sh` (backend, parsare documente, circuit breaker, contracte v2).
- **Poarta de verificare a accesibilității:** Audit automat WCAG 2.2 AA pe toate ecranele HTML (`tests/test_a11y_static.py`).
- **Verificare cap-la-cap (Smoke Tests):** Server uvicorn pe port efemer testând fiecare rută API și pagină statică (`scripts/smoke.sh`).
- **Benchmark de evaluare AI:** 18 cazuri de evaluare pe proprietăți în `evals/run.py` (apărare la prompt injection, confidențialitate, limbaj simplu).
- **Protecție la căderea serviciilor AI:** Modul `mock` funcționează 100% offline, garantând rularea demonstrativă chiar dacă nu există acces la internet.
