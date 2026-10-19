# C2 — linkvault: Reference Spec

| Field | Value |
|---|---|
| id | `c2-linkvault` |
| tier | C2 |
| budget ceiling | $25 |
| expected size | 8-12 tasks, 3 implementation phases |
| stack | Python >=3.11, stdlib only (`http.server`, `sqlite3`, `json`, `argparse`, `urllib`, `secrets`, `hashlib`, `threading`, `signal`); pytest for tests only |
| package location | `linkvault/` at the workspace root (`linkvault/__init__.py`, `linkvault/__main__.py`); commands run with the workspace root as cwd |
| entry points | `python -m linkvault serve ...` (server); `python -m linkvault <client-cmd> ...` (client) |

## Contestant brief

Build `linkvault`, a small URL-shortener HTTP JSON API with a command-line client, in the `linkvault/` package at the root of this workspace. Use only the Python 3.11+ standard library: `http.server` for the server and `sqlite3` for storage; pytest is allowed for your own tests. An admin key issues bearer tokens, and each token can create, list, inspect and delete only its own short links. Short links redirect with HTTP 302, can carry an optional custom slug and expiry, and count their clicks. Each token is rate-limited, and all data except rate-limit counters survives a server restart. The server binds 127.0.0.1 only, prints one ready line, supports a fake clock for testing, and shuts down cleanly on Ctrl+C on Windows, macOS and Linux. Follow `contract.md` exactly, because an automated test suite checks status codes, JSON keys and key order, headers, output and exit codes. Keep the code minimal and readable, and include tests for the behaviour you build.

## Scope

The `serve` HTTP server (SQLite persistence, token auth, per-token rate limit, expiry, click stats, fake clock, clean shutdown) and a CLI client for it.

## Out of scope

HTTPS, non-loopback binding, token revocation, link editing, analytics beyond clicks and last click, HTML, HEAD/OPTIONS, chunked bodies, URL reachability checks, outbound network, third-party packages.

## Functional requirements

- **R1 Server start.** `serve` opens or creates the DB, binds 127.0.0.1, then prints exactly one ready line to stdout. Nothing else is ever written to stdout; logs go to stderr.
- **R2 Token issuance.** `POST /v1/tokens` with the correct admin key returns a new token. The token is `lv_` followed by 32 lowercase hex characters (`secrets.token_hex(16)`). Only its SHA-256 hex digest is stored.
- **R3 Authentication.** Every `/v1/links` route requires `Authorization: Bearer <token>`. A missing, malformed or unknown token returns 401.
- **R4 Create link.** `POST /v1/links` stores `url` with a custom `slug` or a generated slug, and an optional `expires_in`.
- **R5 Slug rules.** Slugs are case-sensitive. A custom slug must match `^[A-Za-z0-9_-]{3,32}$` and must not be `healthz`. A generated slug is 7 characters from `abcdefghijklmnopqrstuvwxyz0123456789`, drawn with `secrets.choice`. It is regenerated if it already exists or is reserved, with up to 5 attempts and then 500. Creating an existing slug returns 409.
- **R6 URL rules.** The scheme is `http` or `https` (case-insensitive). `urllib.parse.urlsplit(url).hostname` is non-empty. The URL is at most 2048 characters and contains no whitespace or control characters (code points < 0x21 or 0x7F). It is stored and redirected to verbatim.
- **R7 Resolve.** `GET /<slug>` returns 302 with `Location: <url>` and an empty body. It atomically increments `clicks` and sets `last_clicked_at` to now.
- **R8 Missing and expired links.** An unknown slug returns 404. A link with `now >= expires_at` returns 410 and its click count is unchanged. Comparisons use whole seconds.
- **R9 List and inspect.** A token can list its own links (expired ones included) and fetch one link with its stats. Another token's link always returns 404, never 403.
- **R10 Delete.** A token can delete its own link. Afterwards the slug resolves 404 and is free to reuse.
- **R11 Rate limit.** Requests are counted per token in fixed 60-second windows aligned to the Unix epoch (`window_start = now - now % 60`). The limit is `--rate-limit` (default 60) counted requests per window. A request is counted when it reaches the rate-limit step (see precedence in Error handling), whatever its final status. Request number `limit + 1` and later in the same window return 429 with `Retry-After: <window_start + 60 - now>`. Counters are in memory and reset on restart. Redirects, `/healthz` and admin routes are not rate-limited.
- **R12 Clock.** "Now" is integer Unix seconds (floor of real time). With `--fake-clock <ISO>`, now is frozen at that instant and changes only through `POST /v1/admin/clock`. The fake clock is not persisted.
- **R13 Persistence.** Tokens, links, clicks and `last_clicked_at` survive a restart on the same `--db`.
- **R14 Concurrency.** The server is a `ThreadingHTTPServer`. N concurrent redirects to one slug leave `clicks == N` exactly.
- **R15 Shutdown.** On SIGINT, SIGTERM (POSIX) or CTRL_BREAK_EVENT/SIGBREAK (Windows), the server stops accepting connections, closes the DB and exits 0 within 5 seconds.
- **R16 Client.** CLI commands wrap the API. Each prints the response body to stdout, and uses the exit codes below.

