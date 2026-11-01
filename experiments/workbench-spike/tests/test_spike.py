"""Real native-watch and owner tests; every destructive edit targets a temporary fixture."""
import contextlib, hashlib, io, json, os, shutil, struct, subprocess, sys, tempfile, threading, time, unittest
from pathlib import Path
SPIKE=Path(__file__).resolve().parents[1];ROOT=SPIKE.parents[1]
sys.dont_write_bytecode=True
sys.path[:0]=[str(SPIKE),str(SPIKE/'service'),str(ROOT/'scripts')]
from fixture import make_fixture, TEXT
from framing import read_frame,encode
from observation import ProjectObservation,build,capture
import story_ops,narrative_runtime
from reader_state import reader_state_at
from jsonschema import Draft202012Validator

class Fragmented(io.BytesIO):
    def read(self,n=-1):return super().read(min(n,1))

class Owners(unittest.TestCase):
    def test_retired_no_resurrection(self):
        state={'knowledge_state':[{'actor':'A','fact':'F','acquired_at':1,'retired_at':5}],'knowledge_uses':[{'actor':'A','fact':'F','acquired':1}]}
        self.assertEqual(story_ops.knowledge_at(state,'A',10),[])
        self.assertEqual(story_ops.knowledge_at({'knowledge_state':[],'knowledge_uses':state['knowledge_uses']},'A',10),[])
    def test_missing_time_not_known(self):
        self.assertEqual(story_ops.knowledge_at({'knowledge_state':[{'actor':'A','fact':'F'}]},'A',10)[0]['status'],'unknown')
    def test_half_open_interval(self):
        s={'knowledge_state':[{'actor':'A','fact':'F','acquired_at':2,'retired_at':5}]}
        self.assertFalse(story_ops.knowledge_at(s,'A',1));self.assertTrue(story_ops.knowledge_at(s,'A',2));self.assertFalse(story_ops.knowledge_at(s,'A',5))
    def test_trace_all_supports_and_cycle(self):
        edges=[{'source':a,'target':b,'kind':'supports'} for a,b in [('A','C'),('B','C'),('A','B'),('C','A')]]
        self.assertEqual(len(narrative_runtime.why_trace(edges,'C')),4)
        self.assertEqual(narrative_runtime.why_trace(edges,'C'),narrative_runtime.why_trace(list(reversed(edges)),'C'))
    def test_retired_propagation(self):
        import argparse
        out=io.StringIO()
        with contextlib.redirect_stdout(out):story_ops.cmd_propagate({'dependencies':[{'source':'A','target':'B','status':'retired'}]},argparse.Namespace(node='A',state=Path('missing/state.json'),dependencies=None,json=True))
        self.assertEqual(json.loads(out.getvalue()),[])
    def test_fragmented_multiple_unicode_frames(self):
        v={'text':'薛照𠮷🙂 e\u0301\r\nLF\n'};s=Fragmented(encode(v)*2)
        self.assertEqual(read_frame(s),v);self.assertEqual(read_frame(s),v);self.assertIsNone(read_frame(s))
    def test_invalid_frames(self):
        for data in [b'\x00',struct.pack('>I',3)+b'{}',struct.pack('>I',8388609),struct.pack('>I',1)+b'\xff']:
            with self.subTest(data=data),self.assertRaises((ValueError,EOFError,UnicodeError)):read_frame(io.BytesIO(data))
    def test_schema_goldens(self):
        schema=json.loads((ROOT/'docs/workbench/contracts/workbench-wire.schema.json').read_bytes());v=Draft202012Validator(schema)
        for filename in ['golden-wire.json','spike-golden-wire.json']:
            gold=json.loads((ROOT/'docs/workbench/contracts'/filename).read_bytes())
            for expected,group in [(True,'valid'),(False,'invalid')]:
                for row in gold[group]:self.assertEqual(v.is_valid(row['message']),expected,row['name'])

