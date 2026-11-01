"""Transport/integrity tests. Mock responses are never campaign evidence."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import shutil
from unittest.mock import patch
import model_campaign as campaign


class CampaignTests(unittest.TestCase):
    def call(self, events):
        process = subprocess.CompletedProcess([], 0, '\n'.join(json.dumps(e) for e in events), '')
        with patch.object(campaign.subprocess, 'run', return_value=process):
            return campaign.cli_call({'messages': [{'content': 'test'}]}, {'model': 'test-only', 'reasoning_effort': 'low'}, 1)

    def test_recovery_is_not_semantic_failure(self):
        result = self.call([{'type': 'error', 'message': 'reconnecting'},
            {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': '原始输出'}},
            {'type': 'turn.completed', 'usage': {'output_tokens': 4}}])
        self.assertEqual(result['status'], 'SUCCESS')
        self.assertEqual(result['output'], '原始输出')

    def test_missing_completion_is_execution_error(self):
        self.assertEqual(self.call([{'type': 'error', 'message': 'timeout'}])['status'], 'EXECUTION_ERROR')

    def test_tool_activity_invalidates_context(self):
        result = self.call([{'type': 'item.completed', 'item': {'type': 'command_execution'}},
            {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'output'}}, {'type': 'turn.completed'}])
        self.assertEqual(result['status'], 'INVALID_OUTPUT')

    def test_unicode_and_immutable_output(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            campaign.write(root / 'campaign-freeze.json', {'source_hash': 'TEST ONLY'})
            request = {'request_id': 'drafting/test', 'messages': []}
            config = {'provider': 'mock-test-only', 'model': 'test', 'reasoning_effort': 'low'}
            response = {'status': 'SUCCESS', 'output': '一盏灯。\n\n没有第二句解释。'}
            campaign.persist(root, request, config, response, 1, campaign.now(), 'test-only')
            saved = campaign.rows(root / 'target/target-results.jsonl')[0]
            self.assertEqual(saved['output'], response['output'])
            with self.assertRaises(ValueError):
                campaign.persist(root, request, config, response, 1, campaign.now(), 'test-only')

    def test_freeze_detects_configuration_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            campaign.write(root / 'campaign-config.json', {'model': 'a'})
            campaign.write(root / 'campaign-manifest.json', {'status': 'FROZEN'})
            campaign.write(root / 'campaign-freeze.json', {'files': {}, 'campaign_files': {'campaign-config.json': campaign.digest((root / 'campaign-config.json').read_bytes())}})
            campaign.verify(root)
            campaign.write(root / 'campaign-config.json', {'model': 'b'})
            with self.assertRaises(ValueError):
                campaign.verify(root)
            self.assertEqual(campaign.read(root / 'campaign-manifest.json')['status'], 'INVALID')

    def setup_campaign(self, root):
        source = campaign.ROOT / 'docs/model-campaign-results/multi-regime-real-model-qualification-20261005-R2/logs'
        (root / 'logs').mkdir()
        for filename in ('fast-clean.json', 'core-clean.json', 'qualification-preflight.json'):
            shutil.copyfile(source / filename, root / 'logs' / filename)
        campaign.prepare(root)

    def test_absence_of_results_is_unknown_not_zero(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.setup_campaign(root)
            summary = campaign.summarize(root)
            self.assertEqual(summary['successful_executions'], 0)
            self.assertEqual(summary['per_stage']['drafting']['verdicts'], {'NOT RUN': 12})
            self.assertIsNone(summary['contamination_incidence'])
            matrix = campaign.read(root / 'aggregates/run_1/contamination-matrix.json')
            self.assertTrue(all(v['affected_task_count'] is None for f in matrix.values() for v in f['classes'].values()))

    def test_calibration_orientation_matches_canonical_builder(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.setup_campaign(root)
            keys = campaign.rows(root / 'private/calibration-key.jsonl')
            for stage in campaign.STAGES:
                campaign.select_stage(stage)
                candidates = root / 'test-only-controls' / stage
                candidates.mkdir(parents=True)
                for fid in campaign.oracle.fixture_names():
                    oracle = campaign.oracle.fixture_oracle(fid)
                    (candidates / (fid + '.md')).write_text(campaign.oracle.read_ref(fid, oracle, 'positive_control'), encoding='utf-8')
                blind, key = root / 'test-only-blind.jsonl', root / 'test-only-key.jsonl'
                campaign.oracle.build_blind(candidates, blind, key, 0)
                mapping = {r['item_id']: r for r in campaign.rows(key)}
                for row in [r for r in keys if r['stage'] == stage]:
                    self.assertEqual(row['left_role'], mapping[row['item_id']]['left_role'])
                    self.assertEqual(row['right_role'], mapping[row['item_id']]['right_role'])

    def test_target_message_excludes_oracle_transport_fields(self):
        task = campaign.rows(campaign.ROOT / 'docs/multi-regime-results/drafting-generation.jsonl')[0]
        request = campaign.target_request(Path('.'), 'drafting', task)
        content = json.loads(request['messages'][1]['content'])
        self.assertEqual(set(content), {'project_poetics', 'task', 'input'})
        self.assertNotIn('fixture_oracle_sha256', request['messages'][1]['content'])


if __name__ == '__main__':
    unittest.main()
