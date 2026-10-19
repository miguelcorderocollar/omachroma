"""Model configuration and metadata regression checks. No live API calls."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN))
from backend import diagnostics, catalog, model_config, providers, storage, upscalers


class CatalogTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.data = Path(temp.name)
        self.patch = patch.object(storage, 'DATA', self.data)
        self.patch.start(); self.addCleanup(self.patch.stop)
        env = patch.dict('os.environ', {}, clear=True)
        env.start(); self.addCleanup(env.stop)

    def custom(self):
        value = copy.deepcopy(model_config.EMPTY)
        value['models']['fal'] = [{'value': 'example/new/edit', 'label': 'My model', 'adapter': 'aspect',
                                   'resolutions': ['1K'], 'maxImages': 4, 'price': {'image': 0.04}}]
        value['defaults']['fal'] = 'example/new/edit'
        return value

    def test_custom_model_default_and_request_adapter(self):
        catalog.save(self.custom())
        self.assertEqual(storage.config()['model'], 'example/new/edit')
        self.assertEqual(storage.default_model('fal'), 'example/new/edit')
        seen = []
        def request(url, payload=None, *args):
            seen.append((url, payload)); return json.dumps({'images': [{'url': 'data:image/png;base64,YQ=='}]}).encode()
        with patch.object(providers, 'request', side_effect=request):
            providers.edit('fal', 'example/new/edit', 'Test', [], '1K', 'high', {'FAL_KEY': 'fixture'}, self.data / 'result')
        self.assertEqual(seen[0][0], 'https://fal.run/example/new/edit')
        self.assertEqual(seen[0][1]['resolution'], '1K')

    def test_hidden_model_cannot_be_default_or_generated(self):
        value = self.custom(); value['hidden']['fal'] = ['example/new/edit']
        with self.assertRaises(ValueError): catalog.save(value)
        value['defaults'] = {}; catalog.save(value)
        self.assertIsNone(storage.model_spec('fal', 'example/new/edit'))

    def test_cannot_hide_every_model(self):
        value = copy.deepcopy(model_config.EMPTY)
        value['hidden']['fal'] = [m['value'] for m in catalog.MODELS['fal']]
        with self.assertRaises(ValueError): catalog.save(value)

    def test_reject_urls_bad_dimensions_and_unknown_fields(self):
        for field, value in [('value', 'https://evil.example/model'), ('dimensions', {'1K': [0, 10]}), ('headers', {'Authorization': 'secret'})]:
            config = self.custom(); config['models']['fal'][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError): catalog.save(config)

    def test_reject_nan_prices_and_duplicate_ids(self):
        value = self.custom(); value['models']['fal'][0]['price']['image'] = float('nan')
        with self.assertRaises(ValueError): catalog.save(value)
        value = self.custom(); value['models']['fal'] *= 2
        with self.assertRaises(ValueError): catalog.save(value)

    def test_invalid_save_preserves_existing_file(self):
        catalog.save(self.custom()); before = (self.data / 'models.json').read_bytes()
        with self.assertRaises(ValueError): catalog.save({'models': 'wrong'})
        self.assertEqual((self.data / 'models.json').read_bytes(), before)

    def test_corrupt_and_oversized_cache_fall_back(self):
        for contents in ('{broken', 'x' * (model_config.MAX_BYTES + 1), '{"schemaVersion":1,"fal":[]}'):
            (self.data / 'catalog-cache.json').write_text(contents)
            metadata, warning = catalog.cache()
            self.assertEqual(metadata, {}); self.assertTrue(warning)
            self.assertTrue(catalog.models('fal'))

    def test_corrupt_user_config_is_not_overwritten(self):
        path = self.data / 'models.json'; path.write_text('{broken')
        self.assertTrue(catalog.user_config()[1]); self.assertTrue(catalog.models('fal'))
        self.assertEqual(path.read_text(), '{broken')
        with self.assertRaises(ValueError): catalog.refresh()

    def test_offline_refresh_keeps_last_good_cache(self):
        before = {'schemaVersion': 1, 'fal': {'google/nano-banana-2.1/edit': {'checkedAt': '2026-01-01', 'rates': [{'usd': 0.05, 'unit': 'image', 'billable': 'output'}]}}}
        path = self.data / 'catalog-cache.json'; storage.atomic_write(path, json.dumps(before))
        with patch.object(storage, 'credentials', return_value={'FAL_KEY': 'fixture'}), patch.object(catalog, 'metadata_request', side_effect=OSError('offline')):
            refreshed = catalog.refresh()
        self.assertEqual(refreshed['updated'], 0); self.assertTrue(refreshed['warnings'])
        self.assertEqual(json.loads(path.read_text()), before)

    def test_fal_refresh_updates_units_and_preserves_manual_override(self):
        catalog.save(self.custom())
        def response(url, *args):
            return {'prices': [{'endpoint_id': 'example/new/edit', 'unit_price': 0.1, 'unit': 'image', 'currency': 'USD'},
                               {'endpoint_id': 'fal-ai/seedvr/upscale/image', 'unit_price': 0.002, 'unit': 'megapixel', 'currency': 'USD'}], 'has_more': False}
        with patch.object(storage, 'credentials', return_value={'FAL_KEY': 'fixture'}), patch.object(catalog, 'metadata_request', side_effect=response):
            result = catalog.refresh()
        self.assertEqual(result['updated'], 1)
        self.assertEqual(storage.model_spec('fal', 'example/new/edit')['price'], {'image': 0.04})
        self.assertNotIn('rates', storage.model_spec('fal', 'example/new/edit'))
        self.assertEqual(upscalers.prices()['upscale']['seedvr']['rates'][0]['unit'], 'megapixel')

    def test_openrouter_missing_model_and_partial_refresh(self):
        visible = catalog.MODELS['openrouter'][0]['value']
        def response(url, *args):
            if url.endswith('/images/models'): return {'data': [{'id': visible}]}
            return {'endpoints': [{'pricing': [{'billable': 'output_image', 'unit': 'token', 'cost_usd': 0.00003}]}]}
        with patch.object(storage, 'credentials', return_value={'OPENROUTER_API_KEY': 'fixture'}), patch.object(catalog, 'metadata_request', side_effect=response):
            catalog.refresh()
        models = catalog.models('openrouter')
        self.assertTrue(models[0]['available']); self.assertFalse(models[1]['available'])
        self.assertEqual(models[0]['rates'][0]['billable'], 'output_image')

    def test_custom_upscaler_uses_adapter(self):
        value = self.custom()
        value['upscalers'] = [{'id': 'my-aura', 'label': 'My Aura', 'endpoint': 'example/aura', 'adapter': 'aura', 'models': ['Aura'], 'factors': [4]}]
        value['defaults'].update(upscaler='my-aura', upscaleModel='Aura', upscaleFactor=4)
        catalog.save(value)
        self.assertEqual(storage.config()['upscaler'], 'my-aura')
        self.assertEqual(upscalers.validate('my-aura', 'Aura', 4)['adapter'], 'aura')

    def test_remove_key_preserves_other_provider_and_environment(self):
        storage.save_key('fal', 'fixture-fal'); storage.save_key('openrouter', 'fixture-or')
        with patch.dict('os.environ', {'FAL_KEY': 'env-fixture'}):
            storage.remove_key('fal')
            self.assertEqual(storage.credentials(), {'FAL_KEY': 'env-fixture', 'OPENROUTER_API_KEY': 'fixture-or'})
        self.assertEqual(storage.credentials(), {'OPENROUTER_API_KEY': 'fixture-or'})

    def test_config_recovery_preserves_bad_file_until_explicit_save(self):
        path = self.data / 'config.json'; path.write_text('[1,2]')
        self.assertTrue(storage.config_warning()); self.assertEqual(storage.config()['provider'], 'fal')
        self.assertEqual(path.read_text(), '[1,2]')

    def test_malformed_rows_do_not_discard_valid_metadata(self):
        ident = catalog.MODELS['openrouter'][0]['value']
        def response(url, *args):
            if 'fal.ai' in url:
                return {'prices': [{}, {'endpoint_id': 'fal-ai/seedvr/upscale/image', 'unit_price': .002, 'unit': 'megapixel'}]}
            if url.endswith('/images/models'):
                return {'data': [{}, {'id': ident}]}
            return {'endpoints': [{'pricing': [{'billable': 'output_image', 'unit': 'token', 'cost_usd': .00003}]}]}
        with patch.object(storage, 'credentials', return_value={'FAL_KEY': 'fixture', 'OPENROUTER_API_KEY': 'fixture'}), patch.object(catalog, 'metadata_request', side_effect=response):
            result = catalog.refresh()
        self.assertEqual(result['updated'], 2)
        self.assertTrue(result['warnings'])
        self.assertTrue(upscalers.prices()['upscale']['seedvr']['rates'])
        self.assertTrue(catalog.models('openrouter')[1]['available'])

    def test_missing_model_does_not_relabel_old_price_as_fresh(self):
        ident = catalog.MODELS['openrouter'][0]['value']
        storage.atomic_write(self.data / 'catalog-cache.json', json.dumps({'openrouter': {ident: {'checkedAt': '2020-01-01', 'rates': [{'unit':'image','billable':'output_image','usd':.1}]}}}))
        with patch.object(storage, 'credentials', return_value={'OPENROUTER_API_KEY': 'fixture'}), patch.object(catalog, 'metadata_request', return_value={'data': []}):
            catalog.refresh()
        item = catalog.models('openrouter')[0]
        self.assertFalse(item['available']); self.assertEqual(item['priceChecked'], '2020-01-01')
        self.assertNotEqual(item['availabilityChecked'], item['priceChecked'])

    def test_cache_rejects_rates_without_timestamp(self):
        (self.data / 'catalog-cache.json').write_text(json.dumps({'fal': {'fixture': {'rates': [{'unit':'image','billable':'output','usd':.1}]}}}))
        self.assertTrue(catalog.cache()[1])
        self.assertTrue(catalog.models('fal'))

    def test_huge_numeric_price_rejected(self):
        value = self.custom(); value['models']['fal'][0]['price']['image'] = 10 ** 400
        with self.assertRaises(ValueError): catalog.save(value)

    def test_openrouter_manual_prices_refresh_availability_only(self):
        value = copy.deepcopy(model_config.EMPTY)
        ident = catalog.MODELS['openrouter'][0]['value']
        value['models']['openrouter'] = [{'value':ident,'label':'Manual model','adapter':'openrouter','resolutions':['1K'],'price':{'image':.99}}]
        catalog.save(value)
        with patch.object(storage, 'credentials', return_value={'OPENROUTER_API_KEY':'fixture'}), patch.object(catalog, 'metadata_request', return_value={'data':[{'id':ident}]}) as request:
            result = catalog.refresh()
        self.assertEqual(request.call_count,1)
        self.assertEqual(result['updated'],0)
        self.assertEqual(result['availabilityUpdated'],len(catalog.MODELS['openrouter']))
        self.assertNotIn('rates',catalog.cache()[0]['openrouter'][ident])
        self.assertEqual(storage.model_spec('openrouter',ident)['price'],{'image':.99})

    def test_storage_usage_does_not_follow_external_symlinks(self):
        (self.data / 'one').write_bytes(b'abc')
        with tempfile.TemporaryDirectory() as external:
            target = Path(external); (target / 'secret').write_bytes(b'x' * 1000)
            (self.data / 'linked-folder').symlink_to(target, target_is_directory=True)
            (self.data / 'linked-file').symlink_to(target / 'secret')
            info = diagnostics.storage_usage()
        self.assertEqual(info['bytes'], 3)
        self.assertTrue(info['complete'])

    def test_launcher_cleanup_protects_user_entry(self):
        with patch.dict('os.environ', {'XDG_DATA_HOME': str(self.data)}):
            storage.install_launcher(); storage.remove_launcher()
            path = self.data / 'applications/omatinta.desktop'; self.assertFalse(path.exists())
            path.write_text('[Desktop Entry]\nName=Custom\n')
            with self.assertRaises(ValueError): storage.remove_launcher()
            self.assertTrue(path.exists())


if __name__ == '__main__':
    unittest.main()
