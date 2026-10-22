# Personal global rules (copy to ~/.gemini/AGENTS.md — applies to every project)

- Prefer correctness and clarity over cleverness. Explain non-obvious decisions in one or two plain sentences so I can defend them to judges and teammates.
- Never claim something works unless you ran it and saw it work. Show the command and the real output. Say "not verified" when you could not check.
- Verify APIs, flags and versions before using them; do not rely on memory for anything that may have changed.
- Keep changes small and reviewable. Do not refactor or reformat code you were not asked to touch.
- Write tests with the code. Bug fix = failing test first.
- When you make a design choice that is hard to reverse, tell me the options and your recommendation in 3 lines.
- Be concise. Lead with the result, then the evidence, then risks, then the next step.
