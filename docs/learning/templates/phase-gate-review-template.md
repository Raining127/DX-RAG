# DX-RAG Phase Gate Review Protocol & Report Template

> **Canonical use**: When asked to “Run the Phase X Gate Review”, read and follow this document before reviewing the Phase.
> **Scope**: This protocol governs future Phase Gate Reviews and explicit Gate Re-reviews. Historical review records are precedent, not retroactive migration targets.
> **Default mode**: **REVIEW-ONLY**.

---

## 0. Purpose and Artifact Boundary

A Phase Gate Review is the formal, independent acceptance decision between one completed Phase and the next Phase. It answers whether the declared implementation is supported by current repository evidence and is a safe foundation for downstream work.

It is not the same artifact as:

| Artifact | Responsibility |
|---|---|
| Technical Learning | Explain what the code does and what to learn from it |
| Engineering Review | Accumulate ADRs, trade-offs, failure analysis, scalability, and known gaps |
| **Phase Gate Review** | Independently audit Tasks, ACs, contracts, runtime evidence, repository state, and readiness; issue the formal verdict |
| Phase Learning Review | Consolidate Phase-level learning and promote selected interview material after the Gate |

Existing Task Completion Reports, Learning documents, Engineering Reviews, and previous Gate verdicts may guide where to inspect, but they do not prove current acceptance.

> **Existing review verdicts are context, not evidence.**

---

## 1. Review Contract

Unless the user explicitly authorizes a different mode, every Phase Gate Review is **REVIEW-ONLY**. The reviewer must not:

- modify any file;
- fix a finding;
- modify `docs/v2/SPEC.md` or historical `docs/SPEC.md`;
- modify Task status or future Task definitions in `docs/v2/TASKS.md` or historical `docs/TASKS.md`;
- implement or start the next Phase;
- install dependencies merely to fix or hide a review finding;
- commit or push.

Read-only inspection and independently executing safe, relevant verification are allowed. If a command would materially mutate repository or external state, do not run it without explicit authorization.

The Gate must independently evaluate the Phase. Do not copy an earlier verdict, accept a `DONE` label without audit, or convert an Engineering Review conclusion into Gate evidence without verification.

At the beginning of the report, state:

- Phase and Tasks under review;
- review mode (`REVIEW-ONLY`, unless explicitly authorized otherwise);
- source-of-truth documents;
- repository/environment constraints that limit verification;
- confirmation that the next Phase was not started.

---

## 2. Source of Truth and Required Reading

Select and report the version under review. For active V2:

```text
docs/v2/SPEC.md > docs/v2/TASKS.md > CLAUDE.md
```

For an explicitly requested V1 re-review, use historical `docs/SPEC.md` and `docs/TASKS.md` anchored at `v1.0.0`, with current `CLAUDE.md` operational rules. Never apply V2 acceptance requirements retroactively to V1. A draft V2 specification is not an approved acceptance contract; report missing approval instead of silently treating it as frozen.

Before reaching a verdict, read:

1. every Task entry in the Phase;
2. every SPEC section and AC referenced by those Tasks;
3. relevant implementation and public contracts;
4. relevant tests and verification scripts;
5. current repository state;
6. relevant prior reports only as navigation/context.

The frozen SPEC must not be reinterpreted to match the implementation. A genuine conflict or missing product decision must be reported and classified; the reviewer must not silently choose new behavior.

---

## 3. Repository State Audit

Inspect enough Git state to avoid false conclusions from `git diff` alone. Use platform-equivalent read-only commands, including at minimum:

```text
git status --short
git diff --stat
git diff
git ls-files --others --exclude-standard
```

Also inspect staged changes when present (for example, `git diff --cached`). Audit:

- tracked, staged, modified, deleted, and untracked files;
- Phase implementation files that are untracked and therefore absent from ordinary `git diff` output;
- generated, scratch, cache, or verification artifacts;
- hardcoded credentials, tokens, keys, or other accidental secrets;
- unrelated changes and future-Phase scope leakage;
- whether the worktree prevents an honest attribution of changes.

