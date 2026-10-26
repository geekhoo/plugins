import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path(r'C:\Users\gerald.khoo\geekhoo-plugins')
BASE=ROOT/'geeky-orchestration/evals/baselines/c0-wordstat'
OUT=ROOT/'outputs/c0-remediation-mock-20261026'
REPORT=ROOT/'geeky-orchestration/evals/analyses/c0-post-remediation-mock-20261026'
REPORT.mkdir(exist_ok=True)
(REPORT/'.gitattributes').write_text('evidence/** -text\nsupport/** -text\nscoring/** -text\nscoped/** -text\ncommands/** -text\n',encoding='utf-8')
SPECS=[
('claude-original','unchanged-source control',BASE/'20261026T105443Z'),
('codex-original','unchanged-source control',BASE/'20261026T105717Z-b3b8245d'),
('claude-crash','expected negative',BASE/'20261026T110135Z'),
('claude-timeout','expected negative',BASE/'20261026T110149Z'),
('claude-refusal-zero','bounded recovery control',BASE/'20261026T110212Z'),
('claude-refusal-one','bounded recovery control',BASE/'20261026T110231Z'),
('codex-fail','expected negative',BASE/'20261026T110548Z-de605bce'),
('claude-timeout-injection-missed','additional timeout; operator setup miss',BASE/'20261026T110713Z'),
('claude-timeout-oracle-fault','verified postprocessing failure',BASE/'20261026T110917Z'),
('claude-c0-full','isolated scripted full fixture',Path(r'C:\repos\c0-remediation-mock-20261026\full-harness\geeky-orchestration\evals\baselines\c0-wordstat\20261026T111333Z')),
('codex-c0-full','isolated scripted full fixture',Path(r'C:\repos\c0-remediation-mock-20261026\full-harness-codex\geeky-orchestration\evals\baselines\c0-wordstat\20261026T111332Z-497b0ffe')),
('codex-timeout','isolated mock negative',Path(r'C:\repos\c0-remediation-mock-20261026\full-harness-codex\geeky-orchestration\evals\baselines\c0-wordstat\20261026T111622Z-c7eaa349'))]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def copy(source,destination):
 destination.parent.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(source,destination)
 assert sha(source)==sha(destination)
 return {'path':str(destination.relative_to(REPORT)).replace('\\','/'),'sha256':sha(destination),'bytes':destination.stat().st_size,'source':str(source)}
rows=[];files=[]
for label,kind,d in SPECS:
 r=read(d/'run.json');e=r['execution'];destination=REPORT/'evidence'/label
 checked=0
 for name,wanted in e.get('artifact_sha256',{}).items():
  p=d/name
  assert p.is_file() and sha(p)==wanted,(label,name,'artifact changed')
  checked+=1
 for name in ('run.json','stream.jsonl','stderr.txt','session.jsonl','mock-summary.json','oracle-output.txt','oracle-seed-output.txt','solution.bundle','analysis.json','mxc-build-provenance.json'):
  p=d/name
  if p.is_file():files.append(copy(p,destination/name))
 row={'label':label,'kind':kind,'harness':r['harness'],'raw_run_directory':str(d),'snapshot':'evidence/'+label,
 'source_plugin_commit':r.get('plugin_sha'),'prompt_sha256':r.get('prompt_sha256'),'controller_exit_not_used_as_acceptance':True,
 'child_exit':r.get('exit_code'),'exit_reason':r.get('exit_reason'),'record_state':e['state'],'process_outcome':e['process_outcome'],
 'capture_status':e['capture_status'],'postprocessing':e['postprocessing'],'failure':e['failure'],'workflow_acceptance':e['workflow_acceptance'],
 'reference_eligible':r.get('reference_eligible'),'telemetry_enabled':(r.get('telemetry') or {}).get('enabled'),
 'oracle':r.get('oracle'),'budget_s':e['hard_wall_budget_s'],'deadline_utc':e['initial_deadline_utc'],'invocations':e['invocations'],
 'contestant_time_s':e.get('contestant_time_s'),'attempt_elapsed_s':e.get('attempt_elapsed_s'),'finalization_time_s':e.get('finalization_time_s'),
 'attempt_deadline_overrun_s':max(0,(e.get('attempt_elapsed_s') or 0)-e['hard_wall_budget_s']),
 'parser_model_calls_not_billing':r.get('model_calls'),'parser_tokens_not_billing':r.get('tokens'),
 'real_provider_calls':0,'provider_call_evidence':'Python mock target; no model executable fallback; telemetry disabled; c0-full also denies egress',
 'declared_artifact_hashes_checked':checked,'workspace':r['workspace']}
 summary=d/'mock-summary.json'
 if summary.exists():
  m=read(summary);checks=m.get('checks',[])
  row['mock_checks']={'count':len(checks),'passed':sum(c.get('status')=='pass' or c.get('passed') is True for c in checks),'failed':m.get('failed',[]),'ok':m.get('ok')}
 w=Path(r['workspace']);full=w/'.git/c0-full-summary.json'
 if full.exists():
  fixture=read(full);row['scripted_fixture']=fixture
  for p in (full,w/'.git/c0-full-commands.json'):
   files.append(copy(p,destination/p.name))
  folder=w/fixture['planning_folder']
  for relative in ('review-plan.md','review-phase-1.md','review-impl.md','run-summary.md','handoff.md','kanban.md','.heartbeat'):
   files.append(copy(folder/relative,destination/'scripted-artifacts'/relative))
  assert fixture['tests_passed']==17 and len(fixture['saved_domain_replies'])==3
  assert fixture['deadline_environment']['GEEKY_DEADLINE_UTC']==e['initial_deadline_utc']
  assert fixture['deadline_environment']['GEEKY_CLOSEOUT_RESERVE_S']==e['closeout_reserve_s']
  assert fixture['model_calls']==0 and fixture['label']=='SCRIPTED MOCK'
  for rel,expected in fixture['source_hashes'].items():assert sha(w/rel)==expected
  assert subprocess.check_output(['git','-C',str(w),'status','--porcelain'],text=True)==''
  assert r['oracle']['passed']==13 and r['oracle']['stable_over_3'] is True
 rows.append(row)