## Interface contract

### Conventions

- Timestamps are `YYYY-MM-DDTHH:MM:SSZ` in UTC with whole seconds. They are stored as INTEGER Unix seconds.
- JSON responses are encoded with `json.dumps(obj, separators=(",", ":"), ensure_ascii=True)` in UTF-8, with `Content-Type: application/json`. Every response sets `Content-Length`; a 204 response has an empty body and MUST send `Content-Length: 0`. Keys appear in exactly the order listed below.
- Request `Content-Type` is ignored. The body is read using `Content-Length` (absent means empty), and the maximum is 8192 bytes.
- Query strings are ignored on every route. Paths are matched exactly, with no trailing-slash normalisation. Any (method, path) pair not listed below returns 404 `not_found`.
- `short_url` is `http://127.0.0.1:<bound port>/<slug>`.

**Link object** (key order is fixed): `{"slug", "url", "short_url", "created_at", "expires_at", "clicks", "last_clicked_at"}`. `expires_at` and `last_clicked_at` are `null` until they are set.

### Server CLI

```
python -m linkvault serve --db PATH --admin-key KEY [--port N] [--rate-limit N] [--fake-clock ISO]
```

| Flag | Rule |
|---|---|
| `--db` | Required. The file is created if missing, and its parent directory must exist. |
| `--admin-key` | Required. Non-empty string. |
| `--port` | 0-65535, default 8000. The value 0 binds an OS-chosen free port. |
| `--rate-limit` | Integer >= 1, default 60. |
| `--fake-clock` | An ISO timestamp in the format above. It enables the admin clock route. |

Ready line: `LISTENING http://127.0.0.1:<port>` followed by a line terminator, which may be `\n` or `\r\n`. It uses the actual bound port, is flushed immediately, and nothing else is written to stdout before it.

Exit codes: 0 for a clean shutdown; 2 for a usage error (argparse); 3 if the port cannot be bound or the DB cannot be opened, with a message to stderr.

### Endpoints

| # | Method and path | Auth | Request body | Success response |
|---|---|---|---|---|
| E1 | `GET /healthz` | none | none | 200 `{"status":"ok"}` |
| E2 | `POST /v1/tokens` | `X-Admin-Key: <key>` | ignored | 201 `{"token":"lv_…","created_at":"…"}` |
| E3 | `POST /v1/links` | Bearer | `{"url": str, "slug"?: str, "expires_in"?: int}` | 201, link object |
| E4 | `GET /v1/links` | Bearer | none | 200 `{"links":[link…]}` ordered by `created_at` ascending, then `slug` ascending |
| E5 | `GET /v1/links/<slug>` | Bearer | none | 200, link object |
| E6 | `DELETE /v1/links/<slug>` | Bearer | none | 204, empty body |
| E7 | `GET /<slug>` | none | none | 302, `Location: <url>`, `Content-Length: 0`, empty body |
| E8 | `POST /v1/admin/clock` | `X-Admin-Key` | `{"now": ISO}` | 200 `{"now":"…"}`. The route exists only with `--fake-clock`; otherwise it returns 404. Any valid timestamp is accepted. |

E3 body rules:
- The body is a JSON object with no extra keys.
- `url` is required and must follow R6.
- `slug` is optional and must follow R5. An explicit `null` is `invalid_request` (400).
- `expires_in` is optional. It is an integer from 1 to 31536000, and `bool` values are rejected. An explicit `null` is `invalid_request` (400). It sets `expires_at = created_at + expires_in`.

