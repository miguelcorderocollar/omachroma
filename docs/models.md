# Model configuration

Use **Settings → Edit model configuration** or edit `models.json` in the data
directory displayed by Settings. Close and reopen the app to reload an external
edit. Saving in Settings validates the entire document before replacing it.
Configuration is private to your machine and persists across plugin updates.

The schema is version 1. Omitted lists are empty; bundled models remain unless
hidden or replaced by a configured entry with the same ID. At least one editing
model must remain visible for each provider. Preferred defaults must remain
visible. Rate refresh does not add models or change generation defaults.

Example structure, using a bundled model as the preferred fal default:

```json
{
  "schemaVersion": 1,
  "models": {"fal": [], "openrouter": []},
  "upscalers": [],
  "hidden": {"fal": ["fal-ai/nano-banana-pro/edit"], "openrouter": [], "upscalers": []},
  "defaults": {
    "fal": "google/nano-banana-2.1/edit",
    "upscaler": "seedvr",
    "upscaleModel": "SeedVR2",
    "upscaleFactor": 2
  }
}
```

**Use selected model by default** records the current provider's preferred model.
**Hide selected model** keeps another visible default. **Show hidden models**
clears the hiding lists. **Restore model defaults** applies your configured
preferences to current generation settings while preserving keys, provider and
prompt. If you have not chosen preferences, bundled defaults apply.

## Add an editing model

Add an object to `models.fal` or `models.openrouter`. The following ID is an
illustration, not an endpoint to generate with. Replace it with a real compatible
provider model and verify its schema before use:

```json
{
  "value": "example/image-editor",
  "label": "My image editor",
  "adapter": "aspect",
  "resolutions": ["1K", "2K"],
  "maxImages": 8,
  "price": {"1K": 0.04, "2K": 0.08}
}
```

Allowed adapters:

| Provider | Adapter | Request contract |
| --- | --- | --- |
| fal | `aspect` | prompt, image_urls, num_images=1, aspect_ratio=16:9, resolution, output_format=png |
| fal | `landscape` | prompt, image_urls, num_images=1, image_size width/height, output_format=jpeg |
| fal | `auto` | prompt, image_urls, num_images=1, image_size=landscape_16_9, quality, output_format=png |
| OpenRouter | `openrouter` | Image API prompt, input_references, n=1, aspect_ratio=16:9; resolution/quality when configured |

fal adapters expect `images[0].url` in the response. The OpenRouter adapter
expects `data[0].b64_json`. Endpoints with different payloads or responses require
a code adapter; a configuration entry cannot invent one. URLs, headers, arbitrary
payload fields and executable code are not accepted.

`resolutions` accepts 1K, 2K and 4K. A fal `landscape` model must also provide
`dimensions` for every configured resolution, for example
`{"1K":[1536,864],"2K":[2048,1152]}`. Other models may provide dimensions when
verified; do not guess them just to obtain an upscale estimate.

`auto` requires `qualityOptions`, selected from auto, low, medium, high, xhigh
and max. OpenRouter may also provide qualityOptions. `maxImages` includes the
source and all references and must be between 2 and 32.

Manual `price` fields accept finite, non-negative USD amounts:
`1K`, `2K`, `4K`, `image`, `outputToken` and `inputImage`. Token rates are per
single output image token. A non-empty manual price overrides live pricing for
that configured entry, including an entry replacing a bundled model. Omit price
or use `{}` to use provider refresh metadata. Manual rates have no provider
verification; keep them current yourself.

## Add an upscaler

Custom upscalers still use fal. Add a configured engine under `upscalers`:

```json
{
  "id": "my-engine",
  "label": "My compatible upscaler",
  "endpoint": "example/upscale/image",
  "adapter": "seedvr",
  "models": ["My model"],
  "factors": [2, 4],
  "description": "A compatible endpoint I maintain."
}
```

The ID above is also illustrative. Adapters are seedvr, precision, aura, clarity
or creative and use the corresponding payload in `backend/providers.py`. They
expect `image.url`. Aura requires factor 4; other engines accept configured
factors 2 and/or 4. Hiding an engine does not delete its data. If you hide the
preferred upscaler, choose another in defaults in the same edit. None cannot be
hidden and is always available without a fal key.

## Recovery and bounds

Invalid model files are preserved and bundled choices remain usable. The warning
in Settings explains the fallback. Open the editor to replace the broken file
with a valid configuration, or repair the file externally. Refresh refuses an
invalid model file so it cannot overwrite your choices.

Configuration/cache files are capped at 256 KB. Up to 40 configured editing
models per provider and 20 configured upscalers are supported. Metadata responses
and refresh time are bounded. Rejected edits leave the saved configuration intact.
