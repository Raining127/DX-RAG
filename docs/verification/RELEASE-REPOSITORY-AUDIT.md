> **Follow-up status:** Path disclosure is RESOLVED with preserved original bytes and explicit public hashes; see [sanitization/provenance](SANITIZATION-PROVENANCE.md). The user approved the four-file learning group for v1.0.0; the current [Public Release Readiness Report](PUBLIC-RELEASE-READINESS.md) records SAFE_TO_COMMIT and supersedes the two open findings below. The remainder records the previous audit checkpoint.

# Release Repository Audit

Date: 2026-09-07. Scope: Git release contents only; no acceptance rerun, product/script/SPEC change, commit, push or tag.

## KEEP_AND_COMMIT

All retained original artifacts are listed below. KEEP means evidence retention; public release remains subject to the local-path finding below. Referenced execution captures are deliberate exceptions to raw-log removal: deleting them would discard assertion-level records, historical failure observations or break recorded hash provenance. A later execution cannot recreate historical provider IDs/responses. No such capture was silently replaced with a new run.

| Artifact | Classification / reason |
|---|---|
| [T1201/backend-regression.txt](T1201/backend-regression.txt) | A ? README-linked regression/failure evidence also covered by historical hash baselines |
| [T1201/corrupt-pdf-regression.txt](T1201/corrupt-pdf-regression.txt) | A ? README-linked regression/failure evidence also covered by historical hash baselines |
| [T1201/deterministic-final.txt](T1201/deterministic-final.txt) | A ? README-linked regression/failure evidence also covered by historical hash baselines |
| [T1201/deterministic-regression.txt](T1201/deterministic-regression.txt) | A ? README-linked regression/failure evidence also covered by historical hash baselines |
| [T1201/live-final.txt](T1201/live-final.txt) | A ? historical provider/network observations; README and/or hash-baseline referenced |
| [T1201/live-network.txt](T1201/live-network.txt) | A ? historical provider/network observations; README and/or hash-baseline referenced |
| [T1201/live-sandbox.txt](T1201/live-sandbox.txt) | A ? historical provider/network observations; README and/or hash-baseline referenced |
| [T1201/README.md](T1201/README.md) | A ? formal acceptance, decision, browser boundary or retained execution summary |
| [T1201/review.txt](T1201/review.txt) | A ? audit decision / preservation and review record |
| [T1201/rollback-regression.txt](T1201/rollback-regression.txt) | A ? README-linked regression/failure evidence also covered by historical hash baselines |
| [T1202/baseline.json](T1202/baseline.json) | A ? machine-readable acceptance / historical hash provenance |
| [T1202/blocker-audit-baseline.json](T1202/blocker-audit-baseline.json) | A ? machine-readable acceptance / historical hash provenance |
| [T1202/blocker-audit-deterministic.txt](T1202/blocker-audit-deterministic.txt) | A ? assertion-level execution evidence referenced by README / blocker audit / matrices |
| [T1202/blocker-audit-failure-contract.txt](T1202/blocker-audit-failure-contract.txt) | A ? assertion-level execution evidence referenced by README / blocker audit / matrices |
| [T1202/blocker-audit-focused.txt](T1202/blocker-audit-focused.txt) | A ? assertion-level execution evidence referenced by README / blocker audit / matrices |
| [T1202/blocker-audit-review.txt](T1202/blocker-audit-review.txt) | A ? audit decision / preservation and review record |
| [T1202/BLOCKER-AUDIT.md](T1202/BLOCKER-AUDIT.md) | A ? formal acceptance, decision, browser boundary or retained execution summary |
| [T1202/deterministic.txt](T1202/deterministic.txt) | A ? assertion-level execution evidence referenced by README / blocker audit / matrices |
| [T1202/focused-before.txt](T1202/focused-before.txt) | A ? assertion-level execution evidence referenced by README / blocker audit / matrices |
| [T1202/live-final.txt](T1202/live-final.txt) | A ? historical provider/network observations; README and/or hash-baseline referenced |
| [T1202/live-first.txt](T1202/live-first.txt) | A ? historical provider/network observations; README and/or hash-baseline referenced |
| [T1202/live-reviewed.txt](T1202/live-reviewed.txt) | A ? audit decision / preservation and review record |
| [T1202/README.md](T1202/README.md) | A ? formal acceptance, decision, browser boundary or retained execution summary |
| [T1202/review.txt](T1202/review.txt) | A ? audit decision / preservation and review record |
| [T1202/summary.json](T1202/summary.json) | A ? machine-readable acceptance / historical hash provenance |
| [T1204/acceptance-matrix.json](T1204/acceptance-matrix.json) | A ? machine-readable acceptance / historical hash provenance |
| [T1204/ACCEPTANCE-MATRIX.md](T1204/ACCEPTANCE-MATRIX.md) | A ? formal acceptance, decision, browser boundary or retained execution summary |
| [T1204/backend-final.txt](T1204/backend-final.txt) | A ? assertion-level execution evidence referenced by README / blocker audit / matrices |
| [T1204/baseline.json](T1204/baseline.json) | A ? machine-readable acceptance / historical hash provenance |
| [T1204/bge.txt](T1204/bge.txt) | A ? assertion-level execution evidence referenced by README / blocker audit / matrices |
| [T1204/browser.md](T1204/browser.md) | A ? formal acceptance, decision, browser boundary or retained execution summary |
| [T1204/DOD-MATRIX.md](T1204/DOD-MATRIX.md) | A ? formal acceptance, decision, browser boundary or retained execution summary |
| [T1204/EXECUTION-SUMMARY.md](T1204/EXECUTION-SUMMARY.md) | A ? formal acceptance, decision, browser boundary or retained execution summary |
| [T1204/frontend-component.txt](T1204/frontend-component.txt) | A ? assertion-level execution evidence referenced by README / blocker audit / matrices |
| [T1204/frontend-validation.txt](T1204/frontend-validation.txt) | A ? assertion-level execution evidence referenced by README / blocker audit / matrices |
| [T1204/live-evidence-validity.json](T1204/live-evidence-validity.json) | A ? machine-readable acceptance / historical hash provenance |
| [T1204/README.md](T1204/README.md) | A ? formal acceptance, decision, browser boundary or retained execution summary |
| [T1204/review.txt](T1204/review.txt) | A ? audit decision / preservation and review record |
| [T1204/rollback-final.txt](T1204/rollback-final.txt) | A ? assertion-level execution evidence referenced by README / blocker audit / matrices |
| [T1204/t1201-final.txt](T1204/t1201-final.txt) | A ? assertion-level execution evidence referenced by README / blocker audit / matrices |
| [T1204/t1202-faults.txt](T1204/t1202-faults.txt) | A ? assertion-level execution evidence referenced by README / blocker audit / matrices |
| [T1204/t1202-final.txt](T1204/t1202-final.txt) | A ? assertion-level execution evidence referenced by README / blocker audit / matrices |
| [T1204/t1203-final.txt](T1204/t1203-final.txt) | A ? assertion-level execution evidence referenced by README / blocker audit / matrices |
| [T1204/t1204-final.txt](T1204/t1204-final.txt) | A ? assertion-level execution evidence referenced by README / blocker audit / matrices |

