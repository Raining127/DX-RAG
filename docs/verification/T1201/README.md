> **Public evidence representation (2026-09-07):** linked captures at the existing paths are the public representations described in [sanitization/provenance](../SANITIZATION-PROVENANCE.md). Path-bearing captures were sanitized only for filesystem paths; immutable originals remain locally preserved and excluded from Git. Historical raw hashes refer to those originals; public hashes are recorded separately. No acceptance, assertion, provider response or evidence classification was changed.

# T1201 — Ingestion Pipeline E2E Verification

Date: 2026-09-07. Result: **PASS**. Scope: **T1201 only**.
SPEC baseline: v1.7 FROZEN, F002–F008, Sections 12.2/12.3, DOD-02.
Base commit: `f41716abb6437187135c86252e06d9cfbf0280e6` plus this task's diff.
Dependencies T0308, T0502, T0503 were DONE before execution.

## Authoritative execution evidence

| Working directory | Command | Result | Evidence |
|---|---|---|---|
| Repository root, authorized network execution | `python backend/scripts/verify_t1201_ingestion.py --live` | **91/91 PASS**, exit 0 | [live-final.txt](live-final.txt) |
| Repository root | `python backend/scripts/verify_t1201_ingestion.py` | **88/88 PASS**, exit 0; deterministic regression only | [deterministic-final.txt](deterministic-final.txt) |
| Repository root | `python backend/scripts/verify_t0503_rollback.py` | **56/56 PASS**, exit 0; existing ingestion rollback regression | [rollback-regression.txt](rollback-regression.txt) |
| `backend/` | `python -m unittest discover -s tests -v` | **82/82 PASS**, exit 0 | [backend-regression.txt](backend-regression.txt) |
| `backend/` | `python -m unittest tests.test_upload.UploadContractTests.test_corrupt_pdf_releases_file_for_rollback_with_traceback_alive -v` | **1/1 PASS**, exit 0 | [corrupt-pdf-regression.txt](corrupt-pdf-regression.txt) |
| Repository root | `python -m py_compile backend/scripts/verify_t1201_ingestion.py backend/app/services/ingest.py backend/tests/test_upload.py` | PASS | Syntax check |
| Repository root | `git diff --check` | PASS | Diff review |

The initial focused upload suite also passed 8/8 before changes. Final backend
regression includes those tests plus the new malformed-PDF regression.
Check totals count assertions, not distinct AC IDs.

Final captures use Python `subprocess.run(..., capture_output=True,
encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})` and write
UTF-8 text to the linked paths. Exit codes are appended to final evidence.
Live evidence captures the script's redacted stdout; raw provider exceptions,
headers, credentials, and stderr are not published.

## Real boundaries and failure method

- Real FastAPI `POST /api/upload` through `TestClient`, actual parsers,
  cleaning, chunking, BGE, Chroma persistence, file listing, and keyword index.
  This is API/application E2E; it does not exercise TCP, browser, or frontend.
- Real `sentence_transformers...SentenceTransformer`, local
  `backend/models/bge-small-zh-v1.5`, 3×512 vectors with norms
  `[1.0, 1.0000001, 1.0000001]`, reused singleton. The previously verified
  official snapshot revision is `7999e1d3359715c523056ef9478215996d62a620`;
  snapshot hashes remain in the earlier Phase 12 remediation artifact.
- Live mode verifies that the effective DashScope credential equals the value
  in `backend/.env`, without printing either. It calls the real
  `dashscope.MultiModalConversation.call`, `model="qwen-vl-plus"`, actual
  rendered JPEG data URI, and frozen prompt `请提取图片中的所有文字，保持格式`.
  No model output or SDK exception is mocked, stubbed, or replaced in live mode.
- The observer delegates to the original SDK and records HTTP status, request
  ID, elapsed time, or exception type. Successful cases use a 60-second SDK
  request timeout. Failure cases set the real SDK's `request_timeout=0.000001`:
  actual network read timeouts exhaust the application's 3 attempts per page,
  with actual 1/2-second backoff. No fake 500 or fabricated timeout is returned.
  These are **controlled transport failures**, not evidence of provider-side
  429/5xx outages or successful server processing of the timed-out requests.
