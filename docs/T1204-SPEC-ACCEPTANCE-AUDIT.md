> **Historical Gate-remediation snapshot.** The current T1204 task audit is [docs/verification/T1204/README.md](verification/T1204/README.md). Its current provider evidence supersedes the availability blockers below; the original Gate event is retained as history.

# Phase 12 Gate Remediation / T1204 Acceptance Evidence

> Remediation date: 2026-09-07  
> SPEC baseline: `docs/SPEC.md` v1.7 (FROZEN)  
> Original Gate verdict: `PHASE_12_FAIL — FIX_REQUIRED`  
> Historical verdict at this remediation checkpoint: **`PHASE_12_FAIL — FIX_REQUIRED`**
> Current final verdict after F-6 and independent incremental re-review: **PHASE_12_PASS** — [Gate closure](verification/PHASE-12-GATE-CLOSURE.md)
> Next Phase started: no

## 1. Historical disposition at this checkpoint

The original T1204 report claimed 100% mandatory AC PASS while the local BGE
model, DashScope OCR, and DeepSeek answer behavior were represented by test
doubles. That conclusion is withdrawn.

The BGE part of the Gate finding is now remediated with product-authorized
contract and REAL runtime evidence. The following provider boundaries remain
unverified and prevent a Phase 12 PASS:

- DashScope/Qwen-VL live OCR: `NOT_AVAILABLE`; no live call was authorized or made.
- DeepSeek live answer, grounding, history/pronoun behavior, and prompt-injection
  behavior: `NOT_AVAILABLE`; no live call was authorized or made.

Accordingly, T1201, T1202, and T1204 are `BLOCKED`; T1203 remains `DONE`.

## 2. Approved SPEC conflict resolution

Original Gate finding: `SPEC_CONFLICT`.

- Frozen v1.6 text required 384-dimensional embeddings.
- The retained official model `BAAI/bge-small-zh-v1.5` actually emits 512
  dimensions.
- Product decision: keep `BAAI/bge-small-zh-v1.5`; do not substitute another
  model; update the specification, implementation guard, test fixtures, and
  acceptance baseline to 512.
- Resolution: SPEC v1.7 now defines a 512-dimensional, L2-normalized contract.

Existing non-512-dimensional Chroma data must not be mixed with the corrected
contract. This remediation did not inspect, delete, migrate, or rebuild the
repository's business `chroma_db` or `uploads`; all runtime checks used system
temporary directories.

## 3. Official local model evidence

| Item | Evidence | Result |
|---|---|---:|
| Repository | `BAAI/bge-small-zh-v1.5` | REAL / PASS |
| Local path | `backend/models/bge-small-zh-v1.5/` | REAL / PASS |
| Revision | `7999e1d3359715c523056ef9478215996d62a620` | REAL / PASS |
| Snapshot inventory | 13/13 Hub files match recorded sizes; required `modules.json`, `1_Pooling/config.json`, tokenizer files, config files, and weights present | REAL / PASS |
| `model.safetensors` | 95,827,648 bytes; SHA-256 `354763b9b1357bc9c44f62c6be2276321081ed2567773608c0d0785b61d5a026` | REAL / PASS |
| `pytorch_model.bin` | 95,842,633 bytes; SHA-256 `7c5fe667bbed05dc10e246e229b701ad266fe4d95ab946e9e5aa402056611b88` | REAL / PASS |
| Git hygiene | `.gitignore` excludes `backend/models/bge-small-zh-v1.5/`; weights are not tracked | STATIC / PASS |

The model was downloaded with the official Hugging Face CLI:

```text
cd backend
hf download BAAI/bge-small-zh-v1.5 --revision main --local-dir models/bge-small-zh-v1.5
```

The exact relative-path load was exercised from `backend/`:

```text
SentenceTransformer("models/bge-small-zh-v1.5")
dimension=512
shape=(2, 512)
norms=[1.0, 1.0]
```

The repository-owned offline probe then verified snapshot integrity, application
singleton behavior, normalized encoding, and real Chroma semantic ranking:

```text
cd backend
python scripts/verify_bge_model.py
Required checks: 4/4 passed
RESULT: PASS
MODEL_REVISION: 7999e1d3359715c523056ef9478215996d62a620
ranking=[
  ('machine-learning.txt', 0.467517),
  ('frontend.txt', 0.415124),
  ('database.txt', 0.367617),
  ('cooking.txt', 0.251864)
]
```

The query was `AI 的子领域是什么？`; the first document states that machine
learning is a branch of artificial intelligence. This is REAL evidence for the
controlled Chinese synonym-ranking case, not a statistical recall/latency
benchmark.

## 4. Runtime regression evidence

