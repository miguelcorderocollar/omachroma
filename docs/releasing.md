# Release checklist

This repository is a locally prepared release candidate. No public repository,
release or marketplace submission has been created yet. CI/CD is intentionally
out of scope; run checks locally.

## Before publication

- Run `./scripts/test.sh` from a fresh checkout with Python, Node and ImageMagick 7.
- Run `omarchy plugin validate .` and `python3 generate-theme-wallpaper.py --doctor`
  in an Omarchy session.
- Verify launch, Settings, model configuration save/default/hide/show, price
  refresh failure recovery, Generate/History, resizing/tiling, image selection
  and native export. Do not treat screenshots as proof of paid generation.
- Review manifest, license, docs, screenshots and tracked files. Exclude keys,
  personal configuration, history, outputs and private review evidence.
- Verify safe local install and removal on an isolated profile. The removal
  helper retains personal data. The optional Hyprland rule is user-installed.
- Confirm public owner/repository URL and version, then remove the README's
  preparation notice when the repository actually becomes public.

## Publication, when authorized

Create the public GitHub repository with only this standalone history. Push main,
then create a tagged 0.x beta with the changelog and limitations. Do not push the
private supplement's history into this repository.

Update the supplement submodule URL to the public remote and push the plugin
commit before pushing a supplement commit that references it. Verify a clean
recursive clone of the supplement resolves the plugin revision.

Follow the [official publishing guide](https://plugins.omarchy.org/publish.html).
It requires a public GitHub repository, root manifest, README/license and safe
install/removal. The optional preview is optimized by the marketplace. Use
`preview.png` at repository root, with additional screenshots linked in README.

Prepare the marketplace issue form with:

- Repository: `https://github.com/miguelcorderocollar/omachroma`
- Name: Omachroma
- ID: `mikelon797.omachroma`
- Category: Appearance
- Tags: wallpaper, ai, themes, image-editing, upscale, quickshell
- Summary: Theme-matched AI wallpaper editing and upscaling with your own
  fal.ai/OpenRouter keys, batches, per-theme references and persistent history.

Submit the form only when authorized. Marketplace listing validation is not a
security audit. Provider schema/rate refresh failures and actual billing remain
outside marketplace guarantees.
