# Native C0 gate fix and authorized attempt

| Work | State | Evidence |
|---|---|---|
| W1 / T1: docs-only none rule | Done | 629ae3f, six scoped paths |
| W2 / T1: paired regression proof | Done | 10 tests, 12 subprocess subtests; readiness exit 0 |
| W3: records and publication | In Progress | Explicit paths, gate and credential scan before each commit/push |
| W4: fresh native preparation | Ready | Requires committed source and clean inventory |
| W5: exactly one launch and terminal analysis | Ready | Requires W1-W4 pass; no retry or overtime |

Credential rotation was reported complete by the owner and the Codex keys
authenticated with exit 0. Historical captures remain unchanged.
