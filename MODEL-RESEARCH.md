# Omatinta image models

These are dated research notes from private development, not a live model catalog.
See [model configuration](docs/models.md) and [pricing](docs/pricing.md) for current application behavior.


Checked against live provider catalogs and APIs on 2026-10-10.

## Selection criteria

The job is reference-led wallpaper editing, not prompt-to-image generation. Prefer catalog entries with `image` inputs, a documented image-edit endpoint, at least four reference inputs (source + three theme images), 16:9 output, and either an explicit resolution tier or documented quality control. Prefer models that are actively positioned as a current tier and include one lower-cost/fast option alongside fidelity choices.

## OpenRouter

Queried `GET https://openrouter.ai/api/v1/images/models`, then each selected model's `/endpoints` entry. The catalog reports input modalities, resolution, aspect-ratio and `input_references` support; endpoint metadata includes actual provider routing and pricing.

- `google/gemini-nano-banana-2.1`: latest image model found in this Google line as of this check, 1K/2K/4K, 16:9, 14 references.
- `google/gemini-3.1-flash-image`: Nano Banana 2, fast general-purpose choice, 1K/2K/4K, 16:9, 14 references.
- `google/gemini-3-pro-image`: Pro detail option, 1K/2K/4K, 16:9, 14 references.
- `bytedance-seed/seedream-5-0-pro` and `bytedance-seed/seedream-5-0-flash`: precise-edit and fast tiers, respectively, 1K/2K, 16:9, 14 references.
- `openai/gpt-image-2.5-sunburst` and `openai/gpt-image-2.5-flare`: quality and faster variants. Both accept 16:9 and up to 16 references. They use `quality` (`high`/`xhigh`/`max` for Sunburst; `medium`/`high`/`xhigh` for Flare) in place of a resolution tier.

The Image API documents `input_references`, model-specific settings and base64 image output. The live models endpoint confirmed each selected slug and capabilities. OpenRouter sources: [image catalog API](https://openrouter.ai/docs/api/api-reference/images/list-image-models), [image generation API](https://openrouter.ai/docs/guides/overview/multimodal/image-generation), [Nano Banana guide](https://openrouter.ai/blog/tutorials/nano-banana/).

## fal

Pricing addition checked 2026-10-12: [Seedream 5 Flash edit](https://fal.ai/models/bytedance/seedream/v5/flash/edit)
lists $0.027 per image. The dropdown and footer use that rate. Other dropdown
rates reuse the dated catalog; AuraSR retains compute-time billing because its
page's displayed per-second amount and descriptive pricing table disagree.

Checked the model pages and their input/output schemas, rather than assuming matching models use a shared request shape.

- `google/nano-banana-2.1/edit`: default all-rounder, 1K/2K/4K and 14 image inputs.
- `fal-ai/nano-banana-pro/edit`: higher-detail Nano Banana editing alternative.
- `bytedance/seedream/v5/pro/edit`: precision editing and up to 10 images. It takes `image_size` dimensions, not a `resolution` string.
- `bytedance/seedream/v5/flash/edit`: fast Seedream tier with the same size and reference constraints.
- `openai/gpt-image-2.5/sunburst/edit` and `openai/gpt-image-2.5/flare/edit`: up to 16 references and `quality` controls. Both accept `landscape_16_9` and do not take the app's 1K/2K resolution parameter.

The fal adapter maps those request shapes separately. fal reference docs: [Nano Banana 2.1](https://fal.ai/models/google/nano-banana-2.1/edit/api), [Seedream 5 Pro](https://fal.ai/models/bytedance/seedream/v5/pro/edit/api), [Seedream 5 Flash](https://fal.ai/models/bytedance/seedream/v5/flash/edit/api), [GPT Image 2.5 Sunburst](https://fal.ai/models/openai/gpt-image-2.5/sunburst/edit/api), [GPT Image 2.5 Flare](https://fal.ai/models/openai/gpt-image-2.5/flare/edit/api).

## Why these defaults

Nano Banana 2.1 is the default on both providers because it combines the broadest documented reference support with 4K output and a simple image-edit schema. The two Seedream tiers and GPT Image variants cover different cost/speed/detail trade-offs. Model labels explain the intended use; users can still choose another model per provider in Settings. Settings uses only the selected provider's model list and hides resolution/quality controls unsupported by the selected model.


## Dedicated upscalers and default

SeedVR2, AuraSR v2, Clarity, Topaz Precision and Topaz Creative are verified fal
endpoints. OpenRouter's live Image Models catalog contained no dedicated
upscaler entries on 2026-10-10, so the editing provider and upscale engine are
separate choices. All available upscale engines use the fal key.

[SeedVR2's ICLR 2026 paper](https://arxiv.org/html/2506.05301v2), Table 1,
reports a perception/fidelity trade-off. On UDM10, SeedVR2-7B has LPIPS 0.203
versus RealViformer's 0.285, while PSNR is 26.26 versus 26.70. Lower LPIPS is
better perceptual similarity; higher PSNR is better pixel fidelity. These are
video restoration benchmarks. They do not compare fal's hosted image endpoint
with Topaz, AuraSR or Clarity, and fal does not identify its checkpoint size.
The results support considering SeedVR2 for detail restoration, not a claim
that it is the universal image-upscaling winner.

The default is **SeedVR2 at 2×**: a practical inference from its public research,
reference-free restoration API and listed $0.001/MP rate. Topaz Precision is the
choice for stricter preservation. AuraSR v2 is the faster fixed-4× GAN option;
Clarity is an optional creative alternative using conservative creativity.
Neither has comparable public measurements in the reviewed SeedVR2 benchmark.

Schemas and prices were checked at the [SeedVR2](https://fal.ai/models/fal-ai/seedvr/upscale/image/api),
[AuraSR](https://fal.ai/models/fal-ai/aura-sr/api), and
[Clarity](https://fal.ai/models/fal-ai/clarity-upscaler/api) endpoints.
SeedVR2 uses `upscale_mode`, `upscale_factor`, and `output_format: jpg`.
AuraSR uses checkpoint `v2`, overlapping tiles and a fixed 4× factor.
Clarity uses creativity 0.15 and resemblance 0.85 to limit reinterpretation.
The dedicated adapters omit Topaz-only model arguments from these requests.
AuraSR has compute-time pricing, and the generic per-megapixel rates for
SeedVR2/Clarity are shown as rates because the public pages do not state the
billing dimension clearly enough to promise an exact output-size quote.