- Final run: **6 real HTTP 200 OCR responses and 12 actual ReadTimeouts**.
  Requests use only generated, nonsensitive scan text. No DeepSeek call occurs.
- Raw uploads, Chroma, and fixtures are in a fresh system temporary tree.
  After the child releases Windows handles, the parent removes it and reports
  `ISOLATED_STORAGE_CLEANUP: PASS`. Repository business storage is not targeted.

## PDF outcomes

| Case | Observed result | AC |
|---|---|---|
| Two native pages | HTTP 200 SUCCESS; ordered native text persisted; zero OCR calls | F002-01; F003 native parsing |
| Two scanned pages | Two real HTTP 200 responses; SUCCESS, no warnings; `SCAN IMAGE ONE` precedes `SCAN IMAGE TWO` in persisted text | F004-01 |
| Native + scanned page | One real HTTP 200 OCR response; SUCCESS; native first, recognized scan second | Section 5 F003-03; Section 12 F003-02; F004-02 |
| Five pages, third scanned page times out | Three real timeouts, two actual backoffs; HTTP 200 SUCCESS_WITH_WARNINGS; pages 1/2/4/5 retained; exactly page 3 OCR_PAGE_FAILED warning | F002-07, F004-03, F004-05 |
| Three scanned pages all time out | Nine real timeouts; HTTP 422 FILE_PARSE_ERROR; warnings for pages 1/2/3 in error.details.warnings | F002-08, F004-04 |
| Post-FAILED state | Raw file absent; complete Chroma chunk records unchanged; no new vector/metadata records; keyword token mappings and cached chunk IDs unchanged; file list excludes failed upload | F002-09 |
| Same bytes and filename after FAILED | Three real HTTP 200 OCR responses; HTTP 200 SUCCESS; all three page markers persisted | F002-09 |
| Re-upload after partial success | Case-variant same filename returns HTTP 409 FILE_ALREADY_EXISTS | F002-10 |

Final successful DashScope request IDs, also present next to timings in the log:

- Scanned pages: `e4f25754-44b4-987d-a0ab-441ddd96c4cb`, `ccc74c6d-96ae-935b-b83a-cfe03fdf3771`.
- Mixed page: `754b6e14-d615-9258-9889-49d88a3677dc`.
- Same-name recovery: `ebfd8148-9bbe-911c-ae8e-57ba2d9ad290`, `689cec1a-3e9e-9aa2-8c65-a0de36a80572`, `31c3474f-5479-9205-9ffc-f166278219a7`.

The log contains generated PDF SHA-256 values, page definitions, extracted
text, statuses, warnings, and rollback observations. Fixtures reuse the existing
runtime builders; no production document was sent. Qwen sometimes wraps OCR
text in code fences or an introductory sentence. Required text and page order
are preserved; no unrequested response-cleaning feature was added.

## Acceptance coverage

The SPEC reuses F003 IDs with different meanings between Sections 5 and 12;
the section-qualified rows below cover both definitions.

