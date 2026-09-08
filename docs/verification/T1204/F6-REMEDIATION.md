# F-6 Remediation and T1204 Incremental Re-audit

Date: 2026-09-07. SPEC v1.7 FROZEN. **F-6: CLOSED at remediation level.**
T1203 and affected T1204 requirements: **PASS**. Historical remediation-time
Gate: `PHASE_12_FAIL — FIX_REQUIRED`. Current final Gate after the completed
independent incremental re-review: **PHASE_12_PASS**; **F-6 CLOSED / REMEDIATED**.
See the [recorded Gate closure](../PHASE-12-GATE-CLOSURE.md).
No Gate was executed here; no commit, push or tag was made.

## Requirement and root cause

F002 AC-F002-01 requires a successful upload to appear in the KB file list.
F017 Sections 17.3/17.6 require file counts and file-management UI states.
T1203 explicitly includes frontend integration; T1204 includes DOD-01.

FileUpload previously updated only its local upload outcome. Home kept all
panels mounted, but had no upload-success callback. FileManager fetched on
KB selection change and retained its empty list when that selection stayed
unchanged. The old T1203 source-string wiring check could not detect this.

## Product change

- [FileUpload](../../../frontend/components/FileUpload.tsx) emits
  `onFileUploaded(collectionName)` only after a successful upload response,
  including SUCCESS_WITH_WARNINGS. Rejected requests emit no event.
- [Home](../../../frontend/app/page.tsx) increments that KB's confirmed file
  count and its `fileRevisions` entry using functional state updates. This
  follows the existing server-confirmed delete-count projection.
- [FileManager](../../../frontend/components/FileManager.tsx) observes the
  selected KB's revision and refetches its authoritative file list even while
  hidden. Existing request-version guards apply to the refetch. Manual KB
  changes record the loaded revision to avoid redundant refreshes.
- KnowledgeBaseManager consumes the existing shared collections prop, so
  its rendered total and per-KB counts update without changing that component.
  QA receives no collection identity mutation or reset signal from uploads.

No API, backend, dependency, global state library or frozen requirement changed.
This fixes ordinary confirmed uploads in the same page session. It does not
claim to solve pre-existing upload-during-KB-rename ownership races, concurrent
external writers, or cross-storage crash recovery.

## Evidence classification and red/green

[verify_f6_integration.cjs](../../../frontend/scripts/verify_f6_integration.cjs)
loads actual Home, FileUpload, FileManager, KnowledgeBaseManager and QAPanel
TSX through installed TypeScript. The actual Home element props connect the
components; state setters, refs, dependency-aware effects, memo/callback
identity and rerender scheduling are controlled. API responses come from a
deterministic in-memory server. There are no source-string acceptance checks.

**DETERMINISTIC component/integration / MOCKED API and hooks**, not browser
DOM, Ant Design event-dispatch, HTTP E2E or live provider evidence. The test
invokes actual element handlers, inspects actual table data/preview content,
and checks KnowledgeBaseManager's rendered total plus shared per-KB counts.
Backend persistence/security are independently exercised by T1203.

Before the product change, the new scenario A failed with exit 1:
`F-6: mounted FileManager must refresh after same-KB upload: 0 !== 1`.
After the fix, all five scenario groups pass; the final script additionally
checks that QA history survives file deletion/re-upload.

| Scenario | Observable checks | Result |
|---|---|---|
| A | Initially empty KB-A list; upload success; server has 1 file; unchanged selection and mounted panel; new list request; table has filename; count 1; QA draft preserved | PASS |
| B | Same session upload/list/preview/delete; list empty and count 0; same-name re-upload has new file identity, list/count 1; QA history preserved | PASS |
| C | KB-B same-name upload does not refetch/change KB-A; selecting B shows B identity; deleting B preserves A and both counts | PASS |
| Error boundaries | Warning-success synchronizes; rejected upload does not refresh/increment | PASS |
| KB mutations | Actual KB rename modal and delete confirmation handlers propagate through Home; FileManager follows rename/fallback with correct rows/counts | PASS |

The test never changes SideMenu or remounts FileManager to make uploads visible.
The prior browser file-chooser limitation remains; **browser upload E2E was
not executed and is not marked PASS**.

## Commands and outcomes

[F6-RESULTS.json](F6-RESULTS.json) contains the execution outputs and exit codes.

| Command | Pass / Fail / Skip | Exit |
|---|---|---:|
| frontend: `node scripts/verify_f6_integration.cjs` | 5 / 0 / 0 scenario groups | 0 |
| frontend: `node scripts/verify_t1204_contracts.cjs` | 2 / 0 / 0 boundary checks | 0 |
| frontend: `node node_modules/typescript/bin/tsc --noEmit --incremental false` | check PASS | 0 |
| frontend: `npm.cmd run build` | check PASS; 4 static pages | 0 |
| isolated cwd: existing T1203 script | 43 / 0 / 0 | 0 |
| isolated cwd: backend unittest discovery | 83 / 0 / 0 | 0 |

