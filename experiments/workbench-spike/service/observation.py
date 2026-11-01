"""Immutable observation generations and native hint aggregation, not narrative authority."""
import copy, hashlib, json, re, threading, time, uuid
from dataclasses import dataclass
from pathlib import Path
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import story_ops, narrative_runtime
from validate_story_state import validate_issues

def digest(data): return 'sha256:'+hashlib.sha256(data).hexdigest()
def safe_path(root, relative):
    path=(root/relative).resolve()
    if not path.is_relative_to(root.resolve()): raise ValueError('Source escapes project root')
    return path
def inventory(root):
    return {p.relative_to(root).as_posix(): (p.stat().st_size,p.stat().st_mtime_ns) for p in root.rglob('*') if p.is_file() and p.suffix in ('.txt','.json','.jsonl')}
def capture(root):
    before=inventory(root)
    data={key:safe_path(root,key).read_bytes() for key in before}
    if inventory(root)!=before: raise ValueError('SOURCE_UNSTABLE')
    return data
def blocks(text):
    markers=list(re.finditer(r'<!-- block:([^>]+) -->\r?\n',text))
    result=[]
    first=markers[0].start() if markers else len(text)
    if first: result.append({'block_id':'intro','start':0,'text':text[:first]})
    for i,m in enumerate(markers):
        end=markers[i+1].start() if i+1<len(markers) else len(text)
        value=text[m.end():end].rstrip('\r\n')
        result.append({'block_id':m[1],'start':m.end(),'text':value})
    ids=[x['block_id'] for x in result]
    if len(set(ids))!=len(ids): raise ValueError('Duplicate block identity')
    return result

@dataclass(frozen=True)
class Snapshot:
    id:str
    revision:str
    source_revision:str
    state:dict
    graph:list
    nodes:dict
    evidence:dict
    blocks:tuple
    issues:tuple
    def resolve(self,eid):
        ev=self.evidence[eid]; matches=[b for b in self.blocks if b['block_id']==ev['block_id']]
        health='BROKEN'; display=''; span=ev['span'];start=0
        if len(matches)>1: health='AMBIGUOUS'
        elif matches:
            b=matches[0];start=b['start']
            health='VALID' if digest(b['text'].encode())==ev['content_fingerprint'] else 'STALE'
            if health=='VALID': display=b['text'][span['start']:span['end']]
        return {'kind':'EvidenceResult','snapshot_id':self.id,'evidence_id':eid,'anchor_id':ev['anchor_id'],'source_revision':self.source_revision,'basis_source_revision':ev['source_revision'],'block_id':ev['block_id'],'content_fingerprint':ev['content_fingerprint'],'context_fingerprint':ev['context_fingerprint'],'span':{'start':start+span['start'],'end':start+span['end'],'offset_unit':'unicode_scalar'},'display_text':display,'health':health,'warnings':[] if health=='VALID' else ['BROKEN_EVIDENCE' if health=='BROKEN' else 'STALE_EVIDENCE']}
    def freshness(self): return 'STALE' if any(self.resolve(k)['health']!='VALID' or self.evidence[k]['source_revision']!=self.source_revision for k in self.evidence) else 'FRESH'

def build(data,serial):
    load=lambda key:json.loads(data[key].decode('utf-8'))
    project=load('project.json'); source=data.get(project['manuscript'],b'')
    parsed=tuple(blocks(source.decode('utf-8',errors='strict')))
    state=load('canonical/state.json'); graph=narrative_runtime.dependency_rows(load('runtime/dependencies.json'))
    evidence=load('canonical/evidence.json'); nodes=load('canonical/provenance-nodes.json')
    events=[json.loads(x) for x in data['runtime/events.jsonl'].decode('utf-8').splitlines() if x]
    branches=narrative_runtime.branch_map(load('runtime/branches.json'))
    errors,_=narrative_runtime.validate_runtime(events,branches,graph)
    if errors:raise ValueError('Runtime validation: '+str(errors))
    replayed,_=narrative_runtime.replay(events,branches,'main')
    if replayed.get('knowledge_state')!=state['knowledge_state']:raise ValueError('Canonical projection diverges from event replay')
    claims=load('canonical/claims.json')
    actual=set(claims)|set(evidence)|{x['event_id'] for x in events}|{x['id'] for x in state['knowledge_state']}|{x['anchor_id'] for x in evidence.values()}|{'SRC1'}
    if any(x not in actual for x in nodes):raise ValueError('Unbacked provenance registry node')
    # Structural shape validation; literary/data gaps are representable diagnostics.
    if not isinstance(state.get('knowledge_state'),list): raise ValueError('Invalid knowledge_state')
    for eid,ev in evidence.items():
        span=ev['span']
        if not 0<=span['start']<=span['end']: raise ValueError('Invalid span')
    issues=tuple({'issue_id':f'I-{i}','code':x['code'],'message':x['message']} for i,x in enumerate(validate_issues(state)))+tuple(load('analysis/issues.json'))
    rev=digest(b''.join(k.encode()+data[k] for k in sorted(data)))
    return Snapshot(f'S{serial:03}',rev,digest(source),state,graph,nodes,evidence,parsed,issues)

