---
name: api-contract
description: Use when two or more components (frontend/backend, firmware/host, service/service, model/app) must talk to each other. Define and freeze the interface before building either side.
---

# Contract-first design

1. **List the boundaries**: which component calls which, and over what (HTTP, function call, serial, queue, file).
2. **For each boundary define**: name, direction, request/input schema, response/output schema, error cases and codes, timing/ordering assumptions, auth if any.
3. **Write it down in `docs/CONTRACTS.md`** (already drafted for this project; only P1 edits it, after all three agree) with concrete examples (real JSON, real byte layouts, real function signatures). One valid example and one error example per message.
4. **Encode the contract in code** where possible: typed models (pydantic/dataclasses/TypeScript types/structs), an OpenAPI snippet, or a shared schema file in one place that both sides import.
5. **Create a stub/fake** for each side that returns the example data, so the other side can be built and tested immediately.
6. **Add a contract test**: validates that real outputs match the schema and that the stub matches the real one.
7. **Freeze**: changing a contract after parallel work starts requires the orchestrator to announce the change to every affected agent. Version it in `docs/decisions/<me>.md`.

## Good contracts are
- Small (only what the demo needs), explicit about units and encodings, explicit about errors, and boring (JSON over HTTP, newline-delimited text over serial, plain structs).
