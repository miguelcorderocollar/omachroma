#!/usr/bin/env python3
"""Omatinta history tests. No network calls, credentials or billed requests."""
import argparse
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
from backend import history, jobs, storage, providers


class OmatintaHistoryTests(unittest.TestCase):
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
        self.stack.enter_context(patch.object(storage, 'credentials', return_value={'FAL_KEY': 'fixture-secret'}))
        (storage.STOCK / 'test').mkdir(parents=True)
        self.source = self.base / 'source.jpg'
        subprocess.run(['magick', '-size', '16x9', 'xc:#113355', str(self.source)], check=True)
        self.reference = self.base / 'reference.jpg'
        subprocess.run(['magick', '-size', '16x9', 'xc:#cc8844', str(self.reference)], check=True)
        self.args = argparse.Namespace(theme='test', source=str(self.source), style_refs=[str(self.reference)],
            prompt='Do not persist this private prompt.', prompt_file=None, provider='fal',
            model=storage.EDIT_MODELS['fal'][0]['value'], res='1K', quality='high',
            upscaler='none', upscale_model='', upscale_factor=2, upscale_only=None,
            creativity=5, env_file='', repo_dir=str(self.base / 'results'), run=True, install=False)

    def capture_run(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            jobs.run(self.args)
        return [json.loads(line) for line in output.getvalue().splitlines()]

    def fake_edit(self, *args):
        subprocess.run(['magick', self.source, args[-1]], check=True)
        return 0.05

    def test_real_success_persists_secure_metadata_and_job_id(self):
        with patch.object(providers, 'edit', side_effect=self.fake_edit):
            events = self.capture_run()
        job_id = events[0]['jobId']
        record = history.read(job_id)
        self.assertEqual(record['status'], 'done')
        self.assertEqual(record['provider'], 'fal')
        self.assertEqual(record['model'], self.args.model)
        self.assertEqual(record['theme'], 'test')
        self.assertEqual(record['sourcePath'], str(self.source))
        self.assertTrue(Path(record['resultPath']).is_file())
        self.assertTrue(all(event['jobId'] == job_id for event in events))
        metadata = storage.DATA / 'history' / job_id / 'job.json'
        self.assertEqual(metadata.stat().st_mode & 0o777, 0o600)
        self.assertEqual((metadata.parent.stat().st_mode & 0o777), 0o700)
        serialized = metadata.read_text()
        self.assertNotIn('fixture-secret', serialized)
        self.assertNotIn(self.args.prompt, serialized)
        self.assertEqual(history.latest(), record)

    def test_failed_real_attempt_is_recorded(self):
        output = io.StringIO()
        with patch.object(providers, 'edit', side_effect=ValueError('provider failed safely')):
            with contextlib.redirect_stdout(output), self.assertRaisesRegex(ValueError, 'provider failed'):
                jobs.run(self.args)
        events = [json.loads(line) for line in output.getvalue().splitlines()]
        job_id = events[0]['jobId']
        record = history.read(job_id)
        self.assertEqual(record['status'], 'failed')
        self.assertEqual(record['error'], 'provider failed safely')
        self.assertTrue(any(item['state'] == 'failed' for item in events))

    def test_upscale_failure_keeps_saved_edit_in_history(self):
        self.args.upscaler = 'precision'
        self.args.upscale_model = 'Standard V2'
        with patch.object(providers, 'edit', side_effect=self.fake_edit), \
             patch.object(providers, 'upscale', side_effect=ValueError('upscaler unavailable')):
            events = self.capture_run()
        record = history.read(events[0]['jobId'])
        self.assertEqual(record['status'], 'done')
        self.assertTrue(record['resultExists'])
        self.assertTrue(record['resultPath'].endswith('wallpaper.jpg'))
        self.assertIn('upscaling failed', record['message'])

    def test_cancelled_attempt_is_persisted(self):
        output = io.StringIO()
        with patch.object(jobs, '_run', side_effect=jobs.Cancelled('Stopped by request')):
            with contextlib.redirect_stdout(output), self.assertRaises(jobs.Cancelled):
                jobs.run(self.args)
        events = [json.loads(line) for line in output.getvalue().splitlines()]
        record = history.read(events[0]['jobId'])
        self.assertEqual(record['status'], 'cancelled')
        self.assertEqual(record['error'], 'Stopped by request')

    def test_cancellation_during_upscale_preserves_edit_and_remains_cancelled(self):
        self.args.upscaler = 'precision'; self.args.upscale_model = 'Standard V2'
        output = io.StringIO()
        with patch.object(providers, 'edit', side_effect=self.fake_edit), \
             patch.object(providers, 'upscale', side_effect=jobs.Cancelled('Stopped during upscale')):
            with contextlib.redirect_stdout(output), self.assertRaises(jobs.Cancelled):
                jobs.run(self.args)
        events = [json.loads(line) for line in output.getvalue().splitlines()]
        record = history.read(events[0]['jobId'])
        self.assertEqual(record['status'], 'cancelled')
        self.assertTrue(record['resultExists'])
        self.assertTrue(record['resultPath'].endswith('edited.png'))
        self.assertNotIn('done', [event['state'] for event in events])

    def test_corrupt_entries_and_traversal_are_ignored_or_rejected(self):
        root = storage.DATA / 'history'
        root.mkdir(parents=True)
        corrupt = root / 'corrupt'
        corrupt.mkdir()
        (corrupt / 'job.json').write_text('{broken')
        outside = self.base / 'outside'
        outside.mkdir()
        (outside / 'job.json').write_text('{"status":"done"}')
        (root / 'linked').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            history.read('../outside')
        self.assertEqual(history.listing(), [])
        self.assertIsNone(history.read('corrupt'))

    def test_previous_result_is_imported_lazily(self):
        old = storage.DATA / 'results' / 'test' / '20260203-040506-abc12345' / 'wallpaper.jpg'
        old.parent.mkdir(parents=True)
        subprocess.run(['magick', '-size', '16x9', 'xc:#315577', str(old)], check=True)
        os.utime(old, (1_700_000_000, 1_700_000_000))
        self.assertFalse((storage.DATA / 'history').exists())
        records = history.listing()
        self.assertTrue((storage.DATA / 'history').exists())
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['status'], 'done')
        self.assertEqual(records[0]['theme'], 'test')
        self.assertEqual(records[0]['resultPath'], str(old.resolve()))
        self.assertTrue(records[0]['date'].startswith('2023-11-14T22:13:20'))

    def test_legacy_folder_prefers_final_and_imports_only_once(self):
        folder = storage.DATA / 'results' / 'test' / 'job-one'
        folder.mkdir(parents=True)
        edited = folder / 'edited.png'
        final = folder / 'wallpaper.jpg'
        subprocess.run(['magick', '-size', '16x9', 'xc:#315577', str(edited)], check=True)
        subprocess.run(['magick', '-size', '16x9', 'xc:#773355', str(final)], check=True)
        first = history.listing()
        second = history.listing()
        self.assertEqual(len(first), 1)
        self.assertEqual(len(second), 1)
        self.assertEqual(first[0]['resultPath'], str(final.resolve()))
        self.assertEqual(first[0]['id'], second[0]['id'])

    def test_modern_result_is_not_reimported_as_legacy(self):
        self.args.repo_dir = str(storage.DATA / 'results')
        with patch.object(providers, 'edit', side_effect=self.fake_edit):
            events = self.capture_run()
        records = history.listing()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['id'], events[0]['jobId'])

    def test_malformed_string_fields_and_oversized_records_are_skipped(self):
        root = storage.DATA / 'history'
        wrong_type = root / 'wrong-type'
        wrong_type.mkdir(parents=True)
        (wrong_type / 'job.json').write_text(json.dumps({
            'status': 'done', 'resultPath': 123, 'name': 'Invalid'}))
        oversized = root / 'oversized'
        oversized.mkdir()
        (oversized / 'job.json').write_bytes(b'{"status":"done","message":"' + b'x' * (128 * 1024) + b'"}')
        self.assertIsNone(history.read('wrong-type'))
        self.assertIsNone(history.read('oversized'))
        self.assertEqual(history.listing(), [])

    def test_old_history_is_retained_beyond_listing_limit(self):
        ids = [history.create(name=f'wallpaper-{number}') for number in range(105)]
        listed = history.listing(limit=500)
        self.assertEqual(len(listed), 100)
        self.assertIsNotNone(history.read(ids[0]))
        self.assertTrue((storage.DATA / 'history' / ids[0] / 'job.json').is_file())

    def test_dry_run_remains_unrecorded(self):
        self.args.run = False
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            jobs.run(self.args)
        event = json.loads(output.getvalue())
        self.assertEqual(event['state'], 'dry-run')
        self.assertNotIn('jobId', event)
        self.assertFalse((storage.DATA / 'history').exists())


if __name__ == '__main__':
    unittest.main()
