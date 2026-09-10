# CLAUDE.md

## Project

DX-RAG — enterprise knowledge base Q&A system built on RAG technology (FastAPI + Next.js 14 + ChromaDB + DeepSeek).

## Source of Truth

```text
docs/v2/SPEC.md > docs/v2/TASKS.md > CLAUDE.md
(product)          (sequencing)      (agent rules)
```

| Document | Role | Status |
|----------|------|--------|
| `docs/v2/SPEC.md` | Active V2 product & technical specification | Current Phase 20 scope approved; future V2 scope remains DRAFT; see Section 1.1 |
| `docs/v2/TASKS.md` | Active V2 evaluation, experiment and implementation sequencing | T2001 DONE; Dataset Contract 0.3 FROZEN; Human Final Gate PASS (2026-09-10); T2002/T2003 TODO and not authorized |
| `CLAUDE.md` | Current agent operational contract | Active |

**Conflict resolution:** `docs/v2/SPEC.md` takes precedence for V2 product behavior; `docs/v2/TASKS.md` controls sequencing. If they conflict, block the affected Task and report; do not silently choose.

### Historical V1 Baseline

- Tag `v1.0.0`: `da8be59a60d7f35a2e3c1ab835624946c53d2a55`.
- `docs/SPEC.md`: v1.7 FROZEN, released V1 contract.
- `docs/TASKS.md`: V1 task history, 55 Tasks DONE across 13 Phases.

These define the released V1 baseline and are read-only historical references during normal V2 work. Preserve existing verification, retrospective and learning evidence. Historical claims of sole authority and V1 section numbers apply to V1 only. Explicit V1 re-reviews use these historical contracts; normal V2 execution uses the active hierarchy above.

## Current State

- V1 released; historical Phase 12 PASS is recorded in `docs/verification/PHASE-12-GATE-CLOSURE.md`, not newly verified by this bootstrap.
- V2: Evaluation-Driven RAG Optimization. Current Phase 20 scope approved. Human project owner approved T2001 DONE and Dataset Contract 0.3 FROZEN with T2001 Final Gate PASS on 2026-09-10. This does not authorize T2002/T2003, runner/metric implementation, dataset construction, benchmark execution, retrieval experiments or product changes.
- Post-release README and Learning & Engineering Workflow improvements are retained.
- Before starting any V2 Task, read `docs/v2/TASKS.md` for current status and approval/dependencies. Do not infer readiness from this file.

## Core Rule — One Task At A Time

Work on exactly **one** Task ID. Complete it before starting another. Never pre-build future phases.

## Before Starting ANY Task

1. Read the Task entry in `docs/v2/TASKS.md` and confirm `docs/v2/SPEC.md` approval for its scope
2. Read all referenced `docs/v2/SPEC.md` sections and explicitly inherited V1 contracts
3. Verify Task dependencies are satisfied
4. Inspect current repository state
5. Output a concise implementation plan (Task ID, goal, files to touch, steps, verification) — then proceed

## Task Execution Workflow

```
Read → Plan → Implement → Test → Verify ACs → Review Diff → Mark DONE → Task Learning Pass → Report
```

Update Task status in `docs/v2/TASKS.md`:
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
- Add abstractions `docs/v2/SPEC.md` did not request

Clean up orphaned imports/variables your change creates. Leave pre-existing dead code alone.

## SPEC Freeze Policy

`docs/v2/SPEC.md` began as DRAFT. Section 1.1 now records approval of the current Phase 20 scope and execution authorization for T2001 only. Future V2 scope remains DRAFT. Scope approval does not authorize T2002/T2003 or any retrieval experiment; later execution requires explicit authorization and satisfied dependencies.

```text
Draft V2 SPEC -> Human Review -> Freeze / Approve -> Execute Task
-> Test / Benchmark -> Evidence -> ADR / Human Decision
-> Explicit SPEC amendment if required
```

Record human approval and its scope in `docs/v2/SPEC.md` before execution. Do not silently rewrite requirements during implementation or after an unexpected experiment result. Negative results are evidence, not permission to change success criteria.

If requirements conflict or required behavior is undefined:

