---
name: backend-api-spec
description: This skill should be used when the user asks to "write a backend-api spec", "audit the conventions or data-models spec", or "spec this endpoint" (the mf-dx-cc docs/backend-api-spec package) — author or audit a spec file with authority-gap validation, structural self-correction, and a PM-review pass.
user-invocable: true
argument-hint: "<spec file under docs/backend-api-spec/, or the entity/topic to spec>"
---

# Backend API Spec

Use to write or audit a file in `mf-dx-cc`'s `docs/backend-api-spec/` (the numbered 15-file spec, `00-conventions.md` … `14-migration-engine.md`). Encodes the repo's spec conventions so the cycle takes 1–2 passes instead of three sessions. (The mf-dx-cc conventions are also recorded in the memory store.)

## Conventions (binding)
- The **REST CRUD surface is the load-bearing, tech-agnostic contract**; the sync-envelope layer sits on top. Only **envelope shapes + error codes are normative** — curl example payloads (IDs like `P-001`, sample UUIDs, messages) are **illustrative**.
- Flag every dev-surprising rule with `> **ASSUMPTION:**` so the critic can audit it.
- Every contract rule must map to a **Tier-1 authority** (locked-decisions table / plan §). If a rule has no authority, that's a gap — escalate, don't invent.
- `ProcurementStatus` (and similar) is **metadata only** — must not drive mode-dependent behavior.

## 1. Plan
- If specing a new area, run `/geeky-plan` first (or read the existing plan). Identify the entity, its CRUD surface, FKs, enums, and which plan sections are the authority.

## 2. Draft the spec file
- Follow the existing file's structure and the numbered-file conventions. Include: overview, data model (fields + `semanticType` metadata), endpoints (method/path/auth), request/response envelope shapes, error codes (inline duplicate codes per status row for readability), and idempotency behavior as **three-block sequences** (request → replay → missing-key failure) where relevant.

## 3. Self-correct (structural audit)
- Remove structurally impossible cases (e.g. drop `409 DUPLICATE_ID` when `id` is a server-assigned UUIDv7 — it's unreachable).
- Ensure estimates respect any AC caps; kill stale forward-references.

## 4. Authority-gap validation
- For each contract rule, confirm a Tier-1 source. List unmapped rules as `> **ASSUMPTION:**` callouts or escalate to the user.

## 5. PM review pass
- Spawn a read-only reviewer (or use the `parallel-audit` skill with a spec-validation + data-model lens) to catch estimate/AC violations, authority leaks, and stale refs. Apply patches; re-audit (expect up to ~3 rounds for foundational files like `02-data-models.md`, whose cost-of-error is ~10× others).

## 6. Update handoff
- Per the repo's two-edit discipline: bump `handoff.md`'s "Last updated" header AND append a chronological entry; surface any dev-surprising assumptions in that log, not just spec headers.

## Notes
For pure runtime contract testing (inventory + exercise endpoints), use the `api-contract-check` skill. This skill is about the spec documents. Depends on the geeky-orchestration plugin (`/geeky-plan`) and the `parallel-audit` / `api-contract-check` skills.