for p in OUT.iterdir():
 if p.is_file() and p.name != 'collection.log' and p.suffix in ('.ps1','.log','.json','.txt','.py'):
  files.append(copy(p,REPORT/'commands'/p.name))
for h in ('claude','codex'):
 for category in ('scoring-'+h,'scoring-fresh-'+h,'scoped-preview-'+h):
  for p in (OUT/category).rglob('*'):
   if p.is_file():files.append(copy(p,REPORT/('scoped' if category.startswith('scoped') else 'scoring')/category/p.relative_to(OUT/category)))
fixture_root=Path(r'C:\repos\c0-remediation-mock-20261026\full-harness')
fixture_out=fixture_root/'outputs/c0-full-fixture'
for name in ('fixture-support.diff','fixture-support-manifest.json','verified-tests.log','script-validation.log','README.md'):
 files.append(copy(fixture_out/name,REPORT/'support'/name))
for p in (fixture_root/'geeky-orchestration/evals/mock-agent/c0_fixture.py',fixture_root/'geeky-orchestration/evals/mock-agent/test_c0_fixture.py'):
 files.append(copy(p,REPORT/'support'/p.name))
head=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
assert head=='d90bbd352d5722784180100bf5e431e91bc55210'
tracked=subprocess.check_output(['git','-C',str(ROOT),'diff','--name-only'],text=True).splitlines()
assert not tracked,tracked
product=[]
for p in read(ROOT/'outputs/remediation-20261026/combined-product-state.json'):
 assert sha(ROOT/p['path'])==p['sha256']
 product.append(p)
metrics={'schema':'geeky-eval.mock-observations/1','as_of_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'accepted_source_commit':head,
 'purpose':'non-chargeable post-remediation C0 mock execution through real vetted Windows MXC','actual_mxc_runs':len(rows),
 'real_provider_calls':0,'model_judge_calls':0,'live_telemetry_calls':0,'billing_readback_performed':False,
 'billing_note':'Mock usage/parser fields are synthetic; no account-wide charge or live-model capability claim.',
 'main_product_files_unchanged':len(product),'fixture_support_promoted_to_main':False,'source_repo_commits_created':0,
 'fixture_local_tests':{'passed':25,'exit':0},'scope_previews':read(OUT/'scoped-preview-results.json'),'runs':rows}
(REPORT/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n',encoding='utf-8')
(REPORT/'evidence-manifest.json').write_text(json.dumps({'schema':'mock-evidence.manifest/1','files':files},indent=2)+'\n',encoding='utf-8')
(REPORT/'source-fingerprints.json').write_text(json.dumps({'accepted_source_commit':head,'main_product':product,'fixture_support':read(fixture_out/'fixture-support-manifest.json')},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'mxc_runs':len(rows),'snapshotted_files':len(files),'snapshot_bytes':sum(f['bytes'] for f in files),'all_declared_hashes_checked':sum(r['declared_artifact_hashes_checked'] for r in rows),'full_c0_oracle':'13/13 x3 each','real_provider_calls':0,'main_product_unchanged':len(product),'report':str(REPORT)},indent=2))