1. **STOP** implementation of the affected behavior.
2. **Do NOT** make a product decision yourself.
3. Mark the affected Task `BLOCKED` in `docs/v2/TASKS.md`.
4. Report exact specification paths/sections, impact and minimum decision needed.

`docs/SPEC.md` remains the frozen historical V1 specification.

## Dependencies

- Verify `Dependencies` in the Task entry before starting
- If prerequisites are not done, report `BLOCKED_BY_TASK_DEPENDENCY` — do not silently implement them
- No new third-party dependency unless required by `docs/v2/SPEC.md` or the Task cannot reasonably proceed without it. Before adding, explain: name, necessity, why existing deps insufficient, impact

## API & Data Contracts

- Existing V1 API contracts (`docs/SPEC.md` Section 6) remain inherited by `docs/v2/SPEC.md` until explicitly amended there and sequenced in `docs/v2/TASKS.md`; they are authoritative — do not rename endpoints, change HTTP methods, request/response fields, status codes, or error codes
- **Identity rules:** `file_id` = file identity (UUID). `chunk_id` = chunk identity (UUID). `file_name` = display only. `chunk_index` = ordering only. Never substitute these.
- No universal success response wrapper (explicitly prohibited by `docs/SPEC.md` Section 7.7)

## V1 Retrieval Baseline - Historical Contract

- `keyword_score * 0.3 + vector_score * 0.7 = final_score`
- `MIN_RELEVANCE_SCORE = 0.30`
- Pipeline order: Retrieve → Merge → Calculate final_score → Sort DESC → Relevance Filter → Top-K
- Score boundary: `similarity_score` (VectorStore output) → `vector_score` (VectorRetriever) → `final_score` (Hybrid) → `relevance_score` (public API)
- No BM25, no reranker, no RRF fusion in the released V1 baseline.

Preserve this behavior, its existing threshold, Top-K and pipeline long enough to capture a reproducible V1 benchmark. Do not silently replace or remove the baseline before that evidence exists. V2 alternatives require explicit authorization in both `docs/v2/SPEC.md` and `docs/v2/TASKS.md`, after the Phase 20 baseline gate. These are historical baseline rules, not permanent prohibitions on V2 experiments.

## Inherited Ingestion Contract

Preserved from `docs/SPEC.md`; changes require explicit V2 specification amendment and Task authorization.

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
- Before marking DONE, verify every AC assigned to the Task in `docs/v2/TASKS.md` and its referenced `docs/v2/SPEC.md` requirements (V1 re-reviews use `docs/TASKS.md` Section 19)
- Report AC IDs verified. If an AC depends on a future integration Task, state that explicitly.
- DONE requires: implementation complete, deliverables match `docs/v2/SPEC.md`, applicable tests/benchmarks and ACs pass, API contract respected, error handling present where applicable, no unrelated changes

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

## Phase Gate Review

When asked to run a Phase Gate Review, first read and follow `docs/learning/templates/phase-gate-review-template.md`. Treat the review as **REVIEW-ONLY** unless the user explicitly authorizes otherwise: independently verify the Phase against the version-specific specification and task paths, implementation, tests, and complete repository state; treat existing review verdicts as context, not acceptance evidence; do not modify files, either version's specification, Task status, or future Task definitions, and do not start the next Phase. Return the verdict and report structure defined by the canonical Gate Review protocol.

## Learning & Engineering Workflow V2

Use `docs/learning/templates/phase-learning-pass-workflow.md` as the canonical Final Learning & Engineering Workflow V2 for all future DX-RAG Tasks and Phases. Its repository binding defines command routing, evidence vocabulary, ownership, preservation and reader checks. For V2, product behavior and Task sequencing follow `docs/v2/SPEC.md` / `docs/v2/TASKS.md`; this workflow does not change their authority.

