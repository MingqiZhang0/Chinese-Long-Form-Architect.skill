"""Five fresh processes; does not claim cold filesystem cache or a product SLA."""
import argparse,json,math,subprocess,sys
from pathlib import Path
SPIKE=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--app',type=Path,required=True);p.add_argument('--engine',type=Path,required=True);p.add_argument('--root',type=Path,required=True);args=p.parse_args()
rows=[]
for i in range(5):
    out=SPIKE/f'artifacts/process-run-{i}.json'
    proc=subprocess.run([sys.executable,'-B',str(SPIKE/'tests/run_ui.py'),'--app',str(args.app),'--engine',str(args.engine),'--root',str(args.root),'--isolated','--output',str(out)],capture_output=True,timeout=40)
    if proc.returncode:raise RuntimeError(proc.stderr.decode(errors='replace'))
    rows.append(json.loads(out.read_bytes()))
fields=['shell_ms','backend_ready_ms','evidence_jump_ms','end_jump_ms','issue_filter_ms','ui_working_set','engine_working_set']
summary={}
for field in fields:
    values=sorted(row[field] for row in rows);summary[field]={'p50':values[len(values)//2],'p95':values[math.ceil(len(values)*.95)-1],'samples':values}
result={'scope':'Current-machine observations; fresh app processes, warm filesystem possible; no product SLA','runs':5,'summary':summary}
(SPIKE/'artifacts/performance.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
