"""Provider adapters. Explicit HTTP deadlines; no automatic billed retries."""
import base64
import json
from pathlib import Path
import urllib.error
import urllib.request

from . import costs, storage, upscalers

MAX_RESPONSE = 80 * 1024 * 1024


def request(url, payload=None, key='', provider='', timeout=600, limit=MAX_RESPONSE):
    headers = {'Content-Type': 'application/json'}
    if key:
        headers['Authorization'] = ('Key ' if provider == 'fal' else 'Bearer ') + key
    req = urllib.request.Request(url, data=json.dumps(payload).encode() if payload is not None else None,
                                 headers=headers)
    try:
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs):
                return None
        opener = urllib.request.build_opener(NoRedirect()) if key else None
        with (opener.open(req, timeout=timeout) if opener else urllib.request.urlopen(req, timeout=timeout)) as r:
            data = r.read(limit + 1)
    except urllib.error.HTTPError as e:
        # Do not expose response bodies, which can echo request images or credentials.
        reason = {401: 'API key rejected. Update it in Settings.', 402: 'Insufficient provider credit.',
                  403: 'Provider denied this request.', 422: 'Provider rejected the model inputs.',
                  429: 'Provider rate limit. Try again later.',
                  500: 'Provider is temporarily unavailable. Try later.', 502: 'Provider gateway failed. Try later.',
                  503: 'Provider is temporarily unavailable. Try later.', 504: 'Provider gateway timed out.'}.get(e.code, 'Provider request failed.')
        raise ValueError(f'{reason} HTTP {e.code}.') from None
    if len(data) > limit:
        raise ValueError('Provider response exceeds the size limit.')
    return data


def data_url(path):
    return 'data:image/jpeg;base64,' + base64.b64encode(Path(path).read_bytes()).decode()


def save_image(value, dest):
    if value.startswith('data:'):
        header, encoded = value.split(',', 1)
        if ';base64' not in header or not header.startswith('data:image/'):
            raise ValueError('Unsupported image response.')
        data = base64.b64decode(encoded, validate=True)
    elif value.startswith('https://'):
        data = request(value)
    else:
        raise ValueError('Provider returned an invalid image URL.')
    if not data or len(data) > MAX_RESPONSE:
        raise ValueError('Invalid image response size.')
    Path(dest).write_bytes(data)


def edit(provider, model, prompt, images, resolution, quality, keys, dest):
    spec = storage.model_spec(provider, model)
    if not spec:
        raise ValueError('The selected model is not available from this provider.')
    image_urls = [data_url(p) for p in images]
    if provider == 'fal':
        payload = {'prompt': prompt, 'image_urls': image_urls, 'num_images': 1}
        if spec.get('adapter') == 'landscape':
            # Both Seedream 5 tiers accept a 16:9 landscape preset and 1K/2K sizes.
            dimensions = spec['dimensions'][resolution]
            payload['image_size'] = {'width': dimensions[0], 'height': dimensions[1]}
            payload['output_format'] = 'jpeg'
        elif spec.get('adapter') == 'auto':
            payload.update(image_size='landscape_16_9', quality=quality, output_format='png')
        else:
            payload.update(aspect_ratio='16:9', output_format='png')
            payload['resolution'] = resolution
            if model == 'google/nano-banana-2.1/edit':
                payload['thinking_level'] = 'minimal'
        result = json.loads(request('https://fal.run/' + model, payload, keys['FAL_KEY'], 'fal'))
        images_out = result.get('images', [])
        if not images_out or not images_out[0].get('url'):
            raise ValueError('fal returned no image. Try another model or prompt.')
        save_image(images_out[0]['url'], dest)
    else:
        payload = {
            'model': model,
            'prompt': prompt,
            'n': 1,
            'aspect_ratio': '16:9',
            'input_references': [{'type': 'image_url', 'image_url': {'url': u}} for u in image_urls],
        }
        if spec['resolutions']:
            payload['resolution'] = resolution
        if spec.get('qualityOptions'):
            payload['quality'] = quality
        result = json.loads(request('https://openrouter.ai/api/v1/images', payload,
                                    keys['OPENROUTER_API_KEY'], 'openrouter'))
        output = result.get('data', [])
        if not output or not output[0].get('b64_json'):
            raise ValueError('OpenRouter returned no image. Try another model or prompt.')
        save_image('data:image/png;base64,' + output[0]['b64_json'], dest)
    return costs.from_response(result)


def upscale(src, kind, model, factor, creativity, keys, dest):
    spec = upscalers.validate(kind, model, factor)
    kind = spec.get('adapter', kind)
    payload = {'image_url': data_url(src)}
    if kind == 'seedvr':
        payload.update(upscale_mode='factor', upscale_factor=factor, noise_scale=0.1, output_format='jpg')
    elif kind == 'aura':
        payload.update(upscale_factor=4, checkpoint='v2', overlapping_tiles=True)
    elif kind == 'clarity':
        payload.update(upscale_factor=factor, creativity=0.15, resemblance=0.85,
                       prompt='high resolution, preserve original colors, subjects and composition')
    else:
        payload.update(model=model, upscale_factor=factor, output_format='jpeg')
        if kind == 'precision':
            payload['face_enhancement'] = False
        elif model == 'Bloom 2':
            payload.update(creativity=creativity, color_preservation=True)
    result = json.loads(request('https://fal.run/' + spec['endpoint'], payload, keys['FAL_KEY'], 'fal'))
    image = result.get('image', {})
    if not image.get('url'):
        raise ValueError('The upscaler returned no image. The saved edit remains available.')
    save_image(image['url'], dest)
    return costs.from_response(result)
