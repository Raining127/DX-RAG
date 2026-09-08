> **Public evidence representation (2026-09-07):** linked captures at the existing paths are the public representations described in [sanitization/provenance](../SANITIZATION-PROVENANCE.md). Path-bearing captures were sanitized only for filesystem paths; immutable originals remain locally preserved and excluded from Git. Historical raw hashes refer to those originals; public hashes are recorded separately. No acceptance, assertion, provider response or evidence classification was changed.

# T1202 — Retrieval + QA Pipeline E2E Verification

Date: 2026-09-07. **Task status: DONE (remaining-acceptance audit).**
SPEC: v1.7 FROZEN, F009-F015, Sections 6.4, 9.3, 12.4, DOD-02/04.
Only T1202 was audited. T1201 remains DONE; T1204 was not started.

## Outcome and acceptance boundary

**All frozen mandatory T1202 ACs are satisfied by complementary evidence.**
The existing LIVE DeepSeek + real BGE matrix passed **70/70 checks**.
DETERMINISTIC fault injection verifies the error-handling contract separately.
See [the requirement-by-requirement blocker audit](BLOCKER-AUDIT.md).

Actual DeepSeek HTTP 429, 5xx and 403 remain **NOT_OBSERVED**. Neither SPEC
nor TASKS requires these statuses to occur naturally at the provider before
T1202 can complete. SPEC F013 / Section 9.3 requires correct retry/auth behavior
when the application receives them. Simulation proves that control flow; it
is not evidence of live HTTP responses or provider availability.

The previous README and live runner incorrectly made unobserved 429/5xx a
completion blocker. That added gate has been removed without changing SPEC,
product code, any AC, or historical observations. The original live log remains
unchanged with **exit 2**, reflecting the old gate, not failed assertions.
No new provider requests were made during this audit.

## Commands and artifacts

| Directory | Command | Result | Evidence |
|---|---|---|---|
| `backend/` | `python -m unittest tests.test_qa tests.test_query -v` | **60/60 PASS**, exit 0, before changes | [focused-before.txt](focused-before.txt) |
| Repository root | `python backend/scripts/verify_t1202_retrieval_qa.py` | **46/46 PASS**, exit 0; deterministic contract matrix | [deterministic.txt](deterministic.txt) |
| Repository root, authorized network execution | `python backend/scripts/verify_t1202_retrieval_qa.py --live` | **70/70 checks PASS**, historical Python exit 2 from the removed extra gate | [live-reviewed.txt](live-reviewed.txt) |
| Repository root | `python -m py_compile backend/scripts/verify_t1202_live.py backend/scripts/verify_t1202_retrieval_qa.py` | PASS | Syntax verification |
| Repository root | `git diff --check` | PASS | Final diff review |

Final live start: `2026-09-07T09:27:24.006226+00:00`.
Captures use Python `subprocess.run(..., capture_output=True,
encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})` and write
UTF-8 output to the linked filenames. The Python process's exit code is appended
to each capture. Shell wrapping may report a generic nonzero execution result.
Counts refer to assertions, not numbers of ACs.

The machine-readable [summary](summary.json) lists every final check and actual
successful response ID. The full live log records fixture text/hashes, upload
identities, retrieved chunks/scores, request messages/settings, real answers,
usage, API sources, retries, HTTP errors, and cleanup.

## Final audit verification

| Command | Result | Evidence |
|---|---|---|
| `cd backend; python -m unittest tests.test_qa tests.test_query -v` | 60/60 PASS | [focused](blocker-audit-focused.txt) |
| `python backend/scripts/verify_t1202_retrieval_qa.py` | 46/46 PASS | [deterministic matrix](blocker-audit-deterministic.txt) |
| `python backend/scripts/verify_t1202_failure_contract.py` | 15/15 PASS; zero provider requests | [failure contract](blocker-audit-failure-contract.txt) |

These runs are DETERMINISTIC; the prior immutable live log remains the LIVE evidence.

## Evidence fidelity

- **REAL:** FastAPI upload/query endpoints via TestClient; parsing/chunking;
  local `bge-small-zh-v1.5` 512-dimensional normalized inference and singleton;
  temporary Chroma persistence; keyword/vector/fusion retrieval; history,
  context, and source assembly; original DeepSeek SDK and remote responses.
- Real calls use the configured `backend/.env` key, verified in memory without
  printing it. The application still requests `deepseek-chat` at
  `https://api.deepseek.com`, temperature 0.2, max_tokens 2048, stream false,
  timeout 60, SDK max_retries 0. The actual successful responses reported
  **`model="deepseek-v4-flash"`**. No alternate model/provider was selected by
  the harness. The requested and returned model names are both preserved.
- SDK observers delegate to the actual constructor and completion method.
  Final successful HTTP status is read from the SDK's raw response, then the
  unchanged parsed response is returned to the application. API answers are
  compared to the actual provider output. `x-request-id` was absent; actual
  completion IDs are recorded instead of inventing request identifiers.
- Real transport timeout: a request-specific `timeout=0.000001` causes actual
  `APITimeoutError`. The next attempt uses normal timeout. Exhaustion uses
  three actual timeouts. The application sleeps for real 1/2-second backoff.
