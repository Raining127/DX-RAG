> **Public evidence representation (2026-09-07):** linked captures at the existing paths are the public representations described in [sanitization/provenance](../SANITIZATION-PROVENANCE.md). Path-bearing captures were sanitized only for filesystem paths; immutable originals remain locally preserved and excluded from Git. Historical raw hashes refer to those originals; public hashes are recorded separately. No acceptance, assertion, provider response or evidence classification was changed.

# T1204 - Full SPEC Acceptance Criteria Audit

> **F-6 incremental remediation, 2026-09-07:** the subsequent Gate found missing upload-to-list/count frontend synchronization. The fix and red/green actual-component integration evidence now restore the affected requirements; see [F6-REMEDIATION.md](F6-REMEDIATION.md) and [execution results](F6-RESULTS.json). T1203/T1204 affected scope is reconfirmed PASS. The subsequent independent incremental Gate re-review is complete: **PHASE_12_PASS**, T1203/T1204 PASS and F-6 CLOSED; see [current Gate closure](../PHASE-12-GATE-CLOSURE.md); no new browser upload or provider execution is claimed. The historical full-audit results below retain their original scope.

Date: 2026-09-07. Baseline: **SPEC v1.7 FROZEN**. **Verdict: DONE.**

All **104 mandatory Section 5/12 occurrences (85 unique IDs)** pass, with
explicit section-qualified traceability. All mandatory DOD-01 through DOD-06
pass in the final v1 audit scope. One actual deviation, ignored CORS
configuration, was fixed and reverified. SPEC was not changed.

This is the T1204 task audit, not a new Phase Gate / Learning Review event.
No future task or feature was started. Existing DONE labels were not treated
as evidence; raw provider records, implementation, test assertions and final
runtime results were reviewed together.

## Complete acceptance and ownership matrix

- [ACCEPTANCE-MATRIX.md](ACCEPTANCE-MATRIX.md): every Section 5 and Section 12
  occurrence, requirement summary/link, owner, implementation, evidence type,
  result and limitations.
- [acceptance-matrix.json](acceptance-matrix.json): same rows with original
  Given/When/Then text and exact SPEC line locations.
- [DOD-MATRIX.md](DOD-MATRIX.md): DOD-01 through DOD-06 for each of F001-F017.
- [live-evidence-validity.json](live-evidence-validity.json): raw-log hashes
  and current-source applicability check.
- [review.txt](review.txt): final diff, secret, preservation and inventory checks.

Inventory is 65 Section 5 + 39 Section 12 = 104 occurrences, 85 distinct IDs.
F003-01/02/03 differ between sections and were not collapsed. Section 19 has
an owner for every ID; ranged entries are expanded without double-counting.
F016-04 through 07 appear in Section 5 but their owner rows are under Section
19's cross-feature table; they still have T0902 ownership and evidence.
No mandatory AC is omitted, deferred or supported only by a task status.

Section 15 is a coverage index, not an alternate AC inventory: its descriptive
counts (for example F003=3, F012=3, F016=7) do not match the explicit Determine
enumeration. The authoritative individual criteria and Section 12's policy
are used, without inventing missing ACs or editing frozen SPEC. CLAUDE.md's
v1.6 label is similarly stale; current SPEC v1.7 and 512 dimensions prevail.

## Current regression commands and results

Counts below are tests/assertions, not additional ACs. Overlapping suites are
not summed into an inflated acceptance rate. No new dependencies/frameworks.

