# Omatinta implementation

Omatinta is a launcher-first panel/service plugin. The panel owns a normal
application window so the compositor can resize, float or tile it. It uses the
Omarchy Commons/Ui theme tokens and controls. The keepLoaded contract preserves
running jobs and previews when the window closes.

Views live under `qml/views`; processes and persistence controllers live under
`qml/controllers`; batch recipes and pricing formatting live under `qml/logic`.
Provider calls use Python's standard library in a separate process. Each
successful output is automatically saved to the chosen theme without changing
the active wallpaper. Partial outputs survive failed upscaling or stopping.

`backend/model_config.py` validates user configuration. `catalog.py` merges
bundled models, user choices and bounded cached metadata. `providers.py` contains
the supported request adapters. Custom models choose an existing adapter; they
cannot provide arbitrary request URLs, headers or commands. Upgraders retain
legacy data directories so history references remain valid.

Provider metadata refresh is explicit and separate from billed operations.
Models stay curated or user-configured; a refresh does not add models or change
defaults. Final costs remain separate from estimates. See docs/models.md and
docs/pricing.md for the contracts.

Keys cross stdin and use atomic 0600 files. Provider error bodies are suppressed.
Authenticated redirects are rejected to avoid forwarding keys to a different
host. Image responses have an 80 MB cap; metadata responses have a 2 MB cap.
ImageMagick subprocesses have 60-second limits and generation has a 15-minute
alarm. Uploads are re-encoded and metadata-stripped. Input/result filenames and
prompts remain local unless explicitly sent as generation inputs.

Launcher registration follows the managed-entry pattern used by Omasettings.
An existing custom launcher is preserved. Removal is explicit through the
bundled helper because native Omarchy plugin removal has no custom cleanup hook.
The helper cleans the launcher before the plugin manager removes code; personal
configuration, keys, results and theme wallpapers are retained.

Tests cover configuration/key permissions, model contracts, offline/partial
metadata refresh, provider payloads, dry-run safety, output isolation, partial
success, history, atomic export, theme saving and batch/pricing logic. They use
mocked providers and temporary files. Native shell validation and isolated UI
checks supplement them. Paid provider integration is deliberately not run by automated checks.

## Workspace and keyboard behavior

Generate and Upscale share one compact action row. Settings replaces the mode
row with Generation, Models, Keys, Data and Keyboard pages; Back preserves the
workspace mode. Mutating controls use a shared I/O lock, including metadata
refresh, without a state-binding cycle. Upscaling has a persisted opt-in flag
and an effective off state whenever the fal key is absent.

Model configuration and image preview use ModalFrame, which disables underlying
controls, traps forward/backward Tab, and restores focus on close. Workspace
shortcuts are blocked while a modal or native file chooser owns input and
generation shortcuts are disabled in Settings and History. Native portal
selection stores image/export directories separately in picker.json.

Reusable demo preparation and scene capture code lives in scripts/demo. It
accepts existing source/result/reference images, copies native modules into an
isolated profile, and blocks provider operations. It can be sequenced later for
code-driven video without automating the user's live desktop.
