"""Read-only Narrative Service Host. No Agent gateway and no mutation dispatch."""
import argparse, concurrent.futures, hashlib, json, os, sys, threading, time, uuid
from pathlib import Path
sys.dont_write_bytecode=True
if getattr(sys,'frozen',False): ROOT=Path(sys._MEIPASS)
else: ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from jsonschema import Draft202012Validator
import story_ops, narrative_runtime
from observation import ProjectObservation
from framing import read_frame, encode, MAX_FRAME

SCHEMA_PATH=ROOT/'docs/workbench/contracts/workbench-wire.schema.json'
# The schema digest is over UTF-8 text with LF newlines on every platform.
SCHEMA=json.loads(SCHEMA_PATH.read_bytes())
def validator(name): return Draft202012Validator({'$ref':'#/$defs/'+name,'$defs':SCHEMA['$defs']})
REQUEST=validator('Request');RESPONSE=Draft202012Validator(SCHEMA)
WIRE=sys.stdout.buffer
# Capture all legacy prints, including worker prints, without thread-global redirect races.
sys.stdout=sys.stderr
def log(event,**fields):
    print(json.dumps({'timestamp':time.time(),'component':'NarrativeHost','severity':'info','event':event,**fields}),file=sys.stderr,flush=True)

class Fault(Exception):
    def __init__(self,code,message):self.code=code;super().__init__(message)