A clean `git diff` does not prove a clean repository: it excludes untracked files and may exclude staged changes.

---

## 4. Task Audit

Audit every Task in the Phase independently. For each Task evaluate:

- declared status;
- dependency satisfaction;
- implementation scope and explicit out-of-scope rules;
- expected/required files and interfaces;
- completion conditions;
- required verification;
- applicable AC ownership and traceability;
- whether the declared `DONE` state is justified by current evidence.

Use exactly these Task results:

- `PASS`
- `PASS_WITH_MINOR_FINDINGS`
- `FAIL`

Do not change Task status during the Gate.

```markdown
| Task | Declared Status | Dependencies | Scope / Deliverables | Verification | AC Ownership | Gate Result | Notes |
|---|---|---|---|---|---|---|---|
| Txxxx | DONE | PASS | ... | ... | AC-Fxxx-xx | PASS | ... |
```

---

## 5. Acceptance Criteria Audit

Audit every applicable AC independently. A prior report, a Task status, or inference from adjacent behavior is not sufficient for `PASS`.

### 5.1 Evidence classification

Use exactly these evidence labels:

| Evidence | Meaning |
|---|---|
| `REAL` | Executed against the real applicable implementation/dependency/path |
| `MOCKED` | Executed with a dependency or boundary replaced by a mock/fake |
| `STATIC` | Established by code/config/contract inspection only; not runtime proof |
| `SUBSTITUTED` | Executed with a declared alternative fixture/path that reaches the same owned behavior |
| `DEFERRED` | Intentionally left to a named later Task/Phase or authorized environment |
| `NOT_AVAILABLE` | Tool, dependency, service, or environment needed for the check is unavailable |

### 5.2 Result classification

Use exactly these AC results:

- `PASS`
- `FAIL`
- `DEFERRED`
- `NOT_APPLICABLE`

`NOT_AVAILABLE` describes evidence availability, not the AC result. If the unavailable evidence is explicitly owned by a later Task/environment, use result `DEFERRED` and name that owner. If the current Phase requires the literal evidence and no independent evidence establishes the AC, use `FAIL`. Use the Gate-level `BLOCKED` verdict only when an unresolved environment/external decision prevents an honest overall judgment; never translate `NOT_AVAILABLE` into `PASS`.

```markdown
| AC | Owner Task | Requirement | Evidence | Evidence Type | Result | Boundary / Deferred Owner |
|---|---|---|---|---|---|---|
| AC-Fxxx-xx | Txxxx | ... | command/file/probe | REAL | PASS | — |
```

### 5.3 Verification Accuracy principle

For every material claim distinguish:

- **verified** — the literal relevant behavior was independently exercised;
- **partially verified** — only some layers or a substitute/mock were exercised;
- **not verified** — no current evidence supports the claim;
- **incorrectly claimed** — a prior/current report labels behavior more strongly than its evidence permits.

Invalid inference examples:

- server startup does not prove browser behavior;
- a clean `git diff` does not prove no untracked files exist;
- unit tests do not automatically prove literal API, browser, persistence, or E2E behavior;
- a mocked dependency does not prove the real dependency's compatibility;
- code inspection alone does not prove a failure/rollback path executes correctly.

When only part of an AC is verified, split the claim instead of writing a qualified `PASS` that hides the unverified literal behavior.

---

## 6. Implementation / Contract Audit

Derive the concrete checks from the current Phase's SPEC and TASKS; do not force every Phase through an irrelevant universal checklist. Audit applicable areas such as:

- SPEC compliance and frozen behavior;
- API methods, paths, status codes, schemas, and error envelopes;
- data identity and score/state semantics;
- lifecycle, state transitions, cache invalidation, and idempotency;
- persistence, rollback, compensation, and observable postconditions;
- error propagation, retry boundaries, and failure ownership;
- security requirements and secret handling;
- dependency boundaries and frozen technology choices;
- public/private interface discipline;
- Phase-specific invariants defined by SPEC, TASKS, or `CLAUDE.md`.

