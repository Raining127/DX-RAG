# Public evidence sanitization and provenance

Date: 2026-09-07. This is a publication transform, not a new execution or acceptance decision.

The 17 public files below are explicitly **sanitized representations**, kept at their existing relative paths so Markdown, JSON matrices and read-only learning documents continue to resolve. Before replacement, each original was copied byte-for-byte to the corresponding path beneath `.local-originals/`, which is ignored by Git. Originals were not deleted. No silent overwrite of historical evidence is implied.

Only filesystem path spans in these 17 files changed. UTF-8 bytes outside those spans, line endings, test/assertion results, provider response semantics, request IDs, timestamps, exit codes and LIVE/DETERMINISTIC labels are unchanged. No header was inserted into the captures. In particular, the historical DeepSeek exit 2 remains unchanged.

Replacement rules:

- Absolute repository prefix -> `<REPO_ROOT>`; preserve the repository-relative suffix.
- User-local temporary root plus the generated per-run directory -> `<TEMP_DIR>`; preserve paths inside that run. Random run-directory names are omitted.
- Local Python installation prefix -> `<PYTHON_ROOT>`; preserve library/package-relative suffixes.
- Other user-home prefix -> `<USER_HOME>` if encountered.
- Normalize Windows separators, including escaped separators, to `/` only inside substituted filesystem paths.

The machine-readable [manifest](sanitization-provenance.json) records original and sanitized SHA-256 values plus the ignored local-original locations. Original values can be checked locally; public clones can verify sanitized hashes. A public hash alone does not independently prove the original-to-public transformation without access to the originals.

The repository `.gitattributes` sets `/docs/verification/** -text` so Git does not change evidence line endings on add/checkout. This preserves the exact bytes addressed by SHA-256 even when local `core.autocrlf` is enabled. It does not change product-file attributes.

Historical `baseline.json` / `blocker-audit-baseline.json` files retain their original hashes and meanings. They are historical snapshots, not current-public-byte checksums. For a sanitized artifact, join its original hash to the manifest to find the public hash. The [LIVE validity record](T1204/live-evidence-validity.json) retains every original field and adds explicit public hashes; its original bytes are also backed up locally. T1201 LIVE has a sanitized public hash; T1202 LIVE needed no transformation and its two hashes are identical.

README/matrix publication notices and the LIVE validity metadata are documentation updates, not path-only transformations of captured observations. Their pre-update versions are also preserved under `.local-originals/`. The acceptance JSON rows and results are unchanged; all existing public evidence targets still resolve.

