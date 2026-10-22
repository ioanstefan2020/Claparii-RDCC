#!/usr/bin/env python3
"""
PrimaZi — Script comparativ de performanță și calitate pentru modele AI.
Rulează același document comprehensiv prin toți furnizorii disponibili:
1. DeepSeek Cloud (deepseek-chat)
2. Groq Cloud (qwen/qwen3.8-27b)
3. Local Ollama (qwen2.5:7b)
4. Local Ollama (qwen2.5:3b)
5. Dynamic Mock Offline

Evaluează: latența (s), numărul de pași, rezumatul și fidelitatea citatelor (verbatim quotes).
"""

import asyncio
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.guardrails import verify_quotes
from app.llm import generate_json
from app.prompts.simplify import SYSTEM as SIMPLIFY_SYS
from app.prompts.simplify import build_user as build_simplify_user
from app.schemas.simplify import SimplifyData

SAMPLE_FILE = ROOT / "data" / "samples" / "demo_comprehensive_ro.txt"


async def benchmark_provider(provider_name: str, model_name: str, text: str):
    os.environ["LLM_PROVIDER"] = provider_name
    if model_name:
        os.environ["LLM_MODEL"] = model_name
        if provider_name == "ollama":
            os.environ["OLLAMA_MODEL"] = model_name
        elif provider_name == "groq":
            os.environ["GROQ_MODEL"] = model_name
    os.environ["NO_CACHE"] = "1"

    user_prompt = build_simplify_user(text=text)
    start_time = time.perf_counter()

    try:
        res, meta = await generate_json(
            task=f"bench_{provider_name}_{model_name}",
            system=SIMPLIFY_SYS,
            user=user_prompt,
            schema=SimplifyData,
            mock={
                "summary": "Mock summary",
                "steps": [],
                "key_terms": [],
                "questions_to_ask": [],
            },
        )
        elapsed = time.perf_counter() - start_time

        raw_steps = [s.model_dump() for s in res.steps]
        kept, dropped = verify_quotes(raw_steps, text, key="source_quote")
        fidelity = (len(kept) / len(raw_steps) * 100) if raw_steps else 0.0

        return {
            "provider": provider_name,
            "model": model_name or meta.get("provider", provider_name),
            "status": "OK",
            "time_sec": round(elapsed, 2),
            "summary": res.summary,
            "steps_count": len(res.steps),
            "quote_fidelity_pct": round(fidelity, 1),
            "key_terms_count": len(res.key_terms),
            "questions_count": len(res.questions_to_ask),
            "steps_detail": [
                (s.text, s.source_quote, s.source_quote in text) for s in res.steps[:3]
            ],
        }
    except Exception as e:
        elapsed = time.perf_counter() - start_time
        return {
            "provider": provider_name,
            "model": model_name,
            "status": f"FAIL: {e}",
            "time_sec": round(elapsed, 2),
            "summary": "",
            "steps_count": 0,
            "quote_fidelity_pct": 0.0,
            "key_terms_count": 0,
            "questions_count": 0,
            "steps_detail": [],
        }


