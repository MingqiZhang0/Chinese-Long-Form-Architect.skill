"""Capture actual Python sender output for independent C# typed decoding tests."""
import json,subprocess,sys,tempfile
from pathlib import Path
SPIKE=Path(__file__).resolve().parents[1];ROOT=SPIKE.parents[1];sys.path[:0]=[str(SPIKE),str(SPIKE/'service')]
from fixture import make_fixture
from framing import read_frame,encode
valid=[]
def normalize(value):
    if isinstance(value,list):return [normalize(v) for v in value]
    if isinstance(value,dict):return {k:('fixture-root' if k=='project_root' else 'engine-instance' if k=='server_instance_id' else 'token' if k=='project_token' else 'lease' if k=='lease_id' else normalize(v)) for k,v in value.items() if k!='server_process_id'}
    return value
with tempfile.TemporaryDirectory() as temp:
    make_fixture(Path(temp));p=subprocess.Popen([sys.executable,'-B',str(SPIKE/'service/host.py')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    def call(method,params):
        rid=f'golden-{len(valid)}';request={'protocol_version':'1.0.0','request_id':rid,'correlation_id':rid,'method':method,'params':params}
        p.stdin.write(encode(request));p.stdin.flush();response=read_frame(p.stdout)
        if 'error' in response:raise RuntimeError(response)
        valid.extend([{'name':method+'-request','message':normalize(request)},{'name':method+'-response','message':normalize(response)}]);return response['result']
    call('hello',{'supported_versions':['1.0.0'],'client_version':'spike-1','max_frame_bytes':8388608})
    project=call('session.open',{'project_root':temp});lease=call('snapshot.pin',{'project_token':project['project_token'],'requested_snapshot_id':None})
    bound={k:lease[k] for k in ('snapshot_id','lease_id')};bound['project_token']=project['project_token']
    call('state.query',{**bound,'domain':'actor_epistemic','character_id':'A','fact_id':'F1','position':{'axis':'story_valid','domain':'day','value':3,'boundary':'at','chapter_id':'CH3'}})
    call('trace.query',{**bound,'node_id':'K1'});call('source.resolve',{**bound,'evidence_id':'EV1'})
    call('manuscript.page',{**bound,'start_block':0,'limit':20,'anchor_id':'A1'});call('snapshot.get',bound)
    call('issue.page',{**bound,'offset':0,'limit':1000,'filter':''});call('service.shutdown',{})
    p.stdin.close();p.wait(timeout=5);p.stderr.close();p.stdout.close()
invalid=[]
for row in valid:
    if row['name']=='state.query-response':
        bad=json.loads(json.dumps(row['message']));bad['result']['epistemic_state']='SUPER_KNOWN';invalid.append({'name':'unknown-epistemic-enum','message':bad})
        bad=json.loads(json.dumps(row['message']));bad['result']['manifest']['agent_calls']=1;invalid.append({'name':'agent-call-violation','message':bad})
    if row['name']=='manuscript.page-response':
        bad=json.loads(json.dumps(row['message']));bad['result']['highlight']['offset_unit']='utf16';invalid.append({'name':'incorrect-offset-unit','message':bad})
(ROOT/'docs/workbench/contracts/spike-golden-wire.json').write_text(json.dumps({'valid':valid,'invalid':invalid},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'Captured {len(valid)} actual wire vectors and {len(invalid)} negative mutations')
