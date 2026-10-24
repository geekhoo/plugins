"""Run-3 operator annotations from exact frozen records; no harness changes."""
import hashlib,json,subprocess
from pathlib import Path
OP=Path(__file__).resolve().parent
run=Path(json.loads((OP/'run-paths.json').read_text())['run_folder'])
audit=json.loads((run/'model-audit.json').read_text());dispatch=json.loads((OP/'thread-dispatch-index.json').read_text())
paths={r['thread_id']:r['source'] for r in audit['records']}
rows={name:[json.loads(x) for x in (run/name).read_text().splitlines() if x.strip()] for name in paths.values()}
root=json.loads((run/'run.json').read_text(encoding='utf-8-sig'))['session_id']
orch='01a16aff-374e-7831-ab5f-3a8210ec6913';O=paths[orch]
def ref(path,index,text):
 row=rows[path][index]
 return {'path':path,'record_index':index,'timestamp':row['timestamp'],'record_sha256':hashlib.sha256(json.dumps(row,sort_keys=True,separators=(',', ':'),ensure_ascii=False).encode()).hexdigest(),'source_text':text}
def command_ref(index):
 row=rows[O][index];return ref(O,index,row['payload']['item']['id'])
def task_reference(sid,task):
 for index,row in enumerate(rows[paths[sid]]):
  item=row.get('payload',{}).get('item',{});cmd=item.get('command','');cmd=cmd[-1] if isinstance(cmd,list) else cmd;cmd=cmd.replace(chr(92),'/')
  if item.get('type')=='CommandExecution' and item.get('status')=='completed' and item.get('exit_code')==0 and 'Get-Content' in cmd and ('tasks/'+task+'-' in cmd or 'tasks\\'+task+'-' in cmd):
   return [ref(paths[sid],index,task+'-')]
 notes=[];product=[]
 for index,row in enumerate(rows[paths[sid]]):
  item=row.get('payload',{}).get('item',{});changes=item.get('changes',{})
  if item.get('type')!='FileChange' or item.get('status')!='completed' or not isinstance(changes,dict):continue
  for path,change in changes.items():
   if change.get('type') in ('delete','remove'):continue
   normalized=path.replace(chr(92),'/')
   if '/tasks/'+task+'-' in normalized and normalized.endswith('.notes.md'):notes.append(ref(paths[sid],index,task+'-'))
   elif normalized.endswith('.py') and '/docs/' not in normalized:product.append(ref(paths[sid],index,normalized))
 if notes and product:return [notes[0],product[0]]
 raise ValueError('Missing own task identity and product evidence: '+task)
data={'schema':'geeky-eval.process-evidence/1','origin':'operator-reviewed','sources':{name:hashlib.sha256((run/name).read_bytes()).hexdigest() for name in rows},'contexts':[],'stage_intervals':[],'reviews':[],'lane_moves':[],'handoff_calls':[],'critical_findings':[],'implementation_commits':{},'expected_implementation_commits':[],'missing':[],'notes':['The automatic extractor does not support one general orchestrator spanning all workflow stages. These annotations use the existing reviewed schema and frozen raw records.','Stage boundaries use dispatch timestamps of the first substantive planning artifact command, the plan-alignment dispatch, the first successful implementation-start lane command, and the final-review preparation command; early skill prereads are excluded.','Repeated T3 Ready/In Progress attempts and the corrected board update are preserved. Reused coder lifetime retains idle time; no duration normalization is applied.']}
by_name={r['dispatches'][0]['task_name']:r for r in dispatch}
for name,entry in by_name.items():
 d=entry['dispatches'][0];parent=next(r['thread_id'] for r in audit['records'] if r['source']==entry['parent_source']);cid=parent+':'+d['call_id'];proof=ref(entry['parent_source'],d['index'],d['call_id'])
 if name=='orchestrator':
  data['contexts'].append({'call_id':cid,'role':'orchestrator','refs':[proof]});scope=cid;continue
 if name.endswith('_research'):stage,role='spec-research',None
 elif name=='planning_pm':stage,role='geeky-plan','reviewer'
 elif name in ('plan_alignment','plan_sequence'):stage,role='plan-review','reviewer'
 elif name.startswith('final_'):stage,role='impl-review','reviewer'
 elif name.startswith('coder_'):stage,role='geeky-implement','coder'
 else:stage,role='geeky-implement','reviewer'
 context={'call_id':cid,'stage':stage,'refs':[proof]}
 if role:context['role']=role
 if name.startswith('coder_'):
  task=name[-2:].upper();context.update(tasks=[task],phase='P1' if task=='T1' else 'P2');context['refs'].extend(task_reference(entry['thread'],task))
 if name in ('phase1_review','phase2_review'):
  tasks=['T1'] if name=='phase1_review' else ['T2','T3'];phase='P1' if name=='phase1_review' else 'P2';last=entry['completions'][-1];result=ref(entry['source'],last['index'],'READY TO ADVANCE');context.update(tasks=tasks,phase=phase);context['refs'].append(result)
  data['reviews'].append({'call_id':cid,'tasks':tasks,'phase':phase,'verdict':'pass','ready':True,'result_ref':result,'refs':[proof,result]})
 data['contexts'].append(context)
