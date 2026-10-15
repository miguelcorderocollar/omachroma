#!/usr/bin/env python3
"""Local export and persisted preview checks. No real chooser or provider calls."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN))
from backend import export, history, storage


class ExportTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root / 'source.jpg'
        subprocess.run(['magick', '-size', '16x9', 'xc:#315577', str(self.source)], check=True)
        self.original = self.source.read_bytes()

    def test_save_copy_keeps_original_and_returns_destination(self):
        target = self.root / 'chosen-name.jpg'
        with patch.object(export, 'choose_destination', return_value=target):
            value = export.save_image(self.source)
        self.assertEqual(value, {'path': str(target), 'cancelled': False})
        self.assertEqual(target.read_bytes(), self.original)
        self.assertEqual(self.source.read_bytes(), self.original)

    def test_cancel_does_not_write_an_export(self):
        before = set(self.root.iterdir())
        with patch.object(export, 'choose_destination', return_value=None):
            self.assertEqual(export.save_image(self.source), {'cancelled': True})
        self.assertEqual(set(self.root.iterdir()), before)

    def test_changed_extension_converts_actual_format(self):
        target = self.root / 'chosen-name.png'
        export.copy_image(self.source, target)
        self.assertTrue(target.read_bytes().startswith(b'\x89PNG'))
        self.assertEqual(self.source.read_bytes(), self.original)

    def test_symlink_is_rejected_and_existing_file_survives_failure(self):
        target = self.root / 'existing.png'
        target.write_bytes(b'keep me')
        link = self.root / 'link.png'; link.symlink_to(target)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            export.copy_image(self.source, link)
        with patch.object(export.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1)):
            with self.assertRaisesRegex(ValueError, 'convert'):
                export.copy_image(self.source, target)
        self.assertEqual(target.read_bytes(), b'keep me')
        self.assertEqual(self.source.read_bytes(), self.original)

    def test_selected_preview_and_clear_survive_snapshot_without_deleting_history(self):
        with patch.object(storage, 'DATA', self.root / 'data'), patch.object(storage, 'credentials', return_value={}), patch.object(storage, 'themes', return_value=[]):
            older = history.create(name='Older')
            history.update(older, status='done', message='First status', resultPath=str(self.source))
            newer = history.create(name='Newer')
            history.update(newer, status='failed', error='Provider rate limit', message='Job failed')
            storage.remember_job(newer)
            snapshot = storage.snapshot()
            self.assertEqual(snapshot['lastJob']['id'], newer)
            self.assertEqual(snapshot['lastJob']['previousResultPath'], str(self.source))
            storage.remember_job(older)
            self.assertEqual(storage.snapshot()['lastJob']['message'], 'First status')
            storage.remember_job(None)
            self.assertIsNone(storage.snapshot()['lastJob'])
            self.assertEqual(len(history.listing()), 2)
            self.assertTrue(self.source.is_file())
            current = storage.DATA / 'current-job.json'
            self.assertEqual(current.stat().st_mode & 0o777, 0o600)
            current.write_text(json.dumps(['invalid']))
            self.assertIsNotNone(storage.snapshot()['lastJob'])


if __name__ == '__main__':
    unittest.main()