| SPEC criteria | Final evidence | Result |
|---|---|---|
| Section 5 AC-F002-01…06 and Section 12 AC-F002-01…06 | Native PDF persistence/listing; same-KB case-insensitive duplicate; same name in separate KBs; 51 MiB rejection; .exe rejection; 0-byte rejection; no residual state | PASS |
| Section 12 AC-F002-07…10 | Real transport failure scenarios, warnings, complete rollback, successful same-name recovery, duplicate protection after partial success | PASS |
| Section 5 AC-F003-01…05 | UTF-8 and GBK text; real mixed-page OCR; DOCX paragraph/table cells; XLSX sheet1/sheet3 with empty sheet2 | PASS |
| Section 12 AC-F003-01…03 | GBK fallback; ordered native + real OCR; DOCX tables | PASS |
| Section 5 AC-F004-01…05 | Real scanned/mixed OCR and controlled real timeouts, all three outcomes, observable warnings | PASS |
| Section 5 AC-F005-01…02 | Trim/drop blank lines; whitespace-only upload rejected and removed | PASS |
| Section 5 AC-F006-01…03 | Nested Markdown title prefix; 2000-character text → 800/800/640 with 120 overlap; 300 characters retained | PASS |
| Section 5 AC-F007-01…02 | Real local 3×512 normalized embeddings and singleton reuse | PASS |
| Section 5 AC-F008-01…03 | Ten UUID chunks/top-3 public similarity results; exact 5/3 deletion fixture; AST check for forbidden Chroma private access in app code | PASS |
| Additional T1201 formats/validation | All 11 extensions: .txt/.md/.csv/.json/.log/.pdf/.docx/.xlsx/.xlsm/.xltx/.xltm; UTF-16 fallback; invalid path names; corrupt PDF with no residual file | PASS |
| DOD-02, T1201 Completion Conditions | All applicable Section 5/12 ingestion ACs above pass; no FAILED residuals; SUCCESS_WITH_WARNINGS correctly reported | PASS |

## Findings and corrections

1. Initial sandbox live execution could not connect: real SDK `ConnectionError`
   / `MaxRetryError`, with no successful OCR response. It was not accepted as
   OCR PASS. Authorized execution outside the network restriction reached
   DashScope successfully. [live-sandbox.txt](live-sandbox.txt) retains that
   failed attempt (83/91).
2. The first authorized-network run reached real Qwen successfully but remained
   **89/91 FAIL**. [live-network.txt](live-network.txt) preserves this pre-fix run.
   Two failures were investigated, not relabeled as PASS.
3. **Product bug:** malformed PDF opening by filename retained a PyMuPDF native
   handle in the exception traceback on Windows. Upload rollback's unlink
   failed with WinError 32, leaving `broken.pdf`. The deterministic pre-fix
   run also reproduced it: [deterministic-regression.txt](deterministic-regression.txt).
   `parse_pdf_file` now reads bytes before opening the PDF stream so it owns
   and closes the filesystem read independently of parser errors. The new
   regression unlinks while the actual exception/traceback is still alive.
   The final real API matrix verifies corrupt-file rejection and no residual.
   This adds a bounded in-memory PDF copy (upload limit defaults to 50 MiB),
   with no format/API/configuration/dependency change.
4. **Test oracle correction:** `FAILED_SCAN_UNIQUE` tokenized to common words
   including `SCAN`, matching previously successful real OCR text. The absent
   token query is now an unshared word; the stronger assertions also compare
   complete Chroma records, actual token-to-chunk mappings, and cached IDs.
   Chroma record comparisons ignore unspecified list order.
5. An exploratory run used the wrong SDK timeout keyword and is excluded from
   acceptance. Installed SDK source confirmed `request_timeout`; both linked
   network runs and final evidence use the correct keyword. Early console
   captures may show replaced non-ASCII characters; `live-final.txt` is a direct
   UTF-8 capture and is authoritative.

## Scope and review

Product diff is limited to the malformed-PDF handle fix. Verification changes
add opt-in live mode and ingestion assertions; deterministic mode remains
explicitly classified as substituted regression evidence. `.env`, SPEC,
dependencies, model weights, business storage, and other task definitions were
not modified. No commit was made.

Existing `.claude/settings.local.json` and inaccessible `backend/tmpnw2f1mgn/`
predate this task and were left untouched. Final review checks task-local
diffs/artifacts for literal configured secrets without printing secret values.
The [review record](review.txt) records the passing secret/scope checks and
SHA-256 values of the three changed Python files. T1201 is now marked DONE in
TASKS.md after the live run, regression checks, AC mapping, and diff review.

Earlier Phase 12 learning/audit artifacts describe the pre-live blocked state.
This T1201 evidence supersedes their T1201/DashScope availability statements;
it does not re-run or complete T1202/T1204 or change the Phase 12 Gate verdict.
Stop after T1201.
