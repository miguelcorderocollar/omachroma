# Release checklist

The standalone repository is public at https://github.com/miguelcorderocollar/omachroma. The `main` branch can be installed directly using the README command. No tagged GitHub release or marketplace listing has been created. CI/CD remains intentionally out of scope.

## Before the first tagged beta

- Run `./scripts/test.sh` from a fresh checkout with Python, Node and ImageMagick 7.
- Run `omarchy plugin validate .` and `python3 generate-theme-wallpaper.py --doctor` in an Omarchy session.
- Verify launch, Settings, model configuration save/default/hide/show, price refresh failure recovery, Generate/History, resizing/tiling, image selection and native export. Do not treat screenshots as proof of paid generation.
- Test shell summon/hide, Escape, disable/re-enable, shell restart and removal in an isolated Omarchy profile.
- Confirm permission for the source, result and reference images visible in the screenshots. The submission form requires an explicit declaration covering preview assets.
- Review manifest, license, docs, screenshots and tracked files. Exclude keys, personal configuration, history, outputs and private review evidence.
- Verify safe local install and removal on an isolated profile. The removal helper retains personal data. The optional Hyprland rule is user-installed.

## Tagged beta and marketplace

When the plugin is ready for a versioned release, tag a 0.x beta with the changelog and known limitations. Verify the tag from a clean clone, then follow the [official publishing guide](https://plugins.omarchy.org/publish.html).

The guide requires a public GitHub repository, root manifest, README/license and safe install/removal. The optional preview is optimized by the marketplace. Use `preview.png` at repository root, with additional screenshots linked in README.

Prepare the marketplace issue form with:

- Repository: https://github.com/miguelcorderocollar/omachroma
- Name: Omachroma
- ID: mikelon797.omachroma
- Category: Appearance
- Tags: AI, Quickshell
- Suggested missing tag: Wallpaper
- Summary: Theme-matched AI wallpaper editing and upscaling with your own fal.ai/OpenRouter keys, batches, per-theme references and persistent history.

Use one to three tags from the form's fixed list. More than three are rejected; an optional missing tag can be suggested separately. Maintainer notes should mention the Python/ImageMagick and portal dependencies, paid provider requests, launcher registration on enable, and retained personal data on removal.

Submit the form only when authorized. Marketplace listing validation is not a security audit. Provider schema/rate refresh failures and actual billing remain outside marketplace guarantees.