| Working directory / command | Pass | Fail | Skip | Exit | Evidence |
|---|---:|---:|---:|---:|---|
| backend: `python -m unittest discover -s tests -v` | 83 | 0 | 0 | 0 | [backend-final.txt](backend-final.txt) |
| root: `python backend/scripts/verify_t0503_rollback.py` | 56 | 0 | 0 | 0 | [rollback-final.txt](rollback-final.txt) |
| root: `python backend/scripts/verify_t1201_ingestion.py` | 88 | 0 | 0 | 0 | [t1201-final.txt](t1201-final.txt) |
| root: `python backend/scripts/verify_t1202_retrieval_qa.py` | 46 | 0 | 0 | 0 | [t1202-final.txt](t1202-final.txt) |
| root: `python backend/scripts/verify_t1202_failure_contract.py` | 15 | 0 | 0 | 0 | [t1202-faults.txt](t1202-faults.txt) |
| root: `python backend/scripts/verify_t1203_file_management_security.py` | 43 | 0 | 0 | 0 | [t1203-final.txt](t1203-final.txt) |
| root: `python backend/scripts/verify_t1204_spec_acceptance.py` | 42 | 0 | 0 | 0 | [t1204-final.txt](t1204-final.txt) |
| backend: `python scripts/verify_bge_model.py` | 4 | 0 | 0 | 0 | [bge.txt](bge.txt) |
| frontend: `npm ls --depth=0` | check PASS | 0 | 0 | 0 | [frontend-dependencies.txt](EXECUTION-SUMMARY.md#dependencies) |
| frontend: `node node_modules/typescript/bin/tsc --noEmit --incremental false` | check PASS | 0 | 0 | 0 | [frontend-typecheck.txt](EXECUTION-SUMMARY.md#typecheck) |
| frontend: `npm run build` | check PASS | 0 | 0 | 0 | [frontend-build.txt](EXECUTION-SUMMARY.md#build) |
| frontend: `node scripts/verify_t1204_contracts.cjs` | 2 | 0 | 0 | 0 | [frontend-component.txt](frontend-component.txt) |
| Browser interactive matrix | 6 | 0 | 0 | N/A | [browser.md](browser.md) |

No standalone lint command/config or existing frontend test runner is
configured. Build's type/lint stage does not establish that a standalone
lint suite ran. No lint/test framework was installed. The additional validator
probe passes 4 cases; its exact command is recorded in frontend-validation.txt.

Superseded current-checkout logs were removed during release hygiene;
[their results and disposition](EXECUTION-SUMMARY.md#superseded-runs) are retained. The added literal file fixture initially failed setup
because its parent directory was absent; [the failure](EXECUTION-SUMMARY.md#fixture-setup-failure)
is summarized with its original failure status. Changing fixture setup to `mkdir(parents=True)` fixed the harness,
not product behavior. The final expanded probe passes 42/42.

## Phase 12 evidence revalidation

**T1201 / LIVE:** [immutable raw evidence](../T1201/live-final.txt) has 91/91
checks, actual Qwen request IDs/HTTP 200 OCR, scanned and mixed PDFs, ordered
recognized text, SUCCESS, controlled real timeout-based SUCCESS_WITH_WARNINGS
and FAILED, full rollback and successful same-name re-upload. Current ingestion
source/test/runner hashes match its review record. Local BGE is the actual
official 512-dimensional model; the independent offline BGE probe passes again.

**T1202 / LIVE:** [immutable raw evidence](../T1202/live-reviewed.txt) has 70/70
checks, 10 HTTP 200 completions, actual 401, real timeout and controlled local
network faults; grounded fixture facts, pronoun/history, injection resistance,
scores, sources and whole-chunk context were reviewed. QA/ingest/embedding/store
source hashes still match the prior audit. Only app initialization's CORS
configuration changed, with separate regression proving default behavior.
No expensive provider calls were repeated because these artifacts remain
applicable to the unchanged provider/pipeline implementations.

**T1202 / DETERMINISTIC:** 429/5xx/403 behavior is separately proven by fault
injection. Live 429/5xx/403 remain NOT_OBSERVED, not PASS. SPEC F013 / Section
9.3 requires handling received errors correctly, not naturally observing each
remote failure. The [blocker audit](../T1202/BLOCKER-AUDIT.md) was independently
checked; its removed gate is not reinstated. Historical live exit 2 is preserved.

**T1203 / E2E:** independently rerun actual upload -> list -> persisted preview
-> delete -> re-upload, exact traversal literals, cache invalidation and KB
isolation. Embedding inference is a declared double. The original lifecycle
uses four files and deletes one chunk; the new T1204 fixture additionally
verifies the literal three-file list and 15 persisted PDF chunks, avoiding a
claim that the older fixture alone matched these numbers.

**Frontend:** actual browser UI evidence is separated from controlled model
output. File chooser access was blocked by Chrome extension permission; this
is reported, not a successful browser upload. Mandatory size rejection and
50 MiB allowance are covered by the actual component's pre-upload handler,
controlled state re-render and Ant Design LIST_IGNORE contract (2/2).

## SPEC / API / error / field audit

| Area | Review and result |
|---|---|
| Routes and methods (Section 6) | PASS: OpenAPI exactly matches the 8 documented paths / 10 method combinations including health; no extra product endpoint added. |
| JSON and response fields | PASS: schemas.py, frontend/lib/types.ts and api-client.ts checked against Section 6/7; runtime upload/query/list/preview/delete/rename outputs verified. Independent success shapes; no universal wrapper. |
| Identity | PASS: UUID file_id/chunk_id; display-only filename; index-based preview order; rename preserves IDs/content/embeddings and changes only collection/source metadata. |
| Retrieval | PASS: 0.3 keyword + 0.7 vector; sort DESC -> >=0.30 filter -> Top-K; source relevance_score equals final_score; whole-chunk context bound. |
| Errors | PASS: exact Section 9 catalog checked; existing API/rollback tests cover validation, missing entities, parsing, embedding, global errors and LLM contracts. Added actual encrypted PDF, missing OCR key, injected 401/403/400/429/503 and render-failure warnings cover remaining OCR error paths. |
| Provider secrets | PASS: secret values kept in memory only; exact scan of task files/diff; browser harness uses nonsecret fixture credential and never calls a live provider. |
| CORS (Section 8.1 / 10.3) | FIXED: main.py ignored CORS_ORIGINS. It now consumes existing settings.CORS_ORIGINS. New test starts isolated app processes and verifies allowed origin 200, denied origin 400/no allow-origin header, and wildcard default. |
| Other deviations | No unresolved mandatory behavioral deviation found. Section 15 counts and CLAUDE version labels are documented index inconsistencies, not new behavioral requirements. |

## Mandatory DoD across all implemented feature areas

| DoD | Result and evidence |
|---|---|
| DOD-01 | PASS: F001-F017 implementation reviewed against requirements; CORS deviation resolved; matrix records implementation for every occurrence. |
| DOD-02 | PASS: 104/104 explicit occurrences; 85/85 unique IDs represented, including both F003 meanings. |
| DOD-03 | PASS: Section 6 routes, request validation, statuses, response fields and identities verified as above. |
| DOD-04 | PASS: defined HTTP errors/warning codes and bounded retry/no-retry contracts implemented and checked; natural provider errors not a prerequisite. |
| DOD-05 | PASS for this task's diff: CORS bug/test, acceptance fixtures, frontend verifier, audit/status/evidence only; unrelated pre-existing changes preserved. |
| DOD-06 | PASS: adjacent Python/TypeScript conventions retained; new verification tools use installed dependencies only. |

The matrix's area-specific evidence applies DOD-01/02/03/04 to all F001-F017,
including internal services without standalone HTTP endpoints. DOD-05/06 were
reviewed across the current implemented code and this audit's actual diff;
they are not inferred from a test count. Recommended DOD-07 through DOD-10
are not extra mandatory criteria; unit/build/browser/startup evidence is
available, with limitations stated rather than converted to new blockers.

## Scope, limitations and stopping point

Raw T1201/T1202 evidence and frozen SPEC remain unchanged. No future feature,
new dependency, provider flood, business-data migration, commit or push.
The old Phase Gate report/learning records remain historical; this report
supersedes their T1204/provider-availability blocker, not their separate Gate
event. Existing inaccessible `backend/tmpnw2f1mgn/` and unrelated
`.claude/settings.local.json` predate this audit and were not edited or claimed
to be inspected/cleaned. No broad filesystem-cleanliness claim is made.

This is finite acceptance evidence, not a general model accuracy/security
guarantee. Live injection can conservatively abstain; context-boundary answer
quality is not asserted by the prompt-length test. No wider adversarial,
performance, browser compatibility or destructive-failure matrix was added.
Only T1204 is marked DONE; no next task is started.
