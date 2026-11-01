#!/usr/bin/env python3
"""Permanent auditability-core regressions; only temporary projects are written."""
import argparse
import copy
import json
import tempfile
import unittest
import subprocess
import shutil
import sys
import os
import contextlib
import io
from pathlib import Path

import narrative_runtime as runtime
import runtime_tx as tx
import story_ops
import reader_state
import runtime_schema
import semantic_kernel
from event_provenance import event_closure
from dependency_activity import is_edge_active

ROOT = Path(__file__).resolve().parents[1]


def planning_event(eid='E'):
    return {'event_id': eid, 'branch': 'main', 'seq': 1, 'event_type': 'fact', 'intent': 'test', 'effects': [],
            'authority': 'canonical', 'provenance': {'version': '1.0.0', 'authority': 'explicit_planning',
            'class': 'planning', 'origin_ref': 'P', 'temporal_scope': {'axis': 'story_valid', 'domain': 'day', 'from': 1}}}


def catalog():
    return {'sources': {'P': {'kind': 'planning', 'revision': 'R1', 'content_sha256': 'a' * 64}}}


class AuditabilityCore(unittest.TestCase):
    def test_A1_untimed_and_valid_interval(self):
        for row in ({'actor': 'A', 'fact': 'F'}, {'actor': 'A', 'fact': 'F', 'status': 'known'}):
            result = story_ops.knowledge_at({'knowledge_state': [row]}, 'A', 5)[0]
            self.assertEqual(result['status'], 'unknown')
            self.assertEqual(result['completeness'], 'PARTIAL')
        row = {'actor': 'A', 'fact': 'F', 'valid_from': 2, 'valid_until': 6}
        self.assertEqual(story_ops.knowledge_at({'knowledge_state': [row]}, 'A', 5)[0]['status'], 'known')
        self.assertEqual(story_ops.knowledge_at({'knowledge_state': [row]}, 'A', 6), [])

    def test_A2_retirement_and_reacquisition(self):
        state = {'knowledge_state': [{'actor': 'A', 'fact': 'F', 'acquired_at': 2, 'retired_at': 6}],
                 'knowledge_uses': [{'actor': 'A', 'fact': 'F', 'acquired': 2}]}
        self.assertEqual(story_ops.knowledge_at(state, 'A', 6), [])
        for at in (2, 5.999):
            self.assertEqual(story_ops.knowledge_at(state, 'A', at)[0]['status'], 'known')
        for at in range(6, 20):
            self.assertEqual(story_ops.knowledge_at(state, 'A', at), [])
        state['knowledge_state'].append({'actor': 'A', 'fact': 'F', 'acquired_at': 10})
        self.assertEqual(story_ops.knowledge_at(state, 'A', 10)[0]['status'], 'known')
        self.assertEqual(story_ops.knowledge_at(state, 'A', 9), [])

    def test_A3_reader_dict_boundary(self):
        state = {'reader_state': {'foreground_questions': [{'id': 'F', 'from_chapter': 12}],
                                 'gist': [{'id': 'G', 'from_chapter': 8}]}}
        old = reader_state.reader_state_at(state, 6)
        self.assertEqual(reader_state.foreground_questions(old), [])
        self.assertEqual(reader_state.gist_items(old), [])
        mid = reader_state.reader_state_at(state, 9)
        self.assertEqual(reader_state.foreground_questions(mid), [])
        self.assertEqual(len(reader_state.gist_items(mid)), 1)

    def test_A4_shared_support(self):
        rows = [{'source': a, 'target': b, 'kind': 'support'} for a, b in [('E', 'C1'), ('E', 'C2'), ('C1', 'C'), ('C2', 'C')]]
        trace = runtime.why_trace(rows, 'C')
        self.assertEqual(len(trace), 4)
        self.assertEqual(trace, runtime.why_trace(list(reversed(rows)), 'C'))
        self.assertEqual(len(runtime.why_trace(rows + [{'source': 'C', 'target': 'E'}], 'C')), 5)

    def test_A5_edge_interval(self):
        rows = [{'source': 'A', 'target': 'B'}, {'source': 'B', 'target': 'C', 'status': 'retired', 'valid_from': 1, 'retired_at': 5}, {'source': 'A', 'target': 'D'}]
        self.assertEqual({r['target'] for r in runtime.impact(rows, 'A', at=4)}, {'B', 'C', 'D'})
        self.assertEqual({r['target'] for r in runtime.impact(rows, 'A', at=5)}, {'B', 'D'})

    def test_A6_canonical_closure_gate(self):
        event = {'event_id': 'E', 'branch': 'main', 'seq': 1, 'event_type': 'fact', 'intent': 'test', 'effects': [], 'authority': 'canonical'}
        errors, _ = runtime.validate_runtime([event], {'main': {'parent': None}})
        self.assertTrue(any('PROVENANCE' in e for e in errors))

    def test_A7_payload_identity(self):
        request = {'transaction_id': 'T', 'branch': 'main', 'proposed_events': [{'event_id': 'E', 'effects': [{'op': 'set', 'path': 'fact', 'value': 1}]}]}
        committed = tx.normalized_proposed(request, [])
        self.assertEqual(tx.transaction_match_state(request, committed), 'exact')
        changed = copy.deepcopy(request)
        changed['proposed_events'][0]['effects'][0]['value'] = 2
        self.assertEqual(tx.transaction_match_state(changed, committed), 'conflict')
        reordered = json.loads(json.dumps(request, sort_keys=True))
        self.assertEqual(tx.transaction_match_state(reordered, committed), 'exact')

    def test_A1_current_is_not_history_and_event_time(self):
        row = {'actor': 'A', 'fact': 'F', 'status': 'known'}
        state = {'knowledge_state': [row]}
        self.assertEqual(story_ops.knowledge_at(state, 'A', None)[0]['status'], 'known')
        self.assertEqual(story_ops.knowledge_at(state, 'A', 5)[0]['status'], 'unknown')
        row['acquisition_event_ref'] = 'E'
        self.assertEqual(story_ops.knowledge_at(state, 'A', 5)[0]['status'], 'unknown')
        event = planning_event()
        event['story_time'] = 2
        state['events'] = [event]
        state['provenance_catalog'] = catalog()
        self.assertEqual(story_ops.knowledge_at(state, 'A', 5)[0]['status'], 'known')
        for invalid in (True, 'bad', float('inf')):
            bad = {'knowledge_state': [{'actor': 'A', 'fact': 'F', 'acquired_at': 1, 'valid_until': invalid}]}
            result = story_ops.knowledge_at(bad, 'A', 5)[0]
            self.assertEqual(result['status'], 'unknown')
            self.assertEqual(result['completeness'], 'PARTIAL')

    def test_A2_interval_aliases_permutation_and_legacy(self):
        for end in ('valid_until', 'valid_to', 'retired_at'):
            rows = [{'actor': 'A', 'fact': 'F', 'valid_from': 2, end: 5}, {'actor': 'A', 'fact': 'F', 'valid_from': 10}]
            for at in (1, 2, 4.999, 5, 8, 10, 20):
                a = story_ops.knowledge_at({'knowledge_state': rows}, 'A', at)
                b = story_ops.knowledge_at({'knowledge_state': list(reversed(rows))}, 'A', at)
                self.assertEqual(a, b)
            self.assertEqual(story_ops.knowledge_at({'knowledge_state': rows}, 'A', 8), [])
        legacy = {'knowledge_uses': [{'actor': 'A', 'fact': 'F'}]}
        self.assertEqual(story_ops.knowledge_at(legacy, 'A', 4)[0]['status'], 'unknown')
        self.assertEqual(story_ops.knowledge_at({'knowledge_state': [], **legacy}, 'A', 4), [])

    def test_A3_flashback_repeated_misdirection(self):
        state = {'reader_state': [
            {'id': 'F', 'from_chapter': 8, 'to_chapter': 11, 'story_time': 1, 'status': 'inferable', 'gist': ['weak']},
            {'id': 'F', 'from_chapter': 12, 'story_time': -10, 'status': 'explicit', 'gist': ['truth']},
            {'id': 'F', 'from_chapter': 15, 'status': 'misdirection', 'gist': ['wrong']}]}
        self.assertEqual(reader_state.reader_state_at(state, 6), [])
        self.assertEqual(reader_state.reader_state_at(state, 9)[0]['status'], 'inferable')
        self.assertEqual(reader_state.reader_state_at(state, 11)[0]['status'], 'inferable')
        self.assertEqual(reader_state.reader_state_at(state, 12)[0]['status'], 'explicit')
        self.assertEqual(reader_state.reader_state_at(state, 16)[0]['status'], 'misdirection')
        self.assertEqual(reader_state.reader_state_at(state, 16), reader_state.reader_state_at({'reader_state': list(reversed(state['reader_state']))}, 16))

    def test_A3_missing_time_unsupported_axis_and_current(self):
        state = {'reader_state': {'gist': ['untimed'], 'foreground_questions': ['future?']}}
        self.assertEqual(reader_state.reader_state_at(state), state['reader_state'])
        for axis in ('story_valid', 'revision', 'presentation'):
            result = reader_state.query_reader_state(state, reader_state.NarrativePosition(axis, 6))
            self.assertEqual(reader_state.gist_items(result['state']), [])
            self.assertEqual(result['completeness'], 'PARTIAL')
            self.assertTrue(result['gap_reasons'])
        for value in (None, {}, []):
            result = reader_state.query_reader_state({'reader_state': value}, reader_state.chapter_position(6))
            self.assertEqual(result['completeness'], 'PARTIAL')

    def test_A3_timed_snapshot_inherits_bounds(self):
        state = {'reader_state': {'from_chapter': 8, 'to_chapter': 12, 'gist': ['revealed'],
                                 'foreground_questions': [{'from_chapter': 10, 'question': 'later'}]}}
        self.assertEqual(reader_state.gist_items(reader_state.reader_state_at(state, 6)), [])
        self.assertEqual(reader_state.gist_items(reader_state.reader_state_at(state, 9)), ['revealed'])
        self.assertEqual(reader_state.foreground_questions(reader_state.reader_state_at(state, 9)), [])
        self.assertEqual(reader_state.gist_items(reader_state.reader_state_at(state, 13)), [])

    def test_A3_runtime_event_reconstruction_and_flashback(self):
        events = [
            {'event_id': 'R1', 'seq': 1, 'branch': 'main', 'chapter': 8, 'story_time': 5, 'effects': [{'op': 'set', 'path': 'reader_state.gist', 'value': ['weak']}]},
            {'event_id': 'R2', 'seq': 2, 'branch': 'main', 'chapter': 12, 'story_time': -10, 'effects': [{'op': 'set', 'path': 'reader_state.gist', 'value': ['explicit']}]},
            {'event_id': 'R3', 'seq': 3, 'branch': 'main', 'chapter': 15, 'effects': [{'op': 'delete', 'path': 'reader_state.gist'}]}]
        current, _ = runtime.replay(events, {'main': {'parent': None}}, 'main')
        state = {**current, 'events': events}
        self.assertEqual(reader_state.gist_items(reader_state.reader_state_at(state, 6)), [])
        self.assertEqual(reader_state.gist_items(reader_state.reader_state_at(state, 9)), ['weak'])
        self.assertEqual(reader_state.gist_items(reader_state.reader_state_at(state, 13)), ['explicit'])
        self.assertEqual(reader_state.gist_items(reader_state.reader_state_at(state, 16)), [])
        self.assertEqual(reader_state.reader_state_at(state, 13), reader_state.reader_state_at({**state, 'events': list(reversed(events))}, 13))
        events[0].pop('chapter')
        result = reader_state.query_reader_state(state, reader_state.chapter_position(9))
        self.assertEqual(result['completeness'], 'PARTIAL')
        self.assertIn('MISSING_READER_EVENT_TIME', result['gap_reasons'])

    def test_A4_parallel_contradiction_retired_invalid_and_gaps(self):
        rows = [{'id': 'S1', 'source': 'E', 'target': 'C', 'kind': 'support'},
                {'id': 'S2', 'source': 'E', 'target': 'C', 'kind': 'support'},
                {'id': 'X', 'source': 'X', 'target': 'C', 'kind': 'contradiction'},
                {'source': 'OLD', 'target': 'C', 'status': 'retired'},
                {'source': 'BAD', 'target': 'C', 'status': 'invalidated'}]
        result = runtime.trace_query(rows, 'C')
        self.assertEqual(len(result['edges']), 3)
        self.assertEqual(result['completeness'], 'PARTIAL')
        self.assertIn('MISSING_TERMINAL_PROVENANCE', result['gap_reasons'])
        minimal = runtime.trace_query(rows, 'C', mode='minimal')
        self.assertEqual(minimal['completeness'], 'PARTIAL')
        self.assertIn('MINIMAL_TRACE', minimal['gap_reasons'])
        self.assertEqual(runtime.why_trace(rows, 'C'), runtime.why_trace(list(reversed(rows)), 'C'))

    def test_A4_closed_terminal_and_cycle_gap(self):
        e = planning_event()
        result = runtime.trace_query([{'source': 'E', 'target': 'C'}], 'C', [e], catalog())
        self.assertEqual(result['completeness'], 'FULL')
        result = runtime.trace_query([{'source': 'E', 'target': 'C'}, {'source': 'C', 'target': 'E'}], 'C', [e], catalog())
        self.assertEqual(result['completeness'], 'PARTIAL')
        result = runtime.trace_query([{'source': 'E', 'target': 'C'}, {'source': 'X', 'target': 'C'}, {'source': 'X', 'target': 'Y'}, {'source': 'Y', 'target': 'X'}], 'C', [e], catalog())
        self.assertIn('UNTERMINATED_SUPPORT_PATH', result['gap_reasons'])

    def test_A5_all_entrypoints_permutation_and_property(self):
        for retired in range(2, 12):
            rows = [{'source': 'A', 'target': 'B'}, {'source': 'B', 'target': 'C', 'status': 'retired', 'valid_from': 1, 'retired_at': retired}, {'source': 'A', 'target': 'D'}]
            for at in (retired - .1, retired, retired + 2):
                expected = {'B', 'C', 'D'} if at < retired else {'B', 'D'}
                a = runtime.impact(rows, 'A', at=at)
                self.assertEqual({r['target'] for r in a}, expected)
                self.assertEqual(a, runtime.impact(list(reversed(rows)), 'A', at=at))
                args = argparse.Namespace(node='A', at=at, policy='active_at', dependencies=None, state=Path('nonexistent/story-state.json'), json=True)
                with contextlib.redirect_stdout(io.StringIO()) as buf:
                    story_ops.cmd_propagate({'dependencies': rows}, args)
                self.assertEqual({r['target'] for r in json.loads(buf.getvalue())}, expected)
                why = runtime.why_trace(rows, 'C', at=at)
                self.assertEqual(bool(why), at < retired)
        self.assertEqual(len(runtime.impact(rows, 'A', policy='historical_all')), 3)
        self.assertFalse(is_edge_active({'status': 'retired'}, 3))
        self.assertFalse(is_edge_active({'valid_from': 'broken'}, 3))
        edge = {'axis': 'presentation', 'domain': 'chapter', 'valid_from': 8, 'valid_until': 12}
        self.assertFalse(is_edge_active(edge, 9))
        self.assertTrue(is_edge_active(edge, reader_state.NarrativePosition('presentation', 9)))
        self.assertFalse(is_edge_active(edge, reader_state.NarrativePosition('story_valid', 9)))

    def test_A5_replay_dependency_lifecycle_view(self):
        events = [{'event_id': 'E1', 'seq': 1, 'branch': 'main', 'effects': [{'op': 'set', 'path': 'dependencies', 'value': [
            {'source': 'A', 'target': 'B'}, {'source': 'B', 'target': 'C', 'status': 'retired'}]}]}]
        state, _ = runtime.replay(events, {'main': {'parent': None}}, 'main')
        self.assertEqual([r['target'] for r in runtime.impact(state['dependencies'], 'A')], ['B'])

    def test_A6_planning_and_legacy_strict_audit(self):
        e = planning_event()
        self.assertEqual(event_closure(e, {'E': e}, catalog())['provenance_status'], 'CLOSED')
        self.assertEqual(runtime.validate_runtime([e], {'main': {'parent': None}}, provenance=catalog())[0], [])
        self.assertEqual(event_closure(e)['provenance_status'], 'BROKEN')
        legacy = {k: v for k, v in e.items() if k not in {'authority', 'provenance'}}
        self.assertEqual(event_closure(legacy)['provenance_status'], 'UNRESOLVED')
        self.assertEqual(runtime.validate_runtime([legacy], {'main': {'parent': None}})[0], [])
        self.assertTrue(runtime.validate_runtime([legacy], {'main': {'parent': None}}, strict_audit=True)[0])
        for field in ('authority', 'origin_ref', 'temporal_scope'):
            bad = copy.deepcopy(e)
            del bad['provenance'][field]
            self.assertNotEqual(event_closure(bad, {'E': bad}, catalog())['provenance_status'], 'CLOSED')

    def test_A6_manuscript_closure(self):
        e = planning_event()
        e['provenance'].update({'class': 'manuscript', 'origin_ref': 'EV'})
        c = {'evidence': {'EV': {'anchor_ref': 'A'}}, 'anchors': {'A': {'source_revision_ref': 'S', 'span': [0, 8], 'content_sha256': 'a'*64}},
             'source_revisions': {'S': {'kind': 'manuscript', 'revision': 'R1', 'content_sha256': 'a'*64}}}
        self.assertEqual(event_closure(e, {'E': e}, c)['provenance_status'], 'CLOSED')
        for table in ('evidence', 'anchors', 'source_revisions'):
            broken = copy.deepcopy(c)
            broken[table] = {}
            self.assertEqual(event_closure(e, {'E': e}, broken)['provenance_status'], 'BROKEN')
        c['anchors']['A']['status'] = 'broken'
        self.assertEqual(event_closure(e, {'E': e}, c)['provenance_status'], 'BROKEN')
        c['anchors']['A']['status'] = 'valid'
        c['anchors']['A']['content_sha256'] = 'not-a-fingerprint'
        self.assertNotEqual(event_closure(e, {'E': e}, c)['provenance_status'], 'CLOSED')

    def test_A6_confirmation_import_migration_derived(self):
        for kind in ('user_confirmed', 'imported', 'migration'):
            e = planning_event()
            e['provenance'].update({'class': kind, 'origin_ref': 'O'})
            c = {'confirmations': {'O': {'confirmed': True, 'canon_ref': 'F', 'confirmed_by': 'user'}},
                 'sources': {'O': {'kind': kind, 'revision': 'R1', 'content_sha256': 'a'*64}}}
            self.assertEqual(event_closure(e, {'E': e}, c)['provenance_status'], 'CLOSED')
            if kind == 'user_confirmed':
                c['confirmations']['O']['confirmed_by'] = True
                self.assertNotEqual(event_closure(e, {'E': e}, c)['provenance_status'], 'CLOSED')
        parent = planning_event('PARENT')
        e = planning_event()
        e['provenance'].update({'class': 'derived', 'origin_ref': 'RULE', 'derived_from': ['PARENT'], 'rule_version': '1'})
        c = catalog()
        c['rules'] = {'RULE': {'version': '1', 'deterministic': True}}
        self.assertEqual(event_closure(e, {'E': e, 'PARENT': parent}, c)['provenance_status'], 'CLOSED')
        self.assertEqual(event_closure(e, {'E': e}, c)['provenance_status'], 'BROKEN')
        e['provenance']['derived_from'] = ['E']
        self.assertEqual(event_closure(e, {'E': e}, c)['provenance_status'], 'BROKEN')

    def test_A6_schema_extension_and_legacy_upcaster(self):
        schema = ROOT/'assets/runtime-schemas/event.schema.json'
        e = planning_event()
        self.assertEqual(runtime_schema.validate_instance(e, schema), [])
        del e['provenance']
        self.assertTrue(runtime_schema.validate_instance(e, schema))
        del e['authority']
        old = copy.deepcopy(e)
        self.assertEqual(runtime_schema.validate_instance(runtime_schema.normalize_legacy_event(e), schema), [])
        self.assertEqual(e, old)
        self.assertNotIn('provenance', runtime_schema.normalize_legacy_event(e))

    def test_A6_schema_project_owner_and_missing_catalog(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = {'runtime_schema_version': '3.0.0', 'schema_dialect': runtime_schema.DIALECT,
                        'project_id': 'TEST', 'current_branch': 'main', 'compatibility_policy': 'backward',
                        'paths': {'events': 'events.jsonl', 'branches': 'branches.json', 'dependencies': 'dependencies.json', 'provenance': 'provenance.json'}}
            mp = root/'manifest.json'
            mp.write_text(json.dumps(manifest), encoding='utf-8')
            (root/'branches.json').write_text(json.dumps({'schema_version': '3.0.0', 'branches': {'main': {'parent': None, 'fork_event': None, 'status': 'active', 'purpose': 'test'}}}), encoding='utf-8')
            (root/'dependencies.json').write_text(json.dumps({'schema_version': '3.0.0', 'edges': []}), encoding='utf-8')
            (root/'events.jsonl').write_text(json.dumps(planning_event())+'\n', encoding='utf-8')
            (root/'provenance.json').write_text(json.dumps(catalog()), encoding='utf-8')
            self.assertEqual(runtime_schema.validate_project(root, mp, runtime_schema.DEFAULT_SCHEMA_DIR)[0], [])
            kernel_rows = []
            project = {'project_id': 'TEST', 'current_branch': 'main', 'enabled_subsystems': ['narrative-runtime'], 'canonical_paths': {'runtime_manifest': 'manifest.json'}}
            self.assertTrue(semantic_kernel.verify_runtime(root, project, kernel_rows).get('events'), kernel_rows)
            (root/'provenance.json').unlink()
            self.assertTrue(runtime_schema.validate_project(root, mp, runtime_schema.DEFAULT_SCHEMA_DIR)[0])
            e = planning_event()
            del e['authority']; del e['provenance']
            (root/'events.jsonl').write_text(json.dumps(e)+'\n', encoding='utf-8')
            errors, warnings = runtime_schema.validate_project(root, mp, runtime_schema.DEFAULT_SCHEMA_DIR)
            self.assertEqual(errors, [])
            self.assertTrue(any('LEGACY_UNCLOSED' in w for w in warnings))
    def test_A7_commit_crash_reload_retry_and_promotion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            events, branches = root/'events.jsonl', root/'branches.json'
            branches.write_text(json.dumps({'main': {'parent': None}}), encoding='utf-8')
            e = planning_event()
            request = {'schema_version': '3.0.0', 'transaction_id': 'T', 'branch': 'main', 'expected_head_event': None,
                       'expected_effective_revision': 0, 'proposed_events': [e], 'status': 'proposed'}
            with self.assertRaisesRegex(tx.TxError, 'PROVENANCE'):
                tx.preflight(events, branches, request, None)
            unmarked = copy.deepcopy(request)
            del unmarked['proposed_events'][0]['authority']
            del unmarked['proposed_events'][0]['provenance']
            with self.assertRaisesRegex(tx.TxError, 'PROVENANCE'):
                tx.preflight(events, branches, unmarked, None, catalog())
            _, _, proposed = tx.preflight(events, branches, request, None, catalog())
            tx.atomic_append_jsonl(events, proposed)  # crash before updating transaction file
            env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
            transaction = root/'transaction.json'
            transaction.write_text(json.dumps(request), encoding='utf-8')
            provenance = root/'provenance.json'
            provenance.write_text(json.dumps(catalog()), encoding='utf-8')
            command = [sys.executable, str(ROOT/'scripts/runtime_tx.py'), 'commit', '--events', str(events), '--branches', str(branches), '--transaction', str(transaction), '--provenance', str(provenance)]
            before = events.read_bytes()
            first = subprocess.run(command, env=env, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            receipt = json.loads(first.stdout)
            self.assertEqual(receipt, {'status': 'committed', 'events': ['E'], 'head_event': 'E', 'effective_revision': 1})
            second = subprocess.run(command, env=env, capture_output=True, text=True)
            self.assertEqual(json.loads(second.stdout), receipt)
            self.assertEqual(events.read_bytes(), before)
            retry = json.loads(transaction.read_text(encoding='utf-8'))
            retry['retry_metadata'] = {'attempt': 3}
            self.assertEqual(tx.transaction_match_state(retry, runtime.load_jsonl(events)), 'exact')
            for change in ('purpose', 'branch', 'expected_head_event'):
                bad = copy.deepcopy(retry)
                bad[change] = 'different'
                self.assertEqual(tx.transaction_match_state(bad, runtime.load_jsonl(events)), 'conflict')
            retry['proposed_events'][0]['intent'] = 'different'
            transaction.write_text(json.dumps(retry), encoding='utf-8')
            bad = subprocess.run(command, env=env, capture_output=True, text=True)
            self.assertNotEqual(bad.returncode, 0)
            self.assertIn('IDEMPOTENCY_CONFLICT', bad.stderr)
            self.assertEqual(events.read_bytes(), before)
            state, _ = runtime.replay(runtime.load_jsonl(events), {'main': {'parent': None}}, 'main')
            self.assertEqual(state, {})

    def test_A7_new_identity_legacy_and_stable_digest(self):
        request = {'transaction_id': 'T', 'branch': 'main', 'proposed_events': [{'event_id': 'E', 'effects': []}]}
        events = tx.normalized_proposed(request, [])
        new = copy.deepcopy(request)
        new['transaction_id'] = 'NEW'
        self.assertEqual(tx.transaction_match_state(new, events), 'absent')
        legacy = copy.deepcopy(events)
        del legacy[0]['transaction_payload_sha256']
        self.assertEqual(tx.transaction_match_state(request, legacy), 'conflict')
        for key in ('diagnostics', 'retry_metadata', 'timestamp', 'correlation_id'):
            same = copy.deepcopy(request)
            same[key] = 'extra'
            self.assertEqual(tx.transaction_payload_hash(same), tx.transaction_payload_hash(request))
        code = "import runtime_tx,json; print(runtime_tx.transaction_payload_hash(json.loads(input())))"
        env = {**os.environ, 'PYTHONPATH': str(ROOT/'scripts'), 'PYTHONDONTWRITEBYTECODE': '1'}
        proc = subprocess.run([sys.executable, '-c', code], input=json.dumps(request), text=True, capture_output=True, env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), tx.transaction_payload_hash(request))


def mutation_tests():
    """Run source mutants only in isolated copies, and require the oracle to fail."""
    mutants = [
        ('A1', 'story_ops.py', '"unknown" if at is not None and (acquired is None or invalid_time) else rec.get("status", "known")', 'rec.get("status", "known")', 'test_A1_untimed_and_valid_interval'),
        ('A2', 'story_ops.py', 'if "knowledge_state" not in state:', 'if not rows:', 'test_A2_retirement_and_reacquisition'),
        ('A3', 'reader_state.py', 'return query_reader_state(state, position)["state"]', 'return data', 'test_A3_reader_dict_boundary'),
        ('A4', 'narrative_runtime.py', 'source = str(edge.get("source"))\n            result.append', 'source = str(edge.get("source"))\n            if source in seen:\n                continue\n            result.append', 'test_A4_shared_support'),
        ('A5', 'dependency_activity.py', 'status = str(edge.get("status", "active"))', 'status = str(edge.get("status", "active"))\n    if status == "retired":\n        return True', 'test_A5_edge_interval'),
        ('A6', 'narrative_runtime.py', 'if canonical_event(e) or strict_audit:', 'if False:', 'test_A6_canonical_closure_gate'),
        ('A7', 'runtime_tx.py', 'return "exact" if all(e.get("transaction_identity_version") == "1.0.0" and e.get("transaction_payload_sha256") == digest for e in committed) else "conflict"', 'return "exact"', 'test_A7_payload_identity'),
    ]
    results = []
    for gap, file, before, after, method in mutants:
        with tempfile.TemporaryDirectory(prefix='auditability-mutant-') as directory:
            root = Path(directory)
            shutil.copytree(ROOT/'scripts', root/'scripts', ignore=shutil.ignore_patterns('__pycache__'))
            path = root/'scripts'/file
            source = path.read_text(encoding='utf-8')
            if source.count(before) != 1:
                raise AssertionError(f'{gap}: mutation anchor is not unique')
            path.write_text(source.replace(before, after), encoding='utf-8')
            env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
            proc = subprocess.run([sys.executable, str(root/'scripts/auditability_core_test.py'), 'AuditabilityCore.'+method], capture_output=True, text=True, env=env)
            killed = proc.returncode != 0 and ('FAIL:' in proc.stderr or 'ERROR: test_' in proc.stderr)
            results.append({'gap': gap, 'killed': killed, 'oracle': method})
            if not killed:
                raise AssertionError(f'{gap} mutant survived: {proc.stdout} {proc.stderr}')
    print(json.dumps({'mutants': results, 'killed': len(results)}, indent=2))


if __name__ == '__main__':
    if '--mutations' in sys.argv:
        mutation_tests()
    elif '--smoke' in sys.argv:
        names = ['test_A1_untimed_and_valid_interval', 'test_A2_retirement_and_reacquisition', 'test_A3_reader_dict_boundary', 'test_A4_shared_support', 'test_A5_edge_interval', 'test_A6_canonical_closure_gate', 'test_A7_payload_identity']
        result = unittest.TextTestRunner().run(unittest.TestSuite(AuditabilityCore(n) for n in names))
        raise SystemExit(not result.wasSuccessful())
    else:
        unittest.main()