E8 body rules:
- The body must be exactly `{"now": ISO}`, where ISO is a string in the timestamp format above.
- A missing `now` key, an extra key, a wrong type or an unparseable timestamp returns 400 `invalid_request`.

A wrong or missing admin key on E2 or E8 returns 401. On E5, E6 and E7, a `<slug>` that fails `^[A-Za-z0-9_-]{3,32}$` is a route mismatch, so it returns 404 at the route step, before auth.

### DB schema (exact)

```sql
PRAGMA user_version = 1;
CREATE TABLE IF NOT EXISTS tokens (
  token_hash TEXT PRIMARY KEY,
  created_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS links (
  slug TEXT PRIMARY KEY,
  url TEXT NOT NULL,
  token_hash TEXT NOT NULL REFERENCES tokens(token_hash),
  created_at INTEGER NOT NULL,
  expires_at INTEGER,
  clicks INTEGER NOT NULL DEFAULT 0,
  last_clicked_at INTEGER);
```

A click is recorded with one statement: `UPDATE links SET clicks = clicks + 1, last_clicked_at = ? WHERE slug = ?`.

### Client CLI

The server URL comes from `--server URL`, or else the `LINKVAULT_SERVER` environment variable. The token comes from `--token T`, or else `LINKVAULT_TOKEN`. Both options are accepted after the subcommand.

| Command | Calls | Stdout on success |
|---|---|---|
| `token create --admin-key K` | E2 | Response JSON, one line |
| `shorten URL [--slug S] [--expires-in N]` | E3 | Response JSON, one line |
| `list` | E4 | Response JSON, one line |
| `stats SLUG` | E5 | Response JSON, one line |
| `delete SLUG` | E6 | Nothing |

Output is re-serialised with the server's `json.dumps` settings and ends with `\n`. Client exit codes:

| Code | Meaning | Output |
|---|---|---|
| 0 | 2xx response | as above |
| 1 | non-2xx response | Error JSON on stderr, stdout empty |
| 2 | usage error, or a missing server or token | Message on stderr |
| 3 | connection failure | Message on stderr |

## Error handling

Every error body has this shape: `{"error":{"code":"<code>","message":"<text>"}}`. Tests assert `code` only.

| Condition | Status | code |
|---|---|---|
| No route matches the method and path; unknown or foreign slug | 404 | `not_found` |
| Missing, malformed or unknown bearer token; bad admin key | 401 | `unauthorized` |
| Over the rate limit (adds a `Retry-After` header) | 429 | `rate_limited` |
| `Content-Length` > 8192 (the response sets `Connection: close` and the body is not read) | 413 | `payload_too_large` |
| Body is not valid UTF-8 JSON, or is not an object | 400 | `invalid_json` |
| Schema violation: missing or extra key, wrong type, bad URL, slug, `expires_in` or `now` | 400 | `invalid_request` |
| Slug already exists, or is reserved (`healthz`) | 409 | `slug_taken` |
| Link expired (E7 only) | 410 | `gone` |
| Unhandled exception | 500 | `internal` |

Precedence (first failure wins): route 404 → auth 401 → rate limit 429 → size 413 → JSON 400 → validation 400 → resource state 404/409/410.

## Acceptance criteria

- **AC1 (R1, R15):** `serve --port 0` prints exactly the `LISTENING` line. `GET /healthz` returns 200. SIGINT (or CTRL_BREAK_EVENT on Windows) makes it exit 0 within 5 s.
- **AC2 (R2):** E2 with the right key returns 201 and a token matching `^lv_[0-9a-f]{32}$`. With a wrong key it returns 401. The DB holds the SHA-256 of the token, never the plaintext.
- **AC3 (R3):** E3, E4 and E5 without a valid bearer token return 401 `unauthorized`.
- **AC4 (R4, R5):** E3 without `slug` returns a slug matching `^[a-z0-9]{7}$`. A custom `slug` is echoed back. A repeated slug returns 409. `healthz` and `ab` return 409 and 400 respectively.
- **AC5 (R6):** `ftp://x`, `javascript:alert(1)`, `http://`, a URL with a space, and a 2049-character URL each return 400 `invalid_request`.
- **AC6 (R7):** `GET /<slug>` returns 302 with the exact `Location`. A later E5 shows `clicks` 1 and `last_clicked_at` set to now.
- **AC7 (R8, R12):** With the fake clock at T and `expires_in=60`, the link resolves 302 at T+59 and 410 at T+60. Its clicks stay at the T+59 value.
- **AC8 (R9, R10):** Token B gets 404 on E5 and E6 for token A's slug. A's E4 lists only A's links in order. After E6, `GET /<slug>` returns 404 and the slug can be created again.
- **AC9 (R11):** With `--rate-limit 3` and the fake clock at a window start plus 10 s, requests 1-3 succeed. Request 4 returns 429 with `Retry-After: 50`. After the clock moves to the next window, the next request succeeds. Redirects are never limited.
- **AC10 (R13):** After a restart on the same DB, tokens still authenticate, and links and clicks are unchanged.
- **AC11 (R14):** 50 concurrent `GET /<slug>` requests leave `clicks == 50`.
- **AC12 (R16):** `shorten` prints the link JSON and exits 0. A 409 makes it exit 1 with empty stdout. An unreachable server makes it exit 3. A missing token makes it exit 2.

