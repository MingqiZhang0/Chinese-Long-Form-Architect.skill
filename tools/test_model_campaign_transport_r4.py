"""Offline test of the minimal CLI bootstrap repair; no model requests."""
import json
import subprocess
import unittest
from unittest.mock import patch
import model_campaign_r4 as repaired


class TransportRepairTest(unittest.TestCase):
    def test_reserved_provider_override_removed_settings_preserved(self):
        events = [
            {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': '测试正文'}},
            {'type': 'turn.completed', 'usage': {'output_tokens': 4}},
        ]
        process = subprocess.CompletedProcess([], 0, '\n'.join(json.dumps(e) for e in events), '')
        with patch.object(repaired.subprocess, 'run', return_value=process) as execute:
            result = repaired.cli_call({'messages': [{'content': 'TEST ONLY'}]},
                                       {'model': 'gpt-6.1-sol', 'reasoning_effort': 'low'}, 60)
        argv = execute.call_args.args[0]
        self.assertFalse(any('model_providers' in value for value in argv))
        self.assertIn('gpt-6.1-sol', argv)
        self.assertIn('model_reasoning_effort="low"', argv)
        self.assertIn('features.shell_tool=false', argv)
        self.assertIn('web_search="disabled"', argv)
        self.assertIn('mcp_servers={}', argv)
        self.assertIn('--ephemeral', argv)
        self.assertEqual(result['status'], 'SUCCESS')


if __name__ == '__main__':
    unittest.main()