- Real network error: one request uses an actual HTTP proxy connection to a
  reserved but non-listening loopback port. That transport cannot connect and
  raises actual `APIConnectionError`; no local server receives a credential.
  The next attempt goes to real DeepSeek normally. This is a controlled local
  transport fault, not a provider HTTP response.
- Real authentication error: one deliberately invalid, nonsecret test
  credential is sent to the actual DeepSeek endpoint. It returns **401**, SDK
  `AuthenticationError`; API returns **500 LLM_AUTH_FAILED**, with one attempt
  and no backoff. The user's valid key is not changed in `.env`.
- **DETERMINISTIC fault-injection evidence, separately labeled:** the existing deterministic matrix and
  focused tests use model/provider doubles and literal branch-score fixtures.
  They cover exact mathematical examples, defensive duplicate inputs, and
  429/500/401/403/400 error classification. They do not establish live provider
  response behavior.
- Fixtures and all durable test storage live in a fresh system temp tree.
  The parent removes it after the child exits and releases Windows handles.
  Every completed matrix reports `ISOLATED_STORAGE_CLEANUP: PASS`.
  No business uploads/Chroma storage is targeted; no DashScope call is made.
- This is application/API E2E, not browser/TCP/CORS/frontend verification.

## Observed results and manual answer review

Final run: **16 SDK attempts: 10 HTTP 200 responses, 4 real timeouts, 1 real
network connection error, and 1 actual HTTP 401**. Successful responses report
**9,818 total tokens**; this is reported usage, not an estimate of billing or
unreported timed-out processing.

| Case | Observed behavior | Actual completion ID |
|---|---|---|
| Matching machine-learning query | Grounded definition: branch of artificial intelligence, learning patterns/prediction from data; 3 sources from the uploaded machine-learning file | `953d0fda-70d3-4184-91aa-2b1d807b1574` |
| Python known facts | Markdown answer reports programming language, documented pros/cons, fixture-only course ID **PY482**, and **7** exercises | `7a87bab0-c6ad-4233-b742-084ff6df6c2f` |
| Unrelated quantum-computing query | HTTP 200, sources=[], actual insufficient-KB-information answer; LLM still called with empty-context placeholder | `24bb4aa2-f432-4903-8d7a-761628c2e820` |
| Pronoun follow-up | Real preceding answer sent as history; “它的优缺点” returns the Python facts: clear syntax/rich ecosystem/limited interpreted performance; Python source identity retained | `231f73d3-5ed8-4d8c-8ab0-9d0bf00d8096` |
| History window | Exact last 20 of 30 messages appear in the real request; first 10 absent | `def3b6fd-2994-424e-988f-8073c0eab0f8` |
| Injection | Malicious English/OVERRIDE_ACCEPTED/EVIL999 instructions actually retrieved and sent; answer remains Chinese and does not obey them | `d21c3954-a7cb-431f-8dbd-f783647740b3` |
| False historical fact | History says FAKE777; answer uses KB fact PY482, not FAKE777 | `bfee9569-7c9c-4cae-954e-bde4c34543ba` |
| Context boundary | 8 retrieved chunks/5073 formatted chars; real request contains the maximal whole-chunk prefix, **3803** chars, within 4000 | `ca67dd2e-d8aa-43da-a56f-915040b4712c` |
| Timeout recovery | Actual timeout, 1-second backoff, second real attempt succeeds | `7f1ea867-cecd-41f2-8068-418aa4e5a0ff` |
| Network recovery | Actual connection error, 1-second backoff, second real attempt succeeds | `59691d50-aae7-4b66-b775-a010f9ff0371` |

Manual inspection of the captured answers confirms the facts above and no
invented inline citation markers. This is a small controlled corpus, not a
general model quality or security guarantee. In the injection case the model
conservatively says information is insufficient even though a legitimate fact
exists alongside the attack. This is a recorded usability limitation; it did
not switch to English or execute the malicious instruction.

One recorded fusion example is
`0.6666666666666666 × 0.3 + 0.7578538060188293 × 0.7 = 0.7304976642131804`.
The exact same final_score is exposed as relevance_score. Sources retain the
four prescribed fields, are sorted descending, and refer to actual persisted
file/chunk identities. Equal-content chunks with distinct IDs remain distinct.

## AC-by-AC ledger

PASS below refers to the stated SPEC AC and its declared evidence boundary;
it does not upgrade the unobserved additional provider statuses to PASS.