For each applicable contract area report what was inspected, the evidence level, and the result. Mark irrelevant areas `NOT_APPLICABLE`; do not fabricate checks merely to fill a section.

---

## 7. Runtime Verification

Execute verification independently where practical:

1. run the smallest relevant check first;
2. expand to API/integration/E2E checks required by the Phase contract;
3. run broader regression checks in proportion to risk;
4. record exact commands, pass/fail counts, and exit status;
5. record environment and dependency versions when they affect evidence;
6. identify mocks, substitutions, missing tools, and real E2E boundaries.

Do not install missing tools simply to repair a review finding. `NOT_AVAILABLE` is acceptable when a tool is not a repository dependency and is not required by the project contract. Do not report unavailable tooling as `PASS`.

```markdown
| Command / Check | Scope | Environment | Exit Status | Result | Count | Evidence Boundary |
|---|---|---|---|---|---|---|
| `...` | focused unit | ... | 0 | PASS | 13/13 | MOCKED VectorStore |
```

---

## 8. Architecture, Scope Leakage, Dependencies, and Hygiene

### 8.1 Scope leakage

Check whether later-Phase functionality was pre-built. Distinguish:

- legitimate placeholder, interface seam, schema, or scaffolding explicitly required by the current Phase;
- real future business behavior that violates sequencing.

Do not flag required scaffolding as leakage merely because a later Phase will consume it.

### 8.2 Dependency and repository hygiene

Audit as applicable:

- declared dependencies and lockfiles;
- unexpected frameworks or libraries;
- frozen technology substitutions;
- `.gitignore` coverage;
- generated/cache/scratch artifacts;
- hardcoded secrets;
- unrelated changes;
- debug code or temporary verification hooks.

---

## 9. Findings Classification

Use exactly these severity levels:

| Severity | Meaning |
|---|---|
| `BLOCKER` | Prevents an honest Gate judgment or makes progression unsafe |
| `MAJOR` | Violates a required contract/AC or creates material downstream risk; normally prevents PASS |
| `MINOR` | Real issue that does not prevent safe progression under the declared scope |
| `INFO` | Observation, limitation, or improvement with no current contract violation |

Each finding should include, where applicable:

- stable ID (`F-1`, `F-2`, ... within the Gate report);
- severity;
- affected requirement, AC, and Task;
- concrete evidence;
- impact;
- owner;
- disposition.

Use these dispositions where applicable:

- `FIX_REQUIRED`
- `ACCEPTED_V1_BOUNDARY`
- `DEFERRED_TO_Txxxx`
- `SPEC_DECISION_REQUIRED`
- `REMEDIATED`
- `REVERIFY_REQUIRED`

```markdown
| ID | Severity | Requirement / AC / Task | Evidence | Impact | Owner | Disposition |
|---|---|---|---|---|---|---|
| F-1 | MAJOR | AC-Fxxx-xx / Txxxx | ... | ... | Txxxx / product | FIX_REQUIRED |
```

Do not fix findings during a default Gate Review. Report ownership and the minimum work or decision needed to unblock progression.

---

## 10. Next-Phase Readiness

Answer explicitly:

1. Are all blocking dependencies for the next Phase satisfied?
2. Is the current Phase a safe foundation for its downstream consumers?
3. Are any `BLOCKER` or `MAJOR` findings unresolved?
4. Are deferred items narrowly scoped, assigned to an owner, and honestly represented?
5. Would starting the next Phase conceal or compound a current defect?

Minor and informational findings may coexist with PASS only when they do not violate required acceptance or make the next Phase unsafe. Explain why each unresolved item does or does not block progression.

---

## 11. Gate Verdict

Use exactly one verdict family:

- `PHASE_X_PASS — READY_FOR_PHASE_Y`
- `PHASE_X_FAIL — FIX_REQUIRED`
- `PHASE_X_BLOCKED — DECISION_REQUIRED`

Decision rules:

- **PASS**: independent evidence supports the Phase, and no unresolved `BLOCKER` or `MAJOR` issue prevents the next Phase.
- **FAIL**: one or more required fixes are needed before progression.
- **BLOCKED**: an unresolved SPEC/product/environment/external decision prevents an honest Gate judgment. Do not use `BLOCKED` merely because verification is difficult.

