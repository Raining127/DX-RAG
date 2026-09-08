# T1202 Remaining Acceptance / Blocker Audit

Date: 2026-09-07. Verdict: **A. T1202 DONE**.

All frozen mandatory ACs applicable to T1202 are satisfied. LIVE provider
compatibility / QA evidence and DETERMINISTIC failure-path evidence are
complementary and explicitly distinguished. No frozen requirement was changed.
No product code was changed and no provider requests were made in this audit.

## Requirement sources and interpretation

Reviewed [T1202](../../TASKS.md#t1202--retrieval--qa-pipeline-e2e-verification)
(TASKS lines 2733–2784), its dependencies, implementation scope, acceptance
list and four Completion Conditions; TASKS Section 19 (lines 2881 onward);
SPEC F009–F015 (1045–1590), Section 9 (2409 onward), Section 12 (2562 onward),
Section 13 (2781 onward); and the current and historical Phase 12 artifacts.
Line references describe the repository version audited here.

Section 19 maps these ACs to their original implementation owners (T0601/02,
T0701/02, T0801–05); it does not literally assign rows to T1202. T1202's own
F009–F015 / Section 12.4 references and “All QA-related ACs pass” condition
require revisiting all 22 feature ACs plus 7 cross-feature QA ACs. None is
dropped in this audit. The [README ledger](README.md#ac-by-ac-ledger) lists
each of the 29 ACs, evidence and PASS result.

| Question | Frozen requirement and location | Conclusion |
|---|---|---|
| A. What must the product implement? | SPEC F013 lines 1394–1409: retry timeout/network/429/5xx, initial + at most 2 retries, exponential backoff, no retry for 401/403/400, defined error mapping. Section 9.3 lines 2455–2462 repeats the contract. | Must handle the received error correctly; does not prescribe how a test obtains the error. |
| B. What observable behavior must acceptance verify? | AC-F013-04 lines 1427–1430: first call fails with network timeout; retry 1 or 2 may succeed normally; three failures yield 502 LLM_UNAVAILABLE. AC-F013-01/02/03 require grounded answers, insufficient-information behavior and resistance to KB instructions. | Actual QA behavior is supported by real DeepSeek responses; retry limits/recovery/error mapping are observable application behavior. |
| C. What extra evidence did the artifact demand? | Previous README “Outcome and remaining blocker”, generated TASKS status note, and final return in verify_t1202_live.py required exit 2 when actual 429/5xx were absent. 403 was recorded as conditional/unobserved. | This was a verification-strategy gate, not an additional frozen AC. It has been removed; observations remain recorded. |

The exact Section 9.3 DeepSeek row is:

`DeepSeek Chat | timeout, network error, 429, 5xx | 2 | 3 | Exponential (~1s, ~2s)`

The next rule states:

> No retry for: 401, 403 (auth errors), 400 (bad request). Backoff applies only before retry attempts (not before initial request).

AC-F013-04's Then clause states:

> 初始请求失败后最多重试 2 次（最多 3 次总尝试）；如第 1 次或第 2 次重试成功，返回正常答案；如全部 3 次尝试均失败，返回 502 `LLM_UNAVAILABLE`

**Explicit answers:** there is no frozen SPEC/TASKS mandatory AC requiring a
naturally occurring live DeepSeek **429**, **5xx**, or **403**, separately or
collectively. There is also no requirement to trigger both 401 and 403 live.
Both are members of the same immediate, non-retry authentication-failure
contract. Live compatibility, error handling and natural remote failure
occurrence are different claims; only the first two are mandatory here.

SPEC Section 12's acceptance-source policy retains both feature-level and E2E
ACs. Section 13.1 DOD-02 requires all applicable ACs to pass; DOD-04 requires
defined error scenarios to return correct codes. Neither specifies naturally
occurring remote failures as the required test method. T1202's Completion
Condition “LLM integration works with retry” likewise adds no such method.
The user's current audit instruction explicitly permits evaluating combined
evidence; this is not a waiver of any frozen product requirement.

## Evidence and final verification

| Evidence class | Execution and result | What it establishes |
|---|---|---|
| LIVE | Historical `python backend/scripts/verify_t1202_retrieval_qa.py --live`: [70/70 checks](live-reviewed.txt), real BGE/Chroma and original DeepSeek SDK. 10 HTTP 200 responses, actual HTTP 401, four actual transport timeouts, one controlled local transport connection failure. | Real provider compatibility, grounded QA, history, sources, injection resistance, context boundaries, timeout recovery/exhaustion, network recovery and live 401 auth mapping. Transport failures were controlled, not naturally occurring provider HTTP failures. |
| DETERMINISTIC | `cd backend; python -m unittest tests.test_qa tests.test_query -v`: [60/60 PASS](blocker-audit-focused.txt), exit 0. | Existing retrieval/QA/API contracts, error mapping including missing key, malformed response, auth, retry and validation. |
| DETERMINISTIC | `python backend/scripts/verify_t1202_retrieval_qa.py`: [46/46 PASS](blocker-audit-deterministic.txt), exit 0, isolated storage cleanup PASS. | Exact AC fixtures, fusion/filter/order/context arithmetic and integrated application contracts with declared model/transport doubles. |
| DETERMINISTIC fault injection | `python backend/scripts/verify_t1202_failure_contract.py`: [15/15 PASS](blocker-audit-failure-contract.txt), exit 0, zero provider requests. Existing StatusError/completion fixtures injected into the unmodified DeepSeekClient. | 429/500/503/599 each recover at retry 1 or retry 2, or exhaust at 3 attempts with 502 LLM_UNAVAILABLE; exact backoff [1] or [1,2]. 401/403 each yield 500 LLM_AUTH_FAILED after one attempt/no sleep; 400 does not retry. |

The injected 403 plus actual 401 verify the shared auth contract. Injected
429/5xx verify bounded retry control flow; **they are not live 429/5xx
evidence**. Actual remote 429/5xx/403 remain NOT_OBSERVED, informational only.
No attempt was made to induce provider overload or a service outage.

The existing live run's raw **EXIT_CODE: 2** is preserved as historical
evidence of the previous extra gate. It is not relabeled as exit 0, nor is a
new live execution claimed. Only the runner's future exit decision changes:
failed checks still return 1; unavailable credentials still return 2; missing
natural error statuses no longer fail otherwise passing live checks. The
machine-readable summary preserves the original observation records.

## Completion Conditions and DoD

| Condition | Result / evidence |
|---|---|
| All QA-related ACs pass | PASS: all 29 rows in the README ledger; no future-task deferrals. |
| Retrieval pipeline produces correct results | PASS: real BGE/keyword/Chroma E2E plus exact deterministic score fixtures. |
| LLM integration works with retry | PASS: LIVE successful integration and transport retry; DETERMINISTIC full retry/auth contracts. |
| Source citation format correct | PASS: exact four fields, persisted identities, descending relevance, no invented inline markers. |
| DOD-01 / DOD-03 | PASS in T1202 scope: reviewed existing implementation against F009–F015 and query API; live and deterministic API observations match. |
| DOD-02 / DOD-04 | PASS in T1202 scope: applicable feature/E2E ACs and QA error scenarios covered, without imposing a natural-failure prerequisite. |
| DOD-05 / DOD-06 | PASS: verification/status/evidence changes only, existing Python style and no dependencies; preservation and secret checks in the audit review. |

See [blocker-audit-review.txt](blocker-audit-review.txt) for final syntax,
diff, exact-secret and preservation checks. Earlier [review.txt](review.txt)
is historical and its BLOCKED conclusion is superseded by this audit.
T1204 and the Phase 12 Gate are not upgraded. Stop after T1202.