| AC | Evidence | Result |
|---|---|---|
| AC-F009-01 | Real uploaded text, Chinese bigrams, keyword score 1.0 | PASS |
| AC-F009-02 | Real keyword query for absent quantum-computing tokens returns [] | PASS |
| AC-F009-03 | Real 3/5 token match yields 0.6 | PASS |
| AC-F009-04 | Python + Chinese mixed tokens, real score 1.0 | PASS |
| AC-F009-05 | Cached index rebuilt after real new upload | PASS |
| AC-F010-01 | Real BGE “AI 的子领域” returns the uploaded machine-learning chunk with positive score | PASS |
| AC-F010-02 | Real empty collection vector search returns [] | PASS |
| AC-F011-01 | Real score arithmetic; exact 0.8/0.9→0.87 example in deterministic contract matrix | PASS |
| AC-F011-02 | Real unrelated candidates below 0.30 removed; literal keyword-only 0.18 removal in deterministic matrix | PASS |
| AC-F011-03 | Literal 20-survivors→top-5 fixture in existing matrix; real API Top-K exercised | PASS |
| AC-F011-04 | Real dual-hit dedupe; defensive inconsistent-content same-ID fixture in existing matrix | PASS |
| AC-F012-01 | Real context sent in score order with file/content formatting | PASS |
| AC-F012-02 | Real empty filtered context still invokes DeepSeek and returns insufficient-info answer | PASS |
| AC-F013-01 | Real grounded Markdown answer, including KB-only PY482/7 facts | PASS |
| AC-F013-02 | Real quantum query refuses to invent facts | PASS |
| AC-F013-03 | Actual retrieved injection does not override system-first rules or Chinese answer language | PASS |
| AC-F013-04 | Actual timeout→retry success; three actual timeouts→502 LLM_UNAVAILABLE, backoff 1/2 seconds | PASS |
| AC-F014-01 | Real previous turn + pronoun follow-up resolves Python facts | PASS |
| AC-F014-02 | Real outbound request contains exactly last 20/30 history messages | PASS |
| AC-F014-03 | Omitted history yields normal real single-turn answer; no history section | PASS |
| AC-F015-01 | Actual API sources match ranked persisted chunks; exact fields and descending scores | PASS |
| AC-F015-02 | Backend constructs sources independently; API answer equals real completion and has no inline markers | PASS |
| AC-QA-01 | Real upload→query yields answer and sources | PASS |
| AC-QA-02 | Real unrelated query: HTTP 200, sources=[], insufficient information | PASS |
| AC-QA-03 | Same real pronoun evidence as F014-01 | PASS |
| AC-QA-04 | Exact machine-learning facts rank highest; raw branch/final/public scores recorded | PASS |
| AC-QA-05 | Empty KB→409 COLLECTION_EMPTY; observers record no retrieval and no LLM call | PASS |
| AC-QA-06 | top_k 0/21/-1→400 INVALID_TOP_K; no retrieval/LLM call | PASS |
| AC-QA-07 | Literal 3800/4000 overflow fixture in existing matrix; real provider gets 3803-char whole-chunk prefix | PASS |
| Section 9.3 timeout/network | Real failures, successful recovery and exhaustion with real backoff | PASS |
| Section 9.3 401 | Actual DeepSeek 401; one attempt; API 500 LLM_AUTH_FAILED | PASS |
| Section 9.3 429/5xx retry contract | Deterministic 429/500/503/599 recovery at either retry and exhaustion; no live responses claimed | PASS (DETERMINISTIC) |
| Section 9.3 401/403 auth contract | LIVE 401 plus DETERMINISTIC 401/403: one attempt, no sleep, 500 LLM_AUTH_FAILED | PASS |
| DOD-02 / DOD-04 (T1202 scope) | All 29 applicable feature/cross-feature ACs and defined QA error contracts verified with explicitly separated evidence | PASS |

## Earlier runs and oracle corrections

- [live-first.txt](live-first.txt): 63/64 checks, exit 1. Injection returned a
  Chinese insufficient-information answer without obeying the attack. The
  initial oracle additionally demanded the factual answer PY482. The final
  oracle separates the literal F013-03 resistance criterion from conservative
  abstention, which remains explicitly reported above. No product prompt was
  changed and no failure log was overwritten.
- [live-final.txt](live-final.txt): 69/70 checks, exit 1. The pronoun answer gave
  exactly the correct Python pros/cons and correct source but did not repeat
  the word “Python”. The oracle now checks the distinctive facts and source
  identity instead of demanding a particular surface wording. The history
  fixture uses “什么是 Python” and the actual provider's preceding answer;
  it does not supply a fabricated prior answer.
- [live-reviewed.txt](live-reviewed.txt): 70/70 executed checks; no fabricated
  answers/errors; historical exit 2 because the then-current harness required live 429/5xx. The audit removes that extra gate; the raw log is preserved.

## Scope and review

No application implementation, system prompt, API contract, configuration,
dependency, or SPEC change was required. This task changes only the T1202
runner, live helper, offline failure-contract verifier, T1202 note in TASKS, and these evidence files.
The previously uncommitted T1201 files/artifacts are protected by hashes in
[baseline.json](baseline.json); historical [review.txt](review.txt) records the earlier scope
and exact-secret checks without disclosing values. The current [audit review](blocker-audit-review.txt) supersedes its BLOCKED verdict. Existing
`.claude/settings.local.json` and inaccessible `backend/tmpnw2f1mgn/` were
left untouched. No commit was made.

Earlier Phase 12 artifacts' “DeepSeek NOT_AVAILABLE / no live call” statements
are historical. This T1202 record supersedes that availability statement but
does not upgrade T1204 or the Phase 12 Gate. Stop after T1202.
