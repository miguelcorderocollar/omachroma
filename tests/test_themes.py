#!/usr/bin/env python3
"""Theme saves target user theme folders and never change the desktop."""
from pathlib import Path
import sys,tempfile,subprocess,unittest
from unittest.mock import patch
PLUGIN=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PLUGIN))
from backend import themes,storage,history
class ThemeTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.root=Path(self.temp.name)
  for name,value in [('DATA',self.root/'data'),('BACKGROUNDS',self.root/'backgrounds')]:
   p=patch.object(storage,name,value);p.start();self.addCleanup(p.stop)
  p=patch.object(storage,'themes',return_value=['nord','other']);p.start();self.addCleanup(p.stop)
  self.source=self.root/'20261012-211550-76cad1d4'/'wallpaper.jpg';self.source.parent.mkdir()
  subprocess.run(['magick','-size','16x9','xc:#315577',str(self.source)],check=True)
  self.current=self.root/'current-background';self.current.symlink_to(self.source)
 def test_save_selected_theme_without_current_background_change(self):
  before=self.current.readlink()
  value=themes.save_image(self.source,'nord')
  self.assertEqual(Path(value['installedPath']).parent,storage.BACKGROUNDS/'nord')
  self.assertEqual(self.current.readlink(),before)
  self.assertEqual(Path(value['installedPath']).read_bytes(),self.source.read_bytes())
  self.assertEqual(themes.save_image(self.source,'nord'),value)
  self.assertFalse((storage.BACKGROUNDS/'other').exists())
 def test_invalid_theme_and_symlink_directory_rejected(self):
  with self.assertRaises(ValueError):themes.save_image(self.source,'../other')
  storage.BACKGROUNDS.mkdir()
  (storage.BACKGROUNDS/'nord').symlink_to(self.root,target_is_directory=True)
  with self.assertRaisesRegex(ValueError,'symlink'):themes.save_image(self.source,'nord')
 def test_history_recovers_installed_path_for_older_result(self):
  ident=history.create(name='Older',theme='nord')
  history.update(ident,status='done',resultPath=str(self.source))
  saved=themes.save_image(self.source,'nord')
  value=history.read(ident)
  self.assertEqual(value['installedPath'],saved['installedPath'])
  self.assertEqual(value['installedTheme'],'nord')
 def test_legacy_wallpaper_names_stay_recognized_after_rename(self):
  saved=Path(themes.save_image(self.source,'nord')['installedPath'])
  for legacy_prefix in ('01-omachroma-','01-omapaper-'):
   legacy=saved.with_name(saved.name.replace('01-omatinta-',legacy_prefix))
   if saved.exists(): saved.rename(legacy)
   self.assertEqual(themes.installed_path(str(self.source),'nord'),str(legacy))
   self.assertEqual(themes.installed_path(str(self.source),'nord',str(legacy)),str(legacy))
   if legacy.exists(): legacy.rename(saved)
if __name__=='__main__':unittest.main()