`npm run build` initially failed before build execution because PowerShell
blocked npm.ps1. `npm.cmd run build` succeeded without changing system policy.
No standalone lint command is configured; no lint suite was invented.

The exact backend wrapper, run as `python -` from repository root, avoids
loading backend/.env: both parent/child tests run from an empty temporary
directory and use an absolute source path. Neither script changes cwd.

```python
from pathlib import Path
import os, subprocess, sys, tempfile
repo = Path.cwd()
env = os.environ.copy()
env['PYTHONDONTWRITEBYTECODE'] = '1'
env['PYTHONPATH'] = str(repo / 'backend')
env['ANONYMIZED_TELEMETRY'] = 'False'
with tempfile.TemporaryDirectory(prefix='f6_no_dotenv_') as cwd:
    for args in [
        [sys.executable, '-B', str(repo / 'backend/scripts/verify_t1203_file_management_security.py')],
        [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(repo / 'backend/tests'), '-q'],
    ]:
        r = subprocess.run(args, cwd=cwd, env=env, capture_output=True,
                           text=True, encoding='utf-8', errors='replace')
        print('COMMAND', 'T1203' if 'scripts' in args[2] else 'backend unittest')
        for line in (r.stdout + r.stderr).splitlines():
            if line.startswith(('Required checks:', 'RESULT:', 'Ran ', 'OK', 'FAILED')) or '[FAIL]' in line:
                print(line)
        print('EXIT_CODE', r.returncode)
        if r.returncode:
            sys.exit(r.returncode)
print('EMPTY_CWD_DOTENV_ISOLATION: backend/.env not loaded; temp cleanup complete')
```

## T1203 and affected T1204 acceptance

| Requirement | Evidence | Result |
|---|---|---|
| F002 AC-F002-01/03 successful upload visibility and KB isolation | Integration A/C + actual backend T1203 | PASS |
| F016 AC-F016-01/03 list and empty state | Integration A/B + existing literal three-file fixture (unchanged backend) | PASS |
| F016 AC-F016-04/05/06/07 preview and errors | Current backend T1203; component B exercises preview handler/output | PASS |
| Section 12 AC-F016-08/09 cascade and missing-file error | Current backend T1203 + component B/C delete projection | PASS |
| AC-SEC-01/02 path rejection and valid filename | Current backend T1203 | PASS |
| F017 Sections 17.3/17.6 normal UI state/count synchronization | Actual Home/feature wiring, integration A/B/C | PASS |
| F017-02 / FE-02 validation | Existing actual component boundary probe rerun 2/2 | PASS |
| F017-03 / FE-03 adjacent QA state | Ctrl+Enter produces fixture answer/history; draft/history survive file events. Markdown/browser behavior retains prior scoped evidence; no new browser claim | PASS in affected scope |
| DOD-01 | Missing cross-feature state update repaired and regression-proven | PASS in affected scope |
| DOD-02 through 06 | Supplementary AC evidence; API/dependencies unchanged; error tests, scoped diff and production type/build checks | PASS in affected scope |

This is an incremental re-audit, not a newly executed 104-row full audit.
The acceptance/DoD matrices link this supplement; unrelated rows retain their
existing evidence. T1201/T1202 source and live artifacts are preserved, with
no Qwen/DeepSeek calls and no new natural-429/5xx/403 gate.

## Completion boundary

Final hygiene review: `git diff --check` PASS; new/updated evidence links
resolve; secret-pattern scan has no matches (no .env comparison/read).
Start-of-remediation SHA-256 inventory confirms backend sources/scripts/tests,
SPEC, dependencies, existing live captures and unrelated user modifications
were preserved. All 17 public representation hashes still match the existing
sanitization manifest. The AC inventory remains 104 rows; only 20 relevant
occurrences gained supplemental evidence. Product edits are confined to the
three frontend files above; no backend or API change.

T1203 DONE is reconfirmed after backend and component integration verification;
T1204 DONE was reconfirmed for the affected requirements at remediation time.
That remediation alone did not issue Gate PASS. The subsequent independent
incremental re-review has now issued **PHASE_12_PASS**, with T1203/T1204 PASS. Remaining known Phase 12 Gate blockers after this fix:
**NONE identified in the authorized remediation scope**. Remediation-time next
action: **PHASE_12_GATE_RE_REVIEW** (historical; subsequently completed PASS).

Previous public-release readiness predates these edits; this document does
not extend that release approval to the new diff. Original captures and
sanitization provenance remain unchanged. No commit/push/tag or Gate execution.
