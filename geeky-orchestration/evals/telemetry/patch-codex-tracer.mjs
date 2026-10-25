// Fail closed on upstream drift; the pinned original remains byte-for-byte intact.
import { readFileSync, writeFileSync, copyFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

export function patch(source) {
  source = source.replace(/\r\n/g, '\n');
  const replace = (before, after) => {
    if (source.split(before).length !== 2) throw Error(`Codex tracer drift at ${before.slice(0, 90)}`);
    source = source.replace(before, after);
  };
  replace('const p = line.payload;\n\treturn {\n\t\tsessionId:',
    'const p = line.payload;\n\tconst spawned = p.source?.subagent?.thread_spawn || {};\n\treturn {\n\t\tagentRole: p.agent_role || spawned.agent_role,\n\t\tagentPath: p.agent_path || spawned.agent_path,\n\t\tagentNickname: p.agent_nickname || spawned.agent_nickname,\n\t\tsessionId:');
  replace('isSubagentThread: typeof p.parent_thread_id === "string" || p.thread_source === "subagent",\n\t\tparentThreadId: p.parent_thread_id ? p.parent_thread_id : void 0',
    'isSubagentThread: typeof (p.parent_thread_id || spawned.parent_thread_id) === "string" || p.thread_source === "subagent",\n\t\tparentThreadId: p.parent_thread_id || spawned.parent_thread_id || void 0');
  replace('parentThreadId: typeof p.parent_thread_id === "string" ? p.parent_thread_id : void 0,',
    'parentThreadId: p.parent_thread_id || p.source?.subagent?.thread_spawn?.parent_thread_id || void 0,');
  replace('async function emitTurn(turn, sessionMeta, ctx) {', `async function emitTurn(turn, sessionMeta, ctx) {
  if (!process.env.GEEKY_AGENT_FAMILY) return emitGeekyTurn(turn, sessionMeta, ctx);
  const identity = geekyAgentIdentity(sessionMeta, ctx);
  // Trace-level user/session attributes must never leak back into another agent.
  return context.with(ROOT_CONTEXT, () => propagateAttributes(identity, () => emitGeekyTurn(turn, sessionMeta, {
    ...ctx, parentObservation: undefined,
    parentSpanContext: ctx.parentObservation || ctx.attached ? undefined : ctx.parentSpanContext,
    attached: false, geekyIdentity: identity
  })));
}
async function emitGeekyTurn(turn, sessionMeta, ctx) {`);
  replace('const root = startObservation(isSubagent ? "Codex Subagent Turn" : "Codex Turn", {',
    'const root = startObservation(ctx.geekyIdentity?.traceName || (isSubagent ? "Codex Subagent Turn" : "Codex Turn"), {');
  replace('"codex.thread_id": sessionMeta.sessionId,',
    '"codex.thread_id": sessionMeta.sessionId,\n\t\t\t...ctx.geekyIdentity?.metadata,');
  return 'import { agentIdentity as geekyAgentIdentity } from "./codex-identity.mjs";\n' + source;
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const [input, output] = process.argv.slice(2);
  if (!input || !output) throw Error('Usage: patch-codex-tracer.mjs INPUT OUTPUT');
  const derived = patch(readFileSync(input, 'utf8'));
  copyFileSync(join(dirname(fileURLToPath(import.meta.url)), 'codex-identity.mjs'), join(dirname(output), 'codex-identity.mjs'));
  writeFileSync(output, derived, 'utf8');
}
