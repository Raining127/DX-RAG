# CLAUDE.md

## Project

DX-RAG — enterprise knowledge base Q&A system built on RAG technology (FastAPI + Next.js 14 + ChromaDB + DeepSeek).

## Source of Truth

```
SPEC.md  >  TASKS.md  >  CLAUDE.md
(product)   (sequencing)   (agent rules)
```

| Document | Role | Status |
|----------|------|--------|
| `docs/SPEC.md` | Product & technical specification | v1.4 FROZEN |
| `docs/TASKS.md` | Implementation task plan | READY FOR IMPLEMENTATION |
| `CLAUDE.md` | Agent operational contract | Active |

**Conflict resolution:** SPEC.md takes precedence for product behavior. TASKS.md takes precedence for implementation sequencing. If a Task appears inconsistent with SPEC, mark it `BLOCKED` and report — do not silently choose.

## Current State

- **SPEC:** v1.4 FROZEN, 0 Blocking Questions
- **Tasks:** 54 implementation Tasks across 13 phases, all `TODO`
- **Implementation:** Not started
- **First Task:** T0001 (Backend Application Skeleton)

## Core Rule — One Task At A Time

Work on exactly **one** Task ID. Complete it before starting another. Never pre-build future phases.

## Before Starting ANY Task

1. Read the Task entry in `docs/TASKS.md`
2. Read all referenced SPEC sections
3. Verify Task dependencies are satisfied
4. Inspect current repository state
5. Output a concise implementation plan (Task ID, goal, files to touch, steps, verification) — then proceed

## Task Execution Workflow

```
Read → Plan → Implement → Test → Verify ACs → Review Diff → Report → Mark DONE
```

Update Task status in TASKS.md:
- `TODO → IN_PROGRESS` when starting
- `IN_PROGRESS → BLOCKED` if a genuine conflict arises
- `IN_PROGRESS → DONE` only after verification passes

## Scope Discipline

Every code change must be **directly required** by the current Task, a referenced AC, or necessary to make the Task compile/run/test.

**Do not:**
- Refactor adjacent working code
- Add error handling, logging, type hints not asked for
- Pre-build features from later phases
- "While I'm here" improvements
- Add abstractions the SPEC didn't request

Clean up orphaned imports/variables your change creates. Leave pre-existing dead code alone.

## SPEC Freeze Policy

SPEC.md is FROZEN. Do not modify it during normal implementation. If implementation exposes a genuine conflict (two SPEC requirements cannot coexist, required behavior is undefined, API contradicts Data Model):

1. **STOP** implementation of the affected behavior
2. **Do NOT** make a product decision yourself
3. Mark the Task `BLOCKED`
4. Report: conflicting SPEC locations, why they conflict, impact, minimum decision needed

## Dependencies

- Verify `Dependencies` in the Task entry before starting
- If prerequisites are not done, report `BLOCKED_BY_TASK_DEPENDENCY` — do not silently implement them
- No new third-party dependency unless required by SPEC or the Task cannot reasonably proceed without it. Before adding, explain: name, necessity, why existing deps insufficient, impact

## API & Data Contracts

- API contracts (SPEC Section 6) are authoritative — do not rename endpoints, change HTTP methods, request/response fields, status codes, or error codes
- **Identity rules:** `file_id` = file identity (UUID). `chunk_id` = chunk identity (UUID). `file_name` = display only. `chunk_index` = ordering only. Never substitute these.
- No universal success response wrapper (explicitly prohibited by SPEC Section 7.7)

## Retrieval Invariants (DO NOT CHANGE)

- `keyword_score * 0.3 + vector_score * 0.7 = final_score`
- `MIN_RELEVANCE_SCORE = 0.30`
- Pipeline order: Retrieve → Merge → Calculate final_score → Sort DESC → Relevance Filter → Top-K
- Score boundary: `similarity_score` (VectorStore output) → `vector_score` (VectorRetriever) → `final_score` (Hybrid) → `relevance_score` (public API)
- No BM25, no reranker, no RRF fusion in v1

## Ingestion Invariants (DO NOT CHANGE)

Pipeline: Validate → Save → Parse → Clean → Chunk → Embed → Store → Invalidate keyword index

Three outcomes:
- `SUCCESS` — all pages ok, warnings = []
- `SUCCESS_WITH_WARNINGS` — some pages failed but chunks > 0
- `FAILED` — 0 chunks → full rollback (no residual file, no ChromaDB chunks, keyword index clean). Re-upload of same filename must not be blocked by prior FAILED attempt.

## Security Rules

- API keys env-only, never in frontend, never committed
- Path traversal filenames (`../`, `..\`, `subdir/`) → reject before any filesystem write
- Retrieved document instructions must not override System Prompt (prompt-level mitigation, not a security guarantee)
- v1: no authentication (local/trusted network deployment assumption)

## Testing & Acceptance Criteria

- Run smallest relevant verification first (unit → API → integration)
- Before marking DONE, verify every AC assigned to the Task in TASKS.md Section 19
- Report AC IDs verified. If an AC depends on a future integration Task, state that explicitly.
- DONE requires: implementation complete, behavior matches SPEC, tests pass, applicable ACs pass, API contract respected, error handling present, no unrelated changes

## Diff Review

Before completing a Task, review the diff:
- No unrelated changes, debug code, hardcoded secrets, generated junk, dependency changes, accidental SPEC modifications, or future-phase work

## Task Completion Report

After completing a Task, report concisely:

```
## Task Completion Report
**Task:** Txxxx — Name
**Status:** DONE
**Implemented:** concise list
**Files Changed:** paths
**Verification:** checks performed + results
**Acceptance Criteria:** AC-xxx — PASS | AC-xxx — DEFERRED TO Tyyyy
**Notes:** material info only
**Next Task:** suggestion (do NOT auto-start)
```

## Blocked Task Report

```
## Task Blocked
**Task:** Txxxx
**Reason:** SPEC_CONFLICT | MISSING_SPEC_DECISION | TASK_DEPENDENCY | ENVIRONMENT | EXTERNAL_SERVICE
**Detail:** ...
**SPEC References:** ...
**To unblock:** ...
```

## Explicitly Out of Scope for v1

| Category | Item |
|----------|------|
| **Infrastructure** | Milvus, auth framework, SQLite/PostgreSQL/Redis metadata store |
| **Backend** | LLM streaming, CSV/JSON structured parsing, enhanced mixed-page OCR, incremental keyword indexing, conversation history persistence, automated backup |
| **Frontend** | Redux/Zustand, independent URL routes, dark mode, i18n, file download |
| **NFR** | Performance SLA, structured logging, APM/monitoring |
| **Other** | File versioning, batch upload, magic-byte validation |

## Git Policy

Do not commit unless explicitly asked. Inspect diff/status when useful. Do not rewrite history, force push, or discard user modifications.