class NativeWatch(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='叙事 spike ');self.root=Path(self.temp.name);make_fixture(self.root)
        self.condition=threading.Condition();self.events=[]
        def published(e):
            with self.condition:self.events.append(e);self.condition.notify_all()
        self.project=ProjectObservation(self.root,published);self.project.subscribed=True
    def tearDown(self):self.project.close();self.temp.cleanup()
    def wait_publish(self,count=1):
        with self.condition:self.assertTrue(self.condition.wait_for(lambda:len(self.events)>=count,timeout=6),'native event not published')
        return self.project.current
    def test_external_delete_historical_pin_and_diff(self):
        old=self.project.pin();s1=self.project.current
        (self.root/'manuscript.txt').write_bytes(TEXT.replace('<!-- block:proof -->\n𠮷🙂 e\u0301 薛照亲眼确认：钥匙是蓝色的。\r\n\r\n','').encode())
        s2=self.wait_publish();self.assertEqual(s2.resolve('EV1')['health'],'BROKEN');self.assertEqual(s1.resolve('EV1')['health'],'VALID')
        self.assertEqual(self.project.leased({'project_token':self.project.token,**old}),s1)
        self.assertNotEqual(s1.source_revision,s2.source_revision);self.assertEqual(s1.state,s2.state)
    def test_modified_stale_not_reattached(self):
        (self.root/'manuscript.txt').write_bytes(TEXT.replace('钥匙是蓝色的','钥匙是红色的').encode())
        self.assertEqual(self.wait_publish().resolve('EV1')['health'],'STALE')
    def test_insert_unrelated_keeps_exact_scalar_span(self):
        (self.root/'manuscript.txt').write_bytes(('新增𠮷🙂 e\u0301\r\n'+TEXT).encode())
        ev=self.wait_publish().resolve('EV1');self.assertEqual(ev['health'],'VALID');self.assertEqual(ev['display_text'],'钥匙是蓝色的')
    def test_rapid_twenty_save_coalescing(self):
        for i in range(20):(self.root/'manuscript.txt').write_bytes((TEXT+str(i)).encode())
        s=self.wait_publish();self.assertEqual(len(self.events),1);self.assertIn('19',s.blocks[-1]['text'])
    def test_bulk_hundred_files_one_publish(self):
        for i in range(100):(self.root/f'chapter-{i}.txt').write_text('中文',encoding='utf-8')
        self.wait_publish();self.assertEqual(len(self.events),1)
    def test_candidate_failure_retains_previous(self):
        old=self.project.current
        (self.root/'canonical/state.json').write_text('{',encoding='utf-8')
        with self.project.wake:self.assertTrue(self.project.wake.wait_for(lambda:self.project.epoch>0,timeout=3))
        deadline=time.monotonic()+4
        with self.project.wake:
            while not self.project.failed and time.monotonic()<deadline:self.project.wake.wait(.05)
        self.assertTrue(self.project.failed);self.assertIs(self.project.current,old);self.assertEqual(self.events,[])
    def test_source_rename_broken_and_history_available(self):
        old=self.project.current;(self.root/'manuscript.txt').rename(self.root/'renamed.txt')
        self.assertEqual(self.wait_publish().resolve('EV1')['health'],'BROKEN');self.assertEqual(old.resolve('EV1')['health'],'VALID')
    def test_event_loss_integrity_reconciliation(self):
        self.project.observer.stop();self.project.observer.join()
        path=self.root/'manuscript.txt';stamp=path.stat();path.write_bytes(TEXT.replace('钥匙是蓝色的','钥匙是红色的').encode());os.utime(path,ns=(stamp.st_atime_ns,stamp.st_mtime_ns))
        self.project.reconcile('EVENT_LOSS_SUSPECTED')
        self.assertEqual(self.wait_publish().resolve('EV1')['health'],'STALE');self.assertEqual(self.project.last_reconciliation_reason,'EVENT_LOSS_SUSPECTED')
    def test_lease_release_and_wrong_snapshot(self):
        pin=self.project.pin()
        with self.assertRaises(TimeoutError):self.project.leased({'project_token':self.project.token,**pin,'snapshot_id':'wrong'})
        self.project.leases.pop(pin['lease_id'])
        with self.assertRaises(TimeoutError):self.project.leased({'project_token':self.project.token,**pin})
    def test_million_corpus_bounded_page_basis(self):
        make_fixture(self.root,True)
        data=capture(self.root);snapshot=build(data,99)
        self.assertEqual(sum(1 for c in data['manuscript.txt'].decode() if '\u4e00'<=c<='\u9fff')-sum(1 for c in TEXT if '\u4e00'<=c<='\u9fff'),1_000_000)
        self.assertEqual(len(snapshot.blocks),4004);self.assertEqual(len(snapshot.blocks[-20:]),20)

