"""Read-only contestant monitoring; writes only operator snapshots."""
import datetime as dt,json,subprocess,time
from pathlib import Path
OP=Path(__file__).resolve().parent
paths=json.loads((OP/'run-paths.json').read_text(encoding='utf-8'))
run=Path(paths['run_folder']); workspace=Path(paths['workspace'])
now=dt.datetime.now(dt.timezone.utc)
state={'observed_utc':now.isoformat(),'files':{},'recent_items':[]}
for name in ('stream.jsonl','stderr.txt','run.json','oracle-output.txt','diagnostic-report.json'):
 p=run/name
 if p.exists():
  st=p.stat();state['files'][name]={'bytes':st.st_size,'modified_utc':dt.datetime.fromtimestamp(st.st_mtime,dt.timezone.utc).isoformat(),'age_s':round(time.time()-st.st_mtime,1)}
stream=run/'stream.jsonl'
if stream.exists():
 with stream.open('rb') as f:
  size=f.seek(0,2);f.seek(max(0,size-131072));data=f.read().decode('utf-8',errors='replace')
 lines=data.splitlines()
 if size>131072:lines=lines[1:]
 for line in lines:
  try:row=json.loads(line)
  except json.JSONDecodeError:continue
  item=row.get('item',{})
  if row.get('type')=='thread.started':state['session_id']=row.get('thread_id')
  if row.get('type') in ('turn.completed','turn.failed','error'):state['terminal_event']=row
  if item:
   brief={k:item[k] for k in ('id','type','status','exit_code') if k in item}
   for k in ('command','text','name'):
    if k in item:brief[k]=str(item[k])[:650]
   state['recent_items'].append(brief)
 state['recent_items']=state['recent_items'][-5:]
if (run/'run.json').exists():
 r=json.loads((run/'run.json').read_text(encoding='utf-8-sig'))
 state['runner_record']={k:r.get(k) for k in ('exit_reason','started_utc','ended_utc','wall_time_s','session_id','is_error','oracle')}
for args,label in [(['git','--no-optional-locks','-C',str(workspace),'log','-1','--format=%h %s'],'workspace_head'),(['git','--no-optional-locks','-C',str(workspace),'status','--short'],'workspace_status')]:
 result=subprocess.run(args,capture_output=True,text=True,timeout=15)
 state[label]=result.stdout.strip()[:1400]
board=workspace/'docs/spec-001-feature/kanban.md'
if board.exists():state['kanban_tail']='\n'.join(board.read_text(encoding='utf-8',errors='replace').splitlines()[-25:])[:2200]
(OP/'monitor.jsonl').open('a',encoding='utf-8').write(json.dumps(state)+'\n')
print(json.dumps(state,indent=2))
