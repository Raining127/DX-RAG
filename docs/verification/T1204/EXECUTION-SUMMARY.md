# T1204 retained command results

Transcribed from the 2026-09-07 acceptance captures during release hygiene.
No command was rerun. Original capture hashes are in the
[release audit](../RELEASE-REPOSITORY-AUDIT.md). Acceptance outcomes and
LIVE/DETERMINISTIC qualifications are unchanged.

## Build

Working directory: `frontend`. Command: `npm run build`. Exit: **0**.
Next.js 14.2.24 compiled successfully, checked types, generated all 4 static
pages, collected build traces and finalized page optimization. Routes `/`
and `/_not-found` were prerendered. This is not a standalone lint-suite claim.

## Typecheck

Working directory: `frontend`.
Command: `node node_modules/typescript/bin/tsc --noEmit --incremental false`.
Exit: **0**, no diagnostics.

## Dependencies

Working directory: `frontend`. Command: `npm ls --depth=0`. Exit: **0**.
Package: `dx-rag-frontend@0.1.0`. Installed direct versions:

| Package | Version |
|---|---|
| @types/node | 20.19.43 |
| @types/react-dom | 18.3.7 |
| @types/react | 18.3.31 |
| antd | 5.22.7 |
| next | 14.2.24 |
| react-dom | 18.3.1 |
| react-markdown | 9.1.0 |
| react | 18.3.1 |
| typescript | 5.9.3 |

The machine-specific installation path was omitted; lockfiles remain the
reproducible dependency inputs.

## Superseded runs

Four captures (rollback, T1201, T1202 and T1203 without the `-final` suffix)
match their retained final captures after normalizing only temporary run
directory names and the ingestion start timestamp. The earlier backend run
passed 82 tests, exit 0; the retained final run passes 83. The earlier T1204
probe passed 29/29, exit 0; the expanded final probe passes 42/42.
These earlier captures add no unique final acceptance coverage.

## Fixture setup failure

The expanded T1204 fixture initially exited **1** with `FileNotFoundError`
(`WinError 3`) at `file_dir.mkdir()` because the parent directory was absent.
The harness correction was `mkdir(parents=True)`, not a product fix. The
[final expanded probe](t1204-final.txt) passed 42/42, exit 0. The failed setup
is not counted as PASS; its traceback and local temporary path were removed.
