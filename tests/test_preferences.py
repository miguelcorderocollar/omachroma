"""Upscale opt-in and remembered picker locations, without provider requests."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend import picker, storage

class PreferenceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name); self.data = self.root / 'data'; self.home = self.root / 'home'
        (self.home / 'Pictures').mkdir(parents=True)
        for name, value in [('DATA',self.data),('HOME',self.home)]:
            context = patch.object(storage,name,value); context.start(); self.addCleanup(context.stop)
        env = patch.dict('os.environ',{},clear=True); env.start(); self.addCleanup(env.stop)

    def test_new_install_requires_upscale_opt_in(self):
        self.assertFalse(storage.config()['upscaleEnabled'])
        self.assertEqual(storage.config()['upscaler'],'seedvr')

    def test_legacy_engine_preference_is_preserved(self):
        self.assertTrue(storage.normalize_config({'upscaler':'seedvr'})['upscaleEnabled'])
        self.assertFalse(storage.normalize_config({'upscaler':'none'})['upscaleEnabled'])
        self.assertFalse(storage.normalize_config({'upscaler':'seedvr','upscaleEnabled':False})['upscaleEnabled'])
        self.assertFalse(storage.normalize_config({'upscaleEnabled':'false'})['upscaleEnabled'])

    def test_removing_fal_key_persists_disabled_preference(self):
        storage.save_key('fal','fixture')
        storage.atomic_write(self.data/'config.json',json.dumps({'upscaleEnabled':True,'upscaler':'seedvr'}))
        storage.remove_key('fal')
        self.assertFalse(storage.config()['upscaleEnabled'])
        self.assertEqual(storage.config()['upscaler'],'seedvr')

    def test_picker_remembers_image_and_export_folders_separately(self):
        images=self.root/'images'; export=self.root/'export'; images.mkdir(); export.mkdir()
        picker.remember(images/'source.jpg','images'); picker.remember(export/'result.png','export')
        self.assertEqual(picker.folder('images'),images)
        self.assertEqual(picker.folder('export'),export)
        self.assertEqual((self.data/'picker.json').stat().st_mode & 0o777,0o600)

    def test_invalid_or_missing_picker_state_falls_back(self):
        self.data.mkdir()
        for value in ('[]','{"images":[]}','{"images":"/no/such/folder"}','broken'):
            (self.data/'picker.json').write_text(value)
            self.assertEqual(picker.folder('images'),self.home/'Pictures')

if __name__ == '__main__': unittest.main()
