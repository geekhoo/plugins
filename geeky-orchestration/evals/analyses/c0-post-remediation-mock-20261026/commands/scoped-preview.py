import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys
root=Path(r'C:\Users\gerald.khoo\geekhoo-plugins')
out=root/'outputs/c0-remediation-mock-20261026'
runs={
 'claude':Path(r'C:\repos\c0-remediation-mock-20261026\full-harness\geeky-orchestration\evals\baselines\c0-wordstat\20261026T111333Z'),
 'codex':Path(r'C:\repos\c0-remediation-mock-20261026\full-harness-codex\geeky-orchestration\evals\baselines\c0-wordstat\20261026T111332Z-497b0ffe')}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
results=[]
for harness,run_dir in runs.items():
 d=out/('scoped-preview-'+harness);d.mkdir(exist_ok=True)
 run=json.loads((run_dir/'run.json').read_text(encoding='utf-8-sig'))
 evidence=Path(run['workspace'])/'.git/c0-full-summary.json'
 obs=d/'observations.json';obs.write_text('[]\n',encoding='utf-8')
 paths={'run':run_dir/'run.json','score':out/('scoring-fresh-'+harness)/'score.json','observations':obs,'scripted-evidence':evidence,'bundle':run_dir/'solution.bundle'}
 sid='mock-c0-'+harness+'-'+run_dir.name
 label={'scope_id':sid,'population':'fresh scripted mock process and disposable candidate','source_ids':['run','bundle'],'additive':False,'complete':True}
 metrics={k:{'population':'synthetic or unavailable; not provider billing evidence','source_ids':['run','scripted-evidence'],'complete':False} for k in ('tokens','calls','latency_idle','backend','cost')}
 metrics['coverage']={'population':'telemetry disabled; no observations','source_ids':['observations'],'complete':False}
 execution=run['execution'];deadline=dt.datetime.fromisoformat(execution['initial_deadline_utc'].replace('Z','+00:00'))
 scope={'schema':'geeky-eval.inputs/1','scope_id':sid,'kind':'initial','parent_scope_id':None,
 'configuration':{'prompt_sha256':run['prompt_sha256'],'plugin_sha':run['plugin_sha']},
 'sources':[{'id':key,'path':str(p),'sha256':sha(p),'ancestry':[]} for key,p in paths.items()],
 'segments':[{'segment_id':execution['segment_id'],'attempt_id':execution['attempt_id'],'authorization_reference':execution['authorization_reference'],'start':(deadline-dt.timedelta(seconds=execution['hard_wall_budget_s'])).isoformat(),'end':deadline.isoformat()}],
 'ownership':{'method':'source-reviewed','rule':'Parent observed one fresh scripted mock invocation; no history merge; scripted evidence is not an independent model review.','evidence_source':'scripted-evidence','assignments':[{'source_id':'run','logical_ids':[execution['segment_id']]}]},
 'metric_default':label,'metrics':metrics}
 scope_path=d/'evaluation-inputs.json';scope_path.write_text(json.dumps(scope,indent=2)+'\n',encoding='utf-8')
 cmd=[sys.executable,str(root/'geeky-orchestration/evals/scripts/parity-eval.py'),str(run_dir),'--observations',str(obs),'--score',str(paths['score']),'--scope',str(scope_path),'--out',str(d/'parity')]
 result=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8')
 (d/'parity.log').write_text(result.stdout+result.stderr,encoding='utf-8')
 row={'harness':harness,'scope':str(scope_path),'parity_command':cmd,'parity_exit':result.returncode,'telemetry_observations':0,'model_judges_called':0}
 if result.returncode==0:
  publisher=[sys.executable,str(root/'geeky-orchestration/evals/telemetry/langfuse-scores.py'),'--run',str(run_dir),'--parity',str(d/'parity/parity.json'),'--scope',str(scope_path),'--dry-run','--evaluator-version','mock-preview/1']
  previews=[]
  for name,args in [('first',publisher),('repeat',publisher),('other-version',publisher[:-1]+['mock-preview/2'])]:
   response=subprocess.run(args,capture_output=True,text=True,encoding='utf-8')
   (d/(name+'.json' if response.returncode==0 else name+'.log')).write_text(response.stdout+response.stderr,encoding='utf-8')
   row[name+'_exit']=response.returncode
   if response.returncode==0:previews.append(json.loads(response.stdout))
  if len(previews)==3:
   ids=[[s['id'] for s in p['expected']] for p in previews]
   assert ids[0]==ids[1] and set(ids[0]).isdisjoint(ids[2])
   assert all(p['status']=='preview' and p['scores_verified'] is False for p in previews)
   row.update(preview_ids=len(ids[0]),same_scope_idempotent=True,version_separated=True,scores_verified=False,http_requests=0)
  parity=json.loads((d/'parity/parity.json').read_text(encoding='utf-8'))
  row['unknown_efficiency']={key:parity['efficiency'].get(key) for key in ('tokens_total','calls','latency_median_ms','backend','cost')}
  assert all(v is None for v in row['unknown_efficiency'].values())
 else:row['limitation']='No parity/score success inferred from disabled observation coverage; exact diagnostic retained.'
 results.append(row)
(out/'scoped-preview-results.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
print(json.dumps(results,indent=2))