#!/usr/bin/env python3
"""Build an isolated, network-guarded Omatinta QML demo profile."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil

from PIL import Image


PLUGIN = Path(__file__).resolve().parents[2]
TEMPLATE = Path(__file__).resolve().parent
def image_hash(path: Path) -> tuple[str, int]:
    """Return a file hash and a small perceptual difference hash."""
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with Image.open(path) as image:
        image = image.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
        pixels = [image.getpixel((x, y)) for y in range(8) for x in range(9)]
    bits = 0
    for y in range(8):
        for x in range(8):
            bits = (bits << 1) | int(pixels[y * 9 + x] > pixels[y * 9 + x + 1])
    return digest, bits


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", Path(value).name).strip(".-") or "image"


def copy_image(source: Path, destination: Path) -> Path:
    source = source.expanduser().resolve(strict=True)
    if not source.is_file():
        raise ValueError(f"Not a file: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    return destination


def prepare(args: argparse.Namespace) -> Path:
    source = args.source.expanduser().resolve(strict=True)
    result = args.result.expanduser().resolve(strict=True)
    references = [path.expanduser().resolve(strict=True) for path in args.references]
    if not source.is_file() or not result.is_file() or any(not path.is_file() for path in references):
        raise ValueError("Source, result, and reference inputs must be regular files.")
    if (not re.fullmatch(r"[A-Za-z0-9._-]{1,80}", args.theme)
            or args.theme in (".", "..") or args.theme.startswith(".")):
        raise ValueError("Theme must be a simple installed-theme name.")
    if not references:
        raise ValueError("Pass at least one stock or custom style reference.")

    inputs = [source, result, *references]
    identities = [image_hash(path) for path in inputs]
    for index, candidate in enumerate(references, start=2):
        digest, perceptual = identities[index]
        for original_index, original in enumerate((source, result)):
            original_digest, original_perceptual = identities[original_index]
            distance = (perceptual ^ original_perceptual).bit_count()
            if digest == original_digest or distance <= 5:
                raise ValueError(
                    f"Reference {candidate} duplicates the source/result "
                    f"(SHA-256 match or perceptual distance {distance}/64)."
                )
        for prior_index in range(2, index):
            prior_digest, prior_perceptual = identities[prior_index]
            distance = (perceptual ^ prior_perceptual).bit_count()
            if digest == prior_digest or distance <= 5:
                raise ValueError(f"Reference {candidate} duplicates another reference.")

    output = args.output_dir.expanduser().resolve()
    if output == PLUGIN or PLUGIN in output.parents:
        raise ValueError("Output directory must be outside the plugin source tree.")
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"Output directory is not empty: {output}")
    output.mkdir(mode=0o700, parents=True, exist_ok=True)
    output.chmod(0o700)

    home = output / "home"
    xdg_data = output / "xdg"
    theme_root = output / "omarchy" / "themes" / args.theme
    background_dir = theme_root / "backgrounds"
    (home / ".config" / "omarchy" / "backgrounds" / args.theme).mkdir(parents=True)
    pictures = home / "Pictures"
    pictures.mkdir(parents=True)
    (home / ".local" / "state" / "omarchy" / "current" / "theme").mkdir(parents=True)
    (xdg_data / "omatinta" / "history" / "demo-saved-result").mkdir(parents=True)
    source_copy = copy_image(source, pictures / ("source" + source.suffix.lower()))
    result_copy = copy_image(result, pictures / ("result" + result.suffix.lower()))
    copied_references = []
    for index, path in enumerate(references, start=1):
        name = safe_name(path.name)
        copied_references.append(copy_image(path, background_dir / f"{index:02d}-{name}"))

    stock_root = Path(os.environ.get("OMARCHY_PATH", "/usr/share/omarchy")).expanduser()
    colors = stock_root / "themes" / args.theme / "colors.toml"
    if colors.is_file():
        shutil.copyfile(colors, theme_root / "colors.toml")
        shutil.copyfile(colors, home / ".local/state/omarchy/current/theme/colors.toml")
    else:
        (theme_root / "colors.toml").write_text("background = '#080b18'\nforeground = '#eee8df'\naccent = '#a9a4f5'\n")
        shutil.copyfile(theme_root / "colors.toml", home / ".local/state/omarchy/current/theme/colors.toml")

    # Credentials are deliberately fake. The copied backend wrapper also blocks
    # every mutating/provider command, including --run and metadata refreshes.
    data = xdg_data / "omatinta"
    env_file = data / ".env"
    env_file.write_text(
        "FAL_KEY=DEMO-PLACEHOLDER-NOT-A-REAL-KEY\n"
        "OPENROUTER_API_KEY=DEMO-PLACEHOLDER-NOT-A-REAL-KEY\n"
    )
    env_file.chmod(0o600)

    date = args.date or datetime.now(timezone.utc).isoformat(timespec="seconds")
    record = {
        "date": date,
        "name": args.label or source.stem,
        "provider": "fal",
        "model": "Saved demo result",
        "theme": args.theme,
        "resultPath": str(result_copy),
        "error": "",
        "message": "Saved result demonstration.",
        "status": "done",
        "sourcePath": str(source_copy),
    }
    job_file = data / "history/demo-saved-result/job.json"
    job_file.write_text(json.dumps(record, indent=2) + "\n")
    job_file.chmod(0o600)
    selection = data / "current-job.json"
    selection.write_text('{"id":"demo-saved-result"}\n')
    selection.chmod(0o600)

    for name in ("Commons", "Ui", "services"):
        native = stock_root / "shell" / name
        if not native.is_dir():
            native = Path("/usr/share/omarchy/shell") / name
        if native.is_dir():
            shutil.copytree(native, output / name, dirs_exist_ok=True)

    app = output / "app"
    shutil.copytree(PLUGIN, app, ignore=shutil.ignore_patterns(".git", "__pycache__"), dirs_exist_ok=True)
    entry = app / "generate-theme-wallpaper.py"
    code = entry.read_text()
    marker = "    args = ap.parse_args()\n"
    guard = marker + (
        "    # This generated copy is render-only. Never call providers or mutate data.\n"
        "    if args.run or args.refresh_prices:\n"
        "        raise ValueError('Provider jobs and metadata refresh are disabled in demo mode.')\n"
        "    forbidden = (args.remember_output, args.clear_preview, args.export_image,\n"
        "                 args.save_to_theme, args.save_config, args.restore_model_defaults,\n"
        "                 args.save_key, args.install_launcher, args.remove_launcher,\n"
        "                 args.remove_key, args.save_models, args.pick_images,\n"
        "                 args.open_data_folder, args.init_env, args.install, args.source,\n"
        "                 args.upscale_only, args.prompt_file)\n"
        "    if any(forbidden):\n"
        "        raise ValueError('Only read-only demo queries are enabled.')\n"
        "    if not any((args.snapshot, args.history, args.load_history, args.list_themes,\n"
        "                args.list_backgrounds, args.theme_colors, args.theme_bundle,\n"
        "                args.storage_info, args.doctor)):\n"
        "        raise ValueError('Only read-only demo queries are enabled.')\n"
    )
    if marker not in code:
        raise ValueError("Could not add the demo-only provider guard to the backend entry point.")
    entry.write_text(code.replace(marker, guard, 1))
    # Metadata is bundled/cached in the demo. Refresh code cannot reach providers.
    catalog = app / "backend/catalog.py"
    text = catalog.read_text()
    text = re.sub(
        r"def metadata_request\(url, key, provider, timeout=8\):\n(?:    .*\n)+?\n",
        "def metadata_request(url, key, provider, timeout=8):\n"
        "    raise RuntimeError('Metadata requests are disabled in demo mode.')\n\n",
        text,
        count=1,
    )
    if "Metadata requests are disabled in demo mode." not in text:
        raise ValueError("Could not stub metadata requests in the demo backend.")
    catalog.write_text(text)

    shutil.copyfile(TEMPLATE / "shell.qml", output / "shell.qml")
    env_sh = output / "render-env.sh"
    env_sh.write_text("\n".join([
        "# Source this file before starting the isolated demo profile.",
        'export DEMO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"',
        'export HOME="$DEMO_ROOT/home"',
        'export XDG_CONFIG_HOME="$HOME/.config"',
        'export XDG_DATA_HOME="$DEMO_ROOT/xdg"',
        'export XDG_STATE_HOME="$DEMO_ROOT/xdg-state"',
        'export XDG_CACHE_HOME="$DEMO_ROOT/xdg-cache"',
        'export OMARCHY_PATH="$DEMO_ROOT/omarchy"',
        'export QML2_IMPORT_PATH="$DEMO_ROOT:/usr/share/omarchy/shell"',
        'export QML_IMPORT_PATH="$QML2_IMPORT_PATH"',
        "export PATH=/usr/bin:/bin",
        "unset FAL_KEY OPENROUTER_API_KEY",
        "export QT_QPA_PLATFORM=offscreen",
        "export DEMO_WIDTH=940",
        "export DEMO_HEIGHT=900",
        f'export DEMO_SOURCE="$DEMO_ROOT/home/Pictures/{source_copy.name}"',
        f'export DEMO_RESULT="$DEMO_ROOT/home/Pictures/{result_copy.name}"',
        "export DEMO_THEME=" + shlex.quote(args.theme),
        "export DEMO_PROMPT=" + shlex.quote(args.prompt),
        "export DEMO_START_VIEW=workspace",
        "export DEMO_SETTINGS_TAB=Generation",
        "export DEMO_CAPTURE_PATH=",
        "export DEMO_EXIT_AFTER_CAPTURE=0",
        "",
    ]))
    env_sh.chmod(0o755)
    print(output)
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="source image for the saved recipe")
    parser.add_argument("--result", type=Path, required=True, help="saved output image")
    parser.add_argument("--theme", required=True, help="theme name, for example ethereal")
    parser.add_argument("--references", type=Path, nargs="+", required=True, help="style reference images")
    parser.add_argument("--output-dir", type=Path, required=True, help="new or empty ignored fixture directory")
    parser.add_argument("--label", help="history label; defaults to source filename")
    parser.add_argument("--date", help="history date string; defaults to current UTC")
    parser.add_argument("--prompt", default="Recreate the source image using the selected theme's colors, light, mood and texture. Preserve the composition. Wide desktop wallpaper, no added text or watermark.")
    return parser.parse_args()


if __name__ == "__main__":
    try:
        prepare(parse_args())
    except (OSError, ValueError) as error:
        raise SystemExit(f"demo preparation failed: {error}")