async def main():
    if not SAMPLE_FILE.exists():
        print(f"Eroare: Nu s-a găsit fișierul {SAMPLE_FILE}")
        return

    text = SAMPLE_FILE.read_text(encoding="utf-8")
    print("\n" + "=" * 80)
    print("  PRIMAZI — BENCHMARK COMPARATIV MODELE AI PE DOCUMENT REAL")
    print(f"  Document analizat: {SAMPLE_FILE.name} ({len(text)} caractere)")
    print("=" * 80 + "\n")

    targets = [
        ("deepseek", "deepseek-chat"),
        ("groq", "qwen/qwen3.8-27b"),
        ("ollama", "qwen2.5:3b"),
        ("ollama", "qwen2.5:7b"),
        ("mock", "mock-dynamic"),
    ]

    results = []
    for provider, model in targets:
        print(f"--> Testez [{provider.upper()}] model='{model}'...", end="", flush=True)
        res = await benchmark_provider(provider, model, text)
        status_label = "SUCCES" if res["status"] == "OK" else "EROARE"
        print(f" {status_label} ({res['time_sec']}s)")
        results.append(res)

    print("\n" + "=" * 80)
    print("  REZULTATE COMPARATIVE")
    print("=" * 80)
    header = f"{'FURNIZOR':<12} | {'MODEL':<20} | {'TIMP (s)':<9} | {'PAȘI':<5} | {'FIDELITATE CITATE':<18} | {'TERMENI'}"
    print(header)
    print("-" * len(header))

    for r in results:
        if r["status"] == "OK":
            line = (
                f"{r['provider']:<12} | "
                f"{r['model']:<20} | "
                f"{r['time_sec']:<9} | "
                f"{r['steps_count']:<5} | "
                f"{r['quote_fidelity_pct']}%{'':<13} | "
                f"{r['key_terms_count']} termeni"
            )
        else:
            line = f"{r['provider']:<12} | {r['model']:<20} | {r['time_sec']:<9} | EȘEC: {r['status'][:30]}"
        print(line)

    print("\n" + "=" * 80)
    print("  DETALII CALITATIVE (REZUMAT & CITATE PRIMUL PAS)")
    print("=" * 80)
    for r in results:
        if r["status"] == "OK":
            print(f"\n[{r['provider'].upper()} — {r['model']}]")
            print(f'  • Rezumat generat: "{r["summary"][:160]}..."')
            if r["steps_detail"]:
                t, q, ok = r["steps_detail"][0]
                badge = "[VERBATIM EXACT]" if ok else "[PARAFRAZAT]"
                print(f"  • Pasul 1: {t}")
                print(f'    Citat: "{q}" -> {badge}')

    # Salvare raport markdown
    report_file = ROOT / "docs" / "MODEL_COMPARISON.md"
    report_md = ["# PrimaZi — Raport Comparativ de Performanță și Calitate Modele AI\n"]
    report_md.append(f"**Data testării:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    report_md.append(
        f"**Document sursă:** `{SAMPLE_FILE.name}` ({len(text)} caractere, română administrativă/muncă)\n\n"
    )
    report_md.append(
        "| Furnizor | Model | Timp de răspuns | Număr Pași | Fidelitate Citate (Verbatim) | Termeni Cheie |\n"
    )
    report_md.append("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
    for r in results:
        if r["status"] == "OK":
            report_md.append(
                f"| **{r['provider'].capitalize()}** | `{r['model']}` | **{r['time_sec']}s** | {r['steps_count']} | **{r['quote_fidelity_pct']}%** | {r['key_terms_count']} |\n"
            )
        else:
            report_md.append(
                f"| **{r['provider'].capitalize()}** | `{r['model']}` | {r['time_sec']}s | - | EȘEC | - |\n"
            )

    report_md.append("\n## Sinteze și Citate pe Fiecare Model\n")
    for r in results:
        if r["status"] == "OK":
            report_md.append(f"\n### {r['provider'].upper()} ({r['model']})\n")
            report_md.append(f"- **Timp:** {r['time_sec']} secunde\n")
            report_md.append(f"- **Rezumat:** {r['summary']}\n")
            report_md.append("- **Mostre de pași și citate:**\n")
            for idx, (t, q, ok) in enumerate(r["steps_detail"], 1):
                badge = " (Verbatim identic)" if ok else " (Parafrazat)"
                report_md.append(
                    f"  {idx}. **{t}**\n     - Citat sursă: *„{q}”*{badge}\n"
                )

    report_file.write_text("".join(report_md), encoding="utf-8")
    print(f"\nRaportul complet salvat în: {report_file.relative_to(ROOT)}")


if __name__ == "__main__":
    asyncio.run(main())
