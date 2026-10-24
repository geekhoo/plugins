"""Audit frozen run-local own-history model contexts without inference calls."""
import hashlib,json,sys
from pathlib import Path
run=Path(sys.argv[1]);out=Path(sys.argv[2])
record=json.loads((run/'run.json').read_text(encoding='utf-8-sig'))
assert record.get('session_id'), 'Runner completion record required before final model audit'
paths=[run/'session.jsonl']+sorted((run/'subagents').glob('*.jsonl'))
results=[];errors=[]
for path in paths:
 rows=[]
 for line in path.read_text(encoding='utf-8').splitlines():
  if line.strip():rows.append(json.loads(line))
 meta=next((r.get('payload',{}) for r in rows if r.get('type')=='session_meta'),{})
 sid=meta.get('id') or meta.get('session_id')
 source=meta.get('source');spawn=(source.get('subagent',{}).get('thread_spawn',{}) if isinstance(source,dict) else {})
 parent=meta.get('parent_thread_id') or spawn.get('parent_thread_id')
 role=meta.get('agent_role') or spawn.get('agent_role') or 'general-purpose'
 cutoff=meta.get('subagent_history_start_ordinal') if parent or spawn else None
 if parent and cutoff is None and sum(r.get('type')=='session_meta' for r in rows)>1:errors.append('Missing inherited-history boundary: '+str(sid))
 own=[r for r in rows if cutoff is None or isinstance(r.get('ordinal'),int) and r['ordinal']>=cutoff]
 effort='high' if sid==record['session_id'] else 'xhigh' if role.split(':')[-1] in ('code-reviewer','code-architect-reviewer') else 'medium'
 contexts=[]
 for number,row in enumerate(rows,1):
  if row.get('type')!='turn_context' or row not in own:continue
  payload=row.get('payload',{});contexts.append({'physical_line':number,'ordinal':row.get('ordinal'),'timestamp':row.get('timestamp'),'model':payload.get('model'),'effort':payload.get('effort',payload.get('reasoning_effort'))})
 passed=bool(contexts) and all(c['model']=='gpt-6.1-sol' and c['effort']==effort for c in contexts)
 results.append({'thread_id':sid,'parent_thread_id':parent,'role':role,'agent_path':meta.get('agent_path') or spawn.get('agent_path'),'own_history_start_ordinal':cutoff,'expected_model':'gpt-6.1-sol','expected_effort':effort,'source':path.relative_to(run).as_posix(),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'contexts':contexts,'passed':passed})
ids={r['thread_id'] for r in results}
for row in results:
 if row['parent_thread_id'] and row['parent_thread_id'] not in ids:errors.append('Missing parent: '+row['thread_id'])
report={'ok':bool(results) and not errors and all(r['passed'] for r in results),'threads':len(results),'own_contexts':sum(len(r['contexts']) for r in results),'errors':errors,'records':results,'scope':'Actual own-history contexts checked by registered role. Review assignment purposes must also be checked against physical dispatch/verdict evidence.'}
out.write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:report[k] for k in ('ok','threads','own_contexts','errors')},indent=2))
raise SystemExit(0 if report['ok'] else 1)
