# Pricing and availability

Three sources remain distinct: bundled dated rates, cached provider metadata,
and explicit user overrides. UI check dates belong to the displayed source.
Refreshing never rewrites a manual rate. OpenRouter availability is still checked for manually priced models, but their endpoint rates are not fetched. The refresh result counts rates and availability separately.

fal refresh uses the authenticated [pricing endpoint](https://fal.ai/docs/platform-apis/v1/models/pricing)
for the configured editing/upscale endpoint IDs. It records the returned billing
unit and USD amount. Base unit pricing may still vary with output dimensions or
other endpoint parameters; it is not a guaranteed per-request quote.

OpenRouter refresh uses the [image model catalog](https://openrouter.ai/docs/api/api-reference/images/list-image-models)
and [per-model endpoint metadata](https://openrouter.ai/docs/api/api-reference/images/list-image-model-endpoints).
It records image billing targets, units and ranges across endpoints. Conditional
pricing remains marked rather than interpreted as a fixed total. A model absent
from the returned catalog is marked unavailable; a request failure retains the
previous state and produces a warning.

No catalog scraper or HTML parsing is used. Refresh requires a saved or
environment provider key and has a 75-second overall request budget, with
individual metadata calls limited to at most 8 seconds and responses to 2 MB.
The CLI has an additional 80-second hard deadline, including slow response reads. A missing key skips that provider. Partial refreshes keep per-entry dates and
last-good data. No image, prompt or generation request is sent by Refresh.

Before generation, known per-output rates can support an approximate remaining
batch total. Token-priced, conditional, routed and unknown-dimension work stays
variable. Upscale estimates use configured model dimensions or the selected
image dimensions, never a universal guessed 1K/2K/4K size. Estimates do not
include every possible provider adjustment and are not spend caps.

The job's final accounting accepts only explicit `usage.cost`. An edit amount
without an upscale amount is a partial report, not a final total. Some providers
or endpoints do not return this field; the app says so. Use the provider dashboard
for your actual bill. Stopping a local process cannot guarantee remote cancellation
or a refund. There are no automatic paid retries.