| Command | Result | Count | Evidence boundary |
|---|---:|---:|---|
| `cd backend && python -m unittest tests.test_embedding -v` | PASS | 3/3 | Focused 512 contract and mismatch guard |
| `cd backend && python scripts/verify_bge_model.py` | PASS | 4/4 | REAL local BGE + REAL temporary Chroma |
| `python backend/scripts/verify_t0503_rollback.py` | PASS | 56/56 | SUBSTITUTED embedding; no provider call |
| `python backend/scripts/verify_t1201_ingestion.py` | PASS | 81/81 | SUBSTITUTED 512 BGE and Qwen responses; REAL app/temp storage |
| `python backend/scripts/verify_t1202_retrieval_qa.py` | PASS | 46/46 | SUBSTITUTED 512 BGE and DeepSeek transport; REAL app/temp storage |
| `python backend/scripts/verify_t1203_file_management_security.py` | PASS | 43/43 | SUBSTITUTED 512 BGE; REAL lifecycle/temp storage |
| `python backend/scripts/verify_t1204_spec_acceptance.py` | PASS | 29/29 | SUBSTITUTED 512 BGE; REAL focused audit paths/temp storage |
| `cd backend && python -m unittest discover -s tests -v` | PASS | 81/81 | Full backend regression; mocked external boundaries where tests declare them |

The expected fault-injection tracebacks in T0503 and the keyword invalidation
test are tested logging behavior; both commands exited 0. The PyMuPDF `fitz`
deprecation warning remains informational and was not changed by this
remediation.

Frontend build/browser evidence was not rerun because no frontend source or
contract changed in this remediation. Historical frontend evidence is not used
to upgrade either provider boundary.

## 5. Evidence classification for affected acceptance areas

| Area / AC | Current evidence | Evidence type | Result | Boundary |
|---|---|---|---:|---|
| F007 / AC-F007-01 | Real 512-dimensional normalized output | REAL | PASS | Fixed revision |
| F007 / AC-F007-02 | Same process returns the same loaded model instance | REAL | PASS | Fixed revision |
| F010 / AC-F010-01 | Controlled Chinese synonym query ranks target first in Chroma | REAL | PASS | Not a broad benchmark |
| F010 / AC-F010-02 | Empty collection and vector adapter paths | REAL + SUBSTITUTED | PASS | No provider dependency |
| F004 / Qwen-VL OCR ACs | Adapter/retry/warning paths only | SUBSTITUTED; live `NOT_AVAILABLE` | FAIL | Live DashScope required |
| F013 / DeepSeek ACs | Prompt/retry/error paths only | SUBSTITUTED; live `NOT_AVAILABLE` | FAIL | Live DeepSeek required |
| F014 history answer semantics | Formatting/window are real; pronoun answer is substituted | SUBSTITUTED; live `NOT_AVAILABLE` | FAIL | Live DeepSeek required |
| QA answer/grounding/injection outcomes | Retrieval/prompt plumbing is real; answer semantics are substituted | SUBSTITUTED; live `NOT_AVAILABLE` | FAIL | Live DeepSeek required |
| F015 backend-owned sources | Sources derive from real ranked persisted rows | REAL | PASS | Independent of LLM answer text |

No aggregate “85/85 PASS” is published while literal provider-dependent rows
remain failed. The 65/39/85 inventory counts still pass as inventory guards;
they are not substituted for runtime evidence.

## 6. Task status

| Task | Current status | Reason |
|---|---|---|
| T1201 | `BLOCKED` | REAL BGE closed; live DashScope/Qwen-VL OCR remains `NOT_AVAILABLE` |
| T1202 | `BLOCKED` | REAL BGE semantic ranking closed; live DeepSeek behavior remains `NOT_AVAILABLE` |
| T1203 | `DONE` | File/security scope remains passing and provider-independent |
| T1204 | `BLOCKED` | Full mandatory audit cannot pass while T1201/T1202 provider findings remain open |

## 7. Gate findings

| ID | Severity | Finding | Current disposition |
|---|---|---|---|
| F-1 | MAJOR | BGE model missing and 384/512 `SPEC_CONFLICT` | `REMEDIATED` — model retained, v1.7=512, REAL 4/4 |
| F-2 | MAJOR | Live DashScope/Qwen-VL OCR unverified | `REVERIFY_REQUIRED` — `NOT_AVAILABLE` |
| F-3 | MAJOR | Live DeepSeek answers/grounding/history/injection unverified | `REVERIFY_REQUIRED` — `NOT_AVAILABLE` |
| F-4 | MAJOR | T1204 report overclaimed 100% using substitutions | `REMEDIATED` — report corrected; PASS claim withdrawn |
| F-5 | MINOR | Opaque inaccessible `backend/tmpnw2f1mgn/` remains in worktree observations | `FIX_REQUIRED` outside this model remediation; not deleted |

## 8. Controlled next step

DashScope acceptance requires an explicitly authorized live-call window, a
configured test credential, a non-sensitive OCR corpus, a budget/rate limit,
and expected-text/error oracles. DeepSeek acceptance requires separate explicit
live-call authorization, a configured test credential, a redacted evaluation
corpus, grounding/history/injection rubrics, and cost/rate limits. Merely finding
a key in environment configuration is not authorization to call either service.
