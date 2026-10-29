# Native encrypted-output failure: local compatibility fix

Implemented and verified offline. `-LitellmWireMode native` now uses an
explicit `codex-v2-native-plaintext` compatibility proxy. It retains native V2
namespaces, task identities, role/model settings, client session metadata and
reasoning envelopes. Collaboration message fields request plaintext, and added
and completed calls carry explicit `encrypted_function_args: []` metadata.
Only exact, validated completed-response plaintext can support tagged replay;
unknown opaque values remain rejected. The legacy mapping mode is unchanged.

Third-party profiles also set the catalog's `supports_search_tool` capability
false, expose MCP functions eagerly, and set request/stream retries to zero.
Feature flags alone did not eliminate deferred-search history; the native CLI
experiment established that the catalog capability was required. This removes
the SDK search-item path implicated in the Azure call_id/id substitution while
retaining direct MCP calls. No provider-side serialization behavior is assumed
fixed or externally tested.

## Evidence

| Check | Result |
|---|---|
| Integrated regression suite | 290 passed, 64 subtests passed, no skips |
| Readiness suite | 10 passed |
| Native proxy inside MXC | 23/23 in each of three configurations, 69/69 total |
| Native configurations | Cold workers with both reviewer roles; full-history forks |
| Upstream fixture request histories | Zero encrypted collaboration schemas, tagged encrypted handoffs or search items |
| Streaming coverage | Added item, argument deltas, argument completion and completed item |
| Full scripted C0 inside MXC | Five stages, 17 product tests, oracle 13/13 stable over 3 runs |
| Readiness inventory | inventory-ready; correctly reports uncommitted working source |
| Paid calls / provider probes / live telemetry | Zero |

The native tests run real codex.exe 0.164.0 against the production compatibility
server and a deterministic local Responses server inside denied-network MXC.
They verify tool execution, MCP, nested dispatch and role settings. The full C0
mock uses a scripted stand-in. Neither supplies live-model success or a parity
ranking. Host HTTP tests also verify authentication, bounded bodies, redirects,
opaque-response rejection and cleanup. Existing diagnostic rules were not weakened.

The saved paid trace has 38 genuinely opaque collaboration fragments with no
readable plaintext matches; all remain unchanged. Its 238 main-thread tool
outputs are ordinary strings, and the exact rejected outbound wire request was
not retained. The local fix prevents the problematic new handoff/search forms;
it does not decrypt the historical envelopes or identify every private upstream
transformation. The saved history and error support those boundaries explicitly.

The explicit metadata control experiment removed 9 false encrypted tags without
changing argument text and passed 21/21 native checks. The eager-catalog control
then passed 21/21 with zero search items. The combined production proxy tests
passed 69/69 on fresh prepared configurations and full SSE sequences.

Authoritative working source: C:\Users\gerald.khoo\geekhoo-plugins. Base HEAD:
`c2287f7e7978f72bdce1dfbee8717323d7d98857`. All remediation is uncommitted and
unpushed. Native fixtures used the recorded working-source overlay and regenerated
profiles; the runner still exports committed plugin HEAD. No old prepared launch
command is reusable. Live execution remains held under the owner's no-paid-run
instruction; live endpoint verification was not performed.

See verification.json, regression-tests.log, readiness-tests.log, kanban.md,
handoff.md and references.md. Local artifacts are under
outputs/c0-encrypted-output-fix-20261029/. Historical paid evidence and the prior
mock evidence hashes were verified unchanged.