The verdict authorizes readiness only; it does not authorize the reviewer to start the next Phase.

---

## 12. Standard Final Report Structure

Use this core structure. Add Phase-specific subsections only when they improve evidence; do not remove the core sections.

```markdown
# Phase X Gate Review — <Phase Name>

## 1. Executive Summary
- Phase / Tasks:
- Mode: REVIEW-ONLY (or the explicitly authorized mode)
- Source of Truth:
- Bottom line:
- Files modified: none (or only explicitly authorized review changes)
- Next Phase started: no

## 2. Gate Verdict
**PHASE_X_PASS — READY_FOR_PHASE_Y**

## 3. Task Audit
<one row per Task; PASS / PASS_WITH_MINOR_FINDINGS / FAIL>

## 4. Acceptance Criteria Audit
<one row per AC; evidence and result classifications>

## 5. Implementation / Contract Audit
<Phase-derived contract areas and results>

## 6. Runtime Verification
<exact commands, counts, environment, and evidence boundaries>

## 7. Findings Classification
<BLOCKER / MAJOR / MINOR / INFO; owner and disposition>

## 8. Architecture / Scope / Repository Hygiene
<scope leakage, dependency, Git-state, artifacts, secrets, unrelated changes>

## 9. Next-Phase Readiness
<explicit answers to the five readiness questions>

## 10. Final Gate Decision
- Verdict:
- Blocking remediation or decision required:
- Deferred evidence:
- Historical reports used as context only:
- Files modified: none (or only explicitly authorized review changes)
- Next Phase started: no
```

---

## 13. Gate Re-review Protocol

A Gate Re-review is a delta verification of an earlier `FAIL` or `BLOCKED` verdict. Do not blindly rewrite the original full Gate, and do not assume a changed status or remediation note proves resolution.

Use this flow:

```text
Original Finding
→ Required Remediation
→ Actual Change
→ Regression Verification
→ Current Disposition
→ Revised Verdict
```

The re-review must independently verify:

- each original blocking finding is actually resolved;
- the actual change matches the required remediation or provides an equally valid contract-preserving solution;
- remediation introduced no relevant regression;
- affected and adjacent ACs still pass;
- unresolved minor/deferred findings remain honestly bounded;
- the revised verdict is supported by current repository state.

Use the same evidence, severity, disposition, and verdict vocabulary as the original Gate.

```markdown
# Phase X Gate Re-review — <Phase Name>

## 1. Re-review Scope
- Original verdict:
- Original blocking findings:
- Remediation commits/files under inspection:
- Mode: REVIEW-ONLY

## 2. Delta Audit
| Finding | Required Remediation | Actual Change | Regression Verification | Current Disposition |
|---|---|---|---|---|

## 3. Related AC Regression
| AC | Evidence | Evidence Type | Result |
|---|---|---|---|

## 4. Remaining Findings
<unresolved or newly discovered findings>

## 5. Revised Verdict
**PHASE_X_PASS — READY_FOR_PHASE_Y**
```

Re-review does not erase the original verdict. Preserve the failure/remediation history as an audit trail.

---

## 14. Reviewer Completion Checklist

- [ ] Review mode and prohibited actions stated
- [ ] All Phase Tasks audited independently
- [ ] All applicable ACs audited with evidence and result labels
- [ ] Repository state includes tracked, staged, and untracked inspection
- [ ] Runtime commands and exact counts recorded
- [ ] Real/mock/substitute/deferred boundaries are explicit
- [ ] Phase-specific contracts and invariants audited
- [ ] Scope leakage, dependencies, artifacts, and secrets checked
- [ ] Findings have severity, owner, impact, and disposition
- [ ] Next-Phase readiness answered explicitly
- [ ] Exactly one standardized verdict family used
- [ ] Existing reports treated as context, not acceptance evidence
- [ ] No files, Task status, SPEC behavior, or future Phase changed unless the user explicitly authorized the recorded review changes
- [ ] No commit or push performed