## Hidden oracle outline

Categories: lifecycle, auth, CRUD and ownership, redirect and expiry, rate limiting, validation, persistence, concurrency, CLI. Each test starts a server with `--port 0`, a temporary `--db` and usually `--fake-clock 2030-01-01T00:00:00Z`; uses `urllib` with redirects disabled; checks key order with `list(obj)`. On Windows it uses `CREATE_NEW_PROCESS_GROUP` and `CTRL_BREAK_EVENT`.

Example cases:
1. Slug collision: two tokens create `promo`. The second gets 409 `slug_taken`, and the first token's link is unchanged.
2. Invalid schemes: `FTP://h`, `mailto:a@b`, `javascript:x` and `file:///etc/passwd` all return 400. `HTTPS://Example.com` returns 201 and is stored verbatim.
3. Expiry boundary: the request at `now == expires_at` returns 410 and the request one second earlier returns 302. E5 on the expired link still returns 200.
4. Rate-limit boundary: with `--rate-limit 2`, a 400 request counts toward the limit, while 401 and 429 responses do not. At `now = window_start + 59` the 429 carries `Retry-After: 1`.
5. Concurrent clicks: 50 threads each send one redirect, and `clicks` ends at exactly 50.
6. Restart persistence: create a link, click it twice, SIGINT the server, restart it on the same DB, and E5 shows clicks 2 and the same `created_at`.
7. Cross-token access: token B gets 404 on E5 and E6, and E4 omits A's links.
8. Malformed JSON: the bodies `{bad`, `[]`, `"x"` and `{"url":"http://a","extra":1}` return `invalid_json`, `invalid_json`, `invalid_json` and `invalid_request`.
9. Oversized body: `Content-Length: 8193` returns 413. A body of exactly 8192 bytes passes the size step.
10. `expires_in` types: `true`, `0`, `1.5`, `"60"` and `31536001` each return 400.
11. Routing: `HEAD /x`, `PUT /v1/links`, `/v1/links/` and E8 without `--fake-clock` each return 404.
12. CLI: `delete` exits 0 with empty stdout. `stats missing` exits 1 with `{"error":{"code":"not_found",…}}` on stderr.

## Suggested decomposition

Reference only.

- **Phase 1, foundation:** T1 package skeleton and argparse dispatch; T2 clock, ISO helpers, DB schema; T3 server bootstrap, ready line, routing, JSON and error helpers, signal shutdown, `/healthz`.
- **Phase 2, API:** T4 admin key, E2, bearer auth; T5 E3 with validation and slug generation; T6 E7 with clicks and expiry; T7 E4-E6 with ownership; T8 rate limiter, precedence, size and JSON guards, E8.
- **Phase 3, client and hardening:** T9 CLI client and exit codes; T10 persistence, concurrency, Windows-shutdown and boundary tests.

## Quality signals

- **Minimal code:** about 350-550 lines of non-test Python across 3-5 modules (for example, `server.py`, `store.py`, `client.py`, `__main__.py`). There are no classes or abstractions without a second use, no config files, and no dependencies outside the stdlib. One shared JSON and error helper serves every route.
- **No defects:** every AC passes on all three OSes; no lost clicks or "database is locked" errors (one lock-guarded connection); parameterised SQL only; no plaintext tokens in DB or logs; never binds `0.0.0.0`; shutdown never hangs; tracebacks surface only as 500 `internal`.