class Host:
    def __init__(self,delays=None):
        self.instance=uuid.uuid4().hex;self.project=None;self.negotiated=False;self.maximum=MAX_FRAME;self.shutdown=False
        self.write_lock=threading.Lock();self.tasks_lock=threading.Lock();self.tasks={};self.pool=concurrent.futures.ThreadPoolExecutor(max_workers=4)
        self.delays=delays or {};self.agent_calls=0;self.write_attempts=0
        sys.addaudithook(self.audit)
    def audit(self,event,args):
        if event in ('socket.connect','subprocess.Popen'):
            self.agent_calls+=1;raise PermissionError('DETERMINISTIC_QUERY_AGENT_CALL_VIOLATION')
        if self.project:
            path=None
            if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
                mode=args[1];flags=args[2]
                if (isinstance(mode,str) and any(x in mode for x in 'wax+')) or flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):path=args[0]
            elif event in ('os.remove','os.rename','os.mkdir','os.rmdir'):path=args[0]
            if event=='os.rename' and Path(os.fsdecode(args[1])).resolve().is_relative_to(self.project.root):
                self.write_attempts+=1;raise PermissionError('READ_ONLY_VIOLATION')
            if path is not None and Path(os.fsdecode(path)).resolve().is_relative_to(self.project.root):
                self.write_attempts+=1;raise PermissionError('READ_ONLY_VIOLATION')
    def send(self,value):
        RESPONSE.validate(value)
        frame=encode(value)
        if len(frame)-4>self.maximum:raise ValueError('Negotiated frame size exceeded')
        with self.write_lock:WIRE.write(frame);WIRE.flush()
    def error(self,r,code,message):
        return {'protocol_version':'1.0.0','request_id':r.get('request_id','invalid'),'correlation_id':r.get('correlation_id','invalid'),'error':{'code':code,'category':'cancellation' if code=='CANCELLED' else 'validation','message':message,'retryable':False,'details':None,'object_refs':[],'snapshot_id':r.get('params',{}).get('snapshot_id'),'origin':'engine'}}
    def manifest(self,*owners):
        if self.agent_calls:raise Fault('INTERNAL_ERROR','DETERMINISTIC_QUERY_AGENT_CALL_VIOLATION')
        return {'execution_kind':'DETERMINISTIC','agent_calls':0,'owner_calls':list(owners),'engine_version':'spike-1','query_semantics_version':'1.0.0'}
    def base(self,s,*owners):
        return {'snapshot_id':s.id,'completeness':'FULL','freshness':s.freshness(),'warnings':[],'manifest':self.manifest(*owners)}
    def dispatch(self,r,cancel):
        method=r['method'];p=r['params']
        if method=='hello':
            if '1.0.0' not in p['supported_versions']:raise Fault('UNSUPPORTED_PROTOCOL','No common protocol')
            self.maximum=min(MAX_FRAME,p['max_frame_bytes']);self.negotiated=True
            return {'kind':'Hello','selected_version':'1.0.0','compatibility':'COMPATIBLE','server_instance_id':self.instance,'server_process_id':os.getpid(),'engine_version':'spike-1','supported_protocols':['1.0.0'],'schema_digest':'sha256:'+hashlib.sha256(SCHEMA_PATH.read_text(encoding='utf-8').encode('utf-8')).hexdigest(),'schema_capabilities':['bootstrap','spike-read'],'supported_features':['state.query','trace.query','source.resolve','manuscript.page','observation.subscribe','snapshot.compare','issue.page'],'health':'READY','readonly_enforcement':'UNVERIFIED','agent_available':False}
        if not self.negotiated or r['protocol_version']!='1.0.0':raise Fault('UNSUPPORTED_PROTOCOL','Handshake required')
        if method=='health.query':return {'kind':'Health','server_instance_id':self.instance,'engine_version':'spike-1','health':'READY','agent_available':False}
        if method=='service.shutdown':self.shutdown=True;return {'kind':'ControlAck','accepted':True}
        if method=='request.cancel':
            with self.tasks_lock:target=self.tasks.get(p['target_request_id'])
            if target:target.set()
            return {'kind':'ControlAck','accepted':target is not None}
        if method=='session.open':
            root=Path(p['project_root']).resolve()
            if not (root/'project.json').is_file():raise Fault('PROJECT_NOT_FOUND','Fixture project.json not found; production manifest adapter not enabled')
            if self.project:self.project.close()
            self.project=ProjectObservation(root,self.send)
            return self.info()
        project=self.project
        if not project or p.get('project_token')!=project.token:raise Fault('INVALID_REQUEST','Invalid project token')
        if method=='project.info':return self.info()
        if method=='snapshot.pin':return project.pin(p['requested_snapshot_id'])
        if method=='snapshot.release':
            with project.lock:removed=project.leases.pop(p['lease_id'],None)
            return {'kind':'ControlAck','accepted':removed is not None}
        if method=='observation.subscribe':project.subscribed=True;return {'kind':'ControlAck','accepted':True}
        s=project.leased(p)
        if method=='snapshot.get':return {'kind':'SnapshotInfo','snapshot_id':s.id,'source_revision':s.source_revision,'freshness':s.freshness(),'watch_status':project.status,'failed_candidate':project.failed,'issues':list(s.issues[:100]),'agent_calls':0}
        if method=='issue.page':
            rows=[x for x in s.issues if p['filter'] in x['message'] or p['filter'] in x['code']]
            return {'kind':'IssuePage','snapshot_id':s.id,'issues':rows[p['offset']:p['offset']+p['limit']],'total':len(rows),'offset':p['offset']}
        if method=='state.query':
            pos=p['position']
            if pos['axis']!='story_valid' or pos['domain']!='day':raise Fault('QUERY_INCOMPLETE','Only explicit numeric story_valid/day is supported; chapter does not imply story time')
            # Test-only delays are launcher configuration, never a production mutation method.
            delay=self.delays.get(p['character_id'],0)
            if cancel.wait(delay):raise Fault('CANCELLED','Cancelled at owner boundary')
            rows=[x for x in story_ops.knowledge_at(s.state,p['character_id'],pos['value']) if x['fact']==p['fact_id']]
            state=rows[-1]['status'].upper() if rows else 'UNKNOWN'
            if len(rows)>1:state='UNKNOWN' # A conflict cannot be collapsed into last-write-wins.
            if state not in ('UNKNOWN','HEARD','KNOWN','BELIEVED'):raise Fault('QUERY_INCOMPLETE','Unsupported epistemic state')
            originals=[x for x in s.state['knowledge_state'] if x.get('actor')==p['character_id'] and x.get('fact')==p['fact_id'] and rows and x.get('source')==rows[-1].get('source')]
            kid=originals[-1].get('id','') if originals else ''
            trace=narrative_runtime.why_trace(s.graph,kid) if kid else []
            refs=sorted({x['source'] for x in trace if x['source'] in s.evidence})
            result={'kind':'KnowledgeResult',**self.base(s,'story_ops.knowledge_at','narrative_runtime.why_trace'),'character_id':p['character_id'],'fact_id':p['fact_id'],'position':pos,'epistemic_state':state,'knowledge_id':kid,'evidence_refs':refs,'provenance_refs':[x['source'] for x in trace]}
            if rows and (state=='UNKNOWN' or not refs):result['completeness']='PARTIAL';result['warnings'].append('TRACE_GAP')
            if len(rows)>1:result['warnings'].append('CONFLICTING_INTERVALS')
            if not rows:result['completeness']='PARTIAL';result['warnings'].append('NO_RECORDED_STATE')
            if result['freshness']=='STALE':result['warnings'].append('REQUIRES_REANALYSIS')
            if any(s.resolve(e)['health']!='VALID' for e in refs):result['completeness']='PARTIAL';result['freshness']='STALE';result['warnings'].append('BROKEN_EVIDENCE')
            return result
        if method=='trace.query':
            edges=narrative_runtime.why_trace(s.graph,p['node_id'])
            ids=sorted({p['node_id']}|{e[k] for e in edges for k in ('source','target')})
            missing=any(x not in s.nodes for x in ids)
            terminals={x for x in ids if not any(e['target']==x for e in edges)}
            closed={x for x in ids if s.nodes.get(x)=='Source'}
            for _ in ids:
                extended=closed|{e['target'] for e in edges if e['source'] in closed}
                if extended==closed:break
                closed=extended
            gap=missing or p['node_id'] not in closed or any(s.nodes.get(x)!='Source' for x in terminals)
            broken=any(s.resolve(x)['health']!='VALID' for x in ids if x in s.evidence)
            return {'kind':'TraceResult',**self.base(s,'narrative_runtime.why_trace'),'nodes':[{'id':x,'kind':s.nodes[x]} for x in ids if x in s.nodes],'edges':[{k:e[k] for k in ('source','target','kind','depth')} for e in edges],'completeness':'PARTIAL' if gap or broken else 'FULL','warnings':(['TRACE_GAP'] if gap else [])+(['BROKEN_EVIDENCE'] if broken else [])}
        if method=='source.resolve':return s.resolve(p['evidence_id'])
        if method=='manuscript.page':
            start=p['start_block'];highlight={'start':0,'end':0,'offset_unit':'unicode_scalar'}
            if p['anchor_id']:
                eid=next((k for k,v in s.evidence.items() if v['anchor_id']==p['anchor_id']),None)
                if not eid:raise Fault('BROKEN_EVIDENCE','Unknown anchor')
                resolved=s.resolve(eid)
                if resolved['health']!='VALID':raise Fault('BROKEN_EVIDENCE','Anchor cannot be highlighted as valid')
                start=next(i for i,b in enumerate(s.blocks) if b['block_id']==resolved['block_id']);highlight=resolved['span']
            return {'kind':'ManuscriptPage','snapshot_id':s.id,'source_revision':s.source_revision,'blocks':list(s.blocks[start:start+p['limit']]),'total_blocks':len(s.blocks),'start_block':start,'highlight':highlight}
        if method=='snapshot.compare':
            old=project.leased({**p,'snapshot_id':p['before_snapshot_id'],'lease_id':p['before_lease_id']})
            return {'kind':'SemanticDiff','before_snapshot_id':old.id,'after_snapshot_id':s.id,'changed_sources':['manuscript'] if old.source_revision!=s.source_revision else [],'changed_evidence':[x for x in old.evidence if x not in s.evidence or old.resolve(x)['health']!=s.resolve(x)['health']],'canonical_changed':old.state!=s.state,'freshness_before':old.freshness(),'freshness_after':s.freshness()}
        raise Fault('INVALID_REQUEST','Unknown method')
    def info(self):
        p=self.project
        return {'kind':'ProjectInfo',**p.project,'project_token':p.token,'supported_features':['spike-read','native-watch']}
    def execute(self,r,cancel):
        begin=time.perf_counter()
        try:
            REQUEST.validate(r)
            result=self.dispatch(r,cancel)
            if cancel.is_set():raise Fault('CANCELLED','Cancelled before terminal')
            response={'protocol_version':'1.0.0','request_id':r['request_id'],'correlation_id':r['correlation_id'],'result':result}
        except Fault as exc:response=self.error(r,exc.code,str(exc))
        except TimeoutError as exc:response=self.error(r,'LEASE_EXPIRED',str(exc))
        except OverflowError as exc:response=self.error(r,'BUSY',str(exc))
        except Exception as exc:
            log('request_error',request_id=r.get('request_id'),error=type(exc).__name__)
            response=self.error(r,'INVALID_REQUEST',type(exc).__name__)
        try:self.send(response)
        finally:
            with self.tasks_lock:self.tasks.pop(r.get('request_id'),None)
            log('request_terminal',request_id=r.get('request_id'),correlation_id=r.get('correlation_id'),snapshot_id=r.get('params',{}).get('snapshot_id'),engine_instance=self.instance,method=r.get('method'),duration_ms=(time.perf_counter()-begin)*1000,payload_bytes=len(encode(response))-4,agent_calls=self.agent_calls,source_write_attempts=self.write_attempts)
    def run(self):
        try:
            while not self.shutdown:
                r=read_frame(sys.stdin.buffer,self.maximum)
                if r is None:break
                rid=r.get('request_id','invalid');cancel=threading.Event()
                with self.tasks_lock:
                    if rid in self.tasks:self.send(self.error(r,'INVALID_REQUEST','Duplicate pending request'));continue
                    if len(self.tasks)>=128:self.send(self.error(r,'BUSY','Request capacity'));continue
                    self.tasks[rid]=cancel
                if r.get('method') in ('hello','session.open','request.cancel','service.shutdown'):self.execute(r,cancel)
                else:self.pool.submit(self.execute,r,cancel)
        except (EOFError,ValueError,UnicodeError) as exc:log('fatal_frame',severity='error',error=str(exc))
        finally:
            with self.tasks_lock:
                for flag in self.tasks.values():flag.set()
            self.pool.shutdown(wait=True,cancel_futures=True)
            if self.project:self.project.close()
            log('service_stopped',engine_instance=self.instance,agent_calls=self.agent_calls,source_write_attempts=self.write_attempts)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--test-delays',default='{}');parser.add_argument('--startup-delay',type=float,default=0)
    args=parser.parse_args();time.sleep(args.startup_delay);Host(json.loads(args.test_delays)).run()