class WatchHints(FileSystemEventHandler):
    def __init__(self,owner): self.owner=owner
    def on_any_event(self,event):
        if event.event_type in ('opened','closed_no_write'):return
        self.owner.hint()

class ProjectObservation:
    def __init__(self,root,publish):
        self.root=root.resolve(); self.publish=publish; self.lock=threading.RLock();self.wake=threading.Condition(); self.closed=False
        self.epoch=0;self.status='UP_TO_DATE';self.failed='';self.subscribed=False;self.sequence=0;self.last_hint=0;self.last_reconcile=time.monotonic()
        self.project=json.loads(safe_path(self.root,'project.json').read_bytes());self.token=uuid.uuid4().hex
        initial=build(capture(self.root),1);self.serial=1;self.snapshots={initial.id:initial};self.current=initial;self.previous=initial.id;self.leases={};self.last_inventory=inventory(self.root)
        self.observer=Observer();self.observer.schedule(WatchHints(self),str(root),recursive=True);self.observer.start()
        self.thread=threading.Thread(target=self.run,daemon=True);self.thread.start()
    def hint(self):
        with self.wake:
            self.epoch+=1;self.last_hint=time.monotonic();self.status='CHANGE_DETECTED';self.wake.notify_all()
    def reconcile(self,reason='EVENT_LOSS_SUSPECTED'):
        """A native overflow/wake adapter can request an integrity capture instead of guessing lost events."""
        self.last_reconciliation_reason=reason
        self.hint()
    def run(self):
        handled=0
        while True:
            with self.wake:
                self.wake.wait_for(lambda:self.closed or self.epoch!=handled,timeout=30)
                if self.closed:return
                if self.epoch==handled:
                    if inventory(self.root)!=self.last_inventory:self.hint()
                    else:continue
                remaining=.3-(time.monotonic()-self.last_hint)
                if remaining>0:self.wake.wait(remaining);continue
                generation=self.epoch
            try:
                self.status='UPDATING';data=capture(self.root)
                with self.wake:
                    self.wake.wait(.15)
                    if self.closed:return
                    if generation!=self.epoch or inventory(self.root)!=self.last_inventory and data!=capture(self.root):continue
                candidate=build(data,self.serial+1)
                with self.lock,self.wake:
                    if generation!=self.epoch:continue
                    handled=generation;self.last_inventory=inventory(self.root)
                    if candidate.revision==self.current.revision:self.status='UP_TO_DATE';continue
                    old=self.current;self.previous=old.id;self.serial+=1;self.snapshots[candidate.id]=candidate;self.current=candidate;self.failed='';self.status='UP_TO_DATE';self.sequence+=1;self.collect()
                    if self.subscribed:self.publish({'protocol_version':'1.0.0','event':'snapshot.published','stream_id':self.token,'sequence':self.sequence,'project_id':self.project['project_id'],'previous_snapshot_id':old.id,'snapshot_id':candidate.id})
            except Exception as exc:
                self.failed=type(exc).__name__+': '+str(exc);self.status='ERROR';handled=generation
    def pin(self,requested=None):
        with self.lock:
            self.collect()
            if len(self.leases)>=128:raise OverflowError('Lease capacity')
            s=self.snapshots[requested] if requested else self.current
            if len({v[0] for v in self.leases.values()}|{s.id})>16:raise OverflowError('Pinned snapshot capacity')
            lid=uuid.uuid4().hex;self.leases[lid]=(s.id,time.monotonic()+300)
            return {'kind':'SnapshotLease','project_id':self.project['project_id'],'snapshot_id':s.id,'lease_id':lid,'project_revision':s.revision,'source_revision':s.source_revision,'index_revision':s.revision,'canonical_basis_revision':digest(json.dumps(s.state,sort_keys=True).encode()),'query_semantics_version':'1.0.0','lease_ttl_ms':300000}
    def collect(self):
        now=time.monotonic();self.leases={k:v for k,v in self.leases.items() if v[1]>now}
        keep={self.current.id,self.previous}|{v[0] for v in self.leases.values()}
        self.snapshots={k:v for k,v in self.snapshots.items() if k in keep}
    def leased(self,p):
        if p['project_token']!=self.token:raise PermissionError('Invalid session')
        with self.lock:
            sid,expires=self.leases.get(p['lease_id'],('',0))
            if sid!=p['snapshot_id'] or expires<time.monotonic():raise TimeoutError('LEASE_EXPIRED')
            return self.snapshots[sid]
    def close(self):
        self.observer.stop();self.observer.join(timeout=3)
        with self.wake:self.closed=True;self.wake.notify_all()
        self.thread.join(timeout=3)
