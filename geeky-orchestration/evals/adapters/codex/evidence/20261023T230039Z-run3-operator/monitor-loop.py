import datetime as dt,json,subprocess,sys,time
from pathlib import Path
op=Path(__file__).resolve().parent
for _ in range(135):
 r=subprocess.run([sys.executable,'-B',str(op/'monitor-run.py')],capture_output=True,text=True,encoding='utf-8',timeout=40)
 if r.returncode:
  print(json.dumps({'monitor_error':r.stderr[-1000:],'observed_utc':dt.datetime.now(dt.timezone.utc).isoformat()}),flush=True)
 else:
  state=json.loads(r.stdout);items=state.get('recent_items',[])
  print(json.dumps({'observed_utc':state['observed_utc'],'stream_bytes':state.get('files',{}).get('stream.jsonl',{}).get('bytes'),'stream_age_s':state.get('files',{}).get('stream.jsonl',{}).get('age_s'),'head':state.get('workspace_head'),'last_item':items[-1] if items else None,'terminal_event':state.get('terminal_event')}),flush=True)
 if (op/'runner-completion.json').exists():break
 time.sleep(45)
