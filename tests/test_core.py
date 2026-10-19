#!/usr/bin/env python3
"""Omatinta regression tests. No network, real credentials or billed requests."""
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
from backend import jobs, providers, storage


class OmatintaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(storage, 'DATA', self.dir / 'data'))
        self.stack.enter_context(patch.object(storage, 'STOCK', self.dir / 'stock'))
        self.stack.enter_context(patch.object(storage, 'USER', self.dir / 'user'))
        self.stack.enter_context(patch.object(storage, 'BACKGROUNDS', self.dir / 'backgrounds'))
        self.stack.enter_context(patch.dict(os.environ, {}, clear=True))
        theme = storage.STOCK / 'test'
        (theme / 'backgrounds').mkdir(parents=True)
        self.image = self.dir / 'source.jpg'
        subprocess.run(['magick', '-size', '16x9', 'xc:#113355', str(self.image)], check=True)
        self.other = self.dir / 'other/source.jpg'
        self.other.parent.mkdir()
        subprocess.run(['magick', '-size', '16x9', 'xc:#cc8844', str(self.other)], check=True)
        self.args = argparse.Namespace(theme='test', source=str(self.image), style_refs=[str(self.other)],
            prompt='Match the reference.', prompt_file=None, provider='fal', model=storage.EDIT_MODELS['fal'][0]['value'],
            res='1K', quality='high', upscaler='none', upscale_model='', upscale_factor=2, upscale_only=None, creativity=5,
            env_file='', repo_dir=str(self.dir / 'results'), run=True, install=False)

    def run_job(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            jobs.run(self.args)
        return [json.loads(line) for line in output.getvalue().splitlines()]

    def fake_edit(self, *args):
        subprocess.run(['magick', self.image, args[-1]], check=True)
        return 0.05

    def test_restore_models_preserves_provider_keys_and_prompt(self):
        storage.save_key('fal', 'fal-fixture')
        storage.save_key('openrouter', 'or-fixture')
        before = (storage.DATA / '.env').read_bytes()
        custom = storage.normalize_config({'provider': 'openrouter', 'model': 'openai/gpt-image-2.5-flare',
            'quality': 'xhigh', 'upscaler': 'creative', 'upscaleModel': 'Bloom 2',
            'upscaleFactor': 4, 'creativity': 9, 'prompt': 'Keep my custom prompt.'})
        storage.atomic_write(storage.DATA / 'config.json', json.dumps(custom))
        restored = storage.restore_model_defaults()
        self.assertEqual(restored['provider'], 'openrouter')
        self.assertEqual(restored['prompt'], 'Keep my custom prompt.')
        self.assertEqual(restored['model'], storage.DEFAULT_PROVIDER_MODELS['openrouter'])
        self.assertEqual(restored['upscaler'], 'seedvr')
        self.assertEqual(restored['upscaleFactor'], 2)
        self.assertEqual(restored['quality'], 'high')
        self.assertEqual(restored['creativity'], 5)
        self.assertEqual((storage.DATA / '.env').read_bytes(), before)
        self.assertEqual(storage.config(), restored)

    def test_secure_keys_preserve_other_provider(self):
        storage.save_key('fal', 'fal-fixture')
        storage.save_key('openrouter', 'or-fixture')
        self.assertEqual(storage.credentials(), {'FAL_KEY': 'fal-fixture', 'OPENROUTER_API_KEY': 'or-fixture'})
        self.assertEqual((storage.DATA / '.env').stat().st_mode & 0o777, 0o600)
        self.assertNotIn('fixture', json.dumps(storage.snapshot()))
        with self.assertRaises(ValueError):
            storage.save_key('fal', 'key\nOTHER=value')

    def test_atomic_write_rejects_symlink(self):
        target = self.dir / 'secret'
        target.write_text('untouched')
        link = self.dir / 'link'
        link.symlink_to(target)
        with self.assertRaises(ValueError):
            storage.atomic_write(link, 'replaced')
        self.assertEqual(target.read_text(), 'untouched')

    def test_model_and_resolution_compatibility(self):
        c = storage.normalize_config({'provider': 'openrouter', 'model': 'old-fal-label'})
        self.assertEqual(c['model'], storage.DEFAULT_PROVIDER_MODELS['openrouter'])
        c = storage.normalize_config({'provider': 'openrouter', 'model': 'openai/gpt-image-2.5-sunburst', 'res': '4K', 'upscaler': 'creative'})
        self.assertEqual(c['res'], '1K')
        self.assertEqual(c['upscaleModel'], 'Bloom 2')

    def test_reference_and_theme_validation_before_provider_call(self):
        with patch.object(providers, 'edit') as edit:
            self.args.style_refs = []
            with self.assertRaisesRegex(ValueError, 'reference'):
                self.run_job()
            self.args.theme = '../bad'
            with self.assertRaisesRegex(ValueError, 'theme'):
                self.run_job()
            edit.assert_not_called()

    def test_original_openrouter_reference_limit(self):
        self.args.provider = 'openrouter'; self.args.model = 'google/gemini-nano-banana-2.1'
        self.args.style_refs = [str(self.other)] * 14
        with self.assertRaisesRegex(ValueError, 'up to 13 style'):
            jobs.validate(self.args)

    def test_theme_overlays_take_precedence(self):
        (storage.STOCK / 'test/colors.toml').write_text('background="#111111"\naccent="#222222"')
        (storage.USER / 'test/backgrounds').mkdir(parents=True)
        (storage.USER / 'test/colors.toml').write_text('accent="#333333"')
        for p in (storage.STOCK, storage.USER):
            (p / 'test/backgrounds/a.jpg').write_bytes(b'test')
        self.assertEqual(storage.colors('test'), ['#111111', '#333333'])
        self.assertEqual(storage.backgrounds('test')[0]['path'], str(storage.USER / 'test/backgrounds/a.jpg'))

    def test_dry_run_has_no_network_or_output_folder(self):
        self.args.run = False
        with patch.object(providers, 'edit') as edit:
            self.assertEqual(self.run_job()[0]['state'], 'dry-run')
            edit.assert_not_called()
        self.assertFalse(Path(self.args.repo_dir).exists())

    def test_no_upscale_produces_final_and_unique_jobs(self):
        storage.save_key('fal', 'fixture')
        with patch.object(providers, 'edit', side_effect=self.fake_edit), patch.object(providers, 'upscale') as upscale:
            first = self.run_job()[-1]; second = self.run_job()[-1]
            self.assertTrue(Path(first['path']).is_file())
            self.assertNotEqual(first['path'], second['path'])
            upscale.assert_not_called()

    def test_same_basename_inputs_remain_distinct(self):
        storage.save_key('fal', 'fixture')
        def edit(provider, model, prompt, images, res, quality, keys, dest):
            self.assertNotEqual(Path(images[0]).read_bytes(), Path(images[1]).read_bytes())
            self.fake_edit(provider, model, prompt, images, res, keys, dest)
        with patch.object(providers, 'edit', side_effect=edit):
            self.run_job()

    def test_failed_upscale_preserves_successful_edit(self):
        storage.save_key('fal', 'fixture')
        self.args.upscaler = 'precision'; self.args.upscale_model = 'Standard V2'
        with patch.object(providers, 'edit', side_effect=self.fake_edit), patch.object(providers, 'upscale', side_effect=ValueError('failed')):
            result = self.run_job()[-1]
        self.assertTrue(Path(result['path']).is_file())
        self.assertIn('upscaling failed', result['warning'])

    def test_openrouter_topaz_requires_both_keys_before_billing(self):
        storage.save_key('openrouter', 'fixture')
        self.args.provider = 'openrouter'; self.args.model = storage.EDIT_MODELS['openrouter'][0]['value']
        self.args.upscaler = 'precision'; self.args.upscale_model = 'Standard V2'
        with patch.object(providers, 'edit') as edit:
            with self.assertRaisesRegex(ValueError, 'FAL_KEY'):
                self.run_job()
            edit.assert_not_called()

    def test_openrouter_request_and_base64_response(self):
        encoded = base64.b64encode(self.image.read_bytes()).decode()
        result = json.dumps({'data': [{'b64_json': encoded}], 'usage': {'cost': 0.04}}).encode()
        with patch.object(providers, 'request', return_value=result) as request:
            cost = providers.edit('openrouter', 'google/gemini-3-pro-image', 'prompt', [self.image, self.other], '2K', 'high', {'OPENROUTER_API_KEY': 'fixture'}, self.dir / 'out.png')
        url, payload, *_ = request.call_args.args
        self.assertEqual(url, 'https://openrouter.ai/api/v1/images')
        self.assertEqual(payload['resolution'], '2K')
        self.assertEqual(len(payload['input_references']), 2)
        self.assertEqual(cost, 0.04)

    def test_fal_model_argv_and_topaz_model_payload(self):
        response = json.dumps({'images': [{'url': 'data:image/png;base64,aGk='}]}).encode()
        with patch.object(providers, 'request', return_value=response) as request:
            providers.edit('fal', 'fal-ai/nano-banana-pro/edit', 'prompt', [self.image], '4K', 'high', {'FAL_KEY': 'fixture'}, self.dir / 'out.png')
            self.assertTrue(request.call_args.args[0].endswith('fal-ai/nano-banana-pro/edit'))
            self.assertNotIn('thinking_level', request.call_args.args[1])
        response = json.dumps({'image': {'url': 'data:image/jpeg;base64,aGk='}}).encode()
        with patch.object(providers, 'request', return_value=response) as request:
            providers.upscale(self.image, 'creative', 'Bloom Realism', 4, 7, {'FAL_KEY': 'fixture'}, self.dir / 'out.jpg')
            self.assertEqual(request.call_args.args[1]['model'], 'Bloom Realism')
            self.assertNotIn('creativity', request.call_args.args[1])


    def test_non_topaz_upscalers_use_their_own_api_contracts(self):
        result = json.dumps({'image': {'url': 'data:image/png;base64,aGk='}}).encode()
        cases = [('seedvr', 'SeedVR2', 2), ('aura', 'AuraSR v2', 4), ('clarity', 'Clarity', 2)]
        for kind, model, factor in cases:
            with self.subTest(kind=kind), patch.object(providers, 'request', return_value=result) as request:
                providers.upscale(self.image, kind, model, factor, 5, {'FAL_KEY': 'fixture'}, self.dir / 'result')
                url, payload, *_ = request.call_args.args
                self.assertNotIn('model', payload)  # This is a Topaz-only parameter.
                if kind == 'seedvr':
                    self.assertTrue(url.endswith('fal-ai/seedvr/upscale/image'))
                    self.assertEqual(payload['upscale_mode'], 'factor')
                    self.assertEqual(payload['output_format'], 'jpg')
                elif kind == 'aura':
                    self.assertTrue(url.endswith('fal-ai/aura-sr'))
                    self.assertEqual(payload['checkpoint'], 'v2')
                    self.assertTrue(payload['overlapping_tiles'])
                    self.assertNotIn('output_format', payload)
                else:
                    self.assertTrue(url.endswith('fal-ai/clarity-upscaler'))
                    self.assertLess(payload['creativity'], 0.35)
                    self.assertGreater(payload['resemblance'], 0.6)

    def test_aura_factor_is_normalized_and_invalid_jobs_never_bill(self):
        value = storage.normalize_config({'upscaler': 'aura', 'upscaleFactor': 2})
        self.assertEqual(value['upscaleModel'], 'AuraSR v2')
        self.assertEqual(value['upscaleFactor'], 4)
        self.args.upscaler = 'aura'; self.args.upscale_model = 'AuraSR v2'
        with patch.object(providers, 'upscale') as call:
            with self.assertRaisesRegex(ValueError, '4×'):
                jobs.validate(self.args)
            call.assert_not_called()

    def test_upscaler_png_response_is_saved_as_actual_jpeg(self):
        storage.save_key('fal', 'fixture')
        self.args.upscaler = 'seedvr'; self.args.upscale_model = 'SeedVR2'
        def upscale(src, kind, model, factor, creativity, keys, dest):
            subprocess.run(['magick', self.image, 'png:' + str(dest)], check=True)
        with patch.object(providers, 'edit', side_effect=self.fake_edit), patch.object(providers, 'upscale', side_effect=upscale):
            result = self.run_job()[-1]
        self.assertEqual(Path(result['path']).read_bytes()[:2], b'\xff\xd8')

if __name__ == '__main__':
    unittest.main()
