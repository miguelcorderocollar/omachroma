# Code driven Omatinta demo

`prepare.py` builds an isolated Quickshell profile from a saved source/result
pair and explicit style references. It copies the current plugin to `app/`,
copies Omarchy's native `Commons`, `Ui`, and service QML into the harness root,
and creates a minimal history record under the fixture data directory. The
source and result live under `home/Pictures/`; the theme directory contains
only the references passed on the command line. Exact hashes and perceptual
hashes are checked to reject references that duplicate either image.

The output profile is created with mode `0700`; its fake `.env` and history
files use `0600`. It includes conspicuously fake local provider keys so the
controls render in their normal enabled state. `render-env.sh` clears provider
key environment variables. The generated backend refuses `--run` and pricing
refresh. Only history, theme, and settings queries are enabled; selecting a
history row updates only the fixture's `current-job.json`. Metadata refresh
code in the copied backend is stubbed as an additional guard. No personal data
is written. This profile is for rendering and navigation only; generation and
provider calls are unavailable.

`prepare.py` uses Pillow for a small perceptual hash check in addition to exact
SHA-256 comparison. Pillow is a demo-preparation dependency only; the plugin
itself remains standard library based. On Arch, install the `python-pillow`
package or provide Pillow in the Python environment used to run the builder.

Example using any local source/result and distinct references:

```bash
python3 scripts/demo/prepare.py \
  --source /path/to/source.jpg \
  --result /path/to/saved-result.jpg \
  --theme ethereal \
  --references /path/to/stock-cosmic.jpg /path/to/stock-meadow.jpg \
  --output-dir /tmp/omatinta-demo
source /tmp/omatinta-demo/render-env.sh
DEMO_CAPTURE_PATH="$DEMO_ROOT/app/preview.png" DEMO_EXIT_AFTER_CAPTURE=1 \
  quickshell --no-color -p "$DEMO_ROOT/shell.qml"
DEMO_HEIGHT=560 DEMO_START_VIEW=settings DEMO_SETTINGS_TAB=Generation \
  DEMO_CAPTURE_PATH="$DEMO_ROOT/app/docs/screenshots/settings.png" \
  DEMO_EXIT_AFTER_CAPTURE=1 quickshell --no-color -p "$DEMO_ROOT/shell.qml"
```

Use `--label`, `--date`, and `--prompt` to set the history row and the visible
prompt. `--output-dir` must be new or empty and must be outside the plugin
source tree. The builder never changes the input images. It reads theme colors
from `$OMARCHY_PATH/themes/<theme>` (or the standard `/usr/share/omarchy`
install) and keeps all writable application data inside the output directory.

The harness exposes deterministic navigation and capture through Quickshell
IPC. List the process with `quickshell ipc -p "$DEMO_ROOT/shell.qml" show`,
then call:

```bash
quickshell ipc -p "$DEMO_ROOT/shell.qml" call omatinta-demo workspace
quickshell ipc -p "$DEMO_ROOT/shell.qml" call omatinta-demo settings Generation
quickshell ipc -p "$DEMO_ROOT/shell.qml" call omatinta-demo settings Models
quickshell ipc -p "$DEMO_ROOT/shell.qml" call omatinta-demo history
quickshell ipc -p "$DEMO_ROOT/shell.qml" call omatinta-demo preview
quickshell ipc -p "$DEMO_ROOT/shell.qml" call omatinta-demo dismissPreview
quickshell ipc -p "$DEMO_ROOT/shell.qml" call omatinta-demo captureTo /tmp/omatinta-frame.png
```

`captureTo` saves the `AppContent` item with `grabToImage`; it does not capture
the desktop. For future video work, keep Quickshell running and sequence the
navigation calls with short pauses before each capture. `upscale` is also
available when the copied provider configuration supports it. `preview` opens
the saved result in the lightbox and `dismissPreview` closes it.

For a code-driven sequence, start the shell once, then call `workspace`,
`settings Generation`, `settings Models`, `history`, and `captureTo <path>` as
needed. The startup capture environment variables shown above are useful for
static screenshots and avoid a second window.

The fixture presents a previously saved result alongside the source and the
references supplied for the demo. It does not assert that those references
were used to create that historical output. Rendering uses the installed
Quickshell/Omarchy QML modules on the current machine and does not validate
other versions. The demo shell is separate from the live Omarchy shell; do not
restart or replace the running shell to use it.