class HostFailures(unittest.TestCase):
    def test_source_write_and_agent_guard(self):
        code="""
import sys,tempfile,socket
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,sys.argv[1]);from host import Host
with tempfile.TemporaryDirectory() as temp:
    path=Path(temp)/'canon.txt';path.write_text('original')
    h=Host();h.project=SimpleNamespace(root=Path(temp))
    try:path.write_text('mutated');raise AssertionError('write allowed')
    except PermissionError:pass
    assert path.read_text()=='original' and h.write_attempts==1
    try:socket.create_connection(('127.0.0.1',1));raise AssertionError('network allowed')
    except PermissionError:pass
    assert h.agent_calls==1
    try:h.manifest('owner');raise AssertionError('agent assertion missing')
    except Exception as e:assert 'DETERMINISTIC_QUERY_AGENT_CALL_VIOLATION' in str(e)
    h.project=None
"""
        p=subprocess.run([sys.executable,'-B','-c',code,str(SPIKE/'service')],capture_output=True,timeout=10)
        self.assertEqual(p.returncode,0,p.stderr.decode(errors='replace'))
    def test_unsupported_version_and_legacy_stdout(self):
        request={'protocol_version':'1.0.0','request_id':'R','correlation_id':'C','method':'hello','params':{'supported_versions':['99.0.0'],'client_version':'test','max_frame_bytes':8388608}}
        p=subprocess.run([sys.executable,'-B',str(SPIKE/'service/host.py')],input=encode(request),capture_output=True,timeout=10)
        self.assertEqual(read_frame(io.BytesIO(p.stdout))['error']['code'],'UNSUPPORTED_PROTOCOL')
        # Owner stdout is redirected once for all worker threads, while raw stdout retains framing.
        code="import sys;sys.path.insert(0,sys.argv[1]);import host;print('legacy print');host.Host().run()"
        p=subprocess.run([sys.executable,'-B','-c',code,str(SPIKE/'service')],input=b'',capture_output=True,timeout=10)
        self.assertEqual(p.stdout,b'');self.assertIn(b'legacy print',p.stderr)
    def test_actual_host_malformed_frame_shutdown(self):
        for data in [b'\x00',struct.pack('>I',8388609),struct.pack('>I',1)+b'\xff']:
            p=subprocess.run([sys.executable,'-B',str(SPIKE/'service/host.py')],input=data,capture_output=True,timeout=10)
            self.assertEqual(p.returncode,0);self.assertEqual(p.stdout,b'');self.assertIn(b'fatal_frame',p.stderr)
    def test_unknown_method_fails_closed(self):
        request={'protocol_version':'1.0.0','request_id':'R','correlation_id':'C','method':'evil.exec','params':{}}
        p=subprocess.run([sys.executable,'-B',str(SPIKE/'service/host.py')],input=encode(request),capture_output=True,timeout=10)
        self.assertEqual(read_frame(io.BytesIO(p.stdout))['error']['code'],'INVALID_REQUEST')

if __name__=='__main__':
    begin=time.perf_counter();suite=unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]);result=unittest.TextTestRunner(verbosity=2).run(suite)
    output={'tests_run':result.testsRun,'failures':[str(x[0]) for x in result.failures],'errors':[str(x[0]) for x in result.errors],'passed':result.wasSuccessful(),'duration_s':time.perf_counter()-begin}
    (SPIKE/'artifacts').mkdir(exist_ok=True);(SPIKE/'artifacts/python-tests.json').write_text(json.dumps(output,indent=2),encoding='utf-8')
    raise SystemExit(0 if result.wasSuccessful() else 1)
