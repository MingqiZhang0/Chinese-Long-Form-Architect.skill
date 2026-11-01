"""Apply the isolated spike read profile to the existing shared contract."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / 'docs/workbench/contracts/workbench-wire.schema.json'
schema = json.loads(PATH.read_text(encoding='utf-8'))
d = schema['$defs']
d['RequestId']={'type':'string','minLength':1,'x-id-type':'RequestId'}
d['Hello']['properties']['server_process_id']={'type':'integer','minimum':1}
def ref(name): return {'$ref': '#/$defs/' + name}
def obj(props, strict=False): return {'type':'object','properties':props,'required':list(props),'additionalProperties':not strict}
def arr(item): return {'type':'array','items':item}
string = {'type':'string'}
integer = {'type':'integer','minimum':0}
boolean = {'type':'boolean'}
for name, values in {
    'Completeness':['FULL','PARTIAL','UNKNOWN'], 'Freshness':['FRESH','STALE','UNKNOWN'],
    'EpistemicState':['UNKNOWN','HEARD','KNOWN','BELIEVED'], 'EvidenceHealth':['VALID','STALE','BROKEN','AMBIGUOUS'],
}.items(): d[name] = {'type':'string','enum':values}
d['NarrativePosition'] = obj({'axis':{'enum':['story_valid','presentation'],'type':'string'},'domain':string,'value':{'type':'number'},'boundary':{'const':'at'},'chapter_id':string}, True)
d['ExecutionManifest'] = obj({'execution_kind':{'const':'DETERMINISTIC'},'agent_calls':{'const':0,'type':'integer'},'owner_calls':arr(string),'engine_version':string,'query_semantics_version':ref('Version')})
d['Span'] = obj({'start':integer,'end':integer,'offset_unit':{'const':'unicode_scalar'}})
d['TraceNode'] = obj({'id':string,'kind':{'type':'string','enum':['KnowledgeState','Event','Claim','Evidence','Anchor','Source']}})
d['TraceEdge'] = obj({'source':string,'target':string,'kind':string,'depth':integer})
d['Block'] = obj({'block_id':string,'start':integer,'text':string})
d['Issue'] = obj({'issue_id':ref('IssueId'),'code':string,'message':string})
def result(name, props):
    d[name] = obj({'kind':{'const':name},**props})
    variants = d['SuccessResponse']['properties']['result']['oneOf']
    if ref(name) not in variants: variants.append(ref(name))
bound={'snapshot_id':ref('SnapshotId'),'completeness':ref('Completeness'),'freshness':ref('Freshness'),'warnings':arr(string),'manifest':ref('ExecutionManifest')}
result('KnowledgeResult',{**bound,'character_id':ref('CharacterId'),'fact_id':ref('FactId'),'position':ref('NarrativePosition'),'epistemic_state':ref('EpistemicState'),'knowledge_id':string,'evidence_refs':arr(ref('EvidenceId')),'provenance_refs':arr(string)})
result('TraceResult',{**bound,'nodes':arr(ref('TraceNode')),'edges':arr(ref('TraceEdge'))})
result('EvidenceResult',{'snapshot_id':ref('SnapshotId'),'evidence_id':ref('EvidenceId'),'anchor_id':ref('AnchorId'),'source_revision':string,'basis_source_revision':string,'block_id':string,'content_fingerprint':string,'context_fingerprint':string,'span':ref('Span'),'display_text':string,'health':ref('EvidenceHealth'),'warnings':arr(string)})
result('ManuscriptPage',{'snapshot_id':ref('SnapshotId'),'source_revision':string,'blocks':arr(ref('Block')),'total_blocks':integer,'start_block':integer,'highlight':ref('Span')})
result('SnapshotInfo',{'snapshot_id':ref('SnapshotId'),'source_revision':string,'freshness':ref('Freshness'),'watch_status':string,'failed_candidate':string,'issues':arr(ref('Issue')),'agent_calls':{'const':0,'type':'integer'}})
result('SemanticDiff',{'before_snapshot_id':ref('SnapshotId'),'after_snapshot_id':ref('SnapshotId'),'changed_sources':arr(string),'changed_evidence':arr(ref('EvidenceId')),'canonical_changed':boolean,'freshness_before':ref('Freshness'),'freshness_after':ref('Freshness')})
result('IssuePage',{'snapshot_id':ref('SnapshotId'),'issues':arr(ref('Issue')),'total':integer,'offset':integer})
lease={'project_token':ref('ProjectToken'),'snapshot_id':ref('SnapshotId'),'lease_id':ref('LeaseId')}
def request(method, props):
    rows=d['Request']['oneOf']
    rows[:]=[x for x in rows if x['properties']['method']['const'] != method]
    rows.append(obj({'protocol_version':ref('Version'),'request_id':{'type':'string','minLength':1},'correlation_id':{'type':'string','minLength':1},'method':{'const':method},'params':obj(props, True)},True))
request('state.query',{**lease,'domain':{'const':'actor_epistemic'},'character_id':ref('CharacterId'),'fact_id':ref('FactId'),'position':ref('NarrativePosition')})
request('trace.query',{**lease,'node_id':string})
request('source.resolve',{**lease,'evidence_id':ref('EvidenceId')})
request('manuscript.page',{**lease,'start_block':integer,'limit':{'type':'integer','minimum':1,'maximum':100},'anchor_id':string})
request('snapshot.get',lease)
request('issue.page',{**lease,'offset':integer,'limit':{'type':'integer','minimum':1,'maximum':1000},'filter':string})
request('observation.subscribe',{'project_token':ref('ProjectToken')})
request('snapshot.compare',{**lease,'before_snapshot_id':ref('SnapshotId'),'before_lease_id':ref('LeaseId')})
schema['title']='Workbench bootstrap and isolated spike read profile'
schema['description']='Existing bootstrap preserved; spike numeric story-time read profile. Not a complete production contract.'
PATH.write_text(json.dumps(schema,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