This audit is also KEEP_AND_COMMIT. The existing `docs/T1204-SPEC-ACCEPTANCE-AUDIT.md`, task ledger, verification scripts, tests, lockfiles and `backend/.env.example` remain retained.

## IGNORE / REMOVE

B ? REGENERATABLE_IGNORE. Removed 10 T1204 captures (55,080 bytes). Results retained in [EXECUTION-SUMMARY.md](T1204/EXECUTION-SUMMARY.md); current assertion-level final captures remain. Hashes below identify removed inputs, not files required to exist.

| Removed capture (historical identifier, not a link) | Original SHA-256 |
|---|---|
| `T1204/backend-unittest.txt` | `a665a912053b805c3997b16750da15d3d2e2dce40b00d24b72a7e3bfec0c3a83` |
| `T1204/rollback.txt` | `2abb792813c7b42624bf8a126d9d57f08e5339d9883207671984fdba66578c9d` |
| `T1204/t1201.txt` | `f201cfe898309efded777a9b6285b8bbdbccb17b72a11c0cddc3742a5391532e` |
| `T1204/t1202.txt` | `83277b380275e291977595bf1b4db71d962a4da79abd6d2e7340c9231449edc9` |
| `T1204/t1203.txt` | `00dc4f9e047a697be690fee4acda4975a0e168b092356a24c30224896226870b` |
| `T1204/t1204.txt` | `e155423c2fb3f12c785ff1a9bf63cfbf04ff8dd9206c3b8ead8461d1bb208a45` |
| `T1204/t1204-fixture-setup-failure.txt` | `22dafacb1d9514ae946bb99a496e0678e45a630ad0f4cb92ca6922b088be6cb7` |
| `T1204/frontend-build.txt` | `9ec2949a7ef16174d25644a26fccda81cfba1486b7bc39969f01f6e770b1d61f` |
| `T1204/frontend-typecheck.txt` | `7ddf0df9da20c33e5b6dec3c9af64035bbd524f414915284d1d19e3fe924ad80` |
| `T1204/frontend-dependencies.txt` | `b157a22813a6cd5291d0c713a25c6c2d3de6528f13b5bc1d6b8e279a0e14b35d` |

The four earlier rollback/T1201/T1202/T1203 captures match their final counterparts after normalizing only temporary run IDs and the ingestion timestamp. Earlier backend 82/82 and T1204 29/29 are superseded by 83/83 and 42/42. Build/typecheck/dependency command results and installed versions were transcribed before deleting stdout. The fixture setup failure remains explicitly recorded as exit 1; it was never acceptance PASS.

## REQUIRED_RUNTIME_OR_TEST_ARTIFACT

