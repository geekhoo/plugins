// Source-bound actor identity; prompts and descriptions never establish roles.
import { createHash } from 'node:crypto';

export function slug(value, fallback = 'unknown') {
  return String(value ?? '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || fallback;
}

export function bounded(value, limit = 190) {
  value = String(value);
  return value.length <= limit ? value : `${value.slice(0, limit - 17)}-${createHash('sha256').update(value).digest('hex').slice(0, 16)}`;
}

export function roleFor(type, root) {
  if (root) return 'orchestrator';
  const role = String(type ?? '').split(':').at(-1);
  if (['geeky-orchestrator', 'geeky-implement-orchestrator'].includes(role)) return 'orchestrator';
  if (role === 'geeky-coder') return 'coder';
  if (['code-reviewer', 'code-architect-reviewer', 'architect-reviewer', 'reviewer', 'plan-reviewer', 'impl-reviewer'].includes(role)) return 'reviewer';
  return 'unknown';
}

export function agentIdentity(meta, ctx, env = process.env) {
  const family = env.GEEKY_AGENT_FAMILY || 'codex-mxc-unknown';
  const root = !meta.isSubagentThread && !ctx.parentObservation;
  const role = roleFor(meta.agentRole, root);
  const name = meta.agentNickname || meta.agentRole || (root ? 'orchestrator' : 'unknown');
  const id = meta.sessionId || 'unknown';
  const traceName = bounded(`${family}-${role}${slug(name) === role ? '' : `-${slug(name)}`}`);
  const userId = bounded(`${family}-${role}${slug(name) === role ? '' : `-${slug(name)}`}-${slug(id)}`);
  // A seeded trace's placeholder parent is not a real dispatch relationship.
  const parent = ctx.parentObservation?.otelSpan.spanContext() || (ctx.attached ? ctx.parentSpanContext : undefined);
  const runMetadata = JSON.parse(env.GEEKY_RUN_METADATA || '{}');
  if (!runMetadata || typeof runMetadata !== 'object' || Array.isArray(runMetadata)) throw Error('GEEKY_RUN_METADATA must be an object');
  const metadata = {
    ...Object.fromEntries(Object.entries(runMetadata).filter(([, v]) => v != null).map(([k, v]) => [k, bounded(v)])),
    identity_schema: 'geeky-eval.agent-identity/1', agent_family: family,
    agent_id: bounded(id), agent_role: role, agent_type: meta.agentRole || (root ? 'orchestrator' : 'unknown'),
    agent_name: bounded(name), agent_user_id: userId, actor_scope: root ? 'main' : 'subagent',
    native_session_id: bounded(id),
    ...(meta.parentThreadId ? { parent_agent_id: bounded(meta.parentThreadId) } : {}),
    ...(meta.agentPath ? { agent_path: bounded(meta.agentPath) } : {}),
    ...(parent ? { parent_trace_id: parent.traceId, parent_observation_id: parent.spanId } : {})
  };
  return {
    sessionId: env.GEEKY_SESSION_ID || id, userId, traceName, metadata,
    tags: [...(ctx.config.tags || []), `agent-role:${role}`, `agent-type:${slug(meta.agentRole || role)}`]
  };
}
