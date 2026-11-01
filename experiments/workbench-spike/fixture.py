"""Deterministic fixture generator. Writes only an explicitly supplied destination."""
import hashlib, json
from pathlib import Path
TEXT='第一章：薛照𠮷🙂 e\u0301，English。\r\n\r\n<!-- block:hears -->\nA听说：铜门后的钥匙是蓝色。\n\n<!-- block:proof -->\n𠮷🙂 e\u0301 薛照亲眼确认：钥匙是蓝色的。\r\n\r\n<!-- block:leak -->\nB说：“F2，密室在东边。”他尚未获得此事。\n'
def digest(data): return 'sha256:'+hashlib.sha256(data).hexdigest()
def make_fixture(root:Path, large=False):
    root.mkdir(parents=True,exist_ok=True)
    (root/'canonical').mkdir(exist_ok=True); (root/'analysis').mkdir(exist_ok=True); (root/'runtime').mkdir(exist_ok=True)
    text=TEXT
    if large:
        # Exactly 1,000,000 Chinese BMP characters in the added corpus, deterministic.
        text+='\n'+''.join(f'<!-- block:corpus-{i} -->\n'+('山河星月风雨人间故事春秋'*25)[:250]+'\n\n' for i in range(4000))
    (root/'manuscript.txt').write_bytes(text.encode('utf-8'))
    def write(path, data): (root/path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    write('project.json',{'project_id':'spike-P1','display_name':'叙事观察实验','schema_version':'spike-1','manuscript':'manuscript.txt'})
    state={'characters':[{'id':'A'},{'id':'B'}], 'facts':[{'id':'F1'},{'id':'F2'}],
        'knowledge_state':[{'id':'K-heard','actor':'A','fact':'F1','status':'heard','acquired_at':1,'retired_at':2,'source':'E-heard'},
            {'id':'K1','actor':'A','fact':'F1','status':'known','acquired_at':2,'retired_at':5,'source':'E1'},
            {'id':'K-untimed','actor':'A','fact':'F2','status':'known','source':'E-gap'}],
        'knowledge_uses':[{'actor':'B','fact':'F2','acquired':4,'used':3}]}
    write('canonical/state.json',state)
    write('canonical/claims.json',{'C1':{'fact_id':'F1','evidence_refs':['EV1']},'C2':{'fact_id':'F1','evidence_refs':['EV1']}})
    events=[{'event_id':'E-heard','branch':'main','seq':1,'event_type':'FactLearned','intent':'synthetic heard transition','source':'C1','effects':[]},
        {'event_id':'E1','branch':'main','seq':2,'event_type':'FactLearned','intent':'synthetic witnessed transition','source':'C1','effects':[{'op':'set','path':'knowledge_state','value':state['knowledge_state']}]}]
    (root/'runtime/events.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in events),encoding='utf-8')
    write('runtime/branches.json',{'main':{'parent':None}})
    proof='𠮷🙂 e\u0301 薛照亲眼确认：钥匙是蓝色的。'
    start=proof.index('钥匙'); end=start+len('钥匙是蓝色的')
    write('canonical/evidence.json',{'EV1':{'anchor_id':'A1','block_id':'proof','source_revision':digest(text.encode()),'content_fingerprint':digest(proof.encode()),'context_fingerprint':digest(b'hears|leak'),'span':{'start':start,'end':end,'offset_unit':'unicode_scalar'},'display_text':proof[start:end]}})
    nodes={'K1':'KnowledgeState','E1':'Event','C1':'Claim','C2':'Claim','EV1':'Evidence','A1':'Anchor','SRC1':'Source','K-heard':'KnowledgeState','E-heard':'Event'}
    write('canonical/provenance-nodes.json',nodes)
    edges=[{'source':a,'target':b,'kind':'supports','status':'active'} for a,b in [('E1','K1'),('C1','E1'),('C2','E1'),('EV1','C1'),('EV1','C2'),('A1','EV1'),('SRC1','A1')]]
    write('runtime/dependencies.json',{'edges':edges})
    write('analysis/freshness.json',{'basis_source_revision':digest(TEXT.encode()),'status':'FRESH','origin':'synthetic-reviewed-fixture'})
    write('analysis/issues.json',[{'issue_id':f'I-synthetic-{i}','code':'SYNTHETIC_DIAGNOSTIC','message':f'虚拟列表压力行 {i:05}'} for i in range(10000)] if large else [])
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('destination',type=Path);p.add_argument('--large',action='store_true');a=p.parse_args();make_fixture(a.destination,a.large)
