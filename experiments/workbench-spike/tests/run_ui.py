"""Launch a real Avalonia window, then edit only a temporary source as an external editor."""
import argparse,json,os,subprocess,sys,tempfile,time
from pathlib import Path
SPIKE=Path(__file__).resolve().parents[1];ROOT=SPIKE.parents[1];sys.path.insert(0,str(SPIKE))
from fixture import make_fixture,TEXT
p=argparse.ArgumentParser();p.add_argument('--app',type=Path,default=SPIKE/'desktop/Workbench.App/bin/Release/net10.0/Workbench.App.exe');p.add_argument('--engine',type=Path);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--isolated',action='store_true');p.add_argument('--output',type=Path,default=SPIKE/'artifacts/ui-large.json');p.add_argument('--live',action='store_true');p.add_argument('--startup-delay',default='0');args=p.parse_args()
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output=args.output.resolve()
Path(str(args.output)+'.ready').unlink(missing_ok=True)
args.output.unlink(missing_ok=True)
with tempfile.TemporaryDirectory(prefix='叙事 UI ') as temp:
    make_fixture(Path(temp),True)
    command=[str(args.app),'--root',str(args.root),'--project',temp,'--python',sys.executable,'--smoke-output',str(args.output),'--startup-delay',args.startup_delay]
    if args.engine:command+=['--engine',str(args.engine)]
    if args.live:command+=['--smoke-live']
    environment=dict(os.environ)
    if args.isolated:
        environment['PATH']=str(Path(os.environ['SystemRoot'])/'System32');environment['DOTNET_ROOT']=str(Path(temp)/'no-dotnet');environment['PYTHONHOME']=str(Path(temp)/'no-python');environment.pop('PYTHONPATH',None)
    started=time.perf_counter();process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=environment)
    if args.live:
        ready=Path(str(args.output)+'.ready');deadline=time.monotonic()+20
        while not ready.exists() and process.poll() is None and time.monotonic()<deadline:
            # Poll a test control file; no sleeps synchronize production code.
            try:process.wait(timeout=.05)
            except subprocess.TimeoutExpired:pass
        if not ready.exists():
            process.kill();stdout,stderr=process.communicate()
            raise RuntimeError('UI did not reach external-edit gate: '+stderr.decode(errors='replace')+' '+stdout.decode(errors='replace'))
        path=Path(temp)/'manuscript.txt';text=path.read_bytes().decode('utf-8');text=text.replace('<!-- block:proof -->\n𠮷🙂 e\u0301 薛照亲眼确认：钥匙是蓝色的。\r\n\r\n','');path.write_bytes(text.encode('utf-8'))
    stdout,stderr=process.communicate(timeout=30)
    result=json.loads(args.output.read_bytes());result['process_elapsed_ms']=(time.perf_counter()-started)*1000;result['exit_code']=process.returncode
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False));
    if process.returncode or not result['passed']:raise SystemExit(stderr.decode(errors='replace'))