| Command / event | Responsibility | Structure |
|---|---|---|
| After an evaluation, experiment or implementation Task is verified and marked DONE; or `Txxxx learning pass` | Capture fresh Task-aware understanding: component names first, concepts, code, flow, rationale, difficulties, verification, limitations and Phase-consolidation inputs | `docs/learning/templates/phase-learning-template.md`, Part A |
| `Phase X learning review` (legacy `Phase X learning pass`) | Consolidate Task material into concept-centric Technical Learning after all Tasks are DONE and Gate state is established; reorganize rather than append a summary | Same template, Part B |
| `Phase X engineering review` | Independently evaluate decisions, constraints, alternatives, costs, failure/consistency, upgrade triggers and Known Gaps after Gate, preferably after learning consolidation | `docs/learning/templates/phase-engineering-review-template.md` |

Preferred Phase sequence: all Tasks DONE → Gate → if FAIL, authorized remediation/tests/Gate re-review → established Gate state → Phase Learning Review → Engineering Review. Unresolved blockers remain explicit; documentation completion never upgrades Gate status or next-Phase readiness. The Gate protocol above stays independent and REVIEW-ONLY by default.

Read current implementation, tests/evidence, relevant `docs/v2/SPEC.md` / `docs/v2/TASKS.md` (or explicit V1 review contracts) and historical findings before writing. Teach Why before How and concepts before symbols; keep real code depth and accurate Python/TypeScript explanations. Phase Learning's main narrative must remain understandable with Task/Gate/Finding/AC identifiers hidden. Engineering Review must answer when each important design stops being appropriate, without becoming another tutorial or Gate report.

Keep historical closure, current implementation and later verification distinct. Do not upgrade STATIC/UNIT/MOCKED/SUBSTITUTED evidence into REAL/LIVE/E2E; state exact boundaries and whether checks were rerun. Preserve existing ADRs, meaningful evidence, limitations and historical terminology.

Interview Guide is a separate derived artifact, synthesized from consolidated Learning, Engineering Reviews, current code and project status. Learning/review commands do not automatically update interview answers or other reviews. Preserve old interview assets and historical workflows; migrate other Phase documents only when explicitly requested. Do not modify code, tests, `docs/v2/SPEC.md` / `docs/v2/TASKS.md` or historical V1 contracts, Gate records or start another Task/Phase merely to complete a documentation command.

For experiment-oriented Tasks, the same Task Learning Pass -> Phase Gate -> Phase Learning Review -> Engineering Review -> independent Interview synthesis flow remains active. Explain the research question, baseline, change, benchmark, acceptance/rejection rationale, trade-off, validity conditions and next experiment. Workflow V2 names the learning workflow revision, independently of product V2. Do not migrate historical V1 documents merely to use newer templates.

## V2 Experiment Governance

Distinguish Evaluation Tasks (measurement), Experiment Tasks (controlled candidate comparison), and Implementation Tasks (approved production integration). Follow:

```text
Research Question -> Baseline -> Candidate -> Controlled Experiment
-> Benchmark - Analysis - ADR / Decision - Production Integration
```

Experimental code does not authorize production adoption. Record architecture decisions in `docs/v2/adr/` with Context, Decision, Alternatives, Evidence, Trade-offs and Consequences. Report unsupported decisions for human judgment. A failed experiment can complete its engineering Task when the approved protocol and evidence requirements are satisfied; candidate superiority is not a universal acceptance criterion.

## V1 Historical Scope Boundary

The following table describes released V1 exclusions. It does not automatically prohibit V2 experiments or enroll these features into V2. They remain excluded unless explicitly introduced by `docs/v2/SPEC.md` and sequenced in `docs/v2/TASKS.md`.


| Category | Item |
|----------|------|
| **Infrastructure** | Milvus, auth framework, SQLite/PostgreSQL/Redis metadata store |
| **Backend** | LLM streaming, CSV/JSON structured parsing, enhanced mixed-page OCR, incremental keyword indexing, conversation history persistence, automated backup |
| **Frontend** | Redux/Zustand, independent URL routes, dark mode, i18n, file download |
| **NFR** | Performance SLA, structured logging, APM/monitoring |
| **Other** | File versioning, batch upload, magic-byte validation |

## Git Policy

Do not commit or create branches unless explicitly asked. Do not create, move or recreate tags (especially `v1.0.0`), reset historical commits, merge branches, or delete historical evidence without explicit authorization. Inspect diff/status when useful. Do not rewrite history, force push, or discard user modifications.