first=next((index for index,row in enumerate(rows['session.jsonl']) if row.get('type')=='response_item' and row.get('payload',{}).get('type')=='message' and row['payload'].get('role')=='assistant'),None)
start=ref('session.jsonl',first,'requested workflows')
align=by_name['plan_alignment']['dispatches'][0];alignment=ref(O,align['index'],align['call_id'])
endrow=next((i for i,row in reversed(list(enumerate(rows['session.jsonl']))) if row.get('payload',{}).get('type')=='task_complete'),None)
end=ref('session.jsonl',endrow,'Implemented and accepted')
bounds=[('spec-research',start),('geeky-plan',ref(O,121,rows[O][121]['payload']['call_id'])),('plan-review',alignment),('geeky-implement',ref(O,230,rows[O][230]['payload']['call_id'])),('impl-review',ref(O,549,rows[O][549]['payload']['call_id']))]
for (stage,a),(_,b) in zip(bounds,bounds[1:]+[('end',end)]):
 for sc in (None,scope):data['stage_intervals'].append({'stage':stage,'scope_call_id':sc,'start':a,'end':b})
for index,task,lane in [(123,'T1','Ready'),(232,'T1','In Progress'),(293,'T1','In Review'),(333,'T1','Done'),(338,'T2','Ready'),(343,'T2','In Progress'),(393,'T2','In Review'),(400,'T3','Ready'),(400,'T3','In Progress'),(407,'T3','In Progress'),(491,'T3','In Review'),(526,'T2','Done'),(526,'T3','Done')]:
 data['lane_moves'].append({'call_id':orch+':'+rows[O][index]['payload']['item']['id'],'task':task,'lane':lane,'refs':[command_ref(index)]})
for index,tasks in [(333,['T1']),(526,['T2','T3'])]:data['handoff_calls'].append({'call_id':orch+':'+rows[O][index]['payload']['item']['id'],'tasks':tasks,'refs':[command_ref(index)]})
workspace=json.loads((OP/'validation-clone.json').read_text(encoding='utf-8-sig'))['workspace']
for task,prefix,index in [('T1','8691b4a',338),('T2','0c14247',535),('T3','5e1aa0d',535),('', '7f010e2',684)]:
 sha=subprocess.check_output(['git','-C',workspace,'rev-parse',prefix],text=True).strip();entry={'sha':sha,'refs':[ref(O,index,prefix)]}
 if task:data['implementation_commits'][task]=entry
 if task:data['expected_implementation_commits'].append(entry)
 else:data.setdefault('final_review_fix_commits',[]).append(entry)
e=by_name['final_inputs'];d=e['dispatches'][0];cid=orch+':'+d['call_id'];result=ref(e['source'],e['completions'][0]['index'],'NEEDS FIXES')
data['critical_findings'].append({'call_id':cid,'refs':[ref(O,d['index'],d['call_id']),result]})
out=run/'process-reviewed.json';out.write_text(json.dumps(data,indent=2),encoding='utf-8');print(json.dumps({'output':str(out),'contexts':len(data['contexts']),'stage_intervals':len(data['stage_intervals']),'lane_moves':len(data['lane_moves']),'commit_checks':len(data['expected_implementation_commits'])}))
