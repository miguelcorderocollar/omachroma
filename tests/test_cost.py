#!/usr/bin/env python3
"""Omatinta provider-reported cost tests. No live provider calls."""
import argparse
import base64
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN))
from backend import costs, history, jobs, providers, storage


class OmatintaCostTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(storage, 'DATA', self.base / 'data'))
        self.stack.enter_context(patch.object(storage, 'STOCK', self.base / 'stock'))
        self.stack.enter_context(patch.object(storage, 'USER', self.base / 'user'))
        self.stack.enter_context(patch.object(storage, 'BACKGROUNDS', self.base / 'backgrounds'))
        self.stack.enter_context(patch.object(storage, 'credentials', return_value={'FAL_KEY': 'test-key'}))
        (storage.STOCK / 'test').mkdir(parents=True)
        self.source = self.base / 'source.jpg'
        subprocess.run(['magick', '-size', '16x9', 'xc:#113355', str(self.source)], check=True)
        self.reference = self.base / 'reference.jpg'
        subprocess.run(['magick', '-size', '16x9', 'xc:#cc8844', str(self.reference)], check=True)
        self.args = argparse.Namespace(theme='test', source=str(self.source), style_refs=[str(self.reference)],
            prompt='Create an edit.', prompt_file=None, provider='fal',
            model=storage.EDIT_MODELS['fal'][0]['value'], res='1K', quality='high',
            upscaler='precision', upscale_model='Standard V2', upscale_factor=2,
            upscale_only=None, creativity=5, env_file='', repo_dir=str(self.base / 'results'),
            run=True, install=False)

    def run_capture(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            jobs.run(self.args)
        return [json.loads(line) for line in output.getvalue().splitlines()]

    def fake_edit(self, *args):
        subprocess.run(['magick', self.source, args[-1]], check=True)
        return '0.25'

    def fake_upscale(self, src, kind, model, factor, creativity, keys, dest):
        subprocess.run(['magick', self.source, 'png:' + str(dest)], check=True)
        return 0.125

    def test_cost_parser_rejects_invalid_values(self):
        self.assertEqual(costs.amount('0.125'), 0.125)
        self.assertEqual(costs.amount(0), 0.0)
        for value in (None, True, -1, float('nan'), float('inf'), 'nan', 'cost', '', 10 ** 1000):
            with self.subTest(value=repr(value)):
                self.assertIsNone(costs.amount(value))

    def test_edit_and_upscale_return_only_explicit_usage_cost(self):
        payload = base64.b64encode(b'fixture-image').decode()
        with patch.object(providers, 'request', return_value=json.dumps({
                'images': [{'url': f'data:image/png;base64,{payload}'}],
                'usage': {'cost': '0.31'}}).encode()):
            actual = providers.edit('fal', self.args.model, 'prompt', [self.source],
                                    '1K', 'high', {'FAL_KEY': 'test'}, self.base / 'edit.png')
        self.assertEqual(actual, 0.31)

        with patch.object(providers, 'request', return_value=json.dumps({
                'image': {'url': f'data:image/jpeg;base64,{payload}'},
                'usage': {'cost': 0.07}}).encode()):
            actual = providers.upscale(self.source, 'precision', 'Standard V2', 2, 5,
                                       {'FAL_KEY': 'test'}, self.base / 'upscale.jpg')
        self.assertEqual(actual, 0.07)

    def test_success_emits_and_persists_total_only_when_all_costs_are_known(self):
        with patch.object(providers, 'edit', side_effect=self.fake_edit), \
             patch.object(providers, 'upscale', side_effect=self.fake_upscale):
            events = self.run_capture()
        edited = next(event for event in events if event['state'] == 'edited')
        done = next(event for event in events if event['state'] == 'done')
        self.assertEqual(edited['cost'], {'edit': 0.25, 'upscale': None, 'total': None,
                                         'complete': False, 'upscaleRequested': True})
        self.assertEqual(done['cost'], {'edit': 0.25, 'upscale': 0.125, 'total': 0.375,
                                       'complete': True, 'upscaleRequested': True})
        saved = history.read(done['jobId'])
        self.assertEqual(saved['cost'], done['cost'])

    def test_failed_upscale_keeps_edit_cost_but_has_no_total(self):
        with patch.object(providers, 'edit', side_effect=self.fake_edit), \
             patch.object(providers, 'upscale', side_effect=ValueError('upscale failed')):
            events = self.run_capture()
        done = next(event for event in events if event['state'] == 'done')
        self.assertEqual(done['cost'], {'edit': 0.25, 'upscale': None, 'total': None,
                                        'complete': False, 'upscaleRequested': True})
        self.assertEqual(history.read(done['jobId'])['cost'], done['cost'])

    def test_cancellation_keeps_cost_reported_for_saved_edit(self):
        output = io.StringIO()
        with patch.object(providers, 'edit', side_effect=self.fake_edit), \
             patch.object(providers, 'upscale', side_effect=jobs.Cancelled('Stopped')):
            with contextlib.redirect_stdout(output), self.assertRaises(jobs.Cancelled):
                jobs.run(self.args)
        events = [json.loads(line) for line in output.getvalue().splitlines()]
        cancelled = next(event for event in events if event['state'] == 'cancelled')
        expected = {'edit': 0.25, 'upscale': None, 'total': None,
                    'complete': False, 'upscaleRequested': True}
        self.assertEqual(cancelled['cost'], expected)
        self.assertEqual(history.read(cancelled['jobId'])['cost'], expected)

    def test_no_upscaler_total_uses_edit_report_only(self):
        self.args.upscaler = 'none'
        self.args.upscale_model = ''
        with patch.object(providers, 'edit', side_effect=self.fake_edit):
            events = self.run_capture()
        done = next(event for event in events if event['state'] == 'done')
        self.assertEqual(done['cost'], {'edit': 0.25, 'upscale': None, 'total': 0.25,
                                       'complete': True, 'upscaleRequested': False})

    def test_cost_metadata_rejects_invalid_shape(self):
        job_id = history.create(name='Example')
        with self.assertRaises(ValueError):
            history.update(job_id, cost={'edit': float('nan'), 'upscale': None,
                'total': None, 'complete': False, 'upscaleRequested': False})
        valid = costs.summary(0.2, None, edit_requested=True, upscale_requested=False)
        history.update(job_id, cost=valid)
        self.assertEqual(history.read(job_id)['cost'], valid)


if __name__ == '__main__':
    unittest.main()