| Public sanitized representation | Original SHA-256 | Sanitized SHA-256 |
|---|---|---|
| [T1201/backend-regression.txt](T1201/backend-regression.txt) | `28a53a8e6acd5324b414e36b4613d644a92643959130960cf5d99fcf32b97f03` | `7652e28d7be8b8e33dc5be55e589a1a45377894f75dcf2a548139d40e45c753c` |
| [T1201/deterministic-final.txt](T1201/deterministic-final.txt) | `468434f71b765f5add534664948234b51f8c26702492f63718b531ebb595970f` | `f96bc24c5a78978b88f07f5af9ba8e4e440dfeb6ed55a73e884287a6c20f5aff` |
| [T1201/deterministic-regression.txt](T1201/deterministic-regression.txt) | `7dd4bb7701b1df55409eab1fac42c833be85c2f37d204b204278d1a3d77cde73` | `de4d930f8c9225261fc18410b7bca7c6d22410a852ce90b842c2085d0f3117be` |
| [T1201/live-final.txt](T1201/live-final.txt) | `99ab2890e7ae90645f4e5f476b13d216d6796f55103512b64e12f77956d185ca` | `670f0c5f86ce47364193ee216f87edf4db6c5bac21573e885f384a3b27cc61e8` |
| [T1201/live-network.txt](T1201/live-network.txt) | `4a38a9d236cea6b4bab69ce070e8d739b2b90f64cfaebe1c1dab384f4afa3ba4` | `1dfabce3e66dd4fcc9a99a9ea44c27e17ab170bf9e888b8f27c315906d37f96f` |
| [T1201/live-sandbox.txt](T1201/live-sandbox.txt) | `c7a274981e886b018a61380bd708748c57967dc41baf4ddc027d274ef457eb61` | `fa1e09f8c28dfccecfe4002d64beeeea29c48eea29c9ab8bab755f4b3ced13a5` |
| [T1201/rollback-regression.txt](T1201/rollback-regression.txt) | `f954536af03d791c78ead6cbc1b6770efb118899f051d0afb638315698a888c3` | `8dd87f03cbd7a8b7db9159a2f47a7317ced9c6e809e458f4246b18536ebce4ab` |
| [T1202/blocker-audit-deterministic.txt](T1202/blocker-audit-deterministic.txt) | `54db12b4c34e9246913bc1bd1ccb83b07e5306300e8d5fd961e9afc7e494c778` | `8517dc7ba537b955f0e0f351b1fac95c857d34ea1c6ebc12c219710ffa39f689` |
| [T1202/deterministic.txt](T1202/deterministic.txt) | `8a06f19fb0aec22eed1445d74eb4284eddd13962907e58557a2213fb11dcad2e` | `7bd1d2e6f3d108e5034ec861decdbb7e6fdd96e5791ebf1e5b10b4a968a1ad8b` |
| [T1204/backend-final.txt](T1204/backend-final.txt) | `a5233a9dddf9a0ade68d946edf0440a1427bc80916bac91c6be377988aae6afa` | `06b4697dfc9c8d4f4d72d7c13cfca54546b8e9a46753503ffdf7aaca2b061ed7` |
| [T1204/bge.txt](T1204/bge.txt) | `053f0897efe76d3dbb49d1db2f2e6b0302acda4866f22ee972c4f6156bc28945` | `67fcef346f7bec5e773d58b89dbec19887c2aa4816e7680b0804a8775b94f8de` |
| [T1204/browser.md](T1204/browser.md) | `b89942f078cbbd0748a484481a1bc3a0cd0ba156e93ee7d395a5790c9fa79238` | `4fc65ac1960e2f72d5cedf2915560e92ee7279764405af686f4c2eba6f60173b` |
| [T1204/rollback-final.txt](T1204/rollback-final.txt) | `74d674aa2df2feaee81fbcb69f894c0118205f916a93770279badca9a3775aca` | `b9a84df9dbbdb920658de077105ec408d0b2862d971fda35b55c13f98fef7f99` |
| [T1204/t1201-final.txt](T1204/t1201-final.txt) | `6da8a3ed01f0c8369402a0ef2b45ff17f1a6fdf8f4be64b49a3587654ae3a625` | `818beede0c4c46e15519248a0fc9f4eef5ceb1924fe5b8f58ca4718dcd6634c9` |
| [T1204/t1202-final.txt](T1204/t1202-final.txt) | `2ec117fe0a2feb30fe8fa6b1b685ccbd3700dd4a28a5e578173bc3ff1eaf4316` | `8517dc7ba537b955f0e0f351b1fac95c857d34ea1c6ebc12c219710ffa39f689` |
| [T1204/t1203-final.txt](T1204/t1203-final.txt) | `449af56dea6faa6461b00e4644f18055e254073be8585c9180865672c0e9a6d2` | `d3d1c43007988364bd0ea26a1d4c87364ef1d371ba78811af9422aa6f9a8b49c` |
| [T1204/t1204-final.txt](T1204/t1204-final.txt) | `ce016305b857031ba947cbdf0eb28688fe14c3964fc378881ef108cf27a15421` | `fb2da54d5c63cc5ec3d30c3a957dc031830fefe6c69716ec4959ad478bb77884` |