C ? no files under `docs/verification` are read as runtime/test inputs by the inspected Phase 12 runners. Backend runners build isolated fixtures; frontend contracts read actual component source. `verify_t1204_spec_acceptance.py` reads SPEC. Live runners read the local environment during execution; no runner was executed in this audit. `verify_bge_model.py` requires separately downloaded model files/cache metadata. Keep verification scripts, actual source/tests, dependency manifests and lockfiles; do not delete local model data as repository hygiene.

## LOCAL_ONLY

D ? `backend/.env` is untracked and ignored; it was never opened, imported, hashed or printed. `backend/.env.example` is tracked and not ignored. Local uploads, Chroma/data/database files, model weights, caches, incremental TypeScript state, `.claude/settings.local.json` and the pre-existing inaccessible `backend/tmpnw2f1mgn/` belong outside Git. No local storage was deleted or inspected for content.

The inaccessible temporary directory remains uninspected. Git also warned that the user-global ignore file could not be read; project-level rules were checked directly.

## .gitignore changes

Added exact local agent settings and existing temporary-directory ignores, `uploads/`, and `*.tsbuildinfo`. Ignore new `.txt` captures in T1201/T1202/T1204, with explicit exceptions for retained reviewed evidence. Existing environment/model/Chroma/cache rules remain. No blanket JSON/Markdown ignore; future evidence promotion requires deliberate review.

## Secret scan

**PASS** for pattern-based scanning of all original verification artifacts and the final retained set: no API-key patterns, Authorization/Bearer credentials, JWTs, private keys or credential assignments detected. Broad auth/token mentions were test names, documentation or token-usage fields; observed URL hosts were the public DeepSeek endpoint and loopback. No secret values were printed. This is not an exact comparison against configured credentials: reading `.env` was prohibited and was not done.

**Public-release environment finding:** 17 retained files contain machine-specific user/workspace/temp paths. These are not credentials, but disclose local environment information. Existing LIVE and historical hash-linked files were deliberately left byte-for-byte unchanged. Resolve the disclosure policy or prepare a separately traceable sanitized evidence set before public release; do not silently edit immutable captures or overwrite historical hashes.

| Artifact | Lines containing local paths |
|---|---|
| [T1201/backend-regression.txt](T1201/backend-regression.txt) | 84 |
| [T1201/deterministic-final.txt](T1201/deterministic-final.txt) | 7 |
| [T1201/deterministic-regression.txt](T1201/deterministic-regression.txt) | 13, 221, 245, 263, 267, 271, 275, 289 |
| [T1201/live-final.txt](T1201/live-final.txt) | 5, 8 |
| [T1201/live-network.txt](T1201/live-network.txt) | 9, 13 |
| [T1201/live-sandbox.txt](T1201/live-sandbox.txt) | 9, 13 |
| [T1201/rollback-regression.txt](T1201/rollback-regression.txt) | 4, 5, 164, 166, 176, 245, 247, 257, 267, 273, 276, 279, 281, 283, 285, 292, 295 |
| [T1202/blocker-audit-deterministic.txt](T1202/blocker-audit-deterministic.txt) | 4 |
| [T1202/deterministic.txt](T1202/deterministic.txt) | 2 |
| [T1204/backend-final.txt](T1204/backend-final.txt) | 87 |
| [T1204/bge.txt](T1204/bge.txt) | 4 |
| [T1204/browser.md](T1204/browser.md) | 15 |
| [T1204/rollback-final.txt](T1204/rollback-final.txt) | 6, 7, 166, 168, 178, 247, 249, 259, 269, 275, 278, 281, 283, 285, 287, 294, 297 |
| [T1204/t1201-final.txt](T1204/t1201-final.txt) | 9 |
| [T1204/t1202-final.txt](T1204/t1202-final.txt) | 4 |
| [T1204/t1203-final.txt](T1204/t1203-final.txt) | 5 |
| [T1204/t1204-final.txt](T1204/t1204-final.txt) | 5 |

## Broken evidence references

**NONE** after replacing removed capture links in README, Acceptance Matrix (Markdown and JSON), and DoD Matrix. The original acceptance JSON inventory and outcomes are unchanged. All T1201/T1202 files and retained raw captures preserve their pre-audit SHA-256; both LIVE hashes match `live-evidence-validity.json`. Baseline JSON documents remain historical snapshots, not assertions that every current source hash still matches.

## Final diff review

`git diff --check` passed. Hygiene edits are limited to `.gitignore`, four T1204 evidence documents, the new command summary, this audit and ten untracked-log removals. Because `docs/verification` was already untracked, ordinary `git diff` does not display its edits/deletions; a pre-edit hash inventory was used for preservation review. Product, scripts, tests, task ledger and SPEC were not edited by this audit.

Concurrent external edits appeared during the audit in `docs/learning/README.md` and `docs/learning/phase-12-integration-acceptance.md`, plus new `docs/learning/phase-12-learning-review.md`. They were left untouched and are not covered by this release-content review.

## Final recommendation

**NEEDS_ACTION** before a public release: resolve the retained local-path disclosure and review the concurrent learning-document changes. Secret-pattern checks and evidence-reference integrity pass; completed T1201/T1202/T1204 acceptance is unchanged. No commit, push or tag was created.